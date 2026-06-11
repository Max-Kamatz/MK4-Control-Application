# MK4 Control Application

A professional GUI control application for the Silent Sentinel MK4 multi-sensor payload system, featuring real-time RTSP video streaming and gimbal control via the UP (Universal Protocol).

## Features

- **Multi-Stream Video Display**: View thermal, daylight, and SWIR camera feeds simultaneously
- **Gimbal Control**: Real-time pan/tilt control with position feedback
- **UP Protocol Support**: Full implementation of Universal Protocol v2.4.7
- **Network Communication**: TCP/UDP connectivity with automatic reconnection
- **Dark Theme UI**: Operator-optimized interface with minimal eye strain
- **Real-time Telemetry**: Live position feedback and status monitoring

## System Requirements

- Windows 10/11
- Python 3.10 or higher
- Network connectivity to MK4 system (192.168.1.100)

## Installation

### Option 1: Standalone Executable (Recommended for End Users)

1. **Download or receive** the `MK4Control_Package` folder
2. **Double-click** `MK4Control.exe` to launch
3. No installation or Python required!

### Option 2: Running from Source (For Developers)

1. **Clone or navigate to the project directory**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

## Building Standalone Executable

To create a single `.exe` file for distribution:

```bash
# Quick build (Windows)
build.bat

# Or manually
python build_exe.py
```

**Output**: `dist/MK4Control_Package/MK4Control.exe` (standalone, ~150-200 MB)

For detailed build instructions, see [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)

## Configuration

All system configuration is stored in `config/default_config.json`:

- **Network settings**: IP addresses, ports, timeouts
- **RTSP streams**: Camera URLs and labels
- **Gimbal parameters**: Pan/tilt ranges, command rates
- **UI settings**: Theme preferences, window title

### Default Configuration

- **Target IP**: 192.168.1.100
- **TCP Port (Pelco)**: 54000
- **UDP Telemetry Port**: 58000
- **UP Protocol Port**: 58004
- **RTSP Streams**:
  - Thermal: `rtsp://192.168.1.100:7031/Cam1Stream1`
  - Daylight: `rtsp://192.168.1.100:7031/Cam2Stream1`
  - SWIR: `rtsp://192.168.1.100:7031/Cam3Stream1`

## Usage

### Starting the Application

```bash
python main.py
```

### Video Streams Tab

- Displays three camera streams simultaneously (thermal, daylight, SWIR)
- Automatic reconnection on stream failure
- Color-coded status indicators:
  - 🟢 Green: Connected
  - 🟡 Yellow: Connecting/Buffering
  - 🔴 Red: Disconnected/Error

### Gimbal Control Tab

**Pan/Tilt Sliders**:
- Pan range: -180° to +180°
- Tilt range: -90° to +90°
- Real-time command transmission

**Position Display**:
- Commanded position (blue): Your input
- Actual position (green): Real-time feedback from gimbal

**Home Position Button**:
- Centers gimbal to (0°, 0°)

**Connection Controls**:
- Connect/Disconnect button
- Status indicator shows connection state

## Architecture

```
MK4ControlApp/
├── main.py                    # Application entry point
├── requirements.txt           # Dependencies
├── config/
│   ├── default_config.json    # System configuration
│   └── up_protocol_commands.json  # Protocol definitions
├── gui/
│   ├── main_window.py         # Main window with tabs
│   ├── tabs/
│   │   ├── video_tab.py       # Video display
│   │   └── control_tab.py     # Gimbal controls
│   └── widgets/
│       └── rtsp_video_widget.py  # Video player widget
├── network/
│   ├── up_protocol.py         # UP protocol implementation
│   ├── network_manager.py     # TCP/UDP client
│   └── network_thread.py      # Qt threading wrapper
├── models/
│   ├── gimbal_state.py        # State management
│   └── telemetry.py           # Telemetry data
└── utils/
    ├── logger.py              # Logging setup
    └── constants.py           # Configuration loader
```

## Threading Model

- **Main Thread**: GUI rendering and user input
- **Network Thread**: TCP/UDP communication (asyncio event loop)
- **Video Threads**: RTSP streaming (one per camera)

All threads communicate via PyQt signals for thread safety.

## UP Protocol Implementation

The application implements Universal Protocol v2.4.7 with the following features:

- **Message Format**:
  - Magic bytes: 0x5550
  - CRC16 checksum validation
  - Sequence numbering

- **Supported Commands**:
  - Pan/Tilt absolute positioning
  - Position query
  - Stop movement

- **Response Parsing**:
  - Position feedback
  - Status updates
  - Error handling

## Logging

All application activity is logged to:
- **Console**: INFO level and above
- **Log files**: `logs/mk4_control_YYYYMMDD_HHMMSS.log` (DEBUG level)

## Troubleshooting

### Video Streams Not Connecting

1. Verify network connectivity: `ping 192.168.1.100`
2. Check RTSP URLs in `config/default_config.json`
3. Ensure firewall allows RTSP traffic (port 7031)
4. Review logs in `logs/` directory

### Gimbal Not Responding

1. Check connection status indicator in Control tab
2. Verify UDP port 58004 is not blocked
3. Review network logs for command transmission
4. Ensure UP protocol configuration matches system firmware

### Application Crashes

1. Check `logs/` directory for error messages
2. Verify Python version: `python --version` (requires 3.10+)
3. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

## Development Status

### ✅ Completed (MVP)

- Project structure and configuration
- Dark theme UI with tabbed interface
- RTSP video streaming (OpenCV backend)
- Gimbal control interface (pan/tilt sliders)
- UP protocol message encoding/decoding
- Network layer (TCP/UDP with asyncio)
- PyQt threading integration
- Telemetry reception and display
- Automatic reconnection logic

### 🚧 Future Enhancements

- Quick functions tab (CLAHE, NUC, stabilization)
- Diagnostics tab with real-time plotting
- Payload power cycling controls
- Video recording and snapshot capture
- Gimbal position presets
- Keyboard shortcuts
- GStreamer backend for improved video performance

## Hardware Testing

To test with actual MK4 hardware:

1. Ensure system is powered and network-accessible
2. Verify IP address matches configuration (192.168.1.100)
3. Launch application: `python main.py`
4. Navigate to Video Streams tab to verify camera feeds
5. Navigate to Gimbal Control tab and click "Connect"
6. Test pan/tilt controls and observe gimbal movement
7. Verify position feedback updates in real-time

## License

Copyright © 2026 Silent Sentinel MK4 Control Application

## Support

For issues or questions, review the logs in the `logs/` directory and check the troubleshooting section above.
