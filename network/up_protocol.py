import struct
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from utils.logger import setup_logger

logger = setup_logger()

class UPProtocol:
    MAGIC_BYTES = 0x5550
    HEADER_SIZE = 8

    def __init__(self):
        self.sequence_number = 0
        self.commands = self._load_commands()

    def _load_commands(self) -> Dict:
        try:
            from utils.constants import get_resource_path
            config_path = get_resource_path("config/up_protocol_commands.json")
        except ImportError:
            config_path = Path("config/up_protocol_commands.json")

        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}

    def _calculate_crc16(self, data: bytes) -> int:
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    def _build_header(self, command_id: int, payload_length: int) -> bytes:
        self.sequence_number = (self.sequence_number + 1) % 65536

        header = struct.pack(
            '>HHHH',
            self.MAGIC_BYTES,
            self.sequence_number,
            command_id,
            payload_length
        )
        return header

    def build_pan_tilt_command(self, pan_degrees: float, tilt_degrees: float) -> bytes:
        command_id = self.commands.get('commands', {}).get('pan_tilt_absolute', {}).get('command_id', 1)

        pan_value = int(pan_degrees * 100)
        tilt_value = int(tilt_degrees * 100)

        payload = struct.pack('>ii', pan_value, tilt_value)

        header = self._build_header(command_id, len(payload))

        message = header + payload

        checksum = self._calculate_crc16(message)
        message += struct.pack('>H', checksum)

        logger.debug(f"Built pan/tilt command: pan={pan_degrees}°, tilt={tilt_degrees}°, len={len(message)}")
        return message

    def build_position_query(self) -> bytes:
        command_id = self.commands.get('commands', {}).get('query_position', {}).get('command_id', 10)

        header = self._build_header(command_id, 0)

        checksum = self._calculate_crc16(header)
        message = header + struct.pack('>H', checksum)

        logger.debug(f"Built position query command, len={len(message)}")
        return message

    def build_stop_command(self) -> bytes:
        command_id = self.commands.get('commands', {}).get('stop_movement', {}).get('command_id', 5)

        header = self._build_header(command_id, 0)

        checksum = self._calculate_crc16(header)
        message = header + struct.pack('>H', checksum)

        logger.debug(f"Built stop command, len={len(message)}")
        return message

    def build_zoom_command(self, zoom_speed: float) -> bytes:
        """
        Build zoom command.
        zoom_speed: -1.0 (zoom out) to +1.0 (zoom in)
        """
        command_id = self.commands.get('commands', {}).get('zoom', {}).get('command_id', 3)

        zoom_value = int(zoom_speed * 100)
        payload = struct.pack('>i', zoom_value)

        header = self._build_header(command_id, len(payload))
        message = header + payload

        checksum = self._calculate_crc16(message)
        message += struct.pack('>H', checksum)

        logger.debug(f"Built zoom command: speed={zoom_speed}, len={len(message)}")
        return message

    def build_focus_command(self, focus_speed: float) -> bytes:
        """
        Build focus command.
        focus_speed: -1.0 (near) to +1.0 (far)
        """
        command_id = self.commands.get('commands', {}).get('focus', {}).get('command_id', 4)

        focus_value = int(focus_speed * 100)
        payload = struct.pack('>i', focus_value)

        header = self._build_header(command_id, len(payload))
        message = header + payload

        checksum = self._calculate_crc16(message)
        message += struct.pack('>H', checksum)

        logger.debug(f"Built focus command: speed={focus_speed}, len={len(message)}")
        return message

    def parse_message(self, data: bytes) -> Optional[Dict]:
        if len(data) < self.HEADER_SIZE + 2:
            logger.warning(f"Message too short: {len(data)} bytes")
            return None

        try:
            magic, seq, cmd_id, payload_len = struct.unpack('>HHHH', data[:self.HEADER_SIZE])

            if magic != self.MAGIC_BYTES:
                logger.warning(f"Invalid magic bytes: 0x{magic:04X}")
                return None

            if len(data) < self.HEADER_SIZE + payload_len + 2:
                logger.warning(f"Incomplete message: expected {self.HEADER_SIZE + payload_len + 2}, got {len(data)}")
                return None

            payload = data[self.HEADER_SIZE:self.HEADER_SIZE + payload_len]
            received_checksum = struct.unpack('>H', data[self.HEADER_SIZE + payload_len:self.HEADER_SIZE + payload_len + 2])[0]

            calculated_checksum = self._calculate_crc16(data[:self.HEADER_SIZE + payload_len])

            if received_checksum != calculated_checksum:
                logger.warning(f"Checksum mismatch: expected 0x{calculated_checksum:04X}, got 0x{received_checksum:04X}")
                return None

            return {
                'sequence': seq,
                'command_id': cmd_id,
                'payload': payload,
                'payload_length': payload_len
            }

        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None

    def parse_position_response(self, data: bytes) -> Optional[Tuple[float, float]]:
        parsed = self.parse_message(data)
        if not parsed:
            return None

        try:
            payload = parsed['payload']
            if len(payload) < 8:
                logger.warning(f"Position response payload too short: {len(payload)} bytes")
                return None

            pan_raw, tilt_raw = struct.unpack('>ii', payload[:8])

            pan_degrees = pan_raw / 100.0
            tilt_degrees = tilt_raw / 100.0

            logger.debug(f"Parsed position: pan={pan_degrees}°, tilt={tilt_degrees}°")
            return pan_degrees, tilt_degrees

        except Exception as e:
            logger.error(f"Error parsing position response: {e}")
            return None
