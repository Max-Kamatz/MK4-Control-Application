from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
import cv2
import numpy as np
from utils.logger import setup_logger

logger = setup_logger()

class VideoStreamThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    status_changed = pyqtSignal(str)

    def __init__(self, rtsp_url: str):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.running = False
        self.cap = None
        self._url_changed = False

    def run(self):
        self.running = True
        reconnect_delay = 5

        while self.running:
            try:
                logger.info(f"Connecting to RTSP stream: {self.rtsp_url}")
                self.status_changed.emit("connecting")

                # Set timeout environment variable for OpenCV (in milliseconds)
                import os
                os.environ['OPENCV_FFMPEG_READ_ATTEMPTS'] = '1'
                os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp|timeout;5000000'

                self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                # Set short timeout for connection
                self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
                self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)

                if not self.cap.isOpened():
                    logger.warning(f"Failed to open RTSP stream: {self.rtsp_url}")
                    self.status_changed.emit("disconnected")
                    self.msleep(reconnect_delay * 1000)
                    continue

                self.status_changed.emit("connected")
                logger.info(f"Successfully connected to: {self.rtsp_url}")

                while self.running and not self._url_changed:
                    ret, frame = self.cap.read()
                    if not ret:
                        logger.warning("Failed to read frame, reconnecting...")
                        self.status_changed.emit("buffering")
                        break

                    self.frame_ready.emit(frame)
                    self.msleep(33)

                # If URL changed, break out to reconnect with new URL
                if self._url_changed:
                    logger.info(f"URL changed, reconnecting to: {self.rtsp_url}")
                    self._url_changed = False

            except Exception as e:
                logger.error(f"Error in video stream: {e}")
                self.status_changed.emit("error")

            finally:
                if self.cap:
                    self.cap.release()

            if self.running:
                self.msleep(reconnect_delay * 1000)

    def change_url(self, new_url: str):
        """Change the RTSP URL and trigger reconnection."""
        if self.rtsp_url != new_url:
            self.rtsp_url = new_url
            self._url_changed = True
            # Release current capture to force reconnect with new URL
            if self.cap:
                self.cap.release()

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.quit()
        # Don't wait() here - it blocks the caller. Let it finish asynchronously.


class RTSPVideoWidget(QWidget):
    # Signal emitted when connection status changes
    status_changed = pyqtSignal(str)  # Emits status string: 'connected', 'disconnected', etc.

    def __init__(self, rtsp_url: str, label: str, auto_start: bool = True):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.label_text = label
        self.init_ui()
        if auto_start:
            self.start_stream()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        self.title_label = QLabel(self.label_text)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12pt; padding: 5px;")

        self.video_label = QLabel("Connecting to stream...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: #1a1a1a; border: 1px solid #444;")
        self.video_label.setMinimumSize(640, 480)

        self.status_label = QLabel("● Disconnected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #ff4444; font-size: 10pt;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.video_label)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def start_stream(self):
        self.stream_thread = VideoStreamThread(self.rtsp_url)
        self.stream_thread.frame_ready.connect(self.update_frame)
        self.stream_thread.status_changed.connect(self.update_status)
        self.stream_thread.start()

    def update_frame(self, frame: np.ndarray):
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

            label_size = self.video_label.size()
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.video_label.setPixmap(scaled_pixmap)

        except Exception as e:
            logger.error(f"Error updating frame: {e}")

    def update_status(self, status: str):
        status_map = {
            "connected": ("● Connected", "#44ff44"),
            "connecting": ("● Connecting...", "#ffff44"),
            "buffering": ("● Buffering...", "#ffaa44"),
            "disconnected": ("● Disconnected", "#ff4444"),
            "error": ("● Error", "#ff0000"),
            "unavailable": ("● Camera Not Available", "#888888")
        }

        text, color = status_map.get(status, ("● Unknown", "#888888"))
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 10pt;")

        # Emit status change signal for external monitoring
        self.status_changed.emit(status)

    def set_unavailable(self):
        """Mark this camera as unavailable (not connected to payload)."""
        self.video_label.setText("Camera Not Available\n\nThis camera is not connected to the payload.")
        self.update_status("unavailable")

    def closeEvent(self, event):
        """
        Clean up on close.

        NOTE: Do NOT call wait() - thread may be blocked in OpenCV operations.
        Let it terminate asynchronously.
        """
        if hasattr(self, 'stream_thread') and self.stream_thread:
            if self.stream_thread.isRunning():
                try:
                    # Disconnect signals to prevent crashes
                    self.stream_thread.frame_ready.disconnect()
                    self.stream_thread.status_changed.disconnect()
                except:
                    pass  # Already disconnected

                # Stop thread (non-blocking)
                self.stream_thread.stop()
                logger.info(f"Video stream thread stop signal sent for {self.label_text}")

        event.accept()
