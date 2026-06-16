# Critical Port Fix: 58004 → 34030

## Problem Found in Logs

Commands were being built and sent correctly, but **sent to the wrong port**:

```
Line 12: UP protocol UDP socket created for port 58004
Line 14: Sent EUP protocol test command to 192.168.1.81:58004
Line 48: Sent EUP command: ID:2/Command/MotorControl/Pan/ToPos:0.0
Line 89: Sent EUP command: ID:14/Command/Camera1/Lens/ZoomIn
```

✅ Commands are being generated correctly  
✅ Commands are being sent via UDP  
❌ **Commands are being sent to port 58004**  
❌ **No responses received from hardware**

## Root Cause

The application was configured to use **port 58004** which appears to be for a different protocol (possibly the old binary UP protocol).

According to **External UP Protocol v2.4.7 specification**, EUP uses:
- **Port 34030** for UDP
- **Port 34030** for TCP

## Fix Applied

### Changed Port Configuration

**File: `config/default_config.json`**
```json
"up_protocol_port": 34030  // Changed from 58004
```

**File: `utils/constants.py`**
```python
UP_PROTOCOL_PORT = 34030  # Changed from 58004
```

## Evidence from Specification

From `tools/UP_IMPLEMENTATION_GUIDE.md`:
```
### Communication

- **Protocol**: UDP or TCP
- **Default Port**: 34030 (UDP) or 34030 (TCP)
- **Format**: ASCII strings ending with '\n'
```

From `tools/pdf_text_sample.txt`:
```
The External Control Universal Protocol (EUP) is designed to allow external 
systems to control the NexOS platform and receive data from it. EUP uses UDP 
or TCP communication, where NexOS listens on a specific UDP / TCP port 
(port 34030 by default for UDP and 34030 for TCP)
```

## What Should Happen Now

### Before Fix:
```
Application sends to: 192.168.1.81:58004
Hardware listening on: 192.168.1.81:34030
Result: Commands never reach hardware ❌
```

### After Fix:
```
Application sends to: 192.168.1.81:34030
Hardware listening on: 192.168.1.81:34030
Result: Hardware receives and processes commands ✅
```

## Testing Instructions

1. **Restart the application** (old port cached in memory)
2. **Connect to MK4** (192.168.1.81)
3. **Check logs** - should now show:
   ```
   UP protocol UDP socket created for port 34030
   Sent EUP protocol test command to 192.168.1.81:34030
   ```
4. **Try PTZ control** - should now work!
5. **Watch for responses**:
   ```
   Received EUP response: ID:0/Ack
   Received EUP response: ID:6/Reply/MotorControl/Pan/Pos:120.5
   ```

## Expected Log Output After Fix

```
[INFO] UP protocol UDP socket created for port 34030
[INFO] Sent EUP protocol test command to 192.168.1.81:34030
[DEBUG] Sent EUP command: ID:2/Command/MotorControl/Pan/ToPos:120.5
[DEBUG] Received EUP response: ID:2/Ack
[DEBUG] Sent EUP command: ID:3/Query/MotorControl/Pan/Pos
[DEBUG] Received EUP response: ID:3/Reply/MotorControl/Pan/Pos:120.5
```

## Port Summary

| Protocol | Port | Usage |
|----------|------|-------|
| TCP Pelco | 54000 | Legacy Pelco-D protocol (optional) |
| UDP Telemetry | 58000 | Old telemetry reception (may not be used) |
| **EUP (External UP)** | **34030** | **String-based commands (CORRECT)** |
| ~~Old UP Binary~~ | ~~58004~~ | ~~Wrong protocol (REMOVED)~~ |

## Why This Wasn't Caught Earlier

1. The original binary protocol implementation used port 58004
2. When migrating to EUP, the port wasn't updated
3. No error was raised because UDP doesn't require connection
4. Commands were sent into the void with no response

## Files Modified

- ✅ `config/default_config.json` - Updated port to 34030
- ✅ `utils/constants.py` - Updated UP_PROTOCOL_PORT to 34030

## Verification

After restarting the application:
1. Check connection log shows port 34030
2. Try pan/tilt control
3. Hardware should respond
4. Position feedback should update
5. Zoom/focus should work

---

**Status**: ✅ Port configuration fixed, application needs restart
