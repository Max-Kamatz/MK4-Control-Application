"""
Network utility functions for connectivity checks.
"""

import socket
import subprocess
import platform
from utils.logger import setup_logger

logger = setup_logger()


def ping_host(host: str, timeout: int = 2) -> bool:
    """
    Ping a host to check if it's reachable.

    Args:
        host: IP address or hostname
        timeout: Timeout in seconds

    Returns:
        True if host responds to ping, False otherwise
    """
    try:
        # Use platform-specific ping command
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'

        command = ['ping', param, '1', timeout_param, str(timeout * 1000 if platform.system().lower() == 'windows' else timeout), host]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout + 1)

        return result.returncode == 0

    except Exception as e:
        logger.debug(f"Ping failed for {host}: {e}")
        return False


def check_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """
    Check if a TCP port is open on a host.

    Args:
        host: IP address or hostname
        port: Port number
        timeout: Connection timeout in seconds

    Returns:
        True if port is open, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0

    except Exception as e:
        logger.debug(f"Port check failed for {host}:{port}: {e}")
        return False


def check_rtsp_host_reachable(rtsp_url: str, timeout: float = 2.0) -> bool:
    """
    Check if the RTSP host is reachable (ping + port check).

    Args:
        rtsp_url: RTSP URL (e.g., rtsp://192.168.1.100:7031/Cam1Stream1)
        timeout: Timeout in seconds

    Returns:
        True if host is reachable, False otherwise
    """
    try:
        # Parse URL to extract host and port
        from urllib.parse import urlparse
        parsed = urlparse(rtsp_url)
        host = parsed.hostname
        port = parsed.port or 554  # Default RTSP port

        # First try ping
        if ping_host(host, timeout=int(timeout)):
            logger.debug(f"Host {host} is pingable")
            # Then check if RTSP port is open
            if check_port_open(host, port, timeout=timeout):
                logger.debug(f"RTSP port {port} is open on {host}")
                return True
            else:
                logger.debug(f"RTSP port {port} is closed on {host}, but host is pingable")
                return True  # Host is up, just port might be filtered

        logger.debug(f"Host {host} is not reachable")
        return False

    except Exception as e:
        logger.error(f"Error checking RTSP host reachability for {rtsp_url}: {e}")
        return False
