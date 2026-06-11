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

    def run(self):
        self.running = True
        reconnect_delay = 5

        while self.running:
            try:
                logger.info(f"Connecting to RTSP stream: {self.rtsp_url}")
                self.status_changed.emit("connecting")

                self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                if not self.cap.isOpened():
                    logger.warning(f"Failed to open RTSP stream: {self.rtsp_url}")
                    self.status_changed.emit("disconnected")
                    self.msleep(reconnect_delay * 1000)
                    continue

                self.status_changed.emit("connected")
                logger.info(f"Successfully connected to: {self.rtsp_url}")

                while self.running:
                    ret, frame = self.cap.read()
                    if not ret:
                        logger.warning("Failed to read frame, reconnecting...")
                        self.status_changed.emit("buffering")
                        break

                    self.frame_ready.emit(frame)
                    self.msleep(33)

            except Exception as e:
                logger.error(f"Error in video stream: {e}")
                self.status_changed.emit("error")

            finally:
                if self.cap:
                    self.cap.release()

            if self.running:
                self.msleep(reconnect_delay * 1000)

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.quit()
        self.wait()


class RTSPVideoWidget(QWidget):
    def __init__(self, rtsp_url: str, label: str):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.label_text = label
        self.init_ui()
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
            "error": ("● Error", "#ff0000")
        }

        text, color = status_map.get(status, ("● Unknown", "#888888"))
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 10pt;")

    def closeEvent(self, event):
        if hasattr(self, 'stream_thread'):
            self.stream_thread.stop()
        event.accept()
