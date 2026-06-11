from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
from network.network_thread import NetworkThread
from utils.logger import setup_logger
from utils.constants import load_config

logger = setup_logger()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.network_thread = None
        self.init_ui()
        self.apply_dark_theme()

    def init_ui(self):
        self.setWindowTitle(self.config['ui']['window_title'])
        self.setGeometry(100, 100, 1400, 900)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Not Connected")

        logger.info("Main window initialized")

    def apply_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

        self.setPalette(dark_palette)

        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                background: #353535;
            }
            QTabBar::tab {
                background: #353535;
                color: white;
                padding: 8px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #2a82da;
            }
            QTabBar::tab:hover {
                background: #454545;
            }
            QStatusBar {
                background: #252525;
                color: white;
            }
        """)

    def add_tab(self, widget: QWidget, label: str):
        self.tab_widget.addTab(widget, label)

    def update_status(self, message: str):
        self.status_bar.showMessage(message)

    def start_network_thread(self):
        if not self.network_thread:
            self.network_thread = NetworkThread()
            self.network_thread.connection_status_changed.connect(self.on_connection_status_changed)
            self.network_thread.command_sent.connect(self.on_command_sent)
            self.network_thread.error_occurred.connect(self.on_error)
            self.network_thread.start()
            logger.info("Network thread started")

    def on_connection_status_changed(self, connected: bool):
        if connected:
            self.update_status("Connected to MK4 System")
        else:
            self.update_status("Disconnected from MK4 System")

    def on_command_sent(self, command: str):
        self.update_status(f"Command sent: {command}")

    def on_error(self, error_msg: str):
        self.update_status(f"Error: {error_msg}")
        logger.error(error_msg)

    def closeEvent(self, event):
        logger.info("Application closing")
        if self.network_thread:
            self.network_thread.stop()
        event.accept()
