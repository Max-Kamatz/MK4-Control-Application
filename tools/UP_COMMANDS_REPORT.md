# UP Protocol Commands - Extracted from PDF

**Source:** Reference Material\External_UP_protocol_v2.4.7.pdf
**Protocol Type:** string-based
**Format:** `ID:N/MessageType/Module/Submodule/Parameter`
**Total Commands Found:** 179
**Total Modules:** 16

## Module List

- **" + command + "\n";** (1 commands)
- **Camera1** (55 commands)
- **Camera2** (49 commands)
- **Camera3** (4 commands)
- **Companion1** (2 commands)
- **Companion2** (2 commands)
- **CompanionMain** (4 commands)
- **ExternalUp** (5 commands)
- **G5Laser** (14 commands)
- **General** (3 commands)
- **Lrf** (7 commands)
- **MotorControl** (5 commands)
- **PeakBeam** (15 commands)
- **PelcoD** (5 commands)
- **ProcedureManager** (3 commands)
- **Speaker** (5 commands)

## Commands by Module


### " + command + "\n"; Module

Found 1 command examples:

**Command:** `command = "ID:0/Command/" + command + "\n";`
  - *Description:* cin >> command;


### Camera1 Module

Found 55 command examples:


#### Camera1/BadPixelProcessor

**Command:** `[client -> system] ID:72/Command/Camera1/BadPixelProcessor/Mode:1 - Enable bad pixel correction.`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:73/Command/Camera1/BadPixelProcessor/ChangeThreshold:40 - Set change`
  - *Description:* [system -> client] ID:72/Ack - Command accepted.

**Command:** `[client -> system] ID:74/Query/Camera1/BadPixelProcessor/LowThreshold - Query low threshold.`
  - *Description:* [system -> client] ID:73/Ack - Command accepted.

**Command:** `[system -> client] ID:74/Reply/Camera1/BadPixelProcessor/LowThreshold:20 - Reply about low`
  - *Description:* [client -> system] ID:74/Query/Camera1/BadPixelProcessor/LowThreshold - Query low threshold.

**Command:** `[client -> system] ID:75/Query/Camera1/BadPixelProcessor/HighThreshold - Query high threshold.`
  - *Description:* threshold.

**Command:** `[system -> client] ID:75/Reply/Camera1/BadPixelProcessor/HighThreshold:235 - Reply about high`
  - *Description:* [client -> system] ID:75/Query/Camera1/BadPixelProcessor/HighThreshold - Query high threshold.


#### Camera1/Camera

**Command:** `[client -> system] ID:18/Command/Camera1/Camera/Profile:2 - Set camera settings profile 2.`
  - *Description:* [system -> client] ID:17/Ack - command accepted.

**Command:** `[client -> system] ID:19/Command/Camera1/Camera/ChangingMode:1 - Set changing mode (day / night)`
  - *Description:* [system -> client] ID:18/Ack - command accepted.


#### Camera1/ChangesDetector

**Command:** `[client -> system] ID:34/Command/Camera1/ChangesDetector/Reset - Reset changes detector of camera`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:35/Command/Camera1/ChangesDetector/MaxObjectWidth:100 - Set maximum`
  - *Description:* [system -> client] ID:34/Ack - Command accepted.


#### Camera1/Clahe

**Command:** `[client -> system] ID:52/Command/Camera1/Clahe/On - Enable clahe filter in camera 1.`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:53/Command/Camera1/Clahe/Type:1 - Set clahe type in camera 1.`
  - *Description:* [system -> client] ID:52/Ack - Command accepted.


#### Camera1/Classification

**Command:** `[client -> system] ID:38/Command/Camera1/Classification/Reset - Reset classification of camera 1.`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:39/Command/Camera1/Classification/MaxObjectWidth:100 - Set maximum object`
  - *Description:* [system -> client] ID:38/Ack - Command accepted.


#### Camera1/ColorFilter

**Command:** `[client -> system] ID:48/Command/Camera1/ColorFilter/On - Enable color filter in camera 1.`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:49/Command/Camera1/ColorFilter/Palette:1 - Set Inverse palette type in camera 1.`
  - *Description:* [system -> client] ID:48/Ack - Command accepted.


#### Camera1/DigitalZoom

**Command:** `[client -> system] ID:42/Command/Camera1/DigitalZoom/On - Enable digital zoom in camera 1.`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:43/Command/Camera1/DigitalZoom/Level:1.5 - Set digital zoom level for camera 1.`
  - *Description:* [system -> client] ID:42/Ack - Command accepted.


#### Camera1/ImageFlip

**Command:** `[client -> system] ID:46/Command/Camera1/ImageFlip/Mode:1 - Set left-right image flip in camera 1.`
  - *Description:* Some example messages:


#### Camera1/Lens

**Command:** `ID:0/Command/Camera1/Lens/ZoomIn`
  - *Description:* Command to move zoom in (tele)

