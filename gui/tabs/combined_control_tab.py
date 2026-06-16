"""
gui/tabs/combined_control_tab.py
Combined video display and PTZ control tab - shows streams and trackpad control together.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                             QGroupBox, QLabel, QGridLayout, QPushButton, QLineEdit, QSlider, QTabWidget, QTextEdit, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QTextCursor
from gui.widgets.rtsp_video_widget import RTSPVideoWidget
from gui.widgets.ptz_trackpad import PTZControlWidget
from utils.constants import load_config
from utils.logger import setup_logger
from utils.network_discovery import discover_payload
from utils.camera_discovery import discover_cameras

logger = setup_logger()


class DiscoveryThread(QThread):
    """Background thread for network discovery to avoid blocking GUI."""
    discovery_complete = pyqtSignal(bool, dict)  # (is_available, services)

    def __init__(self, ip_address: str):
        super().__init__()
        self.ip_address = ip_address

    def run(self):
        is_available, services = discover_payload(self.ip_address)
        self.discovery_complete.emit(is_available, services)


class ComponentStatusThread(QThread):
    """Background thread for component status checks via SSH to main board."""
    status_update = pyqtSignal(str, bool)  # (component_name, is_online)
    check_complete = pyqtSignal()

    def __init__(self, component_status: dict, main_board_ip: str):
        super().__init__()
        self.component_status = component_status
        self.main_board_ip = main_board_ip
        self.ssh_user = "silentsentinel"
        self.ssh_pass = "Sentinel123"

    def run(self):
        from utils.logger import setup_logger

        logger = setup_logger()
        logger.info(f"ComponentStatusThread: SSH to {self.main_board_ip} to ping internal components")

        try:
            import paramiko
        except ImportError:
            logger.error("paramiko library not installed. Install with: pip install paramiko")
            self.check_complete.emit()
            return

        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            logger.info(f"Connecting to {self.main_board_ip} via SSH as {self.ssh_user}")
            ssh.connect(
                self.main_board_ip,
                username=self.ssh_user,
                password=self.ssh_pass,
                timeout=10,
                look_for_keys=False,
                allow_agent=False
            )
            logger.info("SSH connection established")

            for component_name, component_data in self.component_status.items():
                ip = component_data['ip']

                # Skip Main Board (already marked as online)
                if component_name == 'Main Board':
                    logger.debug(f"ComponentStatusThread: Skipping {component_name} (already online)")
                    continue

                if ip is None:
                    logger.warning(f"ComponentStatusThread: {component_name} has no IP address, skipping")
                    continue

                logger.debug(f"ComponentStatusThread: Pinging {component_name} at {ip} via SSH")

                # Execute ping command on the main board
                ping_command = f'ping -c 1 -W 2 {ip}'

                try:
                    stdin, stdout, stderr = ssh.exec_command(ping_command, timeout=5)
                    exit_status = stdout.channel.recv_exit_status()
                    success = (exit_status == 0)

                    logger.info(f"ComponentStatusThread: {component_name} ({ip}) - {'ONLINE' if success else 'OFFLINE'} (exit: {exit_status})")
                    self.status_update.emit(component_name, success)

                except Exception as e:
                    logger.error(f"ComponentStatusThread: {component_name} ({ip}) - PING ERROR: {e}")
                    self.status_update.emit(component_name, False)

            ssh.close()
            logger.info("SSH connection closed")

        except paramiko.AuthenticationException:
            logger.error(f"SSH authentication failed for {self.ssh_user}@{self.main_board_ip}")
        except paramiko.SSHException as e:
            logger.error(f"SSH connection error: {e}")
        except Exception as e:
            logger.error(f"ComponentStatusThread: Unexpected error: {e}")
        finally:
            try:
                ssh.close()
            except:
                pass

        logger.info("ComponentStatusThread: All SSH ping checks complete")
        self.check_complete.emit()


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

    # Speed control signals
    pan_speed_changed = pyqtSignal(float)  # degrees/sec
    tilt_speed_changed = pyqtSignal(float)  # degrees/sec
    zoom_speed_changed = pyqtSignal(float)  # -1.0 to 1.0
    focus_speed_changed = pyqtSignal(float)  # -1.0 to 1.0

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.actual_pan = None
        self.actual_tilt = None
        self.discovery_thread = None
        self.component_status_thread = None
        self.payload_available = False
        self.camera_availability = {}  # Track which cameras are available
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: PTZ control (fixed width like reference app)
        left_widget = self.create_control_section()

        # Right side: Video streams (expands to fill space)
        right_widget = self.create_video_section()

        # Use simple horizontal layout - control panel has fixed width, video expands
        main_layout.addWidget(left_widget, 0)   # Control panel fixed width (no stretch)
        main_layout.addWidget(right_widget, 1)  # Video expands (stretch factor 1)

        self.setLayout(main_layout)

        logger.info("Combined control tab initialized")

    def create_video_section(self) -> QWidget:
        """Create video display section with dynamic camera layout."""
        self.video_widget = QWidget()
        self.video_layout = QVBoxLayout()
        self.video_layout.setSpacing(5)
        self.video_layout.setContentsMargins(0, 0, 0, 0)

        # Create placeholder for dynamic video grid
        self.video_grid_widget = QWidget()
        self.video_grid = QGridLayout()
        self.video_grid.setSpacing(10)
        self.video_grid_widget.setLayout(self.video_grid)
        self.video_layout.addWidget(self.video_grid_widget)

        # Create video widgets with video_grid_widget as parent but don't add to layout yet
        thermal_config = self.config['rtsp_streams']['thermal']
        self.thermal_widget = RTSPVideoWidget(
            thermal_config['url'],
            thermal_config['label'],
            auto_start=False  # Don't auto-connect on startup
        )
        self.thermal_widget.setParent(self.video_grid_widget)

        daylight_config = self.config['rtsp_streams']['daylight']
        self.daylight_widget = RTSPVideoWidget(
            daylight_config['url'],
            daylight_config['label'],
            auto_start=False  # Don't auto-connect on startup
        )
        self.daylight_widget.setParent(self.video_grid_widget)

        swir_config = self.config['rtsp_streams']['swir']
        self.swir_widget = RTSPVideoWidget(
            swir_config['url'],
            swir_config['label'],
            auto_start=False  # Don't auto-connect on startup
        )
        self.swir_widget.setParent(self.video_grid_widget)

        # Initially hide all widgets - they'll be added dynamically after discovery
        self.thermal_widget.hide()
        self.daylight_widget.hide()
        self.swir_widget.hide()

        # Show placeholder message
        self.no_cameras_label = QLabel("Connect to a payload to view camera feeds")
        self.no_cameras_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_cameras_label.setStyleSheet("font-size: 12pt; color: #888; padding: 50px;")
        self.video_grid.addWidget(self.no_cameras_label, 0, 0)

        self.video_widget.setLayout(self.video_layout)
        return self.video_widget

    def create_control_section(self) -> QWidget:
        """Create PTZ control section with tabbed interface."""
        widget = QWidget()
        widget.setFixedWidth(480)  # Fixed width like reference app (360px in reference)
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        tabs = QTabWidget()
        tabs.addTab(self.create_connection_tab(), "Connection")
        tabs.addTab(self.create_control_tab(), "Control")
        tabs.addTab(self.create_status_tab(), "Status")

        layout.addWidget(tabs)
        widget.setLayout(layout)
        return widget

    def create_connection_tab(self) -> QWidget:
        """Create connection tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Connection status group
        status_group = QGroupBox("Network")
        status_layout = QVBoxLayout()

        # IP Address input with status indicator
        ip_row = QHBoxLayout()
        ip_label = QLabel("Target IP Address:")
        ip_label.setStyleSheet("font-size: 10pt; font-weight: bold;")
        ip_row.addWidget(ip_label)

        # Connection status indicator (next to IP label)
        self.connection_indicator = QLabel("not connected")
        self.connection_indicator.setStyleSheet("""
            font-size: 9pt;
            color: #ff4444;
            padding-left: 10px;
        """)
        ip_row.addWidget(self.connection_indicator)
        ip_row.addStretch()

        status_layout.addLayout(ip_row)

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
        status_layout.addWidget(self.ip_input)

        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("padding: 10px; font-size: 11pt;")
        self.connect_button.clicked.connect(self.connection_toggle.emit)
        status_layout.addWidget(self.connect_button)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Connection Log group
        log_group = QGroupBox("Connection Log")
        log_layout = QVBoxLayout()

        self.connection_log = QTextEdit()
        self.connection_log.setReadOnly(True)
        self.connection_log.setMaximumHeight(200)
        self.connection_log.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #aaaaaa;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #555;
            }
        """)
        self.connection_log.append("Ready - waiting for connection...")

        log_layout.addWidget(self.connection_log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Status group - component health indicators
        status_group = QGroupBox("Status")
        status_layout = QGridLayout()
        status_layout.setSpacing(8)

        # Component list with IP addresses (from IP Allocations.txt)
        self.component_status = {
            'Main Board': {'ip': None, 'label': None},  # User-defined IP
            'Daylight': {'ip': '10.10.10.2', 'label': None},
            'Thermal': {'ip': '10.10.10.3', 'label': None},
            'SWIR': {'ip': '10.10.10.4', 'label': None},
            'WL Illuminator': {'ip': '10.10.10.5', 'label': None},
            'IR Illuminator': {'ip': '10.10.10.6', 'label': None},
            'Sub-Payload': {'ip': '10.10.10.8', 'label': None},
            'Speaker': {'ip': '10.10.10.7', 'label': None}
        }

        # Create status indicators for each component
        row = 0
        for component_name, component_data in self.component_status.items():
            # Component name label
            name_label = QLabel(f"{component_name}:")
            name_label.setStyleSheet("font-size: 9pt;")
            status_layout.addWidget(name_label, row, 0)

            # Status indicator (colored dot)
            status_indicator = QLabel("●")
            status_indicator.setStyleSheet("""
                font-size: 14pt;
                color: #888888;
                padding: 0px;
            """)
            status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_layout.addWidget(status_indicator, row, 1)

            # Store reference to the label for updates
            component_data['label'] = status_indicator
            row += 1

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_control_tab(self) -> QWidget:
        """Create PTZ control tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Camera selector group
        camera_select_group = QGroupBox("Active Camera")
        camera_select_layout = QVBoxLayout()

        camera_label = QLabel("Select camera for Zoom/Focus control:")
        camera_label.setStyleSheet("font-size: 9pt; padding-bottom: 5px;")
        camera_select_layout.addWidget(camera_label)

        # Create button group for exclusive selection (only one can be selected)
        self.camera_button_group = QButtonGroup()
        self.camera_button_group.setExclusive(True)

        # Create horizontal layout for camera buttons
        camera_buttons_layout = QHBoxLayout()
        camera_buttons_layout.setSpacing(5)

        # Camera 1 - Daylight button
        self.camera1_button = QPushButton("Daylight")
        self.camera1_button.setCheckable(True)
        self.camera1_button.setChecked(True)  # Default selected
        self.camera1_button.setProperty("camera", "Camera1")
        self.camera1_button.setStyleSheet("""
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
        """)
        self.camera_button_group.addButton(self.camera1_button, 1)
        camera_buttons_layout.addWidget(self.camera1_button)

        # Camera 2 - Thermal button
        self.camera2_button = QPushButton("Thermal")
        self.camera2_button.setCheckable(True)
        self.camera2_button.setProperty("camera", "Camera2")
        self.camera2_button.setStyleSheet("""
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
        """)
        self.camera_button_group.addButton(self.camera2_button, 2)
        camera_buttons_layout.addWidget(self.camera2_button)

        # Camera 3 - SWIR button
        self.camera3_button = QPushButton("SWIR")
        self.camera3_button.setCheckable(True)
        self.camera3_button.setProperty("camera", "Camera3")
        self.camera3_button.setStyleSheet("""
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
        """)
        self.camera_button_group.addButton(self.camera3_button, 3)
        camera_buttons_layout.addWidget(self.camera3_button)

        camera_select_layout.addLayout(camera_buttons_layout)

        # Connect signal
        self.camera_button_group.buttonClicked.connect(self.on_camera_button_clicked)

        camera_select_group.setLayout(camera_select_layout)
        layout.addWidget(camera_select_group)

        # PTZ Trackpad control
        self.ptz_control = PTZControlWidget()
        self.ptz_control.pan_tilt_moved.connect(self.on_trackpad_moved)
        self.ptz_control.pan_tilt_released.connect(self.on_trackpad_released)
        self.ptz_control.zoom_pressed.connect(self.on_zoom_pressed)
        self.ptz_control.zoom_released.connect(self.on_zoom_released)
        self.ptz_control.focus_pressed.connect(self.on_focus_pressed)
        self.ptz_control.focus_released.connect(self.on_focus_released)

        # Connect directional arrows (use slider values)
        self.ptz_control.arrow_up_pressed.connect(self.on_arrow_up_pressed)
        self.ptz_control.arrow_down_pressed.connect(self.on_arrow_down_pressed)
        self.ptz_control.arrow_left_pressed.connect(self.on_arrow_left_pressed)
        self.ptz_control.arrow_right_pressed.connect(self.on_arrow_right_pressed)
        self.ptz_control.arrow_released.connect(self.on_arrow_released)

        layout.addWidget(self.ptz_control)

        # Speed Control group
        speed_group = QGroupBox("Speed Control")
        speed_layout = QGridLayout()
        speed_layout.setSpacing(5)

        # Pan Speed Slider
        speed_layout.addWidget(QLabel("<b>Pan Speed:</b>"), 0, 0)
        self.pan_speed_label = QLabel("0.0 °/s")
        self.pan_speed_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        self.pan_speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        speed_layout.addWidget(self.pan_speed_label, 0, 1)

        self.pan_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.pan_speed_slider.setMinimum(-100)  # -10.0 deg/s
        self.pan_speed_slider.setMaximum(100)   # +10.0 deg/s
        self.pan_speed_slider.setValue(0)
        self.pan_speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.pan_speed_slider.setTickInterval(25)
        self.pan_speed_slider.valueChanged.connect(self.on_pan_speed_changed)
        speed_layout.addWidget(self.pan_speed_slider, 1, 0, 1, 2)

        # Tilt Speed Slider
        speed_layout.addWidget(QLabel("<b>Tilt Speed:</b>"), 2, 0)
        self.tilt_speed_label = QLabel("0.0 °/s")
        self.tilt_speed_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        self.tilt_speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        speed_layout.addWidget(self.tilt_speed_label, 2, 1)

        self.tilt_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.tilt_speed_slider.setMinimum(-100)  # -10.0 deg/s
        self.tilt_speed_slider.setMaximum(100)   # +10.0 deg/s
        self.tilt_speed_slider.setValue(0)
        self.tilt_speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.tilt_speed_slider.setTickInterval(25)
        self.tilt_speed_slider.valueChanged.connect(self.on_tilt_speed_changed)
        speed_layout.addWidget(self.tilt_speed_slider, 3, 0, 1, 2)

        # Zoom Speed Slider
        speed_layout.addWidget(QLabel("<b>Zoom Speed:</b>"), 4, 0)
        self.zoom_speed_label = QLabel("0.0")
        self.zoom_speed_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        self.zoom_speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        speed_layout.addWidget(self.zoom_speed_label, 4, 1)

        self.zoom_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_speed_slider.setMinimum(-100)  # -1.0 (out)
        self.zoom_speed_slider.setMaximum(100)   # +1.0 (in)
        self.zoom_speed_slider.setValue(0)
        self.zoom_speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.zoom_speed_slider.setTickInterval(25)
        self.zoom_speed_slider.valueChanged.connect(self.on_zoom_speed_changed)
        speed_layout.addWidget(self.zoom_speed_slider, 5, 0, 1, 2)

        # Focus Speed Slider
        speed_layout.addWidget(QLabel("<b>Focus Speed:</b>"), 6, 0)
        self.focus_speed_label = QLabel("0.0")
        self.focus_speed_label.setStyleSheet("font-size: 10pt; color: #2a82da;")
        self.focus_speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        speed_layout.addWidget(self.focus_speed_label, 6, 1)

        self.focus_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.focus_speed_slider.setMinimum(-100)  # -1.0 (near)
        self.focus_speed_slider.setMaximum(100)   # +1.0 (far)
        self.focus_speed_slider.setValue(0)
        self.focus_speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.focus_speed_slider.setTickInterval(25)
        self.focus_speed_slider.valueChanged.connect(self.on_focus_speed_changed)
        speed_layout.addWidget(self.focus_speed_slider, 7, 0, 1, 2)

        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)

        # Position feedback group (moved from Status tab)
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

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_status_tab(self) -> QWidget:
        """Create status/telemetry tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Status tab is now available for future telemetry/diagnostics
        info_label = QLabel("Position feedback has been moved to the Control tab.")
        info_label.setStyleSheet("font-size: 10pt; color: #888; padding: 20px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def on_trackpad_moved(self, pan: float, tilt: float):
        """
        Handle trackpad movement - joystick mode.
        Distance from center determines speed.

        pan, tilt: normalized -1.0 to 1.0 (distance from center)
        """
        # Convert to speed (degrees/second)
        # Max speed: 20 deg/s for pan, 10 deg/s for tilt
        max_pan_speed = 20.0  # degrees/second
        max_tilt_speed = 10.0  # degrees/second

        pan_speed = pan * max_pan_speed
        tilt_speed = tilt * max_tilt_speed

        # Update command labels to show speed
        self.cmd_pan_label.setText(f"{pan_speed:.1f} °/s")
        self.cmd_tilt_label.setText(f"{tilt_speed:.1f} °/s")

        # Emit speed commands
        self.pan_speed_changed.emit(pan_speed)
        self.tilt_speed_changed.emit(tilt_speed)
        logger.debug(f"Trackpad speed: Pan={pan_speed:.1f} °/s, Tilt={tilt_speed:.1f} °/s")

    def on_trackpad_released(self):
        """Handle trackpad release - stop movement by setting speed to 0."""
        # Stop by setting speed to 0
        self.pan_speed_changed.emit(0.0)
        self.tilt_speed_changed.emit(0.0)

        # Update labels
        self.cmd_pan_label.setText("0.0 °/s")
        self.cmd_tilt_label.setText("0.0 °/s")

        logger.debug("Trackpad released - speeds set to 0")

    def on_camera_button_clicked(self, button: QPushButton):
        """Handle camera button selection."""
        camera_id = button.property("camera")
        camera_name = button.text()
        logger.info(f"Active camera changed to: {camera_name} ({camera_id})")
        self.log_connection_event(f"Active camera: {camera_name}")

    def get_selected_camera(self) -> str:
        """Get the currently selected camera module name (Camera1, Camera2, or Camera3)."""
        selected_button = self.camera_button_group.checkedButton()
        if selected_button:
            return selected_button.property("camera")
        return "Camera1"  # Default fallback

    def on_zoom_pressed(self, direction: int):
        """Handle zoom button press."""
        camera = self.get_selected_camera()
        self.zoom_command.emit(direction)
        logger.debug(f"Zoom {'in' if direction > 0 else 'out'} pressed for {camera}")

    def on_zoom_released(self):
        """Handle zoom button release."""
        camera = self.get_selected_camera()
        self.zoom_stop.emit()
        logger.debug(f"Zoom released for {camera}")

    def on_focus_pressed(self, direction: int):
        """Handle focus button press."""
        camera = self.get_selected_camera()
        self.focus_command.emit(direction)
        logger.debug(f"Focus {'far' if direction > 0 else 'near'} pressed for {camera}")

    def on_focus_released(self):
        """Handle focus button release."""
        camera = self.get_selected_camera()
        self.focus_stop.emit()
        logger.debug(f"Focus released for {camera}")

    def on_pan_speed_changed(self, value: int):
        """Handle pan speed slider change."""
        speed = value / 10.0  # Convert to degrees/second
        self.pan_speed_label.setText(f"{speed:.1f} °/s")
        self.pan_speed_changed.emit(speed)
        logger.debug(f"Pan speed: {speed:.1f} °/s")

    def on_tilt_speed_changed(self, value: int):
        """Handle tilt speed slider change."""
        speed = value / 10.0  # Convert to degrees/second
        self.tilt_speed_label.setText(f"{speed:.1f} °/s")
        self.tilt_speed_changed.emit(speed)
        logger.debug(f"Tilt speed: {speed:.1f} °/s")

    def on_zoom_speed_changed(self, value: int):
        """Handle zoom speed slider change."""
        speed = value / 100.0  # Convert to -1.0 to +1.0
        self.zoom_speed_label.setText(f"{speed:.2f}")
        self.zoom_speed_changed.emit(speed)
        logger.debug(f"Zoom speed: {speed:.2f}")

    def on_focus_speed_changed(self, value: int):
        """Handle focus speed slider change."""
        speed = value / 100.0  # Convert to -1.0 to +1.0
        self.focus_speed_label.setText(f"{speed:.2f}")
        self.focus_speed_changed.emit(speed)
        logger.debug(f"Focus speed: {speed:.2f}")

    def on_arrow_up_pressed(self):
        """Handle up arrow pressed - use tilt slider value."""
        tilt_speed = self.tilt_speed_slider.value() / 10.0
        # Use positive speed for up, or default if slider is at 0
        if tilt_speed == 0:
            tilt_speed = 5.0  # Default speed
        else:
            tilt_speed = abs(tilt_speed)  # Always positive for up
        self.tilt_speed_changed.emit(tilt_speed)
        logger.debug(f"Arrow UP: Tilt speed {tilt_speed:.1f} °/s")

    def on_arrow_down_pressed(self):
        """Handle down arrow pressed - use tilt slider value."""
        tilt_speed = self.tilt_speed_slider.value() / 10.0
        # Use negative speed for down, or default if slider is at 0
        if tilt_speed == 0:
            tilt_speed = -5.0  # Default speed
        else:
            tilt_speed = -abs(tilt_speed)  # Always negative for down
        self.tilt_speed_changed.emit(tilt_speed)
        logger.debug(f"Arrow DOWN: Tilt speed {tilt_speed:.1f} °/s")

    def on_arrow_left_pressed(self):
        """Handle left arrow pressed - use pan slider value."""
        pan_speed = self.pan_speed_slider.value() / 10.0
        # Use negative speed for left, or default if slider is at 0
        if pan_speed == 0:
            pan_speed = -5.0  # Default speed
        else:
            pan_speed = -abs(pan_speed)  # Always negative for left
        self.pan_speed_changed.emit(pan_speed)
        logger.debug(f"Arrow LEFT: Pan speed {pan_speed:.1f} °/s")

    def on_arrow_right_pressed(self):
        """Handle right arrow pressed - use pan slider value."""
        pan_speed = self.pan_speed_slider.value() / 10.0
        # Use positive speed for right, or default if slider is at 0
        if pan_speed == 0:
            pan_speed = 5.0  # Default speed
        else:
            pan_speed = abs(pan_speed)  # Always positive for right
        self.pan_speed_changed.emit(pan_speed)
        logger.debug(f"Arrow RIGHT: Pan speed {pan_speed:.1f} °/s")

    def on_arrow_released(self):
        """Handle arrow button released - stop movement."""
        self.pan_speed_changed.emit(0.0)
        self.tilt_speed_changed.emit(0.0)
        logger.debug("Arrow released - stopped")

    def update_actual_position(self, pan: float, tilt: float):
        """Update actual position from telemetry."""
        self.actual_pan = pan
        self.actual_tilt = tilt
        self.actual_pan_label.setText(f"{pan:.1f}°")
        self.actual_tilt_label.setText(f"{tilt:.1f}°")

    def get_target_ip(self) -> str:
        """Get the current target IP from the input field."""
        return self.ip_input.text().strip()

    def rebuild_video_layout(self):
        """Rebuild video layout based on available cameras."""
        logger.info(f"Rebuilding video layout. Camera availability: {self.camera_availability}")

        # Clear existing layout - remove all widgets
        while self.video_grid.count():
            item = self.video_grid.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)  # Remove from layout hierarchy
                widget.hide()  # Ensure it's hidden

        # Explicitly hide all camera widgets (they keep their parent, just removed from layout)
        self.thermal_widget.hide()
        logger.debug(f"Thermal widget hidden: {self.thermal_widget.isHidden()}, visible: {self.thermal_widget.isVisible()}")

        self.daylight_widget.hide()
        logger.debug(f"Daylight widget hidden: {self.daylight_widget.isHidden()}, visible: {self.daylight_widget.isVisible()}")

        self.swir_widget.hide()
        logger.debug(f"SWIR widget hidden: {self.swir_widget.isHidden()}, visible: {self.swir_widget.isVisible()}, parent: {self.swir_widget.parent()}")

        self.no_cameras_label.hide()

        # Get list of available cameras with their widgets
        available_cameras = []
        if self.camera_availability.get('thermal', False):
            available_cameras.append(('Thermal', self.thermal_widget))
        if self.camera_availability.get('daylight', False):
            available_cameras.append(('Daylight', self.daylight_widget))
        if self.camera_availability.get('swir', False):
            available_cameras.append(('SWIR', self.swir_widget))

        num_cameras = len(available_cameras)
        logger.info(f"Number of available cameras: {num_cameras}")

        if num_cameras == 0:
            # No cameras available - show message
            self.no_cameras_label.setText("No cameras available")
            self.video_grid.addWidget(self.no_cameras_label, 0, 0)
            self.no_cameras_label.show()
            logger.info("No cameras available - showing placeholder")

        elif num_cameras == 1:
            # One camera - full width
            name, widget = available_cameras[0]
            self.video_grid.addWidget(widget, 0, 0)
            widget.show()
            logger.info(f"Layout: 1 camera ({name}) - full width")

        elif num_cameras == 2:
            # Two cameras - side by side
            name1, widget1 = available_cameras[0]
            name2, widget2 = available_cameras[1]
            self.video_grid.addWidget(widget1, 0, 0)
            self.video_grid.addWidget(widget2, 0, 1)
            widget1.show()
            widget2.show()
            logger.info(f"Layout: 2 cameras ({name1}, {name2}) - side by side")
            logger.debug(f"After layout - SWIR visible: {self.swir_widget.isVisible()}, parent: {self.swir_widget.parent()}")

        elif num_cameras == 3:
            # Three cameras - 2x2 grid (thermal and daylight on top, swir bottom left)
            name1, widget1 = available_cameras[0]
            name2, widget2 = available_cameras[1]
            name3, widget3 = available_cameras[2]
            self.video_grid.addWidget(widget1, 0, 0)
            self.video_grid.addWidget(widget2, 0, 1)
            self.video_grid.addWidget(widget3, 1, 0)
            widget1.show()
            widget2.show()
            widget3.show()
            logger.info(f"Layout: 3 cameras ({name1}, {name2}, {name3}) - 2x2 grid")

    def update_video_streams_ip(self, new_ip: str):
        """Update video stream URLs with new IP address and discover available cameras."""
        self.log_connection_event(f"Discovering cameras at {new_ip}...")

        # Build camera configs with new IP
        camera_configs = {
            'thermal': {'url': f"rtsp://{new_ip}:7031/Cam1Stream1", 'label': 'Thermal Camera'},
            'daylight': {'url': f"rtsp://{new_ip}:7031/Cam2Stream1", 'label': 'Daylight Camera'},
            'swir': {'url': f"rtsp://{new_ip}:7031/Cam3Stream1", 'label': 'SWIR Camera'}
        }

        # Discover which cameras are available (checks actual RTSP stream, not just port)
        logger.info(f"Discovering cameras at {new_ip}...")
        self.camera_availability = discover_cameras(camera_configs, timeout=3.0)

        # Log availability
        for cam_name, available in self.camera_availability.items():
            status = "✓ Available" if available else "✗ Not available"
            logger.info(f"  {cam_name.capitalize()}: {status}")
            self.log_connection_event(f"{cam_name.capitalize()}: {status}")

        # Update URLs for all cameras, but only START streams for available ones
        thermal_url = camera_configs['thermal']['url']
        daylight_url = camera_configs['daylight']['url']
        swir_url = camera_configs['swir']['url']

        # Thermal camera
        if hasattr(self, 'thermal_widget'):
            if hasattr(self.thermal_widget, 'stream_thread') and self.thermal_widget.stream_thread:
                if self.camera_availability.get('thermal', False):
                    self.thermal_widget.stream_thread.change_url(thermal_url)
                else:
                    logger.info("Stopping thermal camera stream - not available")
                    # Stop the existing stream thread
                    self.thermal_widget.stream_thread.stop()
                    self.thermal_widget.set_unavailable()
            else:
                # First time - start only if available
                self.thermal_widget.rtsp_url = thermal_url
                if self.camera_availability.get('thermal', False):
                    self.thermal_widget.start_stream()
                else:
                    logger.info("Thermal camera not available - not starting stream")
                    self.thermal_widget.set_unavailable()

        # Daylight camera
        if hasattr(self, 'daylight_widget'):
            if hasattr(self.daylight_widget, 'stream_thread') and self.daylight_widget.stream_thread:
                if self.camera_availability.get('daylight', False):
                    self.daylight_widget.stream_thread.change_url(daylight_url)
                else:
                    logger.info("Stopping daylight camera stream - not available")
                    # Stop the existing stream thread
                    self.daylight_widget.stream_thread.stop()
                    self.daylight_widget.set_unavailable()
            else:
                self.daylight_widget.rtsp_url = daylight_url
                if self.camera_availability.get('daylight', False):
                    self.daylight_widget.start_stream()
                else:
                    logger.info("Daylight camera not available - not starting stream")
                    self.daylight_widget.set_unavailable()

        # SWIR camera
        if hasattr(self, 'swir_widget'):
            if hasattr(self.swir_widget, 'stream_thread') and self.swir_widget.stream_thread:
                if self.camera_availability.get('swir', False):
                    self.swir_widget.stream_thread.change_url(swir_url)
                else:
                    logger.info("Stopping SWIR camera stream - not available")
                    # Stop the existing stream thread
                    self.swir_widget.stream_thread.stop()
                    self.swir_widget.set_unavailable()
            else:
                self.swir_widget.rtsp_url = swir_url
                if self.camera_availability.get('swir', False):
                    self.swir_widget.start_stream()
                else:
                    logger.info("SWIR camera not available - not starting stream")
                    self.swir_widget.set_unavailable()

        # Count available cameras and rebuild layout
        available_count = sum(1 for v in self.camera_availability.values() if v)
        logger.info(f"Video streams updated: {available_count}/3 cameras available")

        # Log discovery status to connection log
        if available_count > 0:
            self.log_connection_event(f"✅ {available_count}/3 cameras available")
        else:
            self.log_connection_event("⚠️ No cameras available")

        # Rebuild the video layout based on available cameras
        self.rebuild_video_layout()

    def update_connection_status(self, connected: bool):
        """Update connection status indicator."""
        if connected:
            # Green "connected" text
            self.connection_indicator.setText("connected")
            self.connection_indicator.setStyleSheet("""
                font-size: 9pt;
                color: #44ff44;
                padding-left: 10px;
            """)
            self.connect_button.setText("Disconnect")
            self.ip_input.setEnabled(False)  # Disable IP changes while connected
            self.log_connection_event("✓ Connected to MK4 system")
        else:
            # Red "not connected" text
            self.connection_indicator.setText("not connected")
            self.connection_indicator.setStyleSheet("""
                font-size: 9pt;
                color: #ff4444;
                padding-left: 10px;
            """)
            self.connect_button.setText("Connect")
            self.ip_input.setEnabled(True)  # Enable IP changes when disconnected
            self.log_connection_event("✗ Disconnected from MK4 system")

    def log_connection_event(self, message: str):
        """Append a message to the connection log with auto-scroll."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.connection_log.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        cursor = self.connection_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.connection_log.setTextCursor(cursor)

    def update_component_status(self, target_ip: str):
        """Ping all components and update their status indicators (in background thread)."""
        logger.info(f"update_component_status called with target_ip={target_ip}")
        self.log_connection_event("Checking component status...")

        # Update Main Board IP to target IP
        self.component_status['Main Board']['ip'] = target_ip
        logger.debug(f"Main Board IP set to: {target_ip}")

        # Main board is connected (we're calling this after successful connection)
        logger.debug("Setting Main Board status to online (green)")
        self.on_component_status_update('Main Board', True)

        # Stop any existing status check thread
        if self.component_status_thread and self.component_status_thread.isRunning():
            logger.debug("Stopping existing component status thread")
            self.component_status_thread.wait()

        # Start background thread to SSH into main board and ping internal components
        logger.info(f"Starting SSH-based component status checks via {target_ip}")
        self.component_status_thread = ComponentStatusThread(self.component_status, target_ip)
        self.component_status_thread.status_update.connect(self.on_component_status_update)
        self.component_status_thread.check_complete.connect(self.on_component_check_complete)
        self.component_status_thread.start()
        logger.debug("Component status thread started")

    def on_component_status_update(self, component_name: str, is_online: bool):
        """Update a single component status indicator."""
        logger.debug(f"on_component_status_update: {component_name} = {'Online' if is_online else 'Offline'}")
        label = self.component_status[component_name]['label']

        if is_online:
            # Green dot - component responding
            label.setStyleSheet("""
                font-size: 14pt;
                color: #44ff44;
                padding: 0px;
            """)
            self.log_connection_event(f"{component_name}: Online")
        else:
            # Red dot - component not responding
            label.setStyleSheet("""
                font-size: 14pt;
                color: #ff4444;
                padding: 0px;
            """)
            self.log_connection_event(f"{component_name}: Offline")

    def on_component_check_complete(self):
        """Called when all component status checks are complete."""
        self.log_connection_event("Component status check complete")

    def stop_all_video_streams(self):
        """Stop all active video streams."""
        logger.info("Stopping all video streams...")

        # Stop thermal camera
        if hasattr(self, 'thermal_widget') and hasattr(self.thermal_widget, 'stream_thread'):
            if self.thermal_widget.stream_thread and self.thermal_widget.stream_thread.isRunning():
                self.thermal_widget.stream_thread.stop()
                self.thermal_widget.stream_thread.wait(2000)
                logger.info("Thermal camera stream stopped")

        # Stop daylight camera
        if hasattr(self, 'daylight_widget') and hasattr(self.daylight_widget, 'stream_thread'):
            if self.daylight_widget.stream_thread and self.daylight_widget.stream_thread.isRunning():
                self.daylight_widget.stream_thread.stop()
                self.daylight_widget.stream_thread.wait(2000)
                logger.info("Daylight camera stream stopped")

        # Stop SWIR camera
        if hasattr(self, 'swir_widget') and hasattr(self.swir_widget, 'stream_thread'):
            if self.swir_widget.stream_thread and self.swir_widget.stream_thread.isRunning():
                self.swir_widget.stream_thread.stop()
                self.swir_widget.stream_thread.wait(2000)
                logger.info("SWIR camera stream stopped")

        # Hide all video widgets
        self.thermal_widget.hide()
        self.daylight_widget.hide()
        self.swir_widget.hide()

        # Show placeholder message
        if self.no_cameras_label.parent() is None:
            self.video_grid.addWidget(self.no_cameras_label, 0, 0)
        self.no_cameras_label.show()

        self.log_connection_event("All video streams stopped")
        logger.info("All video streams stopped and hidden")

    def closeEvent(self, event):
        """Clean up video streams on close."""
        self.stop_all_video_streams()
        event.accept()
