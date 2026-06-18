#!/usr/bin/env python3
"""
Script to refactor all tabs to use centralized VideoDisplayManager.
This automates the removal of RTSPVideoWidget instantiation and video management code.
"""

import re
import os

# List of tab files to refactor (excluding combined_control_tab.py which is already done)
TAB_FILES = [
    "gui/tabs/connection_tab.py",
    "gui/tabs/control_tab.py",
    "gui/tabs/motor_settings_tab.py",
    "gui/tabs/camera_settings_tab.py",
    "gui/tabs/rtsp_tab.py",
    "gui/tabs/overlay_tab.py",
    "gui/tabs/tracker_settings_tab.py",
    "gui/tabs/advanced_tab.py",
    "gui/tabs/sub_payloads_tab.py",
    "gui/tabs/video_tab.py",
]

def refactor_tab_file(filepath):
    """Refactor a single tab file."""
    print(f"Refactoring {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Step 1: Remove RTSPVideoWidget import
    content = re.sub(
        r'from gui\.widgets\.rtsp_video_widget import RTSPVideoWidget\n',
        '',
        content
    )
    content = re.sub(
        r', RTSPVideoWidget',
        '',
        content
    )

    # Step 2: Remove discover_cameras import
    content = re.sub(
        r'from utils\.camera_discovery import discover_cameras\n',
        '',
        content
    )

    # Step 3: Update __init__ signature to accept video_manager
    content = re.sub(
        r'def __init__\(self\):',
        'def __init__(self, video_manager=None):',
        content
    )

    # Step 4: Replace camera_availability tracking and add video_manager/video_placeholder
    content = re.sub(
        r'self\.camera_availability = \{\}  # Track which cameras are available',
        'self.video_manager = video_manager\n        self.video_placeholder = None  # Will hold the shared video display',
        content
    )

    # Step 5: Replace create_video_section method
    # Find the entire method and replace it
    video_section_pattern = r'    def create_video_section\(self\) -> QWidget:.*?return self\.video_widget'
    video_section_replacement = '''    def create_video_section(self) -> QWidget:
        """Create placeholder for shared video display manager."""
        self.video_placeholder = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(10, 10, 10, 10)
        self.video_placeholder.setLayout(layout)
        return self.video_placeholder

    def set_video_display(self, video_manager):
        """Called when this tab becomes active - reparent video display here."""
        if video_manager and self.video_placeholder:
            # Clear placeholder
            while self.video_placeholder.layout().count():
                item = self.video_placeholder.layout().takeAt(0)
                if item.widget():
                    item.widget().setParent(None)

            # Reparent video manager's display widget
            display_widget = video_manager.get_display_widget()
            display_widget.setParent(self.video_placeholder)
            self.video_placeholder.layout().addWidget(display_widget)
            display_widget.show()
            logger.debug(f"Video display reparented to {self.__class__.__name__}")'''

    content = re.sub(video_section_pattern, video_section_replacement, content, flags=re.DOTALL)

    # Step 6: Remove rebuild_video_layout method
    rebuild_pattern = r'    def rebuild_video_layout\(self\):.*?(?=\n    def |\Z)'
    content = re.sub(rebuild_pattern, '', content, flags=re.DOTALL)

    # Step 7: Remove update_video_streams_ip method
    update_pattern = r'    def update_video_streams_ip\(self.*?\):.*?(?=\n    def |\Z)'
    content = re.sub(update_pattern, '', content, flags=re.DOTALL)

    # Step 8: Remove stop_all_video_streams method
    stop_pattern = r'    def stop_all_video_streams\(self\):.*?(?=\n    def |\Z)'
    content = re.sub(stop_pattern, '', content, flags=re.DOTALL)

    # Step 9: Remove closeEvent method
    close_pattern = r'    def closeEvent\(self, event\):.*?event\.accept\(\)\n'
    content = re.sub(close_pattern, '', content, flags=re.DOTALL)

    # Write back if changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [OK] Refactored {filepath}")
        return True
    else:
        print(f"  [-] No changes needed for {filepath}")
        return False

def main():
    """Main refactoring script."""
    print("=" * 60)
    print("Tab Refactoring Script")
    print("Converting tabs to use centralized VideoDisplayManager")
    print("=" * 60)
    print()

    refactored_count = 0
    for tab_file in TAB_FILES:
        if os.path.exists(tab_file):
            if refactor_tab_file(tab_file):
                refactored_count += 1
        else:
            print(f"[!] File not found: {tab_file}")

    print()
    print("=" * 60)
    print(f"Refactoring complete: {refactored_count}/{len(TAB_FILES)} files modified")
    print("=" * 60)

if __name__ == "__main__":
    main()
