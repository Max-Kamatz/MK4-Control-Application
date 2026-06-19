import asyncio
import socket
from typing import Optional, Callable
from network.eup_protocol import EUPProtocol
from models.telemetry import TelemetryData
from utils.logger import setup_logger
from utils.constants import TARGET_IP, TCP_PELCO_PORT, UDP_TELEMETRY_PORT, UP_PROTOCOL_PORT

logger = setup_logger()

class NetworkManager:
    def __init__(self, target_ip: Optional[str] = None):
        self.target_ip = target_ip or TARGET_IP
        self.tcp_port = TCP_PELCO_PORT
        self.udp_telemetry_port = UDP_TELEMETRY_PORT
        self.up_protocol_port = UP_PROTOCOL_PORT

        self.eup_protocol = EUPProtocol()  # String-based External UP Protocol

        self.tcp_reader: Optional[asyncio.StreamReader] = None
        self.tcp_writer: Optional[asyncio.StreamWriter] = None
        self.udp_socket: Optional[socket.socket] = None
        self.up_udp_socket: Optional[socket.socket] = None

        self.connected = False
        self.running = False

        self.telemetry_callback: Optional[Callable] = None
        self.connection_status_callback: Optional[Callable] = None
        self.system_info_callback: Optional[Callable] = None

    def set_target_ip(self, ip: str):
        """Update the target IP address (must be disconnected first)."""
        if self.connected:
            logger.warning("Cannot change IP while connected")
            return False
        self.target_ip = ip
        logger.info(f"Target IP updated to {ip}")
        return True

    async def connect(self) -> bool:
        try:
            # Try TCP connection to EUP port (34030) first
            tcp_available = False
            try:
                logger.info(f"Attempting TCP connection to {self.target_ip}:{self.up_protocol_port} (EUP)")
                self.tcp_reader, self.tcp_writer = await asyncio.wait_for(
                    asyncio.open_connection(self.target_ip, self.up_protocol_port),
                    timeout=2.0
                )
                logger.info("TCP connection established (EUP protocol available)")
                tcp_available = True
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
                logger.warning(f"TCP connection to EUP port not available: {e}")
                # Try legacy Pelco port as fallback
                try:
                    logger.info(f"Attempting TCP connection to {self.target_ip}:{self.tcp_port} (Pelco)")
                    self.tcp_reader, self.tcp_writer = await asyncio.wait_for(
                        asyncio.open_connection(self.target_ip, self.tcp_port),
                        timeout=2.0
                    )
                    logger.info("TCP connection established (Pelco port)")
                    tcp_available = True
                except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e2:
                    logger.warning(f"TCP connection not available (this is OK for UDP-only systems): {e2}")
                    # Continue anyway - UDP should work

            # Set up UDP sockets (required for UP protocol)
            # Note: For EUP protocol, we send commands to port 34030 and receive replies on the same port
            # The socket must be bound to receive replies
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow port reuse
            try:
                self.udp_socket.bind(('0.0.0.0', self.up_protocol_port))  # Bind to EUP port to receive replies
                self.udp_socket.setblocking(False)
                logger.info(f"✅ UDP socket successfully bound to EUP protocol port {self.up_protocol_port}")
            except OSError as e:
                logger.error(f"❌ Failed to bind UDP socket to port {self.up_protocol_port}: {e}")
                raise

            self.up_udp_socket = self.udp_socket  # Use the same socket for send/receive
            logger.info(f"UP protocol UDP socket configured for bidirectional communication on port {self.up_protocol_port}")

            # Test UDP connectivity by sending a position query
            test_command = self.eup_protocol.query_pan_position()
            self.up_udp_socket.sendto(test_command.encode('utf-8'), (self.target_ip, self.up_protocol_port))
            logger.info(f"Sent EUP protocol test command to {self.target_ip}:{self.up_protocol_port}")

            self.connected = True
            if self.connection_status_callback:
                self.connection_status_callback(True)

            if tcp_available:
                logger.info("Connected with TCP (Pelco) + UDP (UP Protocol)")
            else:
                logger.info("Connected with UDP only (UP Protocol)")

            return True

        except Exception as e:
            logger.error(f"Connection error: {e}")
            self.connected = False
            if self.connection_status_callback:
                self.connection_status_callback(False)
            return False

    async def disconnect(self):
        logger.info("Disconnecting from network")
        self.running = False
        self.connected = False

        if self.tcp_writer:
            self.tcp_writer.close()
            await self.tcp_writer.wait_closed()

        if self.udp_socket:
            self.udp_socket.close()
            self.udp_socket = None

        # Note: up_udp_socket is the same as udp_socket, so don't close twice
        self.up_udp_socket = None

        if self.connection_status_callback:
            self.connection_status_callback(False)

        logger.info("Disconnected")

    async def send_command(self, command_string: str, use_udp: bool = True) -> bool:
        """
        Send EUP command (string-based protocol).

        Args:
            command_string: EUP command string (will be encoded to UTF-8)
            use_udp: Use UDP (default) or TCP
        """
        if not self.connected:
            logger.warning("Cannot send command: not connected")
            return False

        try:
            command_bytes = command_string.encode('utf-8')

            if use_udp:
                if self.up_udp_socket:
                    self.up_udp_socket.sendto(command_bytes, (self.target_ip, self.up_protocol_port))
                    logger.debug(f"Sent EUP command: {command_string.strip()}")
                    return True
            else:
                if self.tcp_writer:
                    self.tcp_writer.write(command_bytes)
                    await self.tcp_writer.drain()
                    logger.debug(f"Sent EUP command via TCP: {command_string.strip()}")
                    return True

        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False

        return False

    async def send_pan_tilt(self, pan: float, tilt: float) -> bool:
        """Send absolute pan/tilt position command."""
        command = self.eup_protocol.build_pan_tilt_absolute(pan, tilt)
        # Try TCP first if available, fall back to UDP
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_position_query(self) -> bool:
        """Query current gimbal position."""
        pan_query = self.eup_protocol.query_pan_position()
        tilt_query = self.eup_protocol.query_tilt_position()
        logger.debug(f"Querying position: pan_query={pan_query}, tilt_query={tilt_query}")
        # Send queries via TCP (not UDP) - system only responds to queries over TCP
        await self.send_command(pan_query, use_udp=False)
        await self.send_command(tilt_query, use_udp=False)
        return True

    async def send_stop(self) -> bool:
        """Stop all gimbal movement."""
        command = self.eup_protocol.build_stop_command()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_zoom(self, zoom_direction: float, camera: str = "Camera1") -> bool:
        """Send zoom command. zoom_direction: -1.0 (out), 0.0 (stop), +1.0 (in), camera: Camera1/Camera2/Camera3"""
        direction = int(zoom_direction)  # Convert to -1, 0, or +1
        # Extract camera number from "Camera1", "Camera2", "Camera3"
        camera_num = int(camera.replace("Camera", ""))
        command = self.eup_protocol.build_zoom_command(direction, camera=camera_num)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_focus(self, focus_direction: float, camera: str = "Camera1") -> bool:
        """Send focus command. focus_direction: -1.0 (near), 0.0 (stop), +1.0 (far), camera: Camera1/Camera2/Camera3"""
        direction = int(focus_direction)  # Convert to -1, 0, or +1
        # Extract camera number from "Camera1", "Camera2", "Camera3"
        camera_num = int(camera.replace("Camera", ""))
        command = self.eup_protocol.build_focus_command(direction, camera=camera_num)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_pan_speed(self, speed: float) -> bool:
        """Send pan speed command. speed in degrees/second."""
        command = self.eup_protocol.build_pan_speed(speed)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_tilt_speed(self, speed: float) -> bool:
        """Send tilt speed command. speed in degrees/second."""
        command = self.eup_protocol.build_tilt_speed(speed)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_zoom_to_position(self, camera: int, position: int) -> bool:
        """Send zoom to absolute position command."""
        command = self.eup_protocol.build_zoom_to_position(position, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_autofocus(self, camera: int) -> bool:
        """Send autofocus command."""
        command = self.eup_protocol.build_autofocus(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_camera_profile(self, camera: int, profile: int) -> bool:
        """Send camera profile command."""
        command = self.eup_protocol.build_camera_profile(profile, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def query_system_info(self) -> dict:
        """
        Query system information (NexOS version, mainboard serial, tracking status).

        Returns:
            dict with keys: 'nexos_version', 'mainboard_serial', 'tracking_status'
        """
        info = {
            'nexos_version': None,
            'mainboard_serial': None,
            'tracking_status': None
        }

        # Query NexOS version
        version_query = self.eup_protocol.query_nexos_version()
        await self.send_command(version_query, use_udp=False)  # Use TCP for queries

        # Query mainboard serial
        serial_query = self.eup_protocol.query_mainboard_serial()
        await self.send_command(serial_query, use_udp=False)

        # Query tracking status
        tracking_query = self.eup_protocol.query_tracking_enabled()
        await self.send_command(tracking_query, use_udp=False)

        # Note: Responses will be received asynchronously via UDP callback
        # The calling code should wait for the responses to arrive
        logger.info("System information queries sent")
        return info

    async def send_video_stabilizer(self, camera: int, enable: bool) -> bool:
        """Send video stabilizer command."""
        command = self.eup_protocol.build_video_stabilizer(enable, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_digital_zoom_level(self, camera: int, level: float) -> bool:
        """Send digital zoom level command."""
        command = self.eup_protocol.build_digital_zoom(level, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_digital_zoom_enable(self, camera: int, enable: bool) -> bool:
        """Send digital zoom enable/disable command."""
        if enable:
            command = self.eup_protocol.enable_digital_zoom(camera)
        else:
            command = self.eup_protocol.disable_digital_zoom(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_clahe(self, camera: int, enable: bool) -> bool:
        """Send CLAHE command."""
        command = self.eup_protocol.build_clahe(enable, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_color_palette(self, camera: int, palette: int) -> bool:
        """Send color palette command."""
        command = self.eup_protocol.build_color_palette(palette, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_color_filter(self, camera: int, enable: bool) -> bool:
        """Send color filter enable/disable command."""
        if enable:
            command = self.eup_protocol.enable_color_filter(camera)
        else:
            command = self.eup_protocol.disable_color_filter(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # Configuration commands
    async def send_slave_zoom_mode(self, enable: bool) -> bool:
        """Send slave zoom mode command."""
        command = self.eup_protocol.build_slave_zoom_mode(enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_slave_zoom_master(self, camera: int) -> bool:
        """Send slave zoom master camera command."""
        command = self.eup_protocol.build_slave_zoom_master_camera(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_pan_left_limit(self, degrees: float) -> bool:
        """Send pan left limit command."""
        command = self.eup_protocol.build_pan_left_limit(degrees)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_pan_right_limit(self, degrees: float) -> bool:
        """Send pan right limit command."""
        command = self.eup_protocol.build_pan_right_limit(degrees)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_tilt_up_limit(self, degrees: float) -> bool:
        """Send tilt up limit command."""
        command = self.eup_protocol.build_tilt_up_limit(degrees)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_tilt_down_limit(self, degrees: float) -> bool:
        """Send tilt down limit command."""
        command = self.eup_protocol.build_tilt_down_limit(degrees)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_homing_delay_mode(self, enable: bool) -> bool:
        """Send homing delay mode command."""
        command = self.eup_protocol.build_homing_delay_mode(enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_homing_delay_time(self, seconds: int) -> bool:
        """Send homing delay time command."""
        command = self.eup_protocol.build_homing_delay_time(seconds)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_query_slave_zoom(self) -> bool:
        """Query slave zoom settings."""
        mode_query = self.eup_protocol.query_slave_zoom_mode()
        master_query = self.eup_protocol.query_slave_zoom_master_camera()
        await self.send_command(mode_query, use_udp=True)
        await self.send_command(master_query, use_udp=True)
        return True

    async def send_query_pan_limits(self) -> bool:
        """Query pan limits."""
        left_query = self.eup_protocol.query_pan_left_limit()
        right_query = self.eup_protocol.query_pan_right_limit()
        await self.send_command(left_query, use_udp=True)
        await self.send_command(right_query, use_udp=True)
        return True

    async def send_query_tilt_limits(self) -> bool:
        """Query tilt limits."""
        up_query = self.eup_protocol.query_tilt_up_limit()
        down_query = self.eup_protocol.query_tilt_down_limit()
        await self.send_command(up_query, use_udp=True)
        await self.send_command(down_query, use_udp=True)
        return True

    async def send_query_homing(self) -> bool:
        """Query homing delay settings."""
        mode_query = self.eup_protocol.query_homing_delay_mode()
        time_query = self.eup_protocol.query_homing_delay_time()
        await self.send_command(mode_query, use_udp=True)
        await self.send_command(time_query, use_udp=True)
        return True

    # ========== MotorControl Zero Position Commands ==========

    async def send_pan_set_zero(self) -> bool:
        """Set current pan position as zero reference."""
        command = self.eup_protocol.build_pan_set_zero()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_pan_reset_zero(self) -> bool:
        """Reset pan zero position to factory default."""
        command = self.eup_protocol.build_pan_reset_zero()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_pan_zero_pos(self, degrees: float) -> bool:
        """Set pan zero position offset."""
        command = self.eup_protocol.build_pan_zero_pos(degrees)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_pan_add_pos(self, degrees: float) -> bool:
        """Add offset to current pan position."""
        command = self.eup_protocol.build_pan_add_pos(degrees)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_tilt_set_zero(self) -> bool:
        """Set current tilt position as zero reference."""
        command = self.eup_protocol.build_tilt_set_zero()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_tilt_reset_zero(self) -> bool:
        """Reset tilt zero position to factory default."""
        command = self.eup_protocol.build_tilt_reset_zero()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_tilt_zero_pos(self, degrees: float) -> bool:
        """Set tilt zero position offset."""
        command = self.eup_protocol.build_tilt_zero_pos(degrees)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_tilt_add_pos(self, degrees: float) -> bool:
        """Add offset to current tilt position."""
        command = self.eup_protocol.build_tilt_add_pos(degrees)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== MotorControl Speed & Movement Settings ==========

    async def send_pan_max_speed(self, dps: float) -> bool:
        """Set pan maximum speed limit."""
        command = self.eup_protocol.build_pan_max_speed(dps)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_pan_position_speed(self, dps: float) -> bool:
        """Set pan speed for position moves."""
        command = self.eup_protocol.build_pan_position_speed(dps)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_pan_invert_movement(self, enable: bool) -> bool:
        """Invert pan movement direction."""
        command = self.eup_protocol.build_pan_invert_movement(enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_tilt_max_speed(self, dps: float) -> bool:
        """Set tilt maximum speed limit."""
        command = self.eup_protocol.build_tilt_max_speed(dps)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_tilt_position_speed(self, dps: float) -> bool:
        """Set tilt speed for position moves."""
        command = self.eup_protocol.build_tilt_position_speed(dps)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_tilt_invert_movement(self, enable: bool) -> bool:
        """Invert tilt movement direction."""
        command = self.eup_protocol.build_tilt_invert_movement(enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== MotorControl System Settings ==========

    async def send_block_pt(self, enable: bool) -> bool:
        """Block pan/tilt movement (safety lock)."""
        command = self.eup_protocol.build_block_pt(enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_zoom_dependent_mode(self, mode: int) -> bool:
        """Set zoom-dependent speed mode."""
        command = self.eup_protocol.build_zoom_dependent_mode(mode)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_acc_vel_max(self, value: int) -> bool:
        """Set maximum acceleration velocity."""
        command = self.eup_protocol.build_acc_vel_max(value)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_acc_dec_max(self, value: int) -> bool:
        """Set maximum deceleration."""
        command = self.eup_protocol.build_acc_dec_max(value)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_acc_dec_rate(self, value: int) -> bool:
        """Set acceleration/deceleration rate."""
        command = self.eup_protocol.build_acc_dec_rate(value)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_acc_dec_vstop(self, value: int) -> bool:
        """Set velocity stop threshold for deceleration."""
        command = self.eup_protocol.build_acc_dec_vstop(value)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_reset_controller(self) -> bool:
        """Reset motor controller to default settings."""
        command = self.eup_protocol.build_reset_controller()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== Lens Control Commands ==========

    async def send_focus_to_position(self, camera: int, position: int) -> bool:
        """Send focus to absolute position command."""
        command = self.eup_protocol.build_focus_to_position(position, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_one_push_af(self, camera: int) -> bool:
        """Trigger one-time autofocus."""
        command = self.eup_protocol.build_one_push_af(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_zoom_speed(self, speed: int, camera: int) -> bool:
        """
        Set zoom speed for a camera.

        Args:
            speed: Speed value [0-100%] of max hardware zoom speed
            camera: Camera number (1, 2, or 3)
        """
        command = self.eup_protocol.build_zoom_speed(speed, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_focus_speed(self, speed: int, camera: int) -> bool:
        """
        Set focus speed for a camera.

        Args:
            speed: Speed value [0-100%] of max hardware focus speed
            camera: Camera number (1, 2, or 3)
        """
        command = self.eup_protocol.build_focus_speed(speed, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_focus_speed_multiplier(self, camera: int, multiplier: float) -> bool:
        """Set focus speed multiplier."""
        command = self.eup_protocol.build_focus_speed_multiplier(multiplier, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_zoom_speed_multiplier(self, camera: int, multiplier: float) -> bool:
        """Set zoom speed multiplier."""
        command = self.eup_protocol.build_zoom_speed_multiplier(multiplier, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_tele_end_pos(self, camera: int, position: int) -> bool:
        """Set telephoto end position limit."""
        command = self.eup_protocol.build_tele_end_pos(position, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_wide_end_pos(self, camera: int, position: int) -> bool:
        """Set wide angle end position limit."""
        command = self.eup_protocol.build_wide_end_pos(position, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_far_end_pos(self, camera: int, position: int) -> bool:
        """Set far focus end position limit."""
        command = self.eup_protocol.build_far_end_pos(position, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_near_end_pos(self, camera: int, position: int) -> bool:
        """Set near focus end position limit."""
        command = self.eup_protocol.build_near_end_pos(position, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== Iris Control ==========

    async def send_iris_open(self, camera: int) -> bool:
        """Open iris (continuous)."""
        command = self.eup_protocol.build_iris_open(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_iris_close(self, camera: int) -> bool:
        """Close iris (continuous)."""
        command = self.eup_protocol.build_iris_close(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_iris_stop(self, camera: int) -> bool:
        """Stop iris movement."""
        command = self.eup_protocol.build_iris_stop(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_iris_to_pos(self, camera: int, position: int) -> bool:
        """Move iris to absolute position."""
        command = self.eup_protocol.build_iris_to_pos(position, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_iris_mode(self, camera: int, mode: int) -> bool:
        """Set iris mode (0=Manual, 1=Auto)."""
        command = self.eup_protocol.build_iris_mode(mode, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_iris_value(self, camera: int, f_stop: float) -> bool:
        """Set iris F-stop value (manual mode)."""
        command = self.eup_protocol.build_iris_value(f_stop, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== Camera Exposure Settings ==========

    async def send_exposure_mode(self, camera: int, mode: int) -> bool:
        """Set exposure mode (0=Full Auto, 1=Manual, 2=Shutter Priority, 3=Iris Priority)."""
        command = self.eup_protocol.build_exposure_mode(mode, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_shutter_speed(self, camera: int, speed: int) -> bool:
        """Set shutter speed."""
        command = self.eup_protocol.build_shutter_speed(speed, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_gain(self, camera: int, gain: int) -> bool:
        """Set gain value."""
        command = self.eup_protocol.build_gain(gain, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_auto_mode(self, camera: int, mode: int) -> bool:
        """Set auto exposure mode."""
        command = self.eup_protocol.build_auto_mode(mode, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== Camera White Balance Settings ==========

    async def send_white_balance(self, camera: int, mode: int) -> bool:
        """Set white balance mode (0=Auto, 1=Indoor, 2=Outdoor, 3=OnePush, 4=Manual)."""
        command = self.eup_protocol.build_white_balance(mode, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_wb_red_gain(self, camera: int, gain: int) -> bool:
        """Set white balance red gain (manual mode)."""
        command = self.eup_protocol.build_wb_red_gain(gain, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_wb_blue_gain(self, camera: int, gain: int) -> bool:
        """Set white balance blue gain (manual mode)."""
        command = self.eup_protocol.build_wb_blue_gain(gain, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_color_mode(self, camera: int, mode: int) -> bool:
        """Set color mode (0=Color, 1=Black & White)."""
        command = self.eup_protocol.build_color_mode(mode, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== Camera Image Enhancement Settings ==========

    async def send_brightness(self, camera: int, value: int) -> bool:
        """Set brightness level."""
        command = self.eup_protocol.build_brightness(value, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_contrast(self, camera: int, value: int) -> bool:
        """Set contrast level."""
        command = self.eup_protocol.build_contrast(value, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_saturation(self, camera: int, value: int) -> bool:
        """Set saturation level."""
        command = self.eup_protocol.build_saturation(value, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_sharpness(self, camera: int, value: int) -> bool:
        """Set sharpness level."""
        command = self.eup_protocol.build_sharpness(value, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_backlight_compensation(self, camera: int, mode: int) -> bool:
        """Set backlight compensation mode."""
        command = self.eup_protocol.build_backlight_compensation(mode, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_wide_dynamic_range(self, camera: int, mode: int) -> bool:
        """Set wide dynamic range (WDR) mode."""
        command = self.eup_protocol.build_wide_dynamic_range(mode, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_noise_reduction(self, camera: int, level: int) -> bool:
        """Set noise reduction level."""
        command = self.eup_protocol.build_noise_reduction(level, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_defog_mode(self, camera: int, mode: int) -> bool:
        """Set defog/haze reduction mode."""
        command = self.eup_protocol.build_defog_mode(mode, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== VideoStabiliser Advanced Settings ==========

    async def send_stabilizer_x_offset_limit(self, camera: int, limit: int) -> bool:
        """Set horizontal offset limit for stabilization."""
        command = self.eup_protocol.build_stabilizer_x_offset_limit(limit, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_stabilizer_y_offset_limit(self, camera: int, limit: int) -> bool:
        """Set vertical offset limit for stabilization."""
        command = self.eup_protocol.build_stabilizer_y_offset_limit(limit, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_stabilizer_a_offset_limit(self, camera: int, limit: int) -> bool:
        """Set angular offset limit for stabilization."""
        command = self.eup_protocol.build_stabilizer_a_offset_limit(limit, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_stabilizer_mode(self, camera: int, mode: int) -> bool:
        """Set stabilizer mode (0=Off, 1=Pan/Tilt, 2=Pan/Tilt/Rotation)."""
        command = self.eup_protocol.build_stabilizer_mode(mode, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_stabilizer_type(self, camera: int, stabilizer_type: int) -> bool:
        """Set stabilizer algorithm type."""
        command = self.eup_protocol.build_stabilizer_type(stabilizer_type, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_stabilizer_transparent_border(self, camera: int, enable: bool) -> bool:
        """Enable/disable transparent border mode."""
        command = self.eup_protocol.build_stabilizer_transparent_border(enable, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_stabilizer_const_x_offset(self, camera: int, offset: int) -> bool:
        """Set constant horizontal offset."""
        command = self.eup_protocol.build_stabilizer_const_x_offset(offset, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_stabilizer_const_y_offset(self, camera: int, offset: int) -> bool:
        """Set constant vertical offset."""
        command = self.eup_protocol.build_stabilizer_const_y_offset(offset, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_stabilizer_const_a_offset(self, camera: int, offset: int) -> bool:
        """Set constant angular offset."""
        command = self.eup_protocol.build_stabilizer_const_a_offset(offset, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== ColorFilter Advanced Settings ==========

    async def send_color_filter_auto_mode(self, camera: int, mode: int) -> bool:
        """Set color filter auto mode (0=Manual, 1=Auto)."""
        command = self.eup_protocol.build_color_filter_auto_mode(mode, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_color_filter_hue(self, camera: int, hue: int) -> bool:
        """Set color filter hue."""
        command = self.eup_protocol.build_color_filter_hue(hue, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_color_filter_saturation(self, camera: int, saturation: int) -> bool:
        """Set color filter saturation."""
        command = self.eup_protocol.build_color_filter_saturation(saturation, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_color_filter_brightness(self, camera: int, brightness: int) -> bool:
        """Set color filter brightness."""
        command = self.eup_protocol.build_color_filter_brightness(brightness, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_color_filter_contrast(self, camera: int, contrast: int) -> bool:
        """Set color filter contrast."""
        command = self.eup_protocol.build_color_filter_contrast(contrast, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_color_filter_gamma(self, camera: int, gamma: float) -> bool:
        """Set color filter gamma."""
        command = self.eup_protocol.build_color_filter_gamma(gamma, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== CLAHE Advanced Settings ==========

    async def send_clahe_clip_limit(self, camera: int, limit: float) -> bool:
        """Set CLAHE clip limit."""
        command = self.eup_protocol.build_clahe_clip_limit(limit, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_clahe_tiles_grid_size(self, camera: int, size: int) -> bool:
        """Set CLAHE tile grid size."""
        command = self.eup_protocol.build_clahe_tiles_grid_size(size, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== ImageFlip Control ==========

    async def send_image_flip_mode(self, camera: int, mode: int) -> bool:
        """Set image flip mode (0=Off, 1=Horizontal, 2=Vertical, 3=Both)."""
        command = self.eup_protocol.build_image_flip_mode(mode, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_image_flip_horizontal(self, camera: int, enable: bool) -> bool:
        """Enable/disable horizontal flip."""
        command = self.eup_protocol.build_image_flip_horizontal(enable, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_image_flip_vertical(self, camera: int, enable: bool) -> bool:
        """Enable/disable vertical flip."""
        command = self.eup_protocol.build_image_flip_vertical(enable, camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # RTSP/Video stream configuration commands
    async def send_video_stream_enable(self, camera: int, stream: int, enable: bool) -> bool:
        """Send video stream enable/disable command."""
        command = self.eup_protocol.build_video_stream_enable(camera, stream, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_rtsp_suffix(self, camera: int, stream: int, suffix: str) -> bool:
        """Send RTSP suffix command."""
        command = self.eup_protocol.build_rtsp_suffix(camera, stream, suffix)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_resolution(self, camera: int, stream: int, width: int, height: int) -> bool:
        """Send video resolution command."""
        command = self.eup_protocol.build_video_resolution(camera, stream, width, height)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_bitrate(self, camera: int, stream: int, bitrate: int) -> bool:
        """Send video bitrate command."""
        command = self.eup_protocol.build_video_bitrate(camera, stream, bitrate)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_bitrate_mode(self, camera: int, stream: int, variable: bool) -> bool:
        """Send video bitrate mode command."""
        command = self.eup_protocol.build_video_bitrate_mode(camera, stream, variable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_fps(self, camera: int, stream: int, fps: int) -> bool:
        """Send video FPS command."""
        command = self.eup_protocol.build_video_fps(camera, stream, fps)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_gop(self, camera: int, stream: int, gop: int) -> bool:
        """Send video GOP command."""
        command = self.eup_protocol.build_video_gop(camera, stream, gop)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_codec(self, camera: int, stream: int, codec: str) -> bool:
        """Send video codec command."""
        command = self.eup_protocol.build_video_codec(camera, stream, codec)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_h264_profile(self, camera: int, stream: int, profile: int) -> bool:
        """Send H264 profile command."""
        command = self.eup_protocol.build_h264_profile(camera, stream, profile)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_query_video_settings(self, camera: int, stream: int) -> bool:
        """Query video stream settings."""
        queries = [
            self.eup_protocol.query_video_resolution(camera, stream),
            self.eup_protocol.query_video_bitrate(camera, stream),
            self.eup_protocol.query_video_fps(camera, stream),
            self.eup_protocol.query_video_codec(camera, stream),
            self.eup_protocol.query_rtsp_suffix(camera, stream)
        ]
        for query in queries:
            await self.send_command(query, use_udp=True)
        return True

    # ========== RTSP/VideoStream Phase 2 Commands ==========

    async def send_video_stream_disable(self, camera: int, stream: int) -> bool:
        """Disable video stream."""
        command = self.eup_protocol.build_video_stream_disable(camera, stream)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_stream_restart(self, camera: int, stream: int) -> bool:
        """Restart video stream."""
        command = self.eup_protocol.build_video_stream_restart(camera, stream)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_rtsp_port(self, camera: int, stream: int, port: int) -> bool:
        """Send RTSP port command."""
        command = self.eup_protocol.build_rtsp_port(camera, stream, port)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_rtsp_multicast_ip(self, camera: int, stream: int, ip: str) -> bool:
        """Send RTSP multicast IP command."""
        command = self.eup_protocol.build_rtsp_multicast_ip(camera, stream, ip)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_rtsp_multicast_port(self, camera: int, stream: int, port: int) -> bool:
        """Send RTSP multicast port command."""
        command = self.eup_protocol.build_rtsp_multicast_port(camera, stream, port)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_rtsp_user(self, camera: int, stream: int, user: str) -> bool:
        """Send RTSP username command."""
        command = self.eup_protocol.build_rtsp_user(camera, stream, user)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_rtsp_password(self, camera: int, stream: int, password: str) -> bool:
        """Send RTSP password command."""
        command = self.eup_protocol.build_rtsp_password(camera, stream, password)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_resolution(self, camera: int, stream: int, resolution: str) -> bool:
        """Send resolution command."""
        command = self.eup_protocol.build_resolution(camera, stream, resolution)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_codec(self, camera: int, stream: int, codec: str) -> bool:
        """Send codec command."""
        command = self.eup_protocol.build_codec(camera, stream, codec)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_h264_profile(self, camera: int, stream: int, profile: str) -> bool:
        """Send H264 profile command."""
        command = self.eup_protocol.build_h264_profile(camera, stream, profile)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_jpeg_quality(self, camera: int, stream: int, quality: int) -> bool:
        """Send JPEG quality command."""
        command = self.eup_protocol.build_jpeg_quality(camera, stream, quality)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_bitrate(self, camera: int, stream: int, bitrate_kbps: int) -> bool:
        """Send bitrate command."""
        command = self.eup_protocol.build_bitrate(camera, stream, bitrate_kbps)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_bitrate_mode(self, camera: int, stream: int, mode: str) -> bool:
        """Send bitrate mode command."""
        command = self.eup_protocol.build_bitrate_mode(camera, stream, mode)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_min_bitrate(self, camera: int, stream: int, bitrate_kbps: int) -> bool:
        """Send minimum bitrate command."""
        command = self.eup_protocol.build_min_bitrate(camera, stream, bitrate_kbps)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_max_bitrate(self, camera: int, stream: int, bitrate_kbps: int) -> bool:
        """Send maximum bitrate command."""
        command = self.eup_protocol.build_max_bitrate(camera, stream, bitrate_kbps)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_fps(self, camera: int, stream: int, fps: int) -> bool:
        """Send FPS command."""
        command = self.eup_protocol.build_fps(camera, stream, fps)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_gop(self, camera: int, stream: int, gop: int) -> bool:
        """Send GOP command."""
        command = self.eup_protocol.build_gop(camera, stream, gop)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_fit_mode(self, camera: int, stream: int, mode: str) -> bool:
        """Send fit mode command."""
        command = self.eup_protocol.build_fit_mode(camera, stream, mode)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_overlay_mode(self, camera: int, stream: int, enable: bool) -> bool:
        """Send overlay mode command."""
        command = self.eup_protocol.build_overlay_mode(camera, stream, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_metadata_mode(self, camera: int, stream: int, enable: bool) -> bool:
        """Send metadata mode command."""
        command = self.eup_protocol.build_metadata_mode(camera, stream, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_metadata_suffix(self, camera: int, stream: int, suffix: str) -> bool:
        """Send metadata suffix command."""
        command = self.eup_protocol.build_metadata_suffix(camera, stream, suffix)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_rtp_mode(self, camera: int, stream: int, enable: bool) -> bool:
        """Send RTP mode command."""
        command = self.eup_protocol.build_rtp_mode(camera, stream, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_rtp_port(self, camera: int, stream: int, port: int) -> bool:
        """Send RTP port command."""
        command = self.eup_protocol.build_rtp_port(camera, stream, port)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_rtp_dest_ip(self, camera: int, stream: int, ip: str) -> bool:
        """Send RTP destination IP command."""
        command = self.eup_protocol.build_rtp_dest_ip(camera, stream, ip)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_rtmp_mode(self, camera: int, stream: int, enable: bool) -> bool:
        """Send RTMP mode command."""
        command = self.eup_protocol.build_rtmp_mode(camera, stream, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_rtmp_port(self, camera: int, stream: int, port: int) -> bool:
        """Send RTMP port command."""
        command = self.eup_protocol.build_rtmp_port(camera, stream, port)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_hls_mode(self, camera: int, stream: int, enable: bool) -> bool:
        """Send HLS mode command."""
        command = self.eup_protocol.build_hls_mode(camera, stream, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_hls_port(self, camera: int, stream: int, port: int) -> bool:
        """Send HLS port command."""
        command = self.eup_protocol.build_hls_port(camera, stream, port)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_srt_mode(self, camera: int, stream: int, enable: bool) -> bool:
        """Send SRT mode command."""
        command = self.eup_protocol.build_srt_mode(camera, stream, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_srt_port(self, camera: int, stream: int, port: int) -> bool:
        """Send SRT port command."""
        command = self.eup_protocol.build_srt_port(camera, stream, port)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_udp_payload_size(self, camera: int, stream: int, size: int) -> bool:
        """Send UDP payload size command."""
        command = self.eup_protocol.build_udp_payload_size(camera, stream, size)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_query_video_stream_settings(self, camera: int, stream: int) -> bool:
        """Query video stream settings."""
        command = self.eup_protocol.query_video_stream_settings(camera, stream)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== Overlay Control Commands ==========

    async def send_crosshair_mode(self, camera: int, enable: bool) -> bool:
        """Send crosshair mode command."""
        command = self.eup_protocol.build_crosshair_mode(camera, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_crosshair_size(self, camera: int, size: int) -> bool:
        """Send crosshair size command."""
        command = self.eup_protocol.build_crosshair_size(camera, size)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_crosshair_color(self, camera: int, color: str) -> bool:
        """Send crosshair color command."""
        command = self.eup_protocol.build_crosshair_color(camera, color)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_datetime_overlay(self, camera: int, enable: bool) -> bool:
        """Send date/time overlay command."""
        command = self.eup_protocol.build_datetime_overlay(camera, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_zoom_pos_overlay(self, camera: int, enable: bool) -> bool:
        """Send zoom position overlay command."""
        command = self.eup_protocol.build_zoom_pos_overlay(camera, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_focus_mode_overlay(self, camera: int, enable: bool) -> bool:
        """Send focus mode overlay command."""
        command = self.eup_protocol.build_focus_mode_overlay(camera, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_digital_zoom_overlay(self, camera: int, enable: bool) -> bool:
        """Send digital zoom overlay command."""
        command = self.eup_protocol.build_digital_zoom_overlay(camera, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_clahe_overlay(self, camera: int, enable: bool) -> bool:
        """Send CLAHE overlay command."""
        command = self.eup_protocol.build_clahe_overlay(camera, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_tracker_overlay(self, camera: int, enable: bool) -> bool:
        """Send tracker overlay command."""
        command = self.eup_protocol.build_tracker_overlay(camera, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_pan_tilt_overlay(self, camera: int, enable: bool) -> bool:
        """Send pan/tilt overlay command."""
        command = self.eup_protocol.build_pan_tilt_overlay(camera, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_lrf_overlay(self, camera: int, enable: bool) -> bool:
        """Send LRF overlay command."""
        command = self.eup_protocol.build_lrf_overlay(camera, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_webrtc_overlay(self, camera: int, enable: bool) -> bool:
        """Send WebRTC overlay command."""
        command = self.eup_protocol.build_webrtc_overlay(camera, enable)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== Motion Magnificator Commands ==========

    async def send_motion_magnificator_enable(self, camera: int) -> bool:
        """Enable motion magnificator."""
        command = self.eup_protocol.build_motion_magnificator_enable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_magnificator_disable(self, camera: int) -> bool:
        """Disable motion magnificator."""
        command = self.eup_protocol.build_motion_magnificator_disable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_magnificator_level(self, camera: int, level: int) -> bool:
        """Send motion magnificator level."""
        command = self.eup_protocol.build_motion_magnificator_level(camera, level)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== VideoTracker Commands ==========

    async def send_video_tracker_reset(self, camera: int) -> bool:
        """Reset video tracker."""
        command = self.eup_protocol.build_video_tracker_reset(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_tracker_enable(self, camera: int) -> bool:
        """Enable video tracker."""
        command = self.eup_protocol.build_video_tracker_enable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_tracker_disable(self, camera: int) -> bool:
        """Disable video tracker."""
        command = self.eup_protocol.build_video_tracker_disable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_tracker_lock(self, camera: int) -> bool:
        """Lock video tracker."""
        command = self.eup_protocol.build_video_tracker_lock(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_tracker_unlock(self, camera: int) -> bool:
        """Unlock video tracker."""
        command = self.eup_protocol.build_video_tracker_unlock(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_tracker_mode(self, camera: int, mode: str) -> bool:
        """Send video tracker mode."""
        command = self.eup_protocol.build_video_tracker_mode(camera, mode)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_tracker_object_size(self, camera: int, size: int) -> bool:
        """Send tracker object size."""
        command = self.eup_protocol.build_video_tracker_object_size(camera, size)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_video_tracker_search_area_size(self, camera: int, size: int) -> bool:
        """Send tracker search area size."""
        command = self.eup_protocol.build_video_tracker_search_area_size(camera, size)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== MotionDetector Commands ==========

    async def send_motion_detector_reset(self, camera: int) -> bool:
        """Reset motion detector."""
        command = self.eup_protocol.build_motion_detector_reset(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_detector_enable(self, camera: int) -> bool:
        """Enable motion detector."""
        command = self.eup_protocol.build_motion_detector_enable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_detector_disable(self, camera: int) -> bool:
        """Disable motion detector."""
        command = self.eup_protocol.build_motion_detector_disable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_detector_frame_buffer(self, camera: int, buffer: int) -> bool:
        """Send motion detector frame buffer."""
        command = self.eup_protocol.build_motion_detector_frame_buffer(camera, buffer)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_detector_min_width(self, camera: int, width: int) -> bool:
        """Send motion detector minimum width."""
        command = self.eup_protocol.build_motion_detector_min_width(camera, width)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_detector_max_width(self, camera: int, width: int) -> bool:
        """Send motion detector maximum width."""
        command = self.eup_protocol.build_motion_detector_max_width(camera, width)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_detector_min_height(self, camera: int, height: int) -> bool:
        """Send motion detector minimum height."""
        command = self.eup_protocol.build_motion_detector_min_height(camera, height)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_detector_max_height(self, camera: int, height: int) -> bool:
        """Send motion detector maximum height."""
        command = self.eup_protocol.build_motion_detector_max_height(camera, height)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_detector_x_criteria(self, camera: int, criteria: int) -> bool:
        """Send motion detector X criteria."""
        command = self.eup_protocol.build_motion_detector_x_criteria(camera, criteria)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_detector_y_criteria(self, camera: int, criteria: int) -> bool:
        """Send motion detector Y criteria."""
        command = self.eup_protocol.build_motion_detector_y_criteria(camera, criteria)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_detector_reset_criteria(self, camera: int) -> bool:
        """Reset motion detector criteria."""
        command = self.eup_protocol.build_motion_detector_reset_criteria(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_detector_sensitivity(self, camera: int, sensitivity: int) -> bool:
        """Send motion detector sensitivity."""
        command = self.eup_protocol.build_motion_detector_sensitivity(camera, sensitivity)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_motion_detector_mode(self, camera: int, mode: str) -> bool:
        """Send motion detector mode."""
        command = self.eup_protocol.build_motion_detector_mode(camera, mode)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== ChangesDetector Commands ==========

    async def send_changes_detector_reset(self, camera: int) -> bool:
        """Reset changes detector."""
        command = self.eup_protocol.build_changes_detector_reset(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_changes_detector_enable(self, camera: int) -> bool:
        """Enable changes detector."""
        command = self.eup_protocol.build_changes_detector_enable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_changes_detector_disable(self, camera: int) -> bool:
        """Disable changes detector."""
        command = self.eup_protocol.build_changes_detector_disable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_changes_detector_frame_buffer(self, camera: int, buffer: int) -> bool:
        """Send changes detector frame buffer."""
        command = self.eup_protocol.build_changes_detector_frame_buffer(camera, buffer)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_changes_detector_min_width(self, camera: int, width: int) -> bool:
        """Send changes detector minimum width."""
        command = self.eup_protocol.build_changes_detector_min_width(camera, width)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_changes_detector_max_width(self, camera: int, width: int) -> bool:
        """Send changes detector maximum width."""
        command = self.eup_protocol.build_changes_detector_max_width(camera, width)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_changes_detector_min_height(self, camera: int, height: int) -> bool:
        """Send changes detector minimum height."""
        command = self.eup_protocol.build_changes_detector_min_height(camera, height)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_changes_detector_max_height(self, camera: int, height: int) -> bool:
        """Send changes detector maximum height."""
        command = self.eup_protocol.build_changes_detector_max_height(camera, height)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_changes_detector_x_criteria(self, camera: int, criteria: int) -> bool:
        """Send changes detector X criteria."""
        command = self.eup_protocol.build_changes_detector_x_criteria(camera, criteria)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_changes_detector_y_criteria(self, camera: int, criteria: int) -> bool:
        """Send changes detector Y criteria."""
        command = self.eup_protocol.build_changes_detector_y_criteria(camera, criteria)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_changes_detector_reset_criteria(self, camera: int) -> bool:
        """Reset changes detector criteria."""
        command = self.eup_protocol.build_changes_detector_reset_criteria(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_changes_detector_sensitivity(self, camera: int, sensitivity: int) -> bool:
        """Send changes detector sensitivity."""
        command = self.eup_protocol.build_changes_detector_sensitivity(camera, sensitivity)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_changes_detector_mode(self, camera: int, mode: str) -> bool:
        """Send changes detector mode."""
        command = self.eup_protocol.build_changes_detector_mode(camera, mode)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== Classification Commands ==========

    async def send_classification_enable(self, camera: int) -> bool:
        """Enable classification."""
        command = self.eup_protocol.build_classification_enable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_classification_disable(self, camera: int) -> bool:
        """Disable classification."""
        command = self.eup_protocol.build_classification_disable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_classification_model(self, camera: int, model: str) -> bool:
        """Send classification model."""
        command = self.eup_protocol.build_classification_model(camera, model)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_classification_confidence(self, camera: int, confidence: int) -> bool:
        """Send classification confidence threshold."""
        command = self.eup_protocol.build_classification_confidence(camera, confidence)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_query_classification_status(self, camera: int) -> bool:
        """Query classification status."""
        command = self.eup_protocol.query_classification_status(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== License Query Commands ==========

    async def send_query_video_tracker_token(self) -> bool:
        """Query video tracker token."""
        command = self.eup_protocol.query_video_tracker_token()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_query_video_tracker_license_status(self) -> bool:
        """Query video tracker license status."""
        command = self.eup_protocol.query_video_tracker_license_status()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_query_video_stabiliser_token(self) -> bool:
        """Query video stabiliser token."""
        command = self.eup_protocol.query_video_stabiliser_token()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_query_video_stabiliser_license_status(self) -> bool:
        """Query video stabiliser license status."""
        command = self.eup_protocol.query_video_stabiliser_license_status()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_query_motion_detector_token(self) -> bool:
        """Query motion detector token."""
        command = self.eup_protocol.query_motion_detector_token()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_query_motion_detector_license_status(self) -> bool:
        """Query motion detector license status."""
        command = self.eup_protocol.query_motion_detector_license_status()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_query_changes_detector_token(self) -> bool:
        """Query changes detector token."""
        command = self.eup_protocol.query_changes_detector_token()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_query_changes_detector_license_status(self) -> bool:
        """Query changes detector license status."""
        command = self.eup_protocol.query_changes_detector_license_status()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_query_classification_token(self) -> bool:
        """Query classification token."""
        command = self.eup_protocol.query_classification_token()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_query_classification_license_status(self) -> bool:
        """Query classification license status."""
        command = self.eup_protocol.query_classification_license_status()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== Detection Subscription Commands ==========

    async def send_subscribe_objects_events(self, camera: int) -> bool:
        """Subscribe to detection objects/events."""
        command = self.eup_protocol.subscribe_objects_events(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== ProcedureManager Commands ==========

    async def send_procedure_load(self, procedure_name: str) -> bool:
        """Send procedure load command."""
        command = self.eup_protocol.build_procedure_load(procedure_name)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_procedure_execute(self) -> bool:
        """Send procedure execute command."""
        command = self.eup_protocol.build_procedure_execute()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_procedure_stop(self) -> bool:
        """Send procedure stop command."""
        command = self.eup_protocol.build_procedure_stop()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def query_procedure_status(self) -> bool:
        """Query procedure status."""
        command = self.eup_protocol.query_procedure_status()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== BadPixelProcessor Commands ==========

    async def send_bad_pixel_enable(self, camera: int) -> bool:
        """Send bad pixel enable command."""
        command = self.eup_protocol.build_bad_pixel_enable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_bad_pixel_disable(self, camera: int) -> bool:
        """Send bad pixel disable command."""
        command = self.eup_protocol.build_bad_pixel_disable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_bad_pixel_calibrate(self, camera: int) -> bool:
        """Send bad pixel calibrate command."""
        command = self.eup_protocol.build_bad_pixel_calibrate(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_bad_pixel_threshold(self, camera: int, threshold: float) -> bool:
        """Send bad pixel threshold command."""
        command = self.eup_protocol.build_bad_pixel_threshold(camera, threshold)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def query_bad_pixel_settings(self, camera: int) -> bool:
        """Query bad pixel settings."""
        command = self.eup_protocol.query_bad_pixel_settings(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== VideoSource Commands ==========

    async def send_video_source(self, camera: int, source_id: str) -> bool:
        """Send video source command."""
        command = self.eup_protocol.build_video_source(camera, source_id)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def query_video_source(self, camera: int) -> bool:
        """Query video source."""
        command = self.eup_protocol.query_video_source(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== WebRtcOverlay Commands ==========

    async def send_webrtc_overlay_enable(self, camera: int) -> bool:
        """Send webrtc overlay enable command."""
        command = self.eup_protocol.build_webrtc_overlay_enable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_webrtc_overlay_disable(self, camera: int) -> bool:
        """Send webrtc overlay disable command."""
        command = self.eup_protocol.build_webrtc_overlay_disable(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def query_webrtc_overlay_settings(self, camera: int) -> bool:
        """Query webrtc overlay settings."""
        command = self.eup_protocol.query_webrtc_overlay_settings(camera)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== ExternalUp Commands ==========

    async def send_external_up_enable(self) -> bool:
        """Send external up enable command."""
        command = self.eup_protocol.build_external_up_enable()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_external_up_disable(self) -> bool:
        """Send external up disable command."""
        command = self.eup_protocol.build_external_up_disable()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_external_up_port(self, port: int) -> bool:
        """Send external up port command."""
        command = self.eup_protocol.build_external_up_port(port)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_external_up_address(self, address: str) -> bool:
        """Send external up address command."""
        command = self.eup_protocol.build_external_up_address(address)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def query_external_up_settings(self) -> bool:
        """Query external up settings."""
        command = self.eup_protocol.query_external_up_settings()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== PelcoD Commands ==========

    async def send_pelco_d_enable(self) -> bool:
        """Send pelco d enable command."""
        command = self.eup_protocol.build_pelco_d_enable()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_pelco_d_disable(self) -> bool:
        """Send pelco d disable command."""
        command = self.eup_protocol.build_pelco_d_disable()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_pelco_d_port(self, port: int) -> bool:
        """Send pelco d port command."""
        command = self.eup_protocol.build_pelco_d_port(port)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_pelco_d_address(self, address: str) -> bool:
        """Send pelco d address command."""
        command = self.eup_protocol.build_pelco_d_address(address)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def query_pelco_d_settings(self) -> bool:
        """Query pelco d settings."""
        command = self.eup_protocol.query_pelco_d_settings()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def receive_telemetry(self):
        """
        Receive EUP responses (string-based protocol).
        Responses are: Ack, Nac, or Reply messages.
        Also periodically queries position to update telemetry.
        """
        logger.info("Starting telemetry reception loop")
        self.running = True

        # Track position separately
        current_pan = None
        current_tilt = None

        # Position query interval (seconds)
        query_interval = 1.0  # Query position at 1Hz (reduced from 10Hz to prevent flooding)
        last_query_time = 0.0

        while self.running and self.connected:
            try:
                await asyncio.sleep(0.1)  # 100ms sleep (reduced CPU usage)

                # Periodically send position queries to get telemetry updates
                import time
                current_time = time.time()
                if current_time - last_query_time >= query_interval:
                    await self.send_position_query()
                    last_query_time = current_time

                # Try reading from TCP if available
                if self.tcp_reader:
                    try:
                        # Check if data is available without blocking
                        if not self.tcp_reader.at_eof():
                            line = await asyncio.wait_for(self.tcp_reader.readline(), timeout=0.001)
                            if line:
                                response_str = line.decode('utf-8', errors='ignore').strip()
                                if response_str:
                                    logger.debug(f"Received EUP response (TCP): {response_str}")

                                    # Parse position responses
                                    parsed = self.eup_protocol.parse_position_response(response_str)
                                    if parsed:
                                        pan, tilt = parsed
                                        if pan is not None:
                                            current_pan = pan
                                            logger.debug(f"Updated pan position: {current_pan}°")
                                        if tilt is not None:
                                            current_tilt = tilt
                                            logger.debug(f"Updated tilt position: {current_tilt}°")

                                        # Send telemetry update if we have both values
                                        if current_pan is not None and current_tilt is not None:
                                            logger.debug(f"Emitting telemetry: pan={current_pan}°, tilt={current_tilt}°")
                                            telemetry = TelemetryData(
                                                pan_position=current_pan,
                                                tilt_position=current_tilt
                                            )
                                            if self.telemetry_callback:
                                                self.telemetry_callback(telemetry)
                                        else:
                                            logger.debug(f"Waiting for both values: pan={current_pan}, tilt={current_tilt}")

                                    # Parse system info responses
                                    system_info = self.eup_protocol.parse_system_info_response(response_str)
                                    if system_info and self.system_info_callback:
                                        info_type, value = system_info
                                        self.system_info_callback(info_type, value)
                    except asyncio.TimeoutError:
                        pass  # No data available

                # Also try UDP
                if self.udp_socket:
                    try:
                        data, addr = self.udp_socket.recvfrom(1024)
                        if data:
                            # EUP responses are strings
                            response_str = data.decode('utf-8', errors='ignore').strip()

                            if response_str:
                                logger.debug(f"Received EUP response (UDP): {response_str}")

                                # Parse position responses
                                parsed = self.eup_protocol.parse_position_response(response_str)
                                if parsed:
                                    pan, tilt = parsed
                                    if pan is not None:
                                        current_pan = pan
                                        logger.debug(f"Updated pan position (UDP): {current_pan}°")
                                    if tilt is not None:
                                        current_tilt = tilt
                                        logger.debug(f"Updated tilt position (UDP): {current_tilt}°")

                                    # Send telemetry update if we have both values
                                    if current_pan is not None and current_tilt is not None:
                                        logger.debug(f"Emitting telemetry (UDP): pan={current_pan}°, tilt={current_tilt}°")
                                        telemetry = TelemetryData(
                                            pan_position=current_pan,
                                            tilt_position=current_tilt
                                        )
                                        if self.telemetry_callback:
                                            self.telemetry_callback(telemetry)
                                    else:
                                        logger.debug(f"Waiting for both values (UDP): pan={current_pan}, tilt={current_tilt}")

                                # Parse system info responses
                                system_info = self.eup_protocol.parse_system_info_response(response_str)
                                if system_info and self.system_info_callback:
                                    info_type, value = system_info
                                    self.system_info_callback(info_type, value)

                    except BlockingIOError:
                        pass

            except Exception as e:
                logger.error(f"Error receiving telemetry: {e}")
                await asyncio.sleep(1)

        logger.info("Telemetry reception loop stopped")

    async def run(self):
        # This method is deprecated - connection is now managed by explicit
        # connect/disconnect calls from the GUI
        logger.warning("NetworkManager.run() is deprecated and should not be called")
        pass

    # ========== Phase 4A: Lrf Commands ==========

    async def send_lrf_fire(self) -> bool:
        """Send LRF fire command."""
        command = self.eup_protocol.build_lrf_fire()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_lrf_mode(self, mode: str) -> bool:
        """Send LRF mode command."""
        command = self.eup_protocol.build_lrf_mode(mode)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def query_lrf_range(self) -> bool:
        """Query LRF range."""
        command = self.eup_protocol.query_lrf_range()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def query_lrf_settings(self) -> bool:
        """Query LRF settings."""
        command = self.eup_protocol.query_lrf_settings()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== Phase 4A: Speaker Commands ==========

    async def send_speaker_play(self, clip_name: str) -> bool:
        """Send speaker play command."""
        command = self.eup_protocol.build_speaker_play(clip_name)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_speaker_stop(self) -> bool:
        """Send speaker stop command."""
        command = self.eup_protocol.build_speaker_stop()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_speaker_volume(self, volume: int) -> bool:
        """Send speaker volume command."""
        command = self.eup_protocol.build_speaker_volume(volume)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def query_speaker_status(self) -> bool:
        """Query speaker status."""
        command = self.eup_protocol.query_speaker_status()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== Phase 4A: G5Laser Commands ==========

    async def send_g5_laser_enable(self) -> bool:
        """Send G5 laser enable command."""
        command = self.eup_protocol.build_g5_laser_enable()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_g5_laser_disable(self) -> bool:
        """Send G5 laser disable command."""
        command = self.eup_protocol.build_g5_laser_disable()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_g5_laser_intensity(self, intensity: int) -> bool:
        """Send G5 laser intensity command."""
        command = self.eup_protocol.build_g5_laser_intensity(intensity)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def query_g5_laser_settings(self) -> bool:
        """Query G5 laser settings."""
        command = self.eup_protocol.query_g5_laser_settings()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== Phase 4A: PeakBeam Commands ==========

    async def send_peakbeam_enable(self) -> bool:
        """Send PeakBeam enable command."""
        command = self.eup_protocol.build_peakbeam_enable()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_peakbeam_disable(self) -> bool:
        """Send PeakBeam disable command."""
        command = self.eup_protocol.build_peakbeam_disable()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_peakbeam_intensity(self, intensity: int) -> bool:
        """Send PeakBeam intensity command."""
        command = self.eup_protocol.build_peakbeam_intensity(intensity)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_peakbeam_mode(self, mode: str) -> bool:
        """Send PeakBeam mode command."""
        command = self.eup_protocol.build_peakbeam_mode(mode)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def query_peakbeam_settings(self) -> bool:
        """Query PeakBeam settings."""
        command = self.eup_protocol.query_peakbeam_settings()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    # ========== Phase 4A: Companion Commands ==========

    async def send_companion_command(self, command: str) -> bool:
        """Send Companion command."""
        eup_command = self.eup_protocol.build_companion_command(command)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(eup_command, use_udp=not use_tcp)

    async def send_companion_enable(self) -> bool:
        """Send Companion enable command."""
        command = self.eup_protocol.build_companion_enable()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_companion_disable(self) -> bool:
        """Send Companion disable command."""
        command = self.eup_protocol.build_companion_disable()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_companion_reset(self) -> bool:
        """Send Companion reset command."""
        command = self.eup_protocol.build_companion_reset()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def query_companion_status(self) -> bool:
        """Query Companion status."""
        command = self.eup_protocol.query_companion_status()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)
