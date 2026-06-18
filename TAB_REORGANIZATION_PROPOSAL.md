# Tab Reorganization Proposal
## MK4 Control Application - Revised Tab Structure

**Date:** 2026-06-17  
**Purpose:** Reorganize all features into logical, well-organized tabs

---

## PROPOSED TAB STRUCTURE (7 Tabs Total)

### 1. **Connection Tab** (KEEP AS-IS)
*Purpose: Network connectivity and system health monitoring*

**Group 1: Network Connection**
- Target IP Address input
- Connect/Disconnect button
- Connection status indicator

**Group 2: Connection Log**
- Auto-scrolling event log (timestamps, searchable)
- 200px max height

**Group 3: Component Status**
- Main Board status
- Daylight/Thermal/SWIR camera status
- WL/IR Illuminator status
- Sub-Payload, Speaker status
- SSH-based ping checks to 10.10.10.x subnet

**Current Status:** ✅ Already implemented  
**No changes needed**

---

### 2. **Control Tab** (KEEP AS-IS)
*Purpose: Real-time PTZ control and operation*

**Group 1: Active Camera**
- Camera selector buttons (Daylight/Thermal/SWIR)
- For targeting zoom/focus commands

**Group 2: PTZ Trackpad**
- Interactive joystick control
- Zoom In/Out buttons (diagonal corners)
- Focus Near/Far buttons (diagonal corners)
- Directional arrows (Up/Down/Left/Right)

**Group 3: Speed Control**
- Pan speed slider (-10.0 to +10.0 °/s)
- Tilt speed slider (-10.0 to +10.0 °/s)
- Zoom speed slider (-1.0 to +1.0)
- Focus speed slider (-1.0 to +1.0)

**Group 4: Position Feedback**
- Commanded pan/tilt (speed display)
- Actual pan/tilt (10Hz telemetry from hardware)

**Current Status:** ✅ Already implemented  
**No changes needed**

---

### 3. **Motor Settings Tab** (NEW - Consolidates motor/gimbal configuration)
*Purpose: Motor calibration, limits, and behavior configuration*

#### **From Configuration Tab (Existing):**
- Pan Left Limit
- Pan Right Limit
- Tilt Up Limit
- Tilt Down Limit
- Homing Delay Mode
- Homing Delay Time
- Query Pan Limits button
- Query Tilt Limits button
- Query Homing button

#### **NEW Features to Add:**

**Group 1: Motor Calibration**
- Pan SetZero (button) - Set current position as zero
- Pan ResetZero (button) - Reset to factory zero
- Pan ZeroPos (input + Set button) - Define zero position manually
- Tilt SetZero (button)
- Tilt ResetZero (button)
- Tilt ZeroPos (input + Set button)

**Group 2: Motor Limits** (move from Configuration)
- Pan Left Limit (0-360°)
- Pan Right Limit (0-360°)
- Tilt Up Limit (-90 to +90°)
- Tilt Down Limit (-90 to +90°)

**Group 3: Motor Speed Settings**
- Pan MaxSpeed (input + Set) - Maximum pan velocity
- Pan PositionSpeed (input + Set) - Speed for ToPos commands
- Tilt MaxSpeed (input + Set)
- Tilt PositionSpeed (input + Set)

**Group 4: Motor Behavior**
- Pan InvertMovement (On/Off) - Swap left/right directions
- Tilt InvertMovement (On/Off) - Swap up/down directions
- ZoomDependentMode (Enable/Disable) - Link PT speed to zoom level
- BlockPT (On/Off) - Disable PT movement

**Group 5: Acceleration/Deceleration**
- AccVelMax (input + Set) - Max acceleration velocity
- AccDecMax (input + Set) - Max deceleration rate
- AccDecRate (input + Set) - Acceleration rate
- AccDecVstop (input + Set) - Velocity at stop

**Group 6: Homing** (move from Configuration)
- Homing Delay Mode (Enable/Disable)
- Homing Delay Time (seconds)

**Group 7: System Controls**
- Reset Controller (button) - Restart motor controller
- Query All Motor Settings (button)

**Total Controls:** ~35 controls in 7 groups

---

### 4. **Camera Settings Tab** (NEW - All camera quality & image capture)
*Purpose: Image capture parameters, exposure, color, and lens control*

#### **From Functions Tab (Existing):**
- Camera Profile selector
- Autofocus button
- Digital Zoom (On/Off, Level)
- CLAHE (On/Off)
- Color Filter (On/Off, Palette)

#### **NEW Features to Add:**

**Group 1: Target Camera Selector**
- Camera selection buttons (Daylight/Thermal/SWIR)
- All settings below apply to selected camera

