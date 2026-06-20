from __future__ import annotations
from PySide6.QtCore import Qt, QRect, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QBrush
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

_MAX_CONTENT_W = 280
_PAD = 12
_CLOSE_W = 22
_RADIUS = 12
_TAIL_H = 14
_TYPING_MS = 30
_AUTO_CLOSE_MS = 10_000

_FONT = QFont("맑은 고딕", 10)


def _calc_bubble_size(text: str) -> tuple[int, int]:
    """텍스트에 맞는 (content_w, content_h) 반환 (꼬리 제외)."""
    fm = QFontMetrics(_FONT)
    avail_w = _MAX_CONTENT_W - _PAD * 2 - _CLOSE_W
    rect = fm.boundingRect(QRect(0, 0, avail_w, 10000),
                           Qt.TextFlag.TextWordWrap, text)
    content_w = max(rect.width() + _PAD * 2 + _CLOSE_W + 4, 80)
    content_h = max(rect.height() + _PAD * 2, 40)
    return content_w, content_h


class SpeechBubble(QWidget):
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        flags = (Qt.WindowType.FramelessWindowHint |
                 Qt.WindowType.WindowStaysOnTopHint |
                 Qt.WindowType.Tool)
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._full_text = ""
        self._display_count = 0
        self._tail_above = False
        self._content_w = 120
        self._content_h = 40

        self._close_btn = QPushButton("✕", self)
        self._close_btn.setFixedSize(18, 18)
        self._close_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; "
            "color: #888; font-size: 11px; }"
            "QPushButton:hover { color: #333; }"
        )
        self._close_btn.clicked.connect(self._on_close)

        self._label = QLabel(self)
        self._label.setWordWrap(True)
        self._label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._label.setFont(_FONT)
        self._label.setStyleSheet("color: #222; background: transparent;")

        self._typing_timer = QTimer(self)
        self._typing_timer.setInterval(_TYPING_MS)
        self._typing_timer.timeout.connect(self._on_typing_tick)

        self._auto_close_timer = QTimer(self)
        self._auto_close_timer.setSingleShot(True)
        self._auto_close_timer.setInterval(_AUTO_CLOSE_MS)
        self._auto_close_timer.timeout.connect(self._on_close)

    def show_text(self, text: str, pet_rect: QRect) -> None:
        self._typing_timer.stop()
        self._auto_close_timer.stop()
        self._full_text = text
        self._display_count = 0
        self._resize_for_text(text)
        self._position_near_pet(pet_rect)
        self._layout_children()
        self._label.setText("")
        self.show()
        self._typing_timer.start()

    def show_typing(self, pet_rect: QRect) -> None:
        self._typing_timer.stop()
        self._auto_close_timer.stop()
        self._full_text = ""
        self._display_count = 0
        self._resize_for_text("...")
        self._position_near_pet(pet_rect)
        self._layout_children()
        self._label.setText("...")
        self.show()

    def update_position(self, pet_rect: QRect) -> None:
        if self.isVisible():
            self._position_near_pet(pet_rect)

    # ── Internal ──────────────────────────────────────────────────────

    def _resize_for_text(self, text: str) -> None:
        self._content_w, self._content_h = _calc_bubble_size(text)
        total_h = self._content_h + _TAIL_H
        self.setFixedSize(self._content_w, total_h)

    def _layout_children(self) -> None:
        label_y = (_TAIL_H + _PAD) if self._tail_above else _PAD
        close_y = (_TAIL_H + _PAD // 2) if self._tail_above else (_PAD // 2)
        label_w = self._content_w - _PAD * 2 - _CLOSE_W
        label_h = self._content_h - _PAD * 2
        self._label.setGeometry(_PAD, label_y, label_w, label_h)
        self._close_btn.move(self._content_w - _CLOSE_W - 2, close_y)

    def _position_near_pet(self, pet_rect: QRect) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        w = self._content_w
        h = self._content_h + _TAIL_H

        x = pet_rect.left()
        y = pet_rect.top() - h - 4

        if x + w > screen.right():
            x = pet_rect.right() - w
        x = max(screen.left(), x)

        self._tail_above = False
        if y < screen.top():
            y = pet_rect.bottom() + 4
            self._tail_above = True

        self.move(x, y)

    def _on_typing_tick(self) -> None:
        self._display_count += 1
        self._label.setText(self._full_text[:self._display_count])
        if self._display_count >= len(self._full_text):
            self._typing_timer.stop()
            self._auto_close_timer.start()

    def _on_close(self) -> None:
        self._typing_timer.stop()
        self._auto_close_timer.stop()
        self.hide()
        self.closed.emit()

    # ── Paint ─────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._tail_above:
            body_rect = QRect(0, _TAIL_H, self._content_w, self._content_h)
            tip_y, base_y = 0, _TAIL_H
        else:
            body_rect = QRect(0, 0, self._content_w, self._content_h)
            tip_y = self._content_h + _TAIL_H
            base_y = self._content_h

        path = QPainterPath()
        path.addRoundedRect(body_rect, _RADIUS, _RADIUS)

        tail_x = 24
        tail = QPainterPath()
        tail.moveTo(tail_x, base_y)
        tail.lineTo(tail_x + _TAIL_H, base_y)
        tail.lineTo(tail_x + _TAIL_H // 2, tip_y)
        tail.closeSubpath()
        path = path.united(tail)

        painter.setPen(QPen(QColor(0, 0, 0, 40), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 204)))
        painter.drawPath(path)
