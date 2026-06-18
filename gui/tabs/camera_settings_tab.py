"""
gui/tabs/camera_settings_tab.py
Camera Settings Tab - All camera image quality and processing features.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QGridLayout, QPushButton, QLineEdit,
                             QSlider, QComboBox, QScrollArea, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
from utils.logger import setup_logger
from utils.constants import load_config

logger = setup_logger()


class CameraSettingsTab(QWidget):
    """
    Camera Settings Tab - Consolidates all camera image quality and processing features.
    Includes exposure, iris, focus, white balance, image enhancement, and advanced processing.
    """

    # Group 2: Exposure Control signals
    exposure_mode_changed = pyqtSignal(int, str)  # camera, mode
    shutter_speed_changed = pyqtSignal(int, int)  # camera, speed
    gain_changed = pyqtSignal(int, int)  # camera, gain
    exposure_auto_mode_changed = pyqtSignal(int, bool)  # camera, enable

    # Group 3: Iris Control signals
    iris_mode_changed = pyqtSignal(int, bool)  # camera, auto
    iris_value_changed = pyqtSignal(int, int)  # camera, value
    iris_open_pressed = pyqtSignal(int)  # camera
    iris_close_pressed = pyqtSignal(int)  # camera
    iris_stop_pressed = pyqtSignal(int)  # camera
    iris_to_pos_changed = pyqtSignal(int, int)  # camera, position

    # Group 4: Focus Control signals
    focus_to_pos_changed = pyqtSignal(int, int)  # camera, position
    one_push_af_pressed = pyqtSignal(int)  # camera
    autofocus_mode_changed = pyqtSignal(int, bool)  # camera, enable
    focus_speed_multiplier_changed = pyqtSignal(int, float)  # camera, multiplier

    # Group 5: Lens Control signals
    zoom_to_pos_changed = pyqtSignal(int, int)  # camera, position
    zoom_speed_multiplier_changed = pyqtSignal(int, float)  # camera, multiplier
    tele_end_pos_changed = pyqtSignal(int, int)  # camera, position
    wide_end_pos_changed = pyqtSignal(int, int)  # camera, position
    far_end_pos_changed = pyqtSignal(int, int)  # camera, position
    near_end_pos_changed = pyqtSignal(int, int)  # camera, position

    # Group 6: White Balance signals
    white_balance_mode_changed = pyqtSignal(int, str)  # camera, mode
    wb_red_gain_changed = pyqtSignal(int, int)  # camera, gain
    wb_blue_gain_changed = pyqtSignal(int, int)  # camera, gain
    color_mode_changed = pyqtSignal(int, str)  # camera, mode

    # Group 7: Image Enhancement signals
    brightness_changed = pyqtSignal(int, int)  # camera, value
    contrast_changed = pyqtSignal(int, int)  # camera, value
    saturation_changed = pyqtSignal(int, int)  # camera, value
    sharpness_changed = pyqtSignal(int, int)  # camera, value

    # Group 8: Advanced Image Processing signals
    backlight_compensation_changed = pyqtSignal(int, bool, int)  # camera, enable, level
    wide_dynamic_range_changed = pyqtSignal(int, bool, int)  # camera, enable, level
    noise_reduction_changed = pyqtSignal(int, bool, int)  # camera, enable, level
    defog_mode_changed = pyqtSignal(int, bool)  # camera, enable

    # Group 9: Digital Zoom signals
    digital_zoom_enabled_changed = pyqtSignal(int, bool)  # camera, enable
    digital_zoom_level_changed = pyqtSignal(int, float)  # camera, level

    # Group 10: CLAHE signals
    clahe_enabled_changed = pyqtSignal(int, bool)  # camera, enable
    clahe_clip_limit_changed = pyqtSignal(int, float)  # camera, limit
    clahe_tiles_grid_size_changed = pyqtSignal(int, int)  # camera, size

    # Group 11: Color Filter signals
    color_filter_enabled_changed = pyqtSignal(int, bool)  # camera, enable
    color_palette_changed = pyqtSignal(int, int)  # camera, palette
    color_filter_auto_mode_changed = pyqtSignal(int, bool)  # camera, enable
    color_filter_hue_changed = pyqtSignal(int, int)  # camera, hue
    color_filter_saturation_changed = pyqtSignal(int, int)  # camera, saturation
    color_filter_gamma_changed = pyqtSignal(int, float)  # camera, gamma

    # Group 12: Image Flip signals
    image_flip_mode_changed = pyqtSignal(int, str)  # camera, mode
    horizontal_flip_changed = pyqtSignal(int, bool)  # camera, enable
    vertical_flip_changed = pyqtSignal(int, bool)  # camera, enable

    # Group 13: Video Stabilizer signals
    video_stabilizer_enabled_changed = pyqtSignal(int, bool)  # camera, enable
    stabilizer_x_offset_limit_changed = pyqtSignal(int, int)  # camera, pixels
    stabilizer_y_offset_limit_changed = pyqtSignal(int, int)  # camera, pixels
    stabilizer_a_offset_limit_changed = pyqtSignal(int, float)  # camera, degrees
    stabilizer_mode_changed = pyqtSignal(int, str)  # camera, mode
    stabilizer_type_changed = pyqtSignal(int, str)  # camera, type
    stabilizer_transparent_border_changed = pyqtSignal(int, bool)  # camera, enable
    stabilizer_const_x_offset_changed = pyqtSignal(int, int)  # camera, offset
    stabilizer_const_y_offset_changed = pyqtSignal(int, int)  # camera, offset
    stabilizer_const_a_offset_changed = pyqtSignal(int, float)  # camera, offset

    # Group 14: Camera Profiles signals
    camera_profile_changed = pyqtSignal(int, int)  # camera, profile
    query_camera_settings_requested = pyqtSignal(int)  # camera

    # Group 15: Slave Zoom Coordination signals
    slave_zoom_enabled = pyqtSignal(bool)  # enable
    slave_zoom_master_changed = pyqtSignal(int)  # camera 0-2
    slave_zoom_query_requested = pyqtSignal()

    def __init__(self, video_manager=None):
        super().__init__()
        self.config = load_config()
        self.video_manager = video_manager
        self.video_placeholder = None  # Will hold the shared video display
        self.init_ui()

    def init_ui(self):
        """Initialize the Camera Settings tab UI - LEFT side settings, RIGHT side video."""
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Scrollable settings (fixed width 480px)
        left_widget = self.create_settings_section()

        # Right side: Video streams (expands to fill space)
        right_widget = self.create_video_section()

        # Use horizontal layout - settings panel has fixed width, video expands
        main_layout.addWidget(left_widget, 0)   # Settings panel fixed width (no stretch)
        main_layout.addWidget(right_widget, 1)  # Video expands (stretch factor 1)

        self.setLayout(main_layout)

        # Connect all button signals
        self.connect_all_signals()

        logger.info("Camera Settings tab initialized")

    def create_settings_section(self) -> QWidget:
        """Create left side scrollable settings section."""
        widget = QWidget()
        widget.setFixedWidth(480)  # Fixed width matching Control tab
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(0)
        settings_layout.setContentsMargins(0, 0, 0, 0)

        # Create scroll area for all content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container widget for scrollable content
        container = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Group 1: Target Camera Selector
        layout.addWidget(self.create_camera_selector_group())

        # Group 2: Exposure Control
        layout.addWidget(self.create_exposure_control_group())

        # Group 3: Iris Control
        layout.addWidget(self.create_iris_control_group())

        # Group 4: Focus Control
        layout.addWidget(self.create_focus_control_group())

        # Group 5: Lens Control
        layout.addWidget(self.create_lens_control_group())

        # Group 6: White Balance
        layout.addWidget(self.create_white_balance_group())

        # Group 7: Image Enhancement
        layout.addWidget(self.create_image_enhancement_group())

        # Group 8: Advanced Image Processing
        layout.addWidget(self.create_advanced_processing_group())

        # Group 9: Digital Zoom
        layout.addWidget(self.create_digital_zoom_group())

        # Group 10: CLAHE
        layout.addWidget(self.create_clahe_group())

        # Group 11: Color Filter
        layout.addWidget(self.create_color_filter_group())

        # Group 12: Image Flip
        layout.addWidget(self.create_image_flip_group())

        # Group 13: Video Stabilizer
        layout.addWidget(self.create_video_stabilizer_group())

        # Group 14: Camera Profiles
        layout.addWidget(self.create_camera_profiles_group())

        # Group 15: Slave Zoom Coordination
        layout.addWidget(self.create_slave_zoom_group())

        layout.addStretch()
        container.setLayout(layout)
        scroll_area.setWidget(container)

        settings_layout.addWidget(scroll_area)
        widget.setLayout(settings_layout)
        return widget

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

    def create_camera_selector_group(self) -> QGroupBox:
        """Group 1: Target Camera Selector."""
        group = QGroupBox("Target Camera")
        layout = QVBoxLayout()

        label = QLabel("Select camera for settings control:")
        label.setStyleSheet("font-size: 9pt; padding-bottom: 5px;")
        layout.addWidget(label)

        # Create button group for exclusive selection
        self.camera_button_group = QButtonGroup()
        self.camera_button_group.setExclusive(True)

        # Create horizontal layout for camera buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)

        # Camera 1 - Daylight button
        self.camera1_button = QPushButton("Daylight")
        self.camera1_button.setCheckable(True)
        self.camera1_button.setChecked(True)  # Default selected
        self.camera1_button.setProperty("camera", 1)
        self.camera1_button.setStyleSheet(self.get_camera_button_style())
        self.camera_button_group.addButton(self.camera1_button, 1)
        buttons_layout.addWidget(self.camera1_button)

        # Camera 2 - Thermal button
        self.camera2_button = QPushButton("Thermal")
        self.camera2_button.setCheckable(True)
        self.camera2_button.setProperty("camera", 2)
        self.camera2_button.setStyleSheet(self.get_camera_button_style())
        self.camera_button_group.addButton(self.camera2_button, 2)
        buttons_layout.addWidget(self.camera2_button)

        # Camera 3 - SWIR button
        self.camera3_button = QPushButton("SWIR")
        self.camera3_button.setCheckable(True)
        self.camera3_button.setProperty("camera", 3)
        self.camera3_button.setStyleSheet(self.get_camera_button_style())
        self.camera_button_group.addButton(self.camera3_button, 3)
        buttons_layout.addWidget(self.camera3_button)

        layout.addLayout(buttons_layout)
        group.setLayout(layout)
        return group

    def create_exposure_control_group(self) -> QGroupBox:
        """Group 2: Exposure Control."""
        group = QGroupBox("Exposure Control")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Exposure Mode
        layout.addWidget(QLabel("Exposure Mode:"), 0, 0)
        self.exposure_mode_combo = QComboBox()
        self.exposure_mode_combo.addItems(["Auto", "Manual", "Aperture Priority", "Shutter Priority"])
        layout.addWidget(self.exposure_mode_combo, 0, 1, 1, 2)

        # Shutter Speed
        layout.addWidget(QLabel("Shutter Speed:"), 1, 0)
        self.shutter_speed_input = QLineEdit()
        self.shutter_speed_input.setPlaceholderText("μs")
        layout.addWidget(self.shutter_speed_input, 1, 1)
        self.shutter_speed_button = QPushButton("Set")
        layout.addWidget(self.shutter_speed_button, 1, 2)

        # Gain
        layout.addWidget(QLabel("Gain:"), 2, 0)
        self.gain_input = QLineEdit()
        self.gain_input.setPlaceholderText("0-100")
        layout.addWidget(self.gain_input, 2, 1)
        self.gain_button = QPushButton("Set")
        layout.addWidget(self.gain_button, 2, 2)

        # Auto Mode
        auto_layout = QHBoxLayout()
        self.exposure_auto_on_button = QPushButton("Auto On")
        self.exposure_auto_off_button = QPushButton("Auto Off")
        auto_layout.addWidget(self.exposure_auto_on_button)
        auto_layout.addWidget(self.exposure_auto_off_button)
        layout.addLayout(auto_layout, 3, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_iris_control_group(self) -> QGroupBox:
        """Group 3: Iris Control."""
        group = QGroupBox("Iris Control")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Iris Mode
        mode_layout = QHBoxLayout()
        self.iris_auto_button = QPushButton("Auto Mode")
        self.iris_manual_button = QPushButton("Manual Mode")
        mode_layout.addWidget(self.iris_auto_button)
        mode_layout.addWidget(self.iris_manual_button)
        layout.addLayout(mode_layout, 0, 0, 1, 3)

        # Iris Value
        layout.addWidget(QLabel("Iris Value:"), 1, 0)
        self.iris_value_input = QLineEdit()
        self.iris_value_input.setPlaceholderText("0-max")
        layout.addWidget(self.iris_value_input, 1, 1)
        self.iris_value_button = QPushButton("Set")
        layout.addWidget(self.iris_value_button, 1, 2)

        # Iris Open/Close/Stop buttons
        iris_control_layout = QHBoxLayout()
        self.iris_open_button = QPushButton("Open")
        self.iris_close_button = QPushButton("Close")
        self.iris_stop_button = QPushButton("Stop")
        iris_control_layout.addWidget(self.iris_open_button)
        iris_control_layout.addWidget(self.iris_close_button)
        iris_control_layout.addWidget(self.iris_stop_button)
        layout.addLayout(iris_control_layout, 2, 0, 1, 3)

        # Iris ToPos
        layout.addWidget(QLabel("Iris Position:"), 3, 0)
        self.iris_to_pos_input = QLineEdit()
        self.iris_to_pos_input.setPlaceholderText("Position")
        layout.addWidget(self.iris_to_pos_input, 3, 1)
        self.iris_to_pos_button = QPushButton("Go To")
        layout.addWidget(self.iris_to_pos_button, 3, 2)

        group.setLayout(layout)
        return group

    def create_focus_control_group(self) -> QGroupBox:
        """Group 4: Focus Control."""
        group = QGroupBox("Focus Control")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Focus ToPos
        layout.addWidget(QLabel("Focus Position:"), 0, 0)
        self.focus_to_pos_input = QLineEdit()
        self.focus_to_pos_input.setPlaceholderText("0-max")
        layout.addWidget(self.focus_to_pos_input, 0, 1)
        self.focus_to_pos_button = QPushButton("Go To")
        layout.addWidget(self.focus_to_pos_button, 0, 2)

        # OnePush AF
        self.one_push_af_button = QPushButton("One-Push Autofocus")
        layout.addWidget(self.one_push_af_button, 1, 0, 1, 3)

        # Autofocus Mode
        af_mode_layout = QHBoxLayout()
        self.autofocus_on_button = QPushButton("Continuous AF On")
        self.autofocus_off_button = QPushButton("Continuous AF Off")
        af_mode_layout.addWidget(self.autofocus_on_button)
        af_mode_layout.addWidget(self.autofocus_off_button)
        layout.addLayout(af_mode_layout, 2, 0, 1, 3)

        # Focus Speed Multiplier
        layout.addWidget(QLabel("Speed Multiplier:"), 3, 0)
        self.focus_speed_multiplier_input = QLineEdit()
        self.focus_speed_multiplier_input.setPlaceholderText("0.1-2.0")
        layout.addWidget(self.focus_speed_multiplier_input, 3, 1)
        self.focus_speed_multiplier_button = QPushButton("Set")
        layout.addWidget(self.focus_speed_multiplier_button, 3, 2)

        group.setLayout(layout)
        return group

    def create_lens_control_group(self) -> QGroupBox:
        """Group 5: Lens Control."""
        group = QGroupBox("Lens Control")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Zoom ToPos
        layout.addWidget(QLabel("Zoom Position:"), 0, 0)
        self.zoom_to_pos_input = QLineEdit()
        self.zoom_to_pos_input.setPlaceholderText("0-max")
        layout.addWidget(self.zoom_to_pos_input, 0, 1)
        self.zoom_to_pos_button = QPushButton("Go To")
        layout.addWidget(self.zoom_to_pos_button, 0, 2)

        # Zoom Speed Multiplier
        layout.addWidget(QLabel("Zoom Speed:"), 1, 0)
        self.zoom_speed_multiplier_input = QLineEdit()
        self.zoom_speed_multiplier_input.setPlaceholderText("0.1-2.0")
        layout.addWidget(self.zoom_speed_multiplier_input, 1, 1)
        self.zoom_speed_multiplier_button = QPushButton("Set")
        layout.addWidget(self.zoom_speed_multiplier_button, 1, 2)

        # Lens Endpoints section label
        layout.addWidget(QLabel("<b>Lens Endpoints:</b>"), 2, 0, 1, 3)

        # TeleEndPos
        layout.addWidget(QLabel("Tele End:"), 3, 0)
        self.tele_end_pos_input = QLineEdit()
        self.tele_end_pos_input.setPlaceholderText("Max zoom")
        layout.addWidget(self.tele_end_pos_input, 3, 1)
        self.tele_end_pos_button = QPushButton("Set")
        layout.addWidget(self.tele_end_pos_button, 3, 2)

        # WideEndPos
        layout.addWidget(QLabel("Wide End:"), 4, 0)
        self.wide_end_pos_input = QLineEdit()
        self.wide_end_pos_input.setPlaceholderText("Min zoom")
        layout.addWidget(self.wide_end_pos_input, 4, 1)
        self.wide_end_pos_button = QPushButton("Set")
        layout.addWidget(self.wide_end_pos_button, 4, 2)

        # FarEndPos
        layout.addWidget(QLabel("Far End:"), 5, 0)
        self.far_end_pos_input = QLineEdit()
        self.far_end_pos_input.setPlaceholderText("Far focus")
        layout.addWidget(self.far_end_pos_input, 5, 1)
        self.far_end_pos_button = QPushButton("Set")
        layout.addWidget(self.far_end_pos_button, 5, 2)

        # NearEndPos
        layout.addWidget(QLabel("Near End:"), 6, 0)
        self.near_end_pos_input = QLineEdit()
        self.near_end_pos_input.setPlaceholderText("Near focus")
        layout.addWidget(self.near_end_pos_input, 6, 1)
        self.near_end_pos_button = QPushButton("Set")
        layout.addWidget(self.near_end_pos_button, 6, 2)

        group.setLayout(layout)
        return group

    def create_white_balance_group(self) -> QGroupBox:
        """Group 6: White Balance."""
        group = QGroupBox("White Balance")
        layout = QGridLayout()
        layout.setSpacing(8)

        # WB Mode
        layout.addWidget(QLabel("WB Mode:"), 0, 0)
        self.wb_mode_combo = QComboBox()
        self.wb_mode_combo.addItems(["Auto", "Manual", "Indoor", "Outdoor", "One-Push", "ATW"])
        layout.addWidget(self.wb_mode_combo, 0, 1, 1, 2)

        # WB Red Gain
        layout.addWidget(QLabel("Red Gain:"), 1, 0)
        self.wb_red_gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.wb_red_gain_slider.setMinimum(0)
        self.wb_red_gain_slider.setMaximum(255)
        self.wb_red_gain_slider.setValue(128)
        layout.addWidget(self.wb_red_gain_slider, 1, 1)
        self.wb_red_gain_label = QLabel("128")
        self.wb_red_gain_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        layout.addWidget(self.wb_red_gain_label, 1, 2)

        # WB Blue Gain
        layout.addWidget(QLabel("Blue Gain:"), 2, 0)
        self.wb_blue_gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.wb_blue_gain_slider.setMinimum(0)
        self.wb_blue_gain_slider.setMaximum(255)
        self.wb_blue_gain_slider.setValue(128)
        layout.addWidget(self.wb_blue_gain_slider, 2, 1)
        self.wb_blue_gain_label = QLabel("128")
        self.wb_blue_gain_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        layout.addWidget(self.wb_blue_gain_label, 2, 2)

        # Color Mode
        layout.addWidget(QLabel("Color Mode:"), 3, 0)
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(["Color", "Black & White", "Sepia"])
        layout.addWidget(self.color_mode_combo, 3, 1, 1, 2)

        group.setLayout(layout)
        return group

    def create_image_enhancement_group(self) -> QGroupBox:
        """Group 7: Image Enhancement."""
        group = QGroupBox("Image Enhancement")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Brightness
        layout.addWidget(QLabel("Brightness:"), 0, 0)
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setMinimum(0)
        self.brightness_slider.setMaximum(100)
        self.brightness_slider.setValue(50)
        layout.addWidget(self.brightness_slider, 0, 1)
        self.brightness_label = QLabel("50")
        self.brightness_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        layout.addWidget(self.brightness_label, 0, 2)

        # Contrast
        layout.addWidget(QLabel("Contrast:"), 1, 0)
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setMinimum(0)
        self.contrast_slider.setMaximum(100)
        self.contrast_slider.setValue(50)
        layout.addWidget(self.contrast_slider, 1, 1)
        self.contrast_label = QLabel("50")
        self.contrast_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        layout.addWidget(self.contrast_label, 1, 2)

        # Saturation
        layout.addWidget(QLabel("Saturation:"), 2, 0)
        self.saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.saturation_slider.setMinimum(0)
        self.saturation_slider.setMaximum(100)
        self.saturation_slider.setValue(50)
        layout.addWidget(self.saturation_slider, 2, 1)
        self.saturation_label = QLabel("50")
        self.saturation_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        layout.addWidget(self.saturation_label, 2, 2)

        # Sharpness
        layout.addWidget(QLabel("Sharpness:"), 3, 0)
        self.sharpness_slider = QSlider(Qt.Orientation.Horizontal)
        self.sharpness_slider.setMinimum(0)
        self.sharpness_slider.setMaximum(100)
        self.sharpness_slider.setValue(50)
        layout.addWidget(self.sharpness_slider, 3, 1)
        self.sharpness_label = QLabel("50")
        self.sharpness_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        layout.addWidget(self.sharpness_label, 3, 2)

        group.setLayout(layout)
        return group

    def create_advanced_processing_group(self) -> QGroupBox:
        """Group 8: Advanced Image Processing."""
        group = QGroupBox("Advanced Image Processing")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Backlight Compensation
        layout.addWidget(QLabel("<b>Backlight Compensation:</b>"), 0, 0, 1, 3)
        blc_toggle_layout = QHBoxLayout()
        self.blc_on_button = QPushButton("Enable")
        self.blc_off_button = QPushButton("Disable")
        blc_toggle_layout.addWidget(self.blc_on_button)
        blc_toggle_layout.addWidget(self.blc_off_button)
        layout.addLayout(blc_toggle_layout, 1, 0, 1, 3)

        layout.addWidget(QLabel("Level:"), 2, 0)
        self.blc_level_slider = QSlider(Qt.Orientation.Horizontal)
        self.blc_level_slider.setMinimum(0)
        self.blc_level_slider.setMaximum(100)
        self.blc_level_slider.setValue(50)
        layout.addWidget(self.blc_level_slider, 2, 1)
        self.blc_level_label = QLabel("50")
        self.blc_level_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        layout.addWidget(self.blc_level_label, 2, 2)

        # Wide Dynamic Range
        layout.addWidget(QLabel("<b>Wide Dynamic Range:</b>"), 3, 0, 1, 3)
        wdr_toggle_layout = QHBoxLayout()
        self.wdr_on_button = QPushButton("Enable")
        self.wdr_off_button = QPushButton("Disable")
        wdr_toggle_layout.addWidget(self.wdr_on_button)
        wdr_toggle_layout.addWidget(self.wdr_off_button)
        layout.addLayout(wdr_toggle_layout, 4, 0, 1, 3)

        layout.addWidget(QLabel("Level:"), 5, 0)
        self.wdr_level_slider = QSlider(Qt.Orientation.Horizontal)
        self.wdr_level_slider.setMinimum(0)
        self.wdr_level_slider.setMaximum(100)
        self.wdr_level_slider.setValue(50)
        layout.addWidget(self.wdr_level_slider, 5, 1)
        self.wdr_level_label = QLabel("50")
        self.wdr_level_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        layout.addWidget(self.wdr_level_label, 5, 2)

        # Noise Reduction
        layout.addWidget(QLabel("<b>Noise Reduction:</b>"), 6, 0, 1, 3)
        nr_toggle_layout = QHBoxLayout()
        self.nr_on_button = QPushButton("Enable")
        self.nr_off_button = QPushButton("Disable")
        nr_toggle_layout.addWidget(self.nr_on_button)
        nr_toggle_layout.addWidget(self.nr_off_button)
        layout.addLayout(nr_toggle_layout, 7, 0, 1, 3)

        layout.addWidget(QLabel("Level:"), 8, 0)
        self.nr_level_slider = QSlider(Qt.Orientation.Horizontal)
        self.nr_level_slider.setMinimum(0)
        self.nr_level_slider.setMaximum(100)
        self.nr_level_slider.setValue(50)
        layout.addWidget(self.nr_level_slider, 8, 1)
        self.nr_level_label = QLabel("50")
        self.nr_level_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        layout.addWidget(self.nr_level_label, 8, 2)

        # Defog Mode
        layout.addWidget(QLabel("<b>Defog Mode:</b>"), 9, 0, 1, 3)
        defog_toggle_layout = QHBoxLayout()
        self.defog_on_button = QPushButton("Enable")
        self.defog_off_button = QPushButton("Disable")
        defog_toggle_layout.addWidget(self.defog_on_button)
        defog_toggle_layout.addWidget(self.defog_off_button)
        layout.addLayout(defog_toggle_layout, 10, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_digital_zoom_group(self) -> QGroupBox:
        """Group 9: Digital Zoom."""
        group = QGroupBox("Digital Zoom")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Enable/Disable
        toggle_layout = QHBoxLayout()
        self.digital_zoom_on_button = QPushButton("Enable")
        self.digital_zoom_off_button = QPushButton("Disable")
        toggle_layout.addWidget(self.digital_zoom_on_button)
        toggle_layout.addWidget(self.digital_zoom_off_button)
        layout.addLayout(toggle_layout, 0, 0, 1, 3)

        # Level
        layout.addWidget(QLabel("Zoom Level:"), 1, 0)
        self.digital_zoom_level_input = QLineEdit()
        self.digital_zoom_level_input.setPlaceholderText("1.0 - 4.0")
        layout.addWidget(self.digital_zoom_level_input, 1, 1)
        self.digital_zoom_level_button = QPushButton("Set")
        layout.addWidget(self.digital_zoom_level_button, 1, 2)

        group.setLayout(layout)
        return group

    def create_clahe_group(self) -> QGroupBox:
        """Group 10: CLAHE."""
        group = QGroupBox("CLAHE Enhancement")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Enable/Disable
        toggle_layout = QHBoxLayout()
        self.clahe_on_button = QPushButton("Enable")
        self.clahe_off_button = QPushButton("Disable")
        toggle_layout.addWidget(self.clahe_on_button)
        toggle_layout.addWidget(self.clahe_off_button)
        layout.addLayout(toggle_layout, 0, 0, 1, 3)

        # Clip Limit
        layout.addWidget(QLabel("Clip Limit:"), 1, 0)
        self.clahe_clip_limit_input = QLineEdit()
        self.clahe_clip_limit_input.setPlaceholderText("1.0 - 10.0")
        layout.addWidget(self.clahe_clip_limit_input, 1, 1)
        self.clahe_clip_limit_button = QPushButton("Set")
        layout.addWidget(self.clahe_clip_limit_button, 1, 2)

        # Tiles Grid Size
        layout.addWidget(QLabel("Tiles Grid Size:"), 2, 0)
        self.clahe_tiles_grid_size_input = QLineEdit()
        self.clahe_tiles_grid_size_input.setPlaceholderText("8-32")
        layout.addWidget(self.clahe_tiles_grid_size_input, 2, 1)
        self.clahe_tiles_grid_size_button = QPushButton("Set")
        layout.addWidget(self.clahe_tiles_grid_size_button, 2, 2)

        group.setLayout(layout)
        return group

    def create_color_filter_group(self) -> QGroupBox:
        """Group 11: Color Filter."""
        group = QGroupBox("Color Filter / Palette")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Enable/Disable
        toggle_layout = QHBoxLayout()
        self.color_filter_on_button = QPushButton("Enable")
        self.color_filter_off_button = QPushButton("Disable")
        toggle_layout.addWidget(self.color_filter_on_button)
        toggle_layout.addWidget(self.color_filter_off_button)
        layout.addLayout(toggle_layout, 0, 0, 1, 3)

        # Palette
        layout.addWidget(QLabel("Palette:"), 1, 0)
        self.color_palette_input = QLineEdit()
        self.color_palette_input.setPlaceholderText("0=Normal, 1=Inverse, etc.")
        layout.addWidget(self.color_palette_input, 1, 1)
        self.color_palette_button = QPushButton("Set")
        layout.addWidget(self.color_palette_button, 1, 2)

        # Auto Mode
        auto_mode_layout = QHBoxLayout()
        self.color_filter_auto_on_button = QPushButton("Auto Mode On")
        self.color_filter_auto_off_button = QPushButton("Auto Mode Off")
        auto_mode_layout.addWidget(self.color_filter_auto_on_button)
        auto_mode_layout.addWidget(self.color_filter_auto_off_button)
        layout.addLayout(auto_mode_layout, 2, 0, 1, 3)

        # Hue
        layout.addWidget(QLabel("Hue:"), 3, 0)
        self.color_filter_hue_slider = QSlider(Qt.Orientation.Horizontal)
        self.color_filter_hue_slider.setMinimum(0)
        self.color_filter_hue_slider.setMaximum(360)
        self.color_filter_hue_slider.setValue(180)
        layout.addWidget(self.color_filter_hue_slider, 3, 1)
        self.color_filter_hue_label = QLabel("180")
        self.color_filter_hue_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        layout.addWidget(self.color_filter_hue_label, 3, 2)

        # Saturation
        layout.addWidget(QLabel("Saturation:"), 4, 0)
        self.color_filter_saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.color_filter_saturation_slider.setMinimum(0)
        self.color_filter_saturation_slider.setMaximum(100)
        self.color_filter_saturation_slider.setValue(50)
        layout.addWidget(self.color_filter_saturation_slider, 4, 1)
        self.color_filter_saturation_label = QLabel("50")
        self.color_filter_saturation_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        layout.addWidget(self.color_filter_saturation_label, 4, 2)

        # Gamma
        layout.addWidget(QLabel("Gamma:"), 5, 0)
        self.color_filter_gamma_input = QLineEdit()
        self.color_filter_gamma_input.setPlaceholderText("0.1 - 5.0")
        layout.addWidget(self.color_filter_gamma_input, 5, 1)
        self.color_filter_gamma_button = QPushButton("Set")
        layout.addWidget(self.color_filter_gamma_button, 5, 2)

        group.setLayout(layout)
        return group

    def create_image_flip_group(self) -> QGroupBox:
        """Group 12: Image Flip."""
        group = QGroupBox("Image Flip")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Flip Mode
        layout.addWidget(QLabel("Flip Mode:"), 0, 0)
        self.image_flip_mode_combo = QComboBox()
        self.image_flip_mode_combo.addItems(["Normal", "Horizontal", "Vertical", "Both"])
        layout.addWidget(self.image_flip_mode_combo, 0, 1, 1, 2)

        # Horizontal Flip toggle
        h_flip_layout = QHBoxLayout()
        self.horizontal_flip_on_button = QPushButton("H-Flip On")
        self.horizontal_flip_off_button = QPushButton("H-Flip Off")
        h_flip_layout.addWidget(self.horizontal_flip_on_button)
        h_flip_layout.addWidget(self.horizontal_flip_off_button)
        layout.addLayout(h_flip_layout, 1, 0, 1, 3)

        # Vertical Flip toggle
        v_flip_layout = QHBoxLayout()
        self.vertical_flip_on_button = QPushButton("V-Flip On")
        self.vertical_flip_off_button = QPushButton("V-Flip Off")
        v_flip_layout.addWidget(self.vertical_flip_on_button)
        v_flip_layout.addWidget(self.vertical_flip_off_button)
        layout.addLayout(v_flip_layout, 2, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_video_stabilizer_group(self) -> QGroupBox:
        """Group 13: Video Stabilizer."""
        group = QGroupBox("Video Stabilizer")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Enable/Disable
        toggle_layout = QHBoxLayout()
        self.stabilizer_on_button = QPushButton("Enable")
        self.stabilizer_off_button = QPushButton("Disable")
        toggle_layout.addWidget(self.stabilizer_on_button)
        toggle_layout.addWidget(self.stabilizer_off_button)
        layout.addLayout(toggle_layout, 0, 0, 1, 3)

        # XOffsetLimit
        layout.addWidget(QLabel("X Offset Limit:"), 1, 0)
        self.stabilizer_x_offset_input = QLineEdit()
        self.stabilizer_x_offset_input.setPlaceholderText("pixels")
        layout.addWidget(self.stabilizer_x_offset_input, 1, 1)
        self.stabilizer_x_offset_button = QPushButton("Set")
        layout.addWidget(self.stabilizer_x_offset_button, 1, 2)

        # YOffsetLimit
        layout.addWidget(QLabel("Y Offset Limit:"), 2, 0)
        self.stabilizer_y_offset_input = QLineEdit()
        self.stabilizer_y_offset_input.setPlaceholderText("pixels")
        layout.addWidget(self.stabilizer_y_offset_input, 2, 1)
        self.stabilizer_y_offset_button = QPushButton("Set")
        layout.addWidget(self.stabilizer_y_offset_button, 2, 2)

        # AOffsetLimit
        layout.addWidget(QLabel("A Offset Limit:"), 3, 0)
        self.stabilizer_a_offset_input = QLineEdit()
        self.stabilizer_a_offset_input.setPlaceholderText("degrees")
        layout.addWidget(self.stabilizer_a_offset_input, 3, 1)
        self.stabilizer_a_offset_button = QPushButton("Set")
        layout.addWidget(self.stabilizer_a_offset_button, 3, 2)

        # Mode
        layout.addWidget(QLabel("Mode:"), 4, 0)
        self.stabilizer_mode_combo = QComboBox()
        self.stabilizer_mode_combo.addItems(["Auto", "Manual", "Hybrid"])
        layout.addWidget(self.stabilizer_mode_combo, 4, 1, 1, 2)

        # Type
        layout.addWidget(QLabel("Type:"), 5, 0)
        self.stabilizer_type_combo = QComboBox()
        self.stabilizer_type_combo.addItems(["Digital", "Mechanical", "Combined"])
        layout.addWidget(self.stabilizer_type_combo, 5, 1, 1, 2)

        # Transparent Border
        border_layout = QHBoxLayout()
        self.stabilizer_border_on_button = QPushButton("Transparent Border On")
        self.stabilizer_border_off_button = QPushButton("Transparent Border Off")
        border_layout.addWidget(self.stabilizer_border_on_button)
        border_layout.addWidget(self.stabilizer_border_off_button)
        layout.addLayout(border_layout, 6, 0, 1, 3)

        # Constant offsets section label
        layout.addWidget(QLabel("<b>Constant Offsets:</b>"), 7, 0, 1, 3)

        # ConstXOffset
        layout.addWidget(QLabel("Const X:"), 8, 0)
        self.stabilizer_const_x_input = QLineEdit()
        self.stabilizer_const_x_input.setPlaceholderText("pixels")
        layout.addWidget(self.stabilizer_const_x_input, 8, 1)
        self.stabilizer_const_x_button = QPushButton("Set")
        layout.addWidget(self.stabilizer_const_x_button, 8, 2)

        # ConstYOffset
        layout.addWidget(QLabel("Const Y:"), 9, 0)
        self.stabilizer_const_y_input = QLineEdit()
        self.stabilizer_const_y_input.setPlaceholderText("pixels")
        layout.addWidget(self.stabilizer_const_y_input, 9, 1)
        self.stabilizer_const_y_button = QPushButton("Set")
        layout.addWidget(self.stabilizer_const_y_button, 9, 2)

        # ConstAOffset
        layout.addWidget(QLabel("Const A:"), 10, 0)
        self.stabilizer_const_a_input = QLineEdit()
        self.stabilizer_const_a_input.setPlaceholderText("degrees")
        layout.addWidget(self.stabilizer_const_a_input, 10, 1)
        self.stabilizer_const_a_button = QPushButton("Set")
        layout.addWidget(self.stabilizer_const_a_button, 10, 2)

        group.setLayout(layout)
        return group

    def create_camera_profiles_group(self) -> QGroupBox:
        """Group 14: Quick Camera Controls."""
        group = QGroupBox("Quick Camera Controls")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Subgroup: Zoom & Focus
        layout.addWidget(QLabel("<b>Zoom & Focus:</b>"), 0, 0, 1, 3)

        # Zoom Position
        layout.addWidget(QLabel("Zoom Position:"), 1, 0)
        self.quick_zoom_position_input = QLineEdit()
        self.quick_zoom_position_input.setPlaceholderText("0-max")
        layout.addWidget(self.quick_zoom_position_input, 1, 1)
        self.quick_zoom_position_button = QPushButton("Set")
        layout.addWidget(self.quick_zoom_position_button, 1, 2)

        # Autofocus
        self.quick_autofocus_button = QPushButton("Autofocus")
        layout.addWidget(self.quick_autofocus_button, 2, 0, 1, 3)

        # Subgroup: Camera Profile
        layout.addWidget(QLabel("<b>Camera Profile:</b>"), 3, 0, 1, 3)

        # Profile Number
        layout.addWidget(QLabel("Profile Number:"), 4, 0)
        self.camera_profile_input = QLineEdit()
        self.camera_profile_input.setPlaceholderText("0-N")
        layout.addWidget(self.camera_profile_input, 4, 1)
        self.camera_profile_button = QPushButton("Set")
        layout.addWidget(self.camera_profile_button, 4, 2)

        # Query Settings
        self.query_camera_settings_button = QPushButton("Query Camera Settings")
        layout.addWidget(self.query_camera_settings_button, 5, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_slave_zoom_group(self) -> QGroupBox:
        """Group 15: Slave Zoom Coordination."""
        group = QGroupBox("Slave Zoom Coordination")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Description
        desc_label = QLabel("Enable slave zoom (all cameras follow one):")
        desc_label.setStyleSheet("font-size: 9pt; padding-bottom: 5px;")
        layout.addWidget(desc_label, 0, 0, 1, 3)

        # Enable/Disable buttons
        toggle_layout = QHBoxLayout()
        self.slave_zoom_enable_button = QPushButton("Enable")
        self.slave_zoom_disable_button = QPushButton("Disable")
        toggle_layout.addWidget(self.slave_zoom_enable_button)
        toggle_layout.addWidget(self.slave_zoom_disable_button)
        layout.addLayout(toggle_layout, 1, 0, 1, 3)

        # Master Camera
        layout.addWidget(QLabel("Master Camera:"), 2, 0)
        self.slave_zoom_master_input = QLineEdit()
        self.slave_zoom_master_input.setPlaceholderText("0=Daylight, 1=Thermal, 2=SWIR")
        layout.addWidget(self.slave_zoom_master_input, 2, 1)
        self.slave_zoom_master_button = QPushButton("Set")
        layout.addWidget(self.slave_zoom_master_button, 2, 2)

        # Query button
        self.slave_zoom_query_button = QPushButton("Query Slave Zoom Status")
        layout.addWidget(self.slave_zoom_query_button, 3, 0, 1, 3)

        group.setLayout(layout)
        return group

    def connect_all_signals(self):
        """Connect all button and widget signals to handler methods."""
        # Group 1: Camera selector
        self.camera_button_group.buttonClicked.connect(self.on_camera_button_clicked)

        # Group 2: Exposure Control
        self.exposure_mode_combo.currentTextChanged.connect(self.on_exposure_mode_changed)
        self.shutter_speed_button.clicked.connect(self.on_shutter_speed_set)
        self.gain_button.clicked.connect(self.on_gain_set)
        self.exposure_auto_on_button.clicked.connect(lambda: self.on_exposure_auto_mode(True))
        self.exposure_auto_off_button.clicked.connect(lambda: self.on_exposure_auto_mode(False))

        # Group 3: Iris Control
        self.iris_auto_button.clicked.connect(lambda: self.on_iris_mode(True))
        self.iris_manual_button.clicked.connect(lambda: self.on_iris_mode(False))
        self.iris_value_button.clicked.connect(self.on_iris_value_set)
        self.iris_open_button.clicked.connect(self.on_iris_open)
        self.iris_close_button.clicked.connect(self.on_iris_close)
        self.iris_stop_button.clicked.connect(self.on_iris_stop)
        self.iris_to_pos_button.clicked.connect(self.on_iris_to_pos_set)

        # Group 4: Focus Control
        self.focus_to_pos_button.clicked.connect(self.on_focus_to_pos_set)
        self.one_push_af_button.clicked.connect(self.on_one_push_af)
        self.autofocus_on_button.clicked.connect(lambda: self.on_autofocus_mode(True))
        self.autofocus_off_button.clicked.connect(lambda: self.on_autofocus_mode(False))
        self.focus_speed_multiplier_button.clicked.connect(self.on_focus_speed_multiplier_set)

        # Group 5: Lens Control
        self.zoom_to_pos_button.clicked.connect(self.on_zoom_to_pos_set)
        self.zoom_speed_multiplier_button.clicked.connect(self.on_zoom_speed_multiplier_set)
        self.tele_end_pos_button.clicked.connect(self.on_tele_end_pos_set)
        self.wide_end_pos_button.clicked.connect(self.on_wide_end_pos_set)
        self.far_end_pos_button.clicked.connect(self.on_far_end_pos_set)
        self.near_end_pos_button.clicked.connect(self.on_near_end_pos_set)

        # Group 6: White Balance
        self.wb_mode_combo.currentTextChanged.connect(self.on_wb_mode_changed)
        self.wb_red_gain_slider.valueChanged.connect(self.on_wb_red_gain_changed)
        self.wb_blue_gain_slider.valueChanged.connect(self.on_wb_blue_gain_changed)
        self.color_mode_combo.currentTextChanged.connect(self.on_color_mode_changed)

        # Group 7: Image Enhancement
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)
        self.contrast_slider.valueChanged.connect(self.on_contrast_changed)
        self.saturation_slider.valueChanged.connect(self.on_saturation_changed)
        self.sharpness_slider.valueChanged.connect(self.on_sharpness_changed)

        # Group 8: Advanced Processing
        self.blc_on_button.clicked.connect(lambda: self.on_backlight_compensation(True))
        self.blc_off_button.clicked.connect(lambda: self.on_backlight_compensation(False))
        self.blc_level_slider.valueChanged.connect(self.on_blc_level_changed)
        self.wdr_on_button.clicked.connect(lambda: self.on_wide_dynamic_range(True))
        self.wdr_off_button.clicked.connect(lambda: self.on_wide_dynamic_range(False))
        self.wdr_level_slider.valueChanged.connect(self.on_wdr_level_changed)
        self.nr_on_button.clicked.connect(lambda: self.on_noise_reduction(True))
        self.nr_off_button.clicked.connect(lambda: self.on_noise_reduction(False))
        self.nr_level_slider.valueChanged.connect(self.on_nr_level_changed)
        self.defog_on_button.clicked.connect(lambda: self.on_defog_mode(True))
        self.defog_off_button.clicked.connect(lambda: self.on_defog_mode(False))

        # Group 9: Digital Zoom
        self.digital_zoom_on_button.clicked.connect(lambda: self.on_digital_zoom_enabled(True))
        self.digital_zoom_off_button.clicked.connect(lambda: self.on_digital_zoom_enabled(False))
        self.digital_zoom_level_button.clicked.connect(self.on_digital_zoom_level_set)

        # Group 10: CLAHE
        self.clahe_on_button.clicked.connect(lambda: self.on_clahe_enabled(True))
        self.clahe_off_button.clicked.connect(lambda: self.on_clahe_enabled(False))
        self.clahe_clip_limit_button.clicked.connect(self.on_clahe_clip_limit_set)
        self.clahe_tiles_grid_size_button.clicked.connect(self.on_clahe_tiles_grid_size_set)

        # Group 11: Color Filter
        self.color_filter_on_button.clicked.connect(lambda: self.on_color_filter_enabled(True))
        self.color_filter_off_button.clicked.connect(lambda: self.on_color_filter_enabled(False))
        self.color_palette_button.clicked.connect(self.on_color_palette_set)
        self.color_filter_auto_on_button.clicked.connect(lambda: self.on_color_filter_auto_mode(True))
        self.color_filter_auto_off_button.clicked.connect(lambda: self.on_color_filter_auto_mode(False))
        self.color_filter_hue_slider.valueChanged.connect(self.on_color_filter_hue_changed)
        self.color_filter_saturation_slider.valueChanged.connect(self.on_color_filter_saturation_changed)
        self.color_filter_gamma_button.clicked.connect(self.on_color_filter_gamma_set)

        # Group 12: Image Flip
        self.image_flip_mode_combo.currentTextChanged.connect(self.on_image_flip_mode_changed)
        self.horizontal_flip_on_button.clicked.connect(lambda: self.on_horizontal_flip(True))
        self.horizontal_flip_off_button.clicked.connect(lambda: self.on_horizontal_flip(False))
        self.vertical_flip_on_button.clicked.connect(lambda: self.on_vertical_flip(True))
        self.vertical_flip_off_button.clicked.connect(lambda: self.on_vertical_flip(False))

        # Group 13: Video Stabilizer
        self.stabilizer_on_button.clicked.connect(lambda: self.on_stabilizer_enabled(True))
        self.stabilizer_off_button.clicked.connect(lambda: self.on_stabilizer_enabled(False))
        self.stabilizer_x_offset_button.clicked.connect(self.on_stabilizer_x_offset_set)
        self.stabilizer_y_offset_button.clicked.connect(self.on_stabilizer_y_offset_set)
        self.stabilizer_a_offset_button.clicked.connect(self.on_stabilizer_a_offset_set)
        self.stabilizer_mode_combo.currentTextChanged.connect(self.on_stabilizer_mode_changed)
        self.stabilizer_type_combo.currentTextChanged.connect(self.on_stabilizer_type_changed)
        self.stabilizer_border_on_button.clicked.connect(lambda: self.on_stabilizer_transparent_border(True))
        self.stabilizer_border_off_button.clicked.connect(lambda: self.on_stabilizer_transparent_border(False))
        self.stabilizer_const_x_button.clicked.connect(self.on_stabilizer_const_x_set)
        self.stabilizer_const_y_button.clicked.connect(self.on_stabilizer_const_y_set)
        self.stabilizer_const_a_button.clicked.connect(self.on_stabilizer_const_a_set)

        # Group 14: Quick Camera Controls
        self.quick_zoom_position_button.clicked.connect(self.on_quick_zoom_position_set)
        self.quick_autofocus_button.clicked.connect(self.on_quick_autofocus)
        self.camera_profile_button.clicked.connect(self.on_camera_profile_set)
        self.query_camera_settings_button.clicked.connect(self.on_query_camera_settings)

        # Group 15: Slave Zoom Coordination
        self.slave_zoom_enable_button.clicked.connect(self._handle_slave_zoom_enable)
        self.slave_zoom_disable_button.clicked.connect(self._handle_slave_zoom_disable)
        self.slave_zoom_master_button.clicked.connect(self._handle_slave_zoom_master_set)
        self.slave_zoom_query_button.clicked.connect(self._handle_slave_zoom_query)

    # Helper methods
    def get_selected_camera(self) -> int:
        """Get the currently selected camera number (1, 2, or 3)."""
        selected_button = self.camera_button_group.checkedButton()
        if selected_button:
            return selected_button.property("camera")
        return 1  # Default to camera 1

    def get_camera_button_style(self) -> str:
        """Return stylesheet for camera selector buttons."""
        return """
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
        """

    # Handler methods for Group 1: Camera Selector
    def on_camera_button_clicked(self, button: QPushButton):
        """Handle camera button selection."""
        camera = button.property("camera")
        camera_name = button.text()
        logger.info(f"Camera Settings target changed to: Camera {camera} ({camera_name})")

    # Handler methods for Group 2: Exposure Control
    def on_exposure_mode_changed(self, mode: str):
        camera = self.get_selected_camera()
        self.exposure_mode_changed.emit(camera, mode)
        logger.info(f"Camera{camera}: Exposure mode = {mode}")

    def on_shutter_speed_set(self):
        try:
            speed = int(self.shutter_speed_input.text())
            camera = self.get_selected_camera()
            self.shutter_speed_changed.emit(camera, speed)
            logger.info(f"Camera{camera}: Shutter speed = {speed} μs")
        except ValueError:
            logger.warning("Invalid shutter speed value")

    def on_gain_set(self):
        try:
            gain = int(self.gain_input.text())
            if gain < 0 or gain > 100:
                logger.warning("Gain must be 0-100")
                return
            camera = self.get_selected_camera()
            self.gain_changed.emit(camera, gain)
            logger.info(f"Camera{camera}: Gain = {gain}")
        except ValueError:
            logger.warning("Invalid gain value")

    def on_exposure_auto_mode(self, enable: bool):
        camera = self.get_selected_camera()
        self.exposure_auto_mode_changed.emit(camera, enable)
        logger.info(f"Camera{camera}: Exposure auto mode = {enable}")

    # Handler methods for Group 3: Iris Control
    def on_iris_mode(self, auto: bool):
        camera = self.get_selected_camera()
        self.iris_mode_changed.emit(camera, auto)
        logger.info(f"Camera{camera}: Iris mode = {'Auto' if auto else 'Manual'}")

    def on_iris_value_set(self):
        try:
            value = int(self.iris_value_input.text())
            camera = self.get_selected_camera()
            self.iris_value_changed.emit(camera, value)
            logger.info(f"Camera{camera}: Iris value = {value}")
        except ValueError:
            logger.warning("Invalid iris value")

    def on_iris_open(self):
        camera = self.get_selected_camera()
        self.iris_open_pressed.emit(camera)
        logger.info(f"Camera{camera}: Iris open")

    def on_iris_close(self):
        camera = self.get_selected_camera()
        self.iris_close_pressed.emit(camera)
        logger.info(f"Camera{camera}: Iris close")

    def on_iris_stop(self):
        camera = self.get_selected_camera()
        self.iris_stop_pressed.emit(camera)
        logger.info(f"Camera{camera}: Iris stop")

    def on_iris_to_pos_set(self):
        try:
            position = int(self.iris_to_pos_input.text())
            camera = self.get_selected_camera()
            self.iris_to_pos_changed.emit(camera, position)
            logger.info(f"Camera{camera}: Iris to position = {position}")
        except ValueError:
            logger.warning("Invalid iris position")

    # Handler methods for Group 4: Focus Control
    def on_focus_to_pos_set(self):
        try:
            position = int(self.focus_to_pos_input.text())
            camera = self.get_selected_camera()
            self.focus_to_pos_changed.emit(camera, position)
            logger.info(f"Camera{camera}: Focus to position = {position}")
        except ValueError:
            logger.warning("Invalid focus position")

    def on_one_push_af(self):
        camera = self.get_selected_camera()
        self.one_push_af_pressed.emit(camera)
        logger.info(f"Camera{camera}: One-push AF triggered")

    def on_autofocus_mode(self, enable: bool):
        camera = self.get_selected_camera()
        self.autofocus_mode_changed.emit(camera, enable)
        logger.info(f"Camera{camera}: Continuous AF = {enable}")

    def on_focus_speed_multiplier_set(self):
        try:
            multiplier = float(self.focus_speed_multiplier_input.text())
            if multiplier < 0.1 or multiplier > 2.0:
                logger.warning("Focus speed multiplier must be 0.1-2.0")
                return
            camera = self.get_selected_camera()
            self.focus_speed_multiplier_changed.emit(camera, multiplier)
            logger.info(f"Camera{camera}: Focus speed multiplier = {multiplier}")
        except ValueError:
            logger.warning("Invalid focus speed multiplier")

    # Handler methods for Group 5: Lens Control
    def on_zoom_to_pos_set(self):
        try:
            position = int(self.zoom_to_pos_input.text())
            camera = self.get_selected_camera()
            self.zoom_to_pos_changed.emit(camera, position)
            logger.info(f"Camera{camera}: Zoom to position = {position}")
        except ValueError:
            logger.warning("Invalid zoom position")

    def on_zoom_speed_multiplier_set(self):
        try:
            multiplier = float(self.zoom_speed_multiplier_input.text())
            if multiplier < 0.1 or multiplier > 2.0:
                logger.warning("Zoom speed multiplier must be 0.1-2.0")
                return
            camera = self.get_selected_camera()
            self.zoom_speed_multiplier_changed.emit(camera, multiplier)
            logger.info(f"Camera{camera}: Zoom speed multiplier = {multiplier}")
        except ValueError:
            logger.warning("Invalid zoom speed multiplier")

    def on_tele_end_pos_set(self):
        try:
            position = int(self.tele_end_pos_input.text())
            camera = self.get_selected_camera()
            self.tele_end_pos_changed.emit(camera, position)
            logger.info(f"Camera{camera}: Tele end position = {position}")
        except ValueError:
            logger.warning("Invalid tele end position")

    def on_wide_end_pos_set(self):
        try:
            position = int(self.wide_end_pos_input.text())
            camera = self.get_selected_camera()
            self.wide_end_pos_changed.emit(camera, position)
            logger.info(f"Camera{camera}: Wide end position = {position}")
        except ValueError:
            logger.warning("Invalid wide end position")

    def on_far_end_pos_set(self):
        try:
            position = int(self.far_end_pos_input.text())
            camera = self.get_selected_camera()
            self.far_end_pos_changed.emit(camera, position)
            logger.info(f"Camera{camera}: Far end position = {position}")
        except ValueError:
            logger.warning("Invalid far end position")

    def on_near_end_pos_set(self):
        try:
            position = int(self.near_end_pos_input.text())
            camera = self.get_selected_camera()
            self.near_end_pos_changed.emit(camera, position)
            logger.info(f"Camera{camera}: Near end position = {position}")
        except ValueError:
            logger.warning("Invalid near end position")

    # Handler methods for Group 6: White Balance
    def on_wb_mode_changed(self, mode: str):
        camera = self.get_selected_camera()
        self.white_balance_mode_changed.emit(camera, mode)
        logger.info(f"Camera{camera}: WB mode = {mode}")

    def on_wb_red_gain_changed(self, value: int):
        self.wb_red_gain_label.setText(str(value))
        camera = self.get_selected_camera()
        self.wb_red_gain_changed.emit(camera, value)
        logger.debug(f"Camera{camera}: WB red gain = {value}")

    def on_wb_blue_gain_changed(self, value: int):
        self.wb_blue_gain_label.setText(str(value))
        camera = self.get_selected_camera()
        self.wb_blue_gain_changed.emit(camera, value)
        logger.debug(f"Camera{camera}: WB blue gain = {value}")

    def on_color_mode_changed(self, mode: str):
        camera = self.get_selected_camera()
        self.color_mode_changed.emit(camera, mode)
        logger.info(f"Camera{camera}: Color mode = {mode}")

    # Handler methods for Group 7: Image Enhancement
    def on_brightness_changed(self, value: int):
        self.brightness_label.setText(str(value))
        camera = self.get_selected_camera()
        self.brightness_changed.emit(camera, value)
        logger.debug(f"Camera{camera}: Brightness = {value}")

    def on_contrast_changed(self, value: int):
        self.contrast_label.setText(str(value))
        camera = self.get_selected_camera()
        self.contrast_changed.emit(camera, value)
        logger.debug(f"Camera{camera}: Contrast = {value}")

    def on_saturation_changed(self, value: int):
        self.saturation_label.setText(str(value))
        camera = self.get_selected_camera()
        self.saturation_changed.emit(camera, value)
        logger.debug(f"Camera{camera}: Saturation = {value}")

    def on_sharpness_changed(self, value: int):
        self.sharpness_label.setText(str(value))
        camera = self.get_selected_camera()
        self.sharpness_changed.emit(camera, value)
        logger.debug(f"Camera{camera}: Sharpness = {value}")

    # Handler methods for Group 8: Advanced Processing
    def on_backlight_compensation(self, enable: bool):
        camera = self.get_selected_camera()
        level = self.blc_level_slider.value()
        self.backlight_compensation_changed.emit(camera, enable, level)
        logger.info(f"Camera{camera}: Backlight compensation = {enable}, level = {level}")

    def on_blc_level_changed(self, value: int):
        self.blc_level_label.setText(str(value))

    def on_wide_dynamic_range(self, enable: bool):
        camera = self.get_selected_camera()
        level = self.wdr_level_slider.value()
        self.wide_dynamic_range_changed.emit(camera, enable, level)
        logger.info(f"Camera{camera}: WDR = {enable}, level = {level}")

    def on_wdr_level_changed(self, value: int):
        self.wdr_level_label.setText(str(value))

    def on_noise_reduction(self, enable: bool):
        camera = self.get_selected_camera()
        level = self.nr_level_slider.value()
        self.noise_reduction_changed.emit(camera, enable, level)
        logger.info(f"Camera{camera}: Noise reduction = {enable}, level = {level}")

    def on_nr_level_changed(self, value: int):
        self.nr_level_label.setText(str(value))

    def on_defog_mode(self, enable: bool):
        camera = self.get_selected_camera()
        self.defog_mode_changed.emit(camera, enable)
        logger.info(f"Camera{camera}: Defog mode = {enable}")

    # Handler methods for Group 9: Digital Zoom
    def on_digital_zoom_enabled(self, enable: bool):
        camera = self.get_selected_camera()
        self.digital_zoom_enabled_changed.emit(camera, enable)
        logger.info(f"Camera{camera}: Digital zoom = {enable}")

    def on_digital_zoom_level_set(self):
        try:
            level = float(self.digital_zoom_level_input.text())
            if level < 1.0 or level > 4.0:
                logger.warning("Digital zoom level must be 1.0-4.0")
                return
            camera = self.get_selected_camera()
            self.digital_zoom_level_changed.emit(camera, level)
            logger.info(f"Camera{camera}: Digital zoom level = {level}")
        except ValueError:
            logger.warning("Invalid digital zoom level")

    # Handler methods for Group 10: CLAHE
    def on_clahe_enabled(self, enable: bool):
        camera = self.get_selected_camera()
        self.clahe_enabled_changed.emit(camera, enable)
        logger.info(f"Camera{camera}: CLAHE = {enable}")

    def on_clahe_clip_limit_set(self):
        try:
            limit = float(self.clahe_clip_limit_input.text())
            if limit < 1.0 or limit > 10.0:
                logger.warning("CLAHE clip limit must be 1.0-10.0")
                return
            camera = self.get_selected_camera()
            self.clahe_clip_limit_changed.emit(camera, limit)
            logger.info(f"Camera{camera}: CLAHE clip limit = {limit}")
        except ValueError:
            logger.warning("Invalid CLAHE clip limit")

    def on_clahe_tiles_grid_size_set(self):
        try:
            size = int(self.clahe_tiles_grid_size_input.text())
            if size < 8 or size > 32:
                logger.warning("CLAHE tiles grid size must be 8-32")
                return
            camera = self.get_selected_camera()
            self.clahe_tiles_grid_size_changed.emit(camera, size)
            logger.info(f"Camera{camera}: CLAHE tiles grid size = {size}")
        except ValueError:
            logger.warning("Invalid CLAHE tiles grid size")

    # Handler methods for Group 11: Color Filter
    def on_color_filter_enabled(self, enable: bool):
        camera = self.get_selected_camera()
        self.color_filter_enabled_changed.emit(camera, enable)
        logger.info(f"Camera{camera}: Color filter = {enable}")

    def on_color_palette_set(self):
        try:
            palette = int(self.color_palette_input.text())
            camera = self.get_selected_camera()
            self.color_palette_changed.emit(camera, palette)
            logger.info(f"Camera{camera}: Color palette = {palette}")
        except ValueError:
            logger.warning("Invalid color palette")

    def on_color_filter_auto_mode(self, enable: bool):
        camera = self.get_selected_camera()
        self.color_filter_auto_mode_changed.emit(camera, enable)
        logger.info(f"Camera{camera}: Color filter auto mode = {enable}")

    def on_color_filter_hue_changed(self, value: int):
        self.color_filter_hue_label.setText(str(value))
        camera = self.get_selected_camera()
        self.color_filter_hue_changed.emit(camera, value)
        logger.debug(f"Camera{camera}: Color filter hue = {value}")

    def on_color_filter_saturation_changed(self, value: int):
        self.color_filter_saturation_label.setText(str(value))
        camera = self.get_selected_camera()
        self.color_filter_saturation_changed.emit(camera, value)
        logger.debug(f"Camera{camera}: Color filter saturation = {value}")

    def on_color_filter_gamma_set(self):
        try:
            gamma = float(self.color_filter_gamma_input.text())
            if gamma < 0.1 or gamma > 5.0:
                logger.warning("Color filter gamma must be 0.1-5.0")
                return
            camera = self.get_selected_camera()
            self.color_filter_gamma_changed.emit(camera, gamma)
            logger.info(f"Camera{camera}: Color filter gamma = {gamma}")
        except ValueError:
            logger.warning("Invalid color filter gamma")

    # Handler methods for Group 12: Image Flip
    def on_image_flip_mode_changed(self, mode: str):
        camera = self.get_selected_camera()
        self.image_flip_mode_changed.emit(camera, mode)
        logger.info(f"Camera{camera}: Image flip mode = {mode}")

    def on_horizontal_flip(self, enable: bool):
        camera = self.get_selected_camera()
        self.horizontal_flip_changed.emit(camera, enable)
        logger.info(f"Camera{camera}: Horizontal flip = {enable}")

    def on_vertical_flip(self, enable: bool):
        camera = self.get_selected_camera()
        self.vertical_flip_changed.emit(camera, enable)
        logger.info(f"Camera{camera}: Vertical flip = {enable}")

    # Handler methods for Group 13: Video Stabilizer
    def on_stabilizer_enabled(self, enable: bool):
        camera = self.get_selected_camera()
        self.video_stabilizer_enabled_changed.emit(camera, enable)
        logger.info(f"Camera{camera}: Video stabilizer = {enable}")

    def on_stabilizer_x_offset_set(self):
        try:
            offset = int(self.stabilizer_x_offset_input.text())
            camera = self.get_selected_camera()
            self.stabilizer_x_offset_limit_changed.emit(camera, offset)
            logger.info(f"Camera{camera}: Stabilizer X offset limit = {offset} px")
        except ValueError:
            logger.warning("Invalid stabilizer X offset")

    def on_stabilizer_y_offset_set(self):
        try:
            offset = int(self.stabilizer_y_offset_input.text())
            camera = self.get_selected_camera()
            self.stabilizer_y_offset_limit_changed.emit(camera, offset)
            logger.info(f"Camera{camera}: Stabilizer Y offset limit = {offset} px")
        except ValueError:
            logger.warning("Invalid stabilizer Y offset")

    def on_stabilizer_a_offset_set(self):
        try:
            offset = float(self.stabilizer_a_offset_input.text())
            camera = self.get_selected_camera()
            self.stabilizer_a_offset_limit_changed.emit(camera, offset)
            logger.info(f"Camera{camera}: Stabilizer A offset limit = {offset} deg")
        except ValueError:
            logger.warning("Invalid stabilizer A offset")

    def on_stabilizer_mode_changed(self, mode: str):
        camera = self.get_selected_camera()
        self.stabilizer_mode_changed.emit(camera, mode)
        logger.info(f"Camera{camera}: Stabilizer mode = {mode}")

    def on_stabilizer_type_changed(self, type_: str):
        camera = self.get_selected_camera()
        self.stabilizer_type_changed.emit(camera, type_)
        logger.info(f"Camera{camera}: Stabilizer type = {type_}")

    def on_stabilizer_transparent_border(self, enable: bool):
        camera = self.get_selected_camera()
        self.stabilizer_transparent_border_changed.emit(camera, enable)
        logger.info(f"Camera{camera}: Stabilizer transparent border = {enable}")

    def on_stabilizer_const_x_set(self):
        try:
            offset = int(self.stabilizer_const_x_input.text())
            camera = self.get_selected_camera()
            self.stabilizer_const_x_offset_changed.emit(camera, offset)
            logger.info(f"Camera{camera}: Stabilizer const X offset = {offset} px")
        except ValueError:
            logger.warning("Invalid stabilizer const X offset")

    def on_stabilizer_const_y_set(self):
        try:
            offset = int(self.stabilizer_const_y_input.text())
            camera = self.get_selected_camera()
            self.stabilizer_const_y_offset_changed.emit(camera, offset)
            logger.info(f"Camera{camera}: Stabilizer const Y offset = {offset} px")
        except ValueError:
            logger.warning("Invalid stabilizer const Y offset")

    def on_stabilizer_const_a_set(self):
        try:
            offset = float(self.stabilizer_const_a_input.text())
            camera = self.get_selected_camera()
            self.stabilizer_const_a_offset_changed.emit(camera, offset)
            logger.info(f"Camera{camera}: Stabilizer const A offset = {offset} deg")
        except ValueError:
            logger.warning("Invalid stabilizer const A offset")

    # Handler methods for Group 14: Quick Camera Controls
    def on_quick_zoom_position_set(self):
        try:
            position = int(self.quick_zoom_position_input.text())
            camera = self.get_selected_camera()
            self.zoom_to_pos_changed.emit(camera, position)
            logger.info(f"Camera{camera}: Quick zoom to position = {position}")
        except ValueError:
            logger.warning("Invalid quick zoom position")

    def on_quick_autofocus(self):
        camera = self.get_selected_camera()
        self.one_push_af_pressed.emit(camera)
        logger.info(f"Camera{camera}: Quick autofocus triggered")

    def on_camera_profile_set(self):
        try:
            profile = int(self.camera_profile_input.text())
            camera = self.get_selected_camera()
            self.camera_profile_changed.emit(camera, profile)
            logger.info(f"Camera{camera}: Profile = {profile}")
        except ValueError:
            logger.warning("Invalid camera profile")

    def on_query_camera_settings(self):
        camera = self.get_selected_camera()
        self.query_camera_settings_requested.emit(camera)
        logger.info(f"Camera{camera}: Query settings requested")

    # Handler methods for Group 15: Slave Zoom Coordination
    def _handle_slave_zoom_enable(self):
        """Handle slave zoom enable button."""
        self.slave_zoom_enabled.emit(True)
        logger.info("Slave zoom enabled")

    def _handle_slave_zoom_disable(self):
        """Handle slave zoom disable button."""
        self.slave_zoom_enabled.emit(False)
        logger.info("Slave zoom disabled")

    def _handle_slave_zoom_master_set(self):
        """Handle slave zoom master camera set button."""
        try:
            master = int(self.slave_zoom_master_input.text())
            if master < 0 or master > 2:
                logger.warning("Master camera must be 0-2 (0=Daylight, 1=Thermal, 2=SWIR)")
                return
            self.slave_zoom_master_changed.emit(master)
            logger.info(f"Slave zoom master camera set to: {master}")
        except ValueError:
            logger.warning("Invalid master camera value")

    def _handle_slave_zoom_query(self):
        """Handle slave zoom query button."""
        self.slave_zoom_query_requested.emit()
        logger.info("Slave zoom status query requested")