**Command:** `[client -> system] ID:14/Command/Camera1/Lens/ZoomToPos:12000 - Go to zoom position 12000.`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:15/Command/Camera1/Lens/AfRoiMode:0 - Set auto focus ROI to auto detection`
  - *Description:* [system -> client] ID:14/Ack - Command accepted.

**Command:** `ID:84/Reply/Camera1/Lens/FocusPos:10000`
  - *Description:* ID:83/Ack

**Command:** `ID:0/Command/Camera1/Lens/ZoomIn`
  - *Description:* UP string-based command (from client to system):


#### Camera1/MotionDetector

**Command:** `[client -> system] ID:30/Command/Camera1/MotionDetector/Reset - Reset motion detector of camera 1.`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:31/Command/Camera1/MotionDetector/MaxObjectWidth:100 - Set maximum`
  - *Description:* [system -> client] ID:30/Ack - Command accepted.


#### Camera1/MotionMagnificator

**Command:** `[client -> system] ID:52/Command/Camera1/MotionMagnificator/On - Enable motion magnification in`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:53/Command/Camera1/MotionMagnificator/Level:10 - Set motion magnification`
  - *Description:* [system -> client] ID:52/Ack - Command accepted.


#### Camera1/Overlay

**Command:** `[client -> system] ID:72/Command/Camera1/Overlay/CrossHairMode:1 - Enable cross hair display for`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:73/Command/Camera1/Overlay/CrossHairSize:40 - Set cross hair size for camera 1.`
  - *Description:* [system -> client] ID:72/Ack - Command accepted.

**Command:** `[client -> system] ID:74/Query/Camera1/Overlay/LrfMode - Query laser range finder display mode from`
  - *Description:* [system -> client] ID:73/Ack - Command accepted.

**Command:** `[system -> client] ID:74/Reply/Camera1/Overlay/LrfMode:1 - Reply about laser range finder display mode`
  - *Description:* camera 1.

**Command:** `[client -> system] ID:75/Query/Camera1/Overlay/FontSize - Query overlay font size from camera 1.`
  - *Description:* from camera 1.

**Command:** `[system -> client] ID:75/Reply/Camera1/Overlay/FontSize:60 - Reply about overlay font size from camera`
  - *Description:* [client -> system] ID:75/Query/Camera1/Overlay/FontSize - Query overlay font size from camera 1.


#### Camera1/Reset - Restart Jafar service for camera 1.

**Command:** `[client -> system] ID:17/Command/Camera1/Reset - Restart Jafar service for camera 1.`
  - *Description:* Some example messages:


#### Camera1/VideoSource

**Command:** `[client -> system] ID:22/Command/Camera1/VideoSource/Restart - Restart video capture module of`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:23/Command/Camera1/VideoSource/Custom1:10 - Set custom parameters of`
  - *Description:* [system -> client] ID:22/Ack - command accepted.


#### Camera1/VideoStabiliser

**Command:** `ID:3/Command/Camera1/VideoStabiliser/On`
  - *Description:* Action command to enable video

**Command:** `[client -> system] ID:26/Command/Camera1/VideoStabiliser/Reset - Reset video stabilizer of camera 1.`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:27/Command/Camera1/VideoStabiliser/TransparentBorderMode:1 - Set`
  - *Description:* [system -> client] ID:26/Ack - command accepted.


#### Camera1/VideoStream1

**Command:** `[client -> system] ID:68/Command/Camera1/VideoStream1/On - Enable first video server of camera 1.`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:69/Command/Camera1/VideoStream1/RtspMulticastPort:7031 - Set RTSP multicast`
  - *Description:* [system -> client] ID:68/Ack - Command accepted.

**Command:** `[client -> system] ID:70/Query/Camera1/VideoStream1/Mode - Query first video server mode of camera 1.`
  - *Description:* 51 / 86

**Command:** `[system -> client] ID:70/Reply/Camera1/VideoStream1/Mode:1 - Reply first video server mode of camera`
  - *Description:* [client -> system] ID:70/Query/Camera1/VideoStream1/Mode - Query first video server mode of camera 1.

**Command:** `[client -> system] ID:71/Query/Camera1/VideoStream1/BitrateKbps - Query bitrate of first video server`
  - *Description:* 1.

**Command:** `[system -> client] ID:71/Reply/Camera1/VideoStream1/BitrateKbps:5000 - Reply about bitrate of first`
  - *Description:* mode of camera 1.


#### Camera1/VideoTracker

**Command:** `ID:4/Command/Camera1/VideoTracker/Reset`
  - *Description:* Action command to reset video

**Command:** `[client -> system] ID:26/Command/Camera1/VideoTracker/Reset - Reset video tracking on camera 1.`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:27/Command/Camera1/VideoTracker/CapturePercents:20.4x36.7 - Capture object`
  - *Description:* [system -> client] ID:26/Ack - command accepted.


#### Camera1/WebRtcOverlay

