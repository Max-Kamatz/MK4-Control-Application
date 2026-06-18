"""
gui/tabs/combined_control_tab.py
Combined video display and PTZ control tab - shows streams and trackpad control together.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                             QGroupBox, QLabel, QGridLayout, QPushButton, QLineEdit, QSlider, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from gui.widgets.ptz_trackpad import PTZControlWidget
from utils.constants import load_config
from utils.logger import setup_logger

logger = setup_logger()


class CombinedControlTab(QWidget):
    """
    Combined tab showing video streams (left) and PTZ control (right).
    This replaces separate video and control tabs.
    """

    # Pan/Tilt signals (normalized -1.0 to 1.0)
    pan_tilt_command = pyqtSignal(float, float)
    pan_tilt_stop = pyqtSignal()

    # Zoom signals
    zoom_command = pyqtSignal(int)      # +1 = in, -1 = out, 0 = stop

    # Focus signals
    focus_command = pyqtSignal(int)     # +1 = far, -1 = near, 0 = stop

    # Home
    home_requested = pyqtSignal()

    # Speed control signals
    pan_speed_changed = pyqtSignal(float)  # degrees/sec
    tilt_speed_changed = pyqtSignal(float)  # degrees/sec
    zoom_speed_changed = pyqtSignal(float)  # -1.0 to 1.0
    focus_speed_changed = pyqtSignal(float)  # -1.0 to 1.0

    # Camera function signals (camera number, value)
    zoom_to_position = pyqtSignal(int, int)  # camera, position
    autofocus_requested = pyqtSignal(int)  # camera
    camera_profile_changed = pyqtSignal(int, int)  # camera, profile
    video_stabilizer_changed = pyqtSignal(int, bool)  # camera, enable
    digital_zoom_level_changed = pyqtSignal(int, float)  # camera, level
    digital_zoom_enabled_changed = pyqtSignal(int, bool)  # camera, enable
    clahe_changed = pyqtSignal(int, bool)  # camera, enable
    color_palette_changed = pyqtSignal(int, int)  # camera, palette
    color_filter_changed = pyqtSignal(int, bool)  # camera, enable

    def __init__(self, video_manager=None):
        super().__init__()
        self.config = load_config()
        self.actual_pan = None
        self.actual_tilt = None
        self.video_manager = video_manager
        self.video_placeholder = None  # Will hold the shared video display
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: PTZ control (fixed width like reference app)
        left_widget = self.create_control_section()

        # Right side: Video streams (expands to fill space)
        right_widget = self.create_video_section()

        # Use simple horizontal layout - control panel has fixed width, video expands
        main_layout.addWidget(left_widget, 0)   # Control panel fixed width (no stretch)
        main_layout.addWidget(right_widget, 1)  # Video expands (stretch factor 1)

        self.setLayout(main_layout)

        logger.info("Combined control tab initialized")

    def create_video_section(self) -> QWidget:
        """Create placeholder for shared video display manager."""
        self.video_placeholder = QWidget()
        self.video_placeholder.setObjectName("video_container")
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(10, 10, 10, 10)
        self.video_placeholder.setLayout(layout)
        return self.video_placeholder

    def set_video_display(self, video_manager):
        """Called when this tab becomes active - reparent video display here."""
        if video_manager and self.video_placeholder:
            # Clear placeholder
            while self.video_placeholder.layout().count():
                item = self.video_placeholder.layout().takeAt(0)
                if item.widget():
                    item.widget().setParent(None)

            # Reparent video manager's display widget
            display_widget = video_manager.get_display_widget()
            display_widget.setParent(self.video_placeholder)
            self.video_placeholder.layout().addWidget(display_widget)
            display_widget.show()
            logger.debug("Video display reparented to Combined Control tab")

    def create_control_section(self) -> QWidget:
        """Create PTZ control section."""
        widget = QWidget()
        widget.setFixedWidth(480)  # Fixed width like reference app (360px in reference)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Camera selector group
        camera_select_group = QGroupBox("Active Camera")
        camera_select_layout = QVBoxLayout()

        camera_label = QLabel("Select camera for Zoom/Focus control:")
        camera_label.setStyleSheet("font-size: 9pt; padding-bottom: 5px;")
        camera_select_layout.addWidget(camera_label)

        # Create button group for exclusive selection (only one can be selected)
        self.camera_button_group = QButtonGroup()
        self.camera_button_group.setExclusive(True)

        # Create horizontal layout for camera buttons
        camera_buttons_layout = QHBoxLayout()
        camera_buttons_layout.setSpacing(5)

        # Camera 1 - Thermal button
        self.camera1_button = QPushButton("Thermal")
        self.camera1_button.setCheckable(True)
        self.camera1_button.setChecked(True)  # Default selected
        self.camera1_button.setProperty("camera", "Camera1")
        self.camera1_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 10pt;
                font-weight: bold;
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border: 2px solid #2a82da;
            }
            QPushButton:checked {
                background-color: #2a82da;
                border: 2px solid #2a82da;
                color: white;
            }
        """)
        self.camera_button_group.addButton(self.camera1_button, 1)
        camera_buttons_layout.addWidget(self.camera1_button)

        # Camera 2 - Daylight button
        self.camera2_button = QPushButton("Daylight")
        self.camera2_button.setCheckable(True)
        self.camera2_button.setProperty("camera", "Camera2")
        self.camera2_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 10pt;
                font-weight: bold;
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border: 2px solid #2a82da;
            }
            QPushButton:checked {
                background-color: #2a82da;
                border: 2px solid #2a82da;
                color: white;
            }
        """)
        self.camera_button_group.addButton(self.camera2_button, 2)
        camera_buttons_layout.addWidget(self.camera2_button)

        # Camera 3 - SWIR button
        self.camera3_button = QPushButton("SWIR")
        self.camera3_button.setCheckable(True)
        self.camera3_button.setProperty("camera", "Camera3")
        self.camera3_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 10pt;
                font-weight: bold;
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border: 2px solid #2a82da;
            }
            QPushButton:checked {
                background-color: #2a82da;
                border: 2px solid #2a82da;
                color: white;
            }
        """)
        self.camera_button_group.addButton(self.camera3_button, 3)
        camera_buttons_layout.addWidget(self.camera3_button)

        camera_select_layout.addLayout(camera_buttons_layout)

        # Connect signal
        self.camera_button_group.buttonClicked.connect(self.on_camera_button_clicked)

        camera_select_group.setLayout(camera_select_layout)
        layout.addWidget(camera_select_group)

        # PTZ Trackpad control
        self.ptz_control = PTZControlWidget()
        self.ptz_control.pan_tilt_moved.connect(self.on_trackpad_moved)
        self.ptz_control.pan_tilt_released.connect(self.on_trackpad_released)
        self.ptz_control.zoom_pressed.connect(self.on_zoom_pressed)
        self.ptz_control.zoom_released.connect(self.on_zoom_released)
        self.ptz_control.focus_pressed.connect(self.on_focus_pressed)
        self.ptz_control.focus_released.connect(self.on_focus_released)

        # Connect directional arrows (use slider values)
        self.ptz_control.arrow_up_pressed.connect(self.on_arrow_up_pressed)
        self.ptz_control.arrow_down_pressed.connect(self.on_arrow_down_pressed)
        self.ptz_control.arrow_left_pressed.connect(self.on_arrow_left_pressed)
        self.ptz_control.arrow_right_pressed.connect(self.on_arrow_right_pressed)
        self.ptz_control.arrow_released.connect(self.on_arrow_released)

        layout.addWidget(self.ptz_control)

        # Speed Control group
        speed_group = QGroupBox("Speed Control")
        speed_layout = QGridLayout()
        speed_layout.setSpacing(5)

        # Pan Speed Slider
        speed_layout.addWidget(QLabel("<b>Pan Speed:</b>"), 0, 0)
        self.pan_speed_label = QLabel("0.00")
        self.pan_speed_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        self.pan_speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        speed_layout.addWidget(self.pan_speed_label, 0, 1)

        self.pan_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.pan_speed_slider.setMinimum(0)     # 0.0
        self.pan_speed_slider.setMaximum(100)   # 1.0
        self.pan_speed_slider.setValue(0)
        self.pan_speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.pan_speed_slider.setTickInterval(25)
        self.pan_speed_slider.valueChanged.connect(self.on_pan_speed_changed)
        speed_layout.addWidget(self.pan_speed_slider, 1, 0, 1, 2)

        # Tilt Speed Slider
        speed_layout.addWidget(QLabel("<b>Tilt Speed:</b>"), 2, 0)
        self.tilt_speed_label = QLabel("0.00")
        self.tilt_speed_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        self.tilt_speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        speed_layout.addWidget(self.tilt_speed_label, 2, 1)

        self.tilt_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.tilt_speed_slider.setMinimum(0)     # 0.0
        self.tilt_speed_slider.setMaximum(100)   # 1.0
        self.tilt_speed_slider.setValue(0)
        self.tilt_speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.tilt_speed_slider.setTickInterval(25)
        self.tilt_speed_slider.valueChanged.connect(self.on_tilt_speed_changed)
        speed_layout.addWidget(self.tilt_speed_slider, 3, 0, 1, 2)

        # Zoom Speed Slider
        speed_layout.addWidget(QLabel("<b>Zoom Speed:</b>"), 4, 0)
        self.zoom_speed_label = QLabel("0.0")
        self.zoom_speed_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        self.zoom_speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        speed_layout.addWidget(self.zoom_speed_label, 4, 1)

        self.zoom_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_speed_slider.setMinimum(0)     # 0.0
        self.zoom_speed_slider.setMaximum(100)   # 1.0
        self.zoom_speed_slider.setValue(0)
        self.zoom_speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_speed_slider.setTickInterval(25)
        self.zoom_speed_slider.valueChanged.connect(self.on_zoom_speed_changed)
        speed_layout.addWidget(self.zoom_speed_slider, 5, 0, 1, 2)

        # Focus Speed Slider
        speed_layout.addWidget(QLabel("<b>Focus Speed:</b>"), 6, 0)
        self.focus_speed_label = QLabel("0.0")
        self.focus_speed_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        self.focus_speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        speed_layout.addWidget(self.focus_speed_label, 6, 1)

        self.focus_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.focus_speed_slider.setMinimum(0)     # 0.0
        self.focus_speed_slider.setMaximum(100)   # 1.0
        self.focus_speed_slider.setValue(0)
        self.focus_speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.focus_speed_slider.setTickInterval(25)
        self.focus_speed_slider.valueChanged.connect(self.on_focus_speed_changed)
        speed_layout.addWidget(self.focus_speed_slider, 7, 0, 1, 2)

        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)

        # Position feedback group (moved from Status tab)
        position_group = QGroupBox("Position Feedback")
        position_layout = QGridLayout()

        position_layout.addWidget(QLabel("<b>Commanded:</b>"), 0, 0, 1, 2)

        position_layout.addWidget(QLabel("Pan:"), 1, 0)
        self.cmd_pan_label = QLabel("0.0°")
        self.cmd_pan_label.setStyleSheet("font-size: 12pt; color: #2a82da;")
        position_layout.addWidget(self.cmd_pan_label, 1, 1)

        position_layout.addWidget(QLabel("Tilt:"), 2, 0)
        self.cmd_tilt_label = QLabel("0.0°")
        self.cmd_tilt_label.setStyleSheet("font-size: 12pt; color: #2a82da;")
        position_layout.addWidget(self.cmd_tilt_label, 2, 1)

        position_layout.addWidget(QLabel("<b>Actual:</b>"), 3, 0, 1, 2)

        position_layout.addWidget(QLabel("Pan:"), 4, 0)
        self.actual_pan_label = QLabel("N/A")
        self.actual_pan_label.setStyleSheet("font-size: 12pt; color: #44ff44;")
        position_layout.addWidget(self.actual_pan_label, 4, 1)

        position_layout.addWidget(QLabel("Tilt:"), 5, 0)
        self.actual_tilt_label = QLabel("N/A")
        self.actual_tilt_label.setStyleSheet("font-size: 12pt; color: #44ff44;")
        position_layout.addWidget(self.actual_tilt_label, 5, 1)

        position_group.setLayout(position_layout)
        layout.addWidget(position_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def on_trackpad_moved(self, pan: float, tilt: float):
        """
        Handle trackpad movement - joystick mode.
        Distance from center determines speed.

        pan, tilt: normalized -1.0 to 1.0 (distance from center)
        """
        # Convert to speed (degrees/second)
        # Max speed: 20 deg/s for pan, 10 deg/s for tilt
        max_pan_speed = 20.0  # degrees/second
        max_tilt_speed = 10.0  # degrees/second

        pan_speed = pan * max_pan_speed
        tilt_speed = tilt * max_tilt_speed

        # Update command labels to show speed
        self.cmd_pan_label.setText(f"{pan_speed:.1f} °/s")
        self.cmd_tilt_label.setText(f"{tilt_speed:.1f} °/s")

        # Emit speed commands
        self.pan_speed_changed.emit(pan_speed)
        self.tilt_speed_changed.emit(tilt_speed)
        logger.debug(f"Trackpad speed: Pan={pan_speed:.1f} °/s, Tilt={tilt_speed:.1f} °/s")

    def on_trackpad_released(self):
        """Handle trackpad release - stop movement by setting speed to 0."""
        # Stop by setting speed to 0
        self.pan_speed_changed.emit(0.0)
        self.tilt_speed_changed.emit(0.0)

        # Update labels
        self.cmd_pan_label.setText("0.0 °/s")
        self.cmd_tilt_label.setText("0.0 °/s")

        logger.debug("Trackpad released - speeds set to 0")

    def on_camera_button_clicked(self, button: QPushButton):
        """Handle camera button selection."""
        camera_id = button.property("camera")
        camera_name = button.text()
        logger.info(f"Active camera changed to: {camera_name} ({camera_id})")

    def get_selected_camera(self) -> str:
        """Get the currently selected camera module name (Camera1, Camera2, or Camera3)."""
        selected_button = self.camera_button_group.checkedButton()
        if selected_button:
            return selected_button.property("camera")
        return "Camera1"  # Default fallback

    def on_zoom_pressed(self, direction: int):
        """Handle zoom button press."""
        camera = self.get_selected_camera()
        self.zoom_command.emit(direction)
        logger.debug(f"Zoom {'in' if direction > 0 else 'out'} pressed for {camera}")

    def on_zoom_released(self):
        """Handle zoom button release - send camera-specific stop."""
        camera = self.get_selected_camera()
        # Emit 0 direction to send ZoomStop command for this specific camera
        self.zoom_command.emit(0)
        logger.debug(f"Zoom stop for {camera}")

    def on_focus_pressed(self, direction: int):
        """Handle focus button press."""
        camera = self.get_selected_camera()
        self.focus_command.emit(direction)
        logger.debug(f"Focus {'far' if direction > 0 else 'near'} pressed for {camera}")

    def on_focus_released(self):
        """Handle focus button release - send camera-specific stop."""
        camera = self.get_selected_camera()
        # Emit 0 direction to send FocusStop command for this specific camera
        self.focus_command.emit(0)
        logger.debug(f"Focus stop for {camera}")

    def on_pan_speed_changed(self, value: int):
        """Handle pan speed slider change."""
        speed = value / 100.0  # Convert to 0.0 to 1.0
        self.pan_speed_label.setText(f"{speed:.2f}")
        self.pan_speed_changed.emit(speed)
        logger.debug(f"Pan speed: {speed:.2f}")

    def on_tilt_speed_changed(self, value: int):
        """Handle tilt speed slider change."""
        speed = value / 100.0  # Convert to 0.0 to 1.0
        self.tilt_speed_label.setText(f"{speed:.2f}")
        self.tilt_speed_changed.emit(speed)
        logger.debug(f"Tilt speed: {speed:.2f}")

    def on_zoom_speed_changed(self, value: int):
        """Handle zoom speed slider change."""
        speed = value / 100.0  # Convert to -1.0 to +1.0
        self.zoom_speed_label.setText(f"{speed:.2f}")
        self.zoom_speed_changed.emit(speed)
        logger.debug(f"Zoom speed: {speed:.2f}")

    def on_focus_speed_changed(self, value: int):
        """Handle focus speed slider change."""
        speed = value / 100.0  # Convert to -1.0 to +1.0
        self.focus_speed_label.setText(f"{speed:.2f}")
        self.focus_speed_changed.emit(speed)
        logger.debug(f"Focus speed: {speed:.2f}")

    def on_arrow_up_pressed(self):
        """Handle up arrow pressed - use tilt slider value."""
        tilt_speed = self.tilt_speed_slider.value() / 100.0
        # Use positive speed for up, or default if slider is at 0
        if tilt_speed == 0:
            tilt_speed = 0.5  # Default speed
        else:
            tilt_speed = abs(tilt_speed)  # Always positive for up

        # Update commanded label
        self.cmd_tilt_label.setText(f"+{tilt_speed:.1f} °/s")

        self.tilt_speed_changed.emit(tilt_speed)
        logger.debug(f"Arrow UP: Tilt speed {tilt_speed:.2f}")

    def on_arrow_down_pressed(self):
        """Handle down arrow pressed - use tilt slider value."""
        tilt_speed = self.tilt_speed_slider.value() / 100.0
        # Use negative speed for down, or default if slider is at 0
        if tilt_speed == 0:
            tilt_speed = -0.5  # Default speed
        else:
            tilt_speed = -abs(tilt_speed)  # Always negative for down

        # Update commanded label
        self.cmd_tilt_label.setText(f"{tilt_speed:.1f} °/s")

        self.tilt_speed_changed.emit(tilt_speed)
        logger.debug(f"Arrow DOWN: Tilt speed {tilt_speed:.2f}")

    def on_arrow_left_pressed(self):
        """Handle left arrow pressed - use pan slider value."""
        pan_speed = self.pan_speed_slider.value() / 100.0
        # Use negative speed for left, or default if slider is at 0
        if pan_speed == 0:
            pan_speed = -0.5  # Default speed
        else:
            pan_speed = -abs(pan_speed)  # Always negative for left

        # Update commanded label
        self.cmd_pan_label.setText(f"{pan_speed:.1f} °/s")

        self.pan_speed_changed.emit(pan_speed)
        logger.debug(f"Arrow LEFT: Pan speed {pan_speed:.2f}")

    def on_arrow_right_pressed(self):
        """Handle right arrow pressed - use pan slider value."""
        pan_speed = self.pan_speed_slider.value() / 100.0
        # Use positive speed for right, or default if slider is at 0
        if pan_speed == 0:
            pan_speed = 0.5  # Default speed
        else:
            pan_speed = abs(pan_speed)  # Always positive for right

        # Update commanded label
        self.cmd_pan_label.setText(f"+{pan_speed:.1f} °/s")

        self.pan_speed_changed.emit(pan_speed)
        logger.debug(f"Arrow RIGHT: Pan speed {pan_speed:.2f}")

    def on_arrow_released(self):
        """Handle arrow button released - stop movement."""
        # Update commanded labels
        self.cmd_pan_label.setText("0.0 °/s")
        self.cmd_tilt_label.setText("0.0 °/s")

        self.pan_speed_changed.emit(0.0)
        self.tilt_speed_changed.emit(0.0)
        logger.debug("Arrow released - stopped")

    def update_actual_position(self, pan: float, tilt: float):
        """Update actual position from telemetry."""
        self.actual_pan = pan
        self.actual_tilt = tilt
        self.actual_pan_label.setText(f"{pan:.1f}°")
        self.actual_tilt_label.setText(f"{tilt:.1f}°")

