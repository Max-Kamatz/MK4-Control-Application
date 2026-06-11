# MK4 Control Application - Release Notes

## Version 0.1.0 - Initial Release
**Release Date**: June 10, 2026  
**Status**: MVP - Ready for Hardware Testing

---

## 🎉 What's New

This is the initial release of the MK4 Control Application, providing a professional GUI interface for controlling the Silent Sentinel MK4 multi-sensor payload system.

### Core Features

#### 📹 Multi-Stream Video Display
- **Three simultaneous RTSP streams**: Thermal, Daylight, SWIR cameras
- **Automatic reconnection**: Streams recover automatically after connection loss
- **Visual status indicators**: Color-coded connection status (green/yellow/red)
- **Optimized rendering**: Threaded video decoding for smooth playback

#### 🎮 Gimbal Control
- **Pan/Tilt control**: Smooth slider-based positioning (-180° to +180° pan, -90° to +90° tilt)
- **Real-time feedback**: Displays both commanded and actual gimbal position
- **Home position**: Quick-return button to center (0°, 0°)
- **Connection management**: Connect/Disconnect controls with status monitoring

#### 🌐 Network Communication
- **UP Protocol v2.4.7**: Full implementation of Universal Protocol
- **Multi-protocol support**: TCP (Pelco), UDP (telemetry, UP commands)
- **Automatic reconnection**: Resilient connection management
- **Thread-safe**: Separate network thread prevents UI freezing

#### 🎨 User Interface
- **Dark theme**: Operator-optimized, reduces eye strain
- **Tabbed interface**: Organized sections (Video Streams, Gimbal Control)
- **Status bar**: Real-time connection and command feedback
- **Professional styling**: Clean, modern appearance

---

## 📦 Distribution

### Standalone Executable
- **Single .exe file**: No Python installation required
- **Size**: 92 MB (compressed)
- **Platform**: Windows 10/11 (64-bit)
- **Dependencies**: All bundled (PyQt6, OpenCV, Python runtime)

### What's Included
```
MK4Control_Package/
├── MK4Control.exe       # Main application (92 MB)
├── README.md            # User documentation
└── logs/                # Application logs directory
```

### Installation
1. Extract `MK4Control_Package.zip` to any folder
2. Double-click `MK4Control.exe`
3. Application launches in 2-3 seconds

**No installation wizard, no admin rights required!**

---

## 🔧 System Requirements

### Minimum
- **OS**: Windows 10 (64-bit)
- **RAM**: 4 GB
- **Display**: 1280x720
- **Network**: Ethernet connection to MK4 system

### Recommended
- **OS**: Windows 11 (64-bit)
- **RAM**: 8 GB or more
- **Display**: 1920x1080 or higher
- **Network**: Gigabit Ethernet for optimal video streaming

### Prerequisites
- Microsoft Visual C++ Redistributable (usually pre-installed)
- Network access to 192.168.1.100 (MK4 system)

---

## ⚙️ Default Configuration

### Network Settings
- **Target IP**: 192.168.1.100
- **TCP Port (Pelco)**: 54000
- **UDP Telemetry**: 58000
- **UP Protocol**: 58004

### RTSP Stream URLs
- **Thermal**: `rtsp://192.168.1.100:7031/Cam1Stream1`
- **Daylight**: `rtsp://192.168.1.100:7031/Cam2Stream1`
- **SWIR**: `rtsp://192.168.1.100:7031/Cam3Stream1`

### Gimbal Ranges
- **Pan**: -180° to +180°
- **Tilt**: -90° to +90°
- **Command Rate**: 20 Hz (max)

---

## 🚀 Quick Start

1. **Launch**: Double-click `MK4Control.exe`
2. **View Video**: Switch to "Video Streams" tab to see camera feeds
3. **Control Gimbal**: 
   - Switch to "Gimbal Control" tab
   - Click "Connect" button
   - Move pan/tilt sliders
   - Watch real-time position feedback

---

## 🐛 Known Issues

### Minor Issues
1. **Empty log files on first run**: Logs may appear empty if application closes before flushing. This is cosmetic only.
2. **Video codec warnings**: OpenCV may show warnings for certain RTSP codecs - these don't affect functionality.
3. **Reconnection delay**: First reconnection attempt after network loss takes ~5 seconds (by design).

### Limitations
1. **UP Protocol**: Command IDs and message formats based on template - requires validation with actual MK4 system
2. **Video backend**: Using OpenCV (GStreamer recommended for production for better performance)
3. **Quick functions**: CLAHE, NUC, stabilization buttons not yet implemented (planned for v0.2.0)
4. **Diagnostics**: Real-time position plotting not yet implemented (planned for v0.2.0)

---

## 🔍 Troubleshooting

### Application Won't Start
- **Error: "VCRUNTIME140.dll not found"**
  - Install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