**Command:** `[client -> system] ID:72/Command/Camera1/WebRtcOverlay/CrossHairMode:1 - Enable cross hair display`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:73/Command/Camera1/WebRtcOverlay/CrossHairSize:40 - Set cross hair size for`
  - *Description:* [system -> client] ID:72/Ack - Command accepted.

**Command:** `[client -> system] ID:74/Query/Camera1/WebRtcOverlay/LrfMode - Query laser range finder display mode`
  - *Description:* [system -> client] ID:73/Ack - Command accepted.

**Command:** `[system -> client] ID:74/Reply/Camera1/WebRtcOverlay/LrfMode:1 - Reply about laser range finder`
  - *Description:* from camera 1.

**Command:** `[client -> system] ID:75/Query/Camera1/WebRtcOverlay/FontSize - Query overlay font size from camera`
  - *Description:* display mode from camera 1.

**Command:** `[system -> client] ID:75/Reply/Camera1/WebRtcOverlay/FontSize:60 - Reply about overlay font size from`
  - *Description:* 1.


### Camera2 Module

Found 49 command examples:


#### Camera2/Camera

**Command:** `ID:1/Command/Camera2/Camera/Profile:2`
  - *Description:* Command to set setting profile 2

**Command:** `[client -> system] ID:20/Query/Camera2/Camera/ChangingMode - Query changing mode from camera 2.`
  - *Description:* [system -> client] ID:19/Ack - command accepted.

**Command:** `[system -> client] ID:20/Reply/Camera2/Camera/ChangingMode:1 - Changing mode is auto.`
  - *Description:* [client -> system] ID:20/Query/Camera2/Camera/ChangingMode - Query changing mode from camera 2.


#### Camera2/ChangesDetector

**Command:** `[client -> system] ID:36/Query/Camera2/ChangesDetector/Mode - Query changes detector mode from`
  - *Description:* [system -> client] ID:35/Ack - Command accepted.

**Command:** `[system -> client] ID:36/Reply/Camera2/ChangesDetector/Mode:1 - Reply about changes detector mode`
  - *Description:* camera 2.

**Command:** `[client -> system] ID:37/Query/Camera2/ChangesDetector/ResetCriteria - Query reset criteria of changes`
  - *Description:* of camera 2.

**Command:** `[system -> client] ID:37/Reply/Camera2/ChangesDetector/ResetCriteria:5 - Reply about reset criteria`
  - *Description:* detector from camera 2.


#### Camera2/Clahe

**Command:** `[client -> system] ID:54/Query/Camera2/Clahe/Mode - Query clahe mode from camera 2.`
  - *Description:* [system -> client] ID:53/Ack - Command accepted.

**Command:** `[system -> client] ID:54/Reply/Camera2/Clahe/Mode:1 - Reply about clahe mode of camera 2.`
  - *Description:* [client -> system] ID:54/Query/Camera2/Clahe/Mode - Query clahe mode from camera 2.

**Command:** `[client -> system] ID:55/Query/Camera2/Clahe/Type - Query clahe type from camera 2.`
  - *Description:* [system -> client] ID:54/Reply/Camera2/Clahe/Mode:1 - Reply about clahe mode of camera 2.

**Command:** `[system -> client] ID:55/Reply/Camera2/Clahe/Type:1 - Reply about clahe type from camera 2.`
  - *Description:* [client -> system] ID:55/Query/Camera2/Clahe/Type - Query clahe type from camera 2.


#### Camera2/Classification

**Command:** `[client -> system] ID:40/Query/Camera2/Classification/Mode - Query classification mode from camera 2.`
  - *Description:* [system -> client] ID:39/Ack - Command accepted.

**Command:** `[system -> client] ID:40/Reply/Camera2/Classification/Mode:1 - Reply about classification mode of camera`
  - *Description:* [client -> system] ID:40/Query/Camera2/Classification/Mode - Query classification mode from camera 2.

**Command:** `[client -> system] ID:41/Query/Camera2/Classification/MinDetectionProbability - Query detection`
  - *Description:* 2.

**Command:** `[system -> client] ID:41/Reply/Camera2/Classification/MinDetectionProbability:50 - Reply about`
  - *Description:* probability threshold of classification from camera 2.


#### Camera2/ColorFilter

**Command:** `[client -> system] ID:50/Query/Camera2/ColorFilter/Mode - Query palette mode from camera 2.`
  - *Description:* [system -> client] ID:49/Ack - Command accepted.

**Command:** `[system -> client] ID:50/Reply/Camera2/ColorFilter/Mode:1 - Reply about palette mode of camera 2.`
  - *Description:* [client -> system] ID:50/Query/Camera2/ColorFilter/Mode - Query palette mode from camera 2.

**Command:** `[client -> system] ID:51/Query/Camera2/ColorFilter/Palette - Query palette type from camera 2.`
  - *Description:* [system -> client] ID:50/Reply/Camera2/ColorFilter/Mode:1 - Reply about palette mode of camera 2.

**Command:** `[system -> client] ID:51/Reply/Camera2/ColorFilter/Palette:1 - Reply about palette type from camera 2.`
  - *Description:* [client -> system] ID:51/Query/Camera2/ColorFilter/Palette - Query palette type from camera 2.


#### Camera2/DigitalZoom

**Command:** `[client -> system] ID:44/Query/Camera2/DigitalZoom/Mode - Query digital zoom mode from camera 2.`
  - *Description:* [system -> client] ID:43/Ack - Command accepted.

**Command:** `[system -> client] ID:44/Reply/Camera2/DigitalZoom/Mode:1 - Reply about digital zoom mode of camera`
  - *Description:* [client -> system] ID:44/Query/Camera2/DigitalZoom/Mode - Query digital zoom mode from camera 2.

**Command:** `[client -> system] ID:45/Query/Camera2/DigitalZoom/Level - Query digital zoom level from camera 2.`
  - *Description:* 2.

**Command:** `[system -> client] ID:45/Reply/Camera2/DigitalZoom/Level:1.5 - Reply about digital zoom level from`
  - *Description:* [client -> system] ID:45/Query/Camera2/DigitalZoom/Level - Query digital zoom level from camera 2.


#### Camera2/ImageFlip

**Command:** `[client -> system] ID:47/Query/Camera2/ImageFlip/Mode - Query image flip mode from camera 2.`
  - *Description:* [system -> client] ID:46/Ack - Command accepted.

**Command:** `[system -> client] ID:47/Reply/Camera2/ImageFlip/Mode:1 - Reply about image flip mode of camera 2.`
  - *Description:* [client -> system] ID:47/Query/Camera2/ImageFlip/Mode - Query image flip mode from camera 2.


#### Camera2/Lens

**Command:** `[client -> system] ID:16/Query/Camera2/Lens/FocusPos - Query focus position from camera 2.`
  - *Description:* [system -> client] ID:15/Ack - Command accepted.

**Command:** `[system -> client] ID:16/Reply/Camera2/Lens/FocusPos:100 - Focus position from camera 2.`
  - *Description:* [client -> system] ID:16/Query/Camera2/Lens/FocusPos - Query focus position from camera 2.


#### Camera2/MotionDetector

**Command:** `[client -> system] ID:32/Query/Camera2/MotionDetector/Mode - Query motion detector mode from`
  - *Description:* [system -> client] ID:31/Ack - Command accepted.

**Command:** `[system -> client] ID:32/Reply/Camera2/MotionDetector/Mode:1 - Reply about motion detector mode of`
  - *Description:* camera 2.

**Command:** `[client -> system] ID:33/Query/Camera2/MotionDetector/ResetCriteria - Query reset criteria of motion`
  - *Description:* camera 2.

**Command:** `[system -> client] ID:33/Reply/Camera2/MotionDetector/ResetCriteria:5 - Reply about reset criteria from`
  - *Description:* detector from camera 2.

**Command:** `ID:2/Query/Camera2/MotionDetector/Mode`
  - *Description:* UP string-based query (from client to system):

**Command:** `ID:2/Reply/Camera2/MotionDetector/Mode:1`
  - *Description:* UP string-based reply (from system to client):


#### Camera2/MotionMagnificator

**Command:** `[client -> system] ID:54/Query/Camera2/MotionMagnificator/Mode - Query motion magnification mode`
  - *Description:* [system -> client] ID:53/Ack - Command accepted.

**Command:** `[system -> client] ID:54/Reply/Camera2/MotionMagnificator/Mode:1 - Reply about motion magnification`
  - *Description:* 45 / 86

**Command:** `[client -> system] ID:55/Query/Camera2/MotionMagnificator/Level - Query motion magnification level`
  - *Description:* mode of camera 2.

**Command:** `[system -> client] ID:55/Reply/Camera2/MotionMagnificator/Level:10 - Reply about motion magnification`
  - *Description:* from camera 2.


#### Camera2/VideoSource

**Command:** `[client -> system] ID:24/Query/Camera2/VideoSource/Width - Query video width from camera 2.`
  - *Description:* [system -> client] ID:23/Ack - command accepted.

**Command:** `[system -> client] ID:24/Reply/Camera2/VideoSource/Width:1920 - Reply about video width of camera 2.`
  - *Description:* 24 / 86

**Command:** `[client -> system] ID:25/Query/Camera2/VideoSource/Height - Query video height from camera 2.`
  - *Description:* [system -> client] ID:24/Reply/Camera2/VideoSource/Width:1920 - Reply about video width of camera 2.

**Command:** `[system -> client] ID:25/Reply/Camera2/VideoSource/Height:1080 - Reply about video height of camera 2.`
  - *Description:* [client -> system] ID:25/Query/Camera2/VideoSource/Height - Query video height from camera 2.


#### Camera2/VideoStabiliser

**Command:** `[client -> system] ID:28/Query/Camera2/VideoStabiliser/Mode - Query video stabilizer mode from camera`
  - *Description:* [system -> client] ID:27/Ack - command accepted.

**Command:** `[system -> client] ID:28/Reply/Camera2/VideoStabiliser/Mode:1 - Reply about stabilizer mode of camera`
  - *Description:* 2.

**Command:** `[client -> system] ID:29/Query/Camera2/VideoStabiliser/ConstXOffset - Query constant horizontal offset`
  - *Description:* 2.

**Command:** `[system -> client] ID:29/Reply/Camera2/VideoStabiliser/ConstXOffset:0 - Reply about constant horizontal`
  - *Description:* from camera 2.


#### Camera2/VideoTracker

**Command:** `[client -> system] ID:28/Query/Camera2/VideoTracker/Mode - Query video tracker mode from camera 2.`
  - *Description:* [system -> client] ID:27/Ack - command accepted.

**Command:** `[system -> client] ID:28/Reply/Camera2/VideoTracker/Mode:0 - FREE video tracker mode of camera 2.`
  - *Description:* [client -> system] ID:28/Query/Camera2/VideoTracker/Mode - Query video tracker mode from camera 2.

**Command:** `[client -> system] ID:29/Query/Camera2/VideoTracker/LostModeOption - Query video tracker lost mode`
  - *Description:* [system -> client] ID:28/Reply/Camera2/VideoTracker/Mode:0 - FREE video tracker mode of camera 2.

**Command:** `[system -> client] ID:29/Reply/Camera2/VideoTracker/LostModeOption:0 - Lost mode option 0 of camera`
  - *Description:* option from camera 2.


### Camera3 Module

Found 4 command examples:


#### Camera3/Camera

**Command:** `[client -> system] ID:21/Query/Camera3/Camera/IsConnected - Query connection status.`
  - *Description:* 23 / 86

**Command:** `[system -> client] ID:21/Reply/Camera3/Camera/IsConnected:1 - Connected.`
  - *Description:* [client -> system] ID:21/Query/Camera3/Camera/IsConnected - Query connection status.


#### Camera3/Lens

**Command:** `[client -> system] ID:17/Query/Camera3/Lens/IsAfActive - Query auto focus status.`
  - *Description:* [system -> client] ID:16/Reply/Camera2/Lens/FocusPos:100 - Focus position from camera 2.

**Command:** `[system -> client] ID:17/Reply/Camera3/Lens/IsAfActive:0 - Auto focus not active.`
  - *Description:* [client -> system] ID:17/Query/Camera3/Lens/IsAfActive - Query auto focus status.


### Companion1 Module

Found 2 command examples:


#### Companion1/HeaterMode:1 - Enable heater in payload board 1.

**Command:** `[client -> system] ID:57/Command/Companion1/HeaterMode:1 - Enable heater in payload board 1.`
  - *Description:* [system -> client] ID:56/Ack - Command accepted.


#### Companion1/WiperMode:1 - Enable wiper in payload board 1.

**Command:** `[client -> system] ID:56/Command/Companion1/WiperMode:1 - Enable wiper in payload board 1.`
  - *Description:* Some example messages:


### Companion2 Module

Found 2 command examples:


#### Companion2/PowerChannel1Mode - Query power channel 1 mode from

**Command:** `[client -> system] ID:58/Query/Companion2/PowerChannel1Mode - Query power channel 1 mode from`
  - *Description:* [system -> client] ID:57/Ack - Command accepted.


#### Companion2/PowerChannel1Mode:1 - Reply about power channel 1 mode

**Command:** `[system -> client] ID:58/Reply/Companion2/PowerChannel1Mode:1 - Reply about power channel 1 mode`
  - *Description:* payload board 2.


### CompanionMain Module

Found 4 command examples:


#### CompanionMain/MainTemperature - Query main temperature from main

**Command:** `[client -> system] ID:59/Query/CompanionMain/MainTemperature - Query main temperature from main`
  - *Description:* of payload board 2.


#### CompanionMain/MainTemperature:56 - Reply about main temperature

**Command:** `[system -> client] ID:59/Reply/CompanionMain/MainTemperature:56 - Reply about main temperature`
  - *Description:* board.


#### CompanionMain/PowerChannel1Temperature channel of companion board

**Command:** `ID:2/Query/CompanionMain/PowerChannel1Temperature channel of companion board`
  - *Description:* Query temperature of first power


#### CompanionMain/PowerChannel1Temperature:50

**Command:** `ID:2/Reply/CompanionMain/PowerChannel1Temperature:50`
  - *Description:* power channel of companion


### ExternalUp Module

Found 5 command examples:


#### ExternalUp/TcpPort - Query TCP port.

**Command:** `[client -> system] ID:108/Query/ExternalUp/TcpPort - Query TCP port.`
  - *Description:* [system -> client] ID:107/Reply/ExternalUp/UdpPort:34020 - Current UDP port is 34020.


#### ExternalUp/TcpPort:34030 - Current TCP port is 34030.

**Command:** `[system -> client] ID:108/Reply/ExternalUp/TcpPort:34030 - Current TCP port is 34030.`
  - *Description:* [client -> system] ID:108/Query/ExternalUp/TcpPort - Query TCP port.


#### ExternalUp/UdpPort - Query UDP port.

**Command:** `[client -> system] ID:107/Query/ExternalUp/UdpPort - Query UDP port.`
  - *Description:* [system -> client] ID:106/Ack - Command accepted.


#### ExternalUp/UdpPort:34020 - Current UDP port is 34020.

**Command:** `[system -> client] ID:107/Reply/ExternalUp/UdpPort:34020 - Current UDP port is 34020.`
  - *Description:* [client -> system] ID:107/Query/ExternalUp/UdpPort - Query UDP port.


#### ExternalUp/UdpPort:34020 - Set UDP port to 34020.

**Command:** `[client -> system] ID:106/Command/ExternalUp/UdpPort:34020 - Set UDP port to 34020.`
  - *Description:* Some example messages:


### G5Laser Module

Found 14 command examples:


#### G5Laser/ARM

**Command:** `[client -> system] ID:97/Query/G5Laser/ARM/STATE - Query arm state.`
  - *Description:* [system -> client] ID:96/Reply/G5Laser/READY:READY - Device is ready.

**Command:** `[system -> client] ID:97/Reply/G5Laser/ARM/STATE:ON - Laser is armed.`
  - *Description:* [client -> system] ID:97/Query/G5Laser/ARM/STATE - Query arm state.


#### G5Laser/ARM-TIME:30 - Set auto-disarm timeout to 30 seconds.

**Command:** `[client -> system] ID:92/Command/G5Laser/ARM-TIME:30 - Set auto-disarm timeout to 30 seconds.`
  - *Description:* [system -> client] ID:91/Ack - Command accepted.


#### G5Laser/BEAM-TIME:60 - Set beam

**Command:** `[client -> system] ID:93/Command/G5Laser/BEAM-TIME:60 - Set beam/strobe auto-off timeout to 60`
  - *Description:* [system -> client] ID:92/Ack - Command accepted.


#### G5Laser/LIGHT

**Command:** `[client -> system] ID:98/Query/G5Laser/LIGHT/STATE - Query light mode.`
  - *Description:* [system -> client] ID:97/Reply/G5Laser/ARM/STATE:ON - Laser is armed.

**Command:** `[system -> client] ID:98/Reply/G5Laser/LIGHT/STATE:BEAM - Light mode is BEAM.`
  - *Description:* [client -> system] ID:98/Query/G5Laser/LIGHT/STATE - Query light mode.


#### G5Laser/MODE

**Command:** `[client -> system] ID:90/Command/G5Laser/MODE/ARM:ON - Arm the laser.`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:91/Command/G5Laser/MODE/LIGHT:BEAM - Turn on light in BEAM mode.`
  - *Description:* [system -> client] ID:90/Ack - Command accepted.


