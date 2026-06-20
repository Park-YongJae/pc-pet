from __future__ import annotations
import random
import math
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication


_SPEED = 80.0       # px/sec
_TICK_MS = 16       # ~60 FPS
_TICK_S = _TICK_MS / 1000.0
_STEP = _SPEED * _TICK_S


class WalkController(QObject):
    position_changed = Signal(int, int)
    direction_changed = Signal(bool)  # True = facing right

    def __init__(self, parent=None):
        super().__init__(parent)
        self._x = 0.0
        self._y = 0.0
        self._vx = 0.0
        self._vy = 0.0
        self._win_w = 120
        self._win_h = 140
        self._facing_right = True
        self._paused = True
        self._area: list[tuple[float, float]] | None = None  # None = 제한 없음

        self._move_timer = QTimer(self)
        self._move_timer.setInterval(_TICK_MS)
        self._move_timer.timeout.connect(self._on_move_tick)

        self._dir_timer = QTimer(self)
        self._dir_timer.setSingleShot(True)
        self._dir_timer.timeout.connect(self._pick_direction)

    def set_window_size(self, w: int, h: int) -> None:
        self._win_w = w
        self._win_h = h

    def set_position(self, x: int, y: int) -> None:
        self._x = float(x)
        self._y = float(y)

    def is_valid_position(self, x: int, y: int) -> bool:
        """드래그 중 이 위치가 이동 영역 안인지 확인."""
        return self._inside_area(float(x), float(y))

    def set_area(self, points: list[tuple[float, float]] | None) -> None:
        self._area = points if points else None
        self._snap_inside_area()

    def _snap_inside_area(self) -> None:
        """영역 밖에 있으면 영역 안의 유효한 위치로 즉시 이동."""
        if self._area and not self._inside_area(self._x, self._y):
            px, py = self._find_valid_position()
            self._x = px - self._win_w / 2
            self._y = py - self._win_h / 2
            self.position_changed.emit(int(self._x), int(self._y))

    def _find_valid_position(self) -> tuple[float, float]:
        """폴리곤 안에 실제로 위치한 점을 반환. 오목 폴리곤도 대응."""
        if not self._area:
            screen = QApplication.primaryScreen().availableGeometry()
            return float(screen.center().x()), float(screen.center().y())

        # 1차: 꼭짓점 중심 시도
        cx, cy = self._area_centroid()
        if self._point_in_polygon(cx, cy):
            return cx, cy

        # 2차: 각 꼭짓점을 중심 방향으로 20% 당긴 지점 시도
        for vx, vy in self._area:
            px = vx * 0.8 + cx * 0.2
            py = vy * 0.8 + cy * 0.2
            if self._point_in_polygon(px, py):
                return px, py

        # 3차: 인접 꼭짓점 쌍의 중점 시도
        n = len(self._area)
        for i in range(n):
            mx = (self._area[i][0] + self._area[(i + 1) % n][0]) / 2
            my = (self._area[i][1] + self._area[(i + 1) % n][1]) / 2
            # 중점에서 중심 방향으로 살짝 이동
            px = mx * 0.9 + cx * 0.1
            py = my * 0.9 + cy * 0.1
            if self._point_in_polygon(px, py):
                return px, py

        # 4차: 바운딩박스 격자 샘플링 (20×20)
        xs = [p[0] for p in self._area]
        ys = [p[1] for p in self._area]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        for i in range(20):
            for j in range(20):
                px = min_x + (max_x - min_x) * (i + 0.5) / 20
                py = min_y + (max_y - min_y) * (j + 0.5) / 20
                if self._point_in_polygon(px, py):
                    return px, py

        # 최후: 첫 번째 꼭짓점 사용
        return self._area[0]

    def _point_in_polygon(self, px: float, py: float) -> bool:
        """레이 캐스팅으로 점이 폴리곤 안에 있는지 확인."""
        n = len(self._area)  # type: ignore[arg-type]
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = self._area[i]  # type: ignore[index]
            xj, yj = self._area[j]  # type: ignore[index]
            if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside

    def _inside_area(self, x: float, y: float) -> bool:
        """펫 바운딩박스의 4개 모서리가 모두 폴리곤 안에 있는지 확인."""
        if not self._area:
            return True
        corners = [
            (x,                  y),
            (x + self._win_w,    y),
            (x,                  y + self._win_h),
            (x + self._win_w,    y + self._win_h),
        ]
        return all(self._point_in_polygon(px, py) for px, py in corners)

    def _area_centroid(self) -> tuple[float, float]:
        pts = self._area or []
        if not pts:
            return self._x, self._y
        return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)

    def resume(self) -> None:
        if self._paused:
            self._paused = False
            # 드래그 후 영역 밖에 놓였으면 안쪽으로 이동
            self._snap_inside_area()
            self._pick_direction()
            self._move_timer.start()

    def pause(self) -> None:
        self._paused = True
        self._move_timer.stop()
        self._dir_timer.stop()
        self._vx = 0.0
        self._vy = 0.0

    def _pick_direction(self) -> None:
        if self._paused:
            return

        pause_chance = random.random() < 0.2
        if pause_chance:
            self._vx = 0.0
            self._vy = 0.0
        else:
            angle_choices = [0, 45, 90, 135, 180, 225, 270, 315]
            angle = math.radians(random.choice(angle_choices))
            self._vx = _SPEED * math.cos(angle)
            self._vy = _SPEED * math.sin(angle)

            new_facing = self._vx >= 0
            if new_facing != self._facing_right:
                self._facing_right = new_facing
                self.direction_changed.emit(self._facing_right)

        interval_ms = random.randint(2000, 5000)
        self._dir_timer.setInterval(interval_ms)
        self._dir_timer.start()

    def _on_move_tick(self) -> None:
        if self._vx == 0.0 and self._vy == 0.0:
            return

        screen = QApplication.primaryScreen().availableGeometry()
        new_x = self._x + self._vx * _TICK_S
        new_y = self._y + self._vy * _TICK_S

        if new_x < screen.left():
            new_x = float(screen.left())
            self._vx = abs(self._vx)
            self._facing_right = True
            self.direction_changed.emit(True)
        elif new_x + self._win_w > screen.right():
            new_x = float(screen.right() - self._win_w)
            self._vx = -abs(self._vx)
            self._facing_right = False
            self.direction_changed.emit(False)

        if new_y < screen.top():
            new_y = float(screen.top())
            self._vy = abs(self._vy)
        elif new_y + self._win_h > screen.bottom():
            new_y = float(screen.bottom() - self._win_h)
            self._vy = -abs(self._vy)

        # 이동 영역 밖이면 새 방향 선택 (현재 위치 유지)
        if not self._inside_area(new_x, new_y):
            self._pick_direction()
            return

        self._x = new_x
        self._y = new_y
        self.position_changed.emit(int(self._x), int(self._y))
