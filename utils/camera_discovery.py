"""
utils/camera_discovery.py
Camera discovery utilities for detecting available RTSP streams.
"""

import socket
from typing import Dict, List
from urllib.parse import urlparse
from utils.logger import setup_logger
import cv2

logger = setup_logger()


def check_rtsp_available(rtsp_url: str, timeout: float = 2.0) -> bool:
    """
    Check if an RTSP stream is available by attempting to open it with OpenCV.

    Args:
        rtsp_url: Full RTSP URL (e.g., rtsp://192.168.1.100:7031/Cam1Stream1)
        timeout: Connection timeout in seconds

    Returns:
        True if RTSP stream can be opened, False otherwise
    """
    try:
        # Try to open the RTSP stream with OpenCV
        # This will verify the specific stream path exists, not just the port
        logger.debug(f"Testing RTSP stream: {rtsp_url}")

        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, int(timeout * 1000))
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, int(timeout * 1000))

        # Check if stream opened successfully
        is_opened = cap.isOpened()

        # Clean up
        cap.release()

        if is_opened:
            logger.info(f"RTSP stream available: {rtsp_url}")
            return True
        else:
            logger.warning(f"RTSP stream not available: {rtsp_url}")
            return False

    except Exception as e:
        logger.error(f"Error checking RTSP availability for {rtsp_url}: {e}")
        return False


def discover_cameras(camera_configs: Dict[str, Dict[str, str]], timeout: float = 2.0) -> Dict[str, bool]:
    """
    Discover which cameras are available from a configuration dictionary.

    Args:
        camera_configs: Dictionary of camera configs, e.g.,
            {'thermal': {'url': 'rtsp://...', 'label': '...'}, ...}
        timeout: Connection timeout per camera in seconds

    Returns:
        Dictionary mapping camera names to availability status
        e.g., {'thermal': True, 'daylight': True, 'swir': False}
    """
    availability = {}

    logger.info(f"Discovering cameras from {len(camera_configs)} configurations...")

    for camera_name, config in camera_configs.items():
        rtsp_url = config.get('url')
        if not rtsp_url:
            logger.warning(f"No URL found for camera '{camera_name}'")
            availability[camera_name] = False
            continue

        logger.debug(f"Checking camera '{camera_name}' at {rtsp_url}")
        availability[camera_name] = check_rtsp_available(rtsp_url, timeout)

    available_count = sum(1 for v in availability.values() if v)
    logger.info(f"Camera discovery complete: {available_count}/{len(camera_configs)} available")

    return availability


def get_available_camera_urls(camera_configs: Dict[str, Dict[str, str]],
                              availability: Dict[str, bool]) -> List[str]:
    """
    Get list of RTSP URLs for available cameras only.

    Args:
        camera_configs: Dictionary of camera configurations
        availability: Dictionary of camera availability (from discover_cameras)

    Returns:
        List of RTSP URLs for cameras that are available
    """
    available_urls = []

    for camera_name, is_available in availability.items():
        if is_available and camera_name in camera_configs:
            url = camera_configs[camera_name].get('url')
            if url:
                available_urls.append(url)

    return available_urls
