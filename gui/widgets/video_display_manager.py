"""
gui/widgets/video_display_manager.py
Centralized video display manager - SINGLE instance manages all RTSP streams.
Video display can be overlaid on any tab.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from gui.widgets.rtsp_video_widget import RTSPVideoWidget
from utils.logger import setup_logger
from utils.constants import load_config

logger = setup_logger()


class VideoDisplayManager(QWidget):
    """
    Manages a single set of video stream widgets that can be displayed on any tab.

    This is a SINGLETON pattern - only ONE instance should exist in the application.
    The video display can be reparented to different tabs as needed.
    """

    # Signals
    camera_availability_changed = pyqtSignal(dict)  # Emits camera availability status

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.camera_availability = {}
        self.streams_started = False

        self.target_ip = None

        # Main layout for video grid
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(5)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Create video grid container with styling
        self.video_grid_widget = QWidget()
        self.video_grid_widget.setObjectName("video_grid")
        self.video_grid_widget.setStyleSheet("""
            QWidget#video_grid {
                background-color: #0f1218;
                border: 2px solid #4a6741;
                border-radius: 4px;
            }
        """)
        self.video_grid = QGridLayout()
        self.video_grid.setSpacing(10)
        self.video_grid_widget.setLayout(self.video_grid)
        self.main_layout.addWidget(self.video_grid_widget)

        # Create the 3 video widgets (but don't add to layout yet)
        thermal_config = self.config['rtsp_streams']['thermal']
        self.thermal_widget = RTSPVideoWidget(
            thermal_config['url'],
            thermal_config['label'],
            auto_start=False  # Never auto-start
        )
        self.thermal_widget.setParent(self.video_grid_widget)
        self.thermal_widget.hide()

        daylight_config = self.config['rtsp_streams']['daylight']
        self.daylight_widget = RTSPVideoWidget(
            daylight_config['url'],
            daylight_config['label'],
            auto_start=False
        )
        self.daylight_widget.setParent(self.video_grid_widget)
        self.daylight_widget.hide()

        swir_config = self.config['rtsp_streams']['swir']
        self.swir_widget = RTSPVideoWidget(
            swir_config['url'],
            swir_config['label'],
            auto_start=False
        )
        self.swir_widget.setParent(self.video_grid_widget)
        self.swir_widget.hide()

        # Placeholder message
        self.no_cameras_label = QLabel("Connect to a payload to view camera feeds")
        self.no_cameras_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_cameras_label.setStyleSheet("""
            font-size: 12pt;
            color: #a0a8b0;
            padding: 50px;
            background-color: transparent;
            border: none;
        """)
        self.video_grid.addWidget(self.no_cameras_label, 0, 0)

        # Apply styling to the main widget
        self.setObjectName("video_container")
        self.setStyleSheet("""
            QWidget#video_container {
                background-color: #0f1218;
            }
        """)

        self.setLayout(self.main_layout)
        logger.info("VideoDisplayManager initialized (singleton)")

    def update_camera_availability(self, availability: dict):
        """
        Update which cameras are available and rebuild the layout.

        Args:
            availability: dict like {'thermal': True, 'daylight': True, 'swir': False}
        """
        logger.info(f"Updating camera availability: {availability}")
        self.camera_availability = availability
        self.camera_availability_changed.emit(availability)
        self.rebuild_layout()

    def rebuild_layout(self):
        """
        Rebuild video grid layout based on discovered camera availability.
        Only shows cameras that passed discovery checks.
        """
        logger.info(f"Rebuilding video layout. Availability: {self.camera_availability}")

        # Clear existing layout
        while self.video_grid.count():
            item = self.video_grid.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.hide()

        # Hide all widgets initially
        self.thermal_widget.hide()
        self.daylight_widget.hide()
        self.swir_widget.hide()
        self.no_cameras_label.hide()

        # Get list of available cameras (only those that passed discovery)
        available_cameras = []
        if self.camera_availability.get('thermal', False):
            available_cameras.append(('Thermal', self.thermal_widget))
        if self.camera_availability.get('daylight', False):
            available_cameras.append(('Daylight', self.daylight_widget))
        if self.camera_availability.get('swir', False):
            available_cameras.append(('SWIR', self.swir_widget))

        num_cameras = len(available_cameras)
        logger.info(f"Available cameras after discovery: {num_cameras}")

        if num_cameras == 0:
            # No cameras - show message
            self.no_cameras_label.setText("No cameras available")
            self.video_grid.addWidget(self.no_cameras_label, 0, 0)
            self.no_cameras_label.show()
            logger.info("Layout: 0 cameras available - showing placeholder")

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

        elif num_cameras == 3:
            # Three cameras - 2x2 grid
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

    def start_streams(self, target_ip: str, availability: dict):
        """
        Start video streams for available cameras only.
        Only starts streams that passed discovery (ping + RTSP 5x retries).

        Args:
            target_ip: Target IP address
            availability: dict of which cameras are available (from discovery with retries)
        """
        logger.info(f"Starting video streams for {target_ip}")
        logger.info(f"Camera availability from discovery: {availability}")

        self.target_ip = target_ip

        # Update availability and rebuild layout (only shows available cameras)
        self.update_camera_availability(availability)

        # Build URLs
        thermal_url = f"rtsp://{target_ip}:7031/Cam1Stream1"
        daylight_url = f"rtsp://{target_ip}:7031/Cam2Stream1"
        swir_url = f"rtsp://{target_ip}:7031/Cam3Stream1"

        streams_started_count = 0

        # Start ONLY cameras that passed discovery
        if availability.get('thermal', False):
            self.thermal_widget.rtsp_url = thermal_url
            if hasattr(self.thermal_widget, 'stream_thread') and self.thermal_widget.stream_thread:
                self.thermal_widget.stream_thread.change_url(thermal_url)
            else:
                self.thermal_widget.start_stream()
            logger.info("✓ Thermal camera stream started")
            streams_started_count += 1
        else:
            logger.info("✗ Thermal camera not available - stream not started")

        if availability.get('daylight', False):
            self.daylight_widget.rtsp_url = daylight_url
            if hasattr(self.daylight_widget, 'stream_thread') and self.daylight_widget.stream_thread:
                self.daylight_widget.stream_thread.change_url(daylight_url)
            else:
                self.daylight_widget.start_stream()
            logger.info("✓ Daylight camera stream started")
            streams_started_count += 1
        else:
            logger.info("✗ Daylight camera not available - stream not started")

        if availability.get('swir', False):
            self.swir_widget.rtsp_url = swir_url
            if hasattr(self.swir_widget, 'stream_thread') and self.swir_widget.stream_thread:
                self.swir_widget.stream_thread.change_url(swir_url)
            else:
                self.swir_widget.start_stream()
            logger.info("✓ SWIR camera stream started")
            streams_started_count += 1
        else:
            logger.info("✗ SWIR camera not available - stream not started")

        self.streams_started = True
        logger.info(f"Video streams started: {streams_started_count}/3 cameras")

    def stop_streams(self):
        """
        Stop all video streams without blocking.

        IMPORTANT: Do NOT call wait() on threads - they may be blocked in OpenCV
        operations and will cause GUI hangs/crashes. Let threads terminate asynchronously.
        """
        logger.info("Stopping all video streams...")

        # Stop thermal camera thread
        if hasattr(self.thermal_widget, 'stream_thread') and self.thermal_widget.stream_thread:
            thread = self.thermal_widget.stream_thread
            if thread.isRunning():
                try:
                    # Disconnect signals first to prevent crashes from stale signal connections
                    thread.frame_ready.disconnect()
                    thread.status_changed.disconnect()
                except:
                    pass  # Already disconnected

                # Stop thread (non-blocking - let it terminate asynchronously)
                thread.stop()
                logger.info("Thermal camera stream stop signal sent")

        # Stop daylight camera thread
        if hasattr(self.daylight_widget, 'stream_thread') and self.daylight_widget.stream_thread:
            thread = self.daylight_widget.stream_thread
            if thread.isRunning():
                try:
                    thread.frame_ready.disconnect()
                    thread.status_changed.disconnect()
                except:
                    pass

                thread.stop()
                logger.info("Daylight camera stream stop signal sent")

        # Stop SWIR camera thread
        if hasattr(self.swir_widget, 'stream_thread') and self.swir_widget.stream_thread:
            thread = self.swir_widget.stream_thread
            if thread.isRunning():
                try:
                    thread.frame_ready.disconnect()
                    thread.status_changed.disconnect()
                except:
                    pass

                thread.stop()
                logger.info("SWIR camera stream stop signal sent")

        # Hide all widgets
        self.thermal_widget.hide()
        self.daylight_widget.hide()
        self.swir_widget.hide()

        # Show placeholder
        if self.no_cameras_label.parent() is None:
            self.video_grid.addWidget(self.no_cameras_label, 0, 0)
        self.no_cameras_label.show()

        self.streams_started = False
        self.target_ip = None
        self.camera_availability = {}

        logger.info("All video stream stop signals sent (threads terminating asynchronously)")

    def get_display_widget(self) -> QWidget:
        """
        Get the widget that should be embedded in tabs.
        This is self - the entire VideoDisplayManager widget.
        """
        return self

    def closeEvent(self, event):
        """Clean up on close."""
        self.stop_streams()
        event.accept()
