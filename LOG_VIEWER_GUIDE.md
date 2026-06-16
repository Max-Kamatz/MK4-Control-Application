# Real-Time Log Viewer Guide

## Accessing the Log Viewer

The application now includes a real-time log viewer to help diagnose connection issues and monitor application behavior.

### How to Open:

1. **Via Menu**: Click `Tools` → `📋 View Logs` in the menu bar
2. **Via Keyboard Shortcut**: Press `Ctrl+L` at any time
3. The status bar at the bottom shows: "Press Ctrl+L to view logs"

## Features

### Color-Coded Log Levels

- **Gray** - DEBUG: Detailed diagnostic information
- **Blue** - INFO: General informational messages
- **Orange** - WARNING: Warning messages
- **Red** - ERROR: Error messages
- **Dark Red** - CRITICAL: Critical error messages

### Controls

- **Auto-scroll checkbox**: Automatically scroll to the newest log entry (enabled by default)
- **Clear Logs button**: Clear all displayed logs
- **Close button**: Close the log viewer window

### Log Format

Each log entry shows:
```
HH:MM:SS [LEVEL   ] Logger - Message
```

Example:
```
15:42:30 [INFO    ] MK4Control - Attempting TCP connection to 192.168.1.100:54000
15:42:35 [ERROR   ] MK4Control - Connection timeout
```

## Troubleshooting with Log Viewer

### To Diagnose Connection Issues:

1. Open the log viewer (`Ctrl+L`) **before** attempting to connect
2. Enter your target IP address in the control tab
3. Click "Connect"
4. Watch the log viewer in real-time to see:
   - Connection attempts
   - Video stream initialization
   - Network errors
   - Thread operations
   - Any crash-related messages

### Common Log Patterns:

**Successful Connection:**
```
[INFO] Attempting TCP connection to 192.168.1.100:54000
[INFO] TCP connection established
[INFO] UDP telemetry socket bound to port 58000
[INFO] Connecting to RTSP stream: rtsp://...
[INFO] Successfully connected to: rtsp://...
```

**Connection Timeout:**
```
[INFO] Attempting TCP connection to 192.168.1.100:54000
[ERROR] Connection timeout to 192.168.1.100:54000
```

**Video Stream Issues:**
```
[WARNING] Failed to open RTSP stream: rtsp://...
[INFO] Connecting to RTSP stream: rtsp://... (retry)
```

## Tips

- Keep the log viewer open during testing to catch crash details
- The log viewer captures ALL application activity from the moment it's opened
- Logs are also saved to files in the `logs/` directory with timestamps
- You can have the log viewer open on a second monitor while operating the application
