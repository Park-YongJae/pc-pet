from __future__ import annotations
import os
import sys
import random
import math
from enum import Enum, auto

from PySide6.QtCore import (
    Qt, QTimer, QRect, QPoint, QPropertyAnimation,
    QEasingCurve, Signal, Property
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QImage, QPainterPath, QPixmap
)
from PySide6.QtWidgets import QWidget


if getattr(sys, 'frozen', False):
    _SPRITE_DIR = os.path.join(sys._MEIPASS, 'assets', 'sprites')
else:
    _SPRITE_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sprites')

_SPRITE_FRAMES = {
    'breathing': 2,
    'walking':   3,
    'eating':    2,
}

_SPRITE_INTERVALS = {
    'breathing': 500,
    'walking':   150,
    'eating':    200,
}


class PetVisualState(Enum):
    EGG = auto()
    HATCHING = auto()
    IDLE = auto()
    WALKING = auto()
    HUNGRY = auto()
    REACT_HAPPY = auto()
    REACT_ANNOYED = auto()
    REACT_ANGRY = auto()
    EATING = auto()
    DEAD = auto()
    THINKING = auto()
    TALKING = auto()


_STATE_TO_SPRITE_KEY = {
    PetVisualState.IDLE:          'breathing',
    PetVisualState.WALKING:       'walking',
    PetVisualState.HUNGRY:        'breathing',
    PetVisualState.REACT_HAPPY:   'happy',
    PetVisualState.REACT_ANNOYED: 'annoyed',
    PetVisualState.REACT_ANGRY:   'angry',
    PetVisualState.EATING:        'eating',
    PetVisualState.DEAD:          'dead',
    PetVisualState.THINKING:      'breathing',
    PetVisualState.TALKING:       'breathing',
}

_W = 120
_H = 140


