"""
gui/tabs/sub_payloads_tab.py
Sub Payloads tab - Phase 4A hardware peripherals.
Includes Laser Rangefinder, Speaker, G5 Laser Illuminator, PeakBeam Illuminator,
and Companion Board.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QGridLayout, QPushButton, QLineEdit,
                             QScrollArea, QTextEdit, QComboBox, QSlider)
from PyQt6.QtCore import pyqtSignal, Qt
from utils.constants import load_config
from utils.logger import setup_logger

logger = setup_logger()


class SubPayloadsTab(QWidget):
    """
    Sub Payloads tab for Phase 4A hardware peripherals.
    Contains 5 groups: Laser Rangefinder, Speaker, G5 Laser Illuminator,
    PeakBeam Illuminator, and Companion Board.
    """

    # ========================================================================
    # Laser Rangefinder (LRF) signals (4)
    # ========================================================================
    lrf_fire_requested = pyqtSignal()
    lrf_mode_changed = pyqtSignal(str)  # mode
    lrf_query_range_requested = pyqtSignal()
    lrf_query_settings_requested = pyqtSignal()

    # ========================================================================
    # Speaker signals (4)
    # ========================================================================
    speaker_play_requested = pyqtSignal(str)  # clip_name
    speaker_stop_requested = pyqtSignal()
    speaker_volume_changed = pyqtSignal(int)  # volume 0-100
    speaker_query_requested = pyqtSignal()

    # ========================================================================
    # G5 Laser Illuminator signals (4)
    # ========================================================================
    g5_laser_enabled = pyqtSignal()
    g5_laser_disabled = pyqtSignal()
    g5_laser_intensity_changed = pyqtSignal(int)  # intensity 0-100
    g5_laser_query_requested = pyqtSignal()

    # ========================================================================
    # PeakBeam Illuminator signals (5)
    # ========================================================================
    peakbeam_enabled = pyqtSignal()
    peakbeam_disabled = pyqtSignal()
    peakbeam_intensity_changed = pyqtSignal(int)  # intensity 0-100
    peakbeam_mode_changed = pyqtSignal(str)  # mode
    peakbeam_query_requested = pyqtSignal()

    # ========================================================================
    # Companion Board signals (5)
    # ========================================================================
    companion_command_sent = pyqtSignal(str)  # command
    companion_enabled = pyqtSignal()
    companion_disabled = pyqtSignal()
    companion_reset_requested = pyqtSignal()
    companion_query_requested = pyqtSignal()

    def __init__(self, video_manager=None):
        super().__init__()
        self.config = load_config()
        self.video_manager = video_manager
        self.video_placeholder = None  # Will hold the shared video display
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """Initialize the Sub Payloads tab UI - LEFT settings, RIGHT video feeds."""
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Settings (fixed width 480px, scrollable)
        left_widget = self.create_settings_section()

        # Right side: Video streams (expands to fill space)
        right_widget = self.create_video_section()

        # Use simple horizontal layout - settings panel has fixed width, video expands
        main_layout.addWidget(left_widget, 0)   # Settings panel fixed width (no stretch)
        main_layout.addWidget(right_widget, 1)  # Video expands (stretch factor 1)

        self.setLayout(main_layout)
        logger.info("Sub Payloads tab initialized")

    def create_settings_section(self) -> QWidget:
        """Create settings section with scrollable container."""
        widget = QWidget()
        widget.setFixedWidth(480)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Create container widget
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setSpacing(10)
        container_layout.setContentsMargins(10, 10, 10, 10)

        # Group 1: Laser Rangefinder
        lrf_group = self.create_laser_rangefinder_group()
        container_layout.addWidget(lrf_group)

        # Group 2: Speaker
        speaker_group = self.create_speaker_group()
        container_layout.addWidget(speaker_group)

        # Group 3: G5 Laser Illuminator
        g5_group = self.create_g5_laser_group()
        container_layout.addWidget(g5_group)

        # Group 4: PeakBeam Illuminator
        peakbeam_group = self.create_peakbeam_group()
        container_layout.addWidget(peakbeam_group)

        # Group 5: Companion Board
        companion_group = self.create_companion_board_group()
        container_layout.addWidget(companion_group)

        container_layout.addStretch()
        container.setLayout(container_layout)

        # Set container in scroll area
        scroll.setWidget(container)

        # Add scroll to widget layout
        layout.addWidget(scroll)
        widget.setLayout(layout)
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

    def create_laser_rangefinder_group(self) -> QGroupBox:
        """Create Laser Rangefinder (LRF) group."""
        group = QGroupBox("Laser Rangefinder (LRF)")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Fire/Measure button
        self.lrf_fire_button = QPushButton("Fire/Measure")
        layout.addWidget(self.lrf_fire_button, 0, 0, 1, 3)

        # Last Range
        layout.addWidget(QLabel("Last Range:"), 1, 0)
        self.lrf_last_range_display = QLineEdit()
        self.lrf_last_range_display.setReadOnly(True)
        self.lrf_last_range_display.setPlaceholderText("N/A")
        layout.addWidget(self.lrf_last_range_display, 1, 1, 1, 2)

        # Query Range
        self.lrf_query_range_button = QPushButton("Query Range")
        layout.addWidget(self.lrf_query_range_button, 2, 0, 1, 3)

        # Mode
        layout.addWidget(QLabel("Mode:"), 3, 0)
        self.lrf_mode_combo = QComboBox()
        self.lrf_mode_combo.addItems(["Single", "Continuous", "Off"])
        layout.addWidget(self.lrf_mode_combo, 3, 1)
        self.lrf_mode_button = QPushButton("Set Mode")
        layout.addWidget(self.lrf_mode_button, 3, 2)

        # Query Settings
        self.lrf_query_settings_button = QPushButton("Query Settings")
        layout.addWidget(self.lrf_query_settings_button, 4, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_speaker_group(self) -> QGroupBox:
        """Create Speaker group."""
        group = QGroupBox("Speaker")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Clip Name
        layout.addWidget(QLabel("Clip Name:"), 0, 0)
        self.speaker_clip_input = QLineEdit()
        self.speaker_clip_input.setPlaceholderText("Enter clip name")
        layout.addWidget(self.speaker_clip_input, 0, 1)
        self.speaker_play_button = QPushButton("Play")
        layout.addWidget(self.speaker_play_button, 0, 2)

        # Stop
        self.speaker_stop_button = QPushButton("Stop")
        layout.addWidget(self.speaker_stop_button, 1, 0, 1, 3)

        # Volume
        layout.addWidget(QLabel("Volume:"), 2, 0)
        volume_layout = QHBoxLayout()
        self.speaker_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.speaker_volume_slider.setMinimum(0)
        self.speaker_volume_slider.setMaximum(100)
        self.speaker_volume_slider.setValue(50)
        volume_layout.addWidget(self.speaker_volume_slider)
        self.speaker_volume_label = QLabel("50")
        self.speaker_volume_label.setFixedWidth(30)
        volume_layout.addWidget(self.speaker_volume_label)
        layout.addLayout(volume_layout, 2, 1)
        self.speaker_volume_button = QPushButton("Set")
        layout.addWidget(self.speaker_volume_button, 2, 2)

        # Query Status
        self.speaker_query_button = QPushButton("Query Status")
        layout.addWidget(self.speaker_query_button, 3, 0, 1, 3)

        # Status Display
        layout.addWidget(QLabel("Status:"), 4, 0, 1, 3)
        self.speaker_status_display = QLabel("N/A")
        self.speaker_status_display.setWordWrap(True)
        self.speaker_status_display.setStyleSheet("QLabel { border: 1px solid #ccc; padding: 5px; background-color: #f9f9f9; }")
        layout.addWidget(self.speaker_status_display, 5, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_g5_laser_group(self) -> QGroupBox:
        """Create G5 Laser Illuminator group."""
        group = QGroupBox("G5 Laser Illuminator")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Enable/Disable
        self.g5_enable_button = QPushButton("Enable")
        layout.addWidget(self.g5_enable_button, 0, 0)
        self.g5_disable_button = QPushButton("Disable")
        layout.addWidget(self.g5_disable_button, 0, 1, 1, 2)

        # Intensity
        layout.addWidget(QLabel("Intensity:"), 1, 0)
        intensity_layout = QHBoxLayout()
        self.g5_intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.g5_intensity_slider.setMinimum(0)
        self.g5_intensity_slider.setMaximum(100)
        self.g5_intensity_slider.setValue(50)
        intensity_layout.addWidget(self.g5_intensity_slider)
        self.g5_intensity_label = QLabel("50")
        self.g5_intensity_label.setFixedWidth(30)
        intensity_layout.addWidget(self.g5_intensity_label)
        layout.addLayout(intensity_layout, 1, 1)
        self.g5_intensity_button = QPushButton("Set")
        layout.addWidget(self.g5_intensity_button, 1, 2)

        # Query Settings
        self.g5_query_button = QPushButton("Query Settings")
        layout.addWidget(self.g5_query_button, 2, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_peakbeam_group(self) -> QGroupBox:
        """Create PeakBeam Illuminator group."""
        group = QGroupBox("PeakBeam Illuminator")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Enable/Disable
        self.peakbeam_enable_button = QPushButton("Enable")
        layout.addWidget(self.peakbeam_enable_button, 0, 0)
        self.peakbeam_disable_button = QPushButton("Disable")
        layout.addWidget(self.peakbeam_disable_button, 0, 1, 1, 2)

        # Intensity
        layout.addWidget(QLabel("Intensity:"), 1, 0)
        intensity_layout = QHBoxLayout()
        self.peakbeam_intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.peakbeam_intensity_slider.setMinimum(0)
        self.peakbeam_intensity_slider.setMaximum(100)
        self.peakbeam_intensity_slider.setValue(50)
        intensity_layout.addWidget(self.peakbeam_intensity_slider)
        self.peakbeam_intensity_label = QLabel("50")
        self.peakbeam_intensity_label.setFixedWidth(30)
        intensity_layout.addWidget(self.peakbeam_intensity_label)
        layout.addLayout(intensity_layout, 1, 1)
        self.peakbeam_intensity_button = QPushButton("Set")
        layout.addWidget(self.peakbeam_intensity_button, 1, 2)

        # Mode
        layout.addWidget(QLabel("Mode:"), 2, 0)
        self.peakbeam_mode_combo = QComboBox()
        self.peakbeam_mode_combo.addItems(["Continuous", "Strobe", "Pulse"])
        layout.addWidget(self.peakbeam_mode_combo, 2, 1)
        self.peakbeam_mode_button = QPushButton("Set Mode")
        layout.addWidget(self.peakbeam_mode_button, 2, 2)

        # Query Settings
        self.peakbeam_query_button = QPushButton("Query Settings")
        layout.addWidget(self.peakbeam_query_button, 3, 0, 1, 3)

        group.setLayout(layout)
        return group

    def create_companion_board_group(self) -> QGroupBox:
        """Create Companion Board group."""
        group = QGroupBox("Companion Board")
        layout = QGridLayout()
        layout.setSpacing(8)

        # Command Input
        layout.addWidget(QLabel("Command:"), 0, 0)
        self.companion_command_input = QLineEdit()
        self.companion_command_input.setPlaceholderText("Enter command")
        layout.addWidget(self.companion_command_input, 0, 1)
        self.companion_send_button = QPushButton("Send")
        layout.addWidget(self.companion_send_button, 0, 2)

        # Enable/Disable
        self.companion_enable_button = QPushButton("Enable")
        layout.addWidget(self.companion_enable_button, 1, 0)
        self.companion_disable_button = QPushButton("Disable")
        layout.addWidget(self.companion_disable_button, 1, 1, 1, 2)

        # Reset
        self.companion_reset_button = QPushButton("Reset")
        layout.addWidget(self.companion_reset_button, 2, 0, 1, 3)

        # Query Status
        self.companion_query_button = QPushButton("Query Status")
        layout.addWidget(self.companion_query_button, 3, 0, 1, 3)

        # Status Display
        layout.addWidget(QLabel("Status:"), 4, 0, 1, 3)
        self.companion_status_display = QTextEdit()
        self.companion_status_display.setReadOnly(True)
        self.companion_status_display.setFixedHeight(100)
        layout.addWidget(self.companion_status_display, 5, 0, 1, 3)

        # Clear Status
        self.companion_clear_button = QPushButton("Clear Status")
        layout.addWidget(self.companion_clear_button, 6, 0, 1, 3)

        group.setLayout(layout)
        return group

    def connect_signals(self):
        """Connect all button and slider signals to their respective handlers."""
        # Laser Rangefinder
        self.lrf_fire_button.clicked.connect(self.on_lrf_fire)
        self.lrf_query_range_button.clicked.connect(self.on_lrf_query_range)
        self.lrf_mode_button.clicked.connect(self.on_lrf_mode_set)
        self.lrf_query_settings_button.clicked.connect(self.on_lrf_query_settings)

        # Speaker
        self.speaker_play_button.clicked.connect(self.on_speaker_play)
        self.speaker_stop_button.clicked.connect(self.on_speaker_stop)
        self.speaker_volume_slider.valueChanged.connect(self.on_speaker_volume_slider_changed)
        self.speaker_volume_button.clicked.connect(self.on_speaker_volume_set)
        self.speaker_query_button.clicked.connect(self.on_speaker_query)

        # G5 Laser Illuminator
        self.g5_enable_button.clicked.connect(self.on_g5_enable)
        self.g5_disable_button.clicked.connect(self.on_g5_disable)
        self.g5_intensity_slider.valueChanged.connect(self.on_g5_intensity_slider_changed)
        self.g5_intensity_button.clicked.connect(self.on_g5_intensity_set)
        self.g5_query_button.clicked.connect(self.on_g5_query)

        # PeakBeam Illuminator
        self.peakbeam_enable_button.clicked.connect(self.on_peakbeam_enable)
        self.peakbeam_disable_button.clicked.connect(self.on_peakbeam_disable)
        self.peakbeam_intensity_slider.valueChanged.connect(self.on_peakbeam_intensity_slider_changed)
        self.peakbeam_intensity_button.clicked.connect(self.on_peakbeam_intensity_set)
        self.peakbeam_mode_button.clicked.connect(self.on_peakbeam_mode_set)
        self.peakbeam_query_button.clicked.connect(self.on_peakbeam_query)

        # Companion Board
        self.companion_send_button.clicked.connect(self.on_companion_send)
        self.companion_enable_button.clicked.connect(self.on_companion_enable)
        self.companion_disable_button.clicked.connect(self.on_companion_disable)
        self.companion_reset_button.clicked.connect(self.on_companion_reset)
        self.companion_query_button.clicked.connect(self.on_companion_query)
        self.companion_clear_button.clicked.connect(self.on_companion_clear)

    # ========================================================================
    # Laser Rangefinder handlers
    # ========================================================================
    def on_lrf_fire(self):
        """Handle LRF Fire/Measure button."""
        logger.info("SubPayloads: LRF Fire/Measure requested")
        self.lrf_fire_requested.emit()

    def on_lrf_query_range(self):
        """Handle LRF Query Range button."""
        logger.info("SubPayloads: LRF Query Range requested")
        self.lrf_query_range_requested.emit()

    def on_lrf_mode_set(self):
        """Handle LRF Set Mode button."""
        mode = self.lrf_mode_combo.currentText()
        logger.info(f"SubPayloads: LRF Mode set to '{mode}'")
        self.lrf_mode_changed.emit(mode)

    def on_lrf_query_settings(self):
        """Handle LRF Query Settings button."""
        logger.info("SubPayloads: LRF Query Settings requested")
        self.lrf_query_settings_requested.emit()

    def set_lrf_range(self, range_meters: float):
        """Set the LRF range display (for external updates)."""
        self.lrf_last_range_display.setText(f"{range_meters:.2f} m")
        logger.debug(f"SubPayloads: LRF Range updated to {range_meters:.2f} m")

    # ========================================================================
    # Speaker handlers
    # ========================================================================
    def on_speaker_play(self):
        """Handle Speaker Play button."""
        clip_name = self.speaker_clip_input.text().strip()
        if clip_name:
            logger.info(f"SubPayloads: Speaker Play clip '{clip_name}' requested")
            self.speaker_play_requested.emit(clip_name)
        else:
            logger.warning("SubPayloads: Clip name is empty")

    def on_speaker_stop(self):
        """Handle Speaker Stop button."""
        logger.info("SubPayloads: Speaker Stop requested")
        self.speaker_stop_requested.emit()

    def on_speaker_volume_slider_changed(self, value: int):
        """Handle Speaker volume slider value change (updates label only)."""
        self.speaker_volume_label.setText(str(value))

    def on_speaker_volume_set(self):
        """Handle Speaker Set Volume button."""
        volume = self.speaker_volume_slider.value()
        logger.info(f"SubPayloads: Speaker Volume set to {volume}")
        self.speaker_volume_changed.emit(volume)

    def on_speaker_query(self):
        """Handle Speaker Query Status button."""
        logger.info("SubPayloads: Speaker Query Status requested")
        self.speaker_query_requested.emit()

    def set_speaker_status(self, status: str):
        """Set the Speaker status display (for external updates)."""
        self.speaker_status_display.setText(status)
        logger.debug(f"SubPayloads: Speaker Status updated: {status}")

    # ========================================================================
    # G5 Laser Illuminator handlers
    # ========================================================================
    def on_g5_enable(self):
        """Handle G5 Laser Enable button."""
        logger.info("SubPayloads: G5 Laser Illuminator Enable")
        self.g5_laser_enabled.emit()

    def on_g5_disable(self):
        """Handle G5 Laser Disable button."""
        logger.info("SubPayloads: G5 Laser Illuminator Disable")
        self.g5_laser_disabled.emit()

    def on_g5_intensity_slider_changed(self, value: int):
        """Handle G5 Laser intensity slider value change (updates label only)."""
        self.g5_intensity_label.setText(str(value))

    def on_g5_intensity_set(self):
        """Handle G5 Laser Set Intensity button."""
        intensity = self.g5_intensity_slider.value()
        logger.info(f"SubPayloads: G5 Laser Intensity set to {intensity}")
        self.g5_laser_intensity_changed.emit(intensity)

    def on_g5_query(self):
        """Handle G5 Laser Query Settings button."""
        logger.info("SubPayloads: G5 Laser Query Settings requested")
        self.g5_laser_query_requested.emit()

    # ========================================================================
    # PeakBeam Illuminator handlers
    # ========================================================================
    def on_peakbeam_enable(self):
        """Handle PeakBeam Enable button."""
        logger.info("SubPayloads: PeakBeam Illuminator Enable")
        self.peakbeam_enabled.emit()

    def on_peakbeam_disable(self):
        """Handle PeakBeam Disable button."""
        logger.info("SubPayloads: PeakBeam Illuminator Disable")
        self.peakbeam_disabled.emit()

    def on_peakbeam_intensity_slider_changed(self, value: int):
        """Handle PeakBeam intensity slider value change (updates label only)."""
        self.peakbeam_intensity_label.setText(str(value))

    def on_peakbeam_intensity_set(self):
        """Handle PeakBeam Set Intensity button."""
        intensity = self.peakbeam_intensity_slider.value()
        logger.info(f"SubPayloads: PeakBeam Intensity set to {intensity}")
        self.peakbeam_intensity_changed.emit(intensity)

    def on_peakbeam_mode_set(self):
        """Handle PeakBeam Set Mode button."""
        mode = self.peakbeam_mode_combo.currentText()
        logger.info(f"SubPayloads: PeakBeam Mode set to '{mode}'")
        self.peakbeam_mode_changed.emit(mode)

    def on_peakbeam_query(self):
        """Handle PeakBeam Query Settings button."""
        logger.info("SubPayloads: PeakBeam Query Settings requested")
        self.peakbeam_query_requested.emit()

    # ========================================================================
    # Companion Board handlers
    # ========================================================================
    def on_companion_send(self):
        """Handle Companion Board Send Command button."""
        command = self.companion_command_input.text().strip()
        if command:
            logger.info(f"SubPayloads: Companion Board Command '{command}' sent")
            self.companion_command_sent.emit(command)
        else:
            logger.warning("SubPayloads: Companion Board command is empty")

    def on_companion_enable(self):
        """Handle Companion Board Enable button."""
        logger.info("SubPayloads: Companion Board Enable")
        self.companion_enabled.emit()

    def on_companion_disable(self):
        """Handle Companion Board Disable button."""
        logger.info("SubPayloads: Companion Board Disable")
        self.companion_disabled.emit()

    def on_companion_reset(self):
        """Handle Companion Board Reset button."""
        logger.info("SubPayloads: Companion Board Reset requested")
        self.companion_reset_requested.emit()

    def on_companion_query(self):
        """Handle Companion Board Query Status button."""
        logger.info("SubPayloads: Companion Board Query Status requested")
        self.companion_query_requested.emit()

    def on_companion_clear(self):
        """Handle Companion Board Clear Status button."""
        logger.info("SubPayloads: Companion Board Clear Status")
        self.companion_status_display.clear()

    def append_companion_status(self, text: str):
        """Append text to Companion Board status display (for external updates)."""
        self.companion_status_display.append(text)
        logger.debug(f"SubPayloads: Companion Board Status appended: {text}")

    # ========================================================================
    # Video management methods
    # ========================================================================



