# UP Protocol Implementation Guide

## Protocol Overview

The External UP Protocol uses a **string-based format**, not binary:

```
ID:N/MessageType/Module/Submodule/Parameter
```

### Message Types

- **Command**: Trigger action or set parameter
- **Query**: Request current value
- **Reply**: Response to Query with data
- **Ack**: Acknowledgment of successful Command
- **Nac**: Negative acknowledgment (error)

### Communication

- **Protocol**: UDP or TCP
- **Default Port**: 34030 (UDP) or 34030 (TCP)
- **Format**: ASCII strings ending with '\n'

## Key Modules


### " + command + "\n";

Total commands: 1

Example commands:
- `command = "ID:0/Command/" + command + "\n";`


### Camera1

Total commands: 55

Example commands:
- `ID:0/Command/Camera1/Lens/ZoomIn`
- `ID:3/Command/Camera1/VideoStabiliser/On`
- `ID:4/Command/Camera1/VideoTracker/Reset`
- `[client -> system] ID:14/Command/Camera1/Lens/ZoomToPos:12000 - Go to zoom position 12000.`
- `[client -> system] ID:15/Command/Camera1/Lens/AfRoiMode:0 - Set auto focus ROI to auto detection`
  *(and 50 more...)*


### Camera2

Total commands: 49

Example commands:
- `ID:1/Command/Camera2/Camera/Profile:2`
- `[client -> system] ID:16/Query/Camera2/Lens/FocusPos - Query focus position from camera 2.`
- `[system -> client] ID:16/Reply/Camera2/Lens/FocusPos:100 - Focus position from camera 2.`
- `[client -> system] ID:20/Query/Camera2/Camera/ChangingMode - Query changing mode from camera 2.`
- `[system -> client] ID:20/Reply/Camera2/Camera/ChangingMode:1 - Changing mode is auto.`
  *(and 44 more...)*


### Camera3

Total commands: 4

Example commands:
- `[client -> system] ID:17/Query/Camera3/Lens/IsAfActive - Query auto focus status.`
- `[system -> client] ID:17/Reply/Camera3/Lens/IsAfActive:0 - Auto focus not active.`
- `[client -> system] ID:21/Query/Camera3/Camera/IsConnected - Query connection status.`
- `[system -> client] ID:21/Reply/Camera3/Camera/IsConnected:1 - Connected.`


### Companion1

Total commands: 2

Example commands:
- `[client -> system] ID:56/Command/Companion1/WiperMode:1 - Enable wiper in payload board 1.`
- `[client -> system] ID:57/Command/Companion1/HeaterMode:1 - Enable heater in payload board 1.`


### Companion2

Total commands: 2

Example commands:
- `[client -> system] ID:58/Query/Companion2/PowerChannel1Mode - Query power channel 1 mode from`
- `[system -> client] ID:58/Reply/Companion2/PowerChannel1Mode:1 - Reply about power channel 1 mode`


### CompanionMain

Total commands: 4

Example commands:
- `ID:2/Query/CompanionMain/PowerChannel1Temperature channel of companion board`
- `ID:2/Reply/CompanionMain/PowerChannel1Temperature:50`
- `[client -> system] ID:59/Query/CompanionMain/MainTemperature - Query main temperature from main`
- `[system -> client] ID:59/Reply/CompanionMain/MainTemperature:56 - Reply about main temperature`


### ExternalUp

Total commands: 5

Example commands:
- `[client -> system] ID:106/Command/ExternalUp/UdpPort:34020 - Set UDP port to 34020.`
- `[client -> system] ID:107/Query/ExternalUp/UdpPort - Query UDP port.`
- `[system -> client] ID:107/Reply/ExternalUp/UdpPort:34020 - Current UDP port is 34020.`
- `[client -> system] ID:108/Query/ExternalUp/TcpPort - Query TCP port.`
- `[system -> client] ID:108/Reply/ExternalUp/TcpPort:34030 - Current TCP port is 34030.`


### G5Laser

Total commands: 14

Example commands:
- `[client -> system] ID:90/Command/G5Laser/MODE/ARM:ON - Arm the laser.`
- `[client -> system] ID:91/Command/G5Laser/MODE/LIGHT:BEAM - Turn on light in BEAM mode.`
- `[client -> system] ID:92/Command/G5Laser/ARM-TIME:30 - Set auto-disarm timeout to 30 seconds.`
- `[client -> system] ID:93/Command/G5Laser/BEAM-TIME:60 - Set beam/strobe auto-off timeout to 60`
- `[client -> system] ID:94/Command/G5Laser/STROBE-TIME/ON:100 - Set strobe ON duration to 100 ms.`
  *(and 9 more...)*


