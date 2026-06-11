@echo off
echo ========================================
echo MK4 Control Application - Build Script
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>NUL
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Run the build script
python build_exe.py

pause
