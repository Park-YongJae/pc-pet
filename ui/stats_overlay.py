from __future__ import annotations
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget

_W = 160
_H = 60
_HIDE_DELAY = 3000  # 3초 후 자동 숨김


class StatsOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        flags = (Qt.WindowType.FramelessWindowHint |
                 Qt.WindowType.WindowStaysOnTopHint |
                 Qt.WindowType.Tool |
                 Qt.WindowType.WindowTransparentForInput)
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(_W, _H)

        self._hunger = 100
        self._stress = 0

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(_HIDE_DELAY)
        self._hide_timer.timeout.connect(self.hide)

    def show_near(self, pet_x: int, pet_y: int, pet_w: int,
                  hunger: int, stress: int,
                  bubble_visible: bool = False) -> None:
        self._hunger = hunger
        self._stress = stress

        if bubble_visible:
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().availableGeometry()
            x = pet_x + pet_w + 8
            if x + _W > screen.right():
                x = pet_x - _W - 8
            self.move(x, pet_y)
        else:
            self.move(pet_x, pet_y - _H - 4)

        self.update()
        self.show()
        self._hide_timer.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 반투명 배경
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(30, 30, 30, 200)))
        painter.drawRoundedRect(0, 0, _W, _H, 8, 8)

        font = QFont("맑은 고딕", 9)
        painter.setFont(font)

        self._draw_bar(painter, y=10,
                       label="배고픔",
                       value=self._hunger,
                       fill_color=QColor("#FF8C00"),
                       low_color=QColor("#CC3300"))
        self._draw_bar(painter, y=35,
                       label="스트레스",
                       value=self._stress,
                       fill_color=QColor("#4CAF50"),
                       low_color=QColor("#FF4444"),
                       invert=True)

    def _draw_bar(self, painter: QPainter, y: int,
                  label: str, value: int,
                  fill_color: QColor, low_color: QColor,
                  invert: bool = False) -> None:
        # 레이블 + 수치
        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.drawText(QRect(8, y, 70, 18), Qt.AlignmentFlag.AlignVCenter,
                         f"{label}: {value}")

        # 바 배경
        bar_x, bar_y = 84, y + 3
        bar_w, bar_h = 68, 12
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 4, 4)

        # 바 채우기
        fill_w = int(bar_w * value / 100)
        if fill_w > 0:
            # invert=True(스트레스): 값이 높을수록 위험색
            danger = value > 60 if invert else value < 30
            color = low_color if danger else fill_color
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 4, 4)