#### G5Laser/READY - Query device readiness.

**Command:** `[client -> system] ID:96/Query/G5Laser/READY - Query device readiness.`
  - *Description:* [system -> client] ID:95/Ack - Command accepted.


#### G5Laser/READY:READY - Device is ready.

**Command:** `[system -> client] ID:96/Reply/G5Laser/READY:READY - Device is ready.`
  - *Description:* [client -> system] ID:96/Query/G5Laser/READY - Query device readiness.


#### G5Laser/STROBE-TIME

**Command:** `[client -> system] ID:94/Command/G5Laser/STROBE-TIME/ON:100 - Set strobe ON duration to 100 ms.`
  - *Description:* [system -> client] ID:93/Ack - Command accepted.

**Command:** `[client -> system] ID:95/Command/G5Laser/STROBE-TIME/OFF:50 - Set strobe OFF duration to 50 ms.`
  - *Description:* [system -> client] ID:94/Ack - Command accepted.


#### G5Laser/TEMP

**Command:** `[client -> system] ID:99/Query/G5Laser/TEMP/LENS - Query lens temperature.`
  - *Description:* [system -> client] ID:98/Reply/G5Laser/LIGHT/STATE:BEAM - Light mode is BEAM.

**Command:** `[system -> client] ID:99/Reply/G5Laser/TEMP/LENS:32 - Lens temperature is 32C.`
  - *Description:* [client -> system] ID:99/Query/G5Laser/TEMP/LENS - Query lens temperature.


