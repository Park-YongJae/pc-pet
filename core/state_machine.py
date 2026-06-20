import random

from PySide6.QtCore import QObject, QTimer, Signal

from game.pet_stats import PetState, select_random_type
from ui.sprite_renderer import PetVisualState

_CLICK_MESSAGES = {
    0: ["신나요! 🎉", "좋아요! 💕", "헤헤 😊", "기분 최고! ✨", "같이 놀아요! 🌟"],
    1: ["음... 😐", "그래요...", "뭐예요 👀", "좀 쉬고 싶어요"],
    2: ["ㅠㅠ", "힘들어요...", "그만해요 😢", "피곤해요..."],
    3: ["으아아! 😱", "살려줘요!", "저 힘들어요...", "제발요..."],
}


class StateMachine(QObject):
    visual_state_changed = Signal(PetVisualState)
    pet_type_changed = Signal(int)
    pet_died = Signal()
    pet_revived = Signal()
    click_message = Signal(str)

    def __init__(self, state: PetState, parent=None):
        super().__init__(parent)
        self._state_data = state
        self._current = PetVisualState.EGG

        self._click_count = 0
        self._click_reset_timer = QTimer(self)
        self._click_reset_timer.setSingleShot(True)
        self._click_reset_timer.setInterval(10000)
        self._click_reset_timer.timeout.connect(self._on_click_reset)

        self._react_timer = QTimer(self)
        self._react_timer.setSingleShot(True)
        self._react_timer.timeout.connect(self._on_react_timeout)

    # ── 공개 API ────────────────────────────────────────────────────

    def force_hatch(self) -> None:
        if self._current == PetVisualState.EGG:
            self._transition(PetVisualState.HATCHING)

    def on_hatch_complete(self) -> None:
        self._state_data.is_alive = True
        self._transition(self._target_idle_state())

    def on_click(self) -> None:
        if self._current in (PetVisualState.EGG, PetVisualState.HATCHING,
                              PetVisualState.DEAD):
            return
        if self._current in (PetVisualState.EATING, PetVisualState.REACT_HAPPY,
                              PetVisualState.REACT_ANNOYED, PetVisualState.REACT_ANGRY):
            return

        self._click_count += 1
        self._click_reset_timer.start()

        if self._click_count <= 3:
            self._apply_stress(-5)
            self._transition(PetVisualState.REACT_HAPPY)
            msg_level = 0
        elif self._click_count <= 7:
            self._apply_stress(3)
            self._transition(PetVisualState.REACT_ANNOYED)
            msg_level = 2
        else:
            self._apply_stress(8)
            self._transition(PetVisualState.REACT_ANGRY)
            msg_level = 3

        self.click_message.emit(random.choice(_CLICK_MESSAGES[msg_level]))
        self._schedule_return(1500)

    def feed(self) -> None:
        if self._current in (PetVisualState.EGG, PetVisualState.HATCHING,
                              PetVisualState.DEAD):
            return
        new_hunger = min(100, self._state_data.hunger + 50)
        self._state_data.hunger = new_hunger
        if self._state_data.hunger >= 80:
            # 배부른데 억지로 먹임 → 먹긴 하지만 스트레스 증가
            self._apply_stress(10)
        else:
            self._apply_stress(-10)
        self._transition(PetVisualState.EATING)
        self._schedule_return(2000)

    def on_poop_cleaned(self) -> None:
        self._apply_stress(-8)

    def start_thinking(self) -> None:
        if self._current in (PetVisualState.IDLE, PetVisualState.HUNGRY,
                              PetVisualState.WALKING):
            self._transition(PetVisualState.THINKING)

    def start_talking(self) -> None:
        if self._current == PetVisualState.THINKING:
            self._transition(PetVisualState.TALKING)

    def end_talking(self) -> None:
        if self._current in (PetVisualState.THINKING, PetVisualState.TALKING):
            self._transition(self._target_idle_state())

    def update_hunger(self, val: int) -> None:
        self._state_data.hunger = val
        if val == 0:
            self._trigger_death()
            return
        # IDLE ↔ HUNGRY 전환
        if self._current in (PetVisualState.IDLE, PetVisualState.WALKING,
                              PetVisualState.HUNGRY):
            self._transition(self._target_idle_state())

    def update_stress(self, val: int) -> None:
        self._state_data.stress = max(0, min(100, val))
        if self._state_data.stress >= 100:
            self._trigger_death()

    # ── 내부 ────────────────────────────────────────────────────────

    def _transition(self, new_state: PetVisualState) -> None:
        # DEAD 상태에서는 EGG(부활)만 허용
        if (self._current == PetVisualState.DEAD
                and new_state != PetVisualState.EGG):
            return
        self._current = new_state
        self.visual_state_changed.emit(new_state)

    def _target_idle_state(self) -> PetVisualState:
        return (PetVisualState.HUNGRY
                if self._state_data.hunger < 70
                else PetVisualState.IDLE)

    def _compute_stress_level(self, stress: int) -> int:
        if stress <= 30:
            return 0
        elif stress <= 60:
            return 1
        elif stress <= 90:
            return 2
        return 3

    def _apply_stress(self, delta: int) -> None:
        new_val = max(0, min(100, self._state_data.stress + delta))
        self._state_data.stress = new_val
        self.update_stress(new_val)

    def _schedule_return(self, ms: int) -> None:
        self._react_timer.setInterval(ms)
        self._react_timer.start()

    def _on_react_timeout(self) -> None:
        if self._current in (PetVisualState.REACT_HAPPY,
                              PetVisualState.REACT_ANNOYED,
                              PetVisualState.REACT_ANGRY,
                              PetVisualState.EATING):
            self._transition(self._target_idle_state())

    def _on_click_reset(self) -> None:
        self._click_count = 0

    def _trigger_death(self) -> None:
        if self._current == PetVisualState.DEAD:
            return
        self._state_data.is_alive = False
        self._react_timer.stop()
        self._transition(PetVisualState.DEAD)
        self.pet_died.emit()
        QTimer.singleShot(5000, self._revive)

    def _revive(self) -> None:
        self._state_data.total_deaths += 1
        self._state_data.hunger = 100
        self._state_data.stress = 0
        self._state_data.is_alive = True
        self._state_data.poops = []
        self._click_count = 0
        self._click_reset_timer.stop()

        new_type = select_random_type()
        self._state_data.pet_type = new_type
        self.pet_type_changed.emit(new_type)

        self.pet_revived.emit()
        self._transition(PetVisualState.EGG)
