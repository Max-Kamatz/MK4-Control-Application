# MK4 Control Application - Deployment Checklist

## Pre-Build Checklist

- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] Application runs from source: `python main.py`
- [ ] All tests pass: `python test_up_protocol.py`
- [ ] Configuration files are correct (`config/*.json`)
- [ ] PyInstaller installed: `pip install pyinstaller`

## Building the Executable

### Step 1: Clean Previous Builds

```bash
# Delete build artifacts (if they exist)
rmdir /s /q build
rmdir /s /q dist
del MK4Control.spec
```

### Step 2: Run Build Script

```bash
# Option A: Double-click in Windows Explorer
build.bat

# Option B: Command line
python build_exe.py
```

### Step 3: Verify Build Output

Check that these files exist:
- [ ] `dist/MK4Control.exe` (main executable)
- [ ] `dist/MK4Control_Package/MK4Control.exe` (distribution copy)
- [ ] `dist/MK4Control_Package/README.md`
- [ ] `dist/MK4Control_Package/logs/` (empty directory)

### Step 4: Check Executable Size

Expected size: **150-250 MB**

```bash
dir dist\MK4Control.exe
```

If significantly larger (>500 MB): Check for unwanted dependencies in the build.

## Post-Build Testing

### Test 1: Local Machine Test

- [ ] Double-click `dist/MK4Control.exe`
- [ ] Application window appears within 5 seconds
- [ ] No error messages displayed
- [ ] All tabs are accessible (Video Streams, Gimbal Control)
- [ ] Log file created in `logs/` directory

### Test 2: Clean Environment Test

**Copy to a different location:**
- [ ] Copy `dist/MK4Control_Package/` to `C:\Temp\MK4Test\`
- [ ] Run from new location
- [ ] Verify application launches correctly
- [ ] Check config files are read (connection attempts visible)

### Test 3: Different Windows Machine (If Available)

- [ ] Copy executable to another Windows 10/11 computer
- [ ] Launch executable
- [ ] Verify no "missing DLL" errors
- [ ] Check application functionality

**Common issue**: Missing Visual C++ Runtime
- Solution: Install [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Test 4: Configuration Loading

- [ ] Check status bar shows "Ready - Not Connected"
- [ ] Video tab shows three placeholders (attempting connection)
- [ ] Control tab displays pan/tilt sliders
- [ ] No Python errors in console (if console=True)

### Test 5: Network Functionality (If MK4 Available)

- [ ] Click "Connect" in Gimbal Control tab
- [ ] Connection status updates (green = success, red = fail)
- [ ] Video streams attempt RTSP connection
- [ ] Pan/tilt sliders send commands (check logs)
- [ ] Position feedback displays (if telemetry received)

## Distribution Package Preparation

### Required Files

Create distribution folder with:
- [ ] `MK4Control.exe` (main executable)
- [ ] `README.md` (user documentation)
- [ ] `QUICK_START.md` (quick reference)
- [ ] `logs/` (empty directory for log files)

### Optional Files

Consider including:
- [ ] `config/` folder (if users need to modify settings)
- [ ] `Reference Material/` (protocol PDFs, credentials)
- [ ] Release notes / changelog
- [ ] Installation instructions

### Packaging Options

**Option 1: ZIP Archive**
```bash
# Create ZIP file
Compress-Archive -Path "dist\MK4Control_Package\*" -DestinationPath "MK4Control_v0.1.0.zip"
```

**Option 2: Installer** (Future enhancement)
- Use NSIS or Inno Setup to create installer
- Adds Start Menu shortcuts
- Handles VC++ Runtime installation
- Professional appearance

## Deployment Methods

### Method 1: Direct File Share
- Copy `MK4Control_Package` folder to network share
- Users copy to their local machine
- Simple, no installation required

### Method 2: USB Drive
- Copy `MK4Control_Package` to USB drive
- Distribute to users physically
- Good for secure/isolated networks

### Method 3: Network Deployment
- Host on internal web server or file share
- Users download ZIP file
- Extract and run

## User Instructions to Include

### Minimum Instructions

```
MK4 Control Application - Quick Setup

1. Extract MK4Control_Package.zip to a folder (e.g., C:\MK4Control)
2. Open the folder
3. Double-click MK4Control.exe
4. Wait for application to load (~3 seconds)

