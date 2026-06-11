from PyQt6.QtWidgets import QWidget, QGridLayout
from gui.widgets.rtsp_video_widget import RTSPVideoWidget
from utils.constants import load_config
from utils.logger import setup_logger

logger = setup_logger()

class VideoTab(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()
        layout.setSpacing(10)

        thermal_config = self.config['rtsp_streams']['thermal']
        self.thermal_widget = RTSPVideoWidget(
            thermal_config['url'],
            thermal_config['label']
        )

        daylight_config = self.config['rtsp_streams']['daylight']
        self.daylight_widget = RTSPVideoWidget(
            daylight_config['url'],
            daylight_config['label']
        )

        swir_config = self.config['rtsp_streams']['swir']
        self.swir_widget = RTSPVideoWidget(
            swir_config['url'],
            swir_config['label']
        )

        layout.addWidget(self.thermal_widget, 0, 0)
        layout.addWidget(self.daylight_widget, 0, 1)
        layout.addWidget(self.swir_widget, 1, 0)

        self.setLayout(layout)
        logger.info("Video tab initialized with 3 RTSP streams")

    def closeEvent(self, event):
        self.thermal_widget.stream_thread.stop()
        self.daylight_widget.stream_thread.stop()
        self.swir_widget.stream_thread.stop()
        event.accept()