**Group 2: Exposure Control**
- Exposure Mode (dropdown: Auto/Manual/Aperture/Shutter Priority)
- Shutter Speed (input + Set)
- Gain (input + Set)
- Auto Mode (toggle)

**Group 3: Iris Control**
- Iris Mode (Auto/Manual toggle)
- Iris (manual value input + Set)
- Iris Open (button)
- Iris Close (button)
- Iris Stop (button)
- Iris ToPos (position input + Set)

**Group 4: Focus Control** (from Functions + new)
- Focus ToPos (position input + Set) - NEW
- OnePushAf (button) - NEW (one-time autofocus)
- Autofocus Mode (toggle) - EXISTING from Functions
- Focus speed multiplier (input + Set) - NEW

**Group 5: Lens Control** (from Functions + new)
- Zoom ToPos (position input + Set) - EXISTING from Functions
- Zoom speed multiplier (input + Set) - NEW
- Lens Endpoints:
  - TeleEndPos (input + Set) - Telephoto limit
  - WideEndPos (input + Set) - Wide-angle limit
  - FarEndPos (input + Set) - Far focus limit
  - NearEndPos (input + Set) - Near focus limit

**Group 6: White Balance**
- White Balance Mode (dropdown: Auto/Manual/Indoor/Outdoor/etc.)
- WB Red Gain (slider 0-255)
- WB Blue Gain (slider 0-255)
- Color Mode (dropdown: Color/B&W/etc.)

**Group 7: Image Enhancement**
- Brightness (slider 0-100)
- Contrast (slider 0-100)
- Saturation (slider 0-100)
- Sharpness (slider 0-100)

**Group 8: Advanced Image Processing**
- Backlight Compensation (Enable/Disable + level slider)
- Wide Dynamic Range (Enable/Disable + level slider)
- Noise Reduction (Enable/Disable + level slider)
- Defog Mode (Enable/Disable)

**Group 9: Digital Zoom** (from Functions)
- Digital Zoom (Enable/Disable)
- Digital Zoom Level (1.0-4.0)

**Group 10: CLAHE** (from Functions + new)
- CLAHE (Enable/Disable)
- CLAHE ClipLimit (input + Set) - NEW
- CLAHE TilesGridSize (input + Set) - NEW

**Group 11: Color Filter** (from Functions + new)
- Color Filter (Enable/Disable)
- Color Palette (0-N)
- Color Filter Auto Mode (toggle) - NEW
- Hue (slider 0-360) - NEW
- Saturation (slider 0-100) - NEW
- Gamma (slider 0.1-5.0) - NEW

**Group 12: Image Flip** (NEW)
- Image Flip Mode (dropdown: Normal/H-Flip/V-Flip/HV-Flip)
- Horizontal Flip (toggle)
- Vertical Flip (toggle)

**Group 13: Video Stabilizer** (from Functions + new)
- Video Stabilizer (Enable/Disable) - EXISTING
- XOffsetLimit (pixels, input + Set) - NEW
- YOffsetLimit (pixels, input + Set) - NEW
- AOffsetLimit (degrees, input + Set) - NEW (rotation compensation)
- Stabilizer Mode (dropdown) - NEW
- Transparent Border Mode (Enable/Disable) - NEW
- Type (dropdown) - NEW
- ConstXOffset/ConstYOffset/ConstAOffset (inputs) - NEW

**Group 14: Camera Profiles** (from Functions)
- Profile Number (input + Set)
- Query Camera Settings (button)

**Total Controls:** ~73 controls in 14 groups

---

### 5. **RTSP Tab** (NEW - All video streaming configuration)
*Purpose: Video stream configuration and protocol management*

#### **From Configuration Tab (Existing):**
- Target Camera/Stream selector (1-3, 1-2)
- Video Stream Enable/Disable
- RTSP Suffix
- Resolution
- Bitrate
- Bitrate Mode (CBR/VBR)
- FPS
- GOP
- Codec
- H264 Profile
- Query Video Settings button

#### **NEW Features to Add:**

**Group 1: Target Selection** (from Configuration)
- Camera selector (1, 2, or 3)
- Stream selector (1 or 2)
- Note: Each camera has 2 independent streams

**Group 2: Stream Control** (from Configuration)
- Enable Stream (button)
- Disable Stream (button)
- Restart Stream (button) - NEW

**Group 3: RTSP Settings** (from Configuration + new)
- RTSP Suffix (input + Set) - e.g., "live" → rtsp://IP:7031/live
- RTSP Port (input + Set) - NEW (default 7031, applies to all)
- RTSP Multicast IP (input + Set) - NEW
- RTSP Multicast Port (input + Set) - NEW
- RTSP User (input + Set) - NEW (authentication)
- RTSP Password (input + Set) - NEW (authentication)

