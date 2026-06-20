from __future__ import annotations
from PySide6.QtCore import QObject, QTimer, Signal

from game.pet_stats import PetState


class HungerTimer(QObject):
    hunger_updated = Signal(int)  # → StateMachine.update_hunger
    stress_penalty = Signal(int)  # delta → StressManager.adjust

    def __init__(self, state: PetState, rate: int, parent=None):
        super().__init__(parent)
        self._state = state
        self._rate = rate

        self._timer = QTimer(self)
        self._timer.setInterval(60 * 60 * 1000)  # 1시간
        self._timer.timeout.connect(self._on_tick)

    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def set_rate(self, rate: int) -> None:
        self._rate = rate

    def set_interval(self, ms: int) -> None:
        """테스트용 인터벌 변경."""
        self._timer.setInterval(ms)

    def _on_tick(self) -> None:
        new_val = max(0, self._state.hunger - self._rate)
        self._state.hunger = new_val
        if new_val < 30:
            self.stress_penalty.emit(3)
        self.hunger_updated.emit(new_val)
