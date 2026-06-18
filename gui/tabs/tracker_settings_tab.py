"""
gui/tabs/tracker_settings_tab.py
Tracker Settings tab - consolidates all video tracker, motion detector, changes detector,
classification, and license management features.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QGridLayout, QPushButton, QLineEdit,
                             QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QScrollArea)
from PyQt6.QtCore import pyqtSignal, Qt
from utils.constants import load_config
from utils.logger import setup_logger

logger = setup_logger()


class TrackerSettingsTab(QWidget):
    """
    Tracker Settings tab for video tracking, motion detection, and classification features.
    Contains 7 groups: Motion Magnificator, VideoTracker, MotionDetector, ChangesDetector,
    Classification, Detection Results, and License Status.
    Layout: LEFT side with scrollable settings (480px fixed), RIGHT side with video feeds (expanding).
    """

    # ========================================================================
    # Motion Magnificator signals (2)
    # ========================================================================
    motion_magnificator_changed = pyqtSignal(int, bool)  # camera, enable
    magnification_level_changed = pyqtSignal(int, int)  # camera, level

    # ========================================================================
    # VideoTracker signals (7)
    # ========================================================================
    video_tracker_reset_pressed = pyqtSignal(int)  # camera
    video_tracker_changed = pyqtSignal(int, bool)  # camera, enable
    video_tracker_lock_pressed = pyqtSignal(int)  # camera
    video_tracker_unlock_pressed = pyqtSignal(int)  # camera
    tracker_mode_changed = pyqtSignal(int, int)  # camera, mode
    object_size_changed = pyqtSignal(int, int)  # camera, size
    search_area_size_changed = pyqtSignal(int, int)  # camera, size

    # ========================================================================
    # MotionDetector signals (13)
    # ========================================================================
    motion_detector_reset_pressed = pyqtSignal(int)  # camera
    motion_detector_changed = pyqtSignal(int, bool)  # camera, enable
    motion_detector_frame_buffer_changed = pyqtSignal(int, int)  # camera, buffer_size
    motion_detector_min_width_changed = pyqtSignal(int, int)  # camera, width
    motion_detector_max_width_changed = pyqtSignal(int, int)  # camera, width
    motion_detector_min_height_changed = pyqtSignal(int, int)  # camera, height
    motion_detector_max_height_changed = pyqtSignal(int, int)  # camera, height
    motion_detector_x_criteria_changed = pyqtSignal(int, int)  # camera, criteria
    motion_detector_y_criteria_changed = pyqtSignal(int, int)  # camera, criteria
    motion_detector_reset_criteria_changed = pyqtSignal(int, int)  # camera, criteria
    motion_detector_sensitivity_changed = pyqtSignal(int, float)  # camera, sensitivity
    motion_detector_mode_changed = pyqtSignal(int, int)  # camera, mode

    # ========================================================================
    # ChangesDetector signals (13 - identical to MotionDetector)
    # ========================================================================
    changes_detector_reset_pressed = pyqtSignal(int)  # camera
    changes_detector_changed = pyqtSignal(int, bool)  # camera, enable
    changes_detector_frame_buffer_changed = pyqtSignal(int, int)  # camera, buffer_size
    changes_detector_min_width_changed = pyqtSignal(int, int)  # camera, width
    changes_detector_max_width_changed = pyqtSignal(int, int)  # camera, width
    changes_detector_min_height_changed = pyqtSignal(int, int)  # camera, height
    changes_detector_max_height_changed = pyqtSignal(int, int)  # camera, height
    changes_detector_x_criteria_changed = pyqtSignal(int, int)  # camera, criteria
    changes_detector_y_criteria_changed = pyqtSignal(int, int)  # camera, criteria
    changes_detector_reset_criteria_changed = pyqtSignal(int, int)  # camera, criteria
    changes_detector_sensitivity_changed = pyqtSignal(int, float)  # camera, sensitivity
    changes_detector_mode_changed = pyqtSignal(int, int)  # camera, mode

    # ========================================================================
    # Classification signals (4)
    # ========================================================================
    classification_changed = pyqtSignal(int, bool)  # camera, enable
    classification_model_changed = pyqtSignal(int, str)  # camera, model_name
    classification_confidence_changed = pyqtSignal(int, float)  # camera, confidence
    query_classification_pressed = pyqtSignal(int)  # camera

    # ========================================================================
    # Detection Results signals (2)
    # ========================================================================
    subscribe_detection_pressed = pyqtSignal(int)  # camera
    clear_detection_pressed = pyqtSignal(int)  # camera

    # ========================================================================
    # License Status signals (5)
    # ========================================================================
    query_video_tracker_license_pressed = pyqtSignal()
    query_video_stabiliser_license_pressed = pyqtSignal()
    query_motion_detector_license_pressed = pyqtSignal()
    query_changes_detector_license_pressed = pyqtSignal()
    query_classification_license_pressed = pyqtSignal()

    def __init__(self, video_manager=None):
        super().__init__()
        self.config = load_config()
        self.selected_camera = 1  # Default to Camera 1
        self.video_manager = video_manager
        self.video_placeholder = None  # Will hold the shared video display
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """Initialize the UI with left settings panel and right video feeds."""
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Scrollable settings panel (fixed width 480px)
        left_widget = self.create_settings_section()

        # Right side: Video feeds (expands to fill space)
        right_widget = self.create_video_section()

        # Add widgets to layout
        main_layout.addWidget(left_widget, 0)   # Settings panel fixed width (no stretch)
        main_layout.addWidget(right_widget, 1)  # Video expands (stretch factor 1)

        self.setLayout(main_layout)
        logger.info("Tracker Settings tab initialized with split layout")

    def create_settings_section(self) -> QWidget:
        """Create scrollable settings panel (left side, 480px fixed width)."""
        # Outer container with fixed width
        container = QWidget()
        container.setFixedWidth(480)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Scrollable content widget
        scroll_content = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)
        settings_layout.setContentsMargins(10, 10, 10, 10)

        # Camera selector at top
        camera_group = self.create_camera_selector()
        settings_layout.addWidget(camera_group)

        # Add all settings groups
        settings_layout.addWidget(self.create_motion_magnificator_group())
        settings_layout.addWidget(self.create_video_tracker_group())
        settings_layout.addWidget(self.create_motion_detector_group())
        settings_layout.addWidget(self.create_changes_detector_group())
        settings_layout.addWidget(self.create_classification_group())
        settings_layout.addWidget(self.create_detection_results_group())
        settings_layout.addWidget(self.create_license_status_group())

        settings_layout.addStretch()
        scroll_content.setLayout(settings_layout)
        scroll_area.setWidget(scroll_content)

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

    def create_camera_selector(self) -> QGroupBox:
        """Create camera selector group."""
        group = QGroupBox("Camera Selection")
        layout = QVBoxLayout()

        label = QLabel("Select camera for tracker settings:")
        label.setStyleSheet("font-size: 9pt; padding-bottom: 5px;")
        layout.addWidget(label)

        # Camera selector combo box
        self.camera_selector = QComboBox()
        self.camera_selector.addItems(["Camera 1 (Thermal)", "Camera 2 (Daylight)", "Camera 3 (SWIR)"])
        self.camera_selector.setCurrentIndex(0)
        self.camera_selector.currentIndexChanged.connect(self.on_camera_changed)
        layout.addWidget(self.camera_selector)

        group.setLayout(layout)
        return group

    def create_motion_magnificator_group(self) -> QGroupBox:
        """Create Motion Magnificator settings group."""
        group = QGroupBox("Motion Magnificator")
        layout = QGridLayout()

        # Enable checkbox
        self.motion_mag_enable = QCheckBox("Enable Motion Magnificator")
        layout.addWidget(self.motion_mag_enable, 0, 0, 1, 2)

        # Magnification level
        layout.addWidget(QLabel("Magnification Level:"), 1, 0)
        self.mag_level_spin = QSpinBox()
        self.mag_level_spin.setRange(1, 10)
        self.mag_level_spin.setValue(5)
        layout.addWidget(self.mag_level_spin, 1, 1)

        group.setLayout(layout)
        return group

    def create_video_tracker_group(self) -> QGroupBox:
        """Create VideoTracker settings group."""
        group = QGroupBox("Video Tracker")
        layout = QGridLayout()

        # Enable checkbox
        self.video_tracker_enable = QCheckBox("Enable Video Tracker")
        layout.addWidget(self.video_tracker_enable, 0, 0, 1, 2)

        # Tracker mode
        layout.addWidget(QLabel("Tracker Mode:"), 1, 0)
        self.tracker_mode_combo = QComboBox()
        self.tracker_mode_combo.addItems(["Auto", "Manual", "Center Lock"])
        layout.addWidget(self.tracker_mode_combo, 1, 1)

        # Object size
        layout.addWidget(QLabel("Object Size:"), 2, 0)
        self.object_size_spin = QSpinBox()
        self.object_size_spin.setRange(10, 500)
        self.object_size_spin.setValue(50)
        layout.addWidget(self.object_size_spin, 2, 1)

        # Search area size
        layout.addWidget(QLabel("Search Area Size:"), 3, 0)
        self.search_area_spin = QSpinBox()
        self.search_area_spin.setRange(50, 1000)
        self.search_area_spin.setValue(200)
        layout.addWidget(self.search_area_spin, 3, 1)

        # Control buttons
        button_layout = QHBoxLayout()
        self.tracker_lock_btn = QPushButton("Lock Target")
        self.tracker_unlock_btn = QPushButton("Unlock")
        self.tracker_reset_btn = QPushButton("Reset")
        button_layout.addWidget(self.tracker_lock_btn)
        button_layout.addWidget(self.tracker_unlock_btn)
        button_layout.addWidget(self.tracker_reset_btn)
        layout.addLayout(button_layout, 4, 0, 1, 2)

        group.setLayout(layout)
        return group

    def create_motion_detector_group(self) -> QGroupBox:
        """Create MotionDetector settings group."""
        group = QGroupBox("Motion Detector")
        layout = QGridLayout()

        # Enable checkbox
        self.motion_detector_enable = QCheckBox("Enable Motion Detector")
        layout.addWidget(self.motion_detector_enable, 0, 0, 1, 2)

        # Frame buffer
        layout.addWidget(QLabel("Frame Buffer:"), 1, 0)
        self.md_frame_buffer_spin = QSpinBox()
        self.md_frame_buffer_spin.setRange(1, 30)
        self.md_frame_buffer_spin.setValue(10)
        layout.addWidget(self.md_frame_buffer_spin, 1, 1)

        # Min/Max width
        layout.addWidget(QLabel("Min Width:"), 2, 0)
        self.md_min_width_spin = QSpinBox()
        self.md_min_width_spin.setRange(10, 1000)
        self.md_min_width_spin.setValue(50)
        layout.addWidget(self.md_min_width_spin, 2, 1)

        layout.addWidget(QLabel("Max Width:"), 3, 0)
        self.md_max_width_spin = QSpinBox()
        self.md_max_width_spin.setRange(10, 1920)
        self.md_max_width_spin.setValue(500)
        layout.addWidget(self.md_max_width_spin, 3, 1)

        # Min/Max height
        layout.addWidget(QLabel("Min Height:"), 4, 0)
        self.md_min_height_spin = QSpinBox()
        self.md_min_height_spin.setRange(10, 1000)
        self.md_min_height_spin.setValue(50)
        layout.addWidget(self.md_min_height_spin, 4, 1)

        layout.addWidget(QLabel("Max Height:"), 5, 0)
        self.md_max_height_spin = QSpinBox()
        self.md_max_height_spin.setRange(10, 1080)
        self.md_max_height_spin.setValue(500)
        layout.addWidget(self.md_max_height_spin, 5, 1)

        # Sensitivity
        layout.addWidget(QLabel("Sensitivity:"), 6, 0)
        self.md_sensitivity_spin = QDoubleSpinBox()
        self.md_sensitivity_spin.setRange(0.0, 1.0)
        self.md_sensitivity_spin.setSingleStep(0.1)
        self.md_sensitivity_spin.setValue(0.5)
        layout.addWidget(self.md_sensitivity_spin, 6, 1)

        # Detection mode
        layout.addWidget(QLabel("Detection Mode:"), 7, 0)
        self.md_mode_combo = QComboBox()
        self.md_mode_combo.addItems(["Standard", "Sensitive", "Robust"])
        layout.addWidget(self.md_mode_combo, 7, 1)

        # Reset button
        self.md_reset_btn = QPushButton("Reset Motion Detector")
        layout.addWidget(self.md_reset_btn, 8, 0, 1, 2)

        group.setLayout(layout)
        return group

    def create_changes_detector_group(self) -> QGroupBox:
        """Create ChangesDetector settings group."""
        group = QGroupBox("Changes Detector")
        layout = QGridLayout()

        # Enable checkbox
        self.changes_detector_enable = QCheckBox("Enable Changes Detector")
        layout.addWidget(self.changes_detector_enable, 0, 0, 1, 2)

        # Frame buffer
        layout.addWidget(QLabel("Frame Buffer:"), 1, 0)
        self.cd_frame_buffer_spin = QSpinBox()
        self.cd_frame_buffer_spin.setRange(1, 30)
        self.cd_frame_buffer_spin.setValue(10)
        layout.addWidget(self.cd_frame_buffer_spin, 1, 1)

        # Min/Max width
        layout.addWidget(QLabel("Min Width:"), 2, 0)
        self.cd_min_width_spin = QSpinBox()
        self.cd_min_width_spin.setRange(10, 1000)
        self.cd_min_width_spin.setValue(50)
        layout.addWidget(self.cd_min_width_spin, 2, 1)

        layout.addWidget(QLabel("Max Width:"), 3, 0)
        self.cd_max_width_spin = QSpinBox()
        self.cd_max_width_spin.setRange(10, 1920)
        self.cd_max_width_spin.setValue(500)
        layout.addWidget(self.cd_max_width_spin, 3, 1)

        # Min/Max height
        layout.addWidget(QLabel("Min Height:"), 4, 0)
        self.cd_min_height_spin = QSpinBox()
        self.cd_min_height_spin.setRange(10, 1000)
        self.cd_min_height_spin.setValue(50)
        layout.addWidget(self.cd_min_height_spin, 4, 1)

        layout.addWidget(QLabel("Max Height:"), 5, 0)
        self.cd_max_height_spin = QSpinBox()
        self.cd_max_height_spin.setRange(10, 1080)
        self.cd_max_height_spin.setValue(500)
        layout.addWidget(self.cd_max_height_spin, 5, 1)

        # Sensitivity
        layout.addWidget(QLabel("Sensitivity:"), 6, 0)
        self.cd_sensitivity_spin = QDoubleSpinBox()
        self.cd_sensitivity_spin.setRange(0.0, 1.0)
        self.cd_sensitivity_spin.setSingleStep(0.1)
        self.cd_sensitivity_spin.setValue(0.5)
        layout.addWidget(self.cd_sensitivity_spin, 6, 1)

        # Detection mode
        layout.addWidget(QLabel("Detection Mode:"), 7, 0)
        self.cd_mode_combo = QComboBox()
        self.cd_mode_combo.addItems(["Standard", "Sensitive", "Robust"])
        layout.addWidget(self.cd_mode_combo, 7, 1)

        # Reset button
        self.cd_reset_btn = QPushButton("Reset Changes Detector")
        layout.addWidget(self.cd_reset_btn, 8, 0, 1, 2)

        group.setLayout(layout)
        return group

    def create_classification_group(self) -> QGroupBox:
        """Create Classification settings group."""
        group = QGroupBox("Classification")
        layout = QGridLayout()

        # Enable checkbox
        self.classification_enable = QCheckBox("Enable Classification")
        layout.addWidget(self.classification_enable, 0, 0, 1, 2)

        # Model selection
        layout.addWidget(QLabel("Model:"), 1, 0)
        self.classification_model_combo = QComboBox()
        self.classification_model_combo.addItems(["YOLO v5", "ResNet50", "MobileNet"])
        layout.addWidget(self.classification_model_combo, 1, 1)

        # Confidence threshold
        layout.addWidget(QLabel("Confidence:"), 2, 0)
        self.classification_confidence_spin = QDoubleSpinBox()
        self.classification_confidence_spin.setRange(0.0, 1.0)
        self.classification_confidence_spin.setSingleStep(0.05)
        self.classification_confidence_spin.setValue(0.75)
        layout.addWidget(self.classification_confidence_spin, 2, 1)

        # Query button
        self.query_classification_btn = QPushButton("Query Classification Status")
        layout.addWidget(self.query_classification_btn, 3, 0, 1, 2)

        group.setLayout(layout)
        return group

    def create_detection_results_group(self) -> QGroupBox:
        """Create Detection Results group."""
        group = QGroupBox("Detection Results")
        layout = QVBoxLayout()

        # Results text area
        self.detection_results_text = QLabel("No detection results")
        self.detection_results_text.setStyleSheet("""
            QLabel {
                background-color: #1e1e1e;
                padding: 10px;
                border: 1px solid #555;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
            }
        """)
        self.detection_results_text.setWordWrap(True)
        self.detection_results_text.setMinimumHeight(80)
        layout.addWidget(self.detection_results_text)

        # Buttons
        button_layout = QHBoxLayout()
        self.subscribe_detection_btn = QPushButton("Subscribe")
        self.clear_detection_btn = QPushButton("Clear")
        button_layout.addWidget(self.subscribe_detection_btn)
        button_layout.addWidget(self.clear_detection_btn)
        layout.addLayout(button_layout)

        group.setLayout(layout)
        return group

    def create_license_status_group(self) -> QGroupBox:
        """Create License Status group."""
        group = QGroupBox("License Status")
        layout = QVBoxLayout()

        # Query buttons for each feature
        self.query_vt_license_btn = QPushButton("Query VideoTracker License")
        self.query_vs_license_btn = QPushButton("Query VideoStabiliser License")
        self.query_md_license_btn = QPushButton("Query MotionDetector License")
        self.query_cd_license_btn = QPushButton("Query ChangesDetector License")
        self.query_class_license_btn = QPushButton("Query Classification License")

        layout.addWidget(self.query_vt_license_btn)
        layout.addWidget(self.query_vs_license_btn)
        layout.addWidget(self.query_md_license_btn)
        layout.addWidget(self.query_cd_license_btn)
        layout.addWidget(self.query_class_license_btn)

        group.setLayout(layout)
        return group

    def connect_signals(self):
        """Connect all widget signals to emit corresponding pyqtSignals."""
        # Motion Magnificator
        self.motion_mag_enable.toggled.connect(
            lambda checked: self.motion_magnificator_changed.emit(self.get_selected_camera(), checked)
        )
        self.mag_level_spin.valueChanged.connect(
            lambda value: self.magnification_level_changed.emit(self.get_selected_camera(), value)
        )

        # VideoTracker
        self.video_tracker_enable.toggled.connect(
            lambda checked: self.video_tracker_changed.emit(self.get_selected_camera(), checked)
        )
        self.tracker_mode_combo.currentIndexChanged.connect(
            lambda idx: self.tracker_mode_changed.emit(self.get_selected_camera(), idx)
        )
        self.object_size_spin.valueChanged.connect(
            lambda value: self.object_size_changed.emit(self.get_selected_camera(), value)
        )
        self.search_area_spin.valueChanged.connect(
            lambda value: self.search_area_size_changed.emit(self.get_selected_camera(), value)
        )
        self.tracker_lock_btn.clicked.connect(
            lambda: self.video_tracker_lock_pressed.emit(self.get_selected_camera())
        )
        self.tracker_unlock_btn.clicked.connect(
            lambda: self.video_tracker_unlock_pressed.emit(self.get_selected_camera())
        )
        self.tracker_reset_btn.clicked.connect(
            lambda: self.video_tracker_reset_pressed.emit(self.get_selected_camera())
        )

        # MotionDetector
        self.motion_detector_enable.toggled.connect(
            lambda checked: self.motion_detector_changed.emit(self.get_selected_camera(), checked)
        )
        self.md_frame_buffer_spin.valueChanged.connect(
            lambda value: self.motion_detector_frame_buffer_changed.emit(self.get_selected_camera(), value)
        )
        self.md_min_width_spin.valueChanged.connect(
            lambda value: self.motion_detector_min_width_changed.emit(self.get_selected_camera(), value)
        )
        self.md_max_width_spin.valueChanged.connect(
            lambda value: self.motion_detector_max_width_changed.emit(self.get_selected_camera(), value)
        )
        self.md_min_height_spin.valueChanged.connect(
            lambda value: self.motion_detector_min_height_changed.emit(self.get_selected_camera(), value)
        )
        self.md_max_height_spin.valueChanged.connect(
            lambda value: self.motion_detector_max_height_changed.emit(self.get_selected_camera(), value)
        )
        self.md_sensitivity_spin.valueChanged.connect(
            lambda value: self.motion_detector_sensitivity_changed.emit(self.get_selected_camera(), value)
        )
        self.md_mode_combo.currentIndexChanged.connect(
            lambda idx: self.motion_detector_mode_changed.emit(self.get_selected_camera(), idx)
        )
        self.md_reset_btn.clicked.connect(
            lambda: self.motion_detector_reset_pressed.emit(self.get_selected_camera())
        )

        # ChangesDetector
        self.changes_detector_enable.toggled.connect(
            lambda checked: self.changes_detector_changed.emit(self.get_selected_camera(), checked)
        )
        self.cd_frame_buffer_spin.valueChanged.connect(
            lambda value: self.changes_detector_frame_buffer_changed.emit(self.get_selected_camera(), value)
        )
        self.cd_min_width_spin.valueChanged.connect(
            lambda value: self.changes_detector_min_width_changed.emit(self.get_selected_camera(), value)
        )
        self.cd_max_width_spin.valueChanged.connect(
            lambda value: self.changes_detector_max_width_changed.emit(self.get_selected_camera(), value)
        )
        self.cd_min_height_spin.valueChanged.connect(
            lambda value: self.changes_detector_min_height_changed.emit(self.get_selected_camera(), value)
        )
        self.cd_max_height_spin.valueChanged.connect(
            lambda value: self.changes_detector_max_height_changed.emit(self.get_selected_camera(), value)
        )
        self.cd_sensitivity_spin.valueChanged.connect(
            lambda value: self.changes_detector_sensitivity_changed.emit(self.get_selected_camera(), value)
        )
        self.cd_mode_combo.currentIndexChanged.connect(
            lambda idx: self.changes_detector_mode_changed.emit(self.get_selected_camera(), idx)
        )
        self.cd_reset_btn.clicked.connect(
            lambda: self.changes_detector_reset_pressed.emit(self.get_selected_camera())
        )

        # Classification
        self.classification_enable.toggled.connect(
            lambda checked: self.classification_changed.emit(self.get_selected_camera(), checked)
        )
        self.classification_model_combo.currentTextChanged.connect(
            lambda text: self.classification_model_changed.emit(self.get_selected_camera(), text)
        )
        self.classification_confidence_spin.valueChanged.connect(
            lambda value: self.classification_confidence_changed.emit(self.get_selected_camera(), value)
        )
        self.query_classification_btn.clicked.connect(
            lambda: self.query_classification_pressed.emit(self.get_selected_camera())
        )

        # Detection Results
        self.subscribe_detection_btn.clicked.connect(
            lambda: self.subscribe_detection_pressed.emit(self.get_selected_camera())
        )
        self.clear_detection_btn.clicked.connect(
            lambda: self.clear_detection_pressed.emit(self.get_selected_camera())
        )

        # License Status (no camera parameter)
        self.query_vt_license_btn.clicked.connect(self.query_video_tracker_license_pressed.emit)
        self.query_vs_license_btn.clicked.connect(self.query_video_stabiliser_license_pressed.emit)
        self.query_md_license_btn.clicked.connect(self.query_motion_detector_license_pressed.emit)
        self.query_cd_license_btn.clicked.connect(self.query_changes_detector_license_pressed.emit)
        self.query_class_license_btn.clicked.connect(self.query_classification_license_pressed.emit)

    def on_camera_changed(self, index: int):
        """Handle camera selection change."""
        self.selected_camera = index + 1  # 0-based index to 1-based camera number
        logger.info(f"Tracker settings camera changed to Camera {self.selected_camera}")

    def get_selected_camera(self) -> int:
        """Get the currently selected camera number (1, 2, or 3)."""
        return self.selected_camera




