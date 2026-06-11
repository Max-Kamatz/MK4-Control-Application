import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.tabs.combined_control_tab import CombinedControlTab
from gui.tabs.control_tab import ControlTab
from utils.logger import setup_logger

logger = setup_logger()

def main():
    logger.info("Starting MK4 Control Application")

    app = QApplication(sys.argv)
    app.setApplicationName("MK4 Control")
    app.setOrganizationName("Silent Sentinel")

    main_window = MainWindow()

    # Combined tab with video + PTZ trackpad control
    combined_tab = CombinedControlTab()
    main_window.add_tab(combined_tab, "📹 Video + Control")

    # Keep original control tab for sliders as backup
    control_tab = ControlTab()
    main_window.add_tab(control_tab, "🎮 Slider Control")

    main_window.start_network_thread()

    # Connect combined tab pan/tilt (trackpad gives normalized -1 to 1)
    def handle_trackpad_pantilt(pan_norm: float, tilt_norm: float):
        # Convert normalized values to degrees for the command
        pan_degrees = pan_norm * 180.0
        tilt_degrees = tilt_norm * 90.0
        main_window.network_thread.send_pan_tilt(pan_degrees, tilt_degrees)

    combined_tab.pan_tilt_command.connect(handle_trackpad_pantilt)
    combined_tab.pan_tilt_stop.connect(main_window.network_thread.send_stop)

    # Connect zoom
    combined_tab.zoom_command.connect(
        lambda direction: main_window.network_thread.send_zoom(float(direction))
    )
    combined_tab.zoom_stop.connect(main_window.network_thread.send_stop)

    # Connect focus
    combined_tab.focus_command.connect(
        lambda direction: main_window.network_thread.send_focus(float(direction))
    )
    combined_tab.focus_stop.connect(main_window.network_thread.send_stop)

    combined_tab.home_requested.connect(
        lambda: main_window.network_thread.send_pan_tilt(0.0, 0.0)
    )

    def handle_combined_connection_toggle():
        if not main_window.network_thread.network_manager or not main_window.network_thread.network_manager.connected:
            target_ip = combined_tab.get_target_ip()
            # Update video streams to use new IP
            combined_tab.update_video_streams_ip(target_ip)
            # Connect to system with new IP
            main_window.network_thread.connect_to_system(target_ip)
        else:
            main_window.network_thread.disconnect_from_system()

    combined_tab.connection_toggle.connect(handle_combined_connection_toggle)

    # Connect slider control tab
    control_tab.pan_tilt_changed.connect(main_window.network_thread.send_pan_tilt)
    control_tab.home_requested.connect(
        lambda: main_window.network_thread.send_pan_tilt(0.0, 0.0)
    )

    def handle_control_connection_toggle():
        if not main_window.network_thread.network_manager or not main_window.network_thread.network_manager.connected:
            target_ip = control_tab.get_target_ip()
            main_window.network_thread.connect_to_system(target_ip)
        else:
            main_window.network_thread.disconnect_from_system()

    control_tab.reconnect_button.clicked.connect(handle_control_connection_toggle)

    # Telemetry updates both tabs
    main_window.network_thread.telemetry_received.connect(
        lambda data: combined_tab.update_actual_position(data['pan'], data['tilt']) if data['pan'] is not None else None
    )
    main_window.network_thread.telemetry_received.connect(
        lambda data: control_tab.update_actual_position(data['pan'], data['tilt']) if data['pan'] is not None else None
    )

    # Connection status updates both tabs
    main_window.network_thread.connection_status_changed.connect(
        combined_tab.update_connection_status
    )
    main_window.network_thread.connection_status_changed.connect(
        control_tab.update_connection_status
    )

    main_window.show()

    logger.info("Application window displayed")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
