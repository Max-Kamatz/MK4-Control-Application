"""
gui/widgets/ptz_trackpad.py
Circular PTZ trackpad widget with surrounding zoom/focus buttons.
Based on onvif-pelco-tool design.
"""

import math
from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
from utils.logger import setup_logger

logger = setup_logger()


class PTZTrackpad(QWidget):
    """
    Circular drag-pad for pan/tilt control.

    Signals:
        moved(pan, tilt)  — normalized [-1.0, 1.0] on each mouse move
        released()        — on mouse button release
    """

    moved = pyqtSignal(float, float)
    released = pyqtSignal()

    # Geometry
    RADIUS = 80     # px from centre to edge
    PAD = 15        # px border padding around circle
    DOT_R = 8       # drag indicator dot radius
    DEAD = 0.04     # normalized dead zone radius

    def __init__(self, parent=None):
        super().__init__(parent)
        size = (self.RADIUS + self.PAD) * 2
        self.setFixedSize(size, size)
        cx = cy = size // 2
        self._centre = QPoint(cx, cy)
        self._dot = QPointF(cx, cy)
        self._active = False

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self._centre.x()
        cy = self._centre.y()
        r = self.RADIUS

        # Background circle
        p.setPen(QPen(QColor("#2a82da"), 3))
        p.setBrush(QBrush(QColor("#0a1428")))
        p.drawEllipse(self._centre, r, r)

        # Crosshair
        crosshair_pen = QPen(QColor("#2e5ac2"), 1, Qt.PenStyle.SolidLine)
        p.setPen(crosshair_pen)
        p.drawLine(cx - r + 6, cy, cx + r - 6, cy)
        p.drawLine(cx, cy - r + 6, cx, cy + r - 6)

        # Centre dot
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#2a82da")))
        p.drawEllipse(self._centre, 4, 4)

        # Drag indicator
        if self._active:
            p.setPen(QPen(QColor("#ffffff"), 2))
            p.setBrush(QBrush(QColor("#2a82da")))
            p.drawEllipse(self._dot, self.DOT_R, self.DOT_R)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._active = True
            self._process(event.position())

    def mouseMoveEvent(self, event):
        if self._active:
            self._process(event.position())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._active = False
            self._dot = QPointF(self._centre)
            self.update()
            self.released.emit()
            logger.debug("PTZ trackpad released")

    def _process(self, pos: QPointF):
        cx = self._centre.x()
        cy = self._centre.y()
        dx = pos.x() - cx
        dy = pos.y() - cy

        dist = math.hypot(dx, dy)

        # Clamp dot to circle edge
        if dist > self.RADIUS:
            scale = self.RADIUS / dist
            dx *= scale
            dy *= scale
            dist = self.RADIUS

        self._dot = QPointF(cx + dx, cy + dy)
        self.update()

        # Normalize to [-1.0, 1.0]; invert Y so up = positive tilt
        pan = dx / self.RADIUS
        tilt = -dy / self.RADIUS

        # Apply dead zone
        if abs(pan) < self.DEAD:
            pan = 0.0
        if abs(tilt) < self.DEAD:
            tilt = 0.0

        self.moved.emit(pan, tilt)