For detailed instructions, see README.md
```

### Prerequisites for End Users

- Windows 10 or Windows 11 (64-bit)
- Network connection to MK4 system (192.168.1.100)
- Microsoft Visual C++ Redistributable (usually pre-installed)
- 4 GB RAM minimum

## Known Issues & Workarounds

### Issue: Antivirus False Positive

**Symptoms**: Antivirus blocks or deletes MK4Control.exe

**Workarounds**:
1. Add exception for MK4Control.exe in antivirus settings
2. Submit exe to antivirus vendor for whitelisting
3. Code-sign the executable (requires certificate)

### Issue: "VCRUNTIME140.dll not found"

**Symptoms**: Error message on startup

**Solution**: Install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Issue: Slow Startup

**Symptoms**: Application takes >10 seconds to start

**Causes**:
- Antivirus scanning the executable
- Slow disk I/O (USB drive, network share)
- Low RAM (< 4 GB)

**Solutions**:
- Copy to local hard drive (C:\)
- Add antivirus exception
- Close other applications

### Issue: Config Files Not Found

**Symptoms**: Application logs show "FileNotFoundError: config/default_config.json"

**Solution**: Ensure `config/` directory is present alongside MK4Control.exe

## Rollback Plan

If issues arise after deployment:

1. **Stop using new version**: Revert to previous version (if exists)
2. **Collect logs**: Gather log files from affected users
3. **Debug**: Review logs for error patterns
4. **Fix and rebuild**: Apply fixes and create new build
5. **Test thoroughly**: Complete full test cycle before redeployment

## Version Management

### Version Numbering

Current: **v0.1.0** (MVP)

Format: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes (v1.0.0, v2.0.0)
- **MINOR**: New features (v0.2.0, v0.3.0)
- **PATCH**: Bug fixes (v0.1.1, v0.1.2)

### Release Naming

- `MK4Control_v0.1.0.zip` - Release package
- `MK4Control.exe` - Executable (version in file properties)

### Changelog Tracking

Document changes between versions:
```
v0.1.0 (2026-06-10) - Initial Release
- Basic gimbal control (pan/tilt)
- RTSP video streaming (3 cameras)
- UP protocol implementation
- Dark theme UI
- Network auto-reconnection
```

## Support & Documentation

### Documentation Files to Review

Before deployment, ensure these are current:
- [ ] `README.md` - Usage instructions
- [ ] `QUICK_START.md` - Quick reference
- [ ] `BUILD_INSTRUCTIONS.md` - For developers
- [ ] `PROJECT_STATUS.md` - Current state

### Support Contact Information

Include in distribution:
- Support email or contact method
- Issue reporting process
- Emergency contact for critical issues

## Post-Deployment Follow-up

### Week 1
- [ ] Monitor for crash reports
- [ ] Collect user feedback
- [ ] Review log files from users
- [ ] Document common issues

### Month 1
- [ ] Assess performance in production
- [ ] Identify feature requests
- [ ] Plan next version enhancements
- [ ] Update documentation based on feedback

## Security Considerations

### Current Status
- [ ] No code signing (executable will show "Unknown publisher")
- [ ] No encryption of config files
- [ ] Credentials stored in plain text JSON

### Recommendations for Production
- [ ] Obtain code signing certificate
- [ ] Encrypt sensitive configuration data
- [ ] Implement secure credential storage
- [ ] Add authentication for network connections
- [ ] Security audit of UP protocol implementation

## Final Checklist

Before marking deployment complete:

- [ ] Executable builds without errors
- [ ] All tests pass (UP protocol, application launch)
- [ ] Tested on clean Windows installation
- [ ] Documentation is complete and accurate
- [ ] Known issues are documented
- [ ] User instructions are clear
- [ ] Support process is defined
- [ ] Version number is correct
- [ ] Distribution package is complete
- [ ] Rollback plan is ready

## Sign-off

**Built by**: _________________  
**Date**: _________________  
**Tested by**: _________________  
**Date**: _________________  
**Approved by**: _________________  
**Date**: _________________  

---

**Notes**:
- This checklist should be completed for each release
- Keep a copy with the release package
- Document any deviations or issues encountered
- Update checklist based on lessons learned
