# Directional Arrow Buttons Added

## Overview

Added directional arrow buttons (▲ ▼ ◀ ▶) around the trackpad that use the speed slider settings for precise, one-axis movements.

## Layout

```
        ▲ Up
         
    ◀  ●  ▶
    Left  Right
    
        ▼ Down
```

The arrows are positioned around the trackpad:
- **Up (▲)**: Above trackpad
- **Down (▼)**: Below trackpad
- **Left (◀)**: Left of trackpad
- **Right (▶)**: Right of trackpad

## How They Work

### Speed Control Integration

Arrow buttons **reference the speed slider values**:

1. **If slider is NOT at zero** → Use slider value (absolute)
   - Pan slider at 7.5 °/s → Right arrow uses 7.5 °/s
   - Tilt slider at -3.0 °/s → Up arrow uses 3.0 °/s (absolute value)

2. **If slider IS at zero** → Use default speed (5.0 °/s)
   - Allows quick movements even when sliders are centered

### Button Behavior

**Press and Hold:**
- Press arrow → Gimbal moves in that direction at slider speed
- Hold arrow → Continuous movement
- Release arrow → Gimbal stops

**One-Axis Control:**
- Each arrow controls only ONE axis (pan OR tilt)
- Up/Down → Tilt only
- Left/Right → Pan only
- No diagonal movements (unlike trackpad)

## Usage Examples

### Example 1: Set Speed, Use Arrows
```
1. Move Pan Speed slider to 8.0 °/s
2. Press Right arrow (▶)
   → Gimbal pans right at 8.0 °/s
3. Release arrow
   → Gimbal stops
4. Press Left arrow (◀)
   → Gimbal pans left at 8.0 °/s (slider value)
```

### Example 2: Default Speed (Sliders at Zero)
```
1. All sliders at center (0.0 °/s)
2. Press Up arrow (▲)
   → Gimbal tilts up at 5.0 °/s (default)
3. Release arrow
   → Gimbal stops
```

### Example 3: Precise Vertical Scan
```
1. Set Tilt Speed slider to 2.0 °/s (slow)
2. Press Up arrow (▲)
   → Gimbal tilts up slowly at 2.0 °/s
3. Hold for smooth vertical scan
4. Release to stop at desired position
```

### Example 4: Adjust Speed On-The-Fly
```
1. Press Right arrow (▶) and hold
   → Gimbal pans right
2. While holding, move Pan Speed slider
   → Speed changes in real-time
3. Release arrow to stop
```

## Advantages

### ✅ Slider Integration
- Uses current slider settings
- Consistent speed control
- Visual feedback of speed

### ✅ One-Axis Precision
- Pure horizontal or vertical movement
- No accidental diagonal drift
- Perfect for scanning patterns

### ✅ Quick Access
- No need to drag trackpad
- Single button press
- Faster for simple movements

### ✅ Default Speed Fallback
- Works even when sliders at zero
- 5.0 °/s default is reasonable
- No "dead" buttons

## Control Comparison

| Method | Axes | Speed Source | Best For |
|--------|------|--------------|----------|
| **Trackpad** | Pan + Tilt | Drag distance | Dynamic tracking, diagonals |
| **Arrow Buttons** | One axis | Speed sliders | Precise scans, single-axis |
| **Speed Sliders** | Pan + Tilt | User set | Continuous movement |

## UI Visual

```
┌────────────────────────────────┐
│  PTZ Control                   │
├────────────────────────────────┤
│        🔍+ Zoom In             │
├────────────────────────────────┤
│                                │
│  🎯         ▲          🎯      │
│  Far     ◀  ●  ▶      Near     │
│             ▼                  │
│                                │
├────────────────────────────────┤
│        🔍- Zoom Out            │
└────────────────────────────────┘
```

## Commands Sent

### Arrow Pressed:
```
ID:N/Command/MotorControl/Pan/Speed:8.0    (Right arrow, slider at 8.0)
ID:N/Command/MotorControl/Tilt/Speed:5.0   (Up arrow, slider at 0)
```

### Arrow Released:
```
ID:N/Command/MotorControl/Pan/Speed:0
ID:N/Command/MotorControl/Tilt/Speed:0
```

## Technical Implementation

### Speed Logic:
```python
def on_arrow_right_pressed(self):
    pan_speed = self.pan_speed_slider.value() / 10.0
    
    if pan_speed == 0:
        pan_speed = 5.0  # Default
    else:
        pan_speed = abs(pan_speed)  # Force positive for right
    
    self.pan_speed_changed.emit(pan_speed)
```

### Direction Mapping:
- **Up (▲)**: `+abs(tilt_slider)` or `+5.0`
- **Down (▼)**: `-abs(tilt_slider)` or `-5.0`
- **Left (◀)**: `-abs(pan_slider)` or `-5.0`
- **Right (▶)**: `+abs(pan_slider)` or `+5.0`

### Files Modified:

1. **`gui/widgets/ptz_trackpad.py`**
   - Added 5 new signals: `arrow_up/down/left/right_pressed`, `arrow_released`
   - Created 4 arrow buttons with styling
   - Positioned around trackpad (up/down/left/right)
   - Connected to emit appropriate signals

2. **`gui/tabs/combined_control_tab.py`**
   - Connected arrow signals to handlers
   - Added 5 handler methods
   - Handlers read current slider values
   - Use absolute value + correct sign for direction

## Use Cases

### Horizontal Scan
```
1. Set Pan Speed to desired rate
2. Press and hold Right arrow
3. Smooth horizontal scan
4. Release to stop
```

### Vertical Scan
```
1. Set Tilt Speed to desired rate
2. Press and hold Up arrow
3. Smooth vertical scan
4. Release to stop
```

### Grid Search Pattern
```
1. Pan right across area (hold Right arrow)
2. Tilt up one step (tap Up arrow)
3. Pan left across area (hold Left arrow)
4. Tilt up one step (tap Up arrow)
5. Repeat...
```

### Quick Look Left/Right
```
1. Leave sliders at zero (default 5.0 °/s)
2. Tap Left arrow briefly
3. Tap Right arrow briefly
4. Quick glances without trackpad
```

## Button Styling

- **Color**: Blue (`#2a82da`) on dark background
- **Border**: Thin blue border
- **Hover**: Slightly lighter background
- **Pressed**: Blue background with white text
- **Size**: 
  - Up/Down: 40×25 pixels
  - Left/Right: 25×40 pixels

## Future Enhancements

Possible improvements:
- [ ] Hold time indicator (visual feedback)
- [ ] Acceleration (speed up if held longer)
- [ ] Keyboard shortcuts (arrow keys)
- [ ] Speed multiplier (shift+arrow = 2× speed)
- [ ] Nudge mode (tap = small fixed movement)
- [ ] Visual speed indicator on arrows

---

**Status**: ✅ Directional arrows implemented and ready to test