### General Module

Found 3 command examples:


#### General/SlaveZoomMode:1 - Enable slave zoom mode.

**Command:** `[client -> system] ID:76/Command/General/SlaveZoomMode:1 - Enable slave zoom mode.`
  - *Description:* Some example messages:


#### General/VideoTrackerToken - Query video tracker license token.

**Command:** `[client -> system] ID:79/Query/General/VideoTrackerToken - Query video tracker license token.`
  - *Description:* [system -> client] ID:76/Ack - Command accepted.


#### General/VideoTrackerToken:C7018FFD1BBE58C96DDD2534FF601FC62A112846FD13C30E5D

**Command:** `ID:79/Reply/General/VideoTrackerToken:C7018FFD1BBE58C96DDD2534FF601FC62A112846FD13C30E5D`
  - *Description:* [system -> client]


### Lrf Module

Found 7 command examples:


#### Lrf/Distance - Query measured distance.

**Command:** `[client -> system] ID:67/Query/Lrf/Distance - Query measured distance.`
  - *Description:* [system -> client] ID:66/Reply/Lrf/PointerModeTimeoutSec:10 - Reply about pointer mode timeout.


#### Lrf/Distance:56 - Reply about measured distance.

**Command:** `[system -> client] ID:67/Reply/Lrf/Distance:56 - Reply about measured distance.`
  - *Description:* [client -> system] ID:67/Query/Lrf/Distance - Query measured distance.


