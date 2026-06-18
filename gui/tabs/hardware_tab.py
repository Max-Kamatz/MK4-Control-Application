"""
gui/tabs/hardware_tab.py
Hardware tab - displays USB device listings for each payload component.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QTextEdit, QPushButton, QScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor
from utils.logger import setup_logger

logger = setup_logger()


class USBDeviceQueryThread(QThread):
    """Background thread for querying USB devices via SSH."""
    device_listing_received = pyqtSignal(str, str)  # (device_name, usb_listing)
    query_complete = pyqtSignal()

    def __init__(self, devices: dict):
        """
        Initialize USB query thread.

        Args:
            devices: dict like {'MainBoard': '192.168.1.100', 'Daylight': '10.10.10.2', 'Thermal': '10.10.10.3'}
        """
        super().__init__()
        self.devices = devices
        self.ssh_user = "silentsentinel"
        self.ssh_pass = "Sentinel123"

    def run(self):
        logger.info("USBDeviceQueryThread: Starting USB device queries")

        try:
            import paramiko
        except ImportError:
            logger.error("paramiko library not installed. Install with: pip install paramiko")
            self.query_complete.emit()
            return

        # Get MainBoard IP (required for SSH hopping to internal devices)
        mainboard_ip = self.devices.get('MainBoard')
        if not mainboard_ip:
            logger.error("USBDeviceQueryThread: MainBoard IP not set, cannot query devices")
            self.query_complete.emit()
            return

        # Connect to MainBoard first (all queries go through this connection)
        logger.info(f"USBDeviceQueryThread: Connecting to MainBoard at {mainboard_ip}")
        ssh_mainboard = paramiko.SSHClient()
        ssh_mainboard.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh_mainboard.connect(
                mainboard_ip,
                username=self.ssh_user,
                password=self.ssh_pass,
                timeout=10,
                look_for_keys=False,
                allow_agent=False
            )
            logger.info(f"USBDeviceQueryThread: Connected to MainBoard at {mainboard_ip}")

            # Query each device
            for device_name, ip_address in self.devices.items():
                if not ip_address:
                    logger.warning(f"USBDeviceQueryThread: {device_name} has no IP address, skipping")
                    continue

                try:
                    if device_name == 'MainBoard':
                        # Query MainBoard directly (already connected)
                        logger.info(f"USBDeviceQueryThread: Querying {device_name} (local)")
                        stdin, stdout, stderr = ssh_mainboard.exec_command('ls -1 /dev/serial/by-id/ 2>/dev/null || echo "No serial devices found"', timeout=10)
                        exit_status = stdout.channel.recv_exit_status()
                        output = stdout.read().decode('utf-8', errors='ignore').strip()
                        error_output = stderr.read().decode('utf-8', errors='ignore').strip()

                    else:
                        # Query internal devices via SSH hop through MainBoard using paramiko tunneling
                        logger.info(f"USBDeviceQueryThread: Querying {device_name} at {ip_address} via MainBoard (SSH tunnel)")

                        # Create SSH tunnel through MainBoard
                        transport = ssh_mainboard.get_transport()
                        dest_addr = (ip_address, 22)
                        local_addr = ('127.0.0.1', 0)
                        channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)

                        # Create new SSH client using the tunnel
                        ssh_internal = paramiko.SSHClient()
                        ssh_internal.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh_internal.connect(
                            ip_address,
                            username=self.ssh_user,
                            password=self.ssh_pass,
                            sock=channel,
                            timeout=10,
                            look_for_keys=False,
                            allow_agent=False
                        )
                        logger.debug(f"USBDeviceQueryThread: SSH tunnel established to {device_name}")

                        # Execute ls /dev/serial/by-id on internal device
                        stdin, stdout, stderr = ssh_internal.exec_command('ls -1 /dev/serial/by-id/ 2>/dev/null || echo "No serial devices found"', timeout=5)
                        exit_status = stdout.channel.recv_exit_status()
                        output = stdout.read().decode('utf-8', errors='ignore').strip()
                        error_output = stderr.read().decode('utf-8', errors='ignore').strip()

                        ssh_internal.close()
                        logger.debug(f"USBDeviceQueryThread: Closed SSH tunnel to {device_name}")

                    logger.debug(f"USBDeviceQueryThread: {device_name} - exit_status={exit_status}, output_len={len(output)}")

                    if exit_status == 0 and output and 'No serial devices found' not in output:
                        logger.info(f"USBDeviceQueryThread: {device_name} - Retrieved USB listing")
                        self.device_listing_received.emit(device_name, output)
                    else:
                        # Show actual output for debugging
                        error_msg = f"Query failed (exit code: {exit_status})\n\n"
                        error_msg += "=== Command Output ===\n"
                        if output:
                            error_msg += output
                        else:
                            error_msg += "(no output)\n"

                        if error_output:
                            error_msg += "\n\n=== Error Output ===\n"
                            error_msg += error_output

                        logger.warning(f"USBDeviceQueryThread: {device_name} - {error_msg}")
                        self.device_listing_received.emit(device_name, error_msg)

                except Exception as e:
                    error_msg = f"Failed to query USB devices: {str(e)}"
                    logger.error(f"USBDeviceQueryThread: {device_name} - {error_msg}")
                    self.device_listing_received.emit(device_name, error_msg)

            ssh_mainboard.close()
            logger.info("USBDeviceQueryThread: Closed MainBoard connection")

        except Exception as e:
            error_msg = f"Failed to connect to MainBoard: {str(e)}"
            logger.error(f"USBDeviceQueryThread: {error_msg}")
            # Emit error for all devices
            for device_name in self.devices.keys():
                self.device_listing_received.emit(device_name, error_msg)

        logger.info("USBDeviceQueryThread: All USB queries complete")
        self.query_complete.emit()


class HardwareTab(QWidget):
    """Hardware tab - displays USB device information for each payload component."""

    def __init__(self, video_manager=None):
        super().__init__()
        self.video_manager = video_manager
        self.video_placeholder = None  # Will hold the video display
        self.usb_query_thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize the hardware tab UI."""
        main_layout = QHBoxLayout()  # Changed to horizontal to support video + content
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Hardware controls
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        # Header with refresh button
        header_layout = QHBoxLayout()
        header_label = QLabel("USB Device Listings")
        header_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        self.refresh_button = QPushButton("Refresh USB Devices")
        self.refresh_button.setStyleSheet("padding: 8px 16px; font-size: 10pt;")
        self.refresh_button.setEnabled(False)  # Disabled until connected
        self.refresh_button.clicked.connect(self.refresh_usb_devices)
        header_layout.addWidget(self.refresh_button)

        controls_layout.addLayout(header_layout)

        # Scroll area for device listings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # MainBoard Port Listing
        mainboard_group = QGroupBox("MainBoard Port Listing")
        mainboard_layout = QVBoxLayout()

        self.mainboard_output = QTextEdit()
        self.mainboard_output.setReadOnly(True)
        self.mainboard_output.setMinimumHeight(150)
        self.mainboard_output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #aaaaaa;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #555;
            }
        """)
        self.mainboard_output.append("Not connected - click 'Refresh USB Devices' after connecting")

        mainboard_layout.addWidget(self.mainboard_output)
        mainboard_group.setLayout(mainboard_layout)
        content_layout.addWidget(mainboard_group)

        # Daylight Port Listing
        daylight_group = QGroupBox("Daylight Port Listing")
        daylight_layout = QVBoxLayout()

        self.daylight_output = QTextEdit()
        self.daylight_output.setReadOnly(True)
        self.daylight_output.setMinimumHeight(150)
        self.daylight_output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #aaaaaa;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #555;
            }
        """)
        self.daylight_output.append("Not connected - click 'Refresh USB Devices' after connecting")

        daylight_layout.addWidget(self.daylight_output)
        daylight_group.setLayout(daylight_layout)
        content_layout.addWidget(daylight_group)

        # Thermal Port Listing
        thermal_group = QGroupBox("Thermal Port Listing")
        thermal_layout = QVBoxLayout()

        self.thermal_output = QTextEdit()
        self.thermal_output.setReadOnly(True)
        self.thermal_output.setMinimumHeight(150)
        self.thermal_output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #aaaaaa;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #555;
            }
        """)
        self.thermal_output.append("Not connected - click 'Refresh USB Devices' after connecting")

        thermal_layout.addWidget(self.thermal_output)
        thermal_group.setLayout(thermal_layout)
        content_layout.addWidget(thermal_group)

        # SWIR Port Listing
        swir_group = QGroupBox("SWIR Port Listing")
        swir_layout = QVBoxLayout()

        self.swir_output = QTextEdit()
        self.swir_output.setReadOnly(True)
        self.swir_output.setMinimumHeight(150)
        self.swir_output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #aaaaaa;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #555;
            }
        """)
        self.swir_output.append("Not connected - click 'Refresh USB Devices' after connecting")

        swir_layout.addWidget(self.swir_output)
        swir_group.setLayout(swir_layout)
        content_layout.addWidget(swir_group)

        # WL Illuminator Port Listing
        wl_illuminator_group = QGroupBox("WL Illuminator Port Listing")
        wl_illuminator_layout = QVBoxLayout()

        self.wl_illuminator_output = QTextEdit()
        self.wl_illuminator_output.setReadOnly(True)
        self.wl_illuminator_output.setMinimumHeight(150)
        self.wl_illuminator_output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #aaaaaa;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #555;
            }
        """)
        self.wl_illuminator_output.append("Not connected - click 'Refresh USB Devices' after connecting")

        wl_illuminator_layout.addWidget(self.wl_illuminator_output)
        wl_illuminator_group.setLayout(wl_illuminator_layout)
        content_layout.addWidget(wl_illuminator_group)

        # IR Illuminator Port Listing
        ir_illuminator_group = QGroupBox("IR Illuminator Port Listing")
        ir_illuminator_layout = QVBoxLayout()

        self.ir_illuminator_output = QTextEdit()
        self.ir_illuminator_output.setReadOnly(True)
        self.ir_illuminator_output.setMinimumHeight(150)
        self.ir_illuminator_output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #aaaaaa;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #555;
            }
        """)
        self.ir_illuminator_output.append("Not connected - click 'Refresh USB Devices' after connecting")

        ir_illuminator_layout.addWidget(self.ir_illuminator_output)
        ir_illuminator_group.setLayout(ir_illuminator_layout)
        content_layout.addWidget(ir_illuminator_group)

        # Speaker Port Listing
        speaker_group = QGroupBox("Speaker Port Listing")
        speaker_layout = QVBoxLayout()

        self.speaker_output = QTextEdit()
        self.speaker_output.setReadOnly(True)
        self.speaker_output.setMinimumHeight(150)
        self.speaker_output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #aaaaaa;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                border: 1px solid #555;
            }
        """)
        self.speaker_output.append("Not connected - click 'Refresh USB Devices' after connecting")

        speaker_layout.addWidget(self.speaker_output)
        speaker_group.setLayout(speaker_layout)
        content_layout.addWidget(speaker_group)

        content_layout.addStretch()

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)

        controls_layout.addWidget(scroll_area)

        # Create left widget container for controls
        left_widget = QWidget()
        left_widget.setFixedWidth(480)  # Match other tabs
        left_widget.setLayout(controls_layout)

        # Add controls to main layout (left side, fixed width)
        main_layout.addWidget(left_widget, 0)  # Fixed width (no stretch)

        # Right side: Video display placeholder
        self.video_placeholder = QWidget()
        self.video_placeholder.setObjectName("video_container")
        video_layout = QVBoxLayout()
        video_layout.setSpacing(0)
        video_layout.setContentsMargins(10, 10, 10, 10)
        self.video_placeholder.setLayout(video_layout)
        main_layout.addWidget(self.video_placeholder, 1)  # Video expands (stretch factor 1)

        self.setLayout(main_layout)
        logger.info("Hardware tab initialized")

    def refresh_usb_devices(self):
        """Trigger USB device query for all connected components."""
        logger.info("Hardware tab: Refreshing USB devices")

        # Get IP addresses from parent (will be set by main.py)
        if not hasattr(self, 'mainboard_ip') or not self.mainboard_ip:
            logger.warning("Hardware tab: MainBoard IP not set, cannot refresh")
            self.log_to_device("MainBoard", "Error: Not connected to system")
            return

        # Clear existing output
        self.mainboard_output.clear()
        self.daylight_output.clear()
        self.thermal_output.clear()
        self.swir_output.clear()
        self.wl_illuminator_output.clear()
        self.ir_illuminator_output.clear()
        self.speaker_output.clear()

        self.mainboard_output.append("Querying USB devices...")
        self.daylight_output.append("Querying USB devices...")
        self.thermal_output.append("Querying USB devices...")
        self.swir_output.append("Querying USB devices...")
        self.wl_illuminator_output.append("Querying USB devices...")
        self.ir_illuminator_output.append("Querying USB devices...")
        self.speaker_output.append("Querying USB devices...")

        # Stop any existing query thread
        if self.usb_query_thread and self.usb_query_thread.isRunning():
            logger.debug("Stopping existing USB query thread")
            self.usb_query_thread.wait()

        # Start background thread to query USB devices
        devices = {
            'MainBoard': self.mainboard_ip,
            'Thermal': '10.10.10.2',
            'Daylight': '10.10.10.3',
            'SWIR': '10.10.10.4',
            'WL Illuminator': '10.10.10.5',
            'IR Illuminator': '10.10.10.6',
            'Speaker': '10.10.10.7'
        }

        self.usb_query_thread = USBDeviceQueryThread(devices)
        self.usb_query_thread.device_listing_received.connect(self.on_device_listing_received)
        self.usb_query_thread.query_complete.connect(self.on_query_complete)
        self.usb_query_thread.start()

        self.refresh_button.setEnabled(False)  # Disable during query

    def on_device_listing_received(self, device_name: str, listing: str):
        """Handle USB device listing received from SSH query."""
        logger.info(f"Hardware tab: Received USB listing for {device_name}")
        self.log_to_device(device_name, listing)

    def on_query_complete(self):
        """Called when all USB queries are complete."""
        logger.info("Hardware tab: USB query complete")
        self.refresh_button.setEnabled(True)

    def log_to_device(self, device_name: str, message: str):
        """Log message to the appropriate device output window."""
        if device_name == "MainBoard":
            output_widget = self.mainboard_output
        elif device_name == "Daylight":
            output_widget = self.daylight_output
        elif device_name == "Thermal":
            output_widget = self.thermal_output
        elif device_name == "SWIR":
            output_widget = self.swir_output
        elif device_name == "WL Illuminator":
            output_widget = self.wl_illuminator_output
        elif device_name == "IR Illuminator":
            output_widget = self.ir_illuminator_output
        elif device_name == "Speaker":
            output_widget = self.speaker_output
        else:
            logger.warning(f"Unknown device name: {device_name}")
            return

        # Clear and set new content
        output_widget.clear()
        output_widget.append(message)

        # Auto-scroll to bottom
        cursor = output_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        output_widget.setTextCursor(cursor)

    def set_connection_status(self, connected: bool, mainboard_ip: str = None):
        """Update connection status and enable/disable refresh button."""
        if connected and mainboard_ip:
            self.mainboard_ip = mainboard_ip
            self.refresh_button.setEnabled(True)
            logger.info(f"Hardware tab: Connected to {mainboard_ip}")

            # Automatically query USB devices on connect
            self.refresh_usb_devices()
        else:
            self.mainboard_ip = None
            self.refresh_button.setEnabled(False)

            # Clear outputs
            self.mainboard_output.clear()
            self.daylight_output.clear()
            self.thermal_output.clear()
            self.swir_output.clear()
            self.wl_illuminator_output.clear()
            self.ir_illuminator_output.clear()
            self.speaker_output.clear()

            self.mainboard_output.append("Not connected - click 'Refresh USB Devices' after connecting")
            self.daylight_output.append("Not connected - click 'Refresh USB Devices' after connecting")
            self.thermal_output.append("Not connected - click 'Refresh USB Devices' after connecting")
            self.swir_output.append("Not connected - click 'Refresh USB Devices' after connecting")
            self.wl_illuminator_output.append("Not connected - click 'Refresh USB Devices' after connecting")
            self.ir_illuminator_output.append("Not connected - click 'Refresh USB Devices' after connecting")
            self.speaker_output.append("Not connected - click 'Refresh USB Devices' after connecting")

            logger.info("Hardware tab: Disconnected")

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
            logger.debug("Hardware tab: Video display reparented")
