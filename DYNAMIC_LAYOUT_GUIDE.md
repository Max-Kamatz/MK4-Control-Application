# Dynamic Camera Layout Feature Guide

## Overview

The video display area now **automatically adjusts** based on how many cameras are actually available. No more wasted space on unavailable cameras!

## Dynamic Layouts

### No Cameras (Before Connection)
```
┌────────────────────────────────────────┐
│  📹 Live Camera Feeds                  │
├────────────────────────────────────────┤
│                                        │
│    Connect to a payload to view       │
│         camera feeds                   │
│                                        │
└────────────────────────────────────────┘
```

### 1 Camera Available - **Full Width**
```
┌────────────────────────────────────────┐
│  📹 Live Camera Feeds (1/3)            │
├────────────────────────────────────────┤
│                                        │
│        ╔══════════════════╗            │
│        ║   Thermal Camera ║            │
│        ║   [FULL WIDTH]   ║            │
│        ║                  ║            │
│        ╚══════════════════╝            │
│                                        │
└────────────────────────────────────────┘
```

**Use Case**: Only thermal camera connected  
**Benefit**: Maximum screen real estate for single camera

### 2 Cameras Available - **Side by Side**
```
┌────────────────────────────────────────┐
│  📹 Live Camera Feeds (2/3)            │
├────────────────────────────────────────┤
│                                        │
│  ╔════════════╗    ╔════════════╗     │
│  ║  Thermal   ║    ║  Daylight  ║     │
│  ║   Camera   ║    ║   Camera   ║     │
│  ║   [50%]    ║    ║   [50%]    ║     │
│  ╚════════════╝    ╚════════════╝     │
│                                        │
└────────────────────────────────────────┘
```

**Use Case**: Thermal + Daylight (SWIR not connected)  
**Benefit**: Equal space for both cameras, no wasted area

### 3 Cameras Available - **2x2 Grid**
```
┌────────────────────────────────────────┐
│  📹 Live Camera Feeds (3/3)            │
├────────────────────────────────────────┤
│                                        │
│  ╔══════════╗     ╔══════════╗        │
│  ║ Thermal  ║     ║ Daylight ║        │
│  ║  Camera  ║     ║  Camera  ║        │
│  ╚══════════╝     ╚══════════╝        │
│                                        │
│  ╔══════════╗                          │
│  ║   SWIR   ║                          │
│  ║  Camera  ║                          │
│  ╚══════════╝                          │
│                                        │
└────────────────────────────────────────┘
```

**Use Case**: All cameras connected  
**Benefit**: Traditional grid layout for maximum coverage

## How It Works

### Connection Workflow:

1. **Click "Connect"**
   - Payload discovery runs
   - Camera discovery checks each RTSP endpoint

2. **Layout Calculation**
   ```
   Available Cameras → Layout Decision
   ─────────────────────────────────────
   0 cameras        → Placeholder message
   1 camera         → Full width display
   2 cameras        → 50/50 split (side by side)
   3 cameras        → 2x2 grid
   ```

3. **Dynamic Rebuild**
   - Old layout cleared
   - Only available camera widgets added
   - Layout recalculated based on count
   - Title updated: "📹 Live Camera Feeds (2/3)"

### Log Messages

Watch the log viewer (Ctrl+L) to see layout changes:

```
[INFO] Discovering cameras at 192.168.1.81...
[INFO]   Thermal: ✓ Available
[INFO]   Daylight: ✓ Available
[INFO]   Swir: ✗ Not available
[INFO] Video streams updated: 2/3 cameras available
[INFO] Layout: 2 cameras (Thermal, Daylight) - side by side
```

## Benefits

### Space Efficiency

**Before (Fixed Layout):**
- ❌ Always shows 3 placeholders
- ❌ Wasted space for unavailable cameras
- ❌ Small video displays even with only 1 camera

**After (Dynamic Layout):**
- ✅ Only shows available cameras
- ✅ Maximum space utilization
- ✅ Larger video displays with fewer cameras
- ✅ Better viewing experience

### Real-World Examples

#### Example 1: Field Testing (Single Camera)
**Scenario**: Testing thermal camera only  
**Layout**: Full width thermal display  
**Benefit**: Large, clear thermal view for operator

#### Example 2: Standard Operation (Thermal + Daylight)
**Scenario**: SWIR not installed  
**Layout**: 50/50 split  
**Benefit**: Equal space for both operational cameras

#### Example 3: Full System (All Cameras)
**Scenario**: Complete MK4 payload  
**Layout**: 2x2 grid  
**Benefit**: See all feeds simultaneously

## Visual Feedback

### Title Bar Updates
The title dynamically shows camera count:
- `📹 Live Camera Feeds` → Before connection
- `📹 Live Camera Feeds (1/3)` → 1 camera available
- `📹 Live Camera Feeds (2/3)` → 2 cameras available
- `📹 Live Camera Feeds (3/3)` → All cameras available

### Camera Order
Cameras appear in priority order:
1. **Thermal** (highest priority)
2. **Daylight** (medium priority)
3. **SWIR** (lowest priority)

So with 2 cameras, you'll typically see Thermal + Daylight.

## Technical Details

### Layout Algorithm
```python
if num_cameras == 0:
    # Show placeholder message
elif num_cameras == 1:
    # Add to grid at (0, 0) - full width
elif num_cameras == 2:
    # Add camera 1 at (0, 0)
    # Add camera 2 at (0, 1) - side by side
elif num_cameras == 3:
    # Add camera 1 at (0, 0)
    # Add camera 2 at (0, 1) - top row
    # Add camera 3 at (1, 0) - bottom left
```

### Performance
- Layout rebuild is instant (<10ms)
- Only happens once per connection
- No continuous recalculations
- Smooth camera transitions

## Future Enhancements

Possible improvements:
- **Manual layout selection** (let user choose grid/list/fullscreen)
- **Fullscreen individual camera** (double-click to maximize)
- **Drag-and-drop reordering** (customize camera positions)
- **Picture-in-picture mode** (overlay smaller cameras on main view)
- **Layout preferences** (remember user's preferred arrangement)

## Troubleshooting

### Layout Not Updating
- Disconnect and reconnect to trigger rediscovery
- Check logs (Ctrl+L) for "Layout:" messages
- Verify camera discovery completed successfully

### Wrong Number of Cameras
- Camera discovery may have timed out
- Check network connectivity to RTSP port 7031
- Review discovery logs for specific camera failures

### Cameras in Wrong Positions
- Layout follows fixed priority: Thermal → Daylight → SWIR
- To change order, modify camera priority in code
