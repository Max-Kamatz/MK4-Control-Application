"""
gui/tabs/rtsp_tab.py
RTSP Tab - All video streaming configuration and protocol management.
Contains 12 groups with ~45 controls for comprehensive video stream setup.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QGridLayout, QPushButton, QLineEdit,
                             QComboBox, QSlider, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from utils.constants import load_config
from utils.logger import setup_logger

logger = setup_logger()


class RTSPTab(QWidget):
    """
    RTSP Tab for video streaming configuration.
    Manages RTSP, RTP, RTMP, HLS, and SRT streaming protocols across 3 cameras and 2 streams each.
    Layout: LEFT side with scrollable settings (480px), RIGHT side with video feeds (expanding).
    """

    # Group 1: Target Selection signals
    target_changed = pyqtSignal(int, int)  # camera (1-3), stream (1-2)

    # Group 2: Stream Control signals
    stream_enable_pressed = pyqtSignal(int, int)  # camera, stream
    stream_disable_pressed = pyqtSignal(int, int)  # camera, stream
    stream_restart_pressed = pyqtSignal(int, int)  # camera, stream

    # Group 3: RTSP Settings signals
    rtsp_suffix_changed = pyqtSignal(int, int, str)  # camera, stream, suffix
    rtsp_port_changed = pyqtSignal(int)  # port (applies to all)
    rtsp_multicast_ip_changed = pyqtSignal(int, int, str)  # camera, stream, ip
    rtsp_multicast_port_changed = pyqtSignal(int, int, int)  # camera, stream, port
    rtsp_user_changed = pyqtSignal(int, int, str)  # camera, stream, user
    rtsp_password_changed = pyqtSignal(int, int, str)  # camera, stream, password

    # Group 4: Video Encoding signals
    resolution_changed = pyqtSignal(int, int, str)  # camera, stream, resolution
    codec_changed = pyqtSignal(int, int, str)  # camera, stream, codec
    h264_profile_changed = pyqtSignal(int, int, str)  # camera, stream, profile
    jpeg_quality_changed = pyqtSignal(int, int, int)  # camera, stream, quality (1-100)

    # Group 5: Bitrate Settings signals
    bitrate_changed = pyqtSignal(int, int, int)  # camera, stream, bitrate (kbps)
    bitrate_mode_changed = pyqtSignal(int, int, str)  # camera, stream, mode (CBR/VBR)
    min_bitrate_changed = pyqtSignal(int, int, int)  # camera, stream, min_bitrate
    max_bitrate_changed = pyqtSignal(int, int, int)  # camera, stream, max_bitrate

    # Group 6: Frame Settings signals
    fps_changed = pyqtSignal(int, int, int)  # camera, stream, fps (1-60)
    gop_changed = pyqtSignal(int, int, int)  # camera, stream, gop

    # Group 7: Video Processing signals
    fit_mode_changed = pyqtSignal(int, int, str)  # camera, stream, mode (Fit/Crop)
    overlay_mode_changed = pyqtSignal(int, int, bool)  # camera, stream, enable
    metadata_mode_changed = pyqtSignal(int, int, bool)  # camera, stream, enable
    metadata_suffix_changed = pyqtSignal(int, int, str)  # camera, stream, suffix

    # Group 8: RTP Direct Streaming signals
    rtp_mode_changed = pyqtSignal(int, int, bool)  # camera, stream, enable
    rtp_port_changed = pyqtSignal(int, int, int)  # camera, stream, port
    rtp_dest_ip_changed = pyqtSignal(int, int, str)  # camera, stream, ip

    # Group 9: RTMP Server signals
    rtmp_mode_changed = pyqtSignal(int, int, bool)  # camera, stream, enable
    rtmp_port_changed = pyqtSignal(int, int, int)  # camera, stream, port

    # Group 10: HLS Server signals
    hls_mode_changed = pyqtSignal(int, int, bool)  # camera, stream, enable
    hls_port_changed = pyqtSignal(int, int, int)  # camera, stream, port

    # Group 11: SRT Server signals
    srt_mode_changed = pyqtSignal(int, int, bool)  # camera, stream, enable
    srt_port_changed = pyqtSignal(int, int, int)  # camera, stream, port

    # Group 12: Advanced Settings signals
    udp_payload_changed = pyqtSignal(int, int, int)  # camera, stream, size (100-65535)
    query_video_settings_pressed = pyqtSignal(int, int)  # camera, stream

    def __init__(self, video_manager=None):
        super().__init__()
        self.config = load_config()
        self.current_camera = 1  # Default: Camera 1
        self.current_stream = 1  # Default: Stream 1
        self.video_manager = video_manager
        self.video_placeholder = None  # Will hold the shared video display
        self.init_ui()
        self.connect_signals()
        logger.info("RTSP tab initialized")

    def init_ui(self):
        """Initialize the RTSP tab UI with LEFT scrollable settings, RIGHT video feeds."""
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Scrollable settings panel (fixed width)
        left_widget = self.create_settings_section()

        # Right side: Video feeds (expands to fill space)
        right_widget = self.create_video_section()

        # Add to layout: settings fixed width, video expands
        main_layout.addWidget(left_widget, 0)   # Settings fixed width (no stretch)
        main_layout.addWidget(right_widget, 1)  # Video expands (stretch factor 1)

        self.setLayout(main_layout)

    def create_settings_section(self) -> QWidget:
        """Create scrollable settings section (left side, fixed 480px width)."""
        widget = QWidget()
        widget.setFixedWidth(480)
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create scroll area for all settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container widget for scrollable content
        container = QWidget()
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)
        settings_layout.setContentsMargins(10, 10, 10, 10)

        # Group 1: Target Selection
        settings_layout.addWidget(self.create_target_selection_group())

        # Group 2: Stream Control
        settings_layout.addWidget(self.create_stream_control_group())

        # Group 3: RTSP Settings
        settings_layout.addWidget(self.create_rtsp_settings_group())

        # Group 4: Video Encoding
        settings_layout.addWidget(self.create_video_encoding_group())

        # Group 5: Bitrate Settings
        settings_layout.addWidget(self.create_bitrate_settings_group())

        # Group 6: Frame Settings
        settings_layout.addWidget(self.create_frame_settings_group())

        # Group 7: Video Processing
        settings_layout.addWidget(self.create_video_processing_group())

        # Group 8: RTP Direct Streaming
        settings_layout.addWidget(self.create_rtp_streaming_group())

        # Group 9: RTMP Server
        settings_layout.addWidget(self.create_rtmp_server_group())

        # Group 10: HLS Server
        settings_layout.addWidget(self.create_hls_server_group())

        # Group 11: SRT Server
        settings_layout.addWidget(self.create_srt_server_group())

        # Group 12: Advanced Settings
        settings_layout.addWidget(self.create_advanced_settings_group())

        settings_layout.addStretch()
        container.setLayout(settings_layout)
        scroll_area.setWidget(container)

        layout.addWidget(scroll_area)
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

    def create_target_selection_group(self) -> QGroupBox:
        """Group 1: Target Selection - Select camera and stream."""
        group = QGroupBox("Target Selection")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("Camera:"), 0, 0)
        self.camera_selector = QComboBox()
        self.camera_selector.addItems(["Camera 1 (Daylight)", "Camera 2 (Thermal)", "Camera 3 (SWIR)"])
        self.camera_selector.setCurrentIndex(0)
        layout.addWidget(self.camera_selector, 0, 1, 1, 2)

        layout.addWidget(QLabel("Stream:"), 1, 0)
        self.stream_selector = QComboBox()
        self.stream_selector.addItems(["Stream 1", "Stream 2"])
        self.stream_selector.setCurrentIndex(0)
        layout.addWidget(self.stream_selector, 1, 1, 1, 2)

        group.setLayout(layout)
        return group

    def create_stream_control_group(self) -> QGroupBox:
        """Group 2: Stream Control - Enable/Disable/Restart stream."""
        group = QGroupBox("Stream Control")
        layout = QGridLayout()
        layout.setSpacing(8)

        self.stream_enable_button = QPushButton("Enable Stream")
        self.stream_enable_button.setStyleSheet("background-color: #4CAF50; color: white;")
        layout.addWidget(self.stream_enable_button, 0, 0)

        self.stream_disable_button = QPushButton("Disable Stream")
        self.stream_disable_button.setStyleSheet("background-color: #f44336; color: white;")
        layout.addWidget(self.stream_disable_button, 0, 1)

        self.stream_restart_button = QPushButton("Restart Stream")
        self.stream_restart_button.setStyleSheet("background-color: #FF9800; color: white;")
        layout.addWidget(self.stream_restart_button, 0, 2)

        group.setLayout(layout)
        return group

    def create_rtsp_settings_group(self) -> QGroupBox:
        """Group 3: RTSP Settings - RTSP configuration."""
        group = QGroupBox("RTSP Settings")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("RTSP Suffix:"), 0, 0)
        self.rtsp_suffix_input = QLineEdit()
        self.rtsp_suffix_input.setPlaceholderText("e.g., live")
        layout.addWidget(self.rtsp_suffix_input, 0, 1)
        self.rtsp_suffix_button = QPushButton("Set")
        layout.addWidget(self.rtsp_suffix_button, 0, 2)

        layout.addWidget(QLabel("RTSP Port (all):"), 1, 0)
        self.rtsp_port_input = QLineEdit()
        self.rtsp_port_input.setPlaceholderText("Default: 7031")
        layout.addWidget(self.rtsp_port_input, 1, 1)
        self.rtsp_port_button = QPushButton("Set")
        layout.addWidget(self.rtsp_port_button, 1, 2)

        layout.addWidget(QLabel("Multicast IP:"), 2, 0)
        self.rtsp_multicast_ip_input = QLineEdit()
        self.rtsp_multicast_ip_input.setPlaceholderText("e.g., 239.0.0.1")
        layout.addWidget(self.rtsp_multicast_ip_input, 2, 1)
        self.rtsp_multicast_ip_button = QPushButton("Set")
        layout.addWidget(self.rtsp_multicast_ip_button, 2, 2)

        layout.addWidget(QLabel("Multicast Port:"), 3, 0)
        self.rtsp_multicast_port_input = QLineEdit()
        self.rtsp_multicast_port_input.setPlaceholderText("Port number")
        layout.addWidget(self.rtsp_multicast_port_input, 3, 1)
        self.rtsp_multicast_port_button = QPushButton("Set")
        layout.addWidget(self.rtsp_multicast_port_button, 3, 2)

        layout.addWidget(QLabel("RTSP User:"), 4, 0)
        self.rtsp_user_input = QLineEdit()
        self.rtsp_user_input.setPlaceholderText("Username")
        layout.addWidget(self.rtsp_user_input, 4, 1)
        self.rtsp_user_button = QPushButton("Set")
        layout.addWidget(self.rtsp_user_button, 4, 2)

        layout.addWidget(QLabel("RTSP Password:"), 5, 0)
        self.rtsp_password_input = QLineEdit()
        self.rtsp_password_input.setPlaceholderText("Password")
        self.rtsp_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.rtsp_password_input, 5, 1)
        self.rtsp_password_button = QPushButton("Set")
        layout.addWidget(self.rtsp_password_button, 5, 2)

        group.setLayout(layout)
        return group

    def create_video_encoding_group(self) -> QGroupBox:
        """Group 4: Video Encoding - Resolution, codec, profile, quality."""
        group = QGroupBox("Video Encoding")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("Resolution:"), 0, 0)
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1920x1080", "1280x720", "640x480", "Custom"])
        layout.addWidget(self.resolution_combo, 0, 1)
        self.resolution_custom_input = QLineEdit()
        self.resolution_custom_input.setPlaceholderText("WxH (e.g., 1024x768)")
        self.resolution_custom_input.setEnabled(False)
        layout.addWidget(self.resolution_custom_input, 0, 2)

        layout.addWidget(QLabel("Codec:"), 1, 0)
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["H264", "H265", "JPEG"])
        layout.addWidget(self.codec_combo, 1, 1, 1, 2)

        layout.addWidget(QLabel("H264 Profile:"), 2, 0)
        self.h264_profile_combo = QComboBox()
        self.h264_profile_combo.addItems(["Baseline", "Main", "High"])
        layout.addWidget(self.h264_profile_combo, 2, 1, 1, 2)

        layout.addWidget(QLabel("JPEG Quality:"), 3, 0)
        self.jpeg_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.jpeg_quality_slider.setMinimum(1)
        self.jpeg_quality_slider.setMaximum(100)
        self.jpeg_quality_slider.setValue(75)
        self.jpeg_quality_slider.setEnabled(False)
        layout.addWidget(self.jpeg_quality_slider, 3, 1)
        self.jpeg_quality_label = QLabel("75")
        layout.addWidget(self.jpeg_quality_label, 3, 2)

        group.setLayout(layout)
        return group

    def create_bitrate_settings_group(self) -> QGroupBox:
        """Group 5: Bitrate Settings - Bitrate configuration."""
        group = QGroupBox("Bitrate Settings")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("Bitrate (kbps):"), 0, 0)
        self.bitrate_input = QLineEdit()
        self.bitrate_input.setPlaceholderText("e.g., 4000")
        layout.addWidget(self.bitrate_input, 0, 1)
        self.bitrate_button = QPushButton("Set")
        layout.addWidget(self.bitrate_button, 0, 2)

        layout.addWidget(QLabel("Bitrate Mode:"), 1, 0)
        self.bitrate_cbr_button = QPushButton("CBR")
        self.bitrate_cbr_button.setCheckable(True)
        self.bitrate_cbr_button.setChecked(True)
        layout.addWidget(self.bitrate_cbr_button, 1, 1)
        self.bitrate_vbr_button = QPushButton("VBR")
        self.bitrate_vbr_button.setCheckable(True)
        layout.addWidget(self.bitrate_vbr_button, 1, 2)

        layout.addWidget(QLabel("Min Bitrate (kbps):"), 2, 0)
        self.min_bitrate_input = QLineEdit()
        self.min_bitrate_input.setPlaceholderText("VBR mode")
        layout.addWidget(self.min_bitrate_input, 2, 1)
        self.min_bitrate_button = QPushButton("Set")
        layout.addWidget(self.min_bitrate_button, 2, 2)

        layout.addWidget(QLabel("Max Bitrate (kbps):"), 3, 0)
        self.max_bitrate_input = QLineEdit()
        self.max_bitrate_input.setPlaceholderText("VBR mode")
        layout.addWidget(self.max_bitrate_input, 3, 1)
        self.max_bitrate_button = QPushButton("Set")
        layout.addWidget(self.max_bitrate_button, 3, 2)

        group.setLayout(layout)
        return group

    def create_frame_settings_group(self) -> QGroupBox:
        """Group 6: Frame Settings - FPS and GOP."""
        group = QGroupBox("Frame Settings")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("FPS:"), 0, 0)
        self.fps_input = QLineEdit()
        self.fps_input.setPlaceholderText("1-60")
        layout.addWidget(self.fps_input, 0, 1)
        self.fps_button = QPushButton("Set")
        layout.addWidget(self.fps_button, 0, 2)

        layout.addWidget(QLabel("GOP (keyframe):"), 1, 0)
        self.gop_input = QLineEdit()
        self.gop_input.setPlaceholderText("e.g., 30")
        layout.addWidget(self.gop_input, 1, 1)
        self.gop_button = QPushButton("Set")
        layout.addWidget(self.gop_button, 1, 2)

        group.setLayout(layout)
        return group

    def create_video_processing_group(self) -> QGroupBox:
        """Group 7: Video Processing - Fit mode, overlays, metadata."""
        group = QGroupBox("Video Processing")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("Fit Mode:"), 0, 0)
        self.fit_mode_combo = QComboBox()
        self.fit_mode_combo.addItems(["Fit", "Crop"])
        layout.addWidget(self.fit_mode_combo, 0, 1, 1, 2)

        layout.addWidget(QLabel("Overlay Mode:"), 1, 0)
        self.overlay_enable_button = QPushButton("Enable")
        self.overlay_enable_button.setCheckable(True)
        layout.addWidget(self.overlay_enable_button, 1, 1)
        self.overlay_disable_button = QPushButton("Disable")
        self.overlay_disable_button.setCheckable(True)
        self.overlay_disable_button.setChecked(True)
        layout.addWidget(self.overlay_disable_button, 1, 2)

        layout.addWidget(QLabel("Metadata Mode:"), 2, 0)
        self.metadata_enable_button = QPushButton("Enable")
        self.metadata_enable_button.setCheckable(True)
        layout.addWidget(self.metadata_enable_button, 2, 1)
        self.metadata_disable_button = QPushButton("Disable")
        self.metadata_disable_button.setCheckable(True)
        self.metadata_disable_button.setChecked(True)
        layout.addWidget(self.metadata_disable_button, 2, 2)

        layout.addWidget(QLabel("Metadata Suffix:"), 3, 0)
        self.metadata_suffix_combo = QComboBox()
        self.metadata_suffix_combo.addItems(["SMPTE336M", "VND.ONVIF.METADATA"])
        layout.addWidget(self.metadata_suffix_combo, 3, 1, 1, 2)

        group.setLayout(layout)
        return group

    def create_rtp_streaming_group(self) -> QGroupBox:
        """Group 8: RTP Direct Streaming - RTP configuration."""
        group = QGroupBox("RTP Direct Streaming")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("RTP Mode:"), 0, 0)
        self.rtp_enable_button = QPushButton("Enable")
        self.rtp_enable_button.setCheckable(True)
        layout.addWidget(self.rtp_enable_button, 0, 1)
        self.rtp_disable_button = QPushButton("Disable")
        self.rtp_disable_button.setCheckable(True)
        self.rtp_disable_button.setChecked(True)
        layout.addWidget(self.rtp_disable_button, 0, 2)

        layout.addWidget(QLabel("RTP Port:"), 1, 0)
        self.rtp_port_input = QLineEdit()
        self.rtp_port_input.setPlaceholderText("Port number")
        layout.addWidget(self.rtp_port_input, 1, 1)
        self.rtp_port_button = QPushButton("Set")
        layout.addWidget(self.rtp_port_button, 1, 2)

        layout.addWidget(QLabel("RTP Dest IP:"), 2, 0)
        self.rtp_dest_ip_input = QLineEdit()
        self.rtp_dest_ip_input.setPlaceholderText("e.g., 192.168.1.100")
        layout.addWidget(self.rtp_dest_ip_input, 2, 1)
        self.rtp_dest_ip_button = QPushButton("Set")
        layout.addWidget(self.rtp_dest_ip_button, 2, 2)

        group.setLayout(layout)
        return group

    def create_rtmp_server_group(self) -> QGroupBox:
        """Group 9: RTMP Server - RTMP configuration."""
        group = QGroupBox("RTMP Server")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("RTMP Mode:"), 0, 0)
        self.rtmp_enable_button = QPushButton("Enable")
        self.rtmp_enable_button.setCheckable(True)
        layout.addWidget(self.rtmp_enable_button, 0, 1)
        self.rtmp_disable_button = QPushButton("Disable")
        self.rtmp_disable_button.setCheckable(True)
        self.rtmp_disable_button.setChecked(True)
        layout.addWidget(self.rtmp_disable_button, 0, 2)

        layout.addWidget(QLabel("RTMP Port:"), 1, 0)
        self.rtmp_port_input = QLineEdit()
        self.rtmp_port_input.setPlaceholderText("Default: 1935")
        layout.addWidget(self.rtmp_port_input, 1, 1)
        self.rtmp_port_button = QPushButton("Set")
        layout.addWidget(self.rtmp_port_button, 1, 2)

        group.setLayout(layout)
        return group

    def create_hls_server_group(self) -> QGroupBox:
        """Group 10: HLS Server - HLS configuration."""
        group = QGroupBox("HLS Server")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("HLS Mode:"), 0, 0)
        self.hls_enable_button = QPushButton("Enable")
        self.hls_enable_button.setCheckable(True)
        layout.addWidget(self.hls_enable_button, 0, 1)
        self.hls_disable_button = QPushButton("Disable")
        self.hls_disable_button.setCheckable(True)
        self.hls_disable_button.setChecked(True)
        layout.addWidget(self.hls_disable_button, 0, 2)

        layout.addWidget(QLabel("HLS Port:"), 1, 0)
        self.hls_port_input = QLineEdit()
        self.hls_port_input.setPlaceholderText("HTTP port")
        layout.addWidget(self.hls_port_input, 1, 1)
        self.hls_port_button = QPushButton("Set")
        layout.addWidget(self.hls_port_button, 1, 2)

        group.setLayout(layout)
        return group

    def create_srt_server_group(self) -> QGroupBox:
        """Group 11: SRT Server - SRT configuration."""
        group = QGroupBox("SRT Server")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("SRT Mode:"), 0, 0)
        self.srt_enable_button = QPushButton("Enable")
        self.srt_enable_button.setCheckable(True)
        layout.addWidget(self.srt_enable_button, 0, 1)
        self.srt_disable_button = QPushButton("Disable")
        self.srt_disable_button.setCheckable(True)
        self.srt_disable_button.setChecked(True)
        layout.addWidget(self.srt_disable_button, 0, 2)

        layout.addWidget(QLabel("SRT Port:"), 1, 0)
        self.srt_port_input = QLineEdit()
        self.srt_port_input.setPlaceholderText("Port number")
        layout.addWidget(self.srt_port_input, 1, 1)
        self.srt_port_button = QPushButton("Set")
        layout.addWidget(self.srt_port_button, 1, 2)

        group.setLayout(layout)
        return group

    def create_advanced_settings_group(self) -> QGroupBox:
        """Group 12: Advanced Settings - UDP payload, query button."""
        group = QGroupBox("Advanced Settings")
        layout = QGridLayout()
        layout.setSpacing(8)

        layout.addWidget(QLabel("UDP Payload Size:"), 0, 0)
        self.udp_payload_input = QLineEdit()
        self.udp_payload_input.setPlaceholderText("100-65535 bytes")
        layout.addWidget(self.udp_payload_input, 0, 1)
        self.udp_payload_button = QPushButton("Set")
        layout.addWidget(self.udp_payload_button, 0, 2)

        self.query_video_settings_button = QPushButton("Query Video Settings")
        self.query_video_settings_button.setStyleSheet("background-color: #2196F3; color: white;")
        layout.addWidget(self.query_video_settings_button, 1, 0, 1, 3)

        group.setLayout(layout)
        return group

    def connect_signals(self):
        """Connect all widget signals to their respective handlers."""
        # Group 1: Target Selection
        self.camera_selector.currentIndexChanged.connect(self.on_target_changed)
        self.stream_selector.currentIndexChanged.connect(self.on_target_changed)

        # Group 2: Stream Control
        self.stream_enable_button.clicked.connect(self.on_stream_enable)
        self.stream_disable_button.clicked.connect(self.on_stream_disable)
        self.stream_restart_button.clicked.connect(self.on_stream_restart)

        # Group 3: RTSP Settings
        self.rtsp_suffix_button.clicked.connect(self.on_rtsp_suffix_set)
        self.rtsp_port_button.clicked.connect(self.on_rtsp_port_set)
        self.rtsp_multicast_ip_button.clicked.connect(self.on_rtsp_multicast_ip_set)
        self.rtsp_multicast_port_button.clicked.connect(self.on_rtsp_multicast_port_set)
        self.rtsp_user_button.clicked.connect(self.on_rtsp_user_set)
        self.rtsp_password_button.clicked.connect(self.on_rtsp_password_set)

        # Group 4: Video Encoding
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        self.resolution_custom_input.returnPressed.connect(self.on_resolution_custom_set)
        self.codec_combo.currentTextChanged.connect(self.on_codec_changed)
        self.h264_profile_combo.currentTextChanged.connect(self.on_h264_profile_changed)
        self.jpeg_quality_slider.valueChanged.connect(self.on_jpeg_quality_changed)

        # Group 5: Bitrate Settings
        self.bitrate_button.clicked.connect(self.on_bitrate_set)
        self.bitrate_cbr_button.clicked.connect(lambda: self.on_bitrate_mode_changed("CBR"))
        self.bitrate_vbr_button.clicked.connect(lambda: self.on_bitrate_mode_changed("VBR"))
        self.min_bitrate_button.clicked.connect(self.on_min_bitrate_set)
        self.max_bitrate_button.clicked.connect(self.on_max_bitrate_set)

        # Group 6: Frame Settings
        self.fps_button.clicked.connect(self.on_fps_set)
        self.gop_button.clicked.connect(self.on_gop_set)

        # Group 7: Video Processing
        self.fit_mode_combo.currentTextChanged.connect(self.on_fit_mode_changed)
        self.overlay_enable_button.clicked.connect(lambda: self.on_overlay_mode_changed(True))
        self.overlay_disable_button.clicked.connect(lambda: self.on_overlay_mode_changed(False))
        self.metadata_enable_button.clicked.connect(lambda: self.on_metadata_mode_changed(True))
        self.metadata_disable_button.clicked.connect(lambda: self.on_metadata_mode_changed(False))
        self.metadata_suffix_combo.currentTextChanged.connect(self.on_metadata_suffix_changed)

        # Group 8: RTP Direct Streaming
        self.rtp_enable_button.clicked.connect(lambda: self.on_rtp_mode_changed(True))
        self.rtp_disable_button.clicked.connect(lambda: self.on_rtp_mode_changed(False))
        self.rtp_port_button.clicked.connect(self.on_rtp_port_set)
        self.rtp_dest_ip_button.clicked.connect(self.on_rtp_dest_ip_set)

        # Group 9: RTMP Server
        self.rtmp_enable_button.clicked.connect(lambda: self.on_rtmp_mode_changed(True))
        self.rtmp_disable_button.clicked.connect(lambda: self.on_rtmp_mode_changed(False))
        self.rtmp_port_button.clicked.connect(self.on_rtmp_port_set)

        # Group 10: HLS Server
        self.hls_enable_button.clicked.connect(lambda: self.on_hls_mode_changed(True))
        self.hls_disable_button.clicked.connect(lambda: self.on_hls_mode_changed(False))
        self.hls_port_button.clicked.connect(self.on_hls_port_set)

        # Group 11: SRT Server
        self.srt_enable_button.clicked.connect(lambda: self.on_srt_mode_changed(True))
        self.srt_disable_button.clicked.connect(lambda: self.on_srt_mode_changed(False))
        self.srt_port_button.clicked.connect(self.on_srt_port_set)

        # Group 12: Advanced Settings
        self.udp_payload_button.clicked.connect(self.on_udp_payload_set)
        self.query_video_settings_button.clicked.connect(self.on_query_video_settings)

    # ========== HANDLER METHODS ==========

    def on_target_changed(self):
        """Handle target camera or stream change."""
        self.current_camera = self.camera_selector.currentIndex() + 1
        self.current_stream = self.stream_selector.currentIndex() + 1
        logger.info(f"RTSP: Target changed to Camera {self.current_camera}, Stream {self.current_stream}")
        self.target_changed.emit(self.current_camera, self.current_stream)

    def on_stream_enable(self):
        """Handle Enable Stream button."""
        logger.info(f"RTSP: Enable stream requested for Camera {self.current_camera}, Stream {self.current_stream}")
        self.stream_enable_pressed.emit(self.current_camera, self.current_stream)

    def on_stream_disable(self):
        """Handle Disable Stream button."""
        logger.info(f"RTSP: Disable stream requested for Camera {self.current_camera}, Stream {self.current_stream}")
        self.stream_disable_pressed.emit(self.current_camera, self.current_stream)

    def on_stream_restart(self):
        """Handle Restart Stream button."""
        logger.info(f"RTSP: Restart stream requested for Camera {self.current_camera}, Stream {self.current_stream}")
        self.stream_restart_pressed.emit(self.current_camera, self.current_stream)

    def on_rtsp_suffix_set(self):
        """Handle RTSP Suffix Set button."""
        suffix = self.rtsp_suffix_input.text().strip()
        if suffix:
            logger.info(f"RTSP: Suffix set to '{suffix}' for Camera {self.current_camera}, Stream {self.current_stream}")
            self.rtsp_suffix_changed.emit(self.current_camera, self.current_stream, suffix)
        else:
            logger.warning("RTSP: RTSP Suffix cannot be empty")

    def on_rtsp_port_set(self):
        """Handle RTSP Port Set button."""
        try:
            port = int(self.rtsp_port_input.text())
            if 1 <= port <= 65535:
                logger.info(f"RTSP: RTSP Port set to {port} (applies to all cameras)")
                self.rtsp_port_changed.emit(port)
            else:
                logger.warning("RTSP: RTSP Port must be between 1-65535")
        except ValueError:
            logger.error("RTSP: Invalid RTSP Port value")

    def on_rtsp_multicast_ip_set(self):
        """Handle RTSP Multicast IP Set button."""
        ip = self.rtsp_multicast_ip_input.text().strip()
        if ip:
            logger.info(f"RTSP: Multicast IP set to '{ip}' for Camera {self.current_camera}, Stream {self.current_stream}")
            self.rtsp_multicast_ip_changed.emit(self.current_camera, self.current_stream, ip)
        else:
            logger.warning("RTSP: Multicast IP cannot be empty")

    def on_rtsp_multicast_port_set(self):
        """Handle RTSP Multicast Port Set button."""
        try:
            port = int(self.rtsp_multicast_port_input.text())
            if 1 <= port <= 65535:
                logger.info(f"RTSP: Multicast Port set to {port} for Camera {self.current_camera}, Stream {self.current_stream}")
                self.rtsp_multicast_port_changed.emit(self.current_camera, self.current_stream, port)
            else:
                logger.warning("RTSP: Multicast Port must be between 1-65535")
        except ValueError:
            logger.error("RTSP: Invalid Multicast Port value")

    def on_rtsp_user_set(self):
        """Handle RTSP User Set button."""
        user = self.rtsp_user_input.text().strip()
        logger.info(f"RTSP: User set to '{user}' for Camera {self.current_camera}, Stream {self.current_stream}")
        self.rtsp_user_changed.emit(self.current_camera, self.current_stream, user)

    def on_rtsp_password_set(self):
        """Handle RTSP Password Set button."""
        password = self.rtsp_password_input.text()
        logger.info(f"RTSP: Password set for Camera {self.current_camera}, Stream {self.current_stream}")
        self.rtsp_password_changed.emit(self.current_camera, self.current_stream, password)

    def on_resolution_changed(self, resolution: str):
        """Handle Resolution combo box change."""
        if resolution == "Custom":
            self.resolution_custom_input.setEnabled(True)
            self.resolution_custom_input.setFocus()
        else:
            self.resolution_custom_input.setEnabled(False)
            logger.info(f"RTSP: Resolution set to {resolution} for Camera {self.current_camera}, Stream {self.current_stream}")
            self.resolution_changed.emit(self.current_camera, self.current_stream, resolution)

    def on_resolution_custom_set(self):
        """Handle custom resolution input."""
        custom_res = self.resolution_custom_input.text().strip()
        if custom_res and 'x' in custom_res:
            logger.info(f"RTSP: Custom resolution set to {custom_res} for Camera {self.current_camera}, Stream {self.current_stream}")
            self.resolution_changed.emit(self.current_camera, self.current_stream, custom_res)
        else:
            logger.warning("RTSP: Invalid custom resolution format (use WxH, e.g., 1024x768)")

    def on_codec_changed(self, codec: str):
        """Handle Codec combo box change."""
        logger.info(f"RTSP: Codec set to {codec} for Camera {self.current_camera}, Stream {self.current_stream}")
        self.codec_changed.emit(self.current_camera, self.current_stream, codec)

        # Enable/disable controls based on codec
        is_jpeg = codec == "JPEG"
        is_h264 = codec == "H264"
        self.jpeg_quality_slider.setEnabled(is_jpeg)
        self.h264_profile_combo.setEnabled(is_h264)

    def on_h264_profile_changed(self, profile: str):
        """Handle H264 Profile combo box change."""
        logger.info(f"RTSP: H264 Profile set to {profile} for Camera {self.current_camera}, Stream {self.current_stream}")
        self.h264_profile_changed.emit(self.current_camera, self.current_stream, profile)

    def on_jpeg_quality_changed(self, quality: int):
        """Handle JPEG Quality slider change."""
        self.jpeg_quality_label.setText(str(quality))
        logger.info(f"RTSP: JPEG Quality set to {quality} for Camera {self.current_camera}, Stream {self.current_stream}")
        self.jpeg_quality_changed.emit(self.current_camera, self.current_stream, quality)

    def on_bitrate_set(self):
        """Handle Bitrate Set button."""
        try:
            bitrate = int(self.bitrate_input.text())
            if bitrate > 0:
                logger.info(f"RTSP: Bitrate set to {bitrate} kbps for Camera {self.current_camera}, Stream {self.current_stream}")
                self.bitrate_changed.emit(self.current_camera, self.current_stream, bitrate)
            else:
                logger.warning("RTSP: Bitrate must be positive")
        except ValueError:
            logger.error("RTSP: Invalid Bitrate value")

    def on_bitrate_mode_changed(self, mode: str):
        """Handle Bitrate Mode button toggle."""
        if mode == "CBR":
            self.bitrate_cbr_button.setChecked(True)
            self.bitrate_vbr_button.setChecked(False)
        else:
            self.bitrate_cbr_button.setChecked(False)
            self.bitrate_vbr_button.setChecked(True)

        logger.info(f"RTSP: Bitrate Mode set to {mode} for Camera {self.current_camera}, Stream {self.current_stream}")
        self.bitrate_mode_changed.emit(self.current_camera, self.current_stream, mode)

    def on_min_bitrate_set(self):
        """Handle Min Bitrate Set button."""
        try:
            min_bitrate = int(self.min_bitrate_input.text())
            if min_bitrate > 0:
                logger.info(f"RTSP: Min Bitrate set to {min_bitrate} kbps for Camera {self.current_camera}, Stream {self.current_stream}")
                self.min_bitrate_changed.emit(self.current_camera, self.current_stream, min_bitrate)
            else:
                logger.warning("RTSP: Min Bitrate must be positive")
        except ValueError:
            logger.error("RTSP: Invalid Min Bitrate value")

    def on_max_bitrate_set(self):
        """Handle Max Bitrate Set button."""
        try:
            max_bitrate = int(self.max_bitrate_input.text())
            if max_bitrate > 0:
                logger.info(f"RTSP: Max Bitrate set to {max_bitrate} kbps for Camera {self.current_camera}, Stream {self.current_stream}")
                self.max_bitrate_changed.emit(self.current_camera, self.current_stream, max_bitrate)
            else:
                logger.warning("RTSP: Max Bitrate must be positive")
        except ValueError:
            logger.error("RTSP: Invalid Max Bitrate value")

    def on_fps_set(self):
        """Handle FPS Set button."""
        try:
            fps = int(self.fps_input.text())
            if 1 <= fps <= 60:
                logger.info(f"RTSP: FPS set to {fps} for Camera {self.current_camera}, Stream {self.current_stream}")
                self.fps_changed.emit(self.current_camera, self.current_stream, fps)
            else:
                logger.warning("RTSP: FPS must be between 1-60")
        except ValueError:
            logger.error("RTSP: Invalid FPS value")

    def on_gop_set(self):
        """Handle GOP Set button."""
        try:
            gop = int(self.gop_input.text())
            if gop > 0:
                logger.info(f"RTSP: GOP set to {gop} for Camera {self.current_camera}, Stream {self.current_stream}")
                self.gop_changed.emit(self.current_camera, self.current_stream, gop)
            else:
                logger.warning("RTSP: GOP must be positive")
        except ValueError:
            logger.error("RTSP: Invalid GOP value")

    def on_fit_mode_changed(self, mode: str):
        """Handle Fit Mode combo box change."""
        logger.info(f"RTSP: Fit Mode set to {mode} for Camera {self.current_camera}, Stream {self.current_stream}")
        self.fit_mode_changed.emit(self.current_camera, self.current_stream, mode)

    def on_overlay_mode_changed(self, enable: bool):
        """Handle Overlay Mode button toggle."""
        self.overlay_enable_button.setChecked(enable)
        self.overlay_disable_button.setChecked(not enable)
        logger.info(f"RTSP: Overlay Mode {'ENABLED' if enable else 'DISABLED'} for Camera {self.current_camera}, Stream {self.current_stream}")
        self.overlay_mode_changed.emit(self.current_camera, self.current_stream, enable)

    def on_metadata_mode_changed(self, enable: bool):
        """Handle Metadata Mode button toggle."""
        self.metadata_enable_button.setChecked(enable)
        self.metadata_disable_button.setChecked(not enable)
        logger.info(f"RTSP: Metadata Mode {'ENABLED' if enable else 'DISABLED'} for Camera {self.current_camera}, Stream {self.current_stream}")
        self.metadata_mode_changed.emit(self.current_camera, self.current_stream, enable)

    def on_metadata_suffix_changed(self, suffix: str):
        """Handle Metadata Suffix combo box change."""
        logger.info(f"RTSP: Metadata Suffix set to {suffix} for Camera {self.current_camera}, Stream {self.current_stream}")
        self.metadata_suffix_changed.emit(self.current_camera, self.current_stream, suffix)

    def on_rtp_mode_changed(self, enable: bool):
        """Handle RTP Mode button toggle."""
        self.rtp_enable_button.setChecked(enable)
        self.rtp_disable_button.setChecked(not enable)
        logger.info(f"RTSP: RTP Mode {'ENABLED' if enable else 'DISABLED'} for Camera {self.current_camera}, Stream {self.current_stream}")
        self.rtp_mode_changed.emit(self.current_camera, self.current_stream, enable)

    def on_rtp_port_set(self):
        """Handle RTP Port Set button."""
        try:
            port = int(self.rtp_port_input.text())
            if 1 <= port <= 65535:
                logger.info(f"RTSP: RTP Port set to {port} for Camera {self.current_camera}, Stream {self.current_stream}")
                self.rtp_port_changed.emit(self.current_camera, self.current_stream, port)
            else:
                logger.warning("RTSP: RTP Port must be between 1-65535")
        except ValueError:
            logger.error("RTSP: Invalid RTP Port value")

    def on_rtp_dest_ip_set(self):
        """Handle RTP Destination IP Set button."""
        ip = self.rtp_dest_ip_input.text().strip()
        if ip:
            logger.info(f"RTSP: RTP Destination IP set to '{ip}' for Camera {self.current_camera}, Stream {self.current_stream}")
            self.rtp_dest_ip_changed.emit(self.current_camera, self.current_stream, ip)
        else:
            logger.warning("RTSP: RTP Destination IP cannot be empty")

    def on_rtmp_mode_changed(self, enable: bool):
        """Handle RTMP Mode button toggle."""
        self.rtmp_enable_button.setChecked(enable)
        self.rtmp_disable_button.setChecked(not enable)
        logger.info(f"RTSP: RTMP Mode {'ENABLED' if enable else 'DISABLED'} for Camera {self.current_camera}, Stream {self.current_stream}")
        self.rtmp_mode_changed.emit(self.current_camera, self.current_stream, enable)

    def on_rtmp_port_set(self):
        """Handle RTMP Port Set button."""
        try:
            port = int(self.rtmp_port_input.text())
            if 1 <= port <= 65535:
                logger.info(f"RTSP: RTMP Port set to {port} for Camera {self.current_camera}, Stream {self.current_stream}")
                self.rtmp_port_changed.emit(self.current_camera, self.current_stream, port)
            else:
                logger.warning("RTSP: RTMP Port must be between 1-65535")
        except ValueError:
            logger.error("RTSP: Invalid RTMP Port value")

    def on_hls_mode_changed(self, enable: bool):
        """Handle HLS Mode button toggle."""
        self.hls_enable_button.setChecked(enable)
        self.hls_disable_button.setChecked(not enable)
        logger.info(f"RTSP: HLS Mode {'ENABLED' if enable else 'DISABLED'} for Camera {self.current_camera}, Stream {self.current_stream}")
        self.hls_mode_changed.emit(self.current_camera, self.current_stream, enable)

    def on_hls_port_set(self):
        """Handle HLS Port Set button."""
        try:
            port = int(self.hls_port_input.text())
            if 1 <= port <= 65535:
                logger.info(f"RTSP: HLS Port set to {port} for Camera {self.current_camera}, Stream {self.current_stream}")
                self.hls_port_changed.emit(self.current_camera, self.current_stream, port)
            else:
                logger.warning("RTSP: HLS Port must be between 1-65535")
        except ValueError:
            logger.error("RTSP: Invalid HLS Port value")

    def on_srt_mode_changed(self, enable: bool):
        """Handle SRT Mode button toggle."""
        self.srt_enable_button.setChecked(enable)
        self.srt_disable_button.setChecked(not enable)
        logger.info(f"RTSP: SRT Mode {'ENABLED' if enable else 'DISABLED'} for Camera {self.current_camera}, Stream {self.current_stream}")
        self.srt_mode_changed.emit(self.current_camera, self.current_stream, enable)

    def on_srt_port_set(self):
        """Handle SRT Port Set button."""
        try:
            port = int(self.srt_port_input.text())
            if 1 <= port <= 65535:
                logger.info(f"RTSP: SRT Port set to {port} for Camera {self.current_camera}, Stream {self.current_stream}")
                self.srt_port_changed.emit(self.current_camera, self.current_stream, port)
            else:
                logger.warning("RTSP: SRT Port must be between 1-65535")
        except ValueError:
            logger.error("RTSP: Invalid SRT Port value")

    def on_udp_payload_set(self):
        """Handle UDP Payload Size Set button."""
        try:
            size = int(self.udp_payload_input.text())
            if 100 <= size <= 65535:
                logger.info(f"RTSP: UDP Payload Size set to {size} bytes for Camera {self.current_camera}, Stream {self.current_stream}")
                self.udp_payload_changed.emit(self.current_camera, self.current_stream, size)
            else:
                logger.warning("RTSP: UDP Payload Size must be between 100-65535")
        except ValueError:
            logger.error("RTSP: Invalid UDP Payload Size value")

    def on_query_video_settings(self):
        """Handle Query Video Settings button."""
        logger.info(f"RTSP: Query Video Settings for Camera {self.current_camera}, Stream {self.current_stream}")
        self.query_video_settings_pressed.emit(self.current_camera, self.current_stream)

    # ========== PUBLIC API METHODS ==========




