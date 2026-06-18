# EUP Protocol Feature Audit
## MK4 Control Application - Implementation Status

**Date:** 2026-06-17  
**Protocol Version:** EUP v2.4.7  
**Application Version:** 0.2.0

---

## Legend
- ✅ **Implemented** - Feature fully implemented in GUI and protocol layer
- ⚠️ **Partial** - Protocol support exists, but no GUI controls
- ❌ **Not Implemented** - No implementation in protocol or GUI
- 🔵 **Hardware Specific** - Feature depends on specific hardware capabilities

---

## 1. MotorControl Messages (Section 4.1)

### Pan Control
| Command | Status | Location |
|---------|--------|----------|
| `Pan/ToPos:n` | ✅ | Control Tab - not exposed directly |
| `Pan/Left/AtDps:n` | ✅ | Control Tab - Pan speed slider/trackpad |
| `Pan/Right/AtDps:n` | ✅ | Control Tab - Pan speed slider/trackpad |
| `Pan/Stop` | ✅ | Control Tab - Trackpad release |
| `Pan/LeftLimit:n` | ✅ | Configuration Tab |
| `Pan/RightLimit:n` | ✅ | Configuration Tab |
| `Pan/SetZero` | ❌ | Not implemented |
| `Pan/ResetZero` | ❌ | Not implemented |
| `Pan/ZeroPos:n` | ❌ | Not implemented |
| `Pan/AddPos:n` | ❌ | Not implemented |
| `Pan/InvertMovement:s` | ❌ | Not implemented |
| `Pan/MaxSpeed:n` | ❌ | Not implemented |
| `Pan/PositionSpeed:n` | ❌ | Not implemented |
| `Pan/Left/AtRate:n` | ❌ | Not implemented (legacy) |
| `Pan/Right/AtRate:n` | ❌ | Not implemented (legacy) |

### Tilt Control
| Command | Status | Location |
|---------|--------|----------|
| `Tilt/ToPos:n` | ✅ | Control Tab - not exposed directly |
| `Tilt/Up/AtDps:n` | ✅ | Control Tab - Tilt speed slider/trackpad |
| `Tilt/Down/AtDps:n` | ✅ | Control Tab - Tilt speed slider/trackpad |
| `Tilt/Stop` | ✅ | Control Tab - Trackpad release |
| `Tilt/UpLimit:n` | ✅ | Configuration Tab |
| `Tilt/DownLimit:n` | ✅ | Configuration Tab |
| `Tilt/SetZero` | ❌ | Not implemented |
| `Tilt/ResetZero` | ❌ | Not implemented |
| `Tilt/ZeroPos:n` | ❌ | Not implemented |
| `Tilt/AddPos:n` | ❌ | Not implemented |
| `Tilt/InvertMovement:s` | ❌ | Not implemented |
| `Tilt/MaxSpeed:n` | ❌ | Not implemented |
| `Tilt/PositionSpeed:n` | ❌ | Not implemented |

### Homing & System Control
| Command | Status | Location |
|---------|--------|----------|
| `HomingDelay:n` | ✅ | Configuration Tab |
| `HomingDelayTime:n` | ✅ | Configuration Tab |
| `BlockPT:s` | ❌ | Not implemented |
| `ResetController` | ❌ | Not implemented |
| `ZoomDependentMode:n` | ❌ | Not implemented |
| `AccVelMax:n` | ❌ | Not implemented |
| `AccDecMax:n` | ❌ | Not implemented |
| `AccDecRate:n` | ❌ | Not implemented |
| `AccDecVstop:n` | ❌ | Not implemented |

### Position Queries
| Query | Status | Location |
|-------|--------|----------|
| `Query Pan/Pos` | ✅ | Automatic 10Hz polling |
| `Query Tilt/Pos` | ✅ | Automatic 10Hz polling |
| `Query Pan/LeftLimit` | ✅ | Configuration Tab - Query buttons |
| `Query Pan/RightLimit` | ✅ | Configuration Tab - Query buttons |
| `Query Tilt/UpLimit` | ✅ | Configuration Tab - Query buttons |
| `Query Tilt/DownLimit` | ✅ | Configuration Tab - Query buttons |

