import asyncio
import socket
from typing import Optional, Callable
from network.up_protocol import UPProtocol
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

        self.up_protocol = UPProtocol()

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
            logger.info(f"Attempting TCP connection to {self.target_ip}:{self.tcp_port}")
            self.tcp_reader, self.tcp_writer = await asyncio.wait_for(
                asyncio.open_connection(self.target_ip, self.tcp_port),
                timeout=5.0
            )
            logger.info("TCP connection established")

            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.bind(('0.0.0.0', self.udp_telemetry_port))
            self.udp_socket.setblocking(False)
            logger.info(f"UDP telemetry socket bound to port {self.udp_telemetry_port}")

            self.up_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            logger.info(f"UP protocol UDP socket created for port {self.up_protocol_port}")

            self.connected = True
            if self.connection_status_callback:
                self.connection_status_callback(True)

            return True

        except asyncio.TimeoutError:
            logger.error(f"Connection timeout to {self.target_ip}:{self.tcp_port}")
            self.connected = False
            if self.connection_status_callback:
                self.connection_status_callback(False)
            return False

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

    async def send_command(self, command_bytes: bytes, use_udp: bool = True) -> bool:
        if not self.connected:
            logger.warning("Cannot send command: not connected")
            return False

        try:
            if use_udp:
                if self.up_udp_socket:
                    self.up_udp_socket.sendto(command_bytes, (self.target_ip, self.up_protocol_port))
                    logger.debug(f"Sent UDP command to {self.target_ip}:{self.up_protocol_port}, {len(command_bytes)} bytes")
                    return True
            else:
                if self.tcp_writer:
                    self.tcp_writer.write(command_bytes)
                    await self.tcp_writer.drain()
                    logger.debug(f"Sent TCP command, {len(command_bytes)} bytes")
                    return True

        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False

        return False

    async def send_pan_tilt(self, pan: float, tilt: float) -> bool:
        command = self.up_protocol.build_pan_tilt_command(pan, tilt)
        return await self.send_command(command, use_udp=True)

    async def send_position_query(self) -> bool:
        command = self.up_protocol.build_position_query()
        return await self.send_command(command, use_udp=True)

    async def send_stop(self) -> bool:
        command = self.up_protocol.build_stop_command()
        return await self.send_command(command, use_udp=True)

    async def send_zoom(self, zoom_speed: float) -> bool:
        """Send zoom command. zoom_speed: -1.0 (out) to +1.0 (in)"""
        command = self.up_protocol.build_zoom_command(zoom_speed)
        return await self.send_command(command, use_udp=True)

    async def send_focus(self, focus_speed: float) -> bool:
        """Send focus command. focus_speed: -1.0 (near) to +1.0 (far)"""
        command = self.up_protocol.build_focus_command(focus_speed)
        return await self.send_command(command, use_udp=True)

    async def receive_telemetry(self):
        logger.info("Starting telemetry reception loop")
        self.running = True

        while self.running and self.connected:
            try:
                if self.udp_socket:
                    await asyncio.sleep(0.01)

                    try:
                        data, addr = self.udp_socket.recvfrom(1024)
                        if data:
                            logger.debug(f"Received telemetry: {len(data)} bytes from {addr}")
                            telemetry = TelemetryData.from_bytes(data)

                            parsed = self.up_protocol.parse_position_response(data)
                            if parsed:
                                pan, tilt = parsed
                                telemetry.pan_position = pan
                                telemetry.tilt_position = tilt

                            if self.telemetry_callback:
                                self.telemetry_callback(telemetry)

                    except BlockingIOError:
                        pass

            except Exception as e:
                logger.error(f"Error receiving telemetry: {e}")
                await asyncio.sleep(1)

        logger.info("Telemetry reception loop stopped")

    async def run(self):
        while True:
            if not self.connected:
                logger.info("Attempting to connect...")
                await self.connect()

                if self.connected:
                    asyncio.create_task(self.receive_telemetry())

            await asyncio.sleep(5)
