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

    # Set combined control as main content (no tabs)
    combined_tab = CombinedControlTab()
    main_window.set_central_content(combined_tab)

    main_window.start_network_thread()

    # NOTE: Trackpad now controls speed (via pan_speed_changed/tilt_speed_changed signals)
    # No longer using pan_tilt_command signal - trackpad is joystick mode

    # Connect zoom - get selected camera each time
    combined_tab.zoom_command.connect(
        lambda direction: main_window.network_thread.send_zoom(float(direction), combined_tab.get_selected_camera())
    )
    combined_tab.zoom_stop.connect(main_window.network_thread.send_stop)

    # Connect focus - get selected camera each time
    combined_tab.focus_command.connect(
        lambda direction: main_window.network_thread.send_focus(float(direction), combined_tab.get_selected_camera())
    )
    combined_tab.focus_stop.connect(main_window.network_thread.send_stop)

    combined_tab.home_requested.connect(
        lambda: main_window.network_thread.send_pan_tilt(0.0, 0.0)
    )

    # Connect speed control sliders
    combined_tab.pan_speed_changed.connect(main_window.network_thread.send_pan_speed)
    combined_tab.tilt_speed_changed.connect(main_window.network_thread.send_tilt_speed)
    combined_tab.zoom_speed_changed.connect(main_window.network_thread.send_zoom)
    combined_tab.focus_speed_changed.connect(main_window.network_thread.send_focus)

    def handle_combined_connection_toggle():
        if not main_window.network_thread.network_manager or not main_window.network_thread.network_manager.connected:
            target_ip = combined_tab.get_target_ip()
            # Connect to system with new IP (video streams will update on successful connection)
            main_window.network_thread.connect_to_system(target_ip)
        else:
            main_window.network_thread.disconnect_from_system()

    def handle_combined_connection_success(connected: bool):
        """Update video streams and component status after TCP connection succeeds, stop streams on disconnect."""
        if connected:
            target_ip = combined_tab.get_target_ip()
            combined_tab.update_video_streams_ip(target_ip)
            combined_tab.update_component_status(target_ip)
        else:
            # Stop all video streams on disconnect
            combined_tab.stop_all_video_streams()

    combined_tab.connection_toggle.connect(handle_combined_connection_toggle)
    main_window.network_thread.connection_status_changed.connect(handle_combined_connection_success)

    # Telemetry updates
    main_window.network_thread.telemetry_received.connect(
        lambda data: combined_tab.update_actual_position(data['pan'], data['tilt']) if data['pan'] is not None else None
    )

    # Connection status updates
    main_window.network_thread.connection_status_changed.connect(
        combined_tab.update_connection_status
    )

    main_window.show()

    logger.info("Application window displayed")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