**Summary:** 16/48 MotorControl features implemented (33%)

---

## 2. Camera Lens Control (Section 4.2.1)

### Basic Lens Commands
| Command | Status | Location |
|---------|--------|----------|
| `ZoomIn` | ✅ | Control Tab - Zoom buttons |
| `ZoomOut` | ✅ | Control Tab - Zoom buttons |
| `ZoomStop` | ✅ | Control Tab - Button release |
| `ZoomToPos:n` | ✅ | Functions Tab |
| `FocusFar` | ✅ | Control Tab - Focus buttons |
| `FocusNear` | ✅ | Control Tab - Focus buttons |
| `FocusStop` | ✅ | Control Tab - Button release |
| `AfMode:n` (Autofocus) | ✅ | Functions Tab |
| `FocusToPos:n` | ❌ | Not implemented |
| `IrisOpen` | ❌ | Not implemented |
| `IrisClose` | ❌ | Not implemented |
| `IrisStop` | ❌ | Not implemented |
| `IrisToPos:n` | ❌ | Not implemented |
| `IrisMode:n` (Auto-iris) | ❌ | Not implemented |

### Advanced Lens Features
| Command | Status | Location |
|---------|--------|----------|
| `ZoomSpeedMultiplier:n` | ❌ | Not implemented |
| `FocusSpeedMultiplier:n` | ❌ | Not implemented |
| `OnePushAf` | ❌ | Not implemented |
| `TeleEndPos:n` | ❌ | Not implemented |
| `WideEndPos:n` | ❌ | Not implemented |
| `FarEndPos:n` | ❌ | Not implemented |
| `NearEndPos:n` | ❌ | Not implemented |

**Summary:** 8/21 Lens features implemented (38%)

---

## 3. Camera Settings (Section 4.2.2)

### Camera Profiles & Modes
| Command | Status | Location |
|---------|--------|----------|
| `Profile:n` | ✅ | Functions Tab |
| `AutoMode:n` | ❌ | Not implemented |
| `ColorMode:n` | ❌ | Not implemented |
| `WhiteBalance:n` | ❌ | Not implemented |
| `WbRedGain:n` | ❌ | Not implemented |
| `WbBlueGain:n` | ❌ | Not implemented |
| `ExposureMode:n` | ❌ | Not implemented |
| `ShutterSpeed:n` | ❌ | Not implemented |
| `Gain:n` | ❌ | Not implemented |
| `Iris:n` | ❌ | Not implemented |

### Image Enhancement
| Command | Status | Location |
|---------|--------|----------|
| `Brightness:n` | ❌ | Not implemented |
| `Contrast:n` | ❌ | Not implemented |
| `Saturation:n` | ❌ | Not implemented |
| `Sharpness:n` | ❌ | Not implemented |
| `BacklightCompensation:n` | ❌ | Not implemented |
| `WideDynamicRange:n` | ❌ | Not implemented |
| `NoiseReduction:n` | ❌ | Not implemented |
| `DefogMode:n` | ❌ | Not implemented |

**Summary:** 1/18+ Camera Settings implemented (6%)

---

## 4. VideoStabiliser (Section 4.2.5)

| Command | Status | Location |
|---------|--------|----------|
| `On` | ✅ | Functions Tab |
| `Off` | ✅ | Functions Tab |
| `XOffsetLimit:n` | ❌ | Not implemented |
| `YOffsetLimit:n` | ❌ | Not implemented |
| `AOffsetLimit:n` | ❌ | Not implemented |
| `Mode:n` | ❌ | Not implemented |
| `TransparentBorderMode:n` | ❌ | Not implemented |
| `ConstXOffset:n` | ❌ | Not implemented |
| `ConstYOffset:n` | ❌ | Not implemented |
| `ConstAOffset:n` | ❌ | Not implemented |
| `Type:n` | ❌ | Not implemented |