**Group 4: Video Encoding** (from Configuration + new)
- Resolution (WxH dropdown or input)
- Codec (dropdown: H264/H265/JPEG)
- H264 Profile (dropdown: Baseline/Main/High)
- JPEG Quality (slider 1-100) - NEW (when JPEG codec selected)

**Group 5: Bitrate Settings** (from Configuration + new)
- Bitrate (kbps input + Set)
- Bitrate Mode (CBR/VBR buttons)
- Min Bitrate (input + Set) - NEW
- Max Bitrate (input + Set) - NEW

**Group 6: Frame Settings** (from Configuration)
- FPS (1-30 input + Set)
- GOP (keyframe interval input + Set)

**Group 7: Video Processing** (NEW)
- Fit Mode (dropdown: Fit/Crop) - How to scale if resolution ≠ camera native
- Overlay Mode (Enable/Disable) - Enable overlays on stream
- Metadata Mode (Enable/Disable) - Include metadata in stream
- Metadata Suffix (dropdown: SMPTE336M/VND.ONVIF.METADATA)

**Group 8: RTP Direct Streaming** (NEW)
- RTP Mode (Enable/Disable)
- RTP Port (input + Set)
- RTP Destination IP (input + Set)

**Group 9: RTMP Server** (NEW)
- RTMP Mode (Enable/Disable)
- RTMP Port (input + Set)

**Group 10: HLS Server** (NEW)
- HLS Mode (Enable/Disable)
- HLS Port (input + Set)

**Group 11: SRT Server** (NEW)
- SRT Mode (Enable/Disable)
- SRT Port (input + Set)

**Group 12: Advanced Settings** (NEW)
- Custom UDP Payload Size (100-65535 bytes)
- Query Video Settings (button) - from Configuration

**Total Controls:** ~45 controls in 12 groups

---

### 6. **Tracker Settings Tab** (NEW - Tracking, detection, AI analysis)
*Purpose: Intelligent video analysis, tracking, and detection*

#### **NEW Features to Add:**

**Group 1: Target Camera Selector**
- Camera selection buttons (Daylight/Thermal/SWIR)
- All settings below apply to selected camera

**Group 2: Motion Magnificator** (NEW)
- Motion Magnificator (Enable/Disable)
- Magnification Level (slider or input)

**Group 3: Video Tracker** (NEW)
- VideoTracker Reset (button)
- VideoTracker (Enable/Disable)
- VideoTracker Lock (button) - Lock onto target
- VideoTracker Unlock (button)
- Tracker Mode (dropdown: Manual/Auto/Continuous)
- Object Size (input + Set)
- Search Area Size (input + Set)

**Group 4: Motion Detector** (NEW)
- Motion Detector Reset (button)
- Motion Detector (Enable/Disable)
- Frame Buffer Size (1-20, input + Set)
- Min Object Width (pixels, input + Set)
- Max Object Width (pixels, input + Set)
- Min Object Height (pixels, input + Set)
- Max Object Height (pixels, input + Set)
- X Detection Criteria (input + Set)
- Y Detection Criteria (input + Set)
- Reset Criteria (input + Set)
- Sensitivity (slider 0-100)
- Motion Detector Mode (dropdown)

**Group 5: Changes Detector** (NEW)
- Changes Detector Reset (button)
- Changes Detector (Enable/Disable)
- Frame Buffer Size (1-20, input + Set)
- Min/Max Object Width/Height (inputs + Set)
- X/Y Detection Criteria (inputs + Set)
- Reset Criteria (input + Set)
- Sensitivity (slider 0-100)
- Changes Detector Mode (dropdown)

**Group 6: Classification** (NEW - if AI license available)
- Classification (Enable/Disable)
- Classification Model (dropdown)
- Confidence Threshold (slider 0-100)
- Query Classification Status (button)

**Group 7: Detection Results** (NEW)
- Subscribe to Objects/Events (button)
- Real-time detection results display (QTextEdit)
- Clear results (button)

**Group 8: License Status** (NEW)
- Query VideoTracker License (button)
- Query VideoStabiliser License (button)
- Query MotionDetector License (button)
- Query ChangesDetector License (button)
- Query Classification License (button)
- License status display area

**Total Controls:** ~52 controls in 8 groups

---

### 7. **Overlay Tab** (NEW - On-screen display elements)
*Purpose: Configure what information is displayed on video streams*

**Group 1: Target Camera Selector**
- Camera selection buttons (Daylight/Thermal/SWIR)
- All overlay settings below apply to selected camera

**Group 2: Crosshair**
- Crosshair Mode (Enable/Disable)
- Crosshair Size (slider 1-100 pixels)
- Crosshair Color (dropdown: White/Black/Red/Green/Blue/Contrast)

