# Speed Control Sliders Added

## Overview

Added continuous speed control sliders for Pan/Tilt and Zoom/Focus operations, providing finer control over gimbal and camera movements.

## Features Added

### 1. Pan/Tilt Speed Control

**UI:** Two horizontal sliders in the "Speed Control" group
- **Pan Speed**: -10.0 to +10.0 degrees/second
- **Tilt Speed**: -10.0 to +10.0 degrees/second

**Commands Sent:**
```
ID:N/Command/MotorControl/Pan/Speed:5.5
ID:N/Command/MotorControl/Tilt/Speed:-3.0
```

**Usage:**
- Move slider right: Positive speed (pan right/tilt up)
- Move slider left: Negative speed (pan left/tilt down)
- Center position (0): Stop movement
- Real-time label shows current speed value

### 2. Zoom/Focus Speed Control

**UI:** Two horizontal sliders in the "Speed Control" group
- **Zoom Speed**: -1.0 (zoom out) to +1.0 (zoom in)
- **Focus Speed**: -1.0 (near) to +1.0 (far)

**Commands Sent:**
```
ID:N/Command/Camera1/Lens/ZoomIn    (speed > 0)
ID:N/Command/Camera1/Lens/ZoomOut   (speed < 0)
ID:N/Command/Camera1/Lens/FocusFar  (speed > 0)
ID:N/Command/Camera1/Lens/FocusNear (speed < 0)
```

**Usage:**
- Continuous variable speed control
- Real-time label shows normalized speed (-1.0 to +1.0)
- Center position (0): No movement

## UI Layout

The Speed Control group appears between "Position Feedback" and "Home" button:

```
┌─────────────────────────────┐
│  Position Feedback          │
│  - Commanded: Pan/Tilt      │
│  - Actual: Pan/Tilt         │
└─────────────────────────────┘
┌─────────────────────────────┐
│  Speed Control              │
│  Pan Speed:  [ ═══╪═══ ]    │  ← NEW
│  Tilt Speed: [ ═══╪═══ ]    │  ← NEW
│  Zoom Speed: [ ═══╪═══ ]    │  ← NEW
│  Focus Speed:[ ═══╪═══ ]    │  ← NEW
└─────────────────────────────┘
┌─────────────────────────────┐
│  🏠 Home Position (0°, 0°)  │
└─────────────────────────────┘
```

## Technical Implementation

### Files Modified

1. **`gui/tabs/combined_control_tab.py`**
   - Added QSlider import
   - Added 4 new signals: `pan_speed_changed`, `tilt_speed_changed`, `zoom_speed_changed`, `focus_speed_changed`
   - Created Speed Control UI group with 4 sliders
   - Added handler methods for slider value changes
   - Real-time label updates showing current speed values

2. **`network/network_thread.py`**
   - Added `send_pan_speed()` method
   - Added `send_tilt_speed()` method
   - Both methods use asyncio to send commands without blocking GUI

3. **`network/network_manager.py`**
   - Added `send_pan_speed()` method
   - Added `send_tilt_speed()` method
   - Both use TCP if available, fall back to UDP
   - Call EUP protocol builders for speed commands

4. **`network/eup_protocol.py`**
   - Already had `build_pan_speed()` and `build_tilt_speed()` methods
   - Already had `build_zoom_command()` and `build_focus_command()` methods
   - No changes needed - all protocol support was already in place!

5. **`main.py`**
   - Connected speed control signals to network thread methods
   - All 4 sliders connected and functional

## Usage Examples

### Pan Right at 5 deg/s
1. Move Pan Speed slider to the right
2. Label shows: "5.0 °/s"
3. Command sent: `ID:X/Command/MotorControl/Pan/Speed:5.0`
4. Gimbal pans right continuously
5. Move slider to center to stop

### Zoom In Slowly
1. Move Zoom Speed slider slightly right
2. Label shows: "0.25"
3. Command sent: `ID:X/Command/Camera1/Lens/ZoomIn`
4. Camera zooms in slowly
5. Move slider to center to stop

### Tilt Down at Max Speed
1. Move Tilt Speed slider all the way left
2. Label shows: "-10.0 °/s"
3. Command sent: `ID:X/Command/MotorControl/Tilt/Speed:-10.0`
4. Gimbal tilts down at maximum speed
5. Move slider to center to stop

## Advantages Over Buttons

### Before (Buttons Only):
- ❌ Fixed on/off control
- ❌ No speed variation
- ❌ Have to hold button
- ❌ No visual feedback of speed

### After (Sliders):
- ✅ Continuous variable speed
- ✅ Set speed and let go
- ✅ Visual feedback with labeled values
- ✅ Fine control over movement rate
- ✅ Easy to stop (center position)

## Control Modes

### Trackpad Mode
- Quick positioning
- Direct position commands
- Good for coarse movements

### Speed Slider Mode
- Continuous scanning
- Variable speed control
- Good for smooth tracking
- Set-and-forget operation

### Combined Usage
- Use trackpad for initial positioning
- Use speed sliders for fine tracking
- Both can be used simultaneously

## Slider Specifications

| Control | Range | Units | Resolution | Center Value |
|---------|-------|-------|------------|--------------|
| Pan Speed | -10.0 to +10.0 | °/s | 0.1 °/s | 0.0 |
| Tilt Speed | -10.0 to +10.0 | °/s | 0.1 °/s | 0.0 |
| Zoom Speed | -1.0 to +1.0 | normalized | 0.01 | 0.0 |
| Focus Speed | -1.0 to +1.0 | normalized | 0.01 | 0.0 |

## EUP Protocol Commands Used

### Pan/Tilt Speed
```
ID:N/Command/MotorControl/Pan/Speed:X.X
ID:N/Command/MotorControl/Tilt/Speed:X.X
```
Where X.X is speed in degrees/second (positive or negative)

### Zoom Control
```
ID:N/Command/Camera1/Lens/ZoomIn
ID:N/Command/Camera1/Lens/ZoomOut
ID:N/Command/Camera1/Lens/ZoomStop
```

### Focus Control
```
ID:N/Command/Camera1/Lens/FocusFar
ID:N/Command/Camera1/Lens/FocusNear
ID:N/Command/Camera1/Lens/FocusStop
```

## Testing

1. **Start application**
2. **Connect to MK4** (192.168.1.81)
3. **Pan Speed Test:**
   - Move Pan Speed slider right
   - Observe gimbal pan right
   - Move slider left
   - Observe gimbal pan left
   - Center slider
   - Observe gimbal stop
4. **Tilt Speed Test:** (same as pan)
5. **Zoom Speed Test:**
   - Move Zoom slider right
   - Observe camera zoom in
6. **Focus Speed Test:**
   - Move Focus slider right
   - Observe camera focus far

## Future Enhancements

Possible improvements:
- [ ] Speed presets (slow/medium/fast buttons)
- [ ] Speed ramping (acceleration/deceleration)
- [ ] Speed limits based on gimbal capabilities
- [ ] Keyboard shortcuts for speed control
- [ ] Speed profiles (save/recall favorite speeds)
- [ ] Coordinated speed control (pan & tilt together)

---

**Status**: ✅ Speed control sliders implemented and ready to test