**Summary:** 2/11 VideoStabiliser features (18%)

---

## 5. DigitalZoom (Section 4.2.9)

| Command | Status | Location |
|---------|--------|----------|
| `On` | ✅ | Functions Tab |
| `Off` | ✅ | Functions Tab |
| `Level:n` | ✅ | Functions Tab |

**Summary:** 3/3 DigitalZoom features (100%) ✅

---

## 6. ImageFlip (Section 4.2.10)

| Command | Status | Location |
|---------|--------|----------|
| `Mode:n` | ❌ | Not implemented |
| `Horizontal:n` | ❌ | Not implemented |
| `Vertical:n` | ❌ | Not implemented |

**Summary:** 0/3 ImageFlip features (0%)

---

## 7. ColorFilter (Section 4.2.11)

| Command | Status | Location |
|---------|--------|----------|
| `On` | ✅ | Functions Tab |
| `Off` | ✅ | Functions Tab |
| `Palette:n` | ✅ | Functions Tab |
| `AutoMode:n` | ❌ | Not implemented |
| `Hue:n` | ❌ | Not implemented |
| `Saturation:n` | ❌ | Not implemented |
| `Brightness:n` | ❌ | Not implemented |
| `Contrast:n` | ❌ | Not implemented |
| `Gamma:n` | ❌ | Not implemented |

**Summary:** 3/9 ColorFilter features (33%)

---

## 8. CLAHE (Section 4.2.12)

| Command | Status | Location |
|---------|--------|----------|
| `On` | ✅ | Functions Tab |
| `Off` | ✅ | Functions Tab |
| `ClipLimit:n` | ❌ | Not implemented |
| `TilesGridSize:n` | ❌ | Not implemented |

**Summary:** 2/4 CLAHE features (50%)

---

## 9. VideoStream Configuration (Section 4.2.14)

### Stream Control
| Command | Status | Location |
|---------|--------|----------|
| `On` | ✅ | Configuration Tab |
| `Off` | ✅ | Configuration Tab |
| `Mode:n` | ⚠️ | Protocol only, no GUI |
| `Restart` | ❌ | Not implemented |

### RTSP Settings
| Command | Status | Location |
|---------|--------|----------|
| `Suffix:string` | ✅ | Configuration Tab |
| `RtspPort:n` | ⚠️ | Protocol only, no GUI |
| `RtspMulticastIp:string` | ❌ | Not implemented |
| `RtspMulticastPort:n` | ❌ | Not implemented |
| `User:string` | ❌ | Not implemented |
| `Password:string` | ❌ | Not implemented |

### Video Encoding
| Command | Status | Location |
|---------|--------|----------|
| `Resolution:WxH` | ✅ | Configuration Tab |
| `BitrateKbps:n` | ✅ | Configuration Tab |
| `BitrateMode:n` | ✅ | Configuration Tab (CBR/VBR) |
| `MinBitrateKbps:n` | ❌ | Not implemented |
| `MaxBitrateKbps:n` | ❌ | Not implemented |
| `Fps:n` | ✅ | Configuration Tab |
| `Gop:n` | ✅ | Configuration Tab |
| `Codec:string` | ✅ | Configuration Tab |
| `H264Profile:n` | ✅ | Configuration Tab |
| `JpegQuality:n` | ❌ | Not implemented |

