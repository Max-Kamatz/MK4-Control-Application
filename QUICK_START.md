# MK4 Control Application - Quick Start Guide

## For End Users (Non-Technical)

### Running the Application

1. **Locate** the `MK4Control_Package` folder
2. **Double-click** `MK4Control.exe`
3. **Wait** for the application window to appear (~2-3 seconds)

### Using the Application

#### Video Streams Tab 📹
- View three camera feeds (Thermal, Daylight, SWIR)
- Streams connect automatically
- Status indicators:
  - 🟢 Green = Connected
  - 🟡 Yellow = Connecting
  - 🔴 Red = Disconnected

#### Gimbal Control Tab 🎮
1. **Click "Connect"** to establish connection to MK4 system
2. **Move sliders** to control pan (left/right) and tilt (up/down)
3. **Click "Home Position"** to center gimbal to (0°, 0°)
4. **Watch feedback** in "Position Feedback" section

### Troubleshooting

**Application won't start:**
- Install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- Check antivirus isn't blocking the .exe

**Can't connect to system:**
- Verify network cable is connected
- Ensure you can ping 192.168.1.100
- Check firewall settings

**Video streams not showing:**
- Connection to MK4 system required
- Check network connectivity
- Review logs in `logs/` folder

---

## For Developers

### Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run from source
python main.py

# Run tests
python test_up_protocol.py
```

### Building Executable

```bash
# Quick build
build.bat

# Or manually
python build_exe.py
```

**Output**: `dist/MK4Control_Package/MK4Control.exe`

### Project Structure

```
MK4 Control Application/
├── main.py                    # Entry point
├── build.bat                  # Build script (Windows)
├── build_exe.py              # PyInstaller build automation
├── config/                    # Configuration files
├── gui/                       # User interface code
├── network/                   # Network & protocol code
├── models/                    # Data models
└── utils/                     # Utilities & logging
```

### Key Files

- **Configuration**: `config/default_config.json`
- **Logs**: `logs/mk4_control_YYYYMMDD_HHMMSS.log`
- **Protocol**: `config/up_protocol_commands.json`

### Testing

```bash
# Protocol tests
python test_up_protocol.py

# Launch application (development mode)
python main.py
```

### Common Tasks

**Change network settings:**
- Edit `config/default_config.json`
- Modify `target_ip`, ports, or RTSP URLs

**View logs:**
- Check `logs/` directory
- Latest log file has newest timestamp

**Modify UI theme:**
- Edit `gui/main_window.py` → `apply_dark_theme()`

**Adjust protocol:**
- Edit `network/up_protocol.py`
- Update `config/up_protocol_commands.json`

---

## System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4 GB minimum, 8 GB recommended
- **Network**: Ethernet connection to MK4 system
- **Display**: 1280x720 minimum, 1920x1080 recommended

## Default Connection Settings

- **MK4 IP**: 192.168.1.100
- **TCP Port (Pelco)**: 54000
- **UDP Telemetry**: 58000
- **UP Protocol**: 58004

## Support

**Documentation:**
- `README.md` - Full user guide
- `BUILD_INSTRUCTIONS.md` - Build and deployment guide
- `PROJECT_STATUS.md` - Development status

**Logs Location:**
- `logs/mk4_control_YYYYMMDD_HHMMSS.log`

**Configuration:**
- `config/default_config.json`

---

## Quick Commands Cheat Sheet

| Task | Command |
|------|---------|
| Run application | `python main.py` |
| Build executable | `build.bat` |
| Run tests | `python test_up_protocol.py` |
| Install dependencies | `pip install -r requirements.txt` |
| Clean build | Delete `build/`, `dist/` folders |

---

**Version**: 0.1.0 (MVP)  
**Status**: Ready for hardware testing  
**Last Updated**: June 10, 2026