**Group 3: Information Overlays**
- Date & Time Display (Enable/Disable)
- Zoom Position Display (Enable/Disable)
- Focus Mode Display (Enable/Disable)
- Digital Zoom Level Display (Enable/Disable)
- CLAHE Status Display (Enable/Disable)
- Tracker Status Display (Enable/Disable)
- Pan/Tilt Position Display (Enable/Disable)
- LRF Range Display (Enable/Disable) - if LRF hardware present

**Group 4: WebRTC Overlay** (NEW - advanced)
- WebRTC Overlay (Enable/Disable)
- WebRTC Overlay parameters (if applicable)

**Total Controls:** ~15 controls in 4 groups

---

## SUMMARY: What Moves Where?

### **Eliminated Tabs:**
- ❌ **Functions Tab** → Content redistributed to Camera Settings & Tracker Settings
- ❌ **Configuration Tab** → Content redistributed to Motor Settings, RTSP, and Tracker Settings

### **Migration Map:**

| Current Location | Feature | New Location |
|------------------|---------|--------------|
| Functions | Camera Profile | Camera Settings |
| Functions | Autofocus | Camera Settings |
| Functions | Zoom to Position | Camera Settings |
| Functions | Digital Zoom | Camera Settings |
| Functions | CLAHE | Camera Settings |
| Functions | Color Filter | Camera Settings |
| Functions | Video Stabilizer | Camera Settings |
| Configuration | Slave Zoom Mode | Motor Settings (or remove - not critical) |
| Configuration | Pan/Tilt Limits | Motor Settings |
| Configuration | Homing Delay | Motor Settings |
| Configuration | RTSP Settings | RTSP Tab |

### **New Content Distribution:**

| Tab | Existing Features | New Features | Total |
|-----|-------------------|--------------|-------|
| Connection | 3 groups | 0 | 3 groups |
| Control | 4 groups | 0 | 4 groups |
| Motor Settings | 2 groups (from Config) | 5 groups | 7 groups, ~35 controls |
| Camera Settings | 6 groups (from Functions) | 8 groups | 14 groups, ~73 controls |
| RTSP | 1 group (from Config) | 11 groups | 12 groups, ~45 controls |
| Tracker Settings | 0 groups | 8 groups | 8 groups, ~52 controls |
| Overlay | 0 groups | 4 groups | 4 groups, ~15 controls |

---

## IMPLEMENTATION PRIORITY

### Phase 1: HIGH PRIORITY (Week 1)
1. **Motor Settings Tab** - Critical for gimbal setup and calibration
2. **Camera Settings Tab** - Essential for image quality

### Phase 2: MEDIUM PRIORITY (Week 2)
3. **RTSP Tab** - Important for video streaming configuration
4. **Overlay Tab** - Operator convenience features

### Phase 3: LOW PRIORITY (Week 3)
5. **Tracker Settings Tab** - Advanced AI features (requires licenses)

---

## SLAVE ZOOM CONSIDERATION

**Question:** Where should Slave Zoom Mode go?

**Option 1:** Keep in Motor Settings
- Rationale: It's a system-level setting that affects gimbal + lens coordination

**Option 2:** Move to Camera Settings
- Rationale: It's about zoom coordination across cameras

**Option 3:** Remove from UI
- Rationale: It's a rarely-used advanced feature

**Recommendation:** Move to Motor Settings under a "System Coordination" group

---

## ADDITIONAL NOTES

### Tab Scrolling
- Motor Settings, Camera Settings, RTSP, and Tracker Settings tabs will have many controls
- Recommend adding `QScrollArea` to these tabs to handle overflow
- Current implementation uses `layout.addStretch()` which pushes content to top

### Tab Width
- All tabs maintain 480px fixed width (consistent with current design)
- 3-column grid layout (Label, Input, Button)

### Tab Count
- Total: 7 tabs (current: 4)
- Fits comfortably in 480px tab bar width

### Signal Count Estimate
- Motor Settings: ~30 signals
- Camera Settings: ~68 signals
- RTSP: ~40 signals
- Tracker Settings: ~42 signals
- Overlay: ~15 signals
- **Total new signals: ~195**

---

## QUESTIONS FOR REVIEW

1. ✅ **Approve Tab Structure?** - Connection, Control, Motor Settings, Camera Settings, RTSP, Tracker Settings, Overlay

2. ✅ **Slave Zoom Placement?** - Motor Settings, Camera Settings, or remove?

3. ✅ **Scrolling Implementation?** - Add QScrollArea to tabs with 40+ controls?

4. ✅ **Grouping?** - Are the QGroupBox sections logical and well-organized?

5. ✅ **Priority?** - Phase 1: Motor + Camera, Phase 2: RTSP + Overlay, Phase 3: Tracker?

---

**Status:** Ready for review and approval
