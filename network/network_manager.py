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
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.bind(('0.0.0.0', self.udp_telemetry_port))
            self.udp_socket.setblocking(False)
            logger.info(f"UDP telemetry socket bound to port {self.udp_telemetry_port}")

            self.up_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            logger.info(f"UP protocol UDP socket created for port {self.up_protocol_port}")

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

        if self.up_udp_socket:
            self.up_udp_socket.close()

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
        await self.send_command(pan_query, use_udp=True)
        await self.send_command(tilt_query, use_udp=True)
        return True

    async def send_stop(self) -> bool:
        """Stop all gimbal movement."""
        command = self.eup_protocol.build_stop_command()
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_zoom(self, zoom_direction: float, camera: str = "Camera1") -> bool:
        """Send zoom command. zoom_direction: -1.0 (out), +1.0 (in), camera: Camera1/Camera2/Camera3"""
        direction = int(zoom_direction)  # Convert to -1, 0, or +1
        # Extract camera number from "Camera1", "Camera2", "Camera3"
        camera_num = int(camera.replace("Camera", ""))
        command = self.eup_protocol.build_zoom_command(direction, camera=camera_num)
        use_tcp = self.tcp_writer is not None
        return await self.send_command(command, use_udp=not use_tcp)

    async def send_focus(self, focus_direction: float, camera: str = "Camera1") -> bool:
        """Send focus command. focus_direction: -1.0 (near), +1.0 (far), camera: Camera1/Camera2/Camera3"""
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

    async def receive_telemetry(self):
        """
        Receive EUP responses (string-based protocol).
        Responses are: Ack, Nac, or Reply messages.
        """
        logger.info("Starting telemetry reception loop")
        self.running = True

        # Track position separately
        current_pan = None
        current_tilt = None

        while self.running and self.connected:
            try:
                await asyncio.sleep(0.01)

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
                                        if tilt is not None:
                                            current_tilt = tilt

                                        # Send telemetry update if we have both values
                                        if current_pan is not None and current_tilt is not None:
                                            telemetry = TelemetryData(
                                                pan_position=current_pan,
                                                tilt_position=current_tilt
                                            )
                                            if self.telemetry_callback:
                                                self.telemetry_callback(telemetry)
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
                                    if tilt is not None:
                                        current_tilt = tilt

                                    # Send telemetry update if we have both values
                                    if current_pan is not None and current_tilt is not None:
                                        telemetry = TelemetryData(
                                            pan_position=current_pan,
                                            tilt_position=current_tilt
                                        )
                                        if self.telemetry_callback:
                                            self.telemetry_callback(telemetry)

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
