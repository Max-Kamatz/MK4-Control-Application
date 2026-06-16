"""
utils/network_discovery.py
Network discovery utilities for detecting available payloads.
"""

import socket
import subprocess
import platform
from typing import List, Tuple
from utils.logger import setup_logger

logger = setup_logger()


def ping_host(ip_address: str, timeout: int = 1) -> bool:
    """
    Ping a host to check if it's reachable.

    Args:
        ip_address: IP address to ping
        timeout: Timeout in seconds (default: 1)

    Returns:
        True if host responds, False otherwise
    """
    try:
        # Platform-specific ping command
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'

        # Build command: ping -n 1 -w 1000 IP (Windows) or ping -c 1 -W 1 IP (Linux)
        command = ['ping', param, '1', timeout_param, str(timeout * 1000 if platform.system().lower() == 'windows' else timeout), ip_address]

        # Execute ping
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 1
        )

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        logger.debug(f"Ping timeout for {ip_address}")
        return False
    except Exception as e:
        logger.debug(f"Ping error for {ip_address}: {e}")
        return False


def check_port_open(ip_address: str, port: int, timeout: float = 1.0) -> bool:
    """
    Check if a TCP port is open on a host.

    Args:
        ip_address: IP address to check
        port: Port number
        timeout: Timeout in seconds (default: 1.0)

    Returns:
        True if port is open, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip_address, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.debug(f"Port check error for {ip_address}:{port}: {e}")
        return False


def discover_payload(ip_address: str) -> Tuple[bool, dict]:
    """
    Discover if a payload is available and what services are responding.

    Args:
        ip_address: IP address to check

    Returns:
        Tuple of (is_available, services_dict)
        services_dict contains: {'ping': bool, 'pelco': bool, 'rtsp': bool, 'up': bool}
    """
    services = {
        'ping': False,
        'pelco': False,  # TCP port 54000 (Pelco protocol - optional)
        'rtsp': False,   # TCP port 7031 (RTSP video)
        'up': False      # UDP port 34030 (EUP protocol)
    }

    # Check if host responds to ping
    logger.debug(f"Pinging {ip_address}...")
    services['ping'] = ping_host(ip_address, timeout=1)

    if not services['ping']:
        logger.debug(f"Host {ip_address} not responding to ping")
        return False, services

    # Check Pelco TCP control port (54000) - optional
    logger.debug(f"Checking Pelco TCP port 54000 on {ip_address}...")
    services['pelco'] = check_port_open(ip_address, 54000, timeout=1.0)

    # Check RTSP port (7031)
    logger.debug(f"Checking RTSP port 7031 on {ip_address}...")
    services['rtsp'] = check_port_open(ip_address, 7031, timeout=1.0)

    # Note: Can't easily check UDP port without sending a packet and waiting for response
    # For now, assume UP protocol is available if ping succeeds
    # A proper check would require sending a UP protocol command and waiting for response
    services['up'] = services['ping']  # Assume available if host responds

    is_available = services['ping'] and (services['pelco'] or services['rtsp'] or services['up'])

    if is_available:
        logger.info(f"Payload discovered at {ip_address}: Pelco={services['pelco']}, RTSP={services['rtsp']}, UP={services['up']}")
    else:
        logger.info(f"No payload found at {ip_address}")

    return is_available, services


def scan_subnet(base_ip: str, start: int = 1, end: int = 254) -> List[Tuple[str, dict]]:
    """
    Scan a subnet for available payloads.

    Args:
        base_ip: Base IP (e.g., "192.168.1")
        start: Starting host number (default: 1)
        end: Ending host number (default: 254)

    Returns:
        List of tuples (ip_address, services_dict) for discovered payloads
    """
    discovered = []

    logger.info(f"Scanning subnet {base_ip}.{start}-{end}...")

    for i in range(start, end + 1):
        ip = f"{base_ip}.{i}"
        is_available, services = discover_payload(ip)
        if is_available:
            discovered.append((ip, services))

    logger.info(f"Scan complete. Found {len(discovered)} payload(s)")
    return discovered
