"""
network/eup_protocol.py
External Universal Protocol (EUP) - String-based implementation.

This is the CORRECT protocol for MK4 systems as per External_UP_protocol_v2.4.7.pdf
Format: ID:N/MessageType/Module/Submodule/Parameter\n
"""

from typing import Optional, Dict, Any
from utils.logger import setup_logger

logger = setup_logger()


class EUPProtocol:
    """
    External Universal Protocol (EUP) - String-based commands.

    Message format: ID:<sequence>/MessageType/Module/Submodule/Parameter\n

    Message Types:
        - Command: Trigger action or set parameter
        - Query: Request current value
        - Reply: Response to Query with data
        - Ack: Acknowledgment of successful Command
        - Nac: Negative acknowledgment (error)
    """

    def __init__(self):
        self.sequence_number = 0

    def _get_next_id(self) -> int:
        """Get next sequence number."""
        self.sequence_number = (self.sequence_number + 1) % 10000
        return self.sequence_number

    def _build_command(self, module: str, submodule: str, parameter: str, value: Optional[str] = None) -> str:
        """
        Build a command string.

        Args:
            module: Module name (e.g., "MotorControl", "Camera1")
            submodule: Submodule name (e.g., "Pan", "Lens")
            parameter: Parameter or action (e.g., "ToPos", "ZoomIn")
            value: Optional value for parameter (e.g., "120.5")

        Returns:
            Command string with newline: "ID:N/Command/Module/Submodule/Parameter:Value\n"
        """
        seq_id = self._get_next_id()

        if value is not None:
            cmd = f"ID:{seq_id}/Command/{module}/{submodule}/{parameter}:{value}\n"
        else:
            cmd = f"ID:{seq_id}/Command/{module}/{submodule}/{parameter}\n"

        logger.debug(f"Built EUP command: {cmd.strip()}")
        return cmd

    def _build_query(self, module: str, submodule: str, parameter: str) -> str:
        """
        Build a query string.

        Args:
            module: Module name
            submodule: Submodule name
            parameter: Parameter to query

        Returns:
            Query string with newline: "ID:N/Query/Module/Submodule/Parameter\n"
        """
        seq_id = self._get_next_id()
        query = f"ID:{seq_id}/Query/{module}/{submodule}/{parameter}\n"

        logger.debug(f"Built EUP query: {query.strip()}")
        return query

    # ========== MotorControl Commands ==========

    def build_pan_tilt_absolute(self, pan_degrees: float, tilt_degrees: float) -> str:
        """
        Build absolute pan/tilt position command.

        Args:
            pan_degrees: Pan position in degrees (-180 to +180)
            tilt_degrees: Tilt position in degrees (-90 to +90)

        Returns:
            Command string
        """
        # Note: This sends two separate commands (pan and tilt)
        # You could also send them together if needed
        pan_cmd = self._build_command("MotorControl", "Pan", "ToPos", str(pan_degrees))
        tilt_cmd = self._build_command("MotorControl", "Tilt", "ToPos", str(tilt_degrees))

        logger.debug(f"Built pan/tilt absolute: pan={pan_degrees}°, tilt={tilt_degrees}°")
        return pan_cmd + tilt_cmd

    def build_pan_command(self, pan_degrees: float) -> str:
        """Build pan position command."""
        return self._build_command("MotorControl", "Pan", "ToPos", str(pan_degrees))

    def build_tilt_command(self, tilt_degrees: float) -> str:
        """Build tilt position command."""
        return self._build_command("MotorControl", "Tilt", "ToPos", str(tilt_degrees))

    def build_pan_speed(self, speed: float) -> str:
        """
        Build pan speed command.

        Args:
            speed: Speed in degrees/second (negative for left, positive for right)

        Returns:
            Command string using AtDps (At Degrees Per Second) parameter
        """
        if speed == 0:
            return self._build_command("MotorControl", "Pan", "Stop")
        elif speed > 0:
            return self._build_command("MotorControl", "Pan/Right", "AtDps", str(abs(speed)))
        else:
            return self._build_command("MotorControl", "Pan/Left", "AtDps", str(abs(speed)))

    def build_tilt_speed(self, speed: float) -> str:
        """
        Build tilt speed command.

        Args:
            speed: Speed in degrees/second (negative for down, positive for up)

        Returns:
            Command string using AtDps (At Degrees Per Second) parameter
        """
        if speed == 0:
            return self._build_command("MotorControl", "Tilt", "Stop")
        elif speed > 0:
            return self._build_command("MotorControl", "Tilt/Up", "AtDps", str(abs(speed)))
        else:
            return self._build_command("MotorControl", "Tilt/Down", "AtDps", str(abs(speed)))

    def build_stop_command(self) -> str:
        """Build stop movement command."""
        # Stop both pan and tilt
        pan_stop = self._build_command("MotorControl", "Pan", "Stop")
        tilt_stop = self._build_command("MotorControl", "Tilt", "Stop")
        return pan_stop + tilt_stop

    def query_pan_position(self) -> str:
        """Query current pan position."""
        return self._build_query("MotorControl", "Pan", "Pos")

    def query_tilt_position(self) -> str:
        """Query current tilt position."""
        return self._build_query("MotorControl", "Tilt", "Pos")

    # ========== Camera/Lens Commands ==========

    def build_zoom_command(self, direction: int, camera: int = 1) -> str:
        """
        Build zoom command.

        Args:
            direction: +1 for zoom in (tele), -1 for zoom out (wide)
            camera: Camera number (1, 2, or 3)

        Returns:
            Command string
        """
        if direction > 0:
            action = "ZoomIn"
        elif direction < 0:
            action = "ZoomOut"
        else:
            action = "ZoomStop"

        return self._build_command(f"Camera{camera}", "Lens", action)

    def build_zoom_to_position(self, position: int, camera: int = 1) -> str:
        """
        Build zoom to absolute position command.

        Args:
            position: Zoom position (0-max, hardware dependent)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Lens", "ZoomToPos", str(position))

    def build_focus_command(self, direction: int, camera: int = 1) -> str:
        """
        Build focus command.

        Args:
            direction: +1 for far, -1 for near
            camera: Camera number
        """
        if direction > 0:
            action = "FocusFar"
        elif direction < 0:
            action = "FocusNear"
        else:
            action = "FocusStop"

        return self._build_command(f"Camera{camera}", "Lens", action)

    def build_autofocus(self, camera: int = 1) -> str:
        """Enable autofocus for camera."""
        return self._build_command(f"Camera{camera}", "Lens", "AfMode", "1")

    # ========== Camera Control Commands ==========

    def build_camera_profile(self, profile: int, camera: int = 1) -> str:
        """
        Set camera profile/preset.

        Args:
            profile: Profile number (0-N, hardware dependent)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "Profile", str(profile))

    def build_video_stabilizer(self, enable: bool, camera: int = 1) -> str:
        """Enable/disable video stabilization."""
        action = "On" if enable else "Off"
        return self._build_command(f"Camera{camera}", "VideoStabiliser", action)

    def build_digital_zoom(self, level: float, camera: int = 1) -> str:
        """
        Set digital zoom level.

        Args:
            level: Zoom level (1.0 = no zoom, 2.0 = 2x, etc.)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "DigitalZoom", "Level", str(level))

    def enable_digital_zoom(self, camera: int = 1) -> str:
        """Enable digital zoom."""
        return self._build_command(f"Camera{camera}", "DigitalZoom", "On")

    def disable_digital_zoom(self, camera: int = 1) -> str:
        """Disable digital zoom."""
        return self._build_command(f"Camera{camera}", "DigitalZoom", "Off")

    # ========== Image Enhancement Commands ==========

    def build_clahe(self, enable: bool, camera: int = 1) -> str:
        """Enable/disable CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        action = "On" if enable else "Off"
        return self._build_command(f"Camera{camera}", "Clahe", action)

    def build_color_palette(self, palette: int, camera: int = 1) -> str:
        """
        Set color palette (for thermal cameras).

        Args:
            palette: Palette number (0=Normal, 1=Inverse, etc.)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "ColorFilter", "Palette", str(palette))

    def enable_color_filter(self, camera: int = 1) -> str:
        """Enable color filter."""
        return self._build_command(f"Camera{camera}", "ColorFilter", "On")

    def disable_color_filter(self, camera: int = 1) -> str:
        """Disable color filter."""
        return self._build_command(f"Camera{camera}", "ColorFilter", "Off")

    # ========== General System Commands ==========

    def build_slave_zoom_mode(self, enable: bool) -> str:
        """Enable/disable slave zoom mode (all cameras zoom together)."""
        value = "1" if enable else "0"
        return self._build_command("General", "", "SlaveZoomMode", value)

    # ========== Parser for Responses ==========

    def parse_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse a response message.

        Expected formats:
            - ID:N/Ack
            - ID:N/Nac
            - ID:N/Reply/Module/Submodule/Parameter:Value

        Args:
            response: Response string (may or may not have trailing \n)

        Returns:
            Parsed response dict or None if invalid
        """
        try:
            response = response.strip()

            if not response.startswith("ID:"):
                logger.warning(f"Invalid response format: {response}")
                return None

            parts = response.split('/')

            if len(parts) < 2:
                logger.warning(f"Response too short: {response}")
                return None

            # Extract ID
            id_part = parts[0]  # "ID:N"
            seq_id = int(id_part.split(':')[1])

            msg_type = parts[1]  # Ack, Nac, Reply

            result = {
                'id': seq_id,
                'type': msg_type,
                'raw': response
            }

            if msg_type == "Reply" and len(parts) >= 5:
                # ID:N/Reply/Module/Submodule/Parameter:Value
                result['module'] = parts[2]
                result['submodule'] = parts[3]

                # Parameter may have value after ':'
                param_part = parts[4]
                if ':' in param_part:
                    param, value = param_part.split(':', 1)
                    result['parameter'] = param
                    result['value'] = value
                else:
                    result['parameter'] = param_part
                    result['value'] = None

            logger.debug(f"Parsed response: {result}")
            return result

        except Exception as e:
            logger.error(f"Error parsing response '{response}': {e}")
            return None

    def parse_position_response(self, response: str) -> Optional[tuple[float, float]]:
        """
        Parse position reply messages.

        Expected format:
            ID:N/Reply/MotorControl/Pan/Pos:120.5
            ID:N/Reply/MotorControl/Tilt/Pos:-45.2

        Returns:
            (pan, tilt) tuple or None
        """
        parsed = self.parse_response(response)

        if not parsed or parsed['type'] != 'Reply':
            return None

        if parsed.get('module') == 'MotorControl':
            submodule = parsed.get('submodule')
            value = parsed.get('value')

            if submodule == 'Pan' and value:
                try:
                    pan = float(value)
                    return (pan, None)
                except ValueError:
                    pass
            elif submodule == 'Tilt' and value:
                try:
                    tilt = float(value)
                    return (None, tilt)
                except ValueError:
                    pass

        return None
