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

    def __init__(self):
        super().__init__()
        self.network_manager = None
        self.loop = None
        self.running = False

    def run(self):
        logger.info("Network thread starting")
        self.running = True

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.network_manager = NetworkManager()

        self.network_manager.telemetry_callback = self._on_telemetry_received
        self.network_manager.connection_status_callback = self._on_connection_status_changed

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
        telemetry_dict = {
            'pan': telemetry.pan_position,
            'tilt': telemetry.tilt_position,
            'pan_velocity': telemetry.pan_velocity,
            'tilt_velocity': telemetry.tilt_velocity,
            'timestamp': telemetry.timestamp.isoformat()
        }
        self.telemetry_received.emit(telemetry_dict)

    def _on_connection_status_changed(self, connected: bool):
        self.connection_status_changed.emit(connected)

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
        """Send zoom command. zoom_speed: -1.0 (out) to +1.0 (in), camera: Camera1/Camera2/Camera3"""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_zoom(zoom_speed, camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
                    direction = "in" if zoom_speed > 0 else "out"
                    self.command_sent.emit(f"Zoom {direction} - {camera}")
                    logger.debug(f"Sent zoom {direction} command for {camera}: {zoom_speed}")
            except Exception as e:
                logger.error(f"Error sending zoom command: {e}")

    def send_focus(self, focus_speed: float, camera: str = "Camera1"):
        """Send focus command. focus_speed: -1.0 (near) to +1.0 (far), camera: Camera1/Camera2/Camera3"""
        if self.loop and self.network_manager:
            future = asyncio.run_coroutine_threadsafe(
                self.network_manager.send_focus(focus_speed, camera),
                self.loop
            )
            try:
                success = future.result(timeout=1.0)
                if success:
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
