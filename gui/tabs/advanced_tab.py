"""
gui/tabs/advanced_tab.py
Advanced tab - Phase 4B advanced features.
Includes Procedure Manager, Bad Pixel Processor, Video Source, WebRTC Overlay,
External UP Forwarding, and Pelco-D Forwarding.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QGridLayout, QPushButton, QLineEdit,
                             QScrollArea, QTextEdit)
from PyQt6.QtCore import pyqtSignal, Qt
from utils.constants import load_config
from utils.logger import setup_logger

logger = setup_logger()


class AdvancedTab(QWidget):
    """
    Advanced tab for Phase 4B features.
    Contains 6 groups: Procedure Manager, Bad Pixel Processor, Video Source,
    WebRTC Overlay, External UP Forwarding, and Pelco-D Forwarding.
    """

    # ========================================================================
    # Procedure Manager signals (4)
    # ========================================================================
    procedure_load_requested = pyqtSignal(str)  # procedure_name
    procedure_execute_requested = pyqtSignal()
    procedure_stop_requested = pyqtSignal()
    procedure_status_query_requested = pyqtSignal()

    # ========================================================================
    # Bad Pixel Processor signals (5)
    # ========================================================================
    bad_pixel_enabled = pyqtSignal(int)  # camera
    bad_pixel_disabled = pyqtSignal(int)  # camera
    bad_pixel_calibrate = pyqtSignal(int)  # camera
    bad_pixel_threshold_changed = pyqtSignal(int, float)  # camera, threshold
    bad_pixel_query_requested = pyqtSignal(int)  # camera

    # ========================================================================
    # Video Source signals (2)
    # ========================================================================
    video_source_changed = pyqtSignal(int, str)  # camera, source_id
    video_source_query_requested = pyqtSignal(int)  # camera

    # ========================================================================
    # WebRTC Overlay signals (3)
    # ========================================================================
    webrtc_overlay_enabled = pyqtSignal(int)  # camera
    webrtc_overlay_disabled = pyqtSignal(int)  # camera
    webrtc_overlay_query_requested = pyqtSignal(int)  # camera

    # ========================================================================
    # External UP Forwarding signals (5)
    # ========================================================================
    external_up_enabled = pyqtSignal()
    external_up_disabled = pyqtSignal()
    external_up_port_changed = pyqtSignal(int)  # port
    external_up_address_changed = pyqtSignal(str)  # address
    external_up_query_requested = pyqtSignal()

    # ========================================================================
    # Pelco-D Forwarding signals (5)
    # ========================================================================
    pelco_d_enabled = pyqtSignal()
    pelco_d_disabled = pyqtSignal()
    pelco_d_port_changed = pyqtSignal(int)  # port
    pelco_d_address_changed = pyqtSignal(str)  # address
    pelco_d_query_requested = pyqtSignal()

    def __init__(self, video_manager=None):
        super().__init__()
        self.config = load_config()
        # Track selected cameras for each feature
        self.selected_camera_bad_pixel = 1
        self.selected_camera_video_source = 1
        self.selected_camera_webrtc = 1
        self.video_manager = video_manager
        self.video_placeholder = None  # Will hold the shared video display
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """Initialize the Advanced tab UI - LEFT side scrollable settings, RIGHT side video feeds."""
        # Main horizontal layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Scrollable settings panel (fixed width 480px)
        left_widget = self.create_settings_section()

        # Right side: Video feeds (expands to fill space)
        right_widget = self.create_video_section()

        # Add widgets - control panel fixed width, video expands
        main_layout.addWidget(left_widget, 0)   # Settings panel fixed width (no stretch)
        main_layout.addWidget(right_widget, 1)  # Video expands (stretch factor 1)

        self.setLayout(main_layout)
        logger.info("Advanced tab initialized with video feeds")

    def create_settings_section(self) -> QWidget:
        """Create left-side scrollable settings panel."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedWidth(480)

        # Create container widget
        container = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)
        settings_layout.setContentsMargins(10, 10, 10, 10)

        # Group 1: Procedure Manager
        procedure_group = self.create_procedure_manager_group()
        settings_layout.addWidget(procedure_group)

        # Group 2: Bad Pixel Processor
        bad_pixel_group = self.create_bad_pixel_processor_group()
        settings_layout.addWidget(bad_pixel_group)

        # Group 3: Video Source
        video_source_group = self.create_video_source_group()
        settings_layout.addWidget(video_source_group)

        # Group 4: WebRTC Overlay
        webrtc_group = self.create_webrtc_overlay_group()
        settings_layout.addWidget(webrtc_group)

        # Group 5: External UP Forwarding
        external_up_group = self.create_external_up_forwarding_group()
        settings_layout.addWidget(external_up_group)

        # Group 6: Pelco-D Forwarding
        pelco_d_group = self.create_pelco_d_forwarding_group()
        settings_layout.addWidget(pelco_d_group)

        settings_layout.addStretch()
        container.setLayout(settings_layout)

        # Set container in scroll area
        scroll.setWidget(container)

        return scroll

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

    def create_procedure_manager_group(self) -> QGroupBox:
        """Create Procedure Manager group."""
        group = QGroupBox("Procedure Manager")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Procedure Name
        layout.addWidget(QLabel("Procedure Name:"), 0, 0)
        self.procedure_name_input = QLineEdit()
        self.procedure_name_input.setPlaceholderText("Enter procedure name")
        layout.addWidget(self.procedure_name_input, 0, 1)
        self.procedure_load_button = QPushButton("Load")
        layout.addWidget(self.procedure_load_button, 0, 2)

        # Execute Procedure
        self.procedure_execute_button = QPushButton("Execute Procedure")
        layout.addWidget(self.procedure_execute_button, 1, 0, 1, 3)

        # Stop Procedure
        self.procedure_stop_button = QPushButton("Stop Procedure")
        layout.addWidget(self.procedure_stop_button, 2, 0, 1, 3)

        # Query Status
        self.procedure_query_button = QPushButton("Query Status")
        layout.addWidget(self.procedure_query_button, 3, 0, 1, 3)

        # Status Display
        layout.addWidget(QLabel("Status:"), 4, 0, 1, 3)
        self.procedure_status_display = QTextEdit()
        self.procedure_status_display.setReadOnly(True)
        self.procedure_status_display.setFixedHeight(100)
        layout.addWidget(self.procedure_status_display, 5, 0, 1, 3)

        # Clear Status
        self.procedure_clear_button = QPushButton("Clear Status")
        layout.addWidget(self.procedure_clear_button, 6, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_bad_pixel_processor_group(self) -> QGroupBox:
        """Create Bad Pixel Processor group."""
        group = QGroupBox("Bad Pixel Processor")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Target Camera Selector
        layout.addWidget(QLabel("Target Camera:"), 0, 0, 1, 3)
        camera_layout = QHBoxLayout()
        self.bad_pixel_cam1_button = QPushButton("Camera 1")
        self.bad_pixel_cam2_button = QPushButton("Camera 2")
        self.bad_pixel_cam3_button = QPushButton("Camera 3")
        camera_layout.addWidget(self.bad_pixel_cam1_button)
        camera_layout.addWidget(self.bad_pixel_cam2_button)
        camera_layout.addWidget(self.bad_pixel_cam3_button)
        layout.addLayout(camera_layout, 1, 0, 1, 3)

        # Enable/Disable
        self.bad_pixel_enable_button = QPushButton("Enable")
        layout.addWidget(self.bad_pixel_enable_button, 2, 0)
        self.bad_pixel_disable_button = QPushButton("Disable")
        layout.addWidget(self.bad_pixel_disable_button, 2, 1, 1, 2)

        # Calibrate
        self.bad_pixel_calibrate_button = QPushButton("Calibrate")
        layout.addWidget(self.bad_pixel_calibrate_button, 3, 0, 1, 3)

        # Threshold
        layout.addWidget(QLabel("Threshold:"), 4, 0)
        self.bad_pixel_threshold_input = QLineEdit()
        self.bad_pixel_threshold_input.setPlaceholderText("e.g., 0.5")
        layout.addWidget(self.bad_pixel_threshold_input, 4, 1)
        self.bad_pixel_threshold_button = QPushButton("Set")
        layout.addWidget(self.bad_pixel_threshold_button, 4, 2)

        # Query Settings
        self.bad_pixel_query_button = QPushButton("Query Settings")
        layout.addWidget(self.bad_pixel_query_button, 5, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_video_source_group(self) -> QGroupBox:
        """Create Video Source group."""
        group = QGroupBox("Video Source")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Target Camera Selector
        layout.addWidget(QLabel("Target Camera:"), 0, 0, 1, 3)
        camera_layout = QHBoxLayout()
        self.video_source_cam1_button = QPushButton("Camera 1")
        self.video_source_cam2_button = QPushButton("Camera 2")
        self.video_source_cam3_button = QPushButton("Camera 3")
        camera_layout.addWidget(self.video_source_cam1_button)
        camera_layout.addWidget(self.video_source_cam2_button)
        camera_layout.addWidget(self.video_source_cam3_button)
        layout.addLayout(camera_layout, 1, 0, 1, 3)

        # Source ID
        layout.addWidget(QLabel("Source ID:"), 2, 0)
        self.video_source_id_input = QLineEdit()
        self.video_source_id_input.setPlaceholderText("Enter source ID")
        layout.addWidget(self.video_source_id_input, 2, 1)
        self.video_source_set_button = QPushButton("Set")
        layout.addWidget(self.video_source_set_button, 2, 2)

        # Query Source
        self.video_source_query_button = QPushButton("Query Source")
        layout.addWidget(self.video_source_query_button, 3, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_webrtc_overlay_group(self) -> QGroupBox:
        """Create WebRTC Overlay group."""
        group = QGroupBox("WebRTC Overlay")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Target Camera Selector
        layout.addWidget(QLabel("Target Camera:"), 0, 0, 1, 3)
        camera_layout = QHBoxLayout()
        self.webrtc_cam1_button = QPushButton("Camera 1")
        self.webrtc_cam2_button = QPushButton("Camera 2")
        self.webrtc_cam3_button = QPushButton("Camera 3")
        camera_layout.addWidget(self.webrtc_cam1_button)
        camera_layout.addWidget(self.webrtc_cam2_button)
        camera_layout.addWidget(self.webrtc_cam3_button)
        layout.addLayout(camera_layout, 1, 0, 1, 3)

        # Enable/Disable
        self.webrtc_enable_button = QPushButton("Enable")
        layout.addWidget(self.webrtc_enable_button, 2, 0)
        self.webrtc_disable_button = QPushButton("Disable")
        layout.addWidget(self.webrtc_disable_button, 2, 1, 1, 2)

        # Query Settings
        self.webrtc_query_button = QPushButton("Query Settings")
        layout.addWidget(self.webrtc_query_button, 3, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_external_up_forwarding_group(self) -> QGroupBox:
        """Create External UP Forwarding group."""
        group = QGroupBox("External UP Forwarding")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Enable/Disable
        self.external_up_enable_button = QPushButton("Enable")
        layout.addWidget(self.external_up_enable_button, 0, 0)
        self.external_up_disable_button = QPushButton("Disable")
        layout.addWidget(self.external_up_disable_button, 0, 1, 1, 2)

        # Port
        layout.addWidget(QLabel("Port:"), 1, 0)
        self.external_up_port_input = QLineEdit()
        self.external_up_port_input.setPlaceholderText("1-65535")
        layout.addWidget(self.external_up_port_input, 1, 1)
        self.external_up_port_button = QPushButton("Set")
        layout.addWidget(self.external_up_port_button, 1, 2)

        # Target Address
        layout.addWidget(QLabel("Target Address:"), 2, 0)
        self.external_up_address_input = QLineEdit()
        self.external_up_address_input.setPlaceholderText("IP:Port")
        layout.addWidget(self.external_up_address_input, 2, 1)
        self.external_up_address_button = QPushButton("Set")
        layout.addWidget(self.external_up_address_button, 2, 2)

        # Query Settings
        self.external_up_query_button = QPushButton("Query Settings")
        layout.addWidget(self.external_up_query_button, 3, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_pelco_d_forwarding_group(self) -> QGroupBox:
        """Create Pelco-D Forwarding group."""
        group = QGroupBox("Pelco-D Forwarding")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Enable/Disable
        self.pelco_d_enable_button = QPushButton("Enable")
        layout.addWidget(self.pelco_d_enable_button, 0, 0)
        self.pelco_d_disable_button = QPushButton("Disable")
        layout.addWidget(self.pelco_d_disable_button, 0, 1, 1, 2)

        # Port
        layout.addWidget(QLabel("Port:"), 1, 0)
        self.pelco_d_port_input = QLineEdit()
        self.pelco_d_port_input.setPlaceholderText("1-65535")
        layout.addWidget(self.pelco_d_port_input, 1, 1)
        self.pelco_d_port_button = QPushButton("Set")
        layout.addWidget(self.pelco_d_port_button, 1, 2)

        # Target Address
        layout.addWidget(QLabel("Target Address:"), 2, 0)
        self.pelco_d_address_input = QLineEdit()
        self.pelco_d_address_input.setPlaceholderText("IP:Port")
        layout.addWidget(self.pelco_d_address_input, 2, 1)
        self.pelco_d_address_button = QPushButton("Set")
        layout.addWidget(self.pelco_d_address_button, 2, 2)

        # Query Settings
        self.pelco_d_query_button = QPushButton("Query Settings")
        layout.addWidget(self.pelco_d_query_button, 3, 0, 1, 3)

        group.setLayout(layout)
        return group

    def connect_signals(self):
        """Connect all button signals to their respective handlers."""
        # Procedure Manager
        self.procedure_load_button.clicked.connect(self.on_procedure_load)
        self.procedure_execute_button.clicked.connect(self.on_procedure_execute)
        self.procedure_stop_button.clicked.connect(self.on_procedure_stop)
        self.procedure_query_button.clicked.connect(self.on_procedure_query)
        self.procedure_clear_button.clicked.connect(self.on_procedure_clear)

        # Bad Pixel Processor - Camera selection
        self.bad_pixel_cam1_button.clicked.connect(lambda: self.on_bad_pixel_camera_selected(1))
        self.bad_pixel_cam2_button.clicked.connect(lambda: self.on_bad_pixel_camera_selected(2))
        self.bad_pixel_cam3_button.clicked.connect(lambda: self.on_bad_pixel_camera_selected(3))
        # Bad Pixel Processor - Actions
        self.bad_pixel_enable_button.clicked.connect(self.on_bad_pixel_enable)
        self.bad_pixel_disable_button.clicked.connect(self.on_bad_pixel_disable)
        self.bad_pixel_calibrate_button.clicked.connect(self.on_bad_pixel_calibrate)
        self.bad_pixel_threshold_button.clicked.connect(self.on_bad_pixel_threshold_set)
        self.bad_pixel_query_button.clicked.connect(self.on_bad_pixel_query)

        # Video Source - Camera selection
        self.video_source_cam1_button.clicked.connect(lambda: self.on_video_source_camera_selected(1))
        self.video_source_cam2_button.clicked.connect(lambda: self.on_video_source_camera_selected(2))
        self.video_source_cam3_button.clicked.connect(lambda: self.on_video_source_camera_selected(3))
        # Video Source - Actions
        self.video_source_set_button.clicked.connect(self.on_video_source_set)
        self.video_source_query_button.clicked.connect(self.on_video_source_query)

        # WebRTC Overlay - Camera selection
        self.webrtc_cam1_button.clicked.connect(lambda: self.on_webrtc_camera_selected(1))
        self.webrtc_cam2_button.clicked.connect(lambda: self.on_webrtc_camera_selected(2))
        self.webrtc_cam3_button.clicked.connect(lambda: self.on_webrtc_camera_selected(3))
        # WebRTC Overlay - Actions
        self.webrtc_enable_button.clicked.connect(self.on_webrtc_enable)
        self.webrtc_disable_button.clicked.connect(self.on_webrtc_disable)
        self.webrtc_query_button.clicked.connect(self.on_webrtc_query)

        # External UP Forwarding
        self.external_up_enable_button.clicked.connect(self.on_external_up_enable)
        self.external_up_disable_button.clicked.connect(self.on_external_up_disable)
        self.external_up_port_button.clicked.connect(self.on_external_up_port_set)
        self.external_up_address_button.clicked.connect(self.on_external_up_address_set)
        self.external_up_query_button.clicked.connect(self.on_external_up_query)

        # Pelco-D Forwarding
        self.pelco_d_enable_button.clicked.connect(self.on_pelco_d_enable)
        self.pelco_d_disable_button.clicked.connect(self.on_pelco_d_disable)
        self.pelco_d_port_button.clicked.connect(self.on_pelco_d_port_set)
        self.pelco_d_address_button.clicked.connect(self.on_pelco_d_address_set)
        self.pelco_d_query_button.clicked.connect(self.on_pelco_d_query)

        # Initialize button states
        self.update_bad_pixel_camera_buttons()
        self.update_video_source_camera_buttons()
        self.update_webrtc_camera_buttons()

    # ========================================================================
    # Procedure Manager handlers
    # ========================================================================
    def on_procedure_load(self):
        """Handle Load Procedure button."""
        procedure_name = self.procedure_name_input.text().strip()
        if procedure_name:
            logger.info(f"Advanced: Load Procedure '{procedure_name}' requested")
            self.procedure_load_requested.emit(procedure_name)
        else:
            logger.warning("Advanced: Procedure name is empty")

    def on_procedure_execute(self):
        """Handle Execute Procedure button."""
        logger.info("Advanced: Execute Procedure requested")
        self.procedure_execute_requested.emit()

    def on_procedure_stop(self):
        """Handle Stop Procedure button."""
        logger.info("Advanced: Stop Procedure requested")
        self.procedure_stop_requested.emit()

    def on_procedure_query(self):
        """Handle Query Status button."""
        logger.info("Advanced: Query Procedure Status requested")
        self.procedure_status_query_requested.emit()

    def on_procedure_clear(self):
        """Handle Clear Status button."""
        logger.info("Advanced: Clear Procedure Status")
        self.procedure_status_display.clear()

    def append_procedure_status(self, text: str):
        """Append text to procedure status display (for external updates)."""
        self.procedure_status_display.append(text)

    # ========================================================================
    # Bad Pixel Processor handlers
    # ========================================================================
    def on_bad_pixel_camera_selected(self, camera: int):
        """Handle Bad Pixel Processor camera selection."""
        self.selected_camera_bad_pixel = camera
        logger.info(f"Advanced: Bad Pixel Processor Camera {camera} selected")
        self.update_bad_pixel_camera_buttons()

    def update_bad_pixel_camera_buttons(self):
        """Update Bad Pixel Processor camera button styles to show selection."""
        self.bad_pixel_cam1_button.setStyleSheet("font-weight: bold;" if self.selected_camera_bad_pixel == 1 else "")
        self.bad_pixel_cam2_button.setStyleSheet("font-weight: bold;" if self.selected_camera_bad_pixel == 2 else "")
        self.bad_pixel_cam3_button.setStyleSheet("font-weight: bold;" if self.selected_camera_bad_pixel == 3 else "")

    def on_bad_pixel_enable(self):
        """Handle Bad Pixel Enable button."""
        logger.info(f"Advanced: Bad Pixel Enable for Camera {self.selected_camera_bad_pixel}")
        self.bad_pixel_enabled.emit(self.selected_camera_bad_pixel)

    def on_bad_pixel_disable(self):
        """Handle Bad Pixel Disable button."""
        logger.info(f"Advanced: Bad Pixel Disable for Camera {self.selected_camera_bad_pixel}")
        self.bad_pixel_disabled.emit(self.selected_camera_bad_pixel)

    def on_bad_pixel_calibrate(self):
        """Handle Bad Pixel Calibrate button."""
        logger.info(f"Advanced: Bad Pixel Calibrate for Camera {self.selected_camera_bad_pixel}")
        self.bad_pixel_calibrate.emit(self.selected_camera_bad_pixel)

    def on_bad_pixel_threshold_set(self):
        """Handle Bad Pixel Threshold Set button."""
        try:
            threshold = float(self.bad_pixel_threshold_input.text())
            if threshold > 0:
                logger.info(f"Advanced: Bad Pixel Threshold set to {threshold} for Camera {self.selected_camera_bad_pixel}")
                self.bad_pixel_threshold_changed.emit(self.selected_camera_bad_pixel, threshold)
            else:
                logger.warning("Advanced: Bad Pixel Threshold must be positive")
        except ValueError:
            logger.error("Advanced: Invalid Bad Pixel Threshold value")

    def on_bad_pixel_query(self):
        """Handle Bad Pixel Query Settings button."""
        logger.info(f"Advanced: Bad Pixel Query Settings for Camera {self.selected_camera_bad_pixel}")
        self.bad_pixel_query_requested.emit(self.selected_camera_bad_pixel)

    # ========================================================================
    # Video Source handlers
    # ========================================================================
    def on_video_source_camera_selected(self, camera: int):
        """Handle Video Source camera selection."""
        self.selected_camera_video_source = camera
        logger.info(f"Advanced: Video Source Camera {camera} selected")
        self.update_video_source_camera_buttons()

    def update_video_source_camera_buttons(self):
        """Update Video Source camera button styles to show selection."""
        self.video_source_cam1_button.setStyleSheet("font-weight: bold;" if self.selected_camera_video_source == 1 else "")
        self.video_source_cam2_button.setStyleSheet("font-weight: bold;" if self.selected_camera_video_source == 2 else "")
        self.video_source_cam3_button.setStyleSheet("font-weight: bold;" if self.selected_camera_video_source == 3 else "")

    def on_video_source_set(self):
        """Handle Video Source Set button."""
        source_id = self.video_source_id_input.text().strip()
        if source_id:
            logger.info(f"Advanced: Video Source set to '{source_id}' for Camera {self.selected_camera_video_source}")
            self.video_source_changed.emit(self.selected_camera_video_source, source_id)
        else:
            logger.warning("Advanced: Video Source ID is empty")

    def on_video_source_query(self):
        """Handle Video Source Query button."""
        logger.info(f"Advanced: Video Source Query for Camera {self.selected_camera_video_source}")
        self.video_source_query_requested.emit(self.selected_camera_video_source)

    # ========================================================================
    # WebRTC Overlay handlers
    # ========================================================================
    def on_webrtc_camera_selected(self, camera: int):
        """Handle WebRTC Overlay camera selection."""
        self.selected_camera_webrtc = camera
        logger.info(f"Advanced: WebRTC Overlay Camera {camera} selected")
        self.update_webrtc_camera_buttons()

    def update_webrtc_camera_buttons(self):
        """Update WebRTC Overlay camera button styles to show selection."""
        self.webrtc_cam1_button.setStyleSheet("font-weight: bold;" if self.selected_camera_webrtc == 1 else "")
        self.webrtc_cam2_button.setStyleSheet("font-weight: bold;" if self.selected_camera_webrtc == 2 else "")
        self.webrtc_cam3_button.setStyleSheet("font-weight: bold;" if self.selected_camera_webrtc == 3 else "")

    def on_webrtc_enable(self):
        """Handle WebRTC Overlay Enable button."""
        logger.info(f"Advanced: WebRTC Overlay Enable for Camera {self.selected_camera_webrtc}")
        self.webrtc_overlay_enabled.emit(self.selected_camera_webrtc)

    def on_webrtc_disable(self):
        """Handle WebRTC Overlay Disable button."""
        logger.info(f"Advanced: WebRTC Overlay Disable for Camera {self.selected_camera_webrtc}")
        self.webrtc_overlay_disabled.emit(self.selected_camera_webrtc)

    def on_webrtc_query(self):
        """Handle WebRTC Overlay Query Settings button."""
        logger.info(f"Advanced: WebRTC Overlay Query Settings for Camera {self.selected_camera_webrtc}")
        self.webrtc_overlay_query_requested.emit(self.selected_camera_webrtc)

    # ========================================================================
    # External UP Forwarding handlers
    # ========================================================================
    def on_external_up_enable(self):
        """Handle External UP Enable button."""
        logger.info("Advanced: External UP Forwarding Enable")
        self.external_up_enabled.emit()

    def on_external_up_disable(self):
        """Handle External UP Disable button."""
        logger.info("Advanced: External UP Forwarding Disable")
        self.external_up_disabled.emit()

    def on_external_up_port_set(self):
        """Handle External UP Port Set button."""
        try:
            port = int(self.external_up_port_input.text())
            if 1 <= port <= 65535:
                logger.info(f"Advanced: External UP Port set to {port}")
                self.external_up_port_changed.emit(port)
            else:
                logger.warning("Advanced: External UP Port must be 1-65535")
        except ValueError:
            logger.error("Advanced: Invalid External UP Port value")

    def on_external_up_address_set(self):
        """Handle External UP Address Set button."""
        address = self.external_up_address_input.text().strip()
        if address:
            logger.info(f"Advanced: External UP Address set to '{address}'")
            self.external_up_address_changed.emit(address)
        else:
            logger.warning("Advanced: External UP Address is empty")

    def on_external_up_query(self):
        """Handle External UP Query Settings button."""
        logger.info("Advanced: External UP Query Settings")
        self.external_up_query_requested.emit()

    # ========================================================================
    # Pelco-D Forwarding handlers
    # ========================================================================
    def on_pelco_d_enable(self):
        """Handle Pelco-D Enable button."""
        logger.info("Advanced: Pelco-D Forwarding Enable")
        self.pelco_d_enabled.emit()

    def on_pelco_d_disable(self):
        """Handle Pelco-D Disable button."""
        logger.info("Advanced: Pelco-D Forwarding Disable")
        self.pelco_d_disabled.emit()

    def on_pelco_d_port_set(self):
        """Handle Pelco-D Port Set button."""
        try:
            port = int(self.pelco_d_port_input.text())
            if 1 <= port <= 65535:
                logger.info(f"Advanced: Pelco-D Port set to {port}")
                self.pelco_d_port_changed.emit(port)
            else:
                logger.warning("Advanced: Pelco-D Port must be 1-65535")
        except ValueError:
            logger.error("Advanced: Invalid Pelco-D Port value")

    def on_pelco_d_address_set(self):
        """Handle Pelco-D Address Set button."""
        address = self.pelco_d_address_input.text().strip()
        if address:
            logger.info(f"Advanced: Pelco-D Address set to '{address}'")
            self.pelco_d_address_changed.emit(address)
        else:
            logger.warning("Advanced: Pelco-D Address is empty")

    def on_pelco_d_query(self):
        """Handle Pelco-D Query Settings button."""
        logger.info("Advanced: Pelco-D Query Settings")
        self.pelco_d_query_requested.emit()

    # ========================================================================
    # Video feed management methods
    # ========================================================================



