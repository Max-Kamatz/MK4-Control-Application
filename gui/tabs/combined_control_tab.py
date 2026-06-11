"""
gui/tabs/combined_control_tab.py
Combined video display and PTZ control tab - shows streams and trackpad control together.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                             QGroupBox, QLabel, QGridLayout, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal
from gui.widgets.rtsp_video_widget import RTSPVideoWidget
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
    zoom_command = pyqtSignal(int)      # +1 = in, -1 = out
    zoom_stop = pyqtSignal()

    # Focus signals
    focus_command = pyqtSignal(int)     # +1 = far, -1 = near
    focus_stop = pyqtSignal()

    # Home/connection
    home_requested = pyqtSignal()
    connection_toggle = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.actual_pan = None
        self.actual_tilt = None
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Left side: Video streams
        left_widget = self.create_video_section()

        # Right side: PTZ control
        right_widget = self.create_control_section()

        # Splitter to allow resizing
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)  # Video gets more space
        splitter.setStretchFactor(1, 1)  # Control panel

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        logger.info("Combined control tab initialized")

    def create_video_section(self) -> QWidget:
        """Create video display section with 3 camera feeds."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(5)

        title = QLabel("<b>📹 Live Camera Feeds</b>")
        title.setStyleSheet("font-size: 14pt; padding: 5px;")
        layout.addWidget(title)

        # Video grid (2x2 layout, 3 streams)
        video_grid = QGridLayout()
        video_grid.setSpacing(10)

        thermal_config = self.config['rtsp_streams']['thermal']
        self.thermal_widget = RTSPVideoWidget(
            thermal_config['url'],
            thermal_config['label']
        )

        daylight_config = self.config['rtsp_streams']['daylight']
        self.daylight_widget = RTSPVideoWidget(
            daylight_config['url'],
            daylight_config['label']
        )

        swir_config = self.config['rtsp_streams']['swir']
        self.swir_widget = RTSPVideoWidget(
            swir_config['url'],
            swir_config['label']
        )

        video_grid.addWidget(self.thermal_widget, 0, 0)
        video_grid.addWidget(self.daylight_widget, 0, 1)
        video_grid.addWidget(self.swir_widget, 1, 0)

        layout.addLayout(video_grid)
        widget.setLayout(layout)
        return widget

    def create_control_section(self) -> QWidget:
        """Create PTZ control section with trackpad and status."""
        widget = QWidget()
        widget.setMaximumWidth(350)
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Connection status group
        status_group = QGroupBox("Connection")
        status_layout = QVBoxLayout()

        self.connection_indicator = QLabel("● Disconnected")
        self.connection_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_indicator.setStyleSheet("""
            font-size: 13pt;
            font-weight: bold;
            color: #ff4444;
            padding: 15px;
        """)

        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("padding: 10px; font-size: 11pt;")
        self.connect_button.clicked.connect(self.connection_toggle.emit)

        status_layout.addWidget(self.connection_indicator)
        status_layout.addWidget(self.connect_button)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # PTZ Trackpad control
        self.ptz_control = PTZControlWidget()
        self.ptz_control.pan_tilt_moved.connect(self.on_trackpad_moved)
        self.ptz_control.pan_tilt_released.connect(self.on_trackpad_released)
        self.ptz_control.zoom_pressed.connect(self.on_zoom_pressed)
        self.ptz_control.zoom_released.connect(self.on_zoom_released)
        self.ptz_control.focus_pressed.connect(self.on_focus_pressed)
        self.ptz_control.focus_released.connect(self.on_focus_released)
        layout.addWidget(self.ptz_control)

        # Position feedback group
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

        # Home button
        self.home_button = QPushButton("🏠 Home Position (0°, 0°)")
        self.home_button.setStyleSheet("""
            QPushButton {
                background-color: #2a82da;
                padding: 12px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a92ea;
            }
        """)
        self.home_button.clicked.connect(self.home_requested.emit)
        layout.addWidget(self.home_button)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def on_trackpad_moved(self, pan: float, tilt: float):
        """Handle trackpad movement - normalize and emit command."""
        # Convert from normalized (-1.0 to 1.0) to degrees
        # Assuming max speed: pan ±180°, tilt ±90°
        pan_degrees = pan * 180.0
        tilt_degrees = tilt * 90.0

        self.cmd_pan_label.setText(f"{pan_degrees:.1f}°")
        self.cmd_tilt_label.setText(f"{tilt_degrees:.1f}°")

        self.pan_tilt_command.emit(pan, tilt)
        logger.debug(f"Trackpad: Pan={pan:.3f}, Tilt={tilt:.3f}")

    def on_trackpad_released(self):
        """Handle trackpad release - stop movement."""
        self.pan_tilt_stop.emit()
        logger.debug("Trackpad released - stop command")

    def on_zoom_pressed(self, direction: int):
        """Handle zoom button press."""
        self.zoom_command.emit(direction)
        logger.debug(f"Zoom {'in' if direction > 0 else 'out'} pressed")

    def on_zoom_released(self):
        """Handle zoom button release."""
        self.zoom_stop.emit()
        logger.debug("Zoom released")

    def on_focus_pressed(self, direction: int):
        """Handle focus button press."""
        self.focus_command.emit(direction)
        logger.debug(f"Focus {'far' if direction > 0 else 'near'} pressed")

    def on_focus_released(self):
        """Handle focus button release."""
        self.focus_stop.emit()
        logger.debug("Focus released")

    def update_actual_position(self, pan: float, tilt: float):
        """Update actual position from telemetry."""
        self.actual_pan = pan
        self.actual_tilt = tilt
        self.actual_pan_label.setText(f"{pan:.1f}°")
        self.actual_tilt_label.setText(f"{tilt:.1f}°")

    def update_connection_status(self, connected: bool):
        """Update connection status indicator."""
        if connected:
            self.connection_indicator.setText("● Connected")
            self.connection_indicator.setStyleSheet("""
                font-size: 13pt;
                font-weight: bold;
                color: #44ff44;
                padding: 15px;
            """)
            self.connect_button.setText("Disconnect")
        else:
            self.connection_indicator.setText("● Disconnected")
            self.connection_indicator.setStyleSheet("""
                font-size: 13pt;
                font-weight: bold;
                color: #ff4444;
                padding: 15px;
            """)
            self.connect_button.setText("Connect")

    def closeEvent(self, event):
        """Clean up video streams on close."""
        if hasattr(self, 'thermal_widget'):
            self.thermal_widget.stream_thread.stop()
        if hasattr(self, 'daylight_widget'):
            self.daylight_widget.stream_thread.stop()
        if hasattr(self, 'swir_widget'):
            self.swir_widget.stream_thread.stop()
        event.accept()
