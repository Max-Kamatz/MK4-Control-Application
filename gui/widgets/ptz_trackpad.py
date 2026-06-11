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

        # Zoom In button (top)
        self.btn_zoom_in = QPushButton("🔍+ Zoom In")
        self.btn_zoom_in.setStyleSheet("""
            QPushButton {
                background-color: #1a2035;
                padding: 8px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a3055;
            }
            QPushButton:pressed {
                background-color: #2a82da;
            }
        """)
        self.btn_zoom_in.pressed.connect(lambda: self.zoom_pressed.emit(1))
        self.btn_zoom_in.released.connect(self.zoom_released.emit)
        main_layout.addWidget(self.btn_zoom_in)

        # Middle row: Focus Far + Trackpad + Focus Near
        middle_row = QHBoxLayout()
        middle_row.setSpacing(10)

        self.btn_focus_far = QPushButton("🎯\nFar")
        self.btn_focus_far.setFixedSize(60, 80)
        self.btn_focus_far.setStyleSheet("""
            QPushButton {
                background-color: #1a2035;
                padding: 5px;
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a3055;
            }
            QPushButton:pressed {
                background-color: #2a82da;
            }
        """)
        self.btn_focus_far.pressed.connect(lambda: self.focus_pressed.emit(1))
        self.btn_focus_far.released.connect(self.focus_released.emit)

        self.trackpad = PTZTrackpad()
        self.trackpad.moved.connect(self.pan_tilt_moved.emit)
        self.trackpad.released.connect(self.pan_tilt_released.emit)

        self.btn_focus_near = QPushButton("🎯\nNear")
        self.btn_focus_near.setFixedSize(60, 80)
        self.btn_focus_near.setStyleSheet("""
            QPushButton {
                background-color: #1a2035;
                padding: 5px;
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a3055;
            }
            QPushButton:pressed {
                background-color: #2a82da;
            }
        """)
        self.btn_focus_near.pressed.connect(lambda: self.focus_pressed.emit(-1))
        self.btn_focus_near.released.connect(self.focus_released.emit)

        middle_row.addWidget(self.btn_focus_far)
        middle_row.addWidget(self.trackpad)
        middle_row.addWidget(self.btn_focus_near)

        main_layout.addLayout(middle_row)

        # Zoom Out button (bottom)
        self.btn_zoom_out = QPushButton("🔍- Zoom Out")
        self.btn_zoom_out.setStyleSheet("""
            QPushButton {
                background-color: #1a2035;
                padding: 8px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a3055;
            }
            QPushButton:pressed {
                background-color: #2a82da;
            }
        """)
        self.btn_zoom_out.pressed.connect(lambda: self.zoom_pressed.emit(-1))
        self.btn_zoom_out.released.connect(self.zoom_released.emit)
        main_layout.addWidget(self.btn_zoom_out)

        # Instructions
        instructions = QLabel("Drag on trackpad for pan/tilt\nHold buttons for zoom/focus")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("font-size: 8pt; color: #888; padding: 5px;")
        main_layout.addWidget(instructions)

        self.setLayout(main_layout)
