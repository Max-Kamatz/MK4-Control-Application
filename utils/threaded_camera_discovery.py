"""
Threaded camera discovery to prevent GUI blocking.
Discovers cameras once in background thread and shares results with all tabs.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict
from utils.camera_discovery import discover_cameras
from utils.logger import setup_logger

logger = setup_logger()


class CameraDiscoveryThread(QThread):
    """Background thread for camera discovery to avoid blocking GUI."""

    discovery_complete = pyqtSignal(dict)  # Emits camera_availability dict

    def __init__(self, ip_address: str, timeout: float = 3.0, retries: int = 5):
        super().__init__()
        self.ip_address = ip_address
        self.timeout = timeout
        self.retries = retries

    def run(self):
        """Run camera discovery in background thread."""
        try:
            logger.info(f"Starting background camera discovery for {self.ip_address}...")

            # Build camera configs
            camera_configs = {
                'thermal': {
                    'url': f"rtsp://{self.ip_address}:7031/Cam1Stream1",
                    'label': 'Thermal Camera'
                },
                'daylight': {
                    'url': f"rtsp://{self.ip_address}:7031/Cam2Stream1",
                    'label': 'Daylight Camera'
                },
                'swir': {
                    'url': f"rtsp://{self.ip_address}:7031/Cam3Stream1",
                    'label': 'SWIR Camera'
                }
            }

            # Discover cameras (blocking operation, but safe because we're in background thread)
            # Tests each camera with retries (ping + RTSP check)
            availability = discover_cameras(camera_configs, timeout=self.timeout, retries=self.retries)

            logger.info(f"Camera discovery complete for {self.ip_address}")

            # Emit results to GUI thread
            self.discovery_complete.emit(availability)

        except Exception as e:
            logger.error(f"Error during camera discovery: {e}")
            # Emit empty dict on error
            self.discovery_complete.emit({})
