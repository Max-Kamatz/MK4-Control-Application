"""
gui/tabs/motor_settings_tab.py
Motor Settings tab - consolidates all gimbal/motor configuration features.
Includes calibration, limits, speed settings, behavior, acceleration, and homing.
Layout: LEFT side with scrollable settings (480px), RIGHT side with video feeds (expanding).
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QGridLayout, QPushButton, QLineEdit, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from utils.constants import load_config
from utils.logger import setup_logger

logger = setup_logger()


class MotorSettingsTab(QWidget):
    """
    Motor Settings tab for gimbal/motor configuration.
    Contains 8 groups: Calibration, Limits, Speed, Behavior, Acceleration, Homing, System, and Slave Zoom.
    Layout: LEFT side (480px) with scrollable settings, RIGHT side with expanding video feeds.
    """

    # Motor Calibration signals
    pan_set_zero_requested = pyqtSignal()
    pan_reset_zero_requested = pyqtSignal()
    pan_zero_pos_changed = pyqtSignal(float)  # degrees
    tilt_set_zero_requested = pyqtSignal()
    tilt_reset_zero_requested = pyqtSignal()
    tilt_zero_pos_changed = pyqtSignal(float)  # degrees

    # Motor Limits signals
    pan_left_limit_changed = pyqtSignal(float)  # degrees 0-360
    pan_right_limit_changed = pyqtSignal(float)  # degrees 0-360
    tilt_up_limit_changed = pyqtSignal(float)  # degrees -90 to +90
    tilt_down_limit_changed = pyqtSignal(float)  # degrees -90 to +90

    # Motor Speed signals
    pan_max_speed_changed = pyqtSignal(float)  # degrees/sec
    pan_position_speed_changed = pyqtSignal(float)  # degrees/sec
    tilt_max_speed_changed = pyqtSignal(float)  # degrees/sec
    tilt_position_speed_changed = pyqtSignal(float)  # degrees/sec

    # Motor Behavior signals
    pan_invert_movement_changed = pyqtSignal(bool)  # True = inverted
    tilt_invert_movement_changed = pyqtSignal(bool)  # True = inverted
    zoom_dependent_mode_changed = pyqtSignal(bool)  # True = enabled
    block_pt_changed = pyqtSignal(bool)  # True = blocked

    # Acceleration/Deceleration signals
    acc_vel_max_changed = pyqtSignal(float)  # max acceleration velocity
    acc_dec_max_changed = pyqtSignal(float)  # max deceleration rate
    acc_dec_rate_changed = pyqtSignal(float)  # acceleration rate
    acc_dec_vstop_changed = pyqtSignal(float)  # velocity at stop

    # Homing signals
    homing_delay_mode_changed = pyqtSignal(bool)  # True = enabled
    homing_delay_time_changed = pyqtSignal(int)  # seconds

    # System Control signals
    reset_controller_requested = pyqtSignal()
    query_all_motor_settings_requested = pyqtSignal()

    # Slave Zoom signals
    slave_zoom_mode_changed = pyqtSignal(bool)  # True = enabled
    slave_zoom_master_changed = pyqtSignal(int)  # 0=Cam1, 1=Cam2, 2=Cam3

    # Query signals
    query_pan_limits_requested = pyqtSignal()
    query_tilt_limits_requested = pyqtSignal()
    query_homing_requested = pyqtSignal()

    def __init__(self, video_manager=None):
        super().__init__()
        self.config = load_config()
        self.video_manager = video_manager
        self.video_placeholder = None  # Will hold the shared video display
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """Initialize the Motor Settings UI with LEFT settings panel and RIGHT video feeds."""
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Scrollable settings panel (fixed width 480px)
        left_widget = self.create_settings_section()

        # Right side: Video streams (expands to fill space)
        right_widget = self.create_video_section()

        # Use simple horizontal layout - settings panel has fixed width, video expands
        main_layout.addWidget(left_widget, 0)   # Settings panel fixed width (no stretch)
        main_layout.addWidget(right_widget, 1)  # Video expands (stretch factor 1)

        self.setLayout(main_layout)

        logger.info("Motor Settings tab initialized with left settings panel and right video feeds")

    def create_settings_section(self) -> QWidget:
        """Create scrollable settings panel (LEFT side, 480px fixed width)."""
        # Container widget with fixed width
        container = QWidget()
        container.setFixedWidth(480)
        container_layout = QVBoxLayout()
        container_layout.setSpacing(0)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Settings content widget
        settings_widget = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)
        settings_layout.setContentsMargins(10, 10, 10, 10)

        # Group 1: Motor Calibration
        calibration_group = self.create_calibration_group()
        settings_layout.addWidget(calibration_group)

        # Group 2: Motor Limits
        limits_group = self.create_limits_group()
        settings_layout.addWidget(limits_group)

        # Group 3: Motor Speed Settings
        speed_group = self.create_speed_group()
        settings_layout.addWidget(speed_group)

        # Group 4: Motor Behavior
        behavior_group = self.create_behavior_group()
        settings_layout.addWidget(behavior_group)

        # Group 5: Acceleration/Deceleration
        acceleration_group = self.create_acceleration_group()
        settings_layout.addWidget(acceleration_group)

        # Group 6: Homing
        homing_group = self.create_homing_group()
        settings_layout.addWidget(homing_group)

        # Group 7: System Controls
        system_group = self.create_system_group()
        settings_layout.addWidget(system_group)

        # Group 8: Slave Zoom (System Coordination)
        slave_zoom_group = self.create_slave_zoom_group()
        settings_layout.addWidget(slave_zoom_group)

        settings_layout.addStretch()
        settings_widget.setLayout(settings_layout)

        scroll_area.setWidget(settings_widget)
        container_layout.addWidget(scroll_area)
        container.setLayout(container_layout)

        return container

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

    def create_calibration_group(self) -> QGroupBox:
        """Create Motor Calibration group."""
        group = QGroupBox("Motor Calibration")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Pan Calibration
        layout.addWidget(QLabel("<b>Pan Calibration:</b>"), 0, 0, 1, 3)

        self.pan_set_zero_button = QPushButton("Set Zero")
        layout.addWidget(self.pan_set_zero_button, 1, 0)

        self.pan_reset_zero_button = QPushButton("Reset Zero")
        layout.addWidget(self.pan_reset_zero_button, 1, 1)

        layout.addWidget(QLabel("Zero Position (°):"), 2, 0)
        self.pan_zero_pos_input = QLineEdit()
        self.pan_zero_pos_input.setPlaceholderText("0.0 - 360.0")
        layout.addWidget(self.pan_zero_pos_input, 2, 1)
        self.pan_zero_pos_button = QPushButton("Set")
        layout.addWidget(self.pan_zero_pos_button, 2, 2)

        # Tilt Calibration
        layout.addWidget(QLabel("<b>Tilt Calibration:</b>"), 3, 0, 1, 3)

        self.tilt_set_zero_button = QPushButton("Set Zero")
        layout.addWidget(self.tilt_set_zero_button, 4, 0)

        self.tilt_reset_zero_button = QPushButton("Reset Zero")
        layout.addWidget(self.tilt_reset_zero_button, 4, 1)

        layout.addWidget(QLabel("Zero Position (°):"), 5, 0)
        self.tilt_zero_pos_input = QLineEdit()
        self.tilt_zero_pos_input.setPlaceholderText("-90.0 - 90.0")
        layout.addWidget(self.tilt_zero_pos_input, 5, 1)
        self.tilt_zero_pos_button = QPushButton("Set")
        layout.addWidget(self.tilt_zero_pos_button, 5, 2)

        group.setLayout(layout)
        return group

    def create_limits_group(self) -> QGroupBox:
        """Create Motor Limits group."""
        group = QGroupBox("Motor Limits")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Pan Limits
        layout.addWidget(QLabel("<b>Pan Limits (degrees):</b>"), 0, 0, 1, 3)

        layout.addWidget(QLabel("Left Limit:"), 1, 0)
        self.pan_left_limit_input = QLineEdit()
        self.pan_left_limit_input.setPlaceholderText("0.0 - 360.0")
        layout.addWidget(self.pan_left_limit_input, 1, 1)
        self.pan_left_limit_button = QPushButton("Set")
        layout.addWidget(self.pan_left_limit_button, 1, 2)

        layout.addWidget(QLabel("Right Limit:"), 2, 0)
        self.pan_right_limit_input = QLineEdit()
        self.pan_right_limit_input.setPlaceholderText("0.0 - 360.0")
        layout.addWidget(self.pan_right_limit_input, 2, 1)
        self.pan_right_limit_button = QPushButton("Set")
        layout.addWidget(self.pan_right_limit_button, 2, 2)

        self.query_pan_limits_button = QPushButton("Query Pan Limits")
        layout.addWidget(self.query_pan_limits_button, 3, 0, 1, 3)

        # Tilt Limits
        layout.addWidget(QLabel("<b>Tilt Limits (degrees):</b>"), 4, 0, 1, 3)

        layout.addWidget(QLabel("Up Limit:"), 5, 0)
        self.tilt_up_limit_input = QLineEdit()
        self.tilt_up_limit_input.setPlaceholderText("-90.0 - 90.0")
        layout.addWidget(self.tilt_up_limit_input, 5, 1)
        self.tilt_up_limit_button = QPushButton("Set")
        layout.addWidget(self.tilt_up_limit_button, 5, 2)

        layout.addWidget(QLabel("Down Limit:"), 6, 0)
        self.tilt_down_limit_input = QLineEdit()
        self.tilt_down_limit_input.setPlaceholderText("-90.0 - 90.0")
        layout.addWidget(self.tilt_down_limit_input, 6, 1)
        self.tilt_down_limit_button = QPushButton("Set")
        layout.addWidget(self.tilt_down_limit_button, 6, 2)

        self.query_tilt_limits_button = QPushButton("Query Tilt Limits")
        layout.addWidget(self.query_tilt_limits_button, 7, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_speed_group(self) -> QGroupBox:
        """Create Motor Speed Settings group."""
        group = QGroupBox("Motor Speed Settings")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Pan Speed
        layout.addWidget(QLabel("<b>Pan Speed:</b>"), 0, 0, 1, 3)

        layout.addWidget(QLabel("Max Speed (°/s):"), 1, 0)
        self.pan_max_speed_input = QLineEdit()
        self.pan_max_speed_input.setPlaceholderText("e.g., 90.0")
        layout.addWidget(self.pan_max_speed_input, 1, 1)
        self.pan_max_speed_button = QPushButton("Set")
        layout.addWidget(self.pan_max_speed_button, 1, 2)

        layout.addWidget(QLabel("Position Speed (°/s):"), 2, 0)
        self.pan_position_speed_input = QLineEdit()
        self.pan_position_speed_input.setPlaceholderText("Speed for ToPos")
        layout.addWidget(self.pan_position_speed_input, 2, 1)
        self.pan_position_speed_button = QPushButton("Set")
        layout.addWidget(self.pan_position_speed_button, 2, 2)

        # Tilt Speed
        layout.addWidget(QLabel("<b>Tilt Speed:</b>"), 3, 0, 1, 3)

        layout.addWidget(QLabel("Max Speed (°/s):"), 4, 0)
        self.tilt_max_speed_input = QLineEdit()
        self.tilt_max_speed_input.setPlaceholderText("e.g., 45.0")
        layout.addWidget(self.tilt_max_speed_input, 4, 1)
        self.tilt_max_speed_button = QPushButton("Set")
        layout.addWidget(self.tilt_max_speed_button, 4, 2)

        layout.addWidget(QLabel("Position Speed (°/s):"), 5, 0)
        self.tilt_position_speed_input = QLineEdit()
        self.tilt_position_speed_input.setPlaceholderText("Speed for ToPos")
        layout.addWidget(self.tilt_position_speed_input, 5, 1)
        self.tilt_position_speed_button = QPushButton("Set")
        layout.addWidget(self.tilt_position_speed_button, 5, 2)

        group.setLayout(layout)
        return group

    def create_behavior_group(self) -> QGroupBox:
        """Create Motor Behavior group."""
        group = QGroupBox("Motor Behavior")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Pan Invert Movement
        layout.addWidget(QLabel("Pan Invert Movement:"), 0, 0, 1, 2)
        pan_invert_layout = QHBoxLayout()
        self.pan_invert_on_button = QPushButton("On")
        self.pan_invert_off_button = QPushButton("Off")
        pan_invert_layout.addWidget(self.pan_invert_on_button)
        pan_invert_layout.addWidget(self.pan_invert_off_button)
        layout.addLayout(pan_invert_layout, 1, 0, 1, 3)

        # Tilt Invert Movement
        layout.addWidget(QLabel("Tilt Invert Movement:"), 2, 0, 1, 2)
        tilt_invert_layout = QHBoxLayout()
        self.tilt_invert_on_button = QPushButton("On")
        self.tilt_invert_off_button = QPushButton("Off")
        tilt_invert_layout.addWidget(self.tilt_invert_on_button)
        tilt_invert_layout.addWidget(self.tilt_invert_off_button)
        layout.addLayout(tilt_invert_layout, 3, 0, 1, 3)

        # Zoom Dependent Mode
        layout.addWidget(QLabel("Zoom Dependent Mode:"), 4, 0, 1, 2)
        zoom_dep_layout = QHBoxLayout()
        self.zoom_dependent_enable_button = QPushButton("Enable")
        self.zoom_dependent_disable_button = QPushButton("Disable")
        zoom_dep_layout.addWidget(self.zoom_dependent_enable_button)
        zoom_dep_layout.addWidget(self.zoom_dependent_disable_button)
        layout.addLayout(zoom_dep_layout, 5, 0, 1, 3)

        # Block PT
        layout.addWidget(QLabel("Block PT Movement:"), 6, 0, 1, 2)
        block_pt_layout = QHBoxLayout()
        self.block_pt_on_button = QPushButton("On")
        self.block_pt_off_button = QPushButton("Off")
        block_pt_layout.addWidget(self.block_pt_on_button)
        block_pt_layout.addWidget(self.block_pt_off_button)
        layout.addLayout(block_pt_layout, 7, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_acceleration_group(self) -> QGroupBox:
        """Create Acceleration/Deceleration group."""
        group = QGroupBox("Acceleration/Deceleration")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("Acc Vel Max:"), 0, 0)
        self.acc_vel_max_input = QLineEdit()
        self.acc_vel_max_input.setPlaceholderText("Max acceleration velocity")
        layout.addWidget(self.acc_vel_max_input, 0, 1)
        self.acc_vel_max_button = QPushButton("Set")
        layout.addWidget(self.acc_vel_max_button, 0, 2)

        layout.addWidget(QLabel("Acc Dec Max:"), 1, 0)
        self.acc_dec_max_input = QLineEdit()
        self.acc_dec_max_input.setPlaceholderText("Max deceleration rate")
        layout.addWidget(self.acc_dec_max_input, 1, 1)
        self.acc_dec_max_button = QPushButton("Set")
        layout.addWidget(self.acc_dec_max_button, 1, 2)

        layout.addWidget(QLabel("Acc Dec Rate:"), 2, 0)
        self.acc_dec_rate_input = QLineEdit()
        self.acc_dec_rate_input.setPlaceholderText("Acceleration rate")
        layout.addWidget(self.acc_dec_rate_input, 2, 1)
        self.acc_dec_rate_button = QPushButton("Set")
        layout.addWidget(self.acc_dec_rate_button, 2, 2)

        layout.addWidget(QLabel("Acc Dec Vstop:"), 3, 0)
        self.acc_dec_vstop_input = QLineEdit()
        self.acc_dec_vstop_input.setPlaceholderText("Velocity at stop")
        layout.addWidget(self.acc_dec_vstop_input, 3, 1)
        self.acc_dec_vstop_button = QPushButton("Set")
        layout.addWidget(self.acc_dec_vstop_button, 3, 2)

        group.setLayout(layout)
        return group

    def create_homing_group(self) -> QGroupBox:
        """Create Homing group."""
        group = QGroupBox("Homing")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("Delays homing procedure on startup:"), 0, 0, 1, 3)

        homing_toggle_layout = QHBoxLayout()
        self.homing_delay_enable_button = QPushButton("Enable")
        self.homing_delay_disable_button = QPushButton("Disable")
        homing_toggle_layout.addWidget(self.homing_delay_enable_button)
        homing_toggle_layout.addWidget(self.homing_delay_disable_button)
        layout.addLayout(homing_toggle_layout, 1, 0, 1, 3)

        layout.addWidget(QLabel("Delay Time (seconds):"), 2, 0)
        self.homing_delay_time_input = QLineEdit()
        self.homing_delay_time_input.setPlaceholderText("Seconds")
        layout.addWidget(self.homing_delay_time_input, 2, 1)
        self.homing_delay_time_button = QPushButton("Set")
        layout.addWidget(self.homing_delay_time_button, 2, 2)

        self.query_homing_button = QPushButton("Query Homing")
        layout.addWidget(self.query_homing_button, 3, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_system_group(self) -> QGroupBox:
        """Create System Controls group."""
        group = QGroupBox("System Controls")
        layout = QGridLayout()
        layout.setSpacing(8)

        self.reset_controller_button = QPushButton("Reset Controller")
        layout.addWidget(self.reset_controller_button, 0, 0)

        self.query_all_motor_button = QPushButton("Query All Motor Settings")
        layout.addWidget(self.query_all_motor_button, 1, 0)

        group.setLayout(layout)
        return group

    def create_slave_zoom_group(self) -> QGroupBox:
        """Create Slave Zoom (System Coordination) group."""
        group = QGroupBox("Slave Zoom (System Coordination)")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("Enable slave zoom (all cameras follow one):"), 0, 0, 1, 3)

        slave_zoom_toggle_layout = QHBoxLayout()
        self.slave_zoom_enable_button = QPushButton("Enable")
        self.slave_zoom_disable_button = QPushButton("Disable")
        slave_zoom_toggle_layout.addWidget(self.slave_zoom_enable_button)
        slave_zoom_toggle_layout.addWidget(self.slave_zoom_disable_button)
        layout.addLayout(slave_zoom_toggle_layout, 1, 0, 1, 3)

        layout.addWidget(QLabel("Master Camera:"), 2, 0)
        self.slave_zoom_master_input = QLineEdit()
        self.slave_zoom_master_input.setPlaceholderText("0=Daylight, 1=Thermal, 2=SWIR")
        layout.addWidget(self.slave_zoom_master_input, 2, 1)
        self.slave_zoom_master_button = QPushButton("Set")
        layout.addWidget(self.slave_zoom_master_button, 2, 2)

        group.setLayout(layout)
        return group

    def connect_signals(self):
        """Connect all button signals to their respective handlers."""
        # Motor Calibration
        self.pan_set_zero_button.clicked.connect(self.on_pan_set_zero)
        self.pan_reset_zero_button.clicked.connect(self.on_pan_reset_zero)
        self.pan_zero_pos_button.clicked.connect(self.on_pan_zero_pos_set)
        self.tilt_set_zero_button.clicked.connect(self.on_tilt_set_zero)
        self.tilt_reset_zero_button.clicked.connect(self.on_tilt_reset_zero)
        self.tilt_zero_pos_button.clicked.connect(self.on_tilt_zero_pos_set)

        # Motor Limits
        self.pan_left_limit_button.clicked.connect(self.on_pan_left_limit_set)
        self.pan_right_limit_button.clicked.connect(self.on_pan_right_limit_set)
        self.tilt_up_limit_button.clicked.connect(self.on_tilt_up_limit_set)
        self.tilt_down_limit_button.clicked.connect(self.on_tilt_down_limit_set)
        self.query_pan_limits_button.clicked.connect(self.on_query_pan_limits)
        self.query_tilt_limits_button.clicked.connect(self.on_query_tilt_limits)

        # Motor Speed
        self.pan_max_speed_button.clicked.connect(self.on_pan_max_speed_set)
        self.pan_position_speed_button.clicked.connect(self.on_pan_position_speed_set)
        self.tilt_max_speed_button.clicked.connect(self.on_tilt_max_speed_set)
        self.tilt_position_speed_button.clicked.connect(self.on_tilt_position_speed_set)

        # Motor Behavior
        self.pan_invert_on_button.clicked.connect(lambda: self.on_pan_invert_changed(True))
        self.pan_invert_off_button.clicked.connect(lambda: self.on_pan_invert_changed(False))
        self.tilt_invert_on_button.clicked.connect(lambda: self.on_tilt_invert_changed(True))
        self.tilt_invert_off_button.clicked.connect(lambda: self.on_tilt_invert_changed(False))
        self.zoom_dependent_enable_button.clicked.connect(lambda: self.on_zoom_dependent_changed(True))
        self.zoom_dependent_disable_button.clicked.connect(lambda: self.on_zoom_dependent_changed(False))
        self.block_pt_on_button.clicked.connect(lambda: self.on_block_pt_changed(True))
        self.block_pt_off_button.clicked.connect(lambda: self.on_block_pt_changed(False))

        # Acceleration/Deceleration
        self.acc_vel_max_button.clicked.connect(self.on_acc_vel_max_set)
        self.acc_dec_max_button.clicked.connect(self.on_acc_dec_max_set)
        self.acc_dec_rate_button.clicked.connect(self.on_acc_dec_rate_set)
        self.acc_dec_vstop_button.clicked.connect(self.on_acc_dec_vstop_set)

        # Homing
        self.homing_delay_enable_button.clicked.connect(lambda: self.on_homing_delay_mode_changed(True))
        self.homing_delay_disable_button.clicked.connect(lambda: self.on_homing_delay_mode_changed(False))
        self.homing_delay_time_button.clicked.connect(self.on_homing_delay_time_set)
        self.query_homing_button.clicked.connect(self.on_query_homing)

        # System Controls
        self.reset_controller_button.clicked.connect(self.on_reset_controller)
        self.query_all_motor_button.clicked.connect(self.on_query_all_motor_settings)

        # Slave Zoom
        self.slave_zoom_enable_button.clicked.connect(lambda: self.on_slave_zoom_mode_changed(True))
        self.slave_zoom_disable_button.clicked.connect(lambda: self.on_slave_zoom_mode_changed(False))
        self.slave_zoom_master_button.clicked.connect(self.on_slave_zoom_master_set)

    # Motor Calibration handlers
    def on_pan_set_zero(self):
        """Handle Pan Set Zero button."""
        logger.info("Motor Settings: Pan Set Zero requested")
        self.pan_set_zero_requested.emit()

    def on_pan_reset_zero(self):
        """Handle Pan Reset Zero button."""
        logger.info("Motor Settings: Pan Reset Zero requested")
        self.pan_reset_zero_requested.emit()

    def on_pan_zero_pos_set(self):
        """Handle Pan Zero Position Set button."""
        try:
            value = float(self.pan_zero_pos_input.text())
            if 0.0 <= value <= 360.0:
                logger.info(f"Motor Settings: Pan Zero Position set to {value}°")
                self.pan_zero_pos_changed.emit(value)
            else:
                logger.warning("Motor Settings: Pan Zero Position must be 0.0 - 360.0")
        except ValueError:
            logger.error("Motor Settings: Invalid Pan Zero Position value")

    def on_tilt_set_zero(self):
        """Handle Tilt Set Zero button."""
        logger.info("Motor Settings: Tilt Set Zero requested")
        self.tilt_set_zero_requested.emit()

    def on_tilt_reset_zero(self):
        """Handle Tilt Reset Zero button."""
        logger.info("Motor Settings: Tilt Reset Zero requested")
        self.tilt_reset_zero_requested.emit()

    def on_tilt_zero_pos_set(self):
        """Handle Tilt Zero Position Set button."""
        try:
            value = float(self.tilt_zero_pos_input.text())
            if -90.0 <= value <= 90.0:
                logger.info(f"Motor Settings: Tilt Zero Position set to {value}°")
                self.tilt_zero_pos_changed.emit(value)
            else:
                logger.warning("Motor Settings: Tilt Zero Position must be -90.0 - 90.0")
        except ValueError:
            logger.error("Motor Settings: Invalid Tilt Zero Position value")

    # Motor Limits handlers
    def on_pan_left_limit_set(self):
        """Handle Pan Left Limit Set button."""
        try:
            value = float(self.pan_left_limit_input.text())
            if 0.0 <= value <= 360.0:
                logger.info(f"Motor Settings: Pan Left Limit set to {value}°")
                self.pan_left_limit_changed.emit(value)
            else:
                logger.warning("Motor Settings: Pan Left Limit must be 0.0 - 360.0")
        except ValueError:
            logger.error("Motor Settings: Invalid Pan Left Limit value")

    def on_pan_right_limit_set(self):
        """Handle Pan Right Limit Set button."""
        try:
            value = float(self.pan_right_limit_input.text())
            if 0.0 <= value <= 360.0:
                logger.info(f"Motor Settings: Pan Right Limit set to {value}°")
                self.pan_right_limit_changed.emit(value)
            else:
                logger.warning("Motor Settings: Pan Right Limit must be 0.0 - 360.0")
        except ValueError:
            logger.error("Motor Settings: Invalid Pan Right Limit value")

    def on_tilt_up_limit_set(self):
        """Handle Tilt Up Limit Set button."""
        try:
            value = float(self.tilt_up_limit_input.text())
            if -90.0 <= value <= 90.0:
                logger.info(f"Motor Settings: Tilt Up Limit set to {value}°")
                self.tilt_up_limit_changed.emit(value)
            else:
                logger.warning("Motor Settings: Tilt Up Limit must be -90.0 - 90.0")
        except ValueError:
            logger.error("Motor Settings: Invalid Tilt Up Limit value")

    def on_tilt_down_limit_set(self):
        """Handle Tilt Down Limit Set button."""
        try:
            value = float(self.tilt_down_limit_input.text())
            if -90.0 <= value <= 90.0:
                logger.info(f"Motor Settings: Tilt Down Limit set to {value}°")
                self.tilt_down_limit_changed.emit(value)
            else:
                logger.warning("Motor Settings: Tilt Down Limit must be -90.0 - 90.0")
        except ValueError:
            logger.error("Motor Settings: Invalid Tilt Down Limit value")

    def on_query_pan_limits(self):
        """Handle Query Pan Limits button."""
        logger.info("Motor Settings: Query Pan Limits requested")
        self.query_pan_limits_requested.emit()

    def on_query_tilt_limits(self):
        """Handle Query Tilt Limits button."""
        logger.info("Motor Settings: Query Tilt Limits requested")
        self.query_tilt_limits_requested.emit()

    # Motor Speed handlers
    def on_pan_max_speed_set(self):
        """Handle Pan Max Speed Set button."""
        try:
            value = float(self.pan_max_speed_input.text())
            if value > 0:
                logger.info(f"Motor Settings: Pan Max Speed set to {value}°/s")
                self.pan_max_speed_changed.emit(value)
            else:
                logger.warning("Motor Settings: Pan Max Speed must be positive")
        except ValueError:
            logger.error("Motor Settings: Invalid Pan Max Speed value")

    def on_pan_position_speed_set(self):
        """Handle Pan Position Speed Set button."""
        try:
            value = float(self.pan_position_speed_input.text())
            if value > 0:
                logger.info(f"Motor Settings: Pan Position Speed set to {value}°/s")
                self.pan_position_speed_changed.emit(value)
            else:
                logger.warning("Motor Settings: Pan Position Speed must be positive")
        except ValueError:
            logger.error("Motor Settings: Invalid Pan Position Speed value")

    def on_tilt_max_speed_set(self):
        """Handle Tilt Max Speed Set button."""
        try:
            value = float(self.tilt_max_speed_input.text())
            if value > 0:
                logger.info(f"Motor Settings: Tilt Max Speed set to {value}°/s")
                self.tilt_max_speed_changed.emit(value)
            else:
                logger.warning("Motor Settings: Tilt Max Speed must be positive")
        except ValueError:
            logger.error("Motor Settings: Invalid Tilt Max Speed value")

    def on_tilt_position_speed_set(self):
        """Handle Tilt Position Speed Set button."""
        try:
            value = float(self.tilt_position_speed_input.text())
            if value > 0:
                logger.info(f"Motor Settings: Tilt Position Speed set to {value}°/s")
                self.tilt_position_speed_changed.emit(value)
            else:
                logger.warning("Motor Settings: Tilt Position Speed must be positive")
        except ValueError:
            logger.error("Motor Settings: Invalid Tilt Position Speed value")

    # Motor Behavior handlers
    def on_pan_invert_changed(self, inverted: bool):
        """Handle Pan Invert Movement change."""
        logger.info(f"Motor Settings: Pan Invert Movement {'ON' if inverted else 'OFF'}")
        self.pan_invert_movement_changed.emit(inverted)

    def on_tilt_invert_changed(self, inverted: bool):
        """Handle Tilt Invert Movement change."""
        logger.info(f"Motor Settings: Tilt Invert Movement {'ON' if inverted else 'OFF'}")
        self.tilt_invert_movement_changed.emit(inverted)

    def on_zoom_dependent_changed(self, enabled: bool):
        """Handle Zoom Dependent Mode change."""
        logger.info(f"Motor Settings: Zoom Dependent Mode {'ENABLED' if enabled else 'DISABLED'}")
        self.zoom_dependent_mode_changed.emit(enabled)

    def on_block_pt_changed(self, blocked: bool):
        """Handle Block PT change."""
        logger.info(f"Motor Settings: Block PT {'ON' if blocked else 'OFF'}")
        self.block_pt_changed.emit(blocked)

    # Acceleration/Deceleration handlers
    def on_acc_vel_max_set(self):
        """Handle Acc Vel Max Set button."""
        try:
            value = float(self.acc_vel_max_input.text())
            logger.info(f"Motor Settings: Acc Vel Max set to {value}")
            self.acc_vel_max_changed.emit(value)
        except ValueError:
            logger.error("Motor Settings: Invalid Acc Vel Max value")

    def on_acc_dec_max_set(self):
        """Handle Acc Dec Max Set button."""
        try:
            value = float(self.acc_dec_max_input.text())
            logger.info(f"Motor Settings: Acc Dec Max set to {value}")
            self.acc_dec_max_changed.emit(value)
        except ValueError:
            logger.error("Motor Settings: Invalid Acc Dec Max value")

    def on_acc_dec_rate_set(self):
        """Handle Acc Dec Rate Set button."""
        try:
            value = float(self.acc_dec_rate_input.text())
            logger.info(f"Motor Settings: Acc Dec Rate set to {value}")
            self.acc_dec_rate_changed.emit(value)
        except ValueError:
            logger.error("Motor Settings: Invalid Acc Dec Rate value")

    def on_acc_dec_vstop_set(self):
        """Handle Acc Dec Vstop Set button."""
        try:
            value = float(self.acc_dec_vstop_input.text())
            logger.info(f"Motor Settings: Acc Dec Vstop set to {value}")
            self.acc_dec_vstop_changed.emit(value)
        except ValueError:
            logger.error("Motor Settings: Invalid Acc Dec Vstop value")

    # Homing handlers
    def on_homing_delay_mode_changed(self, enabled: bool):
        """Handle Homing Delay Mode change."""
        logger.info(f"Motor Settings: Homing Delay Mode {'ENABLED' if enabled else 'DISABLED'}")
        self.homing_delay_mode_changed.emit(enabled)

    def on_homing_delay_time_set(self):
        """Handle Homing Delay Time Set button."""
        try:
            value = int(self.homing_delay_time_input.text())
            if value >= 0:
                logger.info(f"Motor Settings: Homing Delay Time set to {value} seconds")
                self.homing_delay_time_changed.emit(value)
            else:
                logger.warning("Motor Settings: Homing Delay Time must be non-negative")
        except ValueError:
            logger.error("Motor Settings: Invalid Homing Delay Time value")

    def on_query_homing(self):
        """Handle Query Homing button."""
        logger.info("Motor Settings: Query Homing requested")
        self.query_homing_requested.emit()

    # System Control handlers
    def on_reset_controller(self):
        """Handle Reset Controller button."""
        logger.info("Motor Settings: Reset Controller requested")
        self.reset_controller_requested.emit()

    def on_query_all_motor_settings(self):
        """Handle Query All Motor Settings button."""
        logger.info("Motor Settings: Query All Motor Settings requested")
        self.query_all_motor_settings_requested.emit()

    # Slave Zoom handlers
    def on_slave_zoom_mode_changed(self, enabled: bool):
        """Handle Slave Zoom Mode change."""
        logger.info(f"Motor Settings: Slave Zoom Mode {'ENABLED' if enabled else 'DISABLED'}")
        self.slave_zoom_mode_changed.emit(enabled)

    def on_slave_zoom_master_set(self):
        """Handle Slave Zoom Master Set button."""
        try:
            value = int(self.slave_zoom_master_input.text())
            if 0 <= value <= 2:
                camera_names = ["Daylight", "Thermal", "SWIR"]
                logger.info(f"Motor Settings: Slave Zoom Master set to {value} ({camera_names[value]})")
                self.slave_zoom_master_changed.emit(value)
            else:
                logger.warning("Motor Settings: Slave Zoom Master must be 0, 1, or 2")
        except ValueError:
            logger.error("Motor Settings: Invalid Slave Zoom Master value")

    # Video section methods (matching CombinedControlTab interface)



