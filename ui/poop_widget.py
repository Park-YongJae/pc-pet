from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath
from PySide6.QtWidgets import QWidget

_SIZE = 36


class PoopWidget(QWidget):
    clicked = Signal(int)  # idx

    def __init__(self, idx: int, x: int, y: int, parent=None):
        super().__init__(parent)
        self._idx = idx

        flags = (Qt.WindowType.FramelessWindowHint |
                 Qt.WindowType.WindowStaysOnTopHint |
                 Qt.WindowType.Tool)
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setFixedSize(_SIZE, _SIZE)
        self.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_poop(painter)

    def _draw_poop(self, painter: QPainter) -> None:
        cx, cy = _SIZE // 2, _SIZE // 2 + 2
        brown = QColor("#6B3A2A")
        light = QColor("#8B5A3A")

        painter.setPen(QPen(brown.darker(120), 1))

        # 아래 층 (가장 넓은 원)
        painter.setBrush(QBrush(brown))
        painter.drawEllipse(cx - 10, cy + 4, 20, 10)

        # 중간 층
        painter.setBrush(QBrush(brown))
        painter.drawEllipse(cx - 7, cy - 4, 14, 12)

        # 위 층 (가장 작은 원)
        painter.setBrush(QBrush(light))
        painter.drawEllipse(cx - 4, cy - 12, 8, 12)

        # 하이라이트
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#C0896A")))
        painter.drawEllipse(cx - 2, cy - 10, 3, 4)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._idx)