### Advanced Streaming
| Command | Status | Location |
|---------|--------|----------|
| `FitMode:n` | ❌ | Not implemented |
| `OverlayMode:n` | ❌ | Not implemented |
| `MetadataMode:n` | ❌ | Not implemented |
| `MetadataSuffix:string` | ❌ | Not implemented |
| `RtpMode:n` | ❌ | Not implemented |
| `RtpPort:n` | ❌ | Not implemented |
| `Ip:string` (RTP dest) | ❌ | Not implemented |
| `RtmpMode:n` | ❌ | Not implemented |
| `RtmpPort:n` | ❌ | Not implemented |
| `HlsMode:n` | ❌ | Not implemented |
| `HlsPort:n` | ❌ | Not implemented |
| `SrtMode:n` | ❌ | Not implemented |
| `SrtPort:n` | ❌ | Not implemented |
| `Custom1:n` (UDP payload) | ❌ | Not implemented |

**Summary:** 10/28 VideoStream features (36%)

---

## 10. Overlay Control (Section 4.2.15)

| Command | Status | Location |
|---------|--------|----------|
| `CrossHairMode:n` | ❌ | Not implemented |
| `CrossHairSize:n` | ❌ | Not implemented |
| `CrossHairColor:n` | ❌ | Not implemented |
| `DateTimeMode:n` | ❌ | Not implemented |
| `ZoomPosMode:n` | ❌ | Not implemented |
| `FocusMode:n` | ❌ | Not implemented |
| `LrfMode:n` | ❌ | Not implemented |
| `DigitalZoomMode:n` | ❌ | Not implemented |
| `ClaheMode:n` | ❌ | Not implemented |
| `TrackerMode:n` | ❌ | Not implemented |
| `PanTiltPosMode:n` | ❌ | Not implemented |

**Summary:** 0/11 Overlay features (0%)

---

## 11. VideoTracker (Section 4.2.4)

| Command | Status | Location |
|---------|--------|----------|
| `Reset` | ❌ | Not implemented |
| `On` | ❌ | Not implemented |
| `Off` | ❌ | Not implemented |
| `Lock` | ❌ | Not implemented |
| `Unlock` | ❌ | Not implemented |
| `Mode:n` | ❌ | Not implemented |
| `ObjectSize:n` | ❌ | Not implemented |
| `SearchAreaSize:n` | ❌ | Not implemented |

**Summary:** 0/8+ VideoTracker features (0%)

---

## 12. MotionDetector (Section 4.2.6)

| Command | Status | Location |
|---------|--------|----------|
| `Reset` | ❌ | Not implemented |
| `On` | ❌ | Not implemented |
| `Off` | ❌ | Not implemented |
| `FrameBufferSize:n` | ❌ | Not implemented |
| `MinObjectWidth:n` | ❌ | Not implemented |
| `MaxObjectWidth:n` | ❌ | Not implemented |
| `MinObjectHeight:n` | ❌ | Not implemented |
| `MaxObjectHeight:n` | ❌ | Not implemented |
| `Sensitivity:n` | ❌ | Not implemented |

**Summary:** 0/9+ MotionDetector features (0%)

---

## 13. General System Commands (Section 4.6)

| Command | Status | Location |
|---------|--------|----------|
| `SlaveZoomMode:n` | ✅ | Configuration Tab |
| `SlaveZoomMasterCamera:n` | ✅ | Configuration Tab |
| `JafarServiceRestart` | ❌ | Not implemented |

### License Queries
| Query | Status |
|-------|--------|
| `VideoTrackerToken` | ❌ |
| `VideoTrackerLicenseStatus` | ❌ |
| `VideoStabiliserToken` | ❌ |
| `VideoStabiliserLicenseStatus` | ❌ |
| `MotionDetectorToken` | ❌ |
| `MotionDetectorLicenseStatus` | ❌ |
| `ChangesDetectorToken` | ❌ |
| `ChangesDetectorLicenseStatus` | ❌ |
| `ClassificationToken` | ❌ |
| `ClassificationLicenseStatus` | ❌ |

**Summary:** 2/13+ General features (15%)

---

## 14. NOT IMPLEMENTED MODULES

The following entire modules have **NO implementation**:

