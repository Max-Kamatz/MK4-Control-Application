# Trackpad Joystick Mode

## Overview

The PTZ trackpad now operates in **joystick mode** - the further you drag from the center, the faster the gimbal moves. This provides intuitive, proportional speed control.

## How It Works

### Joystick Behavior

```
        Tilt Up (Fast)
              ↑
              │
    Pan ←─────●─────→ Pan
    Left    Center   Right
    (Fast)          (Fast)
              │
              ↓
        Tilt Down (Fast)
```

**Distance from center = Speed:**
- Center position (●) = **0 speed** (stopped)
- Edge of trackpad = **Maximum speed**
- Anywhere between = **Proportional speed**

### Speed Ranges

- **Pan Speed**: 0 to ±20 degrees/second
- **Tilt Speed**: 0 to ±10 degrees/second

**Example:**
- Drag 25% from center right → Pan at 5 °/s (25% × 20)
- Drag 50% from center up → Tilt at 5 °/s (50% × 10)
- Drag 100% from center (edge) → Maximum speed

## Changes from Previous Behavior

### ❌ Before (Position Mode):
```
Trackpad position → Absolute gimbal position
- Drag right 50% → Send "Pan to 90°"
- Drag up 25% → Send "Tilt to 22.5°"
- Direct position control
- Conflicted with speed sliders
```

### ✅ After (Joystick Mode):
```
Trackpad position → Movement speed
- Drag right 50% → Send "Pan speed: 10 °/s"
- Drag up 25% → Send "Tilt speed: 2.5 °/s"  
- Continuous speed control
- Works with speed sliders
```

## Speed Control Integration

### Three Ways to Control Speed:

1. **Trackpad (Joystick)** - Dynamic, hands-on control
   - Hold and drag for continuous movement
   - Release to stop instantly
   - Best for: Active tracking, scanning

2. **Speed Sliders** - Set-and-forget control
   - Set speed and let go
   - Continuous movement at constant speed
   - Best for: Smooth panning, time-lapses

3. **Both Together** - Combined control
   - Set base speed with sliders
   - Use trackpad for quick adjustments
   - Trackpad overrides sliders while held

## Usage Examples

### Example 1: Quick Scan Right
```
1. Click center of trackpad
2. Drag slowly to the right (25% from center)
   → Gimbal pans right at 5 °/s
3. Hold position while gimbal moves
4. Release when done
   → Gimbal stops instantly
```

### Example 2: Fast Pan Left
```
1. Drag all the way to the left edge
   → Gimbal pans left at maximum speed (20 °/s)
2. Release to stop
```

### Example 3: Diagonal Movement
```
1. Drag up and to the right
   → Gimbal pans right AND tilts up simultaneously
   → Each axis proportional to distance from center
2. Release to stop both axes
```

### Example 4: Smooth Tracking
```
1. Start near center (slow speed)
2. Follow target by adjusting trackpad position
3. Move further from center as target speeds up
4. Return toward center as target slows
5. Release when target stops
```

## Commands Sent

### While Dragging:
```
ID:N/Command/MotorControl/Pan/Speed:10.5
ID:N/Command/MotorControl/Tilt/Speed:-5.2
```
(Sent continuously as you move the trackpad)

### On Release:
```
ID:N/Command/MotorControl/Pan/Speed:0
ID:N/Command/MotorControl/Tilt/Speed:0
```
(Immediately stops movement)

## UI Feedback

### Command Labels Update in Real-Time:
```
Commanded:
  Pan:  10.5 °/s    ← Updates while dragging
  Tilt: -5.2 °/s    ← Updates while dragging
```

When released:
```
Commanded:
  Pan:  0.0 °/s     ← Shows stopped
  Tilt: 0.0 °/s     ← Shows stopped
```

## Advantages of Joystick Mode

### ✅ Intuitive Control
- Natural hand-eye coordination
- Like a game controller or drone remote
- Distance = speed (familiar paradigm)

### ✅ Variable Speed
- Fine control near center (slow movements)
- Fast movements at edges
- Smooth transitions between speeds

### ✅ Instant Stop
- Release trackpad → immediate stop
- No need to click separate stop button
- Natural "let go to stop" behavior

### ✅ Works with Sliders
- Sliders set baseline speed
- Trackpad for dynamic adjustments
- No conflicts between controls

### ✅ Smooth Tracking
- Easy to follow moving targets
- Adjust speed on the fly
- Both axes controlled simultaneously

## Technical Implementation

### Code Flow:
```python
# Trackpad moved
on_trackpad_moved(pan=-0.5, tilt=0.25)  # Normalized position

# Calculate speeds
pan_speed = -0.5 × 20.0 = -10.0 °/s    # Pan left at 10 °/s
tilt_speed = 0.25 × 10.0 = 2.5 °/s     # Tilt up at 2.5 °/s

# Emit signals
pan_speed_changed.emit(-10.0)
tilt_speed_changed.emit(2.5)

# Network thread sends commands
send_pan_speed(-10.0)   → ID:X/Command/MotorControl/Pan/Speed:-10.0
send_tilt_speed(2.5)    → ID:X/Command/MotorControl/Tilt/Speed:2.5
```

### On Release:
```python
on_trackpad_released()

# Emit stop signals
pan_speed_changed.emit(0.0)
tilt_speed_changed.emit(0.0)

# Network thread sends stop
send_pan_speed(0.0)     → ID:X/Command/MotorControl/Pan/Speed:0
send_tilt_speed(0.0)    → ID:X/Command/MotorControl/Tilt/Speed:0
```

## Files Modified

1. **`gui/tabs/combined_control_tab.py`**
   - `on_trackpad_moved()`: Changed from position to speed calculation
   - `on_trackpad_released()`: Now sends speed=0 instead of stop command
   - Emits `pan_speed_changed` and `tilt_speed_changed` signals

2. **`main.py`**
   - Removed old `handle_trackpad_pantilt()` function
   - Removed `pan_tilt_command` signal connection
   - Trackpad now uses speed control signals (already connected)

## Comparison with Other Controls

| Control Method | Mode | Best For | Stop Method |
|----------------|------|----------|-------------|
| **Trackpad** | Joystick (speed) | Dynamic tracking | Release trackpad |
| **Speed Sliders** | Continuous (speed) | Smooth scanning | Center slider |
| **Zoom/Focus Buttons** | Momentary (direction) | Quick adjustments | Release button |
| **Home Button** | Absolute (position) | Return to origin | N/A |

## Tips for Operators

1. **Start Slow**: Begin near center for fine control
2. **Release to Stop**: Let go of trackpad for instant stop
3. **Practice Diagonals**: Get comfortable with 2-axis movement
4. **Use Sliders for Base**: Set rough speed with sliders, fine-tune with trackpad
5. **Watch Labels**: Real-time speed display helps gauge movement rate

## Future Enhancements

Possible improvements:
- [ ] Adjustable max speed (user preference)
- [ ] Dead zone size adjustment
- [ ] Speed curve (linear vs exponential)
- [ ] Visual speed indicator on trackpad
- [ ] Haptic feedback (if hardware supports)
- [ ] Speed limiting based on gimbal mode

---

**Status**: ✅ Trackpad joystick mode implemented and ready to test
