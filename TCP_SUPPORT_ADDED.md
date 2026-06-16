# TCP Support Added for EUP Protocol

## Problem Analysis from Logs

From the latest logs (`mk4_control_20260616_131413.log`):

```
Line 12: UP protocol UDP socket created for port 34030  ✅ Correct port
Line 14: Sent EUP protocol test command to 192.168.1.81:34030  ✅ Correct destination
Lines 45-150: Multiple EUP commands sent via UDP  ✅ Commands formatted correctly
```

**BUT:** No responses received from hardware at all!

```bash
$ grep -i "received\|response\|ack\|reply" log.txt
# NO RESULTS - Hardware is not responding via UDP
```

## Root Cause Hypothesis

The MK4 hardware may require **TCP** instead of UDP for EUP protocol, even though the specification says both are supported.

From the spec:
> "EUP uses UDP or TCP communication, where NexOS listens on a specific UDP / TCP port (port 34030 by default for UDP and 34030 for TCP)"

## Solution Implemented

### 1. Try TCP Connection on Port 34030 First

**Modified:** `network/network_manager.py` - `connect()` method

Now tries:
1. **TCP on port 34030** (EUP protocol)
2. If that fails, try TCP on port 54000 (legacy Pelco)
3. Fall back to UDP if TCP not available

```python
# Try TCP connection to EUP port (34030) first
logger.info(f"Attempting TCP connection to {self.target_ip}:{self.up_protocol_port} (EUP)")
self.tcp_reader, self.tcp_writer = await asyncio.open_connection(
    self.target_ip, 
    self.up_protocol_port  # 34030
)
```

### 2. Prefer TCP Over UDP for Commands

**Modified:** All command methods now check if TCP is available and use it first:

```python
async def send_pan_tilt(self, pan: float, tilt: float) -> bool:
    command = self.eup_protocol.build_pan_tilt_absolute(pan, tilt)
    # Try TCP first if available, fall back to UDP
    use_tcp = self.tcp_writer is not None
    return await self.send_command(command, use_udp=not use_tcp)
```

### 3. Listen for TCP Responses

**Modified:** `receive_telemetry()` now reads from both TCP and UDP:

```python
# Try reading from TCP if available
if self.tcp_reader:
    line = await asyncio.wait_for(self.tcp_reader.readline(), timeout=0.001)
    if line:
        response_str = line.decode('utf-8', errors='ignore').strip()
        logger.debug(f"Received EUP response (TCP): {response_str}")

# Also try UDP
if self.udp_socket:
    data, addr = self.udp_socket.recvfrom(1024)
    if data:
        response_str = data.decode('utf-8', errors='ignore').strip()
        logger.debug(f"Received EUP response (UDP): {response_str}")
```

## Expected Behavior After Fix

### Successful TCP Connection

```
[INFO] Attempting TCP connection to 192.168.1.81:34030 (EUP)
[INFO] TCP connection established (EUP protocol available)
[DEBUG] Sent EUP command via TCP: ID:2/Command/MotorControl/Pan/ToPos:120.5
[DEBUG] Received EUP response (TCP): ID:2/Ack
[DEBUG] Sent EUP command via TCP: ID:3/Query/MotorControl/Pan/Pos
[DEBUG] Received EUP response (TCP): ID:3/Reply/MotorControl/Pan/Pos:120.5
```

### TCP Not Available (Falls Back to UDP)

```
[WARNING] TCP connection to EUP port not available
[INFO] UP protocol UDP socket created for port 34030
[DEBUG] Sent EUP command: ID:2/Command/MotorControl/Pan/ToPos:120.5
[DEBUG] Received EUP response (UDP): ID:2/Ack
```

## Testing Instructions

1. **Restart the application** to apply the changes
2. **Connect to MK4** (192.168.1.81)
3. **Watch connection log** - should show:
   - "Attempting TCP connection to 192.168.1.81:34030 (EUP)"
   - Either "TCP connection established" or falls back to UDP
4. **Try PTZ control**
5. **Watch for responses**:
   - "Received EUP response (TCP): ID:X/Ack"
   - "Received EUP response (TCP): ID:X/Reply/..."

## Why TCP Might Be Required

Possible reasons:
1. **Firewall rules** - MK4 firewall may block UDP but allow TCP
2. **NexOS configuration** - MK4 may be configured for TCP-only
3. **Reliability** - TCP ensures command delivery with ACKs
4. **Request-Response** - TCP stream better suits request-response protocol
5. **Multiple commands** - TCP maintains connection state

## Command Flow Comparison

### Before (UDP Only):
```
App --> UDP:34030 --> MK4
App <-- UDP:34030 <-- MK4  ❌ No response
```

### After (TCP Preferred):
```
App --> TCP:34030 --> MK4 (connected)
App <-- TCP:34030 <-- MK4  ✅ Responses received
```

### After (UDP Fallback):
```
App --> UDP:34030 --> MK4
App <-- UDP:34030 <-- MK4  ✅ (if UDP works)
```

## Verification Checklist

After restarting:

- [ ] TCP connection attempt shows in log
- [ ] Either TCP establishes or falls back to UDP gracefully
- [ ] Commands show as sent via TCP or UDP
- [ ] **Responses are received** (Ack/Nac/Reply)
- [ ] PTZ controls move the gimbal
- [ ] Position feedback updates in GUI
- [ ] Zoom/focus commands work

## Files Modified

- ✅ `network/network_manager.py`:
  - `connect()` - Try TCP on 34030 first
  - `send_pan_tilt()` - Prefer TCP over UDP
  - `send_stop()` - Prefer TCP over UDP
  - `send_zoom()` - Prefer TCP over UDP
  - `send_focus()` - Prefer TCP over UDP
  - `receive_telemetry()` - Listen on both TCP and UDP

---

**Status**: ✅ TCP support added, ready to test with hardware
