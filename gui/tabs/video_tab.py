"""
gui/tabs/video_tab.py
Video display tab - shows camera streams with dynamic layout based on availability.
LEFT: Scrollable settings panel (480px fixed width)
RIGHT: Video feeds (expanding)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QGridLayout, QPushButton, QScrollArea)
from PyQt6.QtCore import Qt
from utils.constants import load_config
from utils.logger import setup_logger

logger = setup_logger()


class VideoTab(QWidget):
    """
    Video display tab with left settings panel and right video feeds.
    Dynamically adjusts layout based on available cameras.
    """

    def __init__(self, video_manager=None):
        super().__init__()
        self.config = load_config()
        self.video_manager = video_manager
        self.video_placeholder = None  # Will hold the shared video display
        self.init_ui()

    def init_ui(self):
        """Initialize the UI with left settings panel and right video section."""
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Settings panel (fixed width with scrolling)
        left_widget = self.create_settings_section()

        # Right side: Video feeds (expands to fill space)
        right_widget = self.create_video_section()

        # Use simple horizontal layout - settings panel fixed width, video expands
        main_layout.addWidget(left_widget, 0)   # Settings panel fixed width (no stretch)
        main_layout.addWidget(right_widget, 1)  # Video expands (stretch factor 1)

        self.setLayout(main_layout)
        logger.info("Video tab initialized")

    def create_settings_section(self) -> QWidget:
        """Create left settings panel with scrolling."""
        widget = QWidget()
        widget.setFixedWidth(480)  # Fixed width like control tab

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Create scrollable content widget
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Video Settings group
        video_settings_group = QGroupBox("Video Settings")
        video_settings_layout = QVBoxLayout()

        info_label = QLabel("Video feeds are automatically discovered when connected to a payload.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 9pt; color: #888; padding: 10px;")
        video_settings_layout.addWidget(info_label)

        # Stream info
        stream_info_label = QLabel(
            "<b>Available Streams:</b><br>"
            "• Thermal Camera (Port 7031)<br>"
            "• Daylight Camera (Port 7031)<br>"
            "• SWIR Camera (Port 7031)"
        )
        stream_info_label.setWordWrap(True)
        stream_info_label.setStyleSheet("font-size: 9pt; padding: 10px;")
        video_settings_layout.addWidget(stream_info_label)

        video_settings_group.setLayout(video_settings_layout)
        layout.addWidget(video_settings_group)

        # Camera Status group
        camera_status_group = QGroupBox("Camera Status")
        camera_status_layout = QVBoxLayout()

        # Thermal camera status
        thermal_status_layout = QHBoxLayout()
        thermal_status_layout.addWidget(QLabel("<b>Thermal:</b>"))
        self.thermal_status_label = QLabel("Not Connected")
        self.thermal_status_label.setStyleSheet("color: #888;")
        thermal_status_layout.addWidget(self.thermal_status_label)
        thermal_status_layout.addStretch()
        camera_status_layout.addLayout(thermal_status_layout)

        # Daylight camera status
        daylight_status_layout = QHBoxLayout()
        daylight_status_layout.addWidget(QLabel("<b>Daylight:</b>"))
        self.daylight_status_label = QLabel("Not Connected")
        self.daylight_status_label.setStyleSheet("color: #888;")
        daylight_status_layout.addWidget(self.daylight_status_label)
        daylight_status_layout.addStretch()
        camera_status_layout.addLayout(daylight_status_layout)

        # SWIR camera status
        swir_status_layout = QHBoxLayout()
        swir_status_layout.addWidget(QLabel("<b>SWIR:</b>"))
        self.swir_status_label = QLabel("Not Connected")
        self.swir_status_label.setStyleSheet("color: #888;")
        swir_status_layout.addWidget(self.swir_status_label)
        swir_status_layout.addStretch()
        camera_status_layout.addLayout(swir_status_layout)

        camera_status_group.setLayout(camera_status_layout)
        layout.addWidget(camera_status_group)

        # Stream Controls group
        stream_controls_group = QGroupBox("Stream Controls")
        stream_controls_layout = QVBoxLayout()

        # Refresh button
        self.refresh_button = QPushButton("Refresh Streams")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 10pt;
                background-color: #2a82da;
                border: none;
                border-radius: 4px;
                color: white;
            }
            QPushButton:hover {
                background-color: #3a92ea;
            }
            QPushButton:pressed {
                background-color: #1a72ca;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_streams)
        stream_controls_layout.addWidget(self.refresh_button)

        # Stop All button
        self.stop_all_button = QPushButton("Stop All Streams")
        self.stop_all_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-size: 10pt;
                background-color: #d32f2f;
                border: none;
                border-radius: 4px;
                color: white;
            }
            QPushButton:hover {
                background-color: #e33f3f;
            }
            QPushButton:pressed {
                background-color: #c31f1f;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.stop_all_button.clicked.connect(self.stop_all_video_streams)
        stream_controls_layout.addWidget(self.stop_all_button)

        stream_controls_group.setLayout(stream_controls_layout)
        layout.addWidget(stream_controls_group)

        layout.addStretch()
        content_widget.setLayout(layout)
        scroll.setWidget(content_widget)

        # Wrap scroll area in main widget layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        widget.setLayout(main_layout)

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


    def update_status_labels(self):
        """Update camera status labels based on availability."""
        # Thermal status
        if self.camera_availability.get('thermal', False):
            self.thermal_status_label.setText("Connected")
            self.thermal_status_label.setStyleSheet("color: #44ff44;")
        else:
            self.thermal_status_label.setText("Not Connected")
            self.thermal_status_label.setStyleSheet("color: #888;")

        # Daylight status
        if self.camera_availability.get('daylight', False):
            self.daylight_status_label.setText("Connected")
            self.daylight_status_label.setStyleSheet("color: #44ff44;")
        else:
            self.daylight_status_label.setText("Not Connected")
            self.daylight_status_label.setStyleSheet("color: #888;")

        # SWIR status
        if self.camera_availability.get('swir', False):
            self.swir_status_label.setText("Connected")
            self.swir_status_label.setStyleSheet("color: #44ff44;")
        else:
            self.swir_status_label.setText("Not Connected")
            self.swir_status_label.setStyleSheet("color: #888;")


    def refresh_streams(self):
        """Refresh video streams by re-reading current IP from config."""
        logger.info("Refreshing video streams...")
        # This would typically be called by the main window with the current IP
        # For now, just log the action
        logger.info("Refresh streams button clicked - requires IP from main window")


