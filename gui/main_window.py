from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QAction
from network.network_thread import NetworkThread
from gui.widgets.log_viewer import LogViewerDialog
from utils.logger import setup_logger
from utils.constants import load_config
import os

logger = setup_logger()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.network_thread = None
        self.log_viewer = None
        self.init_ui()
        self.apply_military_theme()

    def init_ui(self):
        self.setWindowTitle(self.config['ui']['window_title'])
        self.setGeometry(100, 100, 1400, 900)

        # Create menu bar
        menubar = self.menuBar()

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        # View Logs action
        view_logs_action = QAction("View Logs", self)
        view_logs_action.setShortcut("Ctrl+L")
        view_logs_action.triggered.connect(self.show_log_viewer)
        tools_menu.addAction(view_logs_action)

        # Create tab widget for multiple tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.setCentralWidget(self.tab_widget)

        # Keep reference to central_widget for backwards compatibility
        self.central_widget = None

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Not Connected | Press Ctrl+L to view logs")

        logger.info("Main window initialized")

    def apply_military_theme(self):
        """Apply military/tactical theme from QSS file."""
        # Set palette for base colors
        military_palette = QPalette()
        military_palette.setColor(QPalette.ColorRole.Window, QColor(26, 29, 36))  # #1a1d24
        military_palette.setColor(QPalette.ColorRole.WindowText, QColor(232, 232, 232))  # #e8e8e8
        military_palette.setColor(QPalette.ColorRole.Base, QColor(15, 18, 24))  # #0f1218
        military_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(37, 40, 49))  # #252831
        military_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(30, 34, 41))  # #1e2229
        military_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(232, 232, 232))  # #e8e8e8
        military_palette.setColor(QPalette.ColorRole.Text, QColor(232, 232, 232))  # #e8e8e8
        military_palette.setColor(QPalette.ColorRole.Button, QColor(37, 45, 56))  # #252d38
        military_palette.setColor(QPalette.ColorRole.ButtonText, QColor(232, 232, 232))  # #e8e8e8
        military_palette.setColor(QPalette.ColorRole.BrightText, QColor(196, 90, 90))  # #c45a5a
        military_palette.setColor(QPalette.ColorRole.Link, QColor(74, 103, 65))  # #4a6741
        military_palette.setColor(QPalette.ColorRole.Highlight, QColor(74, 103, 65))  # #4a6741
        military_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(232, 232, 232))  # #e8e8e8

        self.setPalette(military_palette)

        # Load QSS stylesheet
        qss_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gui', 'styles', 'military_theme.qss')
        try:
            with open(qss_path, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
                logger.info("Military theme applied successfully")
        except FileNotFoundError:
            logger.error(f"Military theme file not found: {qss_path}")
            # Fallback to basic styling
            self.setStyleSheet("""
                QMainWindow { background-color: #1a1d24; }
                QTabWidget::pane { border: 1px solid #3a4556; background: #1e2229; }
                QTabBar::tab { background: #252d38; color: #e8e8e8; padding: 8px 20px; margin-right: 2px; }
                QTabBar::tab:selected { background: #4a6741; }
                QTabBar::tab:hover { background: #354a5f; }
                QStatusBar { background: #0f1218; color: #e8e8e8; }
            """)

    def set_central_content(self, widget: QWidget):
        """Set the main content widget (no tabs). Kept for backwards compatibility."""
        self.central_widget = widget
        self.setCentralWidget(widget)

    def add_tab(self, widget: QWidget, label: str):
        """Add a tab to the tab widget."""
        self.tab_widget.addTab(widget, label)
        logger.info(f"Added tab: {label}")

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

    def show_log_viewer(self):
        """Show the real-time log viewer dialog."""
        if self.log_viewer is None or not self.log_viewer.isVisible():
            self.log_viewer = LogViewerDialog(self)
            self.log_viewer.show()
            logger.info("Log viewer opened")
        else:
            self.log_viewer.raise_()
            self.log_viewer.activateWindow()

    def closeEvent(self, event):
        logger.info("Application closing")
        if self.network_thread:
            self.network_thread.stop()
        if self.log_viewer:
            self.log_viewer.close()
        event.accept()
