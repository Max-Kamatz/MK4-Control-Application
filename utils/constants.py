import json
import sys
import os
from pathlib import Path
from typing import Dict, Any

def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except Exception:
        # Running in normal Python environment
        base_path = Path(__file__).parent.parent

    return base_path / relative_path

def load_config(config_path: str = "config/default_config.json") -> Dict[str, Any]:
    config_file = get_resource_path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    with open(config_file, 'r') as f:
        return json.load(f)

TARGET_IP = "192.168.1.100"
TCP_PELCO_PORT = 54000
UDP_TELEMETRY_PORT = 58000
UP_PROTOCOL_PORT = 58004

RTSP_THERMAL = "rtsp://192.168.1.100:7031/Cam1Stream1"
RTSP_DAYLIGHT = "rtsp://192.168.1.100:7031/Cam2Stream1"
RTSP_SWIR = "rtsp://192.168.1.100:7031/Cam3Stream1"

SSH_USER = "silentsentinel"
SSH_PASS = "Sentinel123"

PAN_MIN = -180
PAN_MAX = 180
TILT_MIN = -90
TILT_MAX = 90
