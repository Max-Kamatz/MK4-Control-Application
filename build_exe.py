#!/usr/bin/env python3
"""
Build script for creating standalone MK4 Control Application executable
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_dirs():
    """Remove previous build artifacts"""
    print("Cleaning build directories...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed: {dir_name}")

    spec_file = 'MK4Control.spec'
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print(f"  Removed: {spec_file}")

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def create_spec_file():
    """Generate PyInstaller spec file"""
    print("Creating PyInstaller spec file...")

    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('Reference Material', 'Reference Material'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'pyqtgraph',
        'numpy',
        'cv2',
        'asyncio',
        'socket',
        'struct',
        'json',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MK4Control',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""

    with open('MK4Control.spec', 'w') as f:
        f.write(spec_content)

    print("  Spec file created: MK4Control.spec")

def build_executable():
    """Run PyInstaller to build the executable"""
    print("\nBuilding executable with PyInstaller...")
    print("This may take several minutes...\n")

    try:
        subprocess.check_call([
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "MK4Control.spec"
        ])
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        return False

def create_distribution():
    """Create distribution folder with necessary files"""
    print("\nCreating distribution package...")

    dist_dir = Path('dist/MK4Control_Package')
    dist_dir.mkdir(parents=True, exist_ok=True)

    # Copy executable
    exe_file = Path('dist/MK4Control.exe')
    if exe_file.exists():
        shutil.copy(exe_file, dist_dir / 'MK4Control.exe')
        print(f"  Copied: MK4Control.exe")

    # Copy README
    if Path('README.md').exists():
        shutil.copy('README.md', dist_dir / 'README.md')
        print(f"  Copied: README.md")

    # Create logs directory
    (dist_dir / 'logs').mkdir(exist_ok=True)
    print(f"  Created: logs/")

    print(f"\nDistribution package created at: {dist_dir.absolute()}")
    print(f"Executable size: {exe_file.stat().st_size / (1024*1024):.2f} MB")

def main():
    print("=" * 60)
    print("MK4 Control Application - Executable Builder")
    print("=" * 60)
    print()

    # Check dependencies
    if not check_pyinstaller():
        print("Failed to install PyInstaller")
        return 1

    # Clean previous builds
    clean_build_dirs()

    # Create spec file
    create_spec_file()

    # Build executable
    if not build_executable():
        print("\nBuild failed!")
        return 1

    # Create distribution package
    create_distribution()

    print("\n" + "=" * 60)
    print("Build completed successfully!")
    print("=" * 60)
    print("\nTo run the application:")
    print("  1. Navigate to: dist/MK4Control_Package/")
    print("  2. Double-click: MK4Control.exe")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
