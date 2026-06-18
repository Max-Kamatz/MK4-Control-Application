import asyncio
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from network.network_manager import NetworkManager
from models.telemetry import TelemetryData
from utils.logger import setup_logger

logger = setup_logger()

class NetworkThread(QThread):
    telemetry_received = pyqtSignal(dict)
    connection_status_changed = pyqtSignal(bool)
    command_sent = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    system_info_received = pyqtSignal(str, str)  # (info_type, value)

    def __init__(self):
        super().__init__()
        self.network_manager = None
        self.loop = None
        self.running = False

        # Telemetry throttling - emit on significant changes OR periodically
        self._last_pan = None
        self._last_tilt = None
        self._position_threshold = 0.1  # degrees - only emit if changed by >0.1°
        self._last_emit_time = 0  # timestamp of last emission
        self._emit_interval = 1.0  # emit at least every 1 second even if no change

    def run(self):
        logger.info("Network thread starting")
        self.running = True

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.network_manager = NetworkManager()

        self.network_manager.telemetry_callback = self._on_telemetry_received
        self.network_manager.connection_status_callback = self._on_connection_status_changed
        self.network_manager.system_info_callback = self._on_system_info_received

        try:
            self.loop.run_until_complete(self._async_run())
        except Exception as e:
            logger.error(f"Network thread error: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.loop.close()
            logger.info("Network thread stopped")

    async def _async_run(self):
        while self.running:
            try:
                # Just keep the event loop alive - don't auto-reconnect
                # Connection is only initiated when user clicks Connect button
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in network thread async loop: {e}")
                await asyncio.sleep(1)

    def _on_telemetry_received(self, telemetry: TelemetryData):
        """
        Throttle telemetry updates to prevent GUI event queue flooding.
        Emit if: (1) first reading, (2) position changed >0.1°, OR (3) >1 second elapsed
        """
        import time
        pan = telemetry.pan_position
        tilt = telemetry.tilt_position
        current_time = time.time()

        logger.info(f"⚡ TELEMETRY CALLBACK RECEIVED: pan={pan}°, tilt={tilt}°")

        should_emit = False

        # Always emit if this is the first reading
        if self._last_pan is None or self._last_tilt is None:
            should_emit = True
        # Emit if position changed beyond threshold
        elif pan is not None and tilt is not None:
            pan_delta = abs(pan - self._last_pan) if self._last_pan is not None else float('inf')
            tilt_delta = abs(tilt - self._last_tilt) if self._last_tilt is not None else float('inf')

            if pan_delta >= self._position_threshold or tilt_delta >= self._position_threshold:
                should_emit = True

        # Emit periodically even if no change (ensures UI always shows current position)
        if not should_emit and (current_time - self._last_emit_time) >= self._emit_interval:
            should_emit = True

        if should_emit and pan is not None and tilt is not None:
            self._last_pan = pan
            self._last_tilt = tilt
            self._last_emit_time = current_time

            telemetry_dict = {
                'pan': pan,
                'tilt': tilt,
                'pan_velocity': telemetry.pan_velocity,
                'tilt_velocity': telemetry.tilt_velocity,
                'timestamp': telemetry.timestamp.isoformat()
            }
            logger.info(f"🔊 EMITTING TELEMETRY SIGNAL: {telemetry_dict}")
            self.telemetry_received.emit(telemetry_dict)

    def _on_connection_status_changed(self, connected: bool):
        self.connection_status_changed.emit(connected)

    def _on_system_info_received(self, info_type: str, value: str):
        """Callback when system info response is received."""
        logger.info(f"System info received: {info_type} = {value}")
        self.system_info_received.emit(info_type, value)

    @pyqtSlot(float, float)
    def send_pan_tilt(self, pan: float, tilt: float):
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pan_tilt(pan, tilt),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    self.command_sent.emit(f"Pan/Tilt: {pan}°, {tilt}°")
                    logger.debug(f"Sent pan/tilt command: {pan}°, {tilt}°")
            except Exception as e:
                logger.error(f"Error sending pan/tilt command: {e}")
                self.error_occurred.emit(f"Failed to send command: {e}")

    @pyqtSlot()
    def send_position_query(self):
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_position_query(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.debug("Sent position query")
            except Exception as e:
                logger.error(f"Error sending position query: {e}")

    @pyqtSlot()
    def send_stop(self):
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_stop(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    self.command_sent.emit("Stop movement")
                    logger.info("Sent stop command")
            except Exception as e:
                logger.error(f"Error sending stop command: {e}")

    def send_zoom(self, zoom_speed: float, camera: str = "Camera1"):
        """Send zoom command. zoom_speed: -1.0 (out), 0.0 (stop), +1.0 (in), camera: Camera1/Camera2/Camera3"""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_zoom(zoom_speed, camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    if zoom_speed == 0:
                        direction = "stop"
                    else:
                        direction = "in" if zoom_speed > 0 else "out"
                    self.command_sent.emit(f"Zoom {direction} - {camera}")
                    logger.debug(f"Sent zoom {direction} command for {camera}: {zoom_speed}")
            except Exception as e:
                logger.error(f"Error sending zoom command: {e}")

    def send_focus(self, focus_speed: float, camera: str = "Camera1"):
        """Send focus command. focus_speed: -1.0 (near), 0.0 (stop), +1.0 (far), camera: Camera1/Camera2/Camera3"""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_focus(focus_speed, camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    if focus_speed == 0:
                        direction = "stop"
                    else:
                        direction = "far" if focus_speed > 0 else "near"
                    self.command_sent.emit(f"Focus {direction} - {camera}")
                    logger.debug(f"Sent focus {direction} command for {camera}: {focus_speed}")
            except Exception as e:
                logger.error(f"Error sending focus command: {e}")

    @pyqtSlot(float)
    def send_pan_speed(self, speed: float):
        """Send pan speed command. speed in degrees/second."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pan_speed(speed),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.debug(f"Sent pan speed: {speed} °/s")
            except Exception as e:
                logger.error(f"Error sending pan speed: {e}")

    @pyqtSlot(float)
    def send_tilt_speed(self, speed: float):
        """Send tilt speed command. speed in degrees/second."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_tilt_speed(speed),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.debug(f"Sent tilt speed: {speed} °/s")
            except Exception as e:
                logger.error(f"Error sending tilt speed: {e}")

    @pyqtSlot()
    def query_system_info(self):
        """Query system information (NexOS version, serial, tracking status)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.query_system_info(),
                self.loop
            )
            try:
                future.result(timeout=1.0)
                logger.info("System info queries sent")
            except Exception as e:
                logger.error(f"Error querying system info: {e}")

    @pyqtSlot()
    @pyqtSlot(str)
    def connect_to_system(self, target_ip: str = None):
        if self.loop and self.network_manager:
            # Update target IP if provided
            if target_ip:
                self.network_manager.set_target_ip(target_ip)

            # Run connection asynchronously without blocking the GUI thread
            async def connect_and_start_telemetry():
                try:
                    success = await self.network_manager.connect()
                    if success and self.network_manager.connected:
                        # Start telemetry reception on successful connection
                        asyncio.create_task(self.network_manager.receive_telemetry())
                except Exception as e:
                    logger.error(f"Error connecting: {e}")
                    self.error_occurred.emit(f"Connection failed: {e}")

            asyncio.run_coroutine_threadsafe(connect_and_start_telemetry(), self.loop)

    @pyqtSlot()
    def disconnect_from_system(self):
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.disconnect(),
                self.loop
            )
            try:
                future.result(timeout=5.0)
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")

    # Camera function methods
    def send_zoom_to_position(self, camera: int, position: int):
        """Send zoom to position command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_zoom_to_position(camera, position),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent zoom to position: Camera{camera}, Position={position}")
            except Exception as e:
                logger.error(f"Error sending zoom to position: {e}")

    def send_autofocus(self, camera: int):
        """Send autofocus command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_autofocus(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent autofocus: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending autofocus: {e}")

    def send_camera_profile(self, camera: int, profile: int):
        """Send camera profile command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_camera_profile(camera, profile),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent camera profile: Camera{camera}, Profile={profile}")
            except Exception as e:
                logger.error(f"Error sending camera profile: {e}")

    def send_video_stabilizer(self, camera: int, enable: bool):
        """Send video stabilizer command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_video_stabilizer(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent video stabilizer: Camera{camera}, Enable={enable}")
            except Exception as e:
                logger.error(f"Error sending video stabilizer: {e}")

    def send_digital_zoom_level(self, camera: int, level: float):
        """Send digital zoom level command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_digital_zoom_level(camera, level),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent digital zoom level: Camera{camera}, Level={level}")
            except Exception as e:
                logger.error(f"Error sending digital zoom level: {e}")

    def send_digital_zoom_enable(self, camera: int, enable: bool):
        """Send digital zoom enable/disable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_digital_zoom_enable(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent digital zoom enable: Camera{camera}, Enable={enable}")
            except Exception as e:
                logger.error(f"Error sending digital zoom enable: {e}")

    def send_clahe(self, camera: int, enable: bool):
        """Send CLAHE command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_clahe(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent CLAHE: Camera{camera}, Enable={enable}")
            except Exception as e:
                logger.error(f"Error sending CLAHE: {e}")

    def send_color_palette(self, camera: int, palette: int):
        """Send color palette command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_color_palette(camera, palette),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent color palette: Camera{camera}, Palette={palette}")
            except Exception as e:
                logger.error(f"Error sending color palette: {e}")

    def send_color_filter(self, camera: int, enable: bool):
        """Send color filter command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_color_filter(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent color filter: Camera{camera}, Enable={enable}")
            except Exception as e:
                logger.error(f"Error sending color filter: {e}")

    # Configuration methods
    def send_slave_zoom_mode(self, enable: bool):
        """Send slave zoom mode command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_slave_zoom_mode(enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent slave zoom mode: Enable={enable}")
            except Exception as e:
                logger.error(f"Error sending slave zoom mode: {e}")

    def send_slave_zoom_master(self, camera: int):
        """Send slave zoom master camera command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_slave_zoom_master(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent slave zoom master: Camera={camera}")
            except Exception as e:
                logger.error(f"Error sending slave zoom master: {e}")

    def send_pan_left_limit(self, limit: float):
        """Send pan left limit command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pan_left_limit(limit),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent pan left limit: {limit} degrees")
            except Exception as e:
                logger.error(f"Error sending pan left limit: {e}")

    def send_pan_right_limit(self, limit: float):
        """Send pan right limit command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pan_right_limit(limit),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent pan right limit: {limit} degrees")
            except Exception as e:
                logger.error(f"Error sending pan right limit: {e}")

    def send_tilt_up_limit(self, limit: float):
        """Send tilt up limit command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_tilt_up_limit(limit),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent tilt up limit: {limit} degrees")
            except Exception as e:
                logger.error(f"Error sending tilt up limit: {e}")

    def send_tilt_down_limit(self, limit: float):
        """Send tilt down limit command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_tilt_down_limit(limit),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent tilt down limit: {limit} degrees")
            except Exception as e:
                logger.error(f"Error sending tilt down limit: {e}")

    def send_homing_delay_mode(self, enable: bool):
        """Send homing delay mode command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_homing_delay_mode(enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent homing delay mode: Enable={enable}")
            except Exception as e:
                logger.error(f"Error sending homing delay mode: {e}")

    def send_homing_delay_time(self, time: int):
        """Send homing delay time command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_homing_delay_time(time),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent homing delay time: {time} seconds")
            except Exception as e:
                logger.error(f"Error sending homing delay time: {e}")

    def send_query_slave_zoom(self):
        """Send query for slave zoom settings."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_slave_zoom(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent query for slave zoom settings")
            except Exception as e:
                logger.error(f"Error sending slave zoom query: {e}")

    def send_query_pan_limits(self):
        """Send query for pan limits."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_pan_limits(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent query for pan limits")
            except Exception as e:
                logger.error(f"Error sending pan limits query: {e}")

    def send_query_tilt_limits(self):
        """Send query for tilt limits."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_tilt_limits(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent query for tilt limits")
            except Exception as e:
                logger.error(f"Error sending tilt limits query: {e}")

    def send_query_homing(self):
        """Send query for homing delay settings."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_homing(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent query for homing delay settings")
            except Exception as e:
                logger.error(f"Error sending homing delay query: {e}")

    # ========== MotorControl Zero Position Commands ==========

    def send_pan_set_zero(self):
        """Set current pan position as zero reference."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pan_set_zero(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Set pan zero position")
            except Exception as e:
                logger.error(f"Error setting pan zero: {e}")

    def send_pan_reset_zero(self):
        """Reset pan zero position to factory default."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pan_reset_zero(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Reset pan zero position")
            except Exception as e:
                logger.error(f"Error resetting pan zero: {e}")

    def send_pan_zero_pos(self, degrees: float):
        """Set pan zero position offset."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pan_zero_pos(degrees),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set pan zero position: {degrees} degrees")
            except Exception as e:
                logger.error(f"Error setting pan zero position: {e}")

    def send_pan_add_pos(self, degrees: float):
        """Add offset to current pan position."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pan_add_pos(degrees),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Added pan position offset: {degrees} degrees")
            except Exception as e:
                logger.error(f"Error adding pan position: {e}")

    def send_tilt_set_zero(self):
        """Set current tilt position as zero reference."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_tilt_set_zero(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Set tilt zero position")
            except Exception as e:
                logger.error(f"Error setting tilt zero: {e}")

    def send_tilt_reset_zero(self):
        """Reset tilt zero position to factory default."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_tilt_reset_zero(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Reset tilt zero position")
            except Exception as e:
                logger.error(f"Error resetting tilt zero: {e}")

    def send_tilt_zero_pos(self, degrees: float):
        """Set tilt zero position offset."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_tilt_zero_pos(degrees),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set tilt zero position: {degrees} degrees")
            except Exception as e:
                logger.error(f"Error setting tilt zero position: {e}")

    def send_tilt_add_pos(self, degrees: float):
        """Add offset to current tilt position."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_tilt_add_pos(degrees),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Added tilt position offset: {degrees} degrees")
            except Exception as e:
                logger.error(f"Error adding tilt position: {e}")

    # ========== MotorControl Speed & Movement Settings ==========

    def send_pan_max_speed(self, dps: float):
        """Set pan maximum speed limit."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pan_max_speed(dps),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set pan max speed: {dps} °/s")
            except Exception as e:
                logger.error(f"Error setting pan max speed: {e}")

    def send_pan_position_speed(self, dps: float):
        """Set pan speed for position moves."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pan_position_speed(dps),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set pan position speed: {dps} °/s")
            except Exception as e:
                logger.error(f"Error setting pan position speed: {e}")

    def send_pan_invert_movement(self, enable: bool):
        """Invert pan movement direction."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pan_invert_movement(enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set pan invert movement: {enable}")
            except Exception as e:
                logger.error(f"Error setting pan invert movement: {e}")

    def send_tilt_max_speed(self, dps: float):
        """Set tilt maximum speed limit."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_tilt_max_speed(dps),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set tilt max speed: {dps} °/s")
            except Exception as e:
                logger.error(f"Error setting tilt max speed: {e}")

    def send_tilt_position_speed(self, dps: float):
        """Set tilt speed for position moves."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_tilt_position_speed(dps),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set tilt position speed: {dps} °/s")
            except Exception as e:
                logger.error(f"Error setting tilt position speed: {e}")

    def send_tilt_invert_movement(self, enable: bool):
        """Invert tilt movement direction."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_tilt_invert_movement(enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set tilt invert movement: {enable}")
            except Exception as e:
                logger.error(f"Error setting tilt invert movement: {e}")

    # ========== MotorControl System Settings ==========

    def send_block_pt(self, enable: bool):
        """Block pan/tilt movement (safety lock)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_block_pt(enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set block P/T: {enable}")
            except Exception as e:
                logger.error(f"Error setting block P/T: {e}")

    def send_zoom_dependent_mode(self, mode: int):
        """Set zoom-dependent speed mode."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_zoom_dependent_mode(mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set zoom-dependent mode: {mode}")
            except Exception as e:
                logger.error(f"Error setting zoom-dependent mode: {e}")

    def send_acc_vel_max(self, value: int):
        """Set maximum acceleration velocity."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_acc_vel_max(value),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set acceleration velocity max: {value}")
            except Exception as e:
                logger.error(f"Error setting acc vel max: {e}")

    def send_acc_dec_max(self, value: int):
        """Set maximum deceleration."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_acc_dec_max(value),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set acceleration/deceleration max: {value}")
            except Exception as e:
                logger.error(f"Error setting acc dec max: {e}")

    def send_acc_dec_rate(self, value: int):
        """Set acceleration/deceleration rate."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_acc_dec_rate(value),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set acceleration/deceleration rate: {value}")
            except Exception as e:
                logger.error(f"Error setting acc dec rate: {e}")

    def send_acc_dec_vstop(self, value: int):
        """Set velocity stop threshold for deceleration."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_acc_dec_vstop(value),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set velocity stop threshold: {value}")
            except Exception as e:
                logger.error(f"Error setting acc dec vstop: {e}")

    def send_reset_controller(self):
        """Reset motor controller to default settings."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_reset_controller(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Reset motor controller")
            except Exception as e:
                logger.error(f"Error resetting controller: {e}")

    # ========== MotorControl Queries ==========

    def send_query_pan_max_speed(self):
        """Query pan maximum speed."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_pan_max_speed(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried pan max speed")
            except Exception as e:
                logger.error(f"Error querying pan max speed: {e}")

    def send_query_pan_position_speed(self):
        """Query pan position move speed."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_pan_position_speed(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried pan position speed")
            except Exception as e:
                logger.error(f"Error querying pan position speed: {e}")

    def send_query_pan_zero_pos(self):
        """Query pan zero position offset."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_pan_zero_pos(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried pan zero position")
            except Exception as e:
                logger.error(f"Error querying pan zero position: {e}")

    def send_query_pan_invert_movement(self):
        """Query pan movement inversion status."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_pan_invert_movement(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried pan invert movement")
            except Exception as e:
                logger.error(f"Error querying pan invert movement: {e}")

    def send_query_tilt_max_speed(self):
        """Query tilt maximum speed."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_tilt_max_speed(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried tilt max speed")
            except Exception as e:
                logger.error(f"Error querying tilt max speed: {e}")

    def send_query_tilt_position_speed(self):
        """Query tilt position move speed."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_tilt_position_speed(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried tilt position speed")
            except Exception as e:
                logger.error(f"Error querying tilt position speed: {e}")

    def send_query_tilt_zero_pos(self):
        """Query tilt zero position offset."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_tilt_zero_pos(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried tilt zero position")
            except Exception as e:
                logger.error(f"Error querying tilt zero position: {e}")

    def send_query_tilt_invert_movement(self):
        """Query tilt movement inversion status."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_tilt_invert_movement(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried tilt invert movement")
            except Exception as e:
                logger.error(f"Error querying tilt invert movement: {e}")

    def send_query_block_pt(self):
        """Query pan/tilt block status."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_block_pt(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried block P/T status")
            except Exception as e:
                logger.error(f"Error querying block P/T: {e}")

    def send_query_zoom_dependent_mode(self):
        """Query zoom-dependent mode status."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_zoom_dependent_mode(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried zoom-dependent mode")
            except Exception as e:
                logger.error(f"Error querying zoom-dependent mode: {e}")

    def send_query_acc_vel_max(self):
        """Query acceleration velocity maximum."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_acc_vel_max(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried acceleration velocity max")
            except Exception as e:
                logger.error(f"Error querying acc vel max: {e}")

    def send_query_acc_dec_max(self):
        """Query deceleration maximum."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_acc_dec_max(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried acceleration/deceleration max")
            except Exception as e:
                logger.error(f"Error querying acc dec max: {e}")

    def send_query_acc_dec_rate(self):
        """Query acceleration/deceleration rate."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_acc_dec_rate(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried acceleration/deceleration rate")
            except Exception as e:
                logger.error(f"Error querying acc dec rate: {e}")

    def send_query_acc_dec_vstop(self):
        """Query velocity stop threshold."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_acc_dec_vstop(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried velocity stop threshold")
            except Exception as e:
                logger.error(f"Error querying acc dec vstop: {e}")

    # ========== Lens Control Commands ==========

    def send_focus_to_position(self, camera: int, position: int):
        """Move focus to absolute position."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_focus_to_position(camera, position),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent focus to position: Camera{camera}, Position={position}")
            except Exception as e:
                logger.error(f"Error sending focus to position: {e}")

    def send_one_push_af(self, camera: int):
        """Trigger one-time autofocus."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_one_push_af(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent one-push AF: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending one-push AF: {e}")

    def send_focus_speed_multiplier(self, camera: int, multiplier: float):
        """Set focus speed multiplier."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_focus_speed_multiplier(camera, multiplier),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set focus speed multiplier: Camera{camera}, {multiplier}x")
            except Exception as e:
                logger.error(f"Error setting focus speed multiplier: {e}")

    def send_zoom_speed_multiplier(self, camera: int, multiplier: float):
        """Set zoom speed multiplier."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_zoom_speed_multiplier(camera, multiplier),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set zoom speed multiplier: Camera{camera}, {multiplier}x")
            except Exception as e:
                logger.error(f"Error setting zoom speed multiplier: {e}")

    def send_tele_end_pos(self, camera: int, position: int):
        """Set telephoto end position limit."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_tele_end_pos(camera, position),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set tele end position: Camera{camera}, Position={position}")
            except Exception as e:
                logger.error(f"Error setting tele end position: {e}")

    def send_wide_end_pos(self, camera: int, position: int):
        """Set wide angle end position limit."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_wide_end_pos(camera, position),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set wide end position: Camera{camera}, Position={position}")
            except Exception as e:
                logger.error(f"Error setting wide end position: {e}")

    def send_far_end_pos(self, camera: int, position: int):
        """Set far focus end position limit."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_far_end_pos(camera, position),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set far end position: Camera{camera}, Position={position}")
            except Exception as e:
                logger.error(f"Error setting far end position: {e}")

    def send_near_end_pos(self, camera: int, position: int):
        """Set near focus end position limit."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_near_end_pos(camera, position),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set near end position: Camera{camera}, Position={position}")
            except Exception as e:
                logger.error(f"Error setting near end position: {e}")

    # ========== Iris Control Commands ==========

    def send_iris_open(self, camera: int):
        """Open iris (continuous)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_iris_open(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent iris open: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending iris open: {e}")

    def send_iris_close(self, camera: int):
        """Close iris (continuous)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_iris_close(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent iris close: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending iris close: {e}")

    def send_iris_stop(self, camera: int):
        """Stop iris movement."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_iris_stop(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent iris stop: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending iris stop: {e}")

    def send_iris_to_pos(self, camera: int, position: int):
        """Move iris to absolute position."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_iris_to_pos(camera, position),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent iris to position: Camera{camera}, Position={position}")
            except Exception as e:
                logger.error(f"Error sending iris to position: {e}")

    def send_iris_mode(self, camera: int, mode: int):
        """Set iris mode (0=Manual, 1=Auto)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_iris_mode(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    mode_str = "Auto" if mode == 1 else "Manual"
                    logger.info(f"Set iris mode: Camera{camera}, {mode_str}")
            except Exception as e:
                logger.error(f"Error setting iris mode: {e}")

    def send_iris_value(self, camera: int, f_stop: float):
        """Set iris F-stop value (manual mode)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_iris_value(camera, f_stop),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set iris value: Camera{camera}, F/{f_stop}")
            except Exception as e:
                logger.error(f"Error setting iris value: {e}")

    # ========== Lens Queries ==========

    def send_query_focus_pos(self, camera: int):
        """Query focus position."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_focus_pos(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried focus position: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying focus position: {e}")

    def send_query_zoom_pos(self, camera: int):
        """Query zoom position."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_zoom_pos(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried zoom position: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying zoom position: {e}")

    def send_query_iris_mode(self, camera: int):
        """Query iris mode."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_iris_mode(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried iris mode: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying iris mode: {e}")

    def send_query_iris_pos(self, camera: int):
        """Query iris position."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_iris_pos(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried iris position: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying iris position: {e}")

    # ========== Camera Exposure Settings ==========

    def send_exposure_mode(self, camera: int, mode: int):
        """Set exposure mode (0=Full Auto, 1=Manual, 2=Shutter Priority, 3=Iris Priority)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_exposure_mode(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    modes = ["Full Auto", "Manual", "Shutter Priority", "Iris Priority"]
                    mode_str = modes[mode] if mode < len(modes) else str(mode)
                    logger.info(f"Set exposure mode: Camera{camera}, {mode_str}")
            except Exception as e:
                logger.error(f"Error setting exposure mode: {e}")

    def send_shutter_speed(self, camera: int, speed: int):
        """Set shutter speed."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_shutter_speed(camera, speed),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set shutter speed: Camera{camera}, {speed}")
            except Exception as e:
                logger.error(f"Error setting shutter speed: {e}")

    def send_gain(self, camera: int, gain: int):
        """Set gain value."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_gain(camera, gain),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set gain: Camera{camera}, {gain} dB")
            except Exception as e:
                logger.error(f"Error setting gain: {e}")

    def send_auto_mode(self, camera: int, mode: int):
        """Set auto exposure mode (0=Off, 1=On)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_auto_mode(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    mode_str = "On" if mode == 1 else "Off"
                    logger.info(f"Set auto mode: Camera{camera}, {mode_str}")
            except Exception as e:
                logger.error(f"Error setting auto mode: {e}")

    # ========== Camera White Balance Settings ==========

    def send_white_balance(self, camera: int, mode: int):
        """Set white balance mode (0=Auto, 1=Indoor, 2=Outdoor, 3=OnePush, 4=Manual)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_white_balance(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    modes = ["Auto", "Indoor", "Outdoor", "OnePush", "Manual"]
                    mode_str = modes[mode] if mode < len(modes) else str(mode)
                    logger.info(f"Set white balance: Camera{camera}, {mode_str}")
            except Exception as e:
                logger.error(f"Error setting white balance: {e}")

    def send_wb_red_gain(self, camera: int, gain: int):
        """Set white balance red gain."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_wb_red_gain(camera, gain),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set WB red gain: Camera{camera}, {gain}")
            except Exception as e:
                logger.error(f"Error setting WB red gain: {e}")

    def send_wb_blue_gain(self, camera: int, gain: int):
        """Set white balance blue gain."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_wb_blue_gain(camera, gain),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set WB blue gain: Camera{camera}, {gain}")
            except Exception as e:
                logger.error(f"Error setting WB blue gain: {e}")

    def send_color_mode(self, camera: int, mode: int):
        """Set color mode (0=Color, 1=Black & White)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_color_mode(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    mode_str = "B&W" if mode == 1 else "Color"
                    logger.info(f"Set color mode: Camera{camera}, {mode_str}")
            except Exception as e:
                logger.error(f"Error setting color mode: {e}")

    # ========== Camera Image Enhancement Settings ==========

    def send_brightness(self, camera: int, value: int):
        """Set brightness level (0-255)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_brightness(camera, value),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set brightness: Camera{camera}, {value}")
            except Exception as e:
                logger.error(f"Error setting brightness: {e}")

    def send_contrast(self, camera: int, value: int):
        """Set contrast level (0-255)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_contrast(camera, value),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set contrast: Camera{camera}, {value}")
            except Exception as e:
                logger.error(f"Error setting contrast: {e}")

    def send_saturation(self, camera: int, value: int):
        """Set saturation level (0-255)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_saturation(camera, value),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set saturation: Camera{camera}, {value}")
            except Exception as e:
                logger.error(f"Error setting saturation: {e}")

    def send_sharpness(self, camera: int, value: int):
        """Set sharpness level (0-255)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_sharpness(camera, value),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set sharpness: Camera{camera}, {value}")
            except Exception as e:
                logger.error(f"Error setting sharpness: {e}")

    def send_backlight_compensation(self, camera: int, mode: int):
        """Set backlight compensation mode (0=Off, 1=On)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_backlight_compensation(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    mode_str = "On" if mode == 1 else "Off"
                    logger.info(f"Set backlight compensation: Camera{camera}, {mode_str}")
            except Exception as e:
                logger.error(f"Error setting backlight compensation: {e}")

    def send_wide_dynamic_range(self, camera: int, mode: int):
        """Set wide dynamic range (WDR) mode (0=Off, 1=On)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_wide_dynamic_range(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    mode_str = "On" if mode == 1 else "Off"
                    logger.info(f"Set WDR: Camera{camera}, {mode_str}")
            except Exception as e:
                logger.error(f"Error setting WDR: {e}")

    def send_noise_reduction(self, camera: int, level: int):
        """Set noise reduction level (0=Off, 1-5=Low to High)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_noise_reduction(camera, level),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set noise reduction: Camera{camera}, Level {level}")
            except Exception as e:
                logger.error(f"Error setting noise reduction: {e}")

    def send_defog_mode(self, camera: int, mode: int):
        """Set defog/haze reduction mode (0=Off, 1=On)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_defog_mode(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    mode_str = "On" if mode == 1 else "Off"
                    logger.info(f"Set defog mode: Camera{camera}, {mode_str}")
            except Exception as e:
                logger.error(f"Error setting defog mode: {e}")

    # ========== Camera Setting Queries ==========

    def send_query_exposure_mode(self, camera: int):
        """Query exposure mode."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_exposure_mode(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried exposure mode: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying exposure mode: {e}")

    def send_query_shutter_speed(self, camera: int):
        """Query shutter speed."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_shutter_speed(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried shutter speed: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying shutter speed: {e}")

    def send_query_gain(self, camera: int):
        """Query gain value."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_gain(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried gain: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying gain: {e}")

    def send_query_white_balance(self, camera: int):
        """Query white balance mode."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_white_balance(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried white balance: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying white balance: {e}")

    def send_query_brightness(self, camera: int):
        """Query brightness level."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_brightness(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried brightness: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying brightness: {e}")

    def send_query_contrast(self, camera: int):
        """Query contrast level."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_contrast(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried contrast: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying contrast: {e}")

    def send_query_saturation(self, camera: int):
        """Query saturation level."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_saturation(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried saturation: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying saturation: {e}")

    # ========== VideoStabiliser Settings ==========

    def send_stabilizer_x_offset_limit(self, camera: int, limit: int):
        """Set horizontal offset limit for stabilization."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_stabilizer_x_offset_limit(camera, limit),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set stabilizer X offset limit: Camera{camera}, {limit}px")
            except Exception as e:
                logger.error(f"Error setting stabilizer X offset limit: {e}")

    def send_stabilizer_y_offset_limit(self, camera: int, limit: int):
        """Set vertical offset limit for stabilization."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_stabilizer_y_offset_limit(camera, limit),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set stabilizer Y offset limit: Camera{camera}, {limit}px")
            except Exception as e:
                logger.error(f"Error setting stabilizer Y offset limit: {e}")

    def send_stabilizer_a_offset_limit(self, camera: int, limit: int):
        """Set angular offset limit for stabilization."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_stabilizer_a_offset_limit(camera, limit),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set stabilizer A offset limit: Camera{camera}, {limit}°")
            except Exception as e:
                logger.error(f"Error setting stabilizer A offset limit: {e}")

    def send_stabilizer_mode(self, camera: int, mode: int):
        """Set stabilizer mode (0=Off, 1=Pan/Tilt, 2=Pan/Tilt/Rotation)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_stabilizer_mode(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    modes = ["Off", "Pan/Tilt", "Pan/Tilt/Rotation"]
                    mode_str = modes[mode] if mode < len(modes) else str(mode)
                    logger.info(f"Set stabilizer mode: Camera{camera}, {mode_str}")
            except Exception as e:
                logger.error(f"Error setting stabilizer mode: {e}")

    def send_stabilizer_type(self, camera: int, stabilizer_type: int):
        """Set stabilizer algorithm type."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_stabilizer_type(camera, stabilizer_type),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set stabilizer type: Camera{camera}, Type={stabilizer_type}")
            except Exception as e:
                logger.error(f"Error setting stabilizer type: {e}")

    def send_stabilizer_transparent_border(self, camera: int, enable: bool):
        """Enable/disable transparent border mode."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_stabilizer_transparent_border(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set stabilizer transparent border: Camera{camera}, {enable}")
            except Exception as e:
                logger.error(f"Error setting stabilizer transparent border: {e}")

    def send_stabilizer_const_x_offset(self, camera: int, offset: int):
        """Set constant horizontal offset."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_stabilizer_const_x_offset(camera, offset),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set stabilizer const X offset: Camera{camera}, {offset}px")
            except Exception as e:
                logger.error(f"Error setting stabilizer const X offset: {e}")

    def send_stabilizer_const_y_offset(self, camera: int, offset: int):
        """Set constant vertical offset."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_stabilizer_const_y_offset(camera, offset),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set stabilizer const Y offset: Camera{camera}, {offset}px")
            except Exception as e:
                logger.error(f"Error setting stabilizer const Y offset: {e}")

    def send_stabilizer_const_a_offset(self, camera: int, offset: int):
        """Set constant angular offset."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_stabilizer_const_a_offset(camera, offset),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set stabilizer const A offset: Camera{camera}, {offset}°")
            except Exception as e:
                logger.error(f"Error setting stabilizer const A offset: {e}")

    # ========== VideoStabiliser Queries ==========

    def send_query_stabilizer_x_offset_limit(self, camera: int):
        """Query horizontal offset limit."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_stabilizer_x_offset_limit(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried stabilizer X offset limit: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying stabilizer X offset limit: {e}")

    def send_query_stabilizer_y_offset_limit(self, camera: int):
        """Query vertical offset limit."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_stabilizer_y_offset_limit(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried stabilizer Y offset limit: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying stabilizer Y offset limit: {e}")

    def send_query_stabilizer_mode(self, camera: int):
        """Query stabilizer mode."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_stabilizer_mode(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried stabilizer mode: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying stabilizer mode: {e}")

    # ========== ColorFilter Settings ==========

    def send_color_filter_auto_mode(self, camera: int, mode: int):
        """Set color filter auto mode (0=Manual, 1=Auto)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_color_filter_auto_mode(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    mode_str = "Auto" if mode == 1 else "Manual"
                    logger.info(f"Set color filter auto mode: Camera{camera}, {mode_str}")
            except Exception as e:
                logger.error(f"Error setting color filter auto mode: {e}")

    def send_color_filter_hue(self, camera: int, hue: int):
        """Set color filter hue (0-360 degrees)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_color_filter_hue(camera, hue),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set color filter hue: Camera{camera}, {hue}°")
            except Exception as e:
                logger.error(f"Error setting color filter hue: {e}")

    def send_color_filter_saturation(self, camera: int, saturation: int):
        """Set color filter saturation (0-255)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_color_filter_saturation(camera, saturation),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set color filter saturation: Camera{camera}, {saturation}")
            except Exception as e:
                logger.error(f"Error setting color filter saturation: {e}")

    def send_color_filter_brightness(self, camera: int, brightness: int):
        """Set color filter brightness (0-255)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_color_filter_brightness(camera, brightness),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set color filter brightness: Camera{camera}, {brightness}")
            except Exception as e:
                logger.error(f"Error setting color filter brightness: {e}")

    def send_color_filter_contrast(self, camera: int, contrast: int):
        """Set color filter contrast (0-255)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_color_filter_contrast(camera, contrast),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set color filter contrast: Camera{camera}, {contrast}")
            except Exception as e:
                logger.error(f"Error setting color filter contrast: {e}")

    def send_color_filter_gamma(self, camera: int, gamma: float):
        """Set color filter gamma (0.1-5.0, 1.0=neutral)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_color_filter_gamma(camera, gamma),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set color filter gamma: Camera{camera}, {gamma}")
            except Exception as e:
                logger.error(f"Error setting color filter gamma: {e}")

    # ========== ColorFilter Queries ==========

    def send_query_color_filter_hue(self, camera: int):
        """Query color filter hue."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_color_filter_hue(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried color filter hue: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying color filter hue: {e}")

    def send_query_color_filter_saturation(self, camera: int):
        """Query color filter saturation."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_color_filter_saturation(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried color filter saturation: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying color filter saturation: {e}")

    def send_query_color_filter_gamma(self, camera: int):
        """Query color filter gamma."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_color_filter_gamma(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried color filter gamma: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying color filter gamma: {e}")

    # ========== CLAHE Settings ==========

    def send_clahe_clip_limit(self, camera: int, limit: float):
        """Set CLAHE clip limit (1.0-40.0, typical 2.0-4.0)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_clahe_clip_limit(camera, limit),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set CLAHE clip limit: Camera{camera}, {limit}")
            except Exception as e:
                logger.error(f"Error setting CLAHE clip limit: {e}")

    def send_clahe_tiles_grid_size(self, camera: int, size: int):
        """Set CLAHE tile grid size (typically 8x8, 16x16)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_clahe_tiles_grid_size(camera, size),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set CLAHE tiles grid size: Camera{camera}, {size}")
            except Exception as e:
                logger.error(f"Error setting CLAHE tiles grid size: {e}")

    # ========== CLAHE Queries ==========

    def send_query_clahe_clip_limit(self, camera: int):
        """Query CLAHE clip limit."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_clahe_clip_limit(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried CLAHE clip limit: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying CLAHE clip limit: {e}")

    def send_query_clahe_tiles_grid_size(self, camera: int):
        """Query CLAHE tile grid size."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_clahe_tiles_grid_size(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried CLAHE tiles grid size: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying CLAHE tiles grid size: {e}")

    # ========== ImageFlip Settings ==========

    def send_image_flip_mode(self, camera: int, mode: int):
        """Set image flip mode (0=Off, 1=Horizontal, 2=Vertical, 3=Both)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_image_flip_mode(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    modes = ["Off", "Horizontal", "Vertical", "Both"]
                    mode_str = modes[mode] if mode < len(modes) else str(mode)
                    logger.info(f"Set image flip mode: Camera{camera}, {mode_str}")
            except Exception as e:
                logger.error(f"Error setting image flip mode: {e}")

    def send_image_flip_horizontal(self, camera: int, enable: bool):
        """Enable/disable horizontal flip."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_image_flip_horizontal(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set horizontal flip: Camera{camera}, {enable}")
            except Exception as e:
                logger.error(f"Error setting horizontal flip: {e}")

    def send_image_flip_vertical(self, camera: int, enable: bool):
        """Enable/disable vertical flip."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_image_flip_vertical(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Set vertical flip: Camera{camera}, {enable}")
            except Exception as e:
                logger.error(f"Error setting vertical flip: {e}")

    # ========== ImageFlip Queries ==========

    def send_query_image_flip_mode(self, camera: int):
        """Query image flip mode."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_image_flip_mode(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried image flip mode: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying image flip mode: {e}")

    def send_query_image_flip_horizontal(self, camera: int):
        """Query horizontal flip status."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_image_flip_horizontal(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried horizontal flip: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying horizontal flip: {e}")

    def send_query_image_flip_vertical(self, camera: int):
        """Query vertical flip status."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_image_flip_vertical(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried vertical flip: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying vertical flip: {e}")

    # Additional missing methods for complete integration

    def send_query_all_motor_settings(self):
        """Send query for all motor settings."""
        logger.info("Querying all motor settings (sends individual queries)")
        # Send individual query commands
        self.send_query_pan_max_speed()
        self.send_query_pan_position_speed()
        self.send_query_pan_zero_pos()
        self.send_query_pan_invert_movement()
        self.send_query_pan_limits()
        self.send_query_tilt_max_speed()
        self.send_query_tilt_position_speed()
        self.send_query_tilt_zero_pos()
        self.send_query_tilt_invert_movement()
        self.send_query_tilt_limits()
        self.send_query_block_pt()
        self.send_query_zoom_dependent_mode()
        self.send_query_acc_vel_max()
        self.send_query_acc_dec_max()
        self.send_query_acc_dec_rate()
        self.send_query_acc_dec_vstop()
        self.send_query_homing()
        self.send_query_slave_zoom()

    def send_autofocus_mode(self, camera: int, enable: bool):
        """Send continuous autofocus mode command (enable/disable)."""
        if self.loop and self.network_manager:
            # Convert bool to mode: 1=continuous AF, 0=manual
            mode = 1 if enable else 0
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_autofocus_mode(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Camera{camera}: Set continuous AF mode: {enable}")
            except Exception as e:
                logger.error(f"Error sending autofocus mode: {e}")

    def send_query_camera_settings(self, camera: int):
        """Send query for all camera settings."""
        logger.info(f"Querying all settings for Camera{camera} (sends individual queries)")
        # Send individual query commands for the specified camera
        self.send_query_exposure_mode(camera)
        self.send_query_shutter_speed(camera)
        self.send_query_gain(camera)
        self.send_query_white_balance(camera)
        self.send_query_brightness(camera)
        self.send_query_contrast(camera)
        self.send_query_saturation(camera)
        self.send_query_focus_pos(camera)
        self.send_query_zoom_pos(camera)
        self.send_query_iris_mode(camera)
        self.send_query_iris_pos(camera)
        self.send_query_image_flip_mode(camera)
        self.send_query_stabilizer_mode(camera)

    # ========== RTSP/VideoStream Control Methods ==========

    def send_video_stream_enable(self, camera: int, stream: int):
        """Enable video stream."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_video_stream_enable(camera, stream),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent video stream enable: Camera{camera} Stream{stream}")
            except Exception as e:
                logger.error(f"Error enabling video stream: {e}")

    def send_video_stream_disable(self, camera: int, stream: int):
        """Disable video stream."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_video_stream_disable(camera, stream),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent video stream disable: Camera{camera} Stream{stream}")
            except Exception as e:
                logger.error(f"Error disabling video stream: {e}")

    def send_video_stream_restart(self, camera: int, stream: int):
        """Restart video stream."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_video_stream_restart(camera, stream),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent video stream restart: Camera{camera} Stream{stream}")
            except Exception as e:
                logger.error(f"Error restarting video stream: {e}")

    def send_rtsp_suffix(self, camera: int, stream: int, suffix: str):
        """Send RTSP suffix command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_rtsp_suffix(camera, stream, suffix),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent RTSP suffix: Camera{camera} Stream{stream} = {suffix}")
            except Exception as e:
                logger.error(f"Error sending RTSP suffix: {e}")

    def send_rtsp_port(self, camera: int, stream: int, port: int):
        """Send RTSP port command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_rtsp_port(camera, stream, port),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent RTSP port: Camera{camera} Stream{stream} = {port}")
            except Exception as e:
                logger.error(f"Error sending RTSP port: {e}")

    def send_rtsp_multicast_ip(self, camera: int, stream: int, ip: str):
        """Send RTSP multicast IP command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_rtsp_multicast_ip(camera, stream, ip),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent RTSP multicast IP: Camera{camera} Stream{stream} = {ip}")
            except Exception as e:
                logger.error(f"Error sending RTSP multicast IP: {e}")

    def send_rtsp_multicast_port(self, camera: int, stream: int, port: int):
        """Send RTSP multicast port command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_rtsp_multicast_port(camera, stream, port),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent RTSP multicast port: Camera{camera} Stream{stream} = {port}")
            except Exception as e:
                logger.error(f"Error sending RTSP multicast port: {e}")

    def send_rtsp_user(self, camera: int, stream: int, username: str):
        """Send RTSP username command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_rtsp_user(camera, stream, username),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent RTSP username: Camera{camera} Stream{stream}")
            except Exception as e:
                logger.error(f"Error sending RTSP username: {e}")

    def send_rtsp_password(self, camera: int, stream: int, password: str):
        """Send RTSP password command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_rtsp_password(camera, stream, password),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent RTSP password: Camera{camera} Stream{stream}")
            except Exception as e:
                logger.error(f"Error sending RTSP password: {e}")

    def send_resolution(self, camera: int, stream: int, width: int, height: int):
        """Send video resolution command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_resolution(camera, stream, width, height),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent resolution: Camera{camera} Stream{stream} = {width}x{height}")
            except Exception as e:
                logger.error(f"Error sending resolution: {e}")

    def send_codec(self, camera: int, stream: int, codec: str):
        """Send video codec command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_codec(camera, stream, codec),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent codec: Camera{camera} Stream{stream} = {codec}")
            except Exception as e:
                logger.error(f"Error sending codec: {e}")

    def send_h264_profile(self, camera: int, stream: int, profile: str):
        """Send H264 profile command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_h264_profile(camera, stream, profile),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent H264 profile: Camera{camera} Stream{stream} = {profile}")
            except Exception as e:
                logger.error(f"Error sending H264 profile: {e}")

    def send_jpeg_quality(self, camera: int, stream: int, quality: int):
        """Send JPEG quality command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_jpeg_quality(camera, stream, quality),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent JPEG quality: Camera{camera} Stream{stream} = {quality}")
            except Exception as e:
                logger.error(f"Error sending JPEG quality: {e}")

    def send_bitrate(self, camera: int, stream: int, bitrate: int):
        """Send video bitrate command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_bitrate(camera, stream, bitrate),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent bitrate: Camera{camera} Stream{stream} = {bitrate} kbps")
            except Exception as e:
                logger.error(f"Error sending bitrate: {e}")

    def send_bitrate_mode(self, camera: int, stream: int, mode: str):
        """Send bitrate mode command (CBR/VBR)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_bitrate_mode(camera, stream, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent bitrate mode: Camera{camera} Stream{stream} = {mode}")
            except Exception as e:
                logger.error(f"Error sending bitrate mode: {e}")

    def send_min_bitrate(self, camera: int, stream: int, bitrate: int):
        """Send minimum bitrate command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_min_bitrate(camera, stream, bitrate),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent min bitrate: Camera{camera} Stream{stream} = {bitrate} kbps")
            except Exception as e:
                logger.error(f"Error sending min bitrate: {e}")

    def send_max_bitrate(self, camera: int, stream: int, bitrate: int):
        """Send maximum bitrate command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_max_bitrate(camera, stream, bitrate),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent max bitrate: Camera{camera} Stream{stream} = {bitrate} kbps")
            except Exception as e:
                logger.error(f"Error sending max bitrate: {e}")

    def send_fps(self, camera: int, stream: int, fps: int):
        """Send frame rate command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_fps(camera, stream, fps),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent FPS: Camera{camera} Stream{stream} = {fps}")
            except Exception as e:
                logger.error(f"Error sending FPS: {e}")

    def send_gop(self, camera: int, stream: int, gop: int):
        """Send GOP (Group of Pictures) command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_gop(camera, stream, gop),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent GOP: Camera{camera} Stream{stream} = {gop}")
            except Exception as e:
                logger.error(f"Error sending GOP: {e}")

    def send_fit_mode(self, camera: int, stream: int, mode: str):
        """Send fit mode command (letterbox/crop/stretch)."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_fit_mode(camera, stream, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent fit mode: Camera{camera} Stream{stream} = {mode}")
            except Exception as e:
                logger.error(f"Error sending fit mode: {e}")

    def send_overlay_mode(self, camera: int, stream: int, enable: bool):
        """Send overlay mode command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_overlay_mode(camera, stream, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent overlay mode: Camera{camera} Stream{stream} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending overlay mode: {e}")

    def send_metadata_mode(self, camera: int, stream: int, enable: bool):
        """Send metadata mode command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_metadata_mode(camera, stream, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent metadata mode: Camera{camera} Stream{stream} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending metadata mode: {e}")

    def send_metadata_suffix(self, camera: int, stream: int, suffix: str):
        """Send metadata suffix command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_metadata_suffix(camera, stream, suffix),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent metadata suffix: Camera{camera} Stream{stream} = {suffix}")
            except Exception as e:
                logger.error(f"Error sending metadata suffix: {e}")

    def send_rtp_mode(self, camera: int, stream: int, enable: bool):
        """Send RTP mode command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_rtp_mode(camera, stream, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent RTP mode: Camera{camera} Stream{stream} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending RTP mode: {e}")

    def send_rtp_port(self, camera: int, stream: int, port: int):
        """Send RTP port command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_rtp_port(camera, stream, port),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent RTP port: Camera{camera} Stream{stream} = {port}")
            except Exception as e:
                logger.error(f"Error sending RTP port: {e}")

    def send_rtp_dest_ip(self, camera: int, stream: int, ip: str):
        """Send RTP destination IP command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_rtp_dest_ip(camera, stream, ip),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent RTP dest IP: Camera{camera} Stream{stream} = {ip}")
            except Exception as e:
                logger.error(f"Error sending RTP dest IP: {e}")

    def send_rtmp_mode(self, camera: int, stream: int, enable: bool):
        """Send RTMP mode command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_rtmp_mode(camera, stream, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent RTMP mode: Camera{camera} Stream{stream} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending RTMP mode: {e}")

    def send_rtmp_port(self, camera: int, stream: int, port: int):
        """Send RTMP port command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_rtmp_port(camera, stream, port),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent RTMP port: Camera{camera} Stream{stream} = {port}")
            except Exception as e:
                logger.error(f"Error sending RTMP port: {e}")

    def send_hls_mode(self, camera: int, stream: int, enable: bool):
        """Send HLS mode command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_hls_mode(camera, stream, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent HLS mode: Camera{camera} Stream{stream} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending HLS mode: {e}")

    def send_hls_port(self, camera: int, stream: int, port: int):
        """Send HLS port command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_hls_port(camera, stream, port),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent HLS port: Camera{camera} Stream{stream} = {port}")
            except Exception as e:
                logger.error(f"Error sending HLS port: {e}")

    def send_srt_mode(self, camera: int, stream: int, enable: bool):
        """Send SRT mode command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_srt_mode(camera, stream, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent SRT mode: Camera{camera} Stream{stream} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending SRT mode: {e}")

    def send_srt_port(self, camera: int, stream: int, port: int):
        """Send SRT port command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_srt_port(camera, stream, port),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent SRT port: Camera{camera} Stream{stream} = {port}")
            except Exception as e:
                logger.error(f"Error sending SRT port: {e}")

    def send_udp_payload_size(self, camera: int, stream: int, size: int):
        """Send UDP payload size command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_udp_payload_size(camera, stream, size),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent UDP payload size: Camera{camera} Stream{stream} = {size} bytes")
            except Exception as e:
                logger.error(f"Error sending UDP payload size: {e}")

    def send_query_video_stream_settings(self, camera: int, stream: int):
        """Query video stream settings."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_video_stream_settings(camera, stream),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried video stream settings: Camera{camera} Stream{stream}")
            except Exception as e:
                logger.error(f"Error querying video stream settings: {e}")

    # ========== Overlay Control Methods ==========

    def send_crosshair_mode(self, camera: int, enable: bool):
        """Send crosshair mode command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_crosshair_mode(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent crosshair mode: Camera{camera} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending crosshair mode: {e}")

    def send_crosshair_size(self, camera: int, size: int):
        """Send crosshair size command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_crosshair_size(camera, size),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent crosshair size: Camera{camera} = {size}")
            except Exception as e:
                logger.error(f"Error sending crosshair size: {e}")

    def send_crosshair_color(self, camera: int, color: str):
        """Send crosshair color command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_crosshair_color(camera, color),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent crosshair color: Camera{camera} = {color}")
            except Exception as e:
                logger.error(f"Error sending crosshair color: {e}")

    def send_datetime_overlay(self, camera: int, enable: bool):
        """Send date/time overlay command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_datetime_overlay(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent date/time overlay: Camera{camera} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending date/time overlay: {e}")

    def send_zoom_pos_overlay(self, camera: int, enable: bool):
        """Send zoom position overlay command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_zoom_pos_overlay(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent zoom position overlay: Camera{camera} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending zoom position overlay: {e}")

    def send_focus_mode_overlay(self, camera: int, enable: bool):
        """Send focus mode overlay command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_focus_mode_overlay(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent focus mode overlay: Camera{camera} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending focus mode overlay: {e}")

    def send_digital_zoom_overlay(self, camera: int, enable: bool):
        """Send digital zoom overlay command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_digital_zoom_overlay(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent digital zoom overlay: Camera{camera} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending digital zoom overlay: {e}")

    def send_clahe_overlay(self, camera: int, enable: bool):
        """Send CLAHE overlay command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_clahe_overlay(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent CLAHE overlay: Camera{camera} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending CLAHE overlay: {e}")

    def send_tracker_overlay(self, camera: int, enable: bool):
        """Send tracker overlay command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_tracker_overlay(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent tracker overlay: Camera{camera} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending tracker overlay: {e}")

    def send_pan_tilt_overlay(self, camera: int, enable: bool):
        """Send pan/tilt overlay command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pan_tilt_overlay(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent pan/tilt overlay: Camera{camera} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending pan/tilt overlay: {e}")

    def send_lrf_overlay(self, camera: int, enable: bool):
        """Send LRF (Laser Range Finder) overlay command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_lrf_overlay(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent LRF overlay: Camera{camera} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending LRF overlay: {e}")

    def send_webrtc_overlay(self, camera: int, enable: bool):
        """Send WebRTC overlay command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_webrtc_overlay(camera, enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent WebRTC overlay: Camera{camera} = {'Enable' if enable else 'Disable'}")
            except Exception as e:
                logger.error(f"Error sending WebRTC overlay: {e}")

    # ========== Motion Magnificator Wrapper Methods ==========

    def send_motion_magnificator_enable(self, camera: int):
        """Enable motion magnificator."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_magnificator_enable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion magnificator enable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending motion magnificator enable: {e}")

    def send_motion_magnificator_disable(self, camera: int):
        """Disable motion magnificator."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_magnificator_disable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion magnificator disable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending motion magnificator disable: {e}")

    def send_motion_magnificator_level(self, camera: int, level: int):
        """Set motion magnificator level."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_magnificator_level(camera, level),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion magnificator level: Camera{camera}, Level={level}")
            except Exception as e:
                logger.error(f"Error sending motion magnificator level: {e}")

    # ========== VideoTracker Wrapper Methods ==========

    def send_video_tracker_reset(self, camera: int):
        """Reset video tracker."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_video_tracker_reset(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent video tracker reset: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending video tracker reset: {e}")

    def send_video_tracker_enable(self, camera: int):
        """Enable video tracker."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_video_tracker_enable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent video tracker enable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending video tracker enable: {e}")

    def send_video_tracker_disable(self, camera: int):
        """Disable video tracker."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_video_tracker_disable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent video tracker disable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending video tracker disable: {e}")

    def send_video_tracker_lock(self, camera: int):
        """Lock video tracker on target."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_video_tracker_lock(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent video tracker lock: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending video tracker lock: {e}")

    def send_video_tracker_unlock(self, camera: int):
        """Unlock video tracker."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_video_tracker_unlock(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent video tracker unlock: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending video tracker unlock: {e}")

    def send_video_tracker_mode(self, camera: int, mode: int):
        """Set video tracker mode."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_video_tracker_mode(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent video tracker mode: Camera{camera}, Mode={mode}")
            except Exception as e:
                logger.error(f"Error sending video tracker mode: {e}")

    def send_video_tracker_object_size(self, camera: int, size: int):
        """Set video tracker object size."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_video_tracker_object_size(camera, size),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent video tracker object size: Camera{camera}, Size={size}")
            except Exception as e:
                logger.error(f"Error sending video tracker object size: {e}")

    def send_video_tracker_search_area_size(self, camera: int, size: int):
        """Set video tracker search area size."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_video_tracker_search_area_size(camera, size),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent video tracker search area size: Camera{camera}, Size={size}")
            except Exception as e:
                logger.error(f"Error sending video tracker search area size: {e}")

    # ========== MotionDetector Wrapper Methods ==========

    def send_motion_detector_reset(self, camera: int):
        """Reset motion detector."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_detector_reset(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion detector reset: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending motion detector reset: {e}")

    def send_motion_detector_enable(self, camera: int):
        """Enable motion detector."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_detector_enable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion detector enable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending motion detector enable: {e}")

    def send_motion_detector_disable(self, camera: int):
        """Disable motion detector."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_detector_disable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion detector disable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending motion detector disable: {e}")

    def send_motion_detector_frame_buffer(self, camera: int, size: int):
        """Set motion detector frame buffer size."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_detector_frame_buffer(camera, size),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion detector frame buffer: Camera{camera}, Size={size}")
            except Exception as e:
                logger.error(f"Error sending motion detector frame buffer: {e}")

    def send_motion_detector_min_width(self, camera: int, width: int):
        """Set motion detector minimum width."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_detector_min_width(camera, width),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion detector min width: Camera{camera}, Width={width}")
            except Exception as e:
                logger.error(f"Error sending motion detector min width: {e}")

    def send_motion_detector_max_width(self, camera: int, width: int):
        """Set motion detector maximum width."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_detector_max_width(camera, width),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion detector max width: Camera{camera}, Width={width}")
            except Exception as e:
                logger.error(f"Error sending motion detector max width: {e}")

    def send_motion_detector_min_height(self, camera: int, height: int):
        """Set motion detector minimum height."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_detector_min_height(camera, height),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion detector min height: Camera{camera}, Height={height}")
            except Exception as e:
                logger.error(f"Error sending motion detector min height: {e}")

    def send_motion_detector_max_height(self, camera: int, height: int):
        """Set motion detector maximum height."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_detector_max_height(camera, height),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion detector max height: Camera{camera}, Height={height}")
            except Exception as e:
                logger.error(f"Error sending motion detector max height: {e}")

    def send_motion_detector_x_criteria(self, camera: int, criteria: float):
        """Set motion detector X criteria."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_detector_x_criteria(camera, criteria),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion detector X criteria: Camera{camera}, Criteria={criteria}")
            except Exception as e:
                logger.error(f"Error sending motion detector X criteria: {e}")

    def send_motion_detector_y_criteria(self, camera: int, criteria: float):
        """Set motion detector Y criteria."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_detector_y_criteria(camera, criteria),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion detector Y criteria: Camera{camera}, Criteria={criteria}")
            except Exception as e:
                logger.error(f"Error sending motion detector Y criteria: {e}")

    def send_motion_detector_reset_criteria(self, camera: int, criteria: float):
        """Set motion detector reset criteria."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_detector_reset_criteria(camera, criteria),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion detector reset criteria: Camera{camera}, Criteria={criteria}")
            except Exception as e:
                logger.error(f"Error sending motion detector reset criteria: {e}")

    def send_motion_detector_sensitivity(self, camera: int, sensitivity: float):
        """Set motion detector sensitivity."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_detector_sensitivity(camera, sensitivity),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion detector sensitivity: Camera{camera}, Sensitivity={sensitivity}")
            except Exception as e:
                logger.error(f"Error sending motion detector sensitivity: {e}")

    def send_motion_detector_mode(self, camera: int, mode: int):
        """Set motion detector mode."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_motion_detector_mode(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent motion detector mode: Camera{camera}, Mode={mode}")
            except Exception as e:
                logger.error(f"Error sending motion detector mode: {e}")

    # ========== ChangesDetector Wrapper Methods ==========

    def send_changes_detector_reset(self, camera: int):
        """Reset changes detector."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_changes_detector_reset(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent changes detector reset: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending changes detector reset: {e}")

    def send_changes_detector_enable(self, camera: int):
        """Enable changes detector."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_changes_detector_enable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent changes detector enable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending changes detector enable: {e}")

    def send_changes_detector_disable(self, camera: int):
        """Disable changes detector."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_changes_detector_disable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent changes detector disable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending changes detector disable: {e}")

    def send_changes_detector_frame_buffer(self, camera: int, size: int):
        """Set changes detector frame buffer size."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_changes_detector_frame_buffer(camera, size),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent changes detector frame buffer: Camera{camera}, Size={size}")
            except Exception as e:
                logger.error(f"Error sending changes detector frame buffer: {e}")

    def send_changes_detector_min_width(self, camera: int, width: int):
        """Set changes detector minimum width."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_changes_detector_min_width(camera, width),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent changes detector min width: Camera{camera}, Width={width}")
            except Exception as e:
                logger.error(f"Error sending changes detector min width: {e}")

    def send_changes_detector_max_width(self, camera: int, width: int):
        """Set changes detector maximum width."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_changes_detector_max_width(camera, width),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent changes detector max width: Camera{camera}, Width={width}")
            except Exception as e:
                logger.error(f"Error sending changes detector max width: {e}")

    def send_changes_detector_min_height(self, camera: int, height: int):
        """Set changes detector minimum height."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_changes_detector_min_height(camera, height),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent changes detector min height: Camera{camera}, Height={height}")
            except Exception as e:
                logger.error(f"Error sending changes detector min height: {e}")

    def send_changes_detector_max_height(self, camera: int, height: int):
        """Set changes detector maximum height."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_changes_detector_max_height(camera, height),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent changes detector max height: Camera{camera}, Height={height}")
            except Exception as e:
                logger.error(f"Error sending changes detector max height: {e}")

    def send_changes_detector_x_criteria(self, camera: int, criteria: float):
        """Set changes detector X criteria."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_changes_detector_x_criteria(camera, criteria),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent changes detector X criteria: Camera{camera}, Criteria={criteria}")
            except Exception as e:
                logger.error(f"Error sending changes detector X criteria: {e}")

    def send_changes_detector_y_criteria(self, camera: int, criteria: float):
        """Set changes detector Y criteria."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_changes_detector_y_criteria(camera, criteria),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent changes detector Y criteria: Camera{camera}, Criteria={criteria}")
            except Exception as e:
                logger.error(f"Error sending changes detector Y criteria: {e}")

    def send_changes_detector_reset_criteria(self, camera: int, criteria: float):
        """Set changes detector reset criteria."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_changes_detector_reset_criteria(camera, criteria),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent changes detector reset criteria: Camera{camera}, Criteria={criteria}")
            except Exception as e:
                logger.error(f"Error sending changes detector reset criteria: {e}")

    def send_changes_detector_sensitivity(self, camera: int, sensitivity: float):
        """Set changes detector sensitivity."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_changes_detector_sensitivity(camera, sensitivity),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent changes detector sensitivity: Camera{camera}, Sensitivity={sensitivity}")
            except Exception as e:
                logger.error(f"Error sending changes detector sensitivity: {e}")

    def send_changes_detector_mode(self, camera: int, mode: int):
        """Set changes detector mode."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_changes_detector_mode(camera, mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent changes detector mode: Camera{camera}, Mode={mode}")
            except Exception as e:
                logger.error(f"Error sending changes detector mode: {e}")

    # ========== Classification Wrapper Methods ==========

    def send_classification_enable(self, camera: int):
        """Enable classification."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_classification_enable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent classification enable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending classification enable: {e}")

    def send_classification_disable(self, camera: int):
        """Disable classification."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_classification_disable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent classification disable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending classification disable: {e}")

    def send_classification_model(self, camera: int, model: str):
        """Set classification model."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_classification_model(camera, model),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent classification model: Camera{camera}, Model={model}")
            except Exception as e:
                logger.error(f"Error sending classification model: {e}")

    def send_classification_confidence(self, camera: int, confidence: float):
        """Set classification confidence threshold."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_classification_confidence(camera, confidence),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent classification confidence: Camera{camera}, Confidence={confidence}")
            except Exception as e:
                logger.error(f"Error sending classification confidence: {e}")

    def send_query_classification_status(self, camera: int):
        """Query classification status."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_classification_status(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried classification status: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying classification status: {e}")

    # ========== License Query Wrapper Methods ==========

    def send_query_video_tracker_token(self):
        """Query video tracker license token."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_video_tracker_token(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried video tracker license token")
            except Exception as e:
                logger.error(f"Error querying video tracker token: {e}")

    def send_query_video_tracker_license_status(self):
        """Query video tracker license status."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_video_tracker_license_status(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried video tracker license status")
            except Exception as e:
                logger.error(f"Error querying video tracker license status: {e}")

    def send_query_video_stabiliser_token(self):
        """Query video stabiliser license token."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_video_stabiliser_token(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried video stabiliser license token")
            except Exception as e:
                logger.error(f"Error querying video stabiliser token: {e}")

    def send_query_video_stabiliser_license_status(self):
        """Query video stabiliser license status."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_video_stabiliser_license_status(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried video stabiliser license status")
            except Exception as e:
                logger.error(f"Error querying video stabiliser license status: {e}")

    def send_query_motion_detector_token(self):
        """Query motion detector license token."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_motion_detector_token(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried motion detector license token")
            except Exception as e:
                logger.error(f"Error querying motion detector token: {e}")

    def send_query_motion_detector_license_status(self):
        """Query motion detector license status."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_motion_detector_license_status(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried motion detector license status")
            except Exception as e:
                logger.error(f"Error querying motion detector license status: {e}")

    def send_query_changes_detector_token(self):
        """Query changes detector license token."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_changes_detector_token(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried changes detector license token")
            except Exception as e:
                logger.error(f"Error querying changes detector token: {e}")

    def send_query_changes_detector_license_status(self):
        """Query changes detector license status."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_changes_detector_license_status(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried changes detector license status")
            except Exception as e:
                logger.error(f"Error querying changes detector license status: {e}")

    def send_query_classification_token(self):
        """Query classification license token."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_classification_token(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried classification license token")
            except Exception as e:
                logger.error(f"Error querying classification token: {e}")

    def send_query_classification_license_status(self):
        """Query classification license status."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_query_classification_license_status(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried classification license status")
            except Exception as e:
                logger.error(f"Error querying classification license status: {e}")

    # ========== Detection Subscription Wrapper Method ==========

    def send_subscribe_objects_events(self, camera: int):
        """Subscribe to objects detection events."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_subscribe_objects_events(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent subscribe objects events: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending subscribe objects events: {e}")

    # ========== ProcedureManager Wrapper Methods ==========

    def send_procedure_load(self, procedure_name: str):
        """Send procedure load command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_procedure_load(procedure_name),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent procedure load: {procedure_name}")
            except Exception as e:
                logger.error(f"Error sending procedure load: {e}")

    def send_procedure_execute(self):
        """Send procedure execute command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_procedure_execute(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent procedure execute")
            except Exception as e:
                logger.error(f"Error sending procedure execute: {e}")

    def send_procedure_stop(self):
        """Send procedure stop command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_procedure_stop(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent procedure stop")
            except Exception as e:
                logger.error(f"Error sending procedure stop: {e}")

    def query_procedure_status(self):
        """Query procedure status."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.query_procedure_status(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried procedure status")
            except Exception as e:
                logger.error(f"Error querying procedure status: {e}")

    # ========== BadPixelProcessor Wrapper Methods ==========

    def send_bad_pixel_enable(self, camera: int):
        """Send bad pixel enable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_bad_pixel_enable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent bad pixel enable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending bad pixel enable: {e}")

    def send_bad_pixel_disable(self, camera: int):
        """Send bad pixel disable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_bad_pixel_disable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent bad pixel disable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending bad pixel disable: {e}")

    def send_bad_pixel_calibrate(self, camera: int):
        """Send bad pixel calibrate command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_bad_pixel_calibrate(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent bad pixel calibrate: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending bad pixel calibrate: {e}")

    def send_bad_pixel_threshold(self, camera: int, threshold: float):
        """Send bad pixel threshold command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_bad_pixel_threshold(camera, threshold),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent bad pixel threshold: Camera{camera}, Threshold={threshold}")
            except Exception as e:
                logger.error(f"Error sending bad pixel threshold: {e}")

    def query_bad_pixel_settings(self, camera: int):
        """Query bad pixel settings."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.query_bad_pixel_settings(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried bad pixel settings: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying bad pixel settings: {e}")

    # ========== VideoSource Wrapper Methods ==========

    def send_video_source(self, camera: int, source_id: str):
        """Send video source command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_video_source(camera, source_id),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent video source: Camera{camera}, Source={source_id}")
            except Exception as e:
                logger.error(f"Error sending video source: {e}")

    def query_video_source(self, camera: int):
        """Query video source."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.query_video_source(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried video source: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying video source: {e}")

    # ========== WebRtcOverlay Wrapper Methods ==========

    def send_webrtc_overlay_enable(self, camera: int):
        """Send webrtc overlay enable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_webrtc_overlay_enable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent WebRTC overlay enable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending WebRTC overlay enable: {e}")

    def send_webrtc_overlay_disable(self, camera: int):
        """Send webrtc overlay disable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_webrtc_overlay_disable(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent WebRTC overlay disable: Camera{camera}")
            except Exception as e:
                logger.error(f"Error sending WebRTC overlay disable: {e}")

    def query_webrtc_overlay_settings(self, camera: int):
        """Query webrtc overlay settings."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.query_webrtc_overlay_settings(camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Queried WebRTC overlay settings: Camera{camera}")
            except Exception as e:
                logger.error(f"Error querying WebRTC overlay settings: {e}")

    # ========== ExternalUp Wrapper Methods ==========

    def send_external_up_enable(self):
        """Send external up enable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_external_up_enable(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent external UP enable")
            except Exception as e:
                logger.error(f"Error sending external UP enable: {e}")

    def send_external_up_disable(self):
        """Send external up disable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_external_up_disable(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent external UP disable")
            except Exception as e:
                logger.error(f"Error sending external UP disable: {e}")

    def send_external_up_port(self, port: int):
        """Send external up port command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_external_up_port(port),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent external UP port: {port}")
            except Exception as e:
                logger.error(f"Error sending external UP port: {e}")

    def send_external_up_address(self, address: str):
        """Send external up address command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_external_up_address(address),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent external UP address: {address}")
            except Exception as e:
                logger.error(f"Error sending external UP address: {e}")

    def query_external_up_settings(self):
        """Query external up settings."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.query_external_up_settings(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried external UP settings")
            except Exception as e:
                logger.error(f"Error querying external UP settings: {e}")

    # ========== PelcoD Wrapper Methods ==========

    def send_pelco_d_enable(self):
        """Send pelco d enable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pelco_d_enable(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent Pelco-D enable")
            except Exception as e:
                logger.error(f"Error sending Pelco-D enable: {e}")

    def send_pelco_d_disable(self):
        """Send pelco d disable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pelco_d_disable(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent Pelco-D disable")
            except Exception as e:
                logger.error(f"Error sending Pelco-D disable: {e}")

    def send_pelco_d_port(self, port: int):
        """Send pelco d port command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pelco_d_port(port),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent Pelco-D port: {port}")
            except Exception as e:
                logger.error(f"Error sending Pelco-D port: {e}")

    def send_pelco_d_address(self, address: str):
        """Send pelco d address command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_pelco_d_address(address),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent Pelco-D address: {address}")
            except Exception as e:
                logger.error(f"Error sending Pelco-D address: {e}")

    def query_pelco_d_settings(self):
        """Query pelco d settings."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.query_pelco_d_settings(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Queried Pelco-D settings")
            except Exception as e:
                logger.error(f"Error querying Pelco-D settings: {e}")

    # ========== Phase 4A: Lrf Wrapper Methods ==========

    def send_lrf_fire(self):
        """Send LRF fire command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_lrf_fire(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent LRF fire")
            except Exception as e:
                logger.error(f"Error sending LRF fire: {e}")

    def send_lrf_power(self, enable: bool):
        """Send LRF power command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_lrf_power(enable),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent LRF power: {enable}")
            except Exception as e:
                logger.error(f"Error sending LRF power: {e}")

    def send_lrf_mode(self, mode: int):
        """Send LRF mode command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_lrf_mode(mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent LRF mode: {mode}")
            except Exception as e:
                logger.error(f"Error sending LRF mode: {e}")

    def send_lrf_query(self):
        """Send LRF query command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_lrf_query(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent LRF query")
            except Exception as e:
                logger.error(f"Error sending LRF query: {e}")

    # ========== Phase 4A: Speaker Wrapper Methods ==========

    def send_speaker_enable(self):
        """Send speaker enable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_speaker_enable(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent speaker enable")
            except Exception as e:
                logger.error(f"Error sending speaker enable: {e}")

    def send_speaker_disable(self):
        """Send speaker disable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_speaker_disable(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent speaker disable")
            except Exception as e:
                logger.error(f"Error sending speaker disable: {e}")

    def send_speaker_volume(self, volume: int):
        """Send speaker volume command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_speaker_volume(volume),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent speaker volume: {volume}")
            except Exception as e:
                logger.error(f"Error sending speaker volume: {e}")

    def send_speaker_query(self):
        """Send speaker query command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_speaker_query(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent speaker query")
            except Exception as e:
                logger.error(f"Error sending speaker query: {e}")

    # ========== Phase 4A: G5Laser Wrapper Methods ==========

    def send_g5_laser_enable(self):
        """Send G5 laser enable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_g5_laser_enable(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent G5 laser enable")
            except Exception as e:
                logger.error(f"Error sending G5 laser enable: {e}")

    def send_g5_laser_disable(self):
        """Send G5 laser disable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_g5_laser_disable(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent G5 laser disable")
            except Exception as e:
                logger.error(f"Error sending G5 laser disable: {e}")

    def send_g5_laser_power(self, power: int):
        """Send G5 laser power command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_g5_laser_power(power),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent G5 laser power: {power}")
            except Exception as e:
                logger.error(f"Error sending G5 laser power: {e}")

    def send_g5_laser_query(self):
        """Send G5 laser query command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_g5_laser_query(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent G5 laser query")
            except Exception as e:
                logger.error(f"Error sending G5 laser query: {e}")

    # ========== Phase 4A: PeakBeam Wrapper Methods ==========

    def send_peak_beam_enable(self):
        """Send PeakBeam enable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_peak_beam_enable(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent PeakBeam enable")
            except Exception as e:
                logger.error(f"Error sending PeakBeam enable: {e}")

    def send_peak_beam_disable(self):
        """Send PeakBeam disable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_peak_beam_disable(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent PeakBeam disable")
            except Exception as e:
                logger.error(f"Error sending PeakBeam disable: {e}")

    def send_peak_beam_intensity(self, intensity: int):
        """Send PeakBeam intensity command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_peak_beam_intensity(intensity),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent PeakBeam intensity: {intensity}")
            except Exception as e:
                logger.error(f"Error sending PeakBeam intensity: {e}")

    def send_peak_beam_mode(self, mode: int):
        """Send PeakBeam mode command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_peak_beam_mode(mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent PeakBeam mode: {mode}")
            except Exception as e:
                logger.error(f"Error sending PeakBeam mode: {e}")

    def send_peak_beam_query(self):
        """Send PeakBeam query command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_peak_beam_query(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent PeakBeam query")
            except Exception as e:
                logger.error(f"Error sending PeakBeam query: {e}")

    # ========== Phase 4A: Companion Wrapper Methods ==========

    def send_companion_enable(self):
        """Send Companion enable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_companion_enable(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent Companion enable")
            except Exception as e:
                logger.error(f"Error sending Companion enable: {e}")

    def send_companion_disable(self):
        """Send Companion disable command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_companion_disable(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent Companion disable")
            except Exception as e:
                logger.error(f"Error sending Companion disable: {e}")

    def send_companion_brightness(self, brightness: int):
        """Send Companion brightness command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_companion_brightness(brightness),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent Companion brightness: {brightness}")
            except Exception as e:
                logger.error(f"Error sending Companion brightness: {e}")

    def send_companion_mode(self, mode: int):
        """Send Companion mode command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_companion_mode(mode),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info(f"Sent Companion mode: {mode}")
            except Exception as e:
                logger.error(f"Error sending Companion mode: {e}")

    def send_companion_query(self):
        """Send Companion query command."""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_companion_query(),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    logger.info("Sent Companion query")
            except Exception as e:
                logger.error(f"Error sending Companion query: {e}")

    def stop(self):
        logger.info("Stopping network thread")
        self.running = False

        if self.network_manager:
            if self.loop:
                future = asyncio.run_coroutine_threadsafe(
                    self.network_manager.disconnect(),
                    self.loop
                )
                try:
                    future.result(timeout=5.0)
                except Exception as e:
                    logger.error(f"Error during shutdown: {e}")

        self.quit()
        self.wait()