class PTZControlWidget(QWidget):
    """
    Complete PTZ control widget with trackpad and surrounding zoom/focus buttons.
    """

    pan_tilt_moved = pyqtSignal(float, float)
    pan_tilt_released = pyqtSignal()
    zoom_pressed = pyqtSignal(int)      # +1 for in, -1 for out
    zoom_released = pyqtSignal()
    focus_pressed = pyqtSignal(int)     # +1 for far, -1 for near
    focus_released = pyqtSignal()

    # Directional arrow signals (use slider speeds)
    arrow_up_pressed = pyqtSignal()
    arrow_down_pressed = pyqtSignal()
    arrow_left_pressed = pyqtSignal()
    arrow_right_pressed = pyqtSignal()
    arrow_released = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)

        # Title
        title = QLabel("<b>PTZ Control</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 12pt; padding: 5px;")
        main_layout.addWidget(title)

        # Top row: Zoom buttons in corners
        top_row = QHBoxLayout()
        top_row.setSpacing(5)

        # Zoom Out button (top left)
        self.btn_zoom_out = QPushButton("Z-")
        self.btn_zoom_out.setFixedSize(50, 40)
        self.btn_zoom_out.setStyleSheet("""
            QPushButton {
                background-color: #252d38;
                color: #e8e8e8;
                padding: 5px;
                font-size: 12pt;
                font-weight: bold;
                border: 1px solid #3a4556;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #354a5f;
                border-color: #4a6741;
            }
            QPushButton:pressed {
                background-color: #4a6741;
                border-color: #6a9955;
            }
        """)
        self.btn_zoom_out.pressed.connect(lambda: self.zoom_pressed.emit(-1))
        self.btn_zoom_out.released.connect(self.zoom_released.emit)
        top_row.addWidget(self.btn_zoom_out)

        top_row.addStretch()

        # Zoom In button (top right)
        self.btn_zoom_in = QPushButton("Z+")
        self.btn_zoom_in.setFixedSize(50, 40)
        self.btn_zoom_in.setStyleSheet("""
            QPushButton {
                background-color: #252d38;
                color: #e8e8e8;
                padding: 5px;
                font-size: 12pt;
                font-weight: bold;
                border: 1px solid #3a4556;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #354a5f;
                border-color: #4a6741;
            }
            QPushButton:pressed {
                background-color: #4a6741;
                border-color: #6a9955;
            }
        """)
        self.btn_zoom_in.pressed.connect(lambda: self.zoom_pressed.emit(1))
        self.btn_zoom_in.released.connect(self.zoom_released.emit)
        top_row.addWidget(self.btn_zoom_in)

        main_layout.addLayout(top_row)

        # Middle section: Trackpad with directional arrows
        # Up arrow button (centered)
        up_layout = QHBoxLayout()
        up_layout.addStretch()
        self.btn_arrow_up = QPushButton("▲")
        self.btn_arrow_up.setFixedSize(40, 40)
        self.btn_arrow_up.setStyleSheet("""
            QPushButton {
                background-color: transparent !important;
                color: #4a6741 !important;
                font-size: 16pt !important;
                font-weight: bold !important;
                border: none !important;
                padding: 0px !important;
                text-align: center !important;
            }
            QPushButton:hover {
                color: #6a9955 !important;
            }
            QPushButton:pressed {
                color: #e8e8e8 !important;
            }
        """)
        self.btn_arrow_up.pressed.connect(self.arrow_up_pressed.emit)
        self.btn_arrow_up.released.connect(self.arrow_released.emit)
        up_layout.addWidget(self.btn_arrow_up)
        up_layout.addStretch()
        main_layout.addLayout(up_layout)

        # Center row: left arrow + trackpad + right arrow
        center_row = QHBoxLayout()
        center_row.setContentsMargins(0, 0, 0, 0)
        center_row.addStretch()

        self.btn_arrow_left = QPushButton("◀")
        self.btn_arrow_left.setFixedSize(40, 40)
        self.btn_arrow_left.setStyleSheet("""
            QPushButton {
                background-color: transparent !important;
                color: #4a6741 !important;
                font-size: 20pt !important;
                font-weight: bold !important;
                border: none !important;
                padding: 0px !important;
                text-align: center !important;
            }
            QPushButton:hover {
                color: #6a9955 !important;
            }
            QPushButton:pressed {
                color: #e8e8e8 !important;
            }
        """)
        self.btn_arrow_left.pressed.connect(self.arrow_left_pressed.emit)
        self.btn_arrow_left.released.connect(self.arrow_released.emit)
        center_row.addWidget(self.btn_arrow_left)

        center_row.addSpacing(10)

        self.trackpad = PTZTrackpad()
        self.trackpad.moved.connect(self.pan_tilt_moved.emit)
        self.trackpad.released.connect(self.pan_tilt_released.emit)
        center_row.addWidget(self.trackpad)

        center_row.addSpacing(10)

        self.btn_arrow_right = QPushButton("▶")
        self.btn_arrow_right.setFixedSize(40, 40)
        self.btn_arrow_right.setStyleSheet("""
            QPushButton {
                background-color: transparent !important;
                color: #4a6741 !important;
                font-size: 20pt !important;
                font-weight: bold !important;
                border: none !important;
                padding: 0px !important;
                text-align: center !important;
            }
            QPushButton:hover {
                color: #6a9955 !important;
            }
            QPushButton:pressed {
                color: #e8e8e8 !important;
            }
        """)
        self.btn_arrow_right.pressed.connect(self.arrow_right_pressed.emit)
        self.btn_arrow_right.released.connect(self.arrow_released.emit)
        center_row.addWidget(self.btn_arrow_right)

        center_row.addStretch()
        main_layout.addLayout(center_row)

        # Down arrow button (centered)
        down_layout = QHBoxLayout()
        down_layout.addStretch()
        self.btn_arrow_down = QPushButton("▼")
        self.btn_arrow_down.setFixedSize(40, 40)
        self.btn_arrow_down.setStyleSheet("""
            QPushButton {
                background-color: transparent !important;
                color: #4a6741 !important;
                font-size: 16pt !important;
                font-weight: bold !important;
                border: none !important;
                padding: 0px !important;
                text-align: center !important;
            }
            QPushButton:hover {
                color: #6a9955 !important;
            }
            QPushButton:pressed {
                color: #e8e8e8 !important;
            }
        """)
        self.btn_arrow_down.pressed.connect(self.arrow_down_pressed.emit)
        self.btn_arrow_down.released.connect(self.arrow_released.emit)
        down_layout.addWidget(self.btn_arrow_down)
        down_layout.addStretch()
        main_layout.addLayout(down_layout)

        # Bottom row: Focus buttons in corners
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(5)

        # Focus Near button (bottom left)
        self.btn_focus_near = QPushButton("F-")
        self.btn_focus_near.setFixedSize(50, 40)
        self.btn_focus_near.setStyleSheet("""
            QPushButton {
                background-color: #252d38;
                color: #e8e8e8;
                padding: 5px;
                font-size: 12pt;
                font-weight: bold;
                border: 1px solid #3a4556;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #354a5f;
                border-color: #4a6741;
            }
            QPushButton:pressed {
                background-color: #4a6741;
                border-color: #6a9955;
            }
        """)
        self.btn_focus_near.pressed.connect(lambda: self.focus_pressed.emit(-1))
        self.btn_focus_near.released.connect(self.focus_released.emit)
        bottom_row.addWidget(self.btn_focus_near)

        bottom_row.addStretch()

        # Focus Far button (bottom right)
        self.btn_focus_far = QPushButton("F+")
        self.btn_focus_far.setFixedSize(50, 40)
        self.btn_focus_far.setStyleSheet("""
            QPushButton {
                background-color: #252d38;
                color: #e8e8e8;
                padding: 5px;
                font-size: 12pt;
                font-weight: bold;
                border: 1px solid #3a4556;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #354a5f;
                border-color: #4a6741;
            }
            QPushButton:pressed {
                background-color: #4a6741;
                border-color: #6a9955;
            }
        """)
        self.btn_focus_far.pressed.connect(lambda: self.focus_pressed.emit(1))
        self.btn_focus_far.released.connect(self.focus_released.emit)
        bottom_row.addWidget(self.btn_focus_far)

        main_layout.addLayout(bottom_row)

        # Instructions
        instructions = QLabel("Drag trackpad for pan/tilt • Arrows for discrete moves")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("font-size: 8pt; color: #888; padding: 5px;")
        main_layout.addWidget(instructions)

        self.setLayout(main_layout)
