from __future__ import annotations
import json
import logging
from datetime import datetime

from PySide6.QtCore import QTimer

from ai.claude_client import ClaudeClient
from ai.conversation import Conversation
from core.config import Config, _data_dir
from core.state_machine import StateMachine
from game.hunger_timer import HungerTimer
from game.pet_stats import PetState, select_random_type
from game.poop_system import PoopSystem
from game.random_event import RandomEventSystem
from game.stress_manager import StressManager
from ui.pet_window import PetWindow
from ui.sprite_renderer import PetVisualState

logger = logging.getLogger(__name__)

_STATE_PATH = _data_dir() / "pet_state.json"


class App:
    def __init__(self):
        self._config = Config()
        self._state = self._load_state()
        self._apply_offline_hunger()

        self._stress_mgr = StressManager(self._state)
        self._state_machine = StateMachine(self._state)
        self._hunger_timer = HungerTimer(
            self._state, rate=self._config.data.hunger_decrease_rate
        )
        self._poop_system = PoopSystem(
            self._state, self._stress_mgr,
            get_pet_pos=lambda: (self._window.x(), self._window.y()),
        )
        self._random_event = RandomEventSystem()

        self._client = ClaudeClient(model=self._config.data.model)
        self._pet_conversation = Conversation()
        self._assistant_conversation = Conversation()

        self._window = PetWindow(
            config=self._config,
            state_machine=self._state_machine,
        )
        # 서브시스템 참조 주입
        self._window._poop_system = self._poop_system
        # AI 관련 참조 주입
        self._window._ai_available = self._client.is_available
        self._window._client = self._client
        self._window._pet_conversation = self._pet_conversation
        self._window._assistant_conversation = self._assistant_conversation
        self._window._stress_mgr = self._stress_mgr

        self._wire_signals()
        self._window._open_settings_callback = self.open_settings

    def _load_state(self) -> PetState:
        if _STATE_PATH.exists():
            try:
                with open(_STATE_PATH, encoding="utf-8") as f:
                    return PetState(**json.load(f))
            except Exception as e:
                logger.warning("pet_state.json corrupted, resetting: %s", e)
                try:
                    _STATE_PATH.replace(_STATE_PATH.with_suffix(".json.bak"))
                except Exception:
                    pass
        return PetState(pet_type=select_random_type())

    def _apply_offline_hunger(self) -> None:
        if not self._state.last_saved:
            return
        try:
            saved = datetime.fromisoformat(self._state.last_saved)
            elapsed = (datetime.now() - saved).total_seconds()
            rate = self._config.data.hunger_decrease_rate
            decrease = int((elapsed / 3600) * rate)
            self._state.hunger = max(0, self._state.hunger - decrease)
        except Exception as e:
            logger.warning("offline hunger calc failed: %s", e)

    def _wire_signals(self) -> None:
        sm = self._state_machine
        ht = self._hunger_timer
        stress = self._stress_mgr
        poop = self._poop_system
        win = self._window

        # StateMachine → PetWindow / SpriteRenderer
        sm.visual_state_changed.connect(win.on_visual_state_changed)
        sm.pet_type_changed.connect(win._renderer.set_pet_type)

        # SpriteRenderer hatching → StateMachine
        win._renderer.hatching_complete.connect(sm.on_hatch_complete)

        # HungerTimer → StateMachine + StressManager
        ht.hunger_updated.connect(sm.update_hunger)
        ht.stress_penalty.connect(stress.adjust)

        # StressManager → StateMachine + SpriteRenderer + PetWindow
        stress.stress_updated.connect(sm.update_stress)
        stress.stress_level_changed.connect(win._renderer.set_stress_level)
        stress.stress_message.connect(win.on_stress_message)
        sm.click_message.connect(win.on_click_message)

        # PoopSystem → PetWindow
        poop.poop_spawned.connect(win.on_poop_spawned)
        poop.poop_removed.connect(win.on_poop_removed)

        # StateMachine 사망/부활 → 서브시스템
        sm.pet_died.connect(ht.stop)
        sm.pet_died.connect(stress.stop)
        sm.pet_died.connect(poop.clear_all)
        sm.pet_died.connect(self._random_event.stop)
        sm.pet_revived.connect(ht.start)
        sm.pet_revived.connect(stress.start)
        sm.pet_revived.connect(poop.start)
        sm.pet_revived.connect(self._start_random_event)
        sm.pet_revived.connect(self._pet_conversation.clear)

        # RandomEventSystem → PetWindow
        self._random_event.event_message.connect(win.on_random_event)

    def _start_random_event(self) -> None:
        self._random_event.start(get_hunger=lambda: self._state.hunger)

    def open_settings(self) -> None:
        from ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(config=self._config, parent=self._window)
        dlg.settings_saved.connect(self._on_settings_saved)
        dlg.exec()

    def _on_settings_saved(self, cfg) -> None:
        self._hunger_timer.set_rate(cfg.hunger_decrease_rate)
        api_key = None
        try:
            import keyring
            api_key = keyring.get_password("pc-pet", "anthropic_api_key")
        except Exception:
            pass
        if not api_key:
            import os
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        self._client.reload(api_key=api_key, model=cfg.model)
        self._window._ai_available = self._client.is_available

    def save_state(self) -> None:
        self._state.stamp()
        _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(self._state.model_dump(), f, ensure_ascii=False, indent=2)

    def run(self) -> None:
        win = self._window
        sm = self._state_machine

        if not self._state.is_alive:
            # 비정상 종료 후 재시작: EGG로 복귀
            self._state.is_alive = True
            self._state.hunger = 100
            self._state.stress = 0
            win._renderer.set_pet_type(self._state.pet_type)
            sm._transition(PetVisualState.EGG)
        else:
            win._renderer.set_pet_type(self._state.pet_type)
            initial = sm._target_idle_state()
            sm._transition(initial)
            # hunger이 0이면 즉시 사망 처리
            if self._state.hunger == 0:
                sm._trigger_death()

        self._hunger_timer.start()
        self._stress_mgr.start()
        self._poop_system.start()
        self._random_event.start(get_hunger=lambda: self._state.hunger)

        # 5분마다 자동 저장 (강제 종료 시 상태 유실 방지)
        self._autosave_timer = QTimer()
        self._autosave_timer.setInterval(5 * 60 * 1000)
        self._autosave_timer.timeout.connect(self.save_state)
        self._autosave_timer.start()

        # 저장된 똥 복원
        for p in list(self._state.poops):
            win.on_poop_spawned(p["idx"], p["x"], p["y"])
            if p["idx"] >= self._poop_system._next_idx:
                self._poop_system._next_idx = p["idx"] + 1

        win.show()
