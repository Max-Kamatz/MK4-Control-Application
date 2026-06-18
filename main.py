import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from gui.tabs.connection_tab import ConnectionTab
from gui.tabs.combined_control_tab import CombinedControlTab
from gui.tabs.motor_settings_tab import MotorSettingsTab
from gui.tabs.camera_settings_tab import CameraSettingsTab
from gui.tabs.rtsp_tab import RTSPTab
from gui.tabs.overlay_tab import OverlayTab
from gui.tabs.tracker_settings_tab import TrackerSettingsTab
from gui.tabs.advanced_tab import AdvancedTab
from gui.tabs.sub_payloads_tab import SubPayloadsTab
from gui.tabs.hardware_tab import HardwareTab
from gui.widgets.video_display_manager import VideoDisplayManager
from utils.logger import setup_logger

logger = setup_logger()

def main():
    logger.info("Starting MK4 Control Application")

    app = QApplication(sys.argv)
    app.setApplicationName("MK4 Control")
    app.setOrganizationName("Silent Sentinel")

    main_window = MainWindow()

    # Create centralized video display manager (singleton - only ONE instance)
    video_manager = VideoDisplayManager()
    main_window.video_display_manager = video_manager
    logger.info("Centralized VideoDisplayManager created (33 streams → 3 streams)")

    # Create tabs with video_manager reference
    connection_tab = ConnectionTab(video_manager)
    combined_tab = CombinedControlTab(video_manager)
    motor_settings_tab = MotorSettingsTab(video_manager)
    camera_settings_tab = CameraSettingsTab(video_manager)
    rtsp_tab = RTSPTab(video_manager)
    overlay_tab = OverlayTab(video_manager)
    tracker_settings_tab = TrackerSettingsTab(video_manager)
    advanced_tab = AdvancedTab(video_manager)
    sub_payloads_tab = SubPayloadsTab(video_manager)
    hardware_tab = HardwareTab(video_manager)

    # Add tabs to main window
    main_window.add_tab(connection_tab, "Connection")
    main_window.add_tab(combined_tab, "Control")
    main_window.add_tab(motor_settings_tab, "Motor Settings")
    main_window.add_tab(camera_settings_tab, "Camera Settings")
    main_window.add_tab(rtsp_tab, "RTSP")
    main_window.add_tab(overlay_tab, "Overlay")
    main_window.add_tab(tracker_settings_tab, "Tracker Settings")
    main_window.add_tab(advanced_tab, "Advanced")
    main_window.add_tab(sub_payloads_tab, "Sub-Payloads")
    main_window.add_tab(hardware_tab, "Hardware")

    # Tab switching handler - moves video display to active tab
    def on_tab_switched(index: int):
        """Reparent video display to the currently active tab."""
        current_tab = main_window.tab_widget.widget(index)
        if hasattr(current_tab, 'set_video_display'):
            current_tab.set_video_display(video_manager)
            logger.debug(f"Video display moved to tab index {index}")

    main_window.tab_widget.currentChanged.connect(on_tab_switched)
    # Trigger initial display on first tab (Connection)
    on_tab_switched(0)

    main_window.start_network_thread()

    # ========================================================================
    # COMBINED CONTROL TAB SIGNAL CONNECTIONS
    # ========================================================================

    # NOTE: Trackpad now controls speed (via pan_speed_changed/tilt_speed_changed signals)
    # No longer using pan_tilt_command signal - trackpad is joystick mode

    # Connect zoom - get selected camera each time (direction: +1 in, -1 out, 0 stop)
    combined_tab.zoom_command.connect(
        lambda direction: main_window.network_thread.send_zoom(float(direction), combined_tab.get_selected_camera())
    )

    # Connect focus - get selected camera each time (direction: +1 far, -1 near, 0 stop)
    combined_tab.focus_command.connect(
        lambda direction: main_window.network_thread.send_focus(float(direction), combined_tab.get_selected_camera())
    )

    combined_tab.home_requested.connect(
        lambda: main_window.network_thread.send_pan_tilt(0.0, 0.0)
    )

    # Connect speed control sliders
    combined_tab.pan_speed_changed.connect(main_window.network_thread.send_pan_speed)
    combined_tab.tilt_speed_changed.connect(main_window.network_thread.send_tilt_speed)
    combined_tab.zoom_speed_changed.connect(main_window.network_thread.send_zoom)
    combined_tab.focus_speed_changed.connect(main_window.network_thread.send_focus)

    def handle_connection_toggle():
        if not main_window.network_thread.network_manager or not main_window.network_thread.network_manager.connected:
            target_ip = connection_tab.get_target_ip()
            # Connect to system with new IP (video streams will update on successful connection)
            main_window.network_thread.connect_to_system(target_ip)
        else:
            main_window.network_thread.disconnect_from_system()

    # Camera discovery thread (runs once in background when connected)
    camera_discovery_thread = None

    def handle_camera_discovery_complete(availability: dict):
        """Called when camera discovery finishes - starts centralized video streams ONCE."""
        target_ip = connection_tab.get_target_ip()
        logger.info(f"Starting centralized video streams for {target_ip}...")

        # Start streams in the centralized video manager (ONCE, not 9 times)
        video_manager.start_streams(target_ip, availability)

    def handle_connection_success(connected: bool):
        """Update connection tab status, video streams and component status after TCP connection succeeds, stop streams on disconnect."""
        nonlocal camera_discovery_thread

        if connected:
            target_ip = connection_tab.get_target_ip()
            connection_tab.update_connection_status(connected)

            # Start component status update (SSH checks)
            connection_tab.update_component_status(target_ip)

            # Query system information (NexOS version, serial, tracking status)
            main_window.network_thread.query_system_info()

            # Enable Hardware tab and auto-refresh USB devices
            hardware_tab.set_connection_status(True, target_ip)

            # Start camera discovery in background thread (runs ONCE, not 9 times)
            # Tests each camera 5 times with ping + RTSP checks
            logger.info(f"Starting camera discovery thread for {target_ip}...")
            from utils.threaded_camera_discovery import CameraDiscoveryThread
            camera_discovery_thread = CameraDiscoveryThread(target_ip, timeout=3.0, retries=5)
            camera_discovery_thread.discovery_complete.connect(handle_camera_discovery_complete)
            camera_discovery_thread.start()

        else:
            # Stop centralized video streams on disconnect (ONCE, not 9 times)
            connection_tab.update_connection_status(connected)
            video_manager.stop_streams()
            hardware_tab.set_connection_status(False)

    connection_tab.connection_toggle.connect(handle_connection_toggle)
    main_window.network_thread.connection_status_changed.connect(handle_connection_success)

    # System information updates
    def handle_system_info(info_type: str, value: str):
        if info_type == 'nexos_version':
            connection_tab.update_system_info(nexos_version=value)
        elif info_type == 'mainboard_serial':
            connection_tab.update_system_info(mainboard_serial=value)
        elif info_type == 'tracking_status':
            connection_tab.update_system_info(tracking_status=value)

    main_window.network_thread.system_info_received.connect(handle_system_info)

    # Telemetry updates
    main_window.network_thread.telemetry_received.connect(
        lambda data: combined_tab.update_actual_position(data['pan'], data['tilt']) if data['pan'] is not None else None
    )

    # Connect Camera Settings tab camera function signals (formerly in Functions tab)
    camera_settings_tab.zoom_to_pos_changed.connect(
        lambda camera, position: main_window.network_thread.send_zoom_to_position(camera, position)
    )
    camera_settings_tab.one_push_af_pressed.connect(
        lambda camera: main_window.network_thread.send_autofocus(camera)
    )
    camera_settings_tab.camera_profile_changed.connect(
        lambda camera, profile: main_window.network_thread.send_camera_profile(camera, profile)
    )
    camera_settings_tab.video_stabilizer_enabled_changed.connect(
        lambda camera, enable: main_window.network_thread.send_video_stabilizer(camera, enable)
    )
    camera_settings_tab.digital_zoom_level_changed.connect(
        lambda camera, level: main_window.network_thread.send_digital_zoom_level(camera, level)
    )
    camera_settings_tab.digital_zoom_enabled_changed.connect(
        lambda camera, enable: main_window.network_thread.send_digital_zoom_enable(camera, enable)
    )
    camera_settings_tab.clahe_enabled_changed.connect(
        lambda camera, enable: main_window.network_thread.send_clahe(camera, enable)
    )
    camera_settings_tab.color_palette_changed.connect(
        lambda camera, palette: main_window.network_thread.send_color_palette(camera, palette)
    )
    camera_settings_tab.color_filter_enabled_changed.connect(
        lambda camera, enable: main_window.network_thread.send_color_filter(camera, enable)
    )

    # Connect Slave Zoom signals from Camera Settings tab
    camera_settings_tab.slave_zoom_enabled.connect(
        lambda enabled: main_window.network_thread.send_slave_zoom_mode(enabled)
    )
    camera_settings_tab.slave_zoom_master_changed.connect(
        lambda camera: main_window.network_thread.send_slave_zoom_master(camera)
    )
    camera_settings_tab.slave_zoom_query_requested.connect(
        main_window.network_thread.send_query_slave_zoom
    )


    # ========================================================================
    # MOTOR SETTINGS TAB SIGNAL CONNECTIONS
    # ========================================================================

    logger.info("Connecting Motor Settings tab signals")

    # Motor Calibration signals
    motor_settings_tab.pan_set_zero_requested.connect(
        lambda: main_window.network_thread.send_pan_set_zero()
    )
    motor_settings_tab.pan_reset_zero_requested.connect(
        lambda: main_window.network_thread.send_pan_reset_zero()
    )
    motor_settings_tab.pan_zero_pos_changed.connect(
        lambda pos: main_window.network_thread.send_pan_zero_pos(pos)
    )
    motor_settings_tab.tilt_set_zero_requested.connect(
        lambda: main_window.network_thread.send_tilt_set_zero()
    )
    motor_settings_tab.tilt_reset_zero_requested.connect(
        lambda: main_window.network_thread.send_tilt_reset_zero()
    )
    motor_settings_tab.tilt_zero_pos_changed.connect(
        lambda pos: main_window.network_thread.send_tilt_zero_pos(pos)
    )

    # Motor Limits signals
    motor_settings_tab.pan_left_limit_changed.connect(
        lambda limit: main_window.network_thread.send_pan_left_limit(limit)
    )
    motor_settings_tab.pan_right_limit_changed.connect(
        lambda limit: main_window.network_thread.send_pan_right_limit(limit)
    )
    motor_settings_tab.tilt_up_limit_changed.connect(
        lambda limit: main_window.network_thread.send_tilt_up_limit(limit)
    )
    motor_settings_tab.tilt_down_limit_changed.connect(
        lambda limit: main_window.network_thread.send_tilt_down_limit(limit)
    )

    # Motor Speed signals
    motor_settings_tab.pan_max_speed_changed.connect(
        lambda speed: main_window.network_thread.send_pan_max_speed(speed)
    )
    motor_settings_tab.pan_position_speed_changed.connect(
        lambda speed: main_window.network_thread.send_pan_position_speed(speed)
    )
    motor_settings_tab.tilt_max_speed_changed.connect(
        lambda speed: main_window.network_thread.send_tilt_max_speed(speed)
    )
    motor_settings_tab.tilt_position_speed_changed.connect(
        lambda speed: main_window.network_thread.send_tilt_position_speed(speed)
    )

    # Motor Behavior signals
    motor_settings_tab.pan_invert_movement_changed.connect(
        lambda inverted: main_window.network_thread.send_pan_invert_movement(inverted)
    )
    motor_settings_tab.tilt_invert_movement_changed.connect(
        lambda inverted: main_window.network_thread.send_tilt_invert_movement(inverted)
    )
    motor_settings_tab.zoom_dependent_mode_changed.connect(
        lambda enable: main_window.network_thread.send_zoom_dependent_mode(enable)
    )
    motor_settings_tab.block_pt_changed.connect(
        lambda blocked: main_window.network_thread.send_block_pt(blocked)
    )

    # Acceleration/Deceleration signals
    motor_settings_tab.acc_vel_max_changed.connect(
        lambda value: main_window.network_thread.send_acc_vel_max(value)
    )
    motor_settings_tab.acc_dec_max_changed.connect(
        lambda value: main_window.network_thread.send_acc_dec_max(value)
    )
    motor_settings_tab.acc_dec_rate_changed.connect(
        lambda value: main_window.network_thread.send_acc_dec_rate(value)
    )
    motor_settings_tab.acc_dec_vstop_changed.connect(
        lambda value: main_window.network_thread.send_acc_dec_vstop(value)
    )

    # Homing signals
    motor_settings_tab.homing_delay_mode_changed.connect(
        lambda enable: main_window.network_thread.send_homing_delay_mode(enable)
    )
    motor_settings_tab.homing_delay_time_changed.connect(
        lambda time: main_window.network_thread.send_homing_delay_time(time)
    )

    # System Control signals
    motor_settings_tab.reset_controller_requested.connect(
        lambda: main_window.network_thread.send_reset_controller()
    )
    motor_settings_tab.query_all_motor_settings_requested.connect(
        lambda: main_window.network_thread.send_query_all_motor_settings()
    )


    # Query signals
    motor_settings_tab.query_pan_limits_requested.connect(
        main_window.network_thread.send_query_pan_limits
    )
    motor_settings_tab.query_tilt_limits_requested.connect(
        main_window.network_thread.send_query_tilt_limits
    )
    motor_settings_tab.query_homing_requested.connect(
        main_window.network_thread.send_query_homing
    )

    # ========================================================================
    # CAMERA SETTINGS TAB SIGNAL CONNECTIONS
    # ========================================================================

    logger.info("Connecting Camera Settings tab signals")

    # Group 2: Exposure Control signals
    # Note: exposure_mode expects int in network_thread, but tab sends string - needs conversion
    def handle_exposure_mode(camera, mode_str):
        mode_map = {"Auto": 0, "Manual": 1, "Aperture Priority": 2, "Shutter Priority": 3}
        mode = mode_map.get(mode_str, 0)
        main_window.network_thread.send_exposure_mode(camera, mode)

    camera_settings_tab.exposure_mode_changed.connect(handle_exposure_mode)

    camera_settings_tab.shutter_speed_changed.connect(
        lambda camera, speed: main_window.network_thread.send_shutter_speed(camera, speed)
    )
    camera_settings_tab.gain_changed.connect(
        lambda camera, gain: main_window.network_thread.send_gain(camera, gain)
    )
    camera_settings_tab.exposure_auto_mode_changed.connect(
        lambda camera, enable: main_window.network_thread.send_auto_mode(camera, 1 if enable else 0)
    )

    # Group 3: Iris Control signals
    camera_settings_tab.iris_mode_changed.connect(
        lambda camera, auto: main_window.network_thread.send_iris_mode(camera, 1 if auto else 0)
    )
    camera_settings_tab.iris_value_changed.connect(
        lambda camera, value: main_window.network_thread.send_iris_value(camera, float(value))
    )
    camera_settings_tab.iris_open_pressed.connect(
        lambda camera: main_window.network_thread.send_iris_open(camera)
    )
    camera_settings_tab.iris_close_pressed.connect(
        lambda camera: main_window.network_thread.send_iris_close(camera)
    )
    camera_settings_tab.iris_stop_pressed.connect(
        lambda camera: main_window.network_thread.send_iris_stop(camera)
    )
    camera_settings_tab.iris_to_pos_changed.connect(
        lambda camera, position: main_window.network_thread.send_iris_to_pos(camera, position)
    )

    # Group 4: Focus Control signals
    camera_settings_tab.focus_to_pos_changed.connect(
        lambda camera, position: main_window.network_thread.send_focus_to_position(camera, position)
    )
    camera_settings_tab.one_push_af_pressed.connect(
        lambda camera: main_window.network_thread.send_one_push_af(camera)
    )
    camera_settings_tab.autofocus_mode_changed.connect(
        lambda camera, enable: main_window.network_thread.send_autofocus_mode(camera, enable)
    )
    camera_settings_tab.focus_speed_multiplier_changed.connect(
        lambda camera, multiplier: main_window.network_thread.send_focus_speed_multiplier(camera, multiplier)
    )

    # Group 5: Lens Control signals
    camera_settings_tab.zoom_to_pos_changed.connect(
        lambda camera, position: main_window.network_thread.send_zoom_to_position(camera, position)  # Reuse existing method
    )
    camera_settings_tab.zoom_speed_multiplier_changed.connect(
        lambda camera, multiplier: main_window.network_thread.send_zoom_speed_multiplier(camera, multiplier)
    )
    camera_settings_tab.tele_end_pos_changed.connect(
        lambda camera, position: main_window.network_thread.send_tele_end_pos(camera, position)
    )
    camera_settings_tab.wide_end_pos_changed.connect(
        lambda camera, position: main_window.network_thread.send_wide_end_pos(camera, position)
    )
    camera_settings_tab.far_end_pos_changed.connect(
        lambda camera, position: main_window.network_thread.send_far_end_pos(camera, position)
    )
    camera_settings_tab.near_end_pos_changed.connect(
        lambda camera, position: main_window.network_thread.send_near_end_pos(camera, position)
    )

    # Group 6: White Balance signals
    def handle_white_balance_mode(camera, mode_str):
        mode_map = {"Auto": 0, "Manual": 1, "Indoor": 2, "Outdoor": 3, "One-Push": 4, "ATW": 5}
        mode = mode_map.get(mode_str, 0)
        main_window.network_thread.send_white_balance(camera, mode)

    camera_settings_tab.white_balance_mode_changed.connect(handle_white_balance_mode)

    camera_settings_tab.wb_red_gain_changed.connect(
        lambda camera, gain: main_window.network_thread.send_wb_red_gain(camera, gain)
    )
    camera_settings_tab.wb_blue_gain_changed.connect(
        lambda camera, gain: main_window.network_thread.send_wb_blue_gain(camera, gain)
    )

    def handle_color_mode(camera, mode_str):
        mode_map = {"Color": 0, "Black & White": 1, "Sepia": 2}
        mode = mode_map.get(mode_str, 0)
        main_window.network_thread.send_color_mode(camera, mode)

    camera_settings_tab.color_mode_changed.connect(handle_color_mode)

    # Group 7: Image Enhancement signals
    camera_settings_tab.brightness_changed.connect(
        lambda camera, value: main_window.network_thread.send_brightness(camera, value)
    )
    camera_settings_tab.contrast_changed.connect(
        lambda camera, value: main_window.network_thread.send_contrast(camera, value)
    )
    camera_settings_tab.saturation_changed.connect(
        lambda camera, value: main_window.network_thread.send_saturation(camera, value)
    )
    camera_settings_tab.sharpness_changed.connect(
        lambda camera, value: main_window.network_thread.send_sharpness(camera, value)
    )

    # Group 8: Advanced Image Processing signals
    # Note: network_thread methods expect mode (int), not enable+level
    camera_settings_tab.backlight_compensation_changed.connect(
        lambda camera, enable, level: main_window.network_thread.send_backlight_compensation(camera, level if enable else 0)
    )
    camera_settings_tab.wide_dynamic_range_changed.connect(
        lambda camera, enable, level: main_window.network_thread.send_wide_dynamic_range(camera, level if enable else 0)
    )
    camera_settings_tab.noise_reduction_changed.connect(
        lambda camera, enable, level: main_window.network_thread.send_noise_reduction(camera, level if enable else 0)
    )
    camera_settings_tab.defog_mode_changed.connect(
        lambda camera, enable: main_window.network_thread.send_defog_mode(camera, 1 if enable else 0)
    )

    # Group 9: Digital Zoom signals (already connected above)
    # camera_settings_tab.digital_zoom_enabled_changed.connect - already connected
    # camera_settings_tab.digital_zoom_level_changed.connect - already connected

    # Group 10: CLAHE signals (CLAHE enable already connected above)
    # camera_settings_tab.clahe_enabled_changed.connect - already connected
    camera_settings_tab.clahe_clip_limit_changed.connect(
        lambda camera, limit: main_window.network_thread.send_clahe_clip_limit(camera, limit)
    )
    camera_settings_tab.clahe_tiles_grid_size_changed.connect(
        lambda camera, size: main_window.network_thread.send_clahe_tiles_grid_size(camera, size)
    )

    # Group 11: Color Filter signals (color_filter_enabled and color_palette already connected above)
    # camera_settings_tab.color_filter_enabled_changed.connect - already connected
    # camera_settings_tab.color_palette_changed.connect - already connected
    camera_settings_tab.color_filter_auto_mode_changed.connect(
        lambda camera, enable: main_window.network_thread.send_color_filter_auto_mode(camera, 1 if enable else 0)
    )
    camera_settings_tab.color_filter_hue_changed.connect(
        lambda camera, hue: main_window.network_thread.send_color_filter_hue(camera, hue)
    )
    camera_settings_tab.color_filter_saturation_changed.connect(
        lambda camera, saturation: main_window.network_thread.send_color_filter_saturation(camera, saturation)
    )
    camera_settings_tab.color_filter_gamma_changed.connect(
        lambda camera, gamma: main_window.network_thread.send_color_filter_gamma(camera, gamma)
    )

    # Group 12: Image Flip signals
    def handle_image_flip_mode(camera, mode_str):
        mode_map = {"Normal": 0, "Horizontal": 1, "Vertical": 2, "Both": 3}
        mode = mode_map.get(mode_str, 0)
        main_window.network_thread.send_image_flip_mode(camera, mode)

    camera_settings_tab.image_flip_mode_changed.connect(handle_image_flip_mode)

    camera_settings_tab.horizontal_flip_changed.connect(
        lambda camera, enable: main_window.network_thread.send_image_flip_horizontal(camera, enable)
    )
    camera_settings_tab.vertical_flip_changed.connect(
        lambda camera, enable: main_window.network_thread.send_image_flip_vertical(camera, enable)
    )

    # Group 13: Video Stabilizer signals (video_stabilizer_enabled already connected above)
    # camera_settings_tab.video_stabilizer_enabled_changed.connect - already connected
    camera_settings_tab.stabilizer_x_offset_limit_changed.connect(
        lambda camera, pixels: main_window.network_thread.send_stabilizer_x_offset_limit(camera, int(pixels))
    )
    camera_settings_tab.stabilizer_y_offset_limit_changed.connect(
        lambda camera, pixels: main_window.network_thread.send_stabilizer_y_offset_limit(camera, int(pixels))
    )
    camera_settings_tab.stabilizer_a_offset_limit_changed.connect(
        lambda camera, degrees: main_window.network_thread.send_stabilizer_a_offset_limit(camera, int(degrees))
    )

    def handle_stabilizer_mode(camera, mode_str):
        mode_map = {"Auto": 0, "Manual": 1, "Hybrid": 2}
        mode = mode_map.get(mode_str, 0)
        main_window.network_thread.send_stabilizer_mode(camera, mode)

    camera_settings_tab.stabilizer_mode_changed.connect(handle_stabilizer_mode)

    def handle_stabilizer_type(camera, type_str):
        type_map = {"Digital": 0, "Mechanical": 1, "Combined": 2}
        stabilizer_type = type_map.get(type_str, 0)
        main_window.network_thread.send_stabilizer_type(camera, stabilizer_type)

    camera_settings_tab.stabilizer_type_changed.connect(handle_stabilizer_type)

    camera_settings_tab.stabilizer_transparent_border_changed.connect(
        lambda camera, enable: main_window.network_thread.send_stabilizer_transparent_border(camera, enable)
    )
    camera_settings_tab.stabilizer_const_x_offset_changed.connect(
        lambda camera, offset: main_window.network_thread.send_stabilizer_const_x_offset(camera, int(offset))
    )
    camera_settings_tab.stabilizer_const_y_offset_changed.connect(
        lambda camera, offset: main_window.network_thread.send_stabilizer_const_y_offset(camera, int(offset))
    )
    camera_settings_tab.stabilizer_const_a_offset_changed.connect(
        lambda camera, offset: main_window.network_thread.send_stabilizer_const_a_offset(camera, int(offset))
    )

    # Group 14: Camera Profiles signals (camera_profile_changed already connected above)
    # camera_settings_tab.camera_profile_changed.connect - already connected
    camera_settings_tab.query_camera_settings_requested.connect(
        lambda camera: main_window.network_thread.send_query_camera_settings(camera)
    )

    # ========================================================================
    # RTSP TAB SIGNAL CONNECTIONS (~45 signals)
    # ========================================================================

    logger.info("Connecting RTSP tab signals")

    # Group 1: Target Selection (optional - for coordination if needed)
    # rtsp_tab.target_changed.connect(...)  # Not connected to network_thread

    # Group 2: Stream Control signals
    rtsp_tab.stream_enable_pressed.connect(
        lambda camera, stream: main_window.network_thread.send_video_stream_enable(camera, stream)
    )
    rtsp_tab.stream_disable_pressed.connect(
        lambda camera, stream: main_window.network_thread.send_video_stream_disable(camera, stream)
    )
    rtsp_tab.stream_restart_pressed.connect(
        lambda camera, stream: main_window.network_thread.send_video_stream_restart(camera, stream)
    )

    # Group 3: RTSP Settings signals
    rtsp_tab.rtsp_suffix_changed.connect(
        lambda camera, stream, suffix: main_window.network_thread.send_rtsp_suffix(camera, stream, suffix)
    )
    rtsp_tab.rtsp_port_changed.connect(
        lambda port: main_window.network_thread.send_rtsp_port(1, 1, port)  # Note: Apply to Camera 1, Stream 1 (or loop through all)
    )
    rtsp_tab.rtsp_multicast_ip_changed.connect(
        lambda camera, stream, ip: main_window.network_thread.send_rtsp_multicast_ip(camera, stream, ip)
    )
    rtsp_tab.rtsp_multicast_port_changed.connect(
        lambda camera, stream, port: main_window.network_thread.send_rtsp_multicast_port(camera, stream, port)
    )
    rtsp_tab.rtsp_user_changed.connect(
        lambda camera, stream, user: main_window.network_thread.send_rtsp_user(camera, stream, user)
    )
    rtsp_tab.rtsp_password_changed.connect(
        lambda camera, stream, password: main_window.network_thread.send_rtsp_password(camera, stream, password)
    )

    # Group 4: Video Encoding signals
    def handle_resolution_changed(camera: int, stream: int, resolution: str):
        """Parse resolution string (e.g., '1920x1080') and send width, height."""
        try:
            if 'x' in resolution.lower():
                width, height = map(int, resolution.lower().split('x'))
                main_window.network_thread.send_resolution(camera, stream, width, height)
            else:
                logger.warning(f"Invalid resolution format: {resolution}")
        except Exception as e:
            logger.error(f"Failed to parse resolution {resolution}: {e}")

    rtsp_tab.resolution_changed.connect(handle_resolution_changed)
    rtsp_tab.codec_changed.connect(
        lambda camera, stream, codec: main_window.network_thread.send_codec(camera, stream, codec)
    )
    rtsp_tab.h264_profile_changed.connect(
        lambda camera, stream, profile: main_window.network_thread.send_h264_profile(camera, stream, profile)
    )
    rtsp_tab.jpeg_quality_changed.connect(
        lambda camera, stream, quality: main_window.network_thread.send_jpeg_quality(camera, stream, quality)
    )

    # Group 5: Bitrate Settings signals
    rtsp_tab.bitrate_changed.connect(
        lambda camera, stream, bitrate: main_window.network_thread.send_bitrate(camera, stream, bitrate)
    )
    rtsp_tab.bitrate_mode_changed.connect(
        lambda camera, stream, mode: main_window.network_thread.send_bitrate_mode(camera, stream, mode)
    )
    rtsp_tab.min_bitrate_changed.connect(
        lambda camera, stream, bitrate: main_window.network_thread.send_min_bitrate(camera, stream, bitrate)
    )
    rtsp_tab.max_bitrate_changed.connect(
        lambda camera, stream, bitrate: main_window.network_thread.send_max_bitrate(camera, stream, bitrate)
    )

    # Group 6: Frame Settings signals
    rtsp_tab.fps_changed.connect(
        lambda camera, stream, fps: main_window.network_thread.send_fps(camera, stream, fps)
    )
    rtsp_tab.gop_changed.connect(
        lambda camera, stream, gop: main_window.network_thread.send_gop(camera, stream, gop)
    )

    # Group 7: Video Processing signals
    rtsp_tab.fit_mode_changed.connect(
        lambda camera, stream, mode: main_window.network_thread.send_fit_mode(camera, stream, mode)
    )
    rtsp_tab.overlay_mode_changed.connect(
        lambda camera, stream, enable: main_window.network_thread.send_overlay_mode(camera, stream, enable)
    )
    rtsp_tab.metadata_mode_changed.connect(
        lambda camera, stream, enable: main_window.network_thread.send_metadata_mode(camera, stream, enable)
    )
    rtsp_tab.metadata_suffix_changed.connect(
        lambda camera, stream, suffix: main_window.network_thread.send_metadata_suffix(camera, stream, suffix)
    )

    # Group 8: RTP Direct Streaming signals
    rtsp_tab.rtp_mode_changed.connect(
        lambda camera, stream, enable: main_window.network_thread.send_rtp_mode(camera, stream, enable)
    )
    rtsp_tab.rtp_port_changed.connect(
        lambda camera, stream, port: main_window.network_thread.send_rtp_port(camera, stream, port)
    )
    rtsp_tab.rtp_dest_ip_changed.connect(
        lambda camera, stream, ip: main_window.network_thread.send_rtp_dest_ip(camera, stream, ip)
    )

    # Group 9: RTMP Server signals
    rtsp_tab.rtmp_mode_changed.connect(
        lambda camera, stream, enable: main_window.network_thread.send_rtmp_mode(camera, stream, enable)
    )
    rtsp_tab.rtmp_port_changed.connect(
        lambda camera, stream, port: main_window.network_thread.send_rtmp_port(camera, stream, port)
    )

    # Group 10: HLS Server signals
    rtsp_tab.hls_mode_changed.connect(
        lambda camera, stream, enable: main_window.network_thread.send_hls_mode(camera, stream, enable)
    )
    rtsp_tab.hls_port_changed.connect(
        lambda camera, stream, port: main_window.network_thread.send_hls_port(camera, stream, port)
    )

    # Group 11: SRT Server signals
    rtsp_tab.srt_mode_changed.connect(
        lambda camera, stream, enable: main_window.network_thread.send_srt_mode(camera, stream, enable)
    )
    rtsp_tab.srt_port_changed.connect(
        lambda camera, stream, port: main_window.network_thread.send_srt_port(camera, stream, port)
    )

    # Group 12: Advanced Settings signals
    rtsp_tab.udp_payload_changed.connect(
        lambda camera, stream, size: main_window.network_thread.send_udp_payload_size(camera, stream, size)
    )
    rtsp_tab.query_video_settings_pressed.connect(
        lambda camera, stream: main_window.network_thread.send_query_video_settings(camera, stream)
    )

    # ========================================================================
    # OVERLAY TAB SIGNAL CONNECTIONS (~12 signals)
    # ========================================================================

    logger.info("Connecting Overlay tab signals")

    # Target Camera Selector (optional - for coordination if needed)
    # overlay_tab.target_camera_changed.connect(...)  # Not connected to network_thread

    # Crosshair signals
    overlay_tab.crosshair_mode_changed.connect(
        lambda camera, enable: main_window.network_thread.send_crosshair_mode(camera, enable)
    )
    overlay_tab.crosshair_size_changed.connect(
        lambda camera, size: main_window.network_thread.send_crosshair_size(camera, size)
    )
    overlay_tab.crosshair_color_changed.connect(
        lambda camera, color: main_window.network_thread.send_crosshair_color(camera, color)
    )

    # Information Overlay signals
    overlay_tab.datetime_overlay_changed.connect(
        lambda camera, enable: main_window.network_thread.send_datetime_overlay(camera, enable)
    )
    overlay_tab.zoom_pos_overlay_changed.connect(
        lambda camera, enable: main_window.network_thread.send_zoom_pos_overlay(camera, enable)
    )
    overlay_tab.focus_mode_overlay_changed.connect(
        lambda camera, enable: main_window.network_thread.send_focus_mode_overlay(camera, enable)
    )
    overlay_tab.digital_zoom_overlay_changed.connect(
        lambda camera, enable: main_window.network_thread.send_digital_zoom_overlay(camera, enable)
    )
    overlay_tab.clahe_overlay_changed.connect(
        lambda camera, enable: main_window.network_thread.send_clahe_overlay(camera, enable)
    )
    overlay_tab.tracker_overlay_changed.connect(
        lambda camera, enable: main_window.network_thread.send_tracker_overlay(camera, enable)
    )
    overlay_tab.pan_tilt_overlay_changed.connect(
        lambda camera, enable: main_window.network_thread.send_pan_tilt_overlay(camera, enable)
    )
    overlay_tab.lrf_overlay_changed.connect(
        lambda camera, enable: main_window.network_thread.send_lrf_overlay(camera, enable)
    )

    # WebRTC Overlay signal
    overlay_tab.webrtc_overlay_changed.connect(
        lambda camera, enable: main_window.network_thread.send_webrtc_overlay(camera, enable)
    )

    # ========================================================================
    # TRACKER SETTINGS TAB SIGNAL CONNECTIONS (~52 signals)
    # ========================================================================

    logger.info("Connecting Tracker Settings tab signals")

    # Motion Magnificator (2 signals)
    tracker_settings_tab.motion_magnificator_changed.connect(
        lambda camera, enable: (
            main_window.network_thread.send_motion_magnificator_enable(camera) if enable
            else main_window.network_thread.send_motion_magnificator_disable(camera)
        )
    )
    tracker_settings_tab.magnification_level_changed.connect(
        lambda camera, level: main_window.network_thread.send_motion_magnificator_level(camera, level)
    )

    # VideoTracker (7 signals)
    tracker_settings_tab.video_tracker_reset_pressed.connect(
        lambda camera: main_window.network_thread.send_video_tracker_reset(camera)
    )
    tracker_settings_tab.video_tracker_changed.connect(
        lambda camera, enable: (
            main_window.network_thread.send_video_tracker_enable(camera) if enable
            else main_window.network_thread.send_video_tracker_disable(camera)
        )
    )
    tracker_settings_tab.video_tracker_lock_pressed.connect(
        lambda camera: main_window.network_thread.send_video_tracker_lock(camera)
    )
    tracker_settings_tab.video_tracker_unlock_pressed.connect(
        lambda camera: main_window.network_thread.send_video_tracker_unlock(camera)
    )
    tracker_settings_tab.tracker_mode_changed.connect(
        lambda camera, mode: main_window.network_thread.send_video_tracker_mode(camera, mode)
    )
    tracker_settings_tab.object_size_changed.connect(
        lambda camera, size: main_window.network_thread.send_video_tracker_object_size(camera, size)
    )
    tracker_settings_tab.search_area_size_changed.connect(
        lambda camera, size: main_window.network_thread.send_video_tracker_search_area_size(camera, size)
    )

    # MotionDetector (13 signals)
    tracker_settings_tab.motion_detector_reset_pressed.connect(
        lambda camera: main_window.network_thread.send_motion_detector_reset(camera)
    )
    tracker_settings_tab.motion_detector_changed.connect(
        lambda camera, enable: (
            main_window.network_thread.send_motion_detector_enable(camera) if enable
            else main_window.network_thread.send_motion_detector_disable(camera)
        )
    )
    tracker_settings_tab.motion_detector_frame_buffer_changed.connect(
        lambda camera, size: main_window.network_thread.send_motion_detector_frame_buffer(camera, size)
    )
    tracker_settings_tab.motion_detector_min_width_changed.connect(
        lambda camera, width: main_window.network_thread.send_motion_detector_min_width(camera, width)
    )
    tracker_settings_tab.motion_detector_max_width_changed.connect(
        lambda camera, width: main_window.network_thread.send_motion_detector_max_width(camera, width)
    )
    tracker_settings_tab.motion_detector_min_height_changed.connect(
        lambda camera, height: main_window.network_thread.send_motion_detector_min_height(camera, height)
    )
    tracker_settings_tab.motion_detector_max_height_changed.connect(
        lambda camera, height: main_window.network_thread.send_motion_detector_max_height(camera, height)
    )
    tracker_settings_tab.motion_detector_x_criteria_changed.connect(
        lambda camera, criteria: main_window.network_thread.send_motion_detector_x_criteria(camera, criteria)
    )
    tracker_settings_tab.motion_detector_y_criteria_changed.connect(
        lambda camera, criteria: main_window.network_thread.send_motion_detector_y_criteria(camera, criteria)
    )
    tracker_settings_tab.motion_detector_reset_criteria_changed.connect(
        lambda camera, criteria: main_window.network_thread.send_motion_detector_reset_criteria(camera, criteria)
    )
    tracker_settings_tab.motion_detector_sensitivity_changed.connect(
        lambda camera, sensitivity: main_window.network_thread.send_motion_detector_sensitivity(camera, sensitivity)
    )
    tracker_settings_tab.motion_detector_mode_changed.connect(
        lambda camera, mode: main_window.network_thread.send_motion_detector_mode(camera, mode)
    )

    # ChangesDetector (13 signals - identical to MotionDetector)
    tracker_settings_tab.changes_detector_reset_pressed.connect(
        lambda camera: main_window.network_thread.send_changes_detector_reset(camera)
    )
    tracker_settings_tab.changes_detector_changed.connect(
        lambda camera, enable: (
            main_window.network_thread.send_changes_detector_enable(camera) if enable
            else main_window.network_thread.send_changes_detector_disable(camera)
        )
    )
    tracker_settings_tab.changes_detector_frame_buffer_changed.connect(
        lambda camera, size: main_window.network_thread.send_changes_detector_frame_buffer(camera, size)
    )
    tracker_settings_tab.changes_detector_min_width_changed.connect(
        lambda camera, width: main_window.network_thread.send_changes_detector_min_width(camera, width)
    )
    tracker_settings_tab.changes_detector_max_width_changed.connect(
        lambda camera, width: main_window.network_thread.send_changes_detector_max_width(camera, width)
    )
    tracker_settings_tab.changes_detector_min_height_changed.connect(
        lambda camera, height: main_window.network_thread.send_changes_detector_min_height(camera, height)
    )
    tracker_settings_tab.changes_detector_max_height_changed.connect(
        lambda camera, height: main_window.network_thread.send_changes_detector_max_height(camera, height)
    )
    tracker_settings_tab.changes_detector_x_criteria_changed.connect(
        lambda camera, criteria: main_window.network_thread.send_changes_detector_x_criteria(camera, criteria)
    )
    tracker_settings_tab.changes_detector_y_criteria_changed.connect(
        lambda camera, criteria: main_window.network_thread.send_changes_detector_y_criteria(camera, criteria)
    )
    tracker_settings_tab.changes_detector_reset_criteria_changed.connect(
        lambda camera, criteria: main_window.network_thread.send_changes_detector_reset_criteria(camera, criteria)
    )
    tracker_settings_tab.changes_detector_sensitivity_changed.connect(
        lambda camera, sensitivity: main_window.network_thread.send_changes_detector_sensitivity(camera, sensitivity)
    )
    tracker_settings_tab.changes_detector_mode_changed.connect(
        lambda camera, mode: main_window.network_thread.send_changes_detector_mode(camera, mode)
    )

    # Classification (4 signals)
    tracker_settings_tab.classification_changed.connect(
        lambda camera, enable: (
            main_window.network_thread.send_classification_enable(camera) if enable
            else main_window.network_thread.send_classification_disable(camera)
        )
    )
    tracker_settings_tab.classification_model_changed.connect(
        lambda camera, model: main_window.network_thread.send_classification_model(camera, model)
    )
    tracker_settings_tab.classification_confidence_changed.connect(
        lambda camera, confidence: main_window.network_thread.send_classification_confidence(camera, confidence)
    )
    tracker_settings_tab.query_classification_pressed.connect(
        lambda camera: main_window.network_thread.send_query_classification_status(camera)
    )

    # Detection Results (2 signals)
    tracker_settings_tab.subscribe_detection_pressed.connect(
        lambda camera: main_window.network_thread.send_subscribe_objects_events(camera)
    )
    tracker_settings_tab.clear_detection_pressed.connect(
        lambda camera: logger.info(f"Clear detection results requested for camera {camera}")
    )

    # License Status (5 signals)
    tracker_settings_tab.query_video_tracker_license_pressed.connect(
        lambda: main_window.network_thread.send_query_video_tracker_license_status()
    )
    tracker_settings_tab.query_video_stabiliser_license_pressed.connect(
        lambda: main_window.network_thread.send_query_video_stabiliser_license_status()
    )
    tracker_settings_tab.query_motion_detector_license_pressed.connect(
        lambda: main_window.network_thread.send_query_motion_detector_license_status()
    )
    tracker_settings_tab.query_changes_detector_license_pressed.connect(
        lambda: main_window.network_thread.send_query_changes_detector_license_status()
    )
    tracker_settings_tab.query_classification_license_pressed.connect(
        lambda: main_window.network_thread.send_query_classification_license_status()
    )

    # ========================================================================
    # ADVANCED TAB SIGNAL CONNECTIONS (24 signals)
    # ========================================================================

    logger.info("Connecting Advanced tab signals")

    # Procedure Manager (4 signals)
    advanced_tab.procedure_load_requested.connect(
        lambda name: main_window.network_thread.send_procedure_load(name)
    )
    advanced_tab.procedure_execute_requested.connect(
        lambda: main_window.network_thread.send_procedure_execute()
    )
    advanced_tab.procedure_stop_requested.connect(
        lambda: main_window.network_thread.send_procedure_stop()
    )
    advanced_tab.procedure_status_query_requested.connect(
        lambda: main_window.network_thread.query_procedure_status()
    )

    # Bad Pixel Processor (5 signals - camera-aware)
    advanced_tab.bad_pixel_enabled.connect(
        lambda camera: main_window.network_thread.send_bad_pixel_enable(camera)
    )
    advanced_tab.bad_pixel_disabled.connect(
        lambda camera: main_window.network_thread.send_bad_pixel_disable(camera)
    )
    advanced_tab.bad_pixel_calibrate.connect(
        lambda camera: main_window.network_thread.send_bad_pixel_calibrate(camera)
    )
    advanced_tab.bad_pixel_threshold_changed.connect(
        lambda camera, threshold: main_window.network_thread.send_bad_pixel_threshold(camera, threshold)
    )
    advanced_tab.bad_pixel_query_requested.connect(
        lambda camera: main_window.network_thread.query_bad_pixel_settings(camera)
    )

    # Video Source (2 signals - camera-aware)
    advanced_tab.video_source_changed.connect(
        lambda camera, source_id: main_window.network_thread.send_video_source(camera, source_id)
    )
    advanced_tab.video_source_query_requested.connect(
        lambda camera: main_window.network_thread.query_video_source(camera)
    )

    # WebRTC Overlay (3 signals - camera-aware)
    advanced_tab.webrtc_overlay_enabled.connect(
        lambda camera: main_window.network_thread.send_webrtc_overlay_enable(camera)
    )
    advanced_tab.webrtc_overlay_disabled.connect(
        lambda camera: main_window.network_thread.send_webrtc_overlay_disable(camera)
    )
    advanced_tab.webrtc_overlay_query_requested.connect(
        lambda camera: main_window.network_thread.query_webrtc_overlay_settings(camera)
    )

    # External UP Forwarding (5 signals)
    advanced_tab.external_up_enabled.connect(
        lambda: main_window.network_thread.send_external_up_enable()
    )
    advanced_tab.external_up_disabled.connect(
        lambda: main_window.network_thread.send_external_up_disable()
    )
    advanced_tab.external_up_port_changed.connect(
        lambda port: main_window.network_thread.send_external_up_port(port)
    )
    advanced_tab.external_up_address_changed.connect(
        lambda address: main_window.network_thread.send_external_up_address(address)
    )
    advanced_tab.external_up_query_requested.connect(
        lambda: main_window.network_thread.query_external_up_settings()
    )

    # Pelco-D Forwarding (5 signals)
    advanced_tab.pelco_d_enabled.connect(
        lambda: main_window.network_thread.send_pelco_d_enable()
    )
    advanced_tab.pelco_d_disabled.connect(
        lambda: main_window.network_thread.send_pelco_d_disable()
    )
    advanced_tab.pelco_d_port_changed.connect(
        lambda port: main_window.network_thread.send_pelco_d_port(port)
    )
    advanced_tab.pelco_d_address_changed.connect(
        lambda address: main_window.network_thread.send_pelco_d_address(address)
    )
    advanced_tab.pelco_d_query_requested.connect(
        lambda: main_window.network_thread.query_pelco_d_settings()
    )

    # ========================================================================
    # SUB-PAYLOADS TAB SIGNAL CONNECTIONS (22 signals)
    # ========================================================================

    logger.info("Connecting Sub-Payloads tab signals")

    # Laser Rangefinder (4 signals)
    sub_payloads_tab.lrf_fire_requested.connect(
        lambda: main_window.network_thread.send_lrf_fire()
    )
    sub_payloads_tab.lrf_mode_changed.connect(
        lambda mode: main_window.network_thread.send_lrf_mode(mode)
    )
    sub_payloads_tab.lrf_query_range_requested.connect(
        lambda: main_window.network_thread.query_lrf_range()
    )
    sub_payloads_tab.lrf_query_settings_requested.connect(
        lambda: main_window.network_thread.query_lrf_settings()
    )

    # Speaker (4 signals)
    sub_payloads_tab.speaker_play_requested.connect(
        lambda clip_name: main_window.network_thread.send_speaker_play(clip_name)
    )
    sub_payloads_tab.speaker_stop_requested.connect(
        lambda: main_window.network_thread.send_speaker_stop()
    )
    sub_payloads_tab.speaker_volume_changed.connect(
        lambda volume: main_window.network_thread.send_speaker_volume(volume)
    )
    sub_payloads_tab.speaker_query_requested.connect(
        lambda: main_window.network_thread.query_speaker_status()
    )

    # G5 Laser (4 signals)
    sub_payloads_tab.g5_laser_enabled.connect(
        lambda: main_window.network_thread.send_g5_laser_enable()
    )
    sub_payloads_tab.g5_laser_disabled.connect(
        lambda: main_window.network_thread.send_g5_laser_disable()
    )
    sub_payloads_tab.g5_laser_intensity_changed.connect(
        lambda intensity: main_window.network_thread.send_g5_laser_intensity(intensity)
    )
    sub_payloads_tab.g5_laser_query_requested.connect(
        lambda: main_window.network_thread.query_g5_laser_settings()
    )

    # PeakBeam (5 signals)
    sub_payloads_tab.peakbeam_enabled.connect(
        lambda: main_window.network_thread.send_peakbeam_enable()
    )
    sub_payloads_tab.peakbeam_disabled.connect(
        lambda: main_window.network_thread.send_peakbeam_disable()
    )
    sub_payloads_tab.peakbeam_intensity_changed.connect(
        lambda intensity: main_window.network_thread.send_peakbeam_intensity(intensity)
    )
    sub_payloads_tab.peakbeam_mode_changed.connect(
        lambda mode: main_window.network_thread.send_peakbeam_mode(mode)
    )
    sub_payloads_tab.peakbeam_query_requested.connect(
        lambda: main_window.network_thread.query_peakbeam_settings()
    )

    # Companion Board (6 signals)
    sub_payloads_tab.companion_command_sent.connect(
        lambda command: main_window.network_thread.send_companion_command(command)
    )
    sub_payloads_tab.companion_enabled.connect(
        lambda: main_window.network_thread.send_companion_enable()
    )
    sub_payloads_tab.companion_disabled.connect(
        lambda: main_window.network_thread.send_companion_disable()
    )
    sub_payloads_tab.companion_reset_requested.connect(
        lambda: main_window.network_thread.send_companion_reset()
    )
    sub_payloads_tab.companion_query_requested.connect(
        lambda: main_window.network_thread.query_companion_status()
    )

    main_window.show()

    logger.info("Application window displayed with tabbed interface")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