### General

Total commands: 3

Example commands:
- `[client -> system] ID:76/Command/General/SlaveZoomMode:1 - Enable slave zoom mode.`
- `[client -> system] ID:79/Query/General/VideoTrackerToken - Query video tracker license token.`
- `ID:79/Reply/General/VideoTrackerToken:C7018FFD1BBE58C96DDD2534FF601FC62A112846FD13C30E5D`


### Lrf

Total commands: 7

Example commands:
- `[client -> system] ID:64/Command/Lrf/PointerMode:1 - Enable laser pointer.`
- `[client -> system] ID:65/Command/Lrf/Measure - Measure distance once.`
- `[client -> system] ID:66/Query/Lrf/PointerModeTimeoutSec - Query pointer mode timeout.`
- `[system -> client] ID:66/Reply/Lrf/PointerModeTimeoutSec:10 - Reply about pointer mode timeout.`
- `[client -> system] ID:67/Query/Lrf/Distance - Query measured distance.`
  *(and 2 more...)*


### MotorControl

Total commands: 5

Example commands:
- `[client -> system] ID:10/Command/MotorControl/Pan/ToPos:120.5 - go to pan position 120.5 degree.`
- `[client -> system] ID:11/Command/MotorControl/Pan/ToPos:500 - go to pan position 500 degree.`
- `[client -> system] ID:12/Query/MotorControl/Tilt/DownLimit - Query tilt down limit.`
- `[system -> client] ID:12/Reply/MotorControl/Tilt/DownLimit:-60.1 - tilt down limit -60 degree.`
- `[client -> system] ID:13/Command/MotorControl/Pan/RightLimit:10.8 - Set right pan limit to 10.8 degree.`


### PeakBeam

Total commands: 15

Example commands:
- `[client -> system] ID:100/Command/PeakBeam/Mode:BEAM - Set operating mode BEAM.`
- `[client -> system] ID:101/Command/PeakBeam/Level:High - Set light intensity to High.`
- `[client -> system] ID:102/Command/PeakBeam/StrobeRate:15 - Set strobe frequency to 15 Hz.`
- `[client -> system] ID:103/Command/PeakBeam/ZoomRate:50 - Set zoom speed to 50%.`
- `[client -> system] ID:104/Command/PeakBeam/ToPos:75 - Move zoom to position 75.`
  *(and 10 more...)*


### PelcoD

Total commands: 5

Example commands:
- `[client -> system] ID:106/Command/PelcoD/UdpPort:34000 - Set UDP port to 34000.`
- `[client -> system] ID:107/Query/PelcoD/UdpPort - Query UDP port.`
- `[system -> client] ID:107/Reply/PelcoD/UdpPort:34000 - Current UDP port is 34000.`
- `[client -> system] ID:108/Query/PelcoD/TcpPort - Query TCP port.`
- `[system -> client] ID:108/Reply/PelcoD/TcpPort:34010 - Current TCP port is 34010.`


### ProcedureManager

Total commands: 3

Example commands:
- `[client -> system] ID:82/Command/ProcedureManager/GoToPreset:2 - Go to preset 2.`
- `ID:82/Command/ProcedureManager/GoToPreset:2\nID:83/Command/Camera1/Lens/ZoomIn\nID:84/`
- `ID:82/Command/ProcedureManager/GoToPreset:2\nID:83/Command/Camera1/Lens/ZoomIn\nID:84/`


### Speaker

Total commands: 5

Example commands:
- `[client -> system] ID:64/Command/Speaker/Play:clip1.mp3 - Play clip1.mp3.`
- `[client -> system] ID:65/Command/Speaker/Stop - Stop playback.`
- `[client -> system] ID:66/Query/Speaker/Volume - Query playback volume.`
- `[system -> client] ID:66/Reply/Speaker/Volume:10 - Reply about playback volume (10%).`
- `[client -> system] ID:67/Command/Speaker/Volume:20 - Set playback volume to 20%.`


## Implementation Steps

1. **Update network layer** to support string-based commands
2. **Create command builders** for each module/submodule
3. **Add parsers** for Reply messages
4. **Update GUI** to add new control buttons
5. **Test** with actual hardware

## Current Implementation Status

Your current `network/up_protocol.py` uses **binary format** (magic bytes 0x5550).
The PDF describes **string-based format** (ID:N/Command/...).

**ACTION REQUIRED:** Verify which protocol format your MK4 hardware actually uses:
- Binary (current implementation)
- String-based (from PDF specification)
- Both (depending on port or configuration)
