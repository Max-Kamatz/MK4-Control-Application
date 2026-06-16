"""
gui/widgets/log_viewer.py
Real-time log viewer window for debugging and monitoring application events.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton,
                             QHBoxLayout, QLabel, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QTextCursor, QFont
import logging


class LogSignaler(QObject):
    """Qt signaler for log messages (needed for thread-safe logging from non-GUI threads)."""
    log_message = pyqtSignal(str, str)  # (level, message)


class QtLogHandler(logging.Handler):
    """Custom logging handler that emits Qt signals for real-time log display."""

    def __init__(self):
        super().__init__()
        self.signaler = LogSignaler()

    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname
            self.signaler.log_message.emit(level, msg)
        except Exception:
            self.handleError(record)


class LogViewerDialog(QDialog):
    """
    Real-time log viewer dialog window.
    Displays application logs with color coding by severity level.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MK4 Control - Live Logs")
        self.resize(1000, 600)
        self.auto_scroll = True
        self.init_ui()
        self.setup_logging()

    def init_ui(self):
        layout = QVBoxLayout()

        # Header with controls
        header_layout = QHBoxLayout()

        title = QLabel("<b>📋 Live Application Logs</b>")
        title.setStyleSheet("font-size: 14pt; padding: 5px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Auto-scroll checkbox
        self.autoscroll_checkbox = QCheckBox("Auto-scroll")
        self.autoscroll_checkbox.setChecked(True)
        self.autoscroll_checkbox.stateChanged.connect(self.toggle_autoscroll)
        header_layout.addWidget(self.autoscroll_checkbox)

        # Clear button
        clear_button = QPushButton("Clear Logs")
        clear_button.clicked.connect(self.clear_logs)
        header_layout.addWidget(clear_button)

        layout.addLayout(header_layout)

        # Log text display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        # Monospace font for better readability
        font = QFont("Consolas", 9)
        if not font.exactMatch():
            font = QFont("Courier New", 9)
        self.log_text.setFont(font)

        # Dark background for logs
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #444;
            }
        """)

        layout.addWidget(self.log_text)

        # Status bar
        self.status_label = QLabel("Logs: 0 lines")
        self.status_label.setStyleSheet("color: #888; font-size: 9pt; padding: 3px;")
        layout.addWidget(self.status_label)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        close_button.setMinimumWidth(100)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.line_count = 0

    def setup_logging(self):
        """Set up the Qt log handler and connect it to this viewer."""
        self.log_handler = QtLogHandler()

        # Format logs with timestamp and level
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)-8s] %(name)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.log_handler.setFormatter(formatter)
        self.log_handler.setLevel(logging.DEBUG)

        # Connect the signal
        self.log_handler.signaler.log_message.connect(self.append_log)

        # Add handler to root logger
        logging.getLogger().addHandler(self.log_handler)

    def append_log(self, level: str, message: str):
        """Append a log message with appropriate color coding."""
        # Color coding by log level
        color_map = {
            'DEBUG': '#888888',
            'INFO': '#4a9eff',
            'WARNING': '#ffaa00',
            'ERROR': '#ff4444',
            'CRITICAL': '#ff0000'
        }

        color = color_map.get(level, '#e0e0e0')

        # Format with HTML for color
        html_message = f'<span style="color: {color};">{message}</span>'

        self.log_text.append(html_message)
        self.line_count += 1
        self.status_label.setText(f"Logs: {self.line_count} lines")

        # Auto-scroll to bottom
        if self.auto_scroll:
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)

    def toggle_autoscroll(self, state):
        """Toggle auto-scroll feature."""
        self.auto_scroll = (state == Qt.CheckState.Checked.value)

    def clear_logs(self):
        """Clear all displayed logs."""
        self.log_text.clear()
        self.line_count = 0
        self.status_label.setText(f"Logs: {self.line_count} lines")

    def closeEvent(self, event):
        """Clean up log handler when window is closed."""
        # Remove handler from logger
        logging.getLogger().removeHandler(self.log_handler)
        event.accept()
