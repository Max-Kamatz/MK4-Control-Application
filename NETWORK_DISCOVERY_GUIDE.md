# Network Discovery Feature Guide

## Overview

The application now includes a network discovery feature that pings and checks payload availability **before** attempting to connect. This prevents long connection timeouts to non-existent payloads.

## How It Works

### Discovery Button (🔍 Check)

Located next to the IP address input field in the "Connection" section.

**What it does:**
1. **Ping Test** - Checks if the host responds to ICMP ping
2. **Control Port Check** - Verifies TCP port 54000 is open (gimbal control)
3. **Video Port Check** - Verifies TCP port 7031 is open (RTSP streams)

**Discovery takes ~1-3 seconds** and runs in a background thread (GUI stays responsive).

### Status Indicators

After clicking "🔍 Check", you'll see one of these status messages:

#### ✅ Available
```
✅ Available: Ping ✓, Control ✓, Video ✓
```
All services are responding - safe to connect!

#### ⚠️ Partial Availability
```
✅ Available: Ping ✓, Control ✓
```
Host is reachable and control works, but video streams may not be available.

#### ❌ Not Available
```
❌ No payload found
```
Host is not responding - check IP address or network connectivity.

#### ⚪ Not Checked
```
⚪ Not checked
```
No discovery has been performed yet for this IP address.

## Recommended Workflow

### Step 1: Enter IP Address
Type the target payload IP address (e.g., `192.168.1.81`)

### Step 2: Click "🔍 Check"
The discovery process starts:
- Button text changes to "Checking..."
- Status shows "🔄 Discovering..."

### Step 3: Review Results
Wait 1-3 seconds for results:
- ✅ Green = Safe to connect
- ❌ Red = Don't waste time trying to connect

### Step 4: Connect (if available)
If the discovery shows "✅ Available", click **"Connect"**

The application will:
1. Establish TCP control connection (fast - already verified open)
2. Start RTSP video streams (only after TCP succeeds)
3. Begin receiving telemetry

## Benefits

### Before Network Discovery:
- Blind connection attempts
- Long timeouts (15-30 seconds per failed stream)
- No indication if payload exists
- Wasted time on unreachable devices

### After Network Discovery:
- ✅ Know payload status **before** connecting
- ✅ Fast discovery (1-3 seconds)
- ✅ Visual confirmation of available services
- ✅ No wasted time on unreachable IPs
- ✅ Video streams only start after successful connection

## Technical Details

### Ports Checked:
- **Port 54000** (TCP) - Pelco gimbal control protocol
- **Port 7031** (TCP) - RTSP video streaming

### Timeouts:
- Ping: 1 second
- Port checks: 1 second each
- Total discovery time: ~3 seconds maximum

### Background Thread:
Discovery runs in a separate thread to keep the GUI responsive. You can continue using the application while discovery is in progress.

## No Auto-Connect on Startup

The application no longer attempts to connect to video streams on startup. Streams only begin connecting when:
1. You click "🔍 Check" (starts discovery, but not video streams)
2. You click "Connect" AND TCP connection succeeds
3. Video streams start connecting in parallel

This prevents the 30-60 second startup delay when default IP addresses aren't available.

## Use Cases

### Testing Multiple Payloads
1. Enter first IP → Check → Not available
2. Enter second IP → Check → Available! → Connect

### Network Troubleshooting
Discovery results help diagnose network issues:
- Ping ✓, Control ✗, Video ✗ → Firewall blocking ports?
- Ping ✗ → Host unreachable / wrong IP / not powered on
- Ping ✓, Control ✓, Video ✗ → RTSP server not running

### Pre-Flight Checks
Before field operations, quickly verify all payloads are online and responding.
