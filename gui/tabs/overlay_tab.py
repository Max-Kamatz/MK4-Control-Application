"""
gui/tabs/overlay_tab.py
Overlay Tab - Configure on-screen display elements for video streams.
Includes crosshair, information overlays, and WebRTC overlay settings.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QGridLayout, QPushButton, QSlider, QComboBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from utils.constants import load_config
from utils.logger import setup_logger

logger = setup_logger()


class OverlayTab(QWidget):
    """
    Overlay Tab for on-screen display configuration.
    Contains 4 groups: Target Camera Selector, Crosshair, Information Overlays, and WebRTC Overlay.
    All overlay settings apply to the currently selected camera.
    """

    # Target Camera Selector signal
    target_camera_changed = pyqtSignal(int)  # camera (0=Daylight, 1=Thermal, 2=SWIR)

    # Crosshair signals
    crosshair_mode_changed = pyqtSignal(int, bool)  # camera, enable
    crosshair_size_changed = pyqtSignal(int, int)  # camera, size (1-100 pixels)
    crosshair_color_changed = pyqtSignal(int, str)  # camera, color

    # Information Overlay signals
    datetime_overlay_changed = pyqtSignal(int, bool)  # camera, enable
    zoom_pos_overlay_changed = pyqtSignal(int, bool)  # camera, enable
    focus_mode_overlay_changed = pyqtSignal(int, bool)  # camera, enable
    digital_zoom_overlay_changed = pyqtSignal(int, bool)  # camera, enable
    clahe_overlay_changed = pyqtSignal(int, bool)  # camera, enable
    tracker_overlay_changed = pyqtSignal(int, bool)  # camera, enable
    pan_tilt_overlay_changed = pyqtSignal(int, bool)  # camera, enable
    lrf_overlay_changed = pyqtSignal(int, bool)  # camera, enable

    # WebRTC Overlay signal
    webrtc_overlay_changed = pyqtSignal(int, bool)  # camera, enable

    def __init__(self, video_manager=None):
        super().__init__()
        self.config = load_config()
        self.current_camera = 0  # Default to Camera 1 (Daylight)
        self.video_manager = video_manager
        self.video_placeholder = None  # Will hold the shared video display
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """Initialize the Overlay tab UI with left settings panel and right video section."""
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Overlay settings in scrollable area (fixed width)
        left_widget = self.create_settings_section()

        # Right side: Video streams (expands to fill space)
        right_widget = self.create_video_section()

        # Use simple horizontal layout - settings panel has fixed width, video expands
        main_layout.addWidget(left_widget, 0)   # Settings panel fixed width (no stretch)
        main_layout.addWidget(right_widget, 1)  # Video expands (stretch factor 1)

        self.setLayout(main_layout)

        logger.info("Overlay tab initialized")

    def create_settings_section(self) -> QWidget:
        """Create scrollable settings section."""
        # Create container widget with fixed width
        container = QWidget()
        container.setFixedWidth(480)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create content widget for scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Group 1: Target Camera Selector
        camera_selector_group = self.create_camera_selector_group()
        content_layout.addWidget(camera_selector_group)

        # Group 2: Crosshair
        crosshair_group = self.create_crosshair_group()
        content_layout.addWidget(crosshair_group)

        # Group 3: Information Overlays
        info_overlays_group = self.create_information_overlays_group()
        content_layout.addWidget(info_overlays_group)

        # Group 4: WebRTC Overlay
        webrtc_group = self.create_webrtc_overlay_group()
        content_layout.addWidget(webrtc_group)

        content_layout.addStretch()
        content_widget.setLayout(content_layout)

        # Set content widget to scroll area
        scroll.setWidget(content_widget)

        # Container layout
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll)
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

    def create_camera_selector_group(self) -> QGroupBox:
        """Create Target Camera Selector group."""
        group = QGroupBox("Target Camera Selector")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("Select Camera:"), 0, 0)
        self.camera_selector = QComboBox()
        self.camera_selector.addItems([
            "Camera 1 (Daylight)",
            "Camera 2 (Thermal)",
            "Camera 3 (SWIR)"
        ])
        layout.addWidget(self.camera_selector, 0, 1, 1, 2)

        layout.addWidget(QLabel("<i>All overlay settings below apply to the selected camera</i>"), 1, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_crosshair_group(self) -> QGroupBox:
        """Create Crosshair group."""
        group = QGroupBox("Crosshair")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Crosshair Mode
        layout.addWidget(QLabel("Crosshair Mode:"), 0, 0, 1, 3)
        crosshair_mode_layout = QHBoxLayout()
        self.crosshair_enable_button = QPushButton("Enable")
        self.crosshair_disable_button = QPushButton("Disable")
        crosshair_mode_layout.addWidget(self.crosshair_enable_button)
        crosshair_mode_layout.addWidget(self.crosshair_disable_button)
        layout.addLayout(crosshair_mode_layout, 1, 0, 1, 3)

        # Crosshair Size
        layout.addWidget(QLabel("Crosshair Size (pixels):"), 2, 0)
        self.crosshair_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.crosshair_size_slider.setMinimum(1)
        self.crosshair_size_slider.setMaximum(100)
        self.crosshair_size_slider.setValue(20)
        self.crosshair_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.crosshair_size_slider.setTickInterval(10)
        layout.addWidget(self.crosshair_size_slider, 2, 1)
        self.crosshair_size_label = QLabel("20")
        layout.addWidget(self.crosshair_size_label, 2, 2)

        # Crosshair Color
        layout.addWidget(QLabel("Crosshair Color:"), 3, 0)
        self.crosshair_color_combo = QComboBox()
        self.crosshair_color_combo.addItems(["White", "Black", "Red", "Green", "Blue", "Contrast"])
        layout.addWidget(self.crosshair_color_combo, 3, 1, 1, 2)

        group.setLayout(layout)
        return group

    def create_information_overlays_group(self) -> QGroupBox:
        """Create Information Overlays group."""
        group = QGroupBox("Information Overlays")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Date & Time Display
        layout.addWidget(QLabel("Date & Time Display:"), 0, 0, 1, 3)
        datetime_layout = QHBoxLayout()
        self.datetime_enable_button = QPushButton("Enable")
        self.datetime_disable_button = QPushButton("Disable")
        datetime_layout.addWidget(self.datetime_enable_button)
        datetime_layout.addWidget(self.datetime_disable_button)
        layout.addLayout(datetime_layout, 1, 0, 1, 3)

        # Zoom Position Display
        layout.addWidget(QLabel("Zoom Position Display:"), 2, 0, 1, 3)
        zoom_pos_layout = QHBoxLayout()
        self.zoom_pos_enable_button = QPushButton("Enable")
        self.zoom_pos_disable_button = QPushButton("Disable")
        zoom_pos_layout.addWidget(self.zoom_pos_enable_button)
        zoom_pos_layout.addWidget(self.zoom_pos_disable_button)
        layout.addLayout(zoom_pos_layout, 3, 0, 1, 3)

        # Focus Mode Display
        layout.addWidget(QLabel("Focus Mode Display:"), 4, 0, 1, 3)
        focus_mode_layout = QHBoxLayout()
        self.focus_mode_enable_button = QPushButton("Enable")
        self.focus_mode_disable_button = QPushButton("Disable")
        focus_mode_layout.addWidget(self.focus_mode_enable_button)
        focus_mode_layout.addWidget(self.focus_mode_disable_button)
        layout.addLayout(focus_mode_layout, 5, 0, 1, 3)

        # Digital Zoom Level Display
        layout.addWidget(QLabel("Digital Zoom Level Display:"), 6, 0, 1, 3)
        digital_zoom_layout = QHBoxLayout()
        self.digital_zoom_enable_button = QPushButton("Enable")
        self.digital_zoom_disable_button = QPushButton("Disable")
        digital_zoom_layout.addWidget(self.digital_zoom_enable_button)
        digital_zoom_layout.addWidget(self.digital_zoom_disable_button)
        layout.addLayout(digital_zoom_layout, 7, 0, 1, 3)

        # CLAHE Status Display
        layout.addWidget(QLabel("CLAHE Status Display:"), 8, 0, 1, 3)
        clahe_layout = QHBoxLayout()
        self.clahe_enable_button = QPushButton("Enable")
        self.clahe_disable_button = QPushButton("Disable")
        clahe_layout.addWidget(self.clahe_enable_button)
        clahe_layout.addWidget(self.clahe_disable_button)
        layout.addLayout(clahe_layout, 9, 0, 1, 3)

        # Tracker Status Display
        layout.addWidget(QLabel("Tracker Status Display:"), 10, 0, 1, 3)
        tracker_layout = QHBoxLayout()
        self.tracker_enable_button = QPushButton("Enable")
        self.tracker_disable_button = QPushButton("Disable")
        tracker_layout.addWidget(self.tracker_enable_button)
        tracker_layout.addWidget(self.tracker_disable_button)
        layout.addLayout(tracker_layout, 11, 0, 1, 3)

        # Pan/Tilt Position Display
        layout.addWidget(QLabel("Pan/Tilt Position Display:"), 12, 0, 1, 3)
        pan_tilt_layout = QHBoxLayout()
        self.pan_tilt_enable_button = QPushButton("Enable")
        self.pan_tilt_disable_button = QPushButton("Disable")
        pan_tilt_layout.addWidget(self.pan_tilt_enable_button)
        pan_tilt_layout.addWidget(self.pan_tilt_disable_button)
        layout.addLayout(pan_tilt_layout, 13, 0, 1, 3)

        # LRF Range Display
        layout.addWidget(QLabel("LRF Range Display:"), 14, 0, 1, 3)
        lrf_layout = QHBoxLayout()
        self.lrf_enable_button = QPushButton("Enable")
        self.lrf_disable_button = QPushButton("Disable")
        lrf_layout.addWidget(self.lrf_enable_button)
        lrf_layout.addWidget(self.lrf_disable_button)
        layout.addLayout(lrf_layout, 15, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_webrtc_overlay_group(self) -> QGroupBox:
        """Create WebRTC Overlay group."""
        group = QGroupBox("WebRTC Overlay")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("WebRTC Overlay:"), 0, 0, 1, 3)
        webrtc_layout = QHBoxLayout()
        self.webrtc_enable_button = QPushButton("Enable")
        self.webrtc_disable_button = QPushButton("Disable")
        webrtc_layout.addWidget(self.webrtc_enable_button)
        webrtc_layout.addWidget(self.webrtc_disable_button)
        layout.addLayout(webrtc_layout, 1, 0, 1, 3)

        group.setLayout(layout)
        return group

    def connect_signals(self):
        """Connect all control signals to their respective handlers."""
        # Target Camera Selector
        self.camera_selector.currentIndexChanged.connect(self.on_camera_changed)

        # Crosshair controls
        self.crosshair_enable_button.clicked.connect(lambda: self.on_crosshair_mode_changed(True))
        self.crosshair_disable_button.clicked.connect(lambda: self.on_crosshair_mode_changed(False))
        self.crosshair_size_slider.valueChanged.connect(self.on_crosshair_size_changed)
        self.crosshair_color_combo.currentTextChanged.connect(self.on_crosshair_color_changed)

        # Information Overlay controls
        self.datetime_enable_button.clicked.connect(lambda: self.on_datetime_overlay_changed(True))
        self.datetime_disable_button.clicked.connect(lambda: self.on_datetime_overlay_changed(False))
        self.zoom_pos_enable_button.clicked.connect(lambda: self.on_zoom_pos_overlay_changed(True))
        self.zoom_pos_disable_button.clicked.connect(lambda: self.on_zoom_pos_overlay_changed(False))
        self.focus_mode_enable_button.clicked.connect(lambda: self.on_focus_mode_overlay_changed(True))
        self.focus_mode_disable_button.clicked.connect(lambda: self.on_focus_mode_overlay_changed(False))
        self.digital_zoom_enable_button.clicked.connect(lambda: self.on_digital_zoom_overlay_changed(True))
        self.digital_zoom_disable_button.clicked.connect(lambda: self.on_digital_zoom_overlay_changed(False))
        self.clahe_enable_button.clicked.connect(lambda: self.on_clahe_overlay_changed(True))
        self.clahe_disable_button.clicked.connect(lambda: self.on_clahe_overlay_changed(False))
        self.tracker_enable_button.clicked.connect(lambda: self.on_tracker_overlay_changed(True))
        self.tracker_disable_button.clicked.connect(lambda: self.on_tracker_overlay_changed(False))
        self.pan_tilt_enable_button.clicked.connect(lambda: self.on_pan_tilt_overlay_changed(True))
        self.pan_tilt_disable_button.clicked.connect(lambda: self.on_pan_tilt_overlay_changed(False))
        self.lrf_enable_button.clicked.connect(lambda: self.on_lrf_overlay_changed(True))
        self.lrf_disable_button.clicked.connect(lambda: self.on_lrf_overlay_changed(False))

        # WebRTC Overlay controls
        self.webrtc_enable_button.clicked.connect(lambda: self.on_webrtc_overlay_changed(True))
        self.webrtc_disable_button.clicked.connect(lambda: self.on_webrtc_overlay_changed(False))

    # Handler methods

    def on_camera_changed(self, index: int):
        """Handle camera selection change."""
        self.current_camera = index
        camera_names = ["Daylight", "Thermal", "SWIR"]
        logger.info(f"Overlay Tab: Target camera changed to {index} ({camera_names[index]})")
        self.target_camera_changed.emit(index)

    def on_crosshair_mode_changed(self, enable: bool):
        """Handle Crosshair Mode change."""
        logger.info(f"Overlay Tab: Crosshair Mode for Camera {self.current_camera}: {'ENABLED' if enable else 'DISABLED'}")
        self.crosshair_mode_changed.emit(self.current_camera, enable)

    def on_crosshair_size_changed(self, size: int):
        """Handle Crosshair Size change."""
        if 1 <= size <= 100:
            self.crosshair_size_label.setText(str(size))
            logger.info(f"Overlay Tab: Crosshair Size for Camera {self.current_camera}: {size} pixels")
            self.crosshair_size_changed.emit(self.current_camera, size)
        else:
            logger.warning(f"Overlay Tab: Invalid Crosshair Size: {size} (must be 1-100)")

    def on_crosshair_color_changed(self, color: str):
        """Handle Crosshair Color change."""
        logger.info(f"Overlay Tab: Crosshair Color for Camera {self.current_camera}: {color}")
        self.crosshair_color_changed.emit(self.current_camera, color)

    def on_datetime_overlay_changed(self, enable: bool):
        """Handle Date & Time Display change."""
        logger.info(f"Overlay Tab: Date & Time Display for Camera {self.current_camera}: {'ENABLED' if enable else 'DISABLED'}")
        self.datetime_overlay_changed.emit(self.current_camera, enable)

    def on_zoom_pos_overlay_changed(self, enable: bool):
        """Handle Zoom Position Display change."""
        logger.info(f"Overlay Tab: Zoom Position Display for Camera {self.current_camera}: {'ENABLED' if enable else 'DISABLED'}")
        self.zoom_pos_overlay_changed.emit(self.current_camera, enable)

    def on_focus_mode_overlay_changed(self, enable: bool):
        """Handle Focus Mode Display change."""
        logger.info(f"Overlay Tab: Focus Mode Display for Camera {self.current_camera}: {'ENABLED' if enable else 'DISABLED'}")
        self.focus_mode_overlay_changed.emit(self.current_camera, enable)

    def on_digital_zoom_overlay_changed(self, enable: bool):
        """Handle Digital Zoom Level Display change."""
        logger.info(f"Overlay Tab: Digital Zoom Level Display for Camera {self.current_camera}: {'ENABLED' if enable else 'DISABLED'}")
        self.digital_zoom_overlay_changed.emit(self.current_camera, enable)

    def on_clahe_overlay_changed(self, enable: bool):
        """Handle CLAHE Status Display change."""
        logger.info(f"Overlay Tab: CLAHE Status Display for Camera {self.current_camera}: {'ENABLED' if enable else 'DISABLED'}")
        self.clahe_overlay_changed.emit(self.current_camera, enable)

    def on_tracker_overlay_changed(self, enable: bool):
        """Handle Tracker Status Display change."""
        logger.info(f"Overlay Tab: Tracker Status Display for Camera {self.current_camera}: {'ENABLED' if enable else 'DISABLED'}")
        self.tracker_overlay_changed.emit(self.current_camera, enable)

    def on_pan_tilt_overlay_changed(self, enable: bool):
        """Handle Pan/Tilt Position Display change."""
        logger.info(f"Overlay Tab: Pan/Tilt Position Display for Camera {self.current_camera}: {'ENABLED' if enable else 'DISABLED'}")
        self.pan_tilt_overlay_changed.emit(self.current_camera, enable)

    def on_lrf_overlay_changed(self, enable: bool):
        """Handle LRF Range Display change."""
        logger.info(f"Overlay Tab: LRF Range Display for Camera {self.current_camera}: {'ENABLED' if enable else 'DISABLED'}")
        self.lrf_overlay_changed.emit(self.current_camera, enable)

    def on_webrtc_overlay_changed(self, enable: bool):
        """Handle WebRTC Overlay change."""
        logger.info(f"Overlay Tab: WebRTC Overlay for Camera {self.current_camera}: {'ENABLED' if enable else 'DISABLED'}")
        self.webrtc_overlay_changed.emit(self.current_camera, enable)




