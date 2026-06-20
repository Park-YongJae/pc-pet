import random
from datetime import datetime
from functools import partial
from typing import Callable

from PySide6.QtCore import QObject, QTimer, Signal

from game.pet_stats import PetState
from game.stress_manager import StressManager

_MAX_POOPS = 3
_NEGLECT_MS = 30 * 60 * 1000  # 30분


class PoopSystem(QObject):
    poop_spawned = Signal(int, int, int)  # idx, x, y
    poop_removed = Signal(int)            # idx

    def __init__(self, state: PetState, stress_manager: StressManager,
                 get_pet_pos: Callable[[], tuple[int, int]] | None = None,
                 parent=None):
        super().__init__(parent)
        self._state = state
        self._stress = stress_manager
        self._get_pet_pos = get_pet_pos  # () → (x, y)
        self._next_idx = 0
        self._neglect_timers: dict[int, QTimer] = {}

        self._spawn_timer = QTimer(self)
        self._spawn_timer.setSingleShot(True)
        self._spawn_timer.timeout.connect(self._on_spawn_tick)

    def start(self) -> None:
        self._spawn_timer.setInterval(self._next_interval())
        self._spawn_timer.start()
        # 저장된 똥 방치 타이머 재개
        for p in self._state.poops:
            self._start_neglect_timer(p["idx"])

    def stop(self) -> None:
        self._spawn_timer.stop()
        for t in self._neglect_timers.values():
            t.stop()

    def clean_poop(self, idx: int) -> None:
        if idx not in self._neglect_timers:
            return
        self._neglect_timers.pop(idx).stop()
        self._state.poops = [p for p in self._state.poops if p["idx"] != idx]
        self._stress.adjust(-8)
        self.poop_removed.emit(idx)

    def clean_all_poops(self) -> None:
        for idx in list(self._neglect_timers.keys()):
            self.clean_poop(idx)

    def clear_all(self) -> None:
        for idx in list(self._neglect_timers.keys()):
            self._neglect_timers.pop(idx).stop()
            self.poop_removed.emit(idx)  # 화면 위젯 제거
        self._state.poops = []
        self._spawn_timer.stop()

    # ── 내부 ────────────────────────────────────────────────────────

    def _on_spawn_tick(self) -> None:
        if len(self._state.poops) < _MAX_POOPS:
            x, y = self._spawn_position()
            idx = self._next_idx
            self._next_idx += 1
            entry = {
                "idx": idx,
                "x": x,
                "y": y,
                "spawned_at": datetime.now().isoformat(),
            }
            self._state.poops.append(entry)
            self._start_neglect_timer(idx)
            self.poop_spawned.emit(idx, x, y)

        self._spawn_timer.setInterval(self._next_interval())
        self._spawn_timer.start()

    def _start_neglect_timer(self, idx: int) -> None:
        t = QTimer(self)
        t.setInterval(_NEGLECT_MS)
        t.timeout.connect(partial(self._on_neglect, idx))
        t.start()
        self._neglect_timers[idx] = t

    def _on_neglect(self, idx: int) -> None:
        self._stress.adjust(5)

    def _spawn_position(self) -> tuple[int, int]:
        if self._get_pet_pos is not None:
            px, py = self._get_pet_pos()
            # 펫 발 아래 ±20px 랜덤 오프셋
            x = px + random.randint(-20, 20)
            y = py + random.randint(-20, 20)
            return x, y
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        return (random.randint(screen.left(), screen.right() - 36),
                random.randint(screen.top(), screen.bottom() - 36))

    def _next_interval(self) -> int:
        return random.randint(30 * 60 * 1000, 2 * 60 * 60 * 1000)  # 30분~2시간
