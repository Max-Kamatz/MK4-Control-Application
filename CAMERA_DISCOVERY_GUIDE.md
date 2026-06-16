# Camera Discovery Feature Guide

## Overview

The application now automatically discovers which cameras are connected to the payload **before** attempting to stream. This prevents wasted resources trying to connect to cameras that aren't there (like an unconnected SWIR camera).

## How It Works

### Automatic Discovery on Connection

When you click **"Connect"**:

1. ✅ **Payload Discovery** - Checks if the host is reachable
2. ✅ **TCP Connection** - Establishes control connection (UDP for UP Protocol)
3. ✅ **Camera Discovery** - Tests each RTSP stream endpoint (2 seconds per camera)
4. ✅ **Selective Streaming** - Only starts streams for **available** cameras

### Discovery Process

For each camera (Thermal, Daylight, SWIR), the application:
- Attempts to connect to the RTSP port (7031)
- Times out after 2 seconds if unavailable
- Logs the availability status

**Total discovery time**: ~2-6 seconds (depending on how many cameras respond)

## Visual Indicators

### Available Camera
```
● Connected (Green)
[Live video feed displayed]
```

### Unavailable Camera
```
● Camera Not Available (Gray)

Camera Not Available

This camera is not connected to the payload.
```

## Benefits

### Before Camera Discovery:
- ❌ All 3 cameras tried to connect regardless
- ❌ SWIR camera would timeout repeatedly (15-30 sec each attempt)
- ❌ Wasted bandwidth and CPU on dead connections
- ❌ Continuous reconnection attempts in background

### After Camera Discovery:
- ✅ Only available cameras attempt connection
- ✅ Fast discovery (2 sec per camera)
- ✅ Clear visual feedback
- ✅ No wasted resources
- ✅ No continuous failed attempts

## Example Scenarios

### Scenario 1: All Cameras Connected
```
Thermal:  ✓ Available  → Connects and streams
Daylight: ✓ Available  → Connects and streams
SWIR:     ✓ Available  → Connects and streams

Result: 3/3 cameras available
```

### Scenario 2: SWIR Not Connected (Common)
```
Thermal:  ✓ Available  → Connects and streams
Daylight: ✓ Available  → Connects and streams
SWIR:     ✗ Not available → Shows "Camera Not Available"

Result: 2/3 cameras available
```

### Scenario 3: Only One Camera
```
Thermal:  ✓ Available  → Connects and streams
Daylight: ✗ Not available → Shows "Camera Not Available"
SWIR:     ✗ Not available → Shows "Camera Not Available"

Result: 1/3 cameras available
```

## Log Messages

Watch the log viewer (Ctrl+L) to see discovery in action:

```
[INFO] Discovering cameras at 192.168.1.81...
[INFO] RTSP stream available: rtsp://192.168.1.81:7031/Cam1Stream1
[INFO]   Thermal: ✓ Available
[INFO] RTSP stream available: rtsp://192.168.1.81:7031/Cam2Stream1
[INFO]   Daylight: ✓ Available
[WARNING] RTSP stream not available: rtsp://192.168.1.81:7031/Cam3Stream1
[INFO]   Swir: ✗ Not available
[INFO] SWIR camera not available - not starting stream
[INFO] Video streams updated: 2/3 cameras available
```

## Technical Details

### Discovery Method
- Tests TCP connection to RTSP port (7031)
- Does NOT attempt full RTSP handshake (just port check)
- Fast and lightweight

### Timeout Settings
- **Per-camera timeout**: 2 seconds
- **Total discovery**: ~6 seconds worst case (3 cameras × 2 sec)
- **Best case**: Faster if cameras respond quickly

### Camera URLs
All cameras share the same IP but different stream paths:
- **Thermal**: `rtsp://[IP]:7031/Cam1Stream1`
- **Daylight**: `rtsp://[IP]:7031/Cam2Stream1`
- **SWIR**: `rtsp://[IP]:7031/Cam3Stream1`

## Future Enhancements

Possible improvements:
- **Retry button** for unavailable cameras
- **Manual camera enable/disable** toggles
- **Parallel discovery** (check all 3 simultaneously for faster results)
- **Periodic rediscovery** (check for cameras that come online later)

## Troubleshooting

### All Cameras Show "Not Available"
- Check network connectivity
- Verify RTSP port 7031 is open
- Confirm cameras are powered on
- Use network discovery (🔍 Check) to verify payload is reachable

### Camera Shows Available But No Video
- Camera may have responded to port check but RTSP stream isn't working
- Check codec compatibility
- Review logs for RTSP-specific errors

### Discovery Takes Too Long
- Normal: 2-6 seconds total
- If longer, check network latency
- Consider reducing timeout (currently 2 sec per camera)
