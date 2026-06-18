"""
gui/tabs/control_tab.py
Control tab with LEFT side scrollable settings (480px fixed) and RIGHT side expanding video feeds.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QSlider, QPushButton, QGroupBox, QLineEdit, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from utils.constants import load_config, PAN_MIN, PAN_MAX, TILT_MIN, TILT_MAX
from utils.logger import setup_logger

logger = setup_logger()

class ControlTab(QWidget):
    pan_tilt_changed = pyqtSignal(float, float)
    home_requested = pyqtSignal()

    def __init__(self, video_manager=None):
        super().__init__()
        self.config = load_config()
        self.commanded_pan = 0.0
        self.commanded_tilt = 0.0
        self.actual_pan = 0.0
        self.actual_tilt = 0.0
        self.video_manager = video_manager
        self.video_placeholder = None  # Will hold the shared video display
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Control settings (fixed width 480px with scroll)
        left_widget = self.create_control_section()

        # Right side: Video streams (expands to fill space)
        right_widget = self.create_video_section()

        # Use simple horizontal layout - control panel has fixed width, video expands
        main_layout.addWidget(left_widget, 0)   # Control panel fixed width (no stretch)
        main_layout.addWidget(right_widget, 1)  # Video expands (stretch factor 1)

        self.setLayout(main_layout)
        logger.info("Control tab initialized")

    def create_control_section(self) -> QWidget:
        """Create left side control section with fixed width and scrolling."""
        # Container widget with fixed width
        container = QWidget()
        container.setFixedWidth(480)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Scrollable content widget
        scroll_content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Status section with IP and connection
        status_group = self.create_status_section()
        layout.addWidget(status_group)

        # Gimbal control section
        control_group = self.create_gimbal_control()
        layout.addWidget(control_group)

        # Position feedback section
        position_group = self.create_position_display()
        layout.addWidget(position_group)

        layout.addStretch()

        scroll_content.setLayout(layout)
        scroll.setWidget(scroll_content)

        container_layout.addWidget(scroll)
        container.setLayout(container_layout)

        return container

    def create_status_section(self) -> QGroupBox:
        """Create connection status section."""
        group = QGroupBox("Connection Status")
        layout = QVBoxLayout()

        # IP Address input
        ip_label = QLabel("Target IP Address:")
        ip_label.setStyleSheet("font-size: 10pt; font-weight: bold;")
        layout.addWidget(ip_label)

        self.ip_input = QLineEdit()
        self.ip_input.setText(self.config['network']['target_ip'])
        self.ip_input.setPlaceholderText("192.168.1.100")
        self.ip_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                font-size: 11pt;
                font-family: 'Courier New', monospace;
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border: 2px solid #2a82da;
            }
        """)
        layout.addWidget(self.ip_input)

        self.connection_indicator = QLabel("● Disconnected")
        self.connection_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_indicator.setStyleSheet("""
            font-size: 14pt;
            font-weight: bold;
            color: #ff4444;
            padding: 20px;
        """)

        self.reconnect_button = QPushButton("Connect")
        self.reconnect_button.setStyleSheet("padding: 10px; font-size: 11pt;")

        layout.addWidget(self.connection_indicator)
        layout.addWidget(self.reconnect_button)

        group.setLayout(layout)
        return group

    def create_gimbal_control(self) -> QGroupBox:
        """Create gimbal control section."""
        group = QGroupBox("Gimbal Control")
        layout = QVBoxLayout()

        pan_layout = QHBoxLayout()
        pan_label = QLabel("Pan:")
        pan_label.setMinimumWidth(60)
        self.pan_slider = QSlider(Qt.Orientation.Horizontal)
        self.pan_slider.setMinimum(PAN_MIN)
        self.pan_slider.setMaximum(PAN_MAX)
        self.pan_slider.setValue(0)
        self.pan_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.pan_slider.setTickInterval(45)
        self.pan_value_label = QLabel("0°")
        self.pan_value_label.setMinimumWidth(50)
        self.pan_value_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        pan_layout.addWidget(pan_label)
        pan_layout.addWidget(self.pan_slider)
        pan_layout.addWidget(self.pan_value_label)

        tilt_layout = QHBoxLayout()
        tilt_label = QLabel("Tilt:")
        tilt_label.setMinimumWidth(60)
        self.tilt_slider = QSlider(Qt.Orientation.Horizontal)
        self.tilt_slider.setMinimum(TILT_MIN)
        self.tilt_slider.setMaximum(TILT_MAX)
        self.tilt_slider.setValue(0)
        self.tilt_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.tilt_slider.setTickInterval(30)
        self.tilt_value_label = QLabel("0°")
        self.tilt_value_label.setMinimumWidth(50)
        self.tilt_value_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        tilt_layout.addWidget(tilt_label)
        tilt_layout.addWidget(self.tilt_slider)
        tilt_layout.addWidget(self.tilt_value_label)

        self.home_button = QPushButton("Home Position (0°, 0°)")
        self.home_button.setStyleSheet("""
            QPushButton {
                background-color: #2a82da;
                padding: 10px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a92ea;
            }
        """)

        layout.addLayout(pan_layout)
        layout.addLayout(tilt_layout)
        layout.addSpacing(20)
        layout.addWidget(self.home_button)

        self.pan_slider.valueChanged.connect(self.on_pan_changed)
        self.tilt_slider.valueChanged.connect(self.on_tilt_changed)
        self.home_button.clicked.connect(self.on_home_clicked)

        group.setLayout(layout)
        return group

    def create_position_display(self) -> QGroupBox:
        """Create position feedback section."""
        group = QGroupBox("Position Feedback")
        layout = QGridLayout()

        layout.addWidget(QLabel("<b>Commanded:</b>"), 0, 0, 1, 2)

        layout.addWidget(QLabel("Pan:"), 1, 0)
        self.cmd_pan_label = QLabel("0.0°")
        self.cmd_pan_label.setStyleSheet("font-size: 14pt; color: #2a82da;")
        layout.addWidget(self.cmd_pan_label, 1, 1)

        layout.addWidget(QLabel("Tilt:"), 2, 0)
        self.cmd_tilt_label = QLabel("0.0°")
        self.cmd_tilt_label.setStyleSheet("font-size: 14pt; color: #2a82da;")
        layout.addWidget(self.cmd_tilt_label, 2, 1)

        layout.addWidget(QLabel("<b>Actual:</b>"), 3, 0, 1, 2)

        layout.addWidget(QLabel("Pan:"), 4, 0)
        self.actual_pan_label = QLabel("N/A")
        self.actual_pan_label.setStyleSheet("font-size: 14pt; color: #44ff44;")
        layout.addWidget(self.actual_pan_label, 4, 1)

        layout.addWidget(QLabel("Tilt:"), 5, 0)
        self.actual_tilt_label = QLabel("N/A")
        self.actual_tilt_label.setStyleSheet("font-size: 14pt; color: #44ff44;")
        layout.addWidget(self.actual_tilt_label, 5, 1)

        layout.setRowStretch(6, 1)

        group.setLayout(layout)
        return group

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
            logger.debug(f"Video display reparented to {self.__class__.__name__}")

    def on_pan_changed(self, value: int):
        self.commanded_pan = float(value)
        self.pan_value_label.setText(f"{value}°")
        self.cmd_pan_label.setText(f"{value}.0°")
        self.pan_tilt_changed.emit(self.commanded_pan, self.commanded_tilt)

    def on_tilt_changed(self, value: int):
        self.commanded_tilt = float(value)
        self.tilt_value_label.setText(f"{value}°")
        self.cmd_tilt_label.setText(f"{value}.0°")
        self.pan_tilt_changed.emit(self.commanded_pan, self.commanded_tilt)

    def on_home_clicked(self):
        self.pan_slider.setValue(0)
        self.tilt_slider.setValue(0)
        self.home_requested.emit()

    def update_actual_position(self, pan: float, tilt: float):
        self.actual_pan = pan
        self.actual_tilt = tilt
        self.actual_pan_label.setText(f"{pan:.1f}°")
        self.actual_tilt_label.setText(f"{tilt:.1f}°")

    def get_target_ip(self) -> str:
        """Get the current target IP from the input field."""
        return self.ip_input.text().strip()

    def update_connection_status(self, connected: bool):
        if connected:
            self.connection_indicator.setText("● Connected")
            self.connection_indicator.setStyleSheet("""
                font-size: 14pt;
                font-weight: bold;
                color: #44ff44;
                padding: 20px;
            """)
            self.reconnect_button.setText("Disconnect")
            self.ip_input.setEnabled(False)  # Disable IP changes while connected
        else:
            self.connection_indicator.setText("● Disconnected")
            self.connection_indicator.setStyleSheet("""
                font-size: 14pt;
                font-weight: bold;
                color: #ff4444;
                padding: 20px;
            """)
            self.reconnect_button.setText("Connect")
            self.ip_input.setEnabled(True)  # Enable IP changes when disconnected