- ❌ **VideoSource** (Section 4.2.3) - Video input selection
- ❌ **ChangesDetector** (Section 4.2.7) - Scene change detection
- ❌ **Classification** (Section 4.2.8) - Object classification
- ❌ **MotionMagnificator** (Section 4.2.13) - Motion amplification
- ❌ **WebRtcOverlay** (Section 4.2.16) - WebRTC overlay controls
- ❌ **BadPixelProcessor** (Section 4.2.17) - Bad pixel correction
- ❌ **Companion** (Section 4.3) - Companion board control
- ❌ **Lrf** (Section 4.4) - Laser rangefinder
- ❌ **Speaker** (Section 4.5) - Audio playback
- ❌ **ProcedureManager** (Section 4.7) - Automated procedures
- ❌ **G5Laser** (Section 4.8) - Laser illuminator
- ❌ **PeakBeam** (Section 4.9) - Peak beam illuminator
- ❌ **ExternalUp** (Section 4.10) - External UP forwarding
- ❌ **PelcoD** (Section 4.11) - Pelco-D protocol forwarding

---

## OVERALL IMPLEMENTATION SUMMARY

| Category | Implemented | Total Available | Percentage |
|----------|-------------|-----------------|------------|
| **MotorControl** | 16 | ~48 | 33% |
| **Lens Control** | 8 | ~21 | 38% |
| **Camera Settings** | 1 | ~18 | 6% |
| **VideoStabiliser** | 2 | 11 | 18% |
| **DigitalZoom** | 3 | 3 | 100% ✅ |
| **ColorFilter** | 3 | 9 | 33% |
| **CLAHE** | 2 | 4 | 50% |
| **VideoStream** | 10 | 28 | 36% |
| **General/System** | 2 | ~13 | 15% |
| **Advanced Modules** | 0 | ~100+ | 0% |

### **TOTAL ESTIMATED COVERAGE: ~20-25%**

---

## PRIORITY RECOMMENDATIONS FOR NEXT IMPLEMENTATION

### **HIGH PRIORITY** (Core functionality gaps)
1. ✅ **Image Flip** - Essential for mounting orientations
2. ✅ **Video Overlay Controls** - Crosshair, timestamp, position display
3. ✅ **Camera Settings** - Exposure, white balance, gain
4. ✅ **MotorControl Queries** - Query current limits, speeds, positions
5. ✅ **Zero Position Commands** - SetZero, ResetZero for calibration

### **MEDIUM PRIORITY** (Enhanced functionality)
6. ⚠️ **VideoTracker** - Auto-tracking capability
7. ⚠️ **MotionDetector** - Motion detection alerts
8. ⚠️ **Iris Control** - Auto-iris, manual iris
9. ⚠️ **Advanced VideoStream** - RTMP, HLS, SRT, RTP streaming
10. ⚠️ **VideoStabiliser Advanced** - Offset limits, stabilization tuning

### **LOW PRIORITY** (Specialized/Hardware-specific)
11. 🔵 **Laser Rangefinder** (if hardware present)
12. 🔵 **Speaker Control** (if hardware present)
13. 🔵 **Laser/PeakBeam Illuminators** (if hardware present)
14. 🔵 **Classification** (AI feature, license required)
15. 🔵 **ChangesDetector** (License required)

---

## NOTES

1. **Protocol Coverage**: The application implements basic control and configuration. Advanced AI features, tracking, and specialized hardware modules are not implemented.

2. **GUI vs Protocol**: Some features have protocol support but no GUI controls (marked ⚠️). These could be quickly exposed in the UI.

3. **Hardware Dependencies**: Many unimplemented features require specific hardware (LRF, illuminators, speakers) that may not be present on all MK4 units.

4. **License Requirements**: VideoTracker, VideoStabiliser, MotionDetector, ChangesDetector, and Classification require software licenses.

5. **Testing Needed**: Implemented features (✅) have not all been tested on hardware yet.

---

**End of Audit**