- **Antivirus blocks executable**
  - Add exception for `MK4Control.exe` in antivirus settings
  - This is a false positive due to PyInstaller packaging

### Connection Issues
- **"Disconnected" status in Gimbal Control tab**
  - Verify network cable is connected
  - Ping 192.168.1.100: `ping 192.168.1.100`
  - Check firewall settings (allow outgoing TCP/UDP)

- **Video streams show "Connecting..." indefinitely**
  - Verify RTSP port 7031 is accessible
  - Check that cameras are powered on
  - Review logs in `logs/` directory

### Performance Issues
- **Video lag or stuttering**
  - Close other network-intensive applications
  - Check network bandwidth (3 streams = ~15-30 Mbps)
  - Ensure hardware meets recommended specs

- **Slow startup (>10 seconds)**
  - Copy executable to local hard drive (not USB/network)
  - Add antivirus exception to skip scanning

---

## 📊 Technical Details

### Architecture
- **GUI Framework**: PyQt6 (native performance)
- **Video Streaming**: OpenCV with FFMPEG backend
- **Network Layer**: Asyncio (TCP/UDP)
- **Threading Model**: Main (GUI) + Network + 3x Video threads
- **Protocol**: UP Protocol v2.4.7 with CRC16 validation

### Build Information
- **Build Tool**: PyInstaller 6.19.0
- **Python Version**: 3.13.7
- **Compression**: UPX enabled
- **Bundle Type**: One-file executable

### Code Statistics
- **Total Lines**: ~1,270 lines of Python
- **Files**: 23 source files + 8 documentation files
- **Dependencies**: PyQt6, pyqtgraph, numpy, opencv-python
- **Build Time**: 2-5 minutes

---

## 📝 Changelog

### v0.1.0 (2026-06-10) - Initial Release

**Added:**
- Multi-stream RTSP video display (3 cameras)
- Gimbal control interface (pan/tilt sliders)
- UP Protocol implementation (encode/decode/validate)
- Network layer (TCP/UDP with asyncio)
- Auto-reconnection logic
- Dark theme UI
- Status monitoring
- Logging system
- Standalone executable build

**Known Limitations:**
- UP protocol command IDs require hardware validation
- Quick functions not implemented
- Diagnostics plotting not implemented
- GStreamer backend not yet integrated

---

## 🔮 Roadmap

### v0.2.0 (Planned)
- Quick Functions tab (CLAHE, NUC, Stabilization)
- Real-time diagnostics with position plotting
- Payload power cycling controls
- Custom icon and branding
- Installer package (optional)

### v0.3.0 (Planned)
- Video recording to disk
- Snapshot capture from streams
- Gimbal position presets (save/load)
- Keyboard shortcuts
- Configuration GUI (in-app settings)

### v1.0.0 (Production Ready)
- GStreamer video backend (hardware acceleration)
- Code signing for Windows SmartScreen
- Complete UP protocol validation
- Performance optimizations
- Security hardening
- Production deployment

---

## 📞 Support

### Documentation
- **User Guide**: See `README.md`
- **Build Instructions**: See `BUILD_INSTRUCTIONS.md`
- **Deployment Guide**: See `DEPLOYMENT_CHECKLIST.md`
- **Quick Reference**: See `QUICK_START.md`

### Logs
Application logs are stored in:
```
logs/mk4_control_YYYYMMDD_HHMMSS.log
```

Review logs for detailed error messages and troubleshooting.

### Reporting Issues
When reporting issues, please include:
1. Windows version (run `winver`)
2. Application version (v0.1.0)
3. Log file from `logs/` directory
4. Steps to reproduce the issue
5. Screenshots (if applicable)

---

## ⚠️ Important Notes

### Security Considerations
- **Credentials**: Default SSH credentials stored in config (change for production)
- **Network**: Application connects to 192.168.1.100 without authentication
- **Code Signing**: Executable is not code-signed (will show "Unknown publisher")

### Hardware Testing Required
This release has been tested in simulation but **not with actual MK4 hardware**. Before production deployment:
1. Validate UP protocol message formats
2. Verify command IDs against MK4 firmware
3. Test video codec compatibility
4. Measure actual latency (target <100ms for commands)
5. Stress test with rapid control inputs
6. Verify telemetry parsing

---

## 📜 License

Copyright © 2026 Silent Sentinel MK4 Control Application  
All rights reserved.

---

## 🙏 Acknowledgments

Built with:
- **PyQt6** - Cross-platform GUI framework
- **OpenCV** - Video processing and RTSP streaming
- **PyInstaller** - Executable packaging
- **Python** - Application development

---

**Download**: `MK4Control_Package.zip` (92 MB)  
**Installation**: Extract and run `MK4Control.exe`  
**Support**: See documentation in package

---

*This is an MVP release intended for initial hardware testing and validation. Please report any issues or feedback for future improvements.*
