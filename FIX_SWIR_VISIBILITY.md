# Fix: SWIR Camera Widget Still Visible After Connection

## Problem

When connecting to a payload where the SWIR camera is not available, the SWIR video widget window was still being displayed in the GUI even though it should have been hidden.

## Root Cause

The issue was in `gui/tabs/combined_control_tab.py`, specifically in the dynamic camera layout system:

1. **Stream threads not stopped**: When a camera was discovered as unavailable, the existing stream thread (from a previous connection) was not being stopped, causing it to continue trying to connect in the background.

2. **Incomplete widget cleanup**: The `rebuild_video_layout()` method was not fully removing widgets from the layout hierarchy before rebuilding, leading to widgets remaining visible.

## Solution

### 1. Stop Stream Threads for Unavailable Cameras

Modified `update_video_streams_ip()` method to properly stop stream threads when cameras are not available:

```python
# For each camera (thermal, daylight, swir):
if hasattr(self.thermal_widget, 'stream_thread') and self.thermal_widget.stream_thread:
    if self.camera_availability.get('thermal', False):
        self.thermal_widget.stream_thread.change_url(thermal_url)
    else:
        logger.info("Stopping thermal camera stream - not available")
        # Stop the existing stream thread
        self.thermal_widget.stream_thread.stop()
        self.thermal_widget.set_unavailable()
```

**Why this matters**: Without stopping the stream thread, the widget continues to display "Connecting..." status even though we don't want it visible at all.

### 2. Enhanced Widget Cleanup in Layout Rebuild

Improved `rebuild_video_layout()` to completely remove widgets from the layout hierarchy:

```python
def rebuild_video_layout(self):
    # Clear existing layout - remove all widgets
    while self.video_grid.count():
        item = self.video_grid.takeAt(0)
        if item.widget():
            widget = item.widget()
            widget.setParent(None)  # Remove from layout hierarchy
            widget.hide()  # Ensure it's hidden

    # Explicitly hide all camera widgets
    self.thermal_widget.hide()
    self.thermal_widget.setParent(None)
    self.daylight_widget.hide()
    self.daylight_widget.setParent(None)
    self.swir_widget.hide()
    self.swir_widget.setParent(None)
    self.no_cameras_label.hide()
    self.no_cameras_label.setParent(None)
```

**Why this matters**: Setting `setParent(None)` completely removes the widget from the Qt widget hierarchy, ensuring it's not rendered even if it was previously added to a layout.

### 3. Proper Re-parenting When Adding Back

When adding available cameras back to the layout:

```python
# Before showing, set the parent
widget.setParent(self.video_grid_widget)
self.video_grid.addWidget(widget, row, col)
widget.show()
```

**Why this matters**: Ensures widgets are properly attached to the correct parent before being displayed.

## Testing the Fix

### Test Case 1: SWIR Not Available (Common Scenario)

**Steps:**
1. Start application
2. Enter IP address for payload (e.g., `192.168.1.81`)
3. Click "Connect"
4. Observe camera discovery results

**Expected Result:**
- Thermal and Daylight cameras: ✅ Available → Displayed side-by-side (50/50 layout)
- SWIR camera: ❌ Not available → **Not displayed at all**
- Title shows: "📹 Live Camera Feeds (2/3)"
- Log shows: "Stopping SWIR camera stream - not available"

### Test Case 2: All Cameras Available

**Expected Result:**
- All 3 cameras displayed in 2x2 grid
- Title shows: "📹 Live Camera Feeds (3/3)"

### Test Case 3: Only One Camera Available

**Expected Result:**
- Single camera displayed full-width
- Title shows: "📹 Live Camera Feeds (1/3)"
- Other camera widgets completely hidden

## Technical Details

### Files Modified

- `gui/tabs/combined_control_tab.py`:
  - `update_video_streams_ip()`: Added stream thread stopping for unavailable cameras
  - `rebuild_video_layout()`: Enhanced widget cleanup and re-parenting

### Key Qt Concepts Used

1. **`setParent(None)`**: Removes widget from parent widget hierarchy
2. **`hide()`**: Makes widget invisible but keeps it in hierarchy
3. **`addWidget()`**: Adds widget to layout and shows it
4. **`takeAt()`**: Removes item from layout

### Compliance with Memory Feedback

This fix follows the critical learnings from previous sessions:

✅ **No GUI thread blocking**: Camera discovery runs in background thread  
✅ **Proper signal disconnection**: Stream threads are stopped before widget changes  
✅ **Thread lifecycle management**: Never destroy threads while running, use `stop()` method

## Benefits

- **Clean UI**: Only shows cameras that are actually available
- **Resource efficiency**: Stops unnecessary connection attempts
- **Better user experience**: Clear visual feedback of available cameras
- **Proper thread cleanup**: Prevents background threads from wasting resources
- **Dynamic layouts**: Maximizes screen space based on available cameras

## Related Features

- Camera Discovery (`utils/camera_discovery.py`)
- Network Discovery (`utils/network_discovery.py`)
- Dynamic Layout Guide (`DYNAMIC_LAYOUT_GUIDE.md`)
- Camera Discovery Guide (`CAMERA_DISCOVERY_GUIDE.md`)
