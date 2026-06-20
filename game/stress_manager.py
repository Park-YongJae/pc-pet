from __future__ import annotations
import random

from PySide6.QtCore import QObject, QTimer, Signal

from game.pet_stats import PetState

_MESSAGES = {
    1: ["...", "음...", "흠..."],
    2: ["ㅠㅠ", "힘들어...", "지쳐..."],
    3: ["저 힘들어요...", "살려줘요...", "으아아..."],
}

_MSG_INTERVAL_MIN = 5 * 60 * 1000   # 5분
_MSG_INTERVAL_MAX = 10 * 60 * 1000  # 10분


class StressManager(QObject):
    stress_updated = Signal(int)        # → StateMachine.update_stress
    stress_level_changed = Signal(int)  # 0~3 → SpriteRenderer.set_stress_level
    stress_message = Signal(str)        # → PetWindow (말풍선 표시)

    def __init__(self, state: PetState, parent=None):
        super().__init__(parent)
        self._state = state
        self._last_level = -1

        self._neglect_timer = QTimer(self)
        self._neglect_timer.setInterval(30 * 60 * 1000)  # 30분
        self._neglect_timer.timeout.connect(self._on_neglect_tick)

        self._msg_timer = QTimer(self)
        self._msg_timer.setSingleShot(True)
        self._msg_timer.timeout.connect(self._on_msg_tick)

    def start(self) -> None:
        self._neglect_timer.start()
        self._reschedule_msg()

    def stop(self) -> None:
        self._neglect_timer.stop()
        self._msg_timer.stop()

    def adjust(self, delta: int) -> None:
        new_val = max(0, min(100, self._state.stress + delta))
        self._state.stress = new_val
        level = self._compute_level(new_val)
        if level != self._last_level:
            self._last_level = level
            self.stress_level_changed.emit(level)
        self.stress_updated.emit(new_val)

    def _on_neglect_tick(self) -> None:
        self.adjust(5)

    def _on_msg_tick(self) -> None:
        level = self._compute_level(self._state.stress)
        if level >= 1:
            msg = random.choice(_MESSAGES[level])
            self.stress_message.emit(msg)
        self._reschedule_msg()

    def _reschedule_msg(self) -> None:
        interval = random.randint(_MSG_INTERVAL_MIN, _MSG_INTERVAL_MAX)
        self._msg_timer.setInterval(interval)
        self._msg_timer.start()

    def _compute_level(self, stress: int) -> int:
        if stress <= 30:
            return 0
        elif stress <= 60:
            return 1
        elif stress <= 90:
            return 2
        return 3
