# Root Cause: SWIR Camera Widget Visibility Issue

## The Real Problem

The SWIR camera widget was appearing even when the camera wasn't actually available because **camera discovery was incorrectly reporting all cameras as available**.

### Evidence from Logs

From `logs/mk4_control_20260616_111355.log`:

```
Line 24: INFO - RTSP stream available: rtsp://192.168.1.81:7031/Cam3Stream1
Line 28: INFO -   Swir: ✓ Available
Line 38: INFO - Layout: 3 cameras (Thermal, Daylight, SWIR) - 2x2 grid

BUT THEN:

Line 41: WARNING - Failed to open RTSP stream: rtsp://192.168.1.81:7031/Cam3Stream1
Line 46: WARNING - Failed to open RTSP stream: rtsp://192.168.1.81:7031/Cam3Stream1
... (repeated failures every 5 seconds)
```

**The discovery said SWIR was available, but the actual stream failed to connect!**

## Root Cause Analysis

### The Flawed Discovery Method

`utils/camera_discovery.py` was using a **port check** instead of a **stream check**:

```python
# OLD CODE (WRONG):
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(timeout)
result = sock.connect_ex((host, port))  # Only checks if port 7031 is open!
```

### Why This Failed

All three RTSP cameras share the **same server and port**:
- **Thermal**: `rtsp://192.168.1.81:7031/Cam1Stream1`
- **Daylight**: `rtsp://192.168.1.81:7031/Cam2Stream1`
- **SWIR**: `rtsp://192.168.1.81:7031/Cam3Stream1`

When checking if SWIR was available, the old code only checked:
- ✅ Can I connect to port 7031? **YES** (the RTSP server is running)
- ❌ Does `/Cam3Stream1` actually exist? **NOT CHECKED**

Result: Discovery said "SWIR available" → GUI showed 3-camera layout → SWIR widget visible → Stream fails repeatedly

## The Solution

### New Discovery Method

Modified `utils/camera_discovery.py` to use **OpenCV to actually open the stream**:

```python
# NEW CODE (CORRECT):
cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, int(timeout * 1000))
cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, int(timeout * 1000))

is_opened = cap.isOpened()  # Checks if the specific stream path exists!
cap.release()
```

### Why This Works

Now the discovery:
1. ✅ Connects to the RTSP server (port 7031)
2. ✅ Sends RTSP DESCRIBE for the specific stream path (`/Cam3Stream1`)
3. ✅ Returns TRUE only if the stream actually exists and can be opened

## Expected Behavior After Fix

### Before Fix:
```
Discovery: Thermal ✓, Daylight ✓, SWIR ✓ (WRONG - port check only)
Layout: 3-camera grid (2x2)
SWIR Widget: Visible, showing "Connecting..." repeatedly failing
```

### After Fix:
```
Discovery: Thermal ✓, Daylight ✓, SWIR ✗ (CORRECT - stream doesn't exist)
Layout: 2-camera side-by-side
SWIR Widget: Hidden completely
```

## Testing the Fix

### Test Case 1: SWIR Not Connected (Current Scenario)

**Steps:**
1. Start application
2. Enter IP: `192.168.1.81`
3. Click "Connect"
4. Wait for camera discovery (~3-9 seconds)

**Expected Result:**
- Log shows: `RTSP stream not available: rtsp://192.168.1.81:7031/Cam3Stream1`
- Log shows: `Swir: ✗ Not available`
- Log shows: `Layout: 2 cameras (Thermal, Daylight) - side by side`
- GUI shows: Only 2 camera windows (Thermal left, Daylight right)
- SWIR widget: **Completely hidden**

### Test Case 2: All Cameras Available

With a payload that has SWIR connected:

**Expected Result:**
- Log shows all 3 streams available
- Log shows: `Layout: 3 cameras (Thermal, Daylight, SWIR) - 2x2 grid`
- GUI shows: 3 camera windows with live video

## Technical Details

### Files Modified

1. **`utils/camera_discovery.py`**: 
   - `check_rtsp_available()`: Changed from socket port check to OpenCV stream open
   - Added `import cv2`
   - Increased robustness by checking actual stream availability

2. **`gui/tabs/combined_control_tab.py`**:
   - Increased discovery timeout from 2.0 to 3.0 seconds (OpenCV needs more time)
   - Updated comment to reflect new behavior

### Performance Impact

- **Before**: ~2-6 seconds (port checks are fast)
- **After**: ~3-9 seconds (stream open is slower but more accurate)
- **Trade-off**: Worth it! Better to wait a few extra seconds than show incorrect layout

### Why OpenCV Instead of RTSP Protocol?

We could implement a raw RTSP DESCRIBE request, but:
- ✅ OpenCV is already a dependency
- ✅ Uses the same code path as actual streaming
- ✅ If OpenCV can open it in discovery, it will work for streaming
- ✅ Simpler implementation

## Related Issues Fixed

This also fixes:
- **Resource waste**: No more continuous failed connection attempts for non-existent streams
- **Confusing UI**: No more empty camera windows
- **Log spam**: No more repeated "Failed to open RTSP stream" warnings

## Future Enhancements

Possible improvements:
- **Parallel discovery**: Check all 3 cameras simultaneously (currently sequential)
- **Cache results**: Remember discovery results to avoid re-checking on reconnect
- **Manual override**: Let user manually disable/enable cameras regardless of discovery
