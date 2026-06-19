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

    # ========== MotorControl Zero Position Commands ==========

    def build_pan_set_zero(self) -> str:
        """Set current pan position as zero reference."""
        return self._build_command("MotorControl", "Pan", "SetZero")

    def build_pan_reset_zero(self) -> str:
        """Reset pan zero position to factory default."""
        return self._build_command("MotorControl", "Pan", "ResetZero")

    def build_pan_zero_pos(self, degrees: float) -> str:
        """
        Set pan zero position offset.

        Args:
            degrees: Zero position offset in degrees
        """
        return self._build_command("MotorControl", "Pan", "ZeroPos", str(degrees))

    def build_pan_add_pos(self, degrees: float) -> str:
        """
        Add offset to current pan position.

        Args:
            degrees: Position offset to add (can be negative)
        """
        return self._build_command("MotorControl", "Pan", "AddPos", str(degrees))

    def build_tilt_set_zero(self) -> str:
        """Set current tilt position as zero reference."""
        return self._build_command("MotorControl", "Tilt", "SetZero")

    def build_tilt_reset_zero(self) -> str:
        """Reset tilt zero position to factory default."""
        return self._build_command("MotorControl", "Tilt", "ResetZero")

    def build_tilt_zero_pos(self, degrees: float) -> str:
        """
        Set tilt zero position offset.

        Args:
            degrees: Zero position offset in degrees
        """
        return self._build_command("MotorControl", "Tilt", "ZeroPos", str(degrees))

    def build_tilt_add_pos(self, degrees: float) -> str:
        """
        Add offset to current tilt position.

        Args:
            degrees: Position offset to add (can be negative)
        """
        return self._build_command("MotorControl", "Tilt", "AddPos", str(degrees))

    # ========== MotorControl Speed & Movement Settings ==========

    def build_pan_max_speed(self, dps: float) -> str:
        """
        Set pan maximum speed limit.

        Args:
            dps: Maximum speed in degrees per second
        """
        return self._build_command("MotorControl", "Pan", "MaxSpeed", str(dps))

    def build_pan_position_speed(self, dps: float) -> str:
        """
        Set pan speed for position moves (ToPos commands).

        Args:
            dps: Position move speed in degrees per second
        """
        return self._build_command("MotorControl", "Pan", "PositionSpeed", str(dps))

    def build_pan_invert_movement(self, enable: bool) -> str:
        """
        Invert pan movement direction.

        Args:
            enable: True to invert, False for normal
        """
        value = "On" if enable else "Off"
        return self._build_command("MotorControl", "Pan", "InvertMovement", value)

    def build_tilt_max_speed(self, dps: float) -> str:
        """
        Set tilt maximum speed limit.

        Args:
            dps: Maximum speed in degrees per second
        """
        return self._build_command("MotorControl", "Tilt", "MaxSpeed", str(dps))

    def build_tilt_position_speed(self, dps: float) -> str:
        """
        Set tilt speed for position moves (ToPos commands).

        Args:
            dps: Position move speed in degrees per second
        """
        return self._build_command("MotorControl", "Tilt", "PositionSpeed", str(dps))

    def build_tilt_invert_movement(self, enable: bool) -> str:
        """
        Invert tilt movement direction.

        Args:
            enable: True to invert, False for normal
        """
        value = "On" if enable else "Off"
        return self._build_command("MotorControl", "Tilt", "InvertMovement", value)

    # ========== MotorControl System Settings ==========

    def build_block_pt(self, enable: bool) -> str:
        """
        Block pan/tilt movement (safety lock).

        Args:
            enable: True to block movement, False to allow
        """
        value = "On" if enable else "Off"
        return self._build_command("MotorControl", "", "BlockPT", value)

    def build_zoom_dependent_mode(self, mode: int) -> str:
        """
        Set zoom-dependent speed mode (slower movement at high zoom).

        Args:
            mode: 0=Off, 1=On
        """
        return self._build_command("MotorControl", "", "ZoomDependentMode", str(mode))

    def build_acc_vel_max(self, value: int) -> str:
        """
        Set maximum acceleration velocity.

        Args:
            value: Maximum acceleration velocity (hardware units)
        """
        return self._build_command("MotorControl", "", "AccVelMax", str(value))

    def build_acc_dec_max(self, value: int) -> str:
        """
        Set maximum deceleration.

        Args:
            value: Maximum deceleration (hardware units)
        """
        return self._build_command("MotorControl", "", "AccDecMax", str(value))

    def build_acc_dec_rate(self, value: int) -> str:
        """
        Set acceleration/deceleration rate.

        Args:
            value: Acceleration rate (hardware units)
        """
        return self._build_command("MotorControl", "", "AccDecRate", str(value))

    def build_acc_dec_vstop(self, value: int) -> str:
        """
        Set velocity stop threshold for deceleration.

        Args:
            value: Velocity stop threshold (hardware units)
        """
        return self._build_command("MotorControl", "", "AccDecVstop", str(value))

    def build_reset_controller(self) -> str:
        """Reset motor controller to default settings."""
        return self._build_command("MotorControl", "", "ResetController")

    # ========== MotorControl Queries ==========

    def query_pan_max_speed(self) -> str:
        """Query pan maximum speed."""
        return self._build_query("MotorControl", "Pan", "MaxSpeed")

    def query_pan_position_speed(self) -> str:
        """Query pan position move speed."""
        return self._build_query("MotorControl", "Pan", "PositionSpeed")

    def query_pan_zero_pos(self) -> str:
        """Query pan zero position offset."""
        return self._build_query("MotorControl", "Pan", "ZeroPos")

    def query_pan_invert_movement(self) -> str:
        """Query pan movement inversion status."""
        return self._build_query("MotorControl", "Pan", "InvertMovement")

    def query_tilt_max_speed(self) -> str:
        """Query tilt maximum speed."""
        return self._build_query("MotorControl", "Tilt", "MaxSpeed")

    def query_tilt_position_speed(self) -> str:
        """Query tilt position move speed."""
        return self._build_query("MotorControl", "Tilt", "PositionSpeed")

    def query_tilt_zero_pos(self) -> str:
        """Query tilt zero position offset."""
        return self._build_query("MotorControl", "Tilt", "ZeroPos")

    def query_tilt_invert_movement(self) -> str:
        """Query tilt movement inversion status."""
        return self._build_query("MotorControl", "Tilt", "InvertMovement")

    def query_block_pt(self) -> str:
        """Query pan/tilt block status."""
        return self._build_query("MotorControl", "", "BlockPT")

    def query_zoom_dependent_mode(self) -> str:
        """Query zoom-dependent mode status."""
        return self._build_query("MotorControl", "", "ZoomDependentMode")

    def query_acc_vel_max(self) -> str:
        """Query acceleration velocity maximum."""
        return self._build_query("MotorControl", "", "AccVelMax")

    def query_acc_dec_max(self) -> str:
        """Query deceleration maximum."""
        return self._build_query("MotorControl", "", "AccDecMax")

    def query_acc_dec_rate(self) -> str:
        """Query acceleration/deceleration rate."""
        return self._build_query("MotorControl", "", "AccDecRate")

    def query_acc_dec_vstop(self) -> str:
        """Query velocity stop threshold."""
        return self._build_query("MotorControl", "", "AccDecVstop")

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

    def build_focus_to_position(self, position: int, camera: int = 1) -> str:
        """
        Build focus to absolute position command.

        Args:
            position: Focus position (0-max, hardware dependent)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Lens", "FocusToPos", str(position))

    def build_one_push_af(self, camera: int = 1) -> str:
        """
        Trigger one-time autofocus (one-push AF).

        Per EUP Protocol v2.4.7 Section 4.2.1 (Lens Control):
        - RunAf: Start autofocus (one-push autofocus)
        - StopAf: Stop autofocus

        Args:
            camera: Camera number

        Returns:
            Command string: ID:N/Command/Camera{X}/Lens/RunAf
        """
        return self._build_command(f"Camera{camera}", "Lens", "RunAf")

    def build_stop_af(self, camera: int = 1) -> str:
        """
        Stop autofocus operation.

        Args:
            camera: Camera number

        Returns:
            Command string: ID:N/Command/Camera{X}/Lens/StopAf
        """
        return self._build_command(f"Camera{camera}", "Lens", "StopAf")

    def build_zoom_speed(self, speed: int, camera: int = 1) -> str:
        """
        Set zoom speed (how fast zoom moves when ZoomIn/ZoomOut commands are sent).

        Args:
            speed: Speed value [0-100%] of max hardware zoom speed
            camera: Camera number

        Returns:
            Command string: ID:N/Command/Camera{X}/Lens/ZoomSpeed:{speed}
        """
        return self._build_command(f"Camera{camera}", "Lens", "ZoomSpeed", str(speed))

    def build_focus_speed(self, speed: int, camera: int = 1) -> str:
        """
        Set focus speed (how fast focus moves when FocusFar/FocusNear commands are sent).

        Args:
            speed: Speed value [0-100%] of max hardware focus speed
            camera: Camera number

        Returns:
            Command string: ID:N/Command/Camera{X}/Lens/FocusSpeed:{speed}
        """
        return self._build_command(f"Camera{camera}", "Lens", "FocusSpeed", str(speed))

    def build_focus_speed_multiplier(self, multiplier: float, camera: int = 1) -> str:
        """
        Set focus speed multiplier.

        Args:
            multiplier: Speed multiplier (e.g., 0.5 = half speed, 2.0 = double speed)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Lens", "FocusSpeedMultiplier", str(multiplier))

    def build_zoom_speed_multiplier(self, multiplier: float, camera: int = 1) -> str:
        """
        Set zoom speed multiplier.

        Args:
            multiplier: Speed multiplier (e.g., 0.5 = half speed, 2.0 = double speed)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Lens", "ZoomSpeedMultiplier", str(multiplier))

    def build_tele_end_pos(self, position: int, camera: int = 1) -> str:
        """
        Set telephoto end position limit.

        Args:
            position: Maximum zoom position
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Lens", "TeleEndPos", str(position))

    def build_wide_end_pos(self, position: int, camera: int = 1) -> str:
        """
        Set wide angle end position limit.

        Args:
            position: Minimum zoom position
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Lens", "WideEndPos", str(position))

    def build_far_end_pos(self, position: int, camera: int = 1) -> str:
        """
        Set far focus end position limit.

        Args:
            position: Maximum focus position
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Lens", "FarEndPos", str(position))

    def build_near_end_pos(self, position: int, camera: int = 1) -> str:
        """
        Set near focus end position limit.

        Args:
            position: Minimum focus position
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Lens", "NearEndPos", str(position))

    # ========== Iris Control ==========

    def build_iris_open(self, camera: int = 1) -> str:
        """Open iris (continuous)."""
        return self._build_command(f"Camera{camera}", "Lens", "IrisOpen")

    def build_iris_close(self, camera: int = 1) -> str:
        """Close iris (continuous)."""
        return self._build_command(f"Camera{camera}", "Lens", "IrisClose")

    def build_iris_stop(self, camera: int = 1) -> str:
        """Stop iris movement."""
        return self._build_command(f"Camera{camera}", "Lens", "IrisStop")

    def build_iris_to_pos(self, position: int, camera: int = 1) -> str:
        """
        Move iris to absolute position.

        Args:
            position: Iris position (0-max, hardware dependent)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Lens", "IrisToPos", str(position))

    def build_iris_mode(self, mode: int, camera: int = 1) -> str:
        """
        Set iris mode.

        Args:
            mode: 0=Manual, 1=Auto
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Lens", "IrisMode", str(mode))

    def build_iris_value(self, f_stop: float, camera: int = 1) -> str:
        """
        Set iris F-stop value (manual mode).

        Args:
            f_stop: F-stop value (e.g., 2.8, 5.6, 11.0)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Lens", "Iris", str(f_stop))

    # ========== Camera Control Commands ==========

    def build_camera_profile(self, profile: int, camera: int = 1) -> str:
        """
        Set camera profile/preset.

        Args:
            profile: Profile number (0-N, hardware dependent)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "Profile", str(profile))

    # ========== Camera Exposure Settings ==========

    def build_exposure_mode(self, mode: int, camera: int = 1) -> str:
        """
        Set exposure mode.

        Args:
            mode: 0=Full Auto, 1=Manual, 2=Shutter Priority, 3=Iris Priority
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "ExposureMode", str(mode))

    def build_shutter_speed(self, speed: int, camera: int = 1) -> str:
        """
        Set shutter speed.

        Args:
            speed: Shutter speed value (hardware dependent, e.g., 1/60, 1/1000)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "ShutterSpeed", str(speed))

    def build_gain(self, gain: int, camera: int = 1) -> str:
        """
        Set gain value.

        Args:
            gain: Gain value in dB (0-max, hardware dependent)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "Gain", str(gain))

    def build_auto_mode(self, mode: int, camera: int = 1) -> str:
        """
        Set auto exposure mode.

        Args:
            mode: Auto exposure mode (0=Off, 1=On)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "AutoMode", str(mode))

    # ========== Camera White Balance Settings ==========

    def build_white_balance(self, mode: int, camera: int = 1) -> str:
        """
        Set white balance mode.

        Args:
            mode: 0=Auto, 1=Indoor, 2=Outdoor, 3=OnePush, 4=Manual
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "WhiteBalance", str(mode))

    def build_wb_red_gain(self, gain: int, camera: int = 1) -> str:
        """
        Set white balance red gain (manual mode).

        Args:
            gain: Red gain value (0-255)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "WbRedGain", str(gain))

    def build_wb_blue_gain(self, gain: int, camera: int = 1) -> str:
        """
        Set white balance blue gain (manual mode).

        Args:
            gain: Blue gain value (0-255)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "WbBlueGain", str(gain))

    def build_color_mode(self, mode: int, camera: int = 1) -> str:
        """
        Set color mode.

        Args:
            mode: 0=Color, 1=Black & White
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "ColorMode", str(mode))

    # ========== Camera Image Enhancement Settings ==========

    def build_brightness(self, value: int, camera: int = 1) -> str:
        """
        Set brightness level.

        Args:
            value: Brightness value (0-255, 128=neutral)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "Brightness", str(value))

    def build_contrast(self, value: int, camera: int = 1) -> str:
        """
        Set contrast level.

        Args:
            value: Contrast value (0-255, 128=neutral)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "Contrast", str(value))

    def build_saturation(self, value: int, camera: int = 1) -> str:
        """
        Set color saturation level.

        Args:
            value: Saturation value (0-255, 128=neutral)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "Saturation", str(value))

    def build_sharpness(self, value: int, camera: int = 1) -> str:
        """
        Set sharpness level.

        Args:
            value: Sharpness value (0-255, 128=neutral)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "Sharpness", str(value))

    def build_backlight_compensation(self, mode: int, camera: int = 1) -> str:
        """
        Set backlight compensation mode.

        Args:
            mode: 0=Off, 1=On
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "BacklightCompensation", str(mode))

    def build_wide_dynamic_range(self, mode: int, camera: int = 1) -> str:
        """
        Set wide dynamic range (WDR) mode.

        Args:
            mode: 0=Off, 1=On
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "WideDynamicRange", str(mode))

    def build_noise_reduction(self, level: int, camera: int = 1) -> str:
        """
        Set noise reduction level.

        Args:
            level: Noise reduction level (0=Off, 1-5=Low to High)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "NoiseReduction", str(level))

    def build_defog_mode(self, mode: int, camera: int = 1) -> str:
        """
        Set defog/haze reduction mode.

        Args:
            mode: 0=Off, 1=On
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Camera", "DefogMode", str(mode))

    # ========== Camera Setting Queries ==========

    def query_exposure_mode(self, camera: int = 1) -> str:
        """Query exposure mode."""
        return self._build_query(f"Camera{camera}", "Camera", "ExposureMode")

    def query_shutter_speed(self, camera: int = 1) -> str:
        """Query shutter speed."""
        return self._build_query(f"Camera{camera}", "Camera", "ShutterSpeed")

    def query_gain(self, camera: int = 1) -> str:
        """Query gain value."""
        return self._build_query(f"Camera{camera}", "Camera", "Gain")

    def query_auto_mode(self, camera: int = 1) -> str:
        """Query auto exposure mode."""
        return self._build_query(f"Camera{camera}", "Camera", "AutoMode")

    def query_white_balance(self, camera: int = 1) -> str:
        """Query white balance mode."""
        return self._build_query(f"Camera{camera}", "Camera", "WhiteBalance")

    def query_wb_red_gain(self, camera: int = 1) -> str:
        """Query white balance red gain."""
        return self._build_query(f"Camera{camera}", "Camera", "WbRedGain")

    def query_wb_blue_gain(self, camera: int = 1) -> str:
        """Query white balance blue gain."""
        return self._build_query(f"Camera{camera}", "Camera", "WbBlueGain")

    def query_color_mode(self, camera: int = 1) -> str:
        """Query color mode."""
        return self._build_query(f"Camera{camera}", "Camera", "ColorMode")

    def query_brightness(self, camera: int = 1) -> str:
        """Query brightness level."""
        return self._build_query(f"Camera{camera}", "Camera", "Brightness")

    def query_contrast(self, camera: int = 1) -> str:
        """Query contrast level."""
        return self._build_query(f"Camera{camera}", "Camera", "Contrast")

    def query_saturation(self, camera: int = 1) -> str:
        """Query saturation level."""
        return self._build_query(f"Camera{camera}", "Camera", "Saturation")

    def query_sharpness(self, camera: int = 1) -> str:
        """Query sharpness level."""
        return self._build_query(f"Camera{camera}", "Camera", "Sharpness")

    def query_backlight_compensation(self, camera: int = 1) -> str:
        """Query backlight compensation mode."""
        return self._build_query(f"Camera{camera}", "Camera", "BacklightCompensation")

    def query_wide_dynamic_range(self, camera: int = 1) -> str:
        """Query wide dynamic range mode."""
        return self._build_query(f"Camera{camera}", "Camera", "WideDynamicRange")

    def query_noise_reduction(self, camera: int = 1) -> str:
        """Query noise reduction level."""
        return self._build_query(f"Camera{camera}", "Camera", "NoiseReduction")

    def query_defog_mode(self, camera: int = 1) -> str:
        """Query defog mode."""
        return self._build_query(f"Camera{camera}", "Camera", "DefogMode")

    def query_iris_mode(self, camera: int = 1) -> str:
        """Query iris mode."""
        return self._build_query(f"Camera{camera}", "Lens", "IrisMode")

    def query_iris_pos(self, camera: int = 1) -> str:
        """Query iris position."""
        return self._build_query(f"Camera{camera}", "Lens", "IrisPos")

    def query_focus_pos(self, camera: int = 1) -> str:
        """Query focus position."""
        return self._build_query(f"Camera{camera}", "Lens", "FocusPos")

    def query_zoom_pos(self, camera: int = 1) -> str:
        """Query zoom position."""
        return self._build_query(f"Camera{camera}", "Lens", "ZoomPos")

    def build_video_stabilizer(self, enable: bool, camera: int = 1) -> str:
        """Enable/disable video stabilization."""
        action = "On" if enable else "Off"
        return self._build_command(f"Camera{camera}", "VideoStabiliser", action)

    # ========== VideoStabiliser Advanced Settings ==========

    def build_stabilizer_x_offset_limit(self, limit: int, camera: int = 1) -> str:
        """
        Set horizontal offset limit for stabilization.

        Args:
            limit: Maximum horizontal offset in pixels
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "VideoStabiliser", "XOffsetLimit", str(limit))

    def build_stabilizer_y_offset_limit(self, limit: int, camera: int = 1) -> str:
        """
        Set vertical offset limit for stabilization.

        Args:
            limit: Maximum vertical offset in pixels
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "VideoStabiliser", "YOffsetLimit", str(limit))

    def build_stabilizer_a_offset_limit(self, limit: int, camera: int = 1) -> str:
        """
        Set angular offset limit for stabilization.

        Args:
            limit: Maximum angular offset in degrees (scaled)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "VideoStabiliser", "AOffsetLimit", str(limit))

    def build_stabilizer_mode(self, mode: int, camera: int = 1) -> str:
        """
        Set stabilizer mode.

        Args:
            mode: 0=Off, 1=Pan/Tilt, 2=Pan/Tilt/Rotation
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "VideoStabiliser", "Mode", str(mode))

    def build_stabilizer_type(self, stabilizer_type: int, camera: int = 1) -> str:
        """
        Set stabilizer algorithm type.

        Args:
            stabilizer_type: Stabilizer algorithm type (0-N, hardware dependent)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "VideoStabiliser", "Type", str(stabilizer_type))

    def build_stabilizer_transparent_border(self, enable: bool, camera: int = 1) -> str:
        """
        Enable/disable transparent border mode (show stabilization borders).

        Args:
            enable: True to show borders, False to hide
            camera: Camera number
        """
        value = "1" if enable else "0"
        return self._build_command(f"Camera{camera}", "VideoStabiliser", "TransparentBorderMode", value)

    def build_stabilizer_const_x_offset(self, offset: int, camera: int = 1) -> str:
        """
        Set constant horizontal offset.

        Args:
            offset: Constant X offset in pixels
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "VideoStabiliser", "ConstXOffset", str(offset))

    def build_stabilizer_const_y_offset(self, offset: int, camera: int = 1) -> str:
        """
        Set constant vertical offset.

        Args:
            offset: Constant Y offset in pixels
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "VideoStabiliser", "ConstYOffset", str(offset))

    def build_stabilizer_const_a_offset(self, offset: int, camera: int = 1) -> str:
        """
        Set constant angular offset.

        Args:
            offset: Constant angular offset in degrees (scaled)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "VideoStabiliser", "ConstAOffset", str(offset))

    # ========== VideoStabiliser Queries ==========

    def query_stabilizer_x_offset_limit(self, camera: int = 1) -> str:
        """Query horizontal offset limit."""
        return self._build_query(f"Camera{camera}", "VideoStabiliser", "XOffsetLimit")

    def query_stabilizer_y_offset_limit(self, camera: int = 1) -> str:
        """Query vertical offset limit."""
        return self._build_query(f"Camera{camera}", "VideoStabiliser", "YOffsetLimit")

    def query_stabilizer_a_offset_limit(self, camera: int = 1) -> str:
        """Query angular offset limit."""
        return self._build_query(f"Camera{camera}", "VideoStabiliser", "AOffsetLimit")

    def query_stabilizer_mode(self, camera: int = 1) -> str:
        """Query stabilizer mode."""
        return self._build_query(f"Camera{camera}", "VideoStabiliser", "Mode")

    def query_stabilizer_type(self, camera: int = 1) -> str:
        """Query stabilizer type."""
        return self._build_query(f"Camera{camera}", "VideoStabiliser", "Type")

    def query_stabilizer_transparent_border(self, camera: int = 1) -> str:
        """Query transparent border mode."""
        return self._build_query(f"Camera{camera}", "VideoStabiliser", "TransparentBorderMode")

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

    # ========== ImageFlip Control ==========

    def build_image_flip_mode(self, mode: int, camera: int = 1) -> str:
        """
        Set image flip mode.

        Args:
            mode: 0=Off, 1=Horizontal, 2=Vertical, 3=Both
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "ImageFlip", "Mode", str(mode))

    def build_image_flip_horizontal(self, enable: bool, camera: int = 1) -> str:
        """
        Enable/disable horizontal flip.

        Args:
            enable: True to flip horizontally
            camera: Camera number
        """
        value = "1" if enable else "0"
        return self._build_command(f"Camera{camera}", "ImageFlip", "Horizontal", value)

    def build_image_flip_vertical(self, enable: bool, camera: int = 1) -> str:
        """
        Enable/disable vertical flip.

        Args:
            enable: True to flip vertically
            camera: Camera number
        """
        value = "1" if enable else "0"
        return self._build_command(f"Camera{camera}", "ImageFlip", "Vertical", value)

    # ========== ImageFlip Queries ==========

    def query_image_flip_mode(self, camera: int = 1) -> str:
        """Query image flip mode."""
        return self._build_query(f"Camera{camera}", "ImageFlip", "Mode")

    def query_image_flip_horizontal(self, camera: int = 1) -> str:
        """Query horizontal flip status."""
        return self._build_query(f"Camera{camera}", "ImageFlip", "Horizontal")

    def query_image_flip_vertical(self, camera: int = 1) -> str:
        """Query vertical flip status."""
        return self._build_query(f"Camera{camera}", "ImageFlip", "Vertical")

    # ========== Image Enhancement Commands ==========

    def build_clahe(self, enable: bool, camera: int = 1) -> str:
        """Enable/disable CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        action = "On" if enable else "Off"
        return self._build_command(f"Camera{camera}", "Clahe", action)

    # ========== CLAHE Advanced Settings ==========

    def build_clahe_clip_limit(self, limit: float, camera: int = 1) -> str:
        """
        Set CLAHE clip limit.

        Args:
            limit: Clip limit (1.0-40.0, typical 2.0-4.0)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Clahe", "ClipLimit", str(limit))

    def build_clahe_tiles_grid_size(self, size: int, camera: int = 1) -> str:
        """
        Set CLAHE tile grid size.

        Args:
            size: Tile grid size (typically 8x8, 16x16)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "Clahe", "TilesGridSize", str(size))

    # ========== CLAHE Queries ==========

    def query_clahe_clip_limit(self, camera: int = 1) -> str:
        """Query CLAHE clip limit."""
        return self._build_query(f"Camera{camera}", "Clahe", "ClipLimit")

    def query_clahe_tiles_grid_size(self, camera: int = 1) -> str:
        """Query CLAHE tile grid size."""
        return self._build_query(f"Camera{camera}", "Clahe", "TilesGridSize")

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

    # ========== ColorFilter Advanced Settings ==========

    def build_color_filter_auto_mode(self, mode: int, camera: int = 1) -> str:
        """
        Set color filter auto mode.

        Args:
            mode: 0=Manual, 1=Auto
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "ColorFilter", "AutoMode", str(mode))

    def build_color_filter_hue(self, hue: int, camera: int = 1) -> str:
        """
        Set color filter hue.

        Args:
            hue: Hue value (0-360 degrees)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "ColorFilter", "Hue", str(hue))

    def build_color_filter_saturation(self, saturation: int, camera: int = 1) -> str:
        """
        Set color filter saturation.

        Args:
            saturation: Saturation value (0-255)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "ColorFilter", "Saturation", str(saturation))

    def build_color_filter_brightness(self, brightness: int, camera: int = 1) -> str:
        """
        Set color filter brightness.

        Args:
            brightness: Brightness value (0-255)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "ColorFilter", "Brightness", str(brightness))

    def build_color_filter_contrast(self, contrast: int, camera: int = 1) -> str:
        """
        Set color filter contrast.

        Args:
            contrast: Contrast value (0-255)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "ColorFilter", "Contrast", str(contrast))

    def build_color_filter_gamma(self, gamma: float, camera: int = 1) -> str:
        """
        Set color filter gamma.

        Args:
            gamma: Gamma value (0.1-5.0, 1.0=neutral)
            camera: Camera number
        """
        return self._build_command(f"Camera{camera}", "ColorFilter", "Gamma", str(gamma))

    # ========== ColorFilter Queries ==========

    def query_color_filter_auto_mode(self, camera: int = 1) -> str:
        """Query color filter auto mode."""
        return self._build_query(f"Camera{camera}", "ColorFilter", "AutoMode")

    def query_color_filter_hue(self, camera: int = 1) -> str:
        """Query color filter hue."""
        return self._build_query(f"Camera{camera}", "ColorFilter", "Hue")

    def query_color_filter_saturation(self, camera: int = 1) -> str:
        """Query color filter saturation."""
        return self._build_query(f"Camera{camera}", "ColorFilter", "Saturation")

    def query_color_filter_brightness(self, camera: int = 1) -> str:
        """Query color filter brightness."""
        return self._build_query(f"Camera{camera}", "ColorFilter", "Brightness")

    def query_color_filter_contrast(self, camera: int = 1) -> str:
        """Query color filter contrast."""
        return self._build_query(f"Camera{camera}", "ColorFilter", "Contrast")

    def query_color_filter_gamma(self, camera: int = 1) -> str:
        """Query color filter gamma."""
        return self._build_query(f"Camera{camera}", "ColorFilter", "Gamma")

    def query_color_filter_palette(self, camera: int = 1) -> str:
        """Query color filter palette."""
        return self._build_query(f"Camera{camera}", "ColorFilter", "Palette")

    # ========== General System Commands ==========

    def build_slave_zoom_mode(self, enable: bool) -> str:
        """Enable/disable slave zoom mode (all cameras zoom together)."""
        value = "1" if enable else "0"
        return self._build_command("General", "", "SlaveZoomMode", value)

    def build_slave_zoom_master_camera(self, camera: int) -> str:
        """
        Set slave zoom master camera (other cameras follow this one's zoom).

        Args:
            camera: 0=Camera1, 1=Camera2, 2=Camera3
        """
        return self._build_command("General", "", "SlaveZoomMasterCamera", str(camera))

    def query_slave_zoom_mode(self) -> str:
        """Query slave zoom mode status."""
        return self._build_query("General", "", "SlaveZoomMode")

    def query_slave_zoom_master_camera(self) -> str:
        """Query which camera is the slave zoom master."""
        return self._build_query("General", "", "SlaveZoomMasterCamera")

    def query_mainboard_serial(self) -> str:
        """
        Query mainboard serial number.

        Returns:
            Query string: ID:N/Query/General/Mainboard/serial
            Response: ID:N/Reply/General/Mainboard/serial:string
        """
        return self._build_query("General", "Mainboard", "serial")

    def query_nexos_version(self) -> str:
        """
        Query NexOS software version.

        Returns:
            Query string: ID:N/Query/General/Mainboard/versionNexOS
            Response: ID:N/Reply/General/Mainboard/versionNexOS:string
        """
        return self._build_query("General", "Mainboard", "versionNexOS")

    def query_tracking_enabled(self) -> str:
        """
        Query whether tracking is enabled.

        Returns:
            Query string: ID:N/Query/General/Mainboard/trackingEnabled
            Response: ID:N/Reply/General/Mainboard/trackingEnabled:string ("On" or "Off")
        """
        return self._build_query("General", "Mainboard", "trackingEnabled")

    # ========== MotorControl Configuration Commands ==========

    def build_pan_left_limit(self, degrees: float) -> str:
        """Set pan left limit (0-360 degrees)."""
        return self._build_command("MotorControl", "Pan", "LeftLimit", str(degrees))

    def build_pan_right_limit(self, degrees: float) -> str:
        """Set pan right limit (0-360 degrees)."""
        return self._build_command("MotorControl", "Pan", "RightLimit", str(degrees))

    def build_tilt_up_limit(self, degrees: float) -> str:
        """Set tilt up limit (-90 to +90 degrees)."""
        return self._build_command("MotorControl", "Tilt", "UpLimit", str(degrees))

    def build_tilt_down_limit(self, degrees: float) -> str:
        """Set tilt down limit (-90 to +90 degrees)."""
        return self._build_command("MotorControl", "Tilt", "DownLimit", str(degrees))

    def build_homing_delay_mode(self, enable: bool) -> str:
        """Enable/disable homing delay."""
        value = "1" if enable else "0"
        return self._build_command("MotorControl", "", "HomingDelay", value)

    def build_homing_delay_time(self, seconds: int) -> str:
        """Set homing delay time in seconds."""
        return self._build_command("MotorControl", "", "HomingDelayTime", str(seconds))

    def query_pan_left_limit(self) -> str:
        """Query pan left limit."""
        return self._build_query("MotorControl", "Pan", "LeftLimit")

    def query_pan_right_limit(self) -> str:
        """Query pan right limit."""
        return self._build_query("MotorControl", "Pan", "RightLimit")

    def query_tilt_up_limit(self) -> str:
        """Query tilt up limit."""
        return self._build_query("MotorControl", "Tilt", "UpLimit")

    def query_tilt_down_limit(self) -> str:
        """Query tilt down limit."""
        return self._build_query("MotorControl", "Tilt", "DownLimit")

    def query_homing_delay_mode(self) -> str:
        """Query homing delay mode."""
        return self._build_query("MotorControl", "", "HomingDelay")

    def query_homing_delay_time(self) -> str:
        """Query homing delay time."""
        return self._build_query("MotorControl", "", "HomingDelayTime")

    # ========== VideoStream Configuration Commands ==========

    def build_video_stream_enable(self, camera: int, stream: int) -> str:
        """Enable video stream."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "On", "")

    def build_video_stream_disable(self, camera: int, stream: int) -> str:
        """Disable video stream."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "Off", "")

    def build_video_stream_restart(self, camera: int, stream: int) -> str:
        """Restart video stream."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "Restart", "")

    # ========== RTSP Configuration ==========

    def build_rtsp_suffix(self, camera: int, stream: int, suffix: str) -> str:
        """Set RTSP suffix (e.g., 'live' for rtsp://IP:7031/live)."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "Suffix", suffix)

    def build_rtsp_port(self, camera: int, stream: int, port: int) -> str:
        """Set RTSP port (default 7031)."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "RtspPort", str(port))

    def build_rtsp_multicast_ip(self, camera: int, stream: int, ip: str) -> str:
        """Set RTSP multicast IP address."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "RtspMulticastIp", ip)

    def build_rtsp_multicast_port(self, camera: int, stream: int, port: int) -> str:
        """Set RTSP multicast port."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "RtspMulticastPort", str(port))

    def build_rtsp_user(self, camera: int, stream: int, user: str) -> str:
        """Set RTSP authentication username."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "User", user)

    def build_rtsp_password(self, camera: int, stream: int, password: str) -> str:
        """Set RTSP authentication password."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "Password", password)

    # ========== Video Encoding Settings ==========

    def build_resolution(self, camera: int, stream: int, resolution: str) -> str:
        """Set video resolution (e.g., '1920x1080')."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "Resolution", resolution)

    def build_codec(self, camera: int, stream: int, codec: str) -> str:
        """Set video codec (H264/H265/JPEG)."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "Codec", codec)

    def build_h264_profile(self, camera: int, stream: int, profile: str) -> str:
        """Set H264 profile (Baseline/Main/High)."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "H264Profile", profile)

    def build_jpeg_quality(self, camera: int, stream: int, quality: int) -> str:
        """Set JPEG quality (1-100)."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "JpegQuality", str(quality))

    def build_bitrate(self, camera: int, stream: int, bitrate_kbps: int) -> str:
        """Set video bitrate in kbps."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "BitrateKbps", str(bitrate_kbps))

    def build_bitrate_mode(self, camera: int, stream: int, mode: str) -> str:
        """Set bitrate mode (CBR/VBR)."""
        mode_map = {"CBR": "0", "VBR": "1"}
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "BitrateMode", mode_map.get(mode, "0"))

    def build_min_bitrate(self, camera: int, stream: int, bitrate_kbps: int) -> str:
        """Set minimum bitrate in kbps (VBR mode)."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "MinBitrateKbps", str(bitrate_kbps))

    def build_max_bitrate(self, camera: int, stream: int, bitrate_kbps: int) -> str:
        """Set maximum bitrate in kbps (VBR mode)."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "MaxBitrateKbps", str(bitrate_kbps))

    def build_fps(self, camera: int, stream: int, fps: int) -> str:
        """Set frames per second (1-60)."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "Fps", str(fps))

    def build_gop(self, camera: int, stream: int, gop: int) -> str:
        """Set GOP (Group of Pictures) keyframe interval."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "Gop", str(gop))

    def build_fit_mode(self, camera: int, stream: int, mode: str) -> str:
        """Set fit mode (Fit/Crop)."""
        mode_map = {"Fit": "0", "Crop": "1"}
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "FitMode", mode_map.get(mode, "0"))

    # ========== Stream Overlay & Metadata ==========

    def build_overlay_mode(self, camera: int, stream: int, enable: bool) -> str:
        """Enable/disable overlays on stream."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "OverlayMode", "1" if enable else "0")

    def build_metadata_mode(self, camera: int, stream: int, enable: bool) -> str:
        """Enable/disable metadata in stream."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "MetadataMode", "1" if enable else "0")

    def build_metadata_suffix(self, camera: int, stream: int, suffix: str) -> str:
        """Set metadata suffix (SMPTE336M/VND.ONVIF.METADATA)."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "MetadataSuffix", suffix)

    # ========== Alternative Streaming Protocols ==========

    def build_rtp_mode(self, camera: int, stream: int, enable: bool) -> str:
        """Enable/disable RTP direct streaming."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "RtpMode", "1" if enable else "0")

    def build_rtp_port(self, camera: int, stream: int, port: int) -> str:
        """Set RTP port."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "RtpPort", str(port))

    def build_rtp_dest_ip(self, camera: int, stream: int, ip: str) -> str:
        """Set RTP destination IP."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "Ip", ip)

    def build_rtmp_mode(self, camera: int, stream: int, enable: bool) -> str:
        """Enable/disable RTMP server."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "RtmpMode", "1" if enable else "0")

    def build_rtmp_port(self, camera: int, stream: int, port: int) -> str:
        """Set RTMP server port."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "RtmpPort", str(port))

    def build_hls_mode(self, camera: int, stream: int, enable: bool) -> str:
        """Enable/disable HLS server."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "HlsMode", "1" if enable else "0")

    def build_hls_port(self, camera: int, stream: int, port: int) -> str:
        """Set HLS server port."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "HlsPort", str(port))

    def build_srt_mode(self, camera: int, stream: int, enable: bool) -> str:
        """Enable/disable SRT server."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "SrtMode", "1" if enable else "0")

    def build_srt_port(self, camera: int, stream: int, port: int) -> str:
        """Set SRT server port."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "SrtPort", str(port))

    def build_udp_payload_size(self, camera: int, stream: int, size: int) -> str:
        """Set custom UDP payload size (100-65535 bytes)."""
        return self._build_command(f"Camera{camera}", f"Stream{stream}", "Custom1", str(size))

    # ========== VideoStream Queries ==========

    def query_video_stream_settings(self, camera: int, stream: int) -> str:
        """Query all video stream settings."""
        return self._build_query(f"Camera{camera}", f"Stream{stream}", "")

    def query_video_resolution(self, camera: int, stream: int) -> str:
        """Query video stream resolution."""
        return self._build_query(f"Camera{camera}", f"Stream{stream}", "Resolution")

    def query_video_bitrate(self, camera: int, stream: int) -> str:
        """Query video stream bitrate."""
        return self._build_query(f"Camera{camera}", f"Stream{stream}", "BitrateKbps")

    def query_video_fps(self, camera: int, stream: int) -> str:
        """Query video FPS."""
        return self._build_query(f"Camera{camera}", f"Stream{stream}", "Fps")

    def query_video_codec(self, camera: int, stream: int) -> str:
        """Query video codec."""
        return self._build_query(f"Camera{camera}", f"Stream{stream}", "Codec")

    def query_rtsp_suffix(self, camera: int, stream: int) -> str:
        """Query RTSP stream suffix."""
        return self._build_query(f"Camera{camera}", f"Stream{stream}", "Suffix")

    # ========== Overlay Configuration Commands ==========

    def build_crosshair_mode(self, camera: int, enable: bool) -> str:
        """Enable/disable crosshair overlay."""
        return self._build_command(f"Camera{camera}", "Overlay", "CrossHairMode", "1" if enable else "0")

    def build_crosshair_size(self, camera: int, size: int) -> str:
        """Set crosshair size (1-100 pixels)."""
        return self._build_command(f"Camera{camera}", "Overlay", "CrossHairSize", str(size))

    def build_crosshair_color(self, camera: int, color: str) -> str:
        """Set crosshair color."""
        color_map = {"White": "0", "Black": "1", "Red": "2", "Green": "3", "Blue": "4", "Contrast": "5"}
        return self._build_command(f"Camera{camera}", "Overlay", "CrossHairColor", color_map.get(color, "0"))

    def build_datetime_overlay(self, camera: int, enable: bool) -> str:
        """Enable/disable date/time overlay."""
        return self._build_command(f"Camera{camera}", "Overlay", "DateTimeMode", "1" if enable else "0")

    def build_zoom_pos_overlay(self, camera: int, enable: bool) -> str:
        """Enable/disable zoom position overlay."""
        return self._build_command(f"Camera{camera}", "Overlay", "ZoomPosMode", "1" if enable else "0")

    def build_focus_mode_overlay(self, camera: int, enable: bool) -> str:
        """Enable/disable focus mode overlay."""
        return self._build_command(f"Camera{camera}", "Overlay", "FocusMode", "1" if enable else "0")

    def build_digital_zoom_overlay(self, camera: int, enable: bool) -> str:
        """Enable/disable digital zoom level overlay."""
        return self._build_command(f"Camera{camera}", "Overlay", "DigitalZoomMode", "1" if enable else "0")

    def build_clahe_overlay(self, camera: int, enable: bool) -> str:
        """Enable/disable CLAHE status overlay."""
        return self._build_command(f"Camera{camera}", "Overlay", "ClaheMode", "1" if enable else "0")

    def build_tracker_overlay(self, camera: int, enable: bool) -> str:
        """Enable/disable tracker status overlay."""
        return self._build_command(f"Camera{camera}", "Overlay", "TrackerMode", "1" if enable else "0")

    def build_pan_tilt_overlay(self, camera: int, enable: bool) -> str:
        """Enable/disable pan/tilt position overlay."""
        return self._build_command(f"Camera{camera}", "Overlay", "PanTiltPosMode", "1" if enable else "0")

    def build_lrf_overlay(self, camera: int, enable: bool) -> str:
        """Enable/disable LRF range overlay."""
        return self._build_command(f"Camera{camera}", "Overlay", "LrfMode", "1" if enable else "0")

    def build_webrtc_overlay(self, camera: int, enable: bool) -> str:
        """Enable/disable WebRTC overlay."""
        return self._build_command(f"Camera{camera}", "WebRtcOverlay", "On" if enable else "Off", "")

    # ========== MotionMagnificator Commands ==========

    def build_motion_magnificator_enable(self, camera: int) -> str:
        """Enable motion magnificator."""
        return self._build_command(f"Camera{camera}", "MotionMagnificator", "On", "")

    def build_motion_magnificator_disable(self, camera: int) -> str:
        """Disable motion magnificator."""
        return self._build_command(f"Camera{camera}", "MotionMagnificator", "Off", "")

    def build_motion_magnificator_level(self, camera: int, level: int) -> str:
        """Set motion magnificator level (1-10)."""
        return self._build_command(f"Camera{camera}", "MotionMagnificator", "Level", str(level))

    # ========== VideoTracker Commands ==========

    def build_video_tracker_reset(self, camera: int) -> str:
        """Reset video tracker."""
        return self._build_command(f"Camera{camera}", "VideoTracker", "Reset", "")

    def build_video_tracker_enable(self, camera: int) -> str:
        """Enable video tracker."""
        return self._build_command(f"Camera{camera}", "VideoTracker", "On", "")

    def build_video_tracker_disable(self, camera: int) -> str:
        """Disable video tracker."""
        return self._build_command(f"Camera{camera}", "VideoTracker", "Off", "")

    def build_video_tracker_lock(self, camera: int) -> str:
        """Lock video tracker onto target."""
        return self._build_command(f"Camera{camera}", "VideoTracker", "Lock", "")

    def build_video_tracker_unlock(self, camera: int) -> str:
        """Unlock video tracker."""
        return self._build_command(f"Camera{camera}", "VideoTracker", "Unlock", "")

    def build_video_tracker_mode(self, camera: int, mode: str) -> str:
        """Set video tracker mode (Manual/Auto/Continuous)."""
        mode_map = {"Manual": "0", "Auto": "1", "Continuous": "2"}
        return self._build_command(f"Camera{camera}", "VideoTracker", "Mode", mode_map.get(mode, "0"))

    def build_video_tracker_object_size(self, camera: int, size: int) -> str:
        """Set tracker object size."""
        return self._build_command(f"Camera{camera}", "VideoTracker", "ObjectSize", str(size))

    def build_video_tracker_search_area_size(self, camera: int, size: int) -> str:
        """Set tracker search area size."""
        return self._build_command(f"Camera{camera}", "VideoTracker", "SearchAreaSize", str(size))

    # ========== MotionDetector Commands ==========

    def build_motion_detector_reset(self, camera: int) -> str:
        """Reset motion detector."""
        return self._build_command(f"Camera{camera}", "MotionDetector", "Reset", "")

    def build_motion_detector_enable(self, camera: int) -> str:
        """Enable motion detector."""
        return self._build_command(f"Camera{camera}", "MotionDetector", "On", "")

    def build_motion_detector_disable(self, camera: int) -> str:
        """Disable motion detector."""
        return self._build_command(f"Camera{camera}", "MotionDetector", "Off", "")

    def build_motion_detector_frame_buffer(self, camera: int, size: int) -> str:
        """Set motion detector frame buffer size (1-20)."""
        return self._build_command(f"Camera{camera}", "MotionDetector", "FrameBufferSize", str(size))

    def build_motion_detector_min_width(self, camera: int, width: int) -> str:
        """Set minimum object width for detection."""
        return self._build_command(f"Camera{camera}", "MotionDetector", "MinObjectWidth", str(width))

    def build_motion_detector_max_width(self, camera: int, width: int) -> str:
        """Set maximum object width for detection."""
        return self._build_command(f"Camera{camera}", "MotionDetector", "MaxObjectWidth", str(width))

    def build_motion_detector_min_height(self, camera: int, height: int) -> str:
        """Set minimum object height for detection."""
        return self._build_command(f"Camera{camera}", "MotionDetector", "MinObjectHeight", str(height))

    def build_motion_detector_max_height(self, camera: int, height: int) -> str:
        """Set maximum object height for detection."""
        return self._build_command(f"Camera{camera}", "MotionDetector", "MaxObjectHeight", str(height))

    def build_motion_detector_x_criteria(self, camera: int, criteria: int) -> str:
        """Set X detection criteria."""
        return self._build_command(f"Camera{camera}", "MotionDetector", "XDetectionCriteria", str(criteria))

    def build_motion_detector_y_criteria(self, camera: int, criteria: int) -> str:
        """Set Y detection criteria."""
        return self._build_command(f"Camera{camera}", "MotionDetector", "YDetectionCriteria", str(criteria))

    def build_motion_detector_reset_criteria(self, camera: int, criteria: int) -> str:
        """Set reset criteria."""
        return self._build_command(f"Camera{camera}", "MotionDetector", "ResetCriteria", str(criteria))

    def build_motion_detector_sensitivity(self, camera: int, sensitivity: int) -> str:
        """Set motion detector sensitivity (0-100)."""
        return self._build_command(f"Camera{camera}", "MotionDetector", "Sensitivity", str(sensitivity))

    def build_motion_detector_mode(self, camera: int, mode: int) -> str:
        """Set motion detector mode (0-2)."""
        return self._build_command(f"Camera{camera}", "MotionDetector", "Mode", str(mode))

    # ========== ChangesDetector Commands ==========

    def build_changes_detector_reset(self, camera: int) -> str:
        """Reset changes detector."""
        return self._build_command(f"Camera{camera}", "ChangesDetector", "Reset", "")

    def build_changes_detector_enable(self, camera: int) -> str:
        """Enable changes detector."""
        return self._build_command(f"Camera{camera}", "ChangesDetector", "On", "")

    def build_changes_detector_disable(self, camera: int) -> str:
        """Disable changes detector."""
        return self._build_command(f"Camera{camera}", "ChangesDetector", "Off", "")

    def build_changes_detector_frame_buffer(self, camera: int, size: int) -> str:
        """Set changes detector frame buffer size (1-20)."""
        return self._build_command(f"Camera{camera}", "ChangesDetector", "FrameBufferSize", str(size))

    def build_changes_detector_min_width(self, camera: int, width: int) -> str:
        """Set minimum object width for detection."""
        return self._build_command(f"Camera{camera}", "ChangesDetector", "MinObjectWidth", str(width))

    def build_changes_detector_max_width(self, camera: int, width: int) -> str:
        """Set maximum object width for detection."""
        return self._build_command(f"Camera{camera}", "ChangesDetector", "MaxObjectWidth", str(width))

    def build_changes_detector_min_height(self, camera: int, height: int) -> str:
        """Set minimum object height for detection."""
        return self._build_command(f"Camera{camera}", "ChangesDetector", "MinObjectHeight", str(height))

    def build_changes_detector_max_height(self, camera: int, height: int) -> str:
        """Set maximum object height for detection."""
        return self._build_command(f"Camera{camera}", "ChangesDetector", "MaxObjectHeight", str(height))

    def build_changes_detector_x_criteria(self, camera: int, criteria: int) -> str:
        """Set X detection criteria."""
        return self._build_command(f"Camera{camera}", "ChangesDetector", "XDetectionCriteria", str(criteria))

    def build_changes_detector_y_criteria(self, camera: int, criteria: int) -> str:
        """Set Y detection criteria."""
        return self._build_command(f"Camera{camera}", "ChangesDetector", "YDetectionCriteria", str(criteria))

    def build_changes_detector_reset_criteria(self, camera: int, criteria: int) -> str:
        """Set reset criteria."""
        return self._build_command(f"Camera{camera}", "ChangesDetector", "ResetCriteria", str(criteria))

    def build_changes_detector_sensitivity(self, camera: int, sensitivity: int) -> str:
        """Set changes detector sensitivity (0-100)."""
        return self._build_command(f"Camera{camera}", "ChangesDetector", "Sensitivity", str(sensitivity))

    def build_changes_detector_mode(self, camera: int, mode: int) -> str:
        """Set changes detector mode (0-2)."""
        return self._build_command(f"Camera{camera}", "ChangesDetector", "Mode", str(mode))

    # ========== Classification Commands ==========

    def build_classification_enable(self, camera: int) -> str:
        """Enable classification."""
        return self._build_command(f"Camera{camera}", "Classification", "On", "")

    def build_classification_disable(self, camera: int) -> str:
        """Disable classification."""
        return self._build_command(f"Camera{camera}", "Classification", "Off", "")

    def build_classification_model(self, camera: int, model: str) -> str:
        """Set classification model."""
        return self._build_command(f"Camera{camera}", "Classification", "Model", model)

    def build_classification_confidence(self, camera: int, confidence: int) -> str:
        """Set classification confidence threshold (0-100)."""
        return self._build_command(f"Camera{camera}", "Classification", "ConfidenceThreshold", str(confidence))

    # ========== Detection Commands ==========

    def subscribe_objects_events(self, camera: int) -> str:
        """Subscribe to detection objects/events for camera."""
        return self._build_command(f"Camera{camera}", "Detection", "Objects/Subscribe", "")

    def query_classification_status(self, camera: int) -> str:
        """Query classification status."""
        return self._build_query(f"Camera{camera}", "Classification", "Status")

    # ========== License Query Commands ==========

    def query_video_tracker_token(self) -> str:
        """Query VideoTracker license token."""
        return self._build_query("System", "License", "VideoTrackerToken")

    def query_video_tracker_license_status(self) -> str:
        """Query VideoTracker license status."""
        return self._build_query("System", "License", "VideoTrackerLicenseStatus")

    def query_video_stabiliser_token(self) -> str:
        """Query VideoStabiliser license token."""
        return self._build_query("System", "License", "VideoStabiliserToken")

    def query_video_stabiliser_license_status(self) -> str:
        """Query VideoStabiliser license status."""
        return self._build_query("System", "License", "VideoStabiliserLicenseStatus")

    def query_motion_detector_token(self) -> str:
        """Query MotionDetector license token."""
        return self._build_query("System", "License", "MotionDetectorToken")

    def query_motion_detector_license_status(self) -> str:
        """Query MotionDetector license status."""
        return self._build_query("System", "License", "MotionDetectorLicenseStatus")

    def query_changes_detector_token(self) -> str:
        """Query ChangesDetector license token."""
        return self._build_query("System", "License", "ChangesDetectorToken")

    def query_changes_detector_license_status(self) -> str:
        """Query ChangesDetector license status."""
        return self._build_query("System", "License", "ChangesDetectorLicenseStatus")

    def query_classification_token(self) -> str:
        """Query Classification license token."""
        return self._build_query("System", "License", "ClassificationToken")

    def query_classification_license_status(self) -> str:
        """Query Classification license status."""
        return self._build_query("System", "License", "ClassificationLicenseStatus")

    # ========== ProcedureManager Commands ==========

    def build_procedure_load(self, procedure_name: str) -> str:
        """
        Load a procedure by name.

        Args:
            procedure_name: Name of the procedure to load

        Returns:
            Command string
        """
        return self._build_command("ProcedureManager", "Load", procedure_name)

    def build_procedure_execute(self) -> str:
        """
        Execute the currently loaded procedure.

        Returns:
            Command string
        """
        return self._build_command("ProcedureManager", "Execute", "")

    def build_procedure_stop(self) -> str:
        """
        Stop the currently executing procedure.

        Returns:
            Command string
        """
        return self._build_command("ProcedureManager", "Stop", "")

    def query_procedure_status(self) -> str:
        """
        Query current procedure status.

        Returns:
            Query string
        """
        return self._build_query("ProcedureManager", "Status", "")

    # ========== BadPixelProcessor Commands ==========

    def build_bad_pixel_enable(self, camera: int) -> str:
        """
        Enable bad pixel processor for camera.

        Args:
            camera: Camera number (1, 2, or 3)

        Returns:
            Command string
        """
        return self._build_command(f"Camera{camera}", "BadPixelProcessor", "On", "")

    def build_bad_pixel_disable(self, camera: int) -> str:
        """
        Disable bad pixel processor for camera.

        Args:
            camera: Camera number (1, 2, or 3)

        Returns:
            Command string
        """
        return self._build_command(f"Camera{camera}", "BadPixelProcessor", "Off", "")

    def build_bad_pixel_calibrate(self, camera: int) -> str:
        """
        Calibrate bad pixel processor for camera.

        Args:
            camera: Camera number (1, 2, or 3)

        Returns:
            Command string
        """
        return self._build_command(f"Camera{camera}", "BadPixelProcessor", "Calibrate", "")

    def build_bad_pixel_threshold(self, camera: int, threshold: float) -> str:
        """
        Set bad pixel detection threshold.

        Args:
            camera: Camera number (1, 2, or 3)
            threshold: Detection threshold value

        Returns:
            Command string
        """
        return self._build_command(f"Camera{camera}", "BadPixelProcessor", "Threshold", str(threshold))

    def query_bad_pixel_settings(self, camera: int) -> str:
        """
        Query bad pixel processor settings.

        Args:
            camera: Camera number (1, 2, or 3)

        Returns:
            Query string
        """
        return self._build_query(f"Camera{camera}", "BadPixelProcessor", "")

    # ========== VideoSource Commands ==========

    def build_video_source(self, camera: int, source_id: str) -> str:
        """
        Set video source for camera.

        Args:
            camera: Camera number (1, 2, or 3)
            source_id: Video source identifier

        Returns:
            Command string
        """
        return self._build_command(f"Camera{camera}", "VideoSource", "Source", source_id)

    def query_video_source(self, camera: int) -> str:
        """
        Query current video source.

        Args:
            camera: Camera number (1, 2, or 3)

        Returns:
            Query string
        """
        return self._build_query(f"Camera{camera}", "VideoSource", "Source")

    # ========== WebRtcOverlay Commands ==========

    def build_webrtc_overlay_enable(self, camera: int) -> str:
        """
        Enable WebRTC overlay for camera.

        Args:
            camera: Camera number (1, 2, or 3)

        Returns:
            Command string
        """
        return self._build_command(f"Camera{camera}", "WebRtcOverlay", "On", "")

    def build_webrtc_overlay_disable(self, camera: int) -> str:
        """
        Disable WebRTC overlay for camera.

        Args:
            camera: Camera number (1, 2, or 3)

        Returns:
            Command string
        """
        return self._build_command(f"Camera{camera}", "WebRtcOverlay", "Off", "")

    def query_webrtc_overlay_settings(self, camera: int) -> str:
        """
        Query WebRTC overlay settings.

        Args:
            camera: Camera number (1, 2, or 3)

        Returns:
            Query string
        """
        return self._build_query(f"Camera{camera}", "WebRtcOverlay", "")

    # ========== ExternalUp Commands ==========

    def build_external_up_enable(self) -> str:
        """
        Enable external UP protocol.

        Returns:
            Command string
        """
        return self._build_command("ExternalUp", "", "On", "")

    def build_external_up_disable(self) -> str:
        """
        Disable external UP protocol.

        Returns:
            Command string
        """
        return self._build_command("ExternalUp", "", "Off", "")

    def build_external_up_port(self, port: int) -> str:
        """
        Set external UP port.

        Args:
            port: UDP port number

        Returns:
            Command string
        """
        return self._build_command("ExternalUp", "", "Port", str(port))

    def build_external_up_address(self, address: str) -> str:
        """
        Set external UP address.

        Args:
            address: IP address

        Returns:
            Command string
        """
        return self._build_command("ExternalUp", "", "Address", address)

    def query_external_up_settings(self) -> str:
        """
        Query external UP settings.

        Returns:
            Query string
        """
        return self._build_query("ExternalUp", "", "")

    # ========== PelcoD Commands ==========

    def build_pelco_d_enable(self) -> str:
        """
        Enable Pelco-D protocol.

        Returns:
            Command string
        """
        return self._build_command("PelcoD", "", "On", "")

    def build_pelco_d_disable(self) -> str:
        """
        Disable Pelco-D protocol.

        Returns:
            Command string
        """
        return self._build_command("PelcoD", "", "Off", "")

    def build_pelco_d_port(self, port: int) -> str:
        """
        Set Pelco-D port.

        Args:
            port: Serial port number or TCP port

        Returns:
            Command string
        """
        return self._build_command("PelcoD", "", "Port", str(port))

    def build_pelco_d_address(self, address: str) -> str:
        """
        Set Pelco-D address.

        Args:
            address: Device address or IP address

        Returns:
            Command string
        """
        return self._build_command("PelcoD", "", "Address", address)

    def query_pelco_d_settings(self) -> str:
        """
        Query Pelco-D settings.

        Returns:
            Query string
        """
        return self._build_query("PelcoD", "", "")

    # ========== Lrf (Laser Rangefinder) Commands ==========

    def build_lrf_fire(self) -> str:
        """
        Fire laser rangefinder to measure distance.

        Returns:
            Command string
        """
        return self._build_command("Lrf", "", "Fire", "")

    def build_lrf_mode(self, mode: str) -> str:
        """
        Set laser rangefinder mode.

        Args:
            mode: LRF mode (Single/Continuous/etc.)

        Returns:
            Command string
        """
        return self._build_command("Lrf", "", "Mode", mode)

    def query_lrf_range(self) -> str:
        """
        Query current laser rangefinder range measurement.

        Returns:
            Query string
        """
        return self._build_query("Lrf", "", "Range")

    def query_lrf_settings(self) -> str:
        """
        Query laser rangefinder settings.

        Returns:
            Query string
        """
        return self._build_query("Lrf", "", "")

    # ========== Speaker Commands ==========

    def build_speaker_play(self, clip_name: str) -> str:
        """
        Play audio clip through speaker.

        Args:
            clip_name: Name of audio clip to play

        Returns:
            Command string
        """
        return self._build_command("Speaker", "", "Play", clip_name)

    def build_speaker_stop(self) -> str:
        """
        Stop speaker audio playback.

        Returns:
            Command string
        """
        return self._build_command("Speaker", "", "Stop", "")

    def build_speaker_volume(self, volume: int) -> str:
        """
        Set speaker volume level.

        Args:
            volume: Volume level (0-100)

        Returns:
            Command string
        """
        return self._build_command("Speaker", "", "Volume", str(volume))

    def query_speaker_status(self) -> str:
        """
        Query speaker status and settings.

        Returns:
            Query string
        """
        return self._build_query("Speaker", "", "Status")

    # ========== G5Laser Commands ==========

    def build_g5_laser_enable(self) -> str:
        """
        Enable G5 laser.

        Returns:
            Command string
        """
        return self._build_command("G5Laser", "", "On", "")

    def build_g5_laser_disable(self) -> str:
        """
        Disable G5 laser.

        Returns:
            Command string
        """
        return self._build_command("G5Laser", "", "Off", "")

    def build_g5_laser_intensity(self, intensity: int) -> str:
        """
        Set G5 laser intensity level.

        Args:
            intensity: Intensity level (0-100)

        Returns:
            Command string
        """
        return self._build_command("G5Laser", "", "Intensity", str(intensity))

    def query_g5_laser_settings(self) -> str:
        """
        Query G5 laser settings.

        Returns:
            Query string
        """
        return self._build_query("G5Laser", "", "")

    # ========== PeakBeam Commands ==========

    def build_peakbeam_enable(self) -> str:
        """
        Enable PeakBeam illuminator.

        Returns:
            Command string
        """
        return self._build_command("PeakBeam", "", "On", "")

    def build_peakbeam_disable(self) -> str:
        """
        Disable PeakBeam illuminator.

        Returns:
            Command string
        """
        return self._build_command("PeakBeam", "", "Off", "")

    def build_peakbeam_intensity(self, intensity: int) -> str:
        """
        Set PeakBeam intensity level.

        Args:
            intensity: Intensity level (0-100)

        Returns:
            Command string
        """
        return self._build_command("PeakBeam", "", "Intensity", str(intensity))

    def build_peakbeam_mode(self, mode: str) -> str:
        """
        Set PeakBeam mode.

        Args:
            mode: Operating mode (Continuous/Strobe/etc.)

        Returns:
            Command string
        """
        return self._build_command("PeakBeam", "", "Mode", mode)

    def query_peakbeam_settings(self) -> str:
        """
        Query PeakBeam settings.

        Returns:
            Query string
        """
        return self._build_query("PeakBeam", "", "")

    # ========== Companion Commands ==========

    def build_companion_command(self, command: str) -> str:
        """
        Send command to companion system.

        Args:
            command: Command string for companion system

        Returns:
            Command string
        """
        return self._build_command("Companion", "", "Command", command)

    def build_companion_enable(self) -> str:
        """
        Enable companion system.

        Returns:
            Command string
        """
        return self._build_command("Companion", "", "On", "")

    def build_companion_disable(self) -> str:
        """
        Disable companion system.

        Returns:
            Command string
        """
        return self._build_command("Companion", "", "Off", "")

    def build_companion_reset(self) -> str:
        """
        Reset companion system.

        Returns:
            Command string
        """
        return self._build_command("Companion", "", "Reset", "")

    def query_companion_status(self) -> str:
        """
        Query companion system status.

        Returns:
            Query string
        """
        return self._build_query("Companion", "", "Status")

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

    def parse_system_info_response(self, response: str) -> Optional[tuple[str, str]]:
        """
        Parse system information reply messages.

        Expected formats:
            ID:N/Reply/General/Mainboard/versionNexOS:2.4.7
            ID:N/Reply/General/Mainboard/serial:ABC123456
            ID:N/Reply/General/Mainboard/trackingEnabled:On

        Returns:
            (info_type, value) tuple where info_type is 'nexos_version', 'mainboard_serial', or 'tracking_status'
            Returns None if not a system info response
        """
        parsed = self.parse_response(response)

        if not parsed or parsed['type'] != 'Reply':
            return None

        if parsed.get('module') == 'General' and parsed.get('submodule') == 'Mainboard':
            parameter = parsed.get('parameter')
            value = parsed.get('value')

            if parameter == 'versionNexOS' and value:
                return ('nexos_version', value)
            elif parameter == 'serial' and value:
                return ('mainboard_serial', value)
            elif parameter == 'trackingEnabled' and value:
                return ('tracking_status', value)

        return None