#### Lrf/Measure - Measure distance once.

**Command:** `[client -> system] ID:65/Command/Lrf/Measure - Measure distance once.`
  - *Description:* [system -> client] ID:64/Ack - Command accepted.


#### Lrf/MinGateDistance:10

**Command:** `ID:1/Command/Lrf/MinGateDistance:10`
  - *Description:* UP string-based command (from client to system):


#### Lrf/PointerMode:1 - Enable laser pointer.

**Command:** `[client -> system] ID:64/Command/Lrf/PointerMode:1 - Enable laser pointer.`
  - *Description:* Some example messages:


#### Lrf/PointerModeTimeoutSec - Query pointer mode timeout.

**Command:** `[client -> system] ID:66/Query/Lrf/PointerModeTimeoutSec - Query pointer mode timeout.`
  - *Description:* [system -> client] ID:65/Ack - Command accepted.


#### Lrf/PointerModeTimeoutSec:10 - Reply about pointer mode timeout.

**Command:** `[system -> client] ID:66/Reply/Lrf/PointerModeTimeoutSec:10 - Reply about pointer mode timeout.`
  - *Description:* [client -> system] ID:66/Query/Lrf/PointerModeTimeoutSec - Query pointer mode timeout.


### MotorControl Module

Found 5 command examples:


