"""
gui/tabs/connection_tab.py
Connection tab - handles network connection, discovery, and component status.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QGridLayout, QPushButton, QLineEdit, QTextEdit, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QTextCursor
from utils.constants import load_config
from utils.logger import setup_logger
from utils.network_discovery import discover_payload

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


class ConnectionTab(QWidget):
    """Connection tab - handles network connection, discovery, and component status."""

    # Signals
    connection_toggle = pyqtSignal()
    home_requested = pyqtSignal()

    def __init__(self, video_manager=None):
        super().__init__()
        self.config = load_config()
        self.discovery_thread = None
        self.component_status_thread = None
        self.payload_available = False
        self.video_manager = video_manager
        self.video_placeholder = None  # Will hold the shared video display
        self.init_ui()

    def init_ui(self):
        """Initialize the connection tab UI with left settings panel and right video section."""
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Connection settings (fixed width, scrollable)
        left_widget = self.create_settings_section()

        # Right side: Video streams (expands to fill space)
        right_widget = self.create_video_section()

        # Use simple horizontal layout - settings panel has fixed width, video expands
        main_layout.addWidget(left_widget, 0)   # Settings panel fixed width (no stretch)
        main_layout.addWidget(right_widget, 1)  # Video expands (stretch factor 1)

        self.setLayout(main_layout)
        logger.info("Connection tab initialized")

    def create_settings_section(self) -> QWidget:
        """Create left settings panel with scrollable content."""
        # Container widget with fixed width
        container = QWidget()
        container.setFixedWidth(480)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        # Content widget inside scroll area
        content_widget = QWidget()
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
        component_status_group = QGroupBox("Status")
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

        component_status_group.setLayout(status_layout)
        layout.addWidget(component_status_group)

        # System Information group
        system_info_group = QGroupBox("System Information")
        system_info_layout = QGridLayout()
        system_info_layout.setSpacing(8)

        # NexOS Version
        version_label = QLabel("NexOS Version:")
        version_label.setStyleSheet("font-size: 9pt;")
        system_info_layout.addWidget(version_label, 0, 0)

        self.nexos_version_value = QLabel("—")
        self.nexos_version_value.setStyleSheet("font-size: 9pt; color: #aaaaaa;")
        self.nexos_version_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        system_info_layout.addWidget(self.nexos_version_value, 0, 1)

        # Mainboard Serial
        serial_label = QLabel("Mainboard Serial:")
        serial_label.setStyleSheet("font-size: 9pt;")
        system_info_layout.addWidget(serial_label, 1, 0)

        self.mainboard_serial_value = QLabel("—")
        self.mainboard_serial_value.setStyleSheet("font-size: 9pt; color: #aaaaaa;")
        self.mainboard_serial_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        system_info_layout.addWidget(self.mainboard_serial_value, 1, 1)

        # Tracking Status
        tracking_label = QLabel("Tracking:")
        tracking_label.setStyleSheet("font-size: 9pt;")
        system_info_layout.addWidget(tracking_label, 2, 0)

        self.tracking_status_value = QLabel("—")
        self.tracking_status_value.setStyleSheet("font-size: 9pt; color: #aaaaaa;")
        system_info_layout.addWidget(self.tracking_status_value, 2, 1)

        system_info_group.setLayout(system_info_layout)
        layout.addWidget(system_info_group)

        layout.addStretch()

        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)

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

    def get_target_ip(self) -> str:
        """Get the current target IP from the input field."""
        return self.ip_input.text().strip()

    def log_connection_event(self, message: str):
        """Append a message to the connection log with auto-scroll."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.connection_log.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        cursor = self.connection_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.connection_log.setTextCursor(cursor)

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
            self.log_connection_event("Connected to MK4 system")
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
            self.clear_system_info()  # Clear system information on disconnect
            self.log_connection_event("Disconnected from MK4 system")

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

    def update_system_info(self, nexos_version: str = None, mainboard_serial: str = None, tracking_status: str = None):
        """Update system information fields."""
        if nexos_version is not None:
            self.nexos_version_value.setText(nexos_version)
            logger.info(f"NexOS Version: {nexos_version}")

        if mainboard_serial is not None:
            self.mainboard_serial_value.setText(mainboard_serial)
            logger.info(f"Mainboard Serial: {mainboard_serial}")

        if tracking_status is not None:
            # Color code tracking status
            if tracking_status.lower() == "on":
                self.tracking_status_value.setText(tracking_status)
                self.tracking_status_value.setStyleSheet("font-size: 9pt; color: #44ff44;")  # Green
            else:
                self.tracking_status_value.setText(tracking_status)
                self.tracking_status_value.setStyleSheet("font-size: 9pt; color: #aaaaaa;")  # Gray
            logger.info(f"Tracking Status: {tracking_status}")

    def clear_system_info(self):
        """Clear system information fields on disconnect."""
        self.nexos_version_value.setText("—")
        self.nexos_version_value.setStyleSheet("font-size: 9pt; color: #aaaaaa;")
        self.mainboard_serial_value.setText("—")
        self.tracking_status_value.setText("—")
        self.tracking_status_value.setStyleSheet("font-size: 9pt; color: #aaaaaa;")