class SpriteRenderer(QWidget):
    hatching_complete = Signal()
    egg_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(_W, _H)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._state = PetVisualState.EGG
        self._pet_type = 1
        self._facing_right = True
        self._blinking = False
        self._egg_opacity = 1.0
        self._wobble_angle_val = 0.0
        self._stress_level = 0
        self._dot_count = 0

        # sprite state
        self._sprite_frame = 0
        self._sprite_egg: QPixmap | None = None
        self._sprite_egg_cracked: QPixmap | None = None
        self._sprites: dict[str, QPixmap | None] = {}
        self._load_sprites()

        # sprite frame timer
        self._sprite_frame_timer = QTimer(self)
        self._sprite_frame_timer.timeout.connect(self._on_sprite_frame_tick)

        # crack lines for hatching
        self._cracks: list[tuple[int, int, int, int]] = []
        self._crack_timer = QTimer(self)
        self._crack_timer.setInterval(80)
        self._crack_timer.timeout.connect(self._add_crack)

        # blink timer
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._start_blink)

        self._blink_end_timer = QTimer(self)
        self._blink_end_timer.setSingleShot(True)
        self._blink_end_timer.setInterval(150)
        self._blink_end_timer.timeout.connect(self._end_blink)

        # thinking dots animation
        self._dot_timer = QTimer(self)
        self._dot_timer.setInterval(500)
        self._dot_timer.timeout.connect(self._on_dot_tick)

        # wobble animation (egg)
        self._wobble_anim = QPropertyAnimation(self, b"wobble_angle", self)
        self._wobble_anim.setDuration(1200)
        self._wobble_anim.setStartValue(-5.0)
        self._wobble_anim.setEndValue(5.0)
        self._wobble_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._wobble_anim.setLoopCount(-1)

        # fade animation (hatching phase B)
        self._fade_anim = QPropertyAnimation(self, b"egg_opacity", self)
        self._fade_anim.setDuration(400)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(self._on_fade_done)

        # start in EGG state
        self._wobble_anim.start()

    # --- Sprite loading ---

    def _load_sprites(self) -> None:
        self._sprite_egg = self._load_px('egg.png')
        self._sprite_egg_cracked = self._load_px('egg_cracked.png')
        n = self._pet_type
        for key in ('breathing', 'walking', 'eating', 'happy', 'annoyed', 'angry', 'dead'):
            self._sprites[key] = self._load_px(f'pet{n}_{key}.png')

    def _load_px(self, filename: str) -> 'QPixmap | None':
        path = os.path.join(_SPRITE_DIR, filename)
        if not os.path.exists(path):
            return None
        px = QPixmap(path)
        if px.isNull():
            return None
        px.setDevicePixelRatio(2.0)
        return px

    def _on_sprite_frame_tick(self) -> None:
        self._sprite_frame += 1
        self.update()

    # --- Qt Properties for animation ---

    def _get_wobble_angle(self) -> float:
        return self._wobble_angle_val

    def _set_wobble_angle(self, v: float) -> None:
        self._wobble_angle_val = v
        self.update()

    wobble_angle = Property(float, _get_wobble_angle, _set_wobble_angle)

    def _get_egg_opacity(self) -> float:
        return self._egg_opacity

    def _set_egg_opacity(self, v: float) -> None:
        self._egg_opacity = v
        self.update()

    egg_opacity = Property(float, _get_egg_opacity, _set_egg_opacity)

    # --- Public API ---

    def set_state(self, state: PetVisualState) -> None:
        self._stop_all()
        self._state = state
        self._cracks.clear()
        self._egg_opacity = 1.0
        self._sprite_frame = 0

        if state == PetVisualState.EGG:
            self._wobble_anim.start()
        elif state == PetVisualState.HATCHING:
            self._crack_timer.start()
            QTimer.singleShot(800, self._start_fade)
        elif state in (PetVisualState.IDLE, PetVisualState.WALKING,
                       PetVisualState.HUNGRY, PetVisualState.REACT_HAPPY,
                       PetVisualState.REACT_ANNOYED, PetVisualState.REACT_ANGRY,
                       PetVisualState.EATING):
            self._schedule_blink()
            self._start_sprite_anim(state)
        elif state == PetVisualState.THINKING:
            self._dot_count = 0
            self._dot_timer.start()
            self._schedule_blink()
            self._start_sprite_anim(state)
        elif state == PetVisualState.TALKING:
            self._schedule_blink()
            self._start_sprite_anim(state)

        self.update()

    def _start_sprite_anim(self, state: PetVisualState) -> None:
        key = _STATE_TO_SPRITE_KEY.get(state)
        if not key:
            return
        interval = _SPRITE_INTERVALS.get(key, 0)
        if interval > 0 and self._sprites.get(key):
            self._sprite_frame_timer.setInterval(interval)
            self._sprite_frame_timer.start()

    def set_pet_type(self, type_id: int) -> None:
        self._pet_type = type_id
        self._load_sprites()
        self.update()

    def set_facing(self, right: bool) -> None:
        if self._facing_right != right:
            self._facing_right = right
            self.update()

    def set_stress_level(self, level: int) -> None:
        if self._stress_level != level:
            self._stress_level = level
            self.update()

    def is_opaque_at(self, local_pos: QPoint) -> bool:
        img = QImage(self.size(), QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        painter = QPainter(img)
        self._draw(painter)
        painter.end()
        if (0 <= local_pos.x() < img.width() and
                0 <= local_pos.y() < img.height()):
            return (img.pixel(local_pos.x(), local_pos.y()) >> 24) > 10
        return False

    # --- Internal helpers ---

    def _stop_all(self) -> None:
        self._wobble_anim.stop()
        self._crack_timer.stop()
        self._fade_anim.stop()
        self._blink_timer.stop()
        self._blink_end_timer.stop()
        self._dot_timer.stop()
        self._sprite_frame_timer.stop()
        self._blinking = False

    def _add_crack(self) -> None:
        cx, cy = _W // 2, _H // 2 + 5
        angle = random.uniform(0, 2 * math.pi)
        length = random.randint(10, 25)
        ex = int(cx + math.cos(angle) * length)
        ey = int(cy + math.sin(angle) * length)
        self._cracks.append((cx + random.randint(-8, 8),
                              cy + random.randint(-8, 8), ex, ey))
        self.update()

    def _start_fade(self) -> None:
        self._crack_timer.stop()
        self._fade_anim.start()

    def _on_fade_done(self) -> None:
        self.hatching_complete.emit()

    def _schedule_blink(self) -> None:
        interval_ms = random.randint(3000, 6000)
        self._blink_timer.setInterval(interval_ms)
        self._blink_timer.setSingleShot(True)
        self._blink_timer.start()

    def _start_blink(self) -> None:
        self._blinking = True
        self.update()
        self._blink_end_timer.start()

    def _end_blink(self) -> None:
        self._blinking = False
        self.update()
        if self._state in (PetVisualState.IDLE, PetVisualState.WALKING,
                           PetVisualState.HUNGRY, PetVisualState.REACT_HAPPY,
                           PetVisualState.REACT_ANNOYED, PetVisualState.REACT_ANGRY,
                           PetVisualState.EATING, PetVisualState.THINKING,
                           PetVisualState.TALKING):
            self._schedule_blink()

    def _on_dot_tick(self) -> None:
        self._dot_count = (self._dot_count % 3) + 1
        self.update()

    # --- Paint ---

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw(painter)

    def _draw_sprite_frame(self, painter: QPainter, pixmap: QPixmap,
                           frame: int, frame_count: int) -> None:
        frame_phys_w = pixmap.width() // frame_count
        src = QRect(frame * frame_phys_w, 0, frame_phys_w, pixmap.height())
        dst = QRect(0, 0, _W, _H)
        painter.drawPixmap(dst, pixmap, src)

    def _draw(self, painter: QPainter) -> None:
        if self._state == PetVisualState.EGG:
            painter.save()
            painter.translate(_W / 2, _H / 2)
            painter.rotate(self._wobble_angle_val)
            painter.translate(-_W / 2, -_H / 2)
            if self._sprite_egg:
                self._draw_sprite_frame(painter, self._sprite_egg, 0, 1)
            else:
                self._draw_egg(painter)
            painter.restore()

        elif self._state == PetVisualState.HATCHING:
            painter.save()
            painter.setOpacity(self._egg_opacity)
            if self._sprite_egg_cracked:
                self._draw_sprite_frame(painter, self._sprite_egg_cracked, 0, 1)
            else:
                self._draw_hatching_shape(painter)
            painter.restore()

        elif self._state == PetVisualState.DEAD:
            sprite = self._sprites.get('dead')
            if sprite:
                self._draw_sprite_frame(painter, sprite, 0, 1)
            else:
                self._draw_dead(painter)

        else:
            key = _STATE_TO_SPRITE_KEY.get(self._state)
            sprite = self._sprites.get(key) if key else None

            if sprite:
                frame_count = _SPRITE_FRAMES.get(key, 1)
                frame = self._sprite_frame % frame_count
                painter.save()
                if not self._facing_right:
                    painter.translate(_W, 0)
                    painter.scale(-1, 1)
                self._draw_sprite_frame(painter, sprite, frame, frame_count)
                painter.restore()

                if self._state == PetVisualState.HUNGRY:
                    painter.setPen(QPen(QColor("#FFA500"), 3))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawEllipse(QPoint(_W // 2, _H // 2 + 10), 43, 43)
                if self._state == PetVisualState.THINKING:
                    self._draw_thinking_dots(painter)
                if self._stress_level >= 2:
                    self._draw_sweat(painter, _W // 2, _H // 2 + 10, 38)
            else:
                # QPainter fallback (스프라이트 없는 펫 타입)
                if self._state in (PetVisualState.IDLE, PetVisualState.WALKING,
                                   PetVisualState.HUNGRY, PetVisualState.REACT_HAPPY,
                                   PetVisualState.REACT_ANNOYED, PetVisualState.REACT_ANGRY,
                                   PetVisualState.EATING):
                    self._draw_pet(painter)
                elif self._state in (PetVisualState.THINKING, PetVisualState.TALKING):
                    self._draw_pet(painter)
                    if self._state == PetVisualState.THINKING:
                        self._draw_thinking_dots(painter)

    def _draw_egg(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#CCCCCC"), 2))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QRect(20, 15, 80, 100))

    def _draw_hatching_shape(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#CCCCCC"), 2))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QRect(20, 15, 80, 100))
        painter.setPen(QPen(QColor("#888888"), 1))
        for x1, y1, x2, y2 in self._cracks:
            painter.drawLine(x1, y1, x2, y2)

    def _draw_pet(self, painter: QPainter) -> None:
        """스프라이트 로드 실패 시 단순 도형 폴백."""
        if not self._facing_right:
            painter.translate(_W, 0)
            painter.scale(-1, 1)

        cx, cy = _W // 2, _H // 2 + 10
        body_r = 38

        painter.setPen(QPen(QColor("#00000033"), 1))
        painter.setBrush(QBrush(QColor("#AAAAAA")))
        painter.drawEllipse(QPoint(cx, cy), body_r, body_r)

        self._draw_eyes(painter, cx, cy, body_r)

        if self._state == PetVisualState.HUNGRY:
            painter.setPen(QPen(QColor("#FFA500"), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPoint(cx, cy), body_r + 5, body_r + 5)

        if self._stress_level >= 2:
            self._draw_sweat(painter, cx, cy, body_r)

    def _draw_ears(self, painter: QPainter, ear: str,
                   cx: int, cy: int, r: int, body_color: QColor) -> None:
        ear_color = body_color.darker(120)
        painter.setBrush(QBrush(ear_color))
        painter.setPen(Qt.PenStyle.NoPen)

        if ear == "triangle":
            for sign in (-1, 1):
                pts = [
                    QPoint(cx + sign * 18, cy - r + 5),
                    QPoint(cx + sign * 10, cy - r - 20),
                    QPoint(cx + sign * 30, cy - r - 15),
                ]
                from PySide6.QtGui import QPolygon
                painter.drawPolygon(QPolygon(pts))
        elif ear == "round":
            for sign in (-1, 1):
                painter.drawEllipse(QPoint(cx + sign * 28, cy - r + 2), 12, 12)
        elif ear == "droopy":
            painter.setBrush(QBrush(ear_color))
            for sign in (-1, 1):
                painter.drawEllipse(QRect(cx + sign * 18 - 10,
                                          cy - r + 5, 20, 30))
        elif ear == "long":
            for sign in (-1, 1):
                painter.drawRoundedRect(
                    QRect(cx + sign * 12, cy - r - 30, 14, 34), 6, 6)
        elif ear == "horn":
            painter.setBrush(QBrush(QColor("#FF4500")))
            for sign in (-1, 1):
                pts = [
                    QPoint(cx + sign * 14, cy - r + 5),
                    QPoint(cx + sign * 20, cy - r - 22),
                    QPoint(cx + sign * 26, cy - r + 5),
                ]
                from PySide6.QtGui import QPolygon
                painter.drawPolygon(QPolygon(pts))

    def _draw_eyes(self, painter: QPainter,
                   cx: int, cy: int, r: int) -> None:
        eye_y = cy - r // 3
        eye_offsets = (-12, 12)

        if self._blinking:
            painter.setPen(QPen(QColor("#333333"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for ox in eye_offsets:
                painter.drawLine(cx + ox - 5, eye_y, cx + ox + 5, eye_y)
        elif self._state == PetVisualState.REACT_HAPPY:
            painter.setPen(QPen(QColor("#333333"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for ox in eye_offsets:
                path = QPainterPath()
                path.moveTo(cx + ox - 5, eye_y + 2)
                path.quadTo(cx + ox, eye_y - 6, cx + ox + 5, eye_y + 2)
                painter.drawPath(path)
        elif self._state == PetVisualState.REACT_ANNOYED:
            painter.setPen(QPen(QColor("#333333"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for ox in eye_offsets:
                painter.drawArc(cx + ox - 5, eye_y - 3, 10, 8, 0, 180 * 16)
            painter.setPen(QPen(QColor("#333333"), 2))
            sign_map = [(-1, -12), (1, 12)]
            for sign, ox in sign_map:
                painter.drawLine(cx + ox - 5, eye_y - 8,
                                 cx + ox + 5 * sign, eye_y - 11)
        elif self._state == PetVisualState.REACT_ANGRY:
            painter.setPen(QPen(QColor("#CC2200"), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for ox in eye_offsets:
                painter.drawLine(cx + ox - 4, eye_y - 4, cx + ox + 4, eye_y + 4)
                painter.drawLine(cx + ox + 4, eye_y - 4, cx + ox - 4, eye_y + 4)
        elif self._state == PetVisualState.EATING:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#333333")))
            for ox in eye_offsets:
                painter.drawEllipse(QPoint(cx + ox, eye_y - 2), 4, 4)
            painter.setBrush(QBrush(QColor("#CC4444")))
            painter.drawEllipse(QPoint(cx, eye_y + r // 2), 8, 8)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#333333")))
            for ox in eye_offsets:
                painter.drawEllipse(QPoint(cx + ox, eye_y), 5, 5)
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            for ox in eye_offsets:
                painter.drawEllipse(QPoint(cx + ox + 2, eye_y - 2), 2, 2)

    def _draw_sweat(self, painter: QPainter,
                    cx: int, cy: int, r: int) -> None:
        count = 2 if self._stress_level == 2 else 3
        positions = [(cx + r + 2, cy - r // 2),
                     (cx - r - 8, cy - r // 3),
                     (cx + r - 4, cy + r // 4)]
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#88BBFF")))
        for i in range(count):
            x, y = positions[i]
            path = QPainterPath()
            path.moveTo(x, y - 8)
            path.cubicTo(x + 5, y - 4, x + 5, y + 4, x, y + 6)
            path.cubicTo(x - 5, y + 4, x - 5, y - 4, x, y - 8)
            painter.drawPath(path)

    def _draw_thinking_dots(self, painter: QPainter) -> None:
        from PySide6.QtGui import QFont
        dots = "." * self._dot_count
        cx = _W // 2
        cy = _H // 2 + 10
        body_r = 38
        painter.setPen(QPen(QColor("#444444"), 1))
        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        painter.drawText(
            QRect(cx - 20, cy - body_r - 30, 40, 22),
            Qt.AlignmentFlag.AlignCenter,
            dots,
        )

    def _draw_dead(self, painter: QPainter) -> None:
        """스프라이트 로드 실패 시 단순 도형 폴백."""
        painter.save()
        painter.translate(_W / 2, _H / 2 + 10)
        painter.rotate(20)
        painter.translate(-_W / 2, -(_H / 2 + 10))

        cx, cy = _W // 2, _H // 2 + 10
        body_r = 38

        painter.setPen(QPen(QColor("#55555533"), 1))
        painter.setBrush(QBrush(QColor("#888888")))
        painter.drawEllipse(QPoint(cx, cy), body_r, body_r)

        eye_y = cy - body_r // 3
        painter.setPen(QPen(QColor("#555555"), 3))
        for ox in (-12, 12):
            painter.drawLine(cx + ox - 5, eye_y - 5, cx + ox + 5, eye_y + 5)
            painter.drawLine(cx + ox + 5, eye_y - 5, cx + ox - 5, eye_y + 5)

        painter.restore()