#### MotorControl/Pan

**Command:** `[client -> system] ID:10/Command/MotorControl/Pan/ToPos:120.5 - go to pan position 120.5 degree.`
  - *Description:* Some example messages:

**Command:** `[client -> system] ID:11/Command/MotorControl/Pan/ToPos:500 - go to pan position 500 degree.`
  - *Description:* [system -> client] ID:10/Ack - command accepted.

**Command:** `[client -> system] ID:13/Command/MotorControl/Pan/RightLimit:10.8 - Set right pan limit to 10.8 degree.`
  - *Description:* [system -> client] ID:12/Reply/MotorControl/Tilt/DownLimit:-60.1 - tilt down limit -60 degree.


#### MotorControl/Tilt

**Command:** `[client -> system] ID:12/Query/MotorControl/Tilt/DownLimit - Query tilt down limit.`
  - *Description:* [system -> client] ID:11/Nac - command not accepted.

**Command:** `[system -> client] ID:12/Reply/MotorControl/Tilt/DownLimit:-60.1 - tilt down limit -60 degree.`
  - *Description:* [client -> system] ID:12/Query/MotorControl/Tilt/DownLimit - Query tilt down limit.


### PeakBeam Module

Found 15 command examples:


#### PeakBeam/Level:High - Set light intensity to High.

**Command:** `[client -> system] ID:101/Command/PeakBeam/Level:High - Set light intensity to High.`
  - *Description:* [system -> client] ID:100/Ack - Command accepted.


#### PeakBeam/Mode - Query current mode.

**Command:** `[client -> system] ID:107/Query/PeakBeam/Mode - Query current mode.`
  - *Description:* [system -> client] ID:106/Ack - Command accepted.


#### PeakBeam/Mode:BEAM - Current mode is BEAM.

**Command:** `[system -> client] ID:107/Reply/PeakBeam/Mode:BEAM - Current mode is BEAM.`
  - *Description:* [client -> system] ID:107/Query/PeakBeam/Mode - Query current mode.


#### PeakBeam/Mode:BEAM - Set operating mode BEAM.

**Command:** `[client -> system] ID:100/Command/PeakBeam/Mode:BEAM - Set operating mode BEAM.`
  - *Description:* Some example messages:


#### PeakBeam/Pos - Query zoom position.

**Command:** `[client -> system] ID:109/Query/PeakBeam/Pos - Query zoom position.`
  - *Description:* [system -> client] ID:108/Reply/PeakBeam/StrobeRate/Hz:15 - Strobe rate is 15 Hz.


#### PeakBeam/Pos:75 - Zoom position is 75.

**Command:** `[system -> client] ID:109/Reply/PeakBeam/Pos:75 - Zoom position is 75.`
  - *Description:* [client -> system] ID:109/Query/PeakBeam/Pos - Query zoom position.


#### PeakBeam/StrobeRate

**Command:** `[client -> system] ID:108/Query/PeakBeam/StrobeRate/Hz - Query strobe rate in Hz.`
  - *Description:* [system -> client] ID:107/Reply/PeakBeam/Mode:BEAM - Current mode is BEAM.

**Command:** `[system -> client] ID:108/Reply/PeakBeam/StrobeRate/Hz:15 - Strobe rate is 15 Hz.`
  - *Description:* [client -> system] ID:108/Query/PeakBeam/StrobeRate/Hz - Query strobe rate in Hz.


#### PeakBeam/StrobeRate:15 - Set strobe frequency to 15 Hz.

**Command:** `[client -> system] ID:102/Command/PeakBeam/StrobeRate:15 - Set strobe frequency to 15 Hz.`
  - *Description:* [system -> client] ID:101/Ack - Command accepted.


