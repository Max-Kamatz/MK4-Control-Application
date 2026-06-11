# MK4 Control Application - Build Instructions

This document explains how to build a standalone executable (.exe) for the MK4 Control Application.

## Prerequisites

- Windows 10/11
- Python 3.10 or higher
- All project dependencies installed (`pip install -r requirements.txt`)

## Quick Build

### Method 1: Using the Build Script (Recommended)

Simply double-click `build.bat` or run from command line:

```batch
build.bat
```

This will:
1. Check and install PyInstaller if needed
2. Clean previous build artifacts
3. Generate the PyInstaller spec file
4. Build the executable
5. Create a distribution package in `dist/MK4Control_Package/`

### Method 2: Manual Build

```bash
# Install PyInstaller
pip install pyinstaller

# Run the Python build script
python build_exe.py
```

### Method 3: Direct PyInstaller Command

```bash
# First, create the spec file
python build_exe.py

# Then build with PyInstaller
pyinstaller --clean MK4Control.spec
```

## Build Output

After successful build, you'll find:

```
dist/
├── MK4Control.exe                    # Standalone executable (main)
└── MK4Control_Package/               # Distribution folder
    ├── MK4Control.exe                # Standalone executable (copy)
    ├── README.md                     # User documentation
    └── logs/                         # Log directory (empty)
```

### What Gets Included

The executable bundles:
- All Python code (gui, network, models, utils)
- Configuration files (`config/` directory)
- Reference materials (`Reference Material/` directory)
- PyQt6 runtime and dependencies
- OpenCV libraries
- Python runtime

### What's NOT Included

Users need to have separately:
- Network access to the MK4 system (192.168.1.100)
- No additional software installation required

## Distribution

To distribute the application:

1. **Recommended**: Share the entire `dist/MK4Control_Package/` folder
   - Contains the .exe, documentation, and logs directory
   - Users just double-click `MK4Control.exe`

2. **Minimal**: Share only `dist/MK4Control.exe`
   - Single file, easier to distribute
   - Will create its own `logs/` directory on first run

## Build Configuration

The build is configured via `MK4Control.spec` (auto-generated):

### Key Settings

```python
# One-file bundle (everything in single .exe)
exe = EXE(
    ...
    name='MK4Control',           # Output filename
    console=False,               # No console window (GUI only)
    upx=True,                    # Compress with UPX
    icon=None,                   # No custom icon (can add later)
)
```

### Included Data Files

- `config/` directory → Configuration files
- `Reference Material/` directory → Protocol PDFs and credentials

### Hidden Imports

Explicitly included modules:
- PyQt6 (Core, Gui, Widgets)
- pyqtgraph
- numpy
- cv2 (OpenCV)
- asyncio, socket, struct, json

### Excluded Modules

To reduce file size, these are excluded:
- matplotlib
- pandas
- scipy
- PIL
- tkinter

## Troubleshooting

### Build Fails with "Module not found"

Add the missing module to `hiddenimports` in the spec file:

```python
hiddenimports=[
    'PyQt6.QtCore',
    'your_missing_module',  # Add here
],
```

### Executable is Too Large

Current size: ~150-200 MB (typical for PyQt6 applications)

To reduce size:
1. Remove `upx=True` from spec (or install UPX compressor)
2. Add more modules to `excludes` list
3. Use PyInstaller's `--strip` option (debugging harder)

### Executable Won't Run on Other Computers

**Common causes**:
1. **Missing Visual C++ Runtime**: User needs to install:
   - Microsoft Visual C++ Redistributable (latest)
   - Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe

2. **Antivirus blocking**: Some antivirus software flags PyInstaller executables
   - Add exception for `MK4Control.exe`
   - Sign the executable with a code signing certificate (for production)

3. **Windows version**: Built on Windows 11, test on Windows 10

### Config Files Not Found

The executable looks for `config/` relative to the .exe location.

Ensure the distribution includes:
```
MK4Control_Package/
├── MK4Control.exe
└── config/              ← Must be present
    ├── default_config.json
    └── up_protocol_commands.json
```

If files are embedded in the .exe, they're extracted to a temp folder. The application should handle both cases.

## Advanced Customization

### Adding a Custom Icon

1. Create or obtain a `.ico` file (e.g., `mk4_icon.ico`)
2. Place it in the project root
3. Update the spec file:

```python
exe = EXE(
    ...
    icon='mk4_icon.ico',  # Add this line
)
```

4. Rebuild: `pyinstaller --clean MK4Control.spec`

### Console Window for Debugging

To show a console window (useful for troubleshooting):

```python
exe = EXE(
    ...
    console=True,  # Change to True
)
```

### Multiple Executables

To create separate executables for different environments:

```python
# Production build (no console)
exe_prod = EXE(..., console=False, name='MK4Control')

# Debug build (with console)
exe_debug = EXE(..., console=True, name='MK4Control_Debug')
```

## Version Management

### Embedding Version Information

Create `version_info.txt`:

```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(0, 1, 0, 0),
    prodvers=(0, 1, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Silent Sentinel'),
        StringStruct(u'FileDescription', u'MK4 Control Application'),
        StringStruct(u'FileVersion', u'0.1.0'),
        StringStruct(u'ProductName', u'MK4 Control System'),
        StringStruct(u'ProductVersion', u'0.1.0')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

Then reference in spec file:
```python
exe = EXE(
    ...
    version='version_info.txt',
)
```

## Testing the Executable

After building:

1. **Clean environment test**: Copy `dist/MK4Control_Package/` to a different computer
2. **Startup test**: Double-click `MK4Control.exe` → Should launch without errors
3. **Functionality test**: 
   - Check all tabs load
   - Verify config files are read correctly
   - Test video stream initialization
   - Test network connection attempts
4. **Log verification**: Check `logs/` directory for proper log file creation

## Build Performance

Typical build times on modern hardware:
- **First build**: 3-5 minutes (downloads dependencies)
- **Subsequent builds**: 1-2 minutes (cached)
- **Clean build**: 2-3 minutes

## Deployment Checklist

Before distributing to end users:

- [ ] Build completes without errors
- [ ] Test executable on clean Windows installation
- [ ] Verify all config files are accessible
- [ ] Check log files are created in correct location
- [ ] Test video streaming initialization
- [ ] Verify network connection attempts work
- [ ] Include README.md with distribution
- [ ] Test with actual MK4 hardware (if available)
- [ ] Document known issues or limitations
- [ ] Consider code signing for production releases

## Support

For build issues:
1. Check the build log output for error messages
2. Verify all dependencies are installed: `pip list`
3. Try a clean build: Delete `build/`, `dist/`, `*.spec` and rebuild
4. Check PyInstaller documentation: https://pyinstaller.org/

For runtime issues with the built executable:
1. Run with console=True to see error messages
2. Check the log files in the `logs/` directory
3. Verify config files are present and valid
4. Test on the development machine first

## Future Enhancements

Potential build improvements:
- Automatic version numbering from git tags
- Code signing for Windows SmartScreen bypass
- Installer creation (NSIS, Inno Setup)
- Auto-update mechanism
- Portable vs. installed versions
- Multi-language support
