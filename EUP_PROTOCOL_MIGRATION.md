# EUP Protocol Migration - String-Based Implementation

## Problem

PTZ (pan/tilt/zoom) controls were not functioning because the application was using an **incorrect binary protocol format** instead of the **string-based External Universal Protocol (EUP)** that the MK4 hardware actually uses.

## Root Cause

The original implementation in `network/up_protocol.py` used:
- Binary format with magic bytes `0x5550`
- Binary payload with `struct.pack()`
- CRC16 checksums

But the External UP Protocol specification (v2.4.7) clearly states it is **string-based**:
```
ID:N/MessageType/Module/Submodule/Parameter\n
```

## Solution

### 1. Created New EUP Protocol Implementation

**File:** `network/eup_protocol.py`

Implements the correct string-based protocol:
```python
# Example commands:
"ID:0/Command/MotorControl/Pan/ToPos:120.5\n"
"ID:1/Command/MotorControl/Tilt/ToPos:-45.2\n"
"ID:2/Query/MotorControl/Pan/Pos\n"
```

**Key features:**
- String-based command generation
- Sequence number management
- Command builders for:
  - Pan/Tilt absolute positioning
  - Pan/Tilt speed control
  - Zoom control (Camera1/2/3)
  - Focus control (Camera1/2/3)
  - Stop commands
  - Position queries
  - Camera profiles
  - Video stabilization
  - Digital zoom
  - Image enhancement (CLAHE, color filters)
- Response parser for Ack/Nac/Reply messages

### 2. Updated Network Manager

**File:** `network/network_manager.py`

Changes:
- Replaced `from network.up_protocol import UPProtocol` with `from network.eup_protocol import EUPProtocol`
- Updated `send_command()` to handle strings instead of bytes
- Updated telemetry reception to decode string responses
- All command methods now use EUP protocol

### 3. Command Extraction Tool

**Files:**
- `tools/extract_up_commands_v2.py` - PDF extraction tool
- `tools/UP_COMMANDS_REPORT.md` - Extracted command list (179 commands, 16 modules)
- `tools/UP_IMPLEMENTATION_GUIDE.md` - Implementation guide

**Extracted Modules:**
- MotorControl (5 commands)
- Camera1/2/3 (108 total commands)
- Lens control
- Image processing
- Video stabilization
- General system commands
- Laser/LRF control
- And more...

## Protocol Format

### Message Structure

```
ID:<sequence>/MessageType/Module/Submodule/Parameter[:Value]\n
```

### Message Types

- **Command**: Trigger action or set parameter
- **Query**: Request current value
- **Reply**: Response to Query with data
- **Ack**: Acknowledgment of successful Command
- **Nac**: Negative acknowledgment (error)

### Communication

- **Protocol**: UDP (primary) or TCP
- **Port**: 34030 (UDP) or 34030 (TCP)
- **Format**: ASCII strings ending with `\n`
- **Encoding**: UTF-8

## Examples

### Pan/Tilt Control

```python
# Absolute positioning
"ID:0/Command/MotorControl/Pan/ToPos:120.5\n"
"ID:1/Command/MotorControl/Tilt/ToPos:-45.2\n"

# Speed control
"ID:2/Command/MotorControl/Pan/Speed:10.0\n"  # 10 deg/sec right
"ID:3/Command/MotorControl/Tilt/Speed:-5.0\n"  # 5 deg/sec down

# Stop
"ID:4/Command/MotorControl/Pan/Speed:0\n"
"ID:5/Command/MotorControl/Tilt/Speed:0\n"

# Query position
"ID:6/Query/MotorControl/Pan/Pos\n"
# Response: "ID:6/Reply/MotorControl/Pan/Pos:120.5\n"
```

### Camera Control

```python
# Zoom
"ID:10/Command/Camera1/Lens/ZoomIn\n"
"ID:11/Command/Camera1/Lens/ZoomOut\n"
"ID:12/Command/Camera1/Lens/ZoomStop\n"
"ID:13/Command/Camera1/Lens/ZoomToPos:12000\n"

# Focus
"ID:20/Command/Camera1/Lens/FocusFar\n"
"ID:21/Command/Camera1/Lens/FocusNear\n"
"ID:22/Command/Camera1/Lens/FocusStop\n"
"ID:23/Command/Camera1/Lens/AfMode:1\n"  # Auto focus on

# Stabilization
"ID:30/Command/Camera1/VideoStabiliser/On\n"
"ID:31/Command/Camera1/VideoStabiliser/Off\n"

# Digital Zoom
"ID:40/Command/Camera1/DigitalZoom/On\n"
"ID:41/Command/Camera1/DigitalZoom/Level:2.0\n"  # 2x digital zoom

# Image Enhancement
"ID:50/Command/Camera1/Clahe/On\n"  # CLAHE filter
"ID:51/Command/Camera1/ColorFilter/Palette:1\n"  # Inverse palette
```

## Testing

### Expected Behavior After Migration

1. **Pan/Tilt Control**: 
   - Trackpad should now control gimbal position
   - Position feedback should update in GUI

2. **Zoom Control**: 
   - Zoom In/Out buttons should work
   - Camera should respond to zoom commands

3. **Focus Control**: 
   - Focus Far/Near buttons should work
   - Camera should adjust focus

4. **Connection**:
   - UDP connection on port 34030
   - Commands sent as UTF-8 strings
   - Responses received as UTF-8 strings

### Debug Logging

Check logs (Ctrl+L) for:
```
[DEBUG] Built EUP command: ID:0/Command/MotorControl/Pan/ToPos:120.5
[DEBUG] Sent EUP command: ID:0/Command/MotorControl/Pan/ToPos:120.5
[DEBUG] Received EUP response: ID:0/Ack
[DEBUG] Received EUP response: ID:6/Reply/MotorControl/Pan/Pos:120.5
```

## Benefits

1. **Correct Protocol**: Now using the actual protocol the hardware expects
2. **Human Readable**: String commands are easy to debug
3. **Extensible**: Easy to add new commands from the 179 extracted commands
4. **Better Logging**: Can see exactly what commands are being sent
5. **Standards Compliant**: Matches External UP Protocol v2.4.7 specification

## Future Enhancements

Additional commands available to implement (from extracted list):
- Camera profiles/presets
- Motion detection
- Video tracking
- Bad pixel correction
- Motion magnification
- Overlay control
- Laser range finder
- Speaker control
- Companion board control (wiper, heater, power channels)
- Procedure manager (presets)

## Files Modified

- `network/eup_protocol.py` - **NEW** - String-based EUP implementation
- `network/network_manager.py` - Updated to use EUP instead of binary protocol
- `tools/extract_up_commands_v2.py` - **NEW** - PDF extraction tool
- `tools/UP_COMMANDS_REPORT.md` - **NEW** - Extracted command list
- `tools/UP_IMPLEMENTATION_GUIDE.md` - **NEW** - Implementation guide
- `EUP_PROTOCOL_MIGRATION.md` - **NEW** - This document

## Files To Deprecate

- `network/up_protocol.py` - Old binary implementation (can be deleted after testing)
- `config/up_protocol_commands.json` - Binary command IDs (no longer needed)

## References

- External UP Protocol Specification v2.4.7 (`Reference Material/External_UP_protocol_v2.4.7.pdf`)
- 179 extracted command examples in `tools/UP_COMMANDS_REPORT.md`