#### PeakBeam/Temperature - Query housing temperature.

**Command:** `[client -> system] ID:110/Query/PeakBeam/Temperature - Query housing temperature.`
  - *Description:* [system -> client] ID:109/Reply/PeakBeam/Pos:75 - Zoom position is 75.


#### PeakBeam/Temperature:32 - Housing temperature is 32C.

**Command:** `[system -> client] ID:110/Reply/PeakBeam/Temperature:32 - Housing temperature is 32C.`
  - *Description:* [client -> system] ID:110/Query/PeakBeam/Temperature - Query housing temperature.


#### PeakBeam/ToPos:75 - Move zoom to position 75.

**Command:** `[client -> system] ID:104/Command/PeakBeam/ToPos:75 - Move zoom to position 75.`
  - *Description:* [system -> client] ID:103/Ack - Command accepted.


#### PeakBeam/Zoom:In - Start continuous zoom in.

**Command:** `[client -> system] ID:105/Command/PeakBeam/Zoom:In - Start continuous zoom in.`
  - *Description:* [system -> client] ID:104/Ack - Command accepted.


#### PeakBeam/ZoomRate:50 - Set zoom speed to 50%.

**Command:** `[client -> system] ID:103/Command/PeakBeam/ZoomRate:50 - Set zoom speed to 50%.`
  - *Description:* [system -> client] ID:102/Ack - Command accepted.


#### PeakBeam/ZoomStop - Stop zoom movement.

**Command:** `[client -> system] ID:106/Command/PeakBeam/ZoomStop - Stop zoom movement.`
  - *Description:* [system -> client] ID:105/Ack - Command accepted.


### PelcoD Module

Found 5 command examples:


#### PelcoD/TcpPort - Query TCP port.

**Command:** `[client -> system] ID:108/Query/PelcoD/TcpPort - Query TCP port.`
  - *Description:* [system -> client] ID:107/Reply/PelcoD/UdpPort:34000 - Current UDP port is 34000.


#### PelcoD/TcpPort:34010 - Current TCP port is 34010.

**Command:** `[system -> client] ID:108/Reply/PelcoD/TcpPort:34010 - Current TCP port is 34010.`
  - *Description:* [client -> system] ID:108/Query/PelcoD/TcpPort - Query TCP port.


#### PelcoD/UdpPort - Query UDP port.

**Command:** `[client -> system] ID:107/Query/PelcoD/UdpPort - Query UDP port.`
  - *Description:* [system -> client] ID:106/Ack - Command accepted.


#### PelcoD/UdpPort:34000 - Current UDP port is 34000.

**Command:** `[system -> client] ID:107/Reply/PelcoD/UdpPort:34000 - Current UDP port is 34000.`
  - *Description:* [client -> system] ID:107/Query/PelcoD/UdpPort - Query UDP port.


#### PelcoD/UdpPort:34000 - Set UDP port to 34000.

**Command:** `[client -> system] ID:106/Command/PelcoD/UdpPort:34000 - Set UDP port to 34000.`
  - *Description:* Some example messages:


### ProcedureManager Module

Found 3 command examples:


#### ProcedureManager/GoToPreset:2 - Go to preset 2.

**Command:** `[client -> system] ID:82/Command/ProcedureManager/GoToPreset:2 - Go to preset 2.`
  - *Description:* Some example messages:


#### ProcedureManager/GoToPreset:2\nID:83

**Command:** `ID:82/Command/ProcedureManager/GoToPreset:2\nID:83/Command/Camera1/Lens/ZoomIn\nID:84/`
  - *Description:* multiple commands in one. User need put end of line symbol '\n' between commands. Example:

**Command:** `ID:82/Command/ProcedureManager/GoToPreset:2\nID:83/Command/Camera1/Lens/ZoomIn\nID:84/`
  - *Description:* Client -> system:


### Speaker Module

Found 5 command examples:


#### Speaker/Play:clip1.mp3 - Play clip1.mp3.

**Command:** `[client -> system] ID:64/Command/Speaker/Play:clip1.mp3 - Play clip1.mp3.`
  - *Description:* Some example messages:


#### Speaker/Stop - Stop playback.

**Command:** `[client -> system] ID:65/Command/Speaker/Stop - Stop playback.`
  - *Description:* [system -> client] ID:64/Ack - Command accepted.


#### Speaker/Volume - Query playback volume.

**Command:** `[client -> system] ID:66/Query/Speaker/Volume - Query playback volume.`
  - *Description:* [system -> client] ID:65/Ack - Command accepted.


#### Speaker/Volume:10 - Reply about playback volume (10%).

**Command:** `[system -> client] ID:66/Reply/Speaker/Volume:10 - Reply about playback volume (10%).`
  - *Description:* [client -> system] ID:66/Query/Speaker/Volume - Query playback volume.


#### Speaker/Volume:20 - Set playback volume to 20%.

**Command:** `[client -> system] ID:67/Command/Speaker/Volume:20 - Set playback volume to 20%.`
  - *Description:* [system -> client] ID:66/Reply/Speaker/Volume:10 - Reply about playback volume (10%).
