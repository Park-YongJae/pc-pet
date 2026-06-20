from __future__ import annotations
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QImage, QBitmap, QPainter
from PySide6.QtWidgets import QWidget, QApplication, QMenu

from core.config import Config
from core.platform_utils import set_click_through
from core.state_machine import StateMachine
from game.walk_controller import WalkController
from ui.sprite_renderer import SpriteRenderer, PetVisualState

_DEAD_STATES = (PetVisualState.EGG, PetVisualState.HATCHING, PetVisualState.DEAD)
_ACTIVE_STATES = (PetVisualState.IDLE, PetVisualState.WALKING, PetVisualState.HUNGRY)


class PetWindow(QWidget):
    def __init__(self, config: Config, state_machine: StateMachine,
                 parent=None):
        super().__init__(parent)
        self._config = config
        self._state_machine = state_machine
        self._poop_widgets: dict = {}  # idx → PoopWidget
        self._poop_system = None       # App에서 주입
        self._open_settings_callback = None  # App에서 주입

        flags = (Qt.WindowType.FramelessWindowHint |
                 Qt.WindowType.Tool)
        if config.data.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        self._renderer = SpriteRenderer(self)
        self.setFixedSize(self._renderer.size())

        self._walk = WalkController(self)
        self._walk.set_window_size(self.width(), self.height())
        self._walk.position_changed.connect(self._on_position_changed)
        self._walk.direction_changed.connect(self._on_direction_changed)

        if config.data.movement_area:
            self._walk.set_area(
                [(p[0], p[1]) for p in config.data.movement_area]
            )

        self._drag_pos: QPoint | None = None
        self._drag_start_pos: QPoint | None = None
        self._area_editor = None

        # AI 관련 (App에서 주입)
        self._ai_available: bool = False
        self._client = None
        self._pet_conversation = None
        self._assistant_conversation = None
        self._stress_mgr = None
        self._speech_bubble = None
        self._chat_dialog = None

        from ui.stats_overlay import StatsOverlay
        self._stats_overlay = StatsOverlay()

        self._center_on_screen()

    def showEvent(self, event):
        super().showEvent(event)
        self._update_mask()
        # macOS: setMask가 마우스 이벤트 필터링을 담당하므로
        # NSWindow는 이벤트를 무시하지 않도록 명시
        import platform
        if platform.system() == "Darwin":
            set_click_through(self, False)

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2 + screen.left()
        y = (screen.height() - self.height()) // 2 + screen.top()
        self.move(x, y)
        self._walk.set_position(x, y)

    def _update_mask(self) -> None:
        img = QImage(self.size(), QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        p = QPainter(img)
        self._renderer._draw(p)
        p.end()
        self.setMask(QBitmap.fromImage(img.createAlphaMask()))

    # ── 슬롯: StateMachine → 시각 업데이트 ──────────────────────────

    def on_visual_state_changed(self, state: PetVisualState) -> None:
        self._renderer.set_state(state)
        self._update_mask()

        pause_states = (PetVisualState.REACT_HAPPY, PetVisualState.REACT_ANNOYED,
                        PetVisualState.REACT_ANGRY, PetVisualState.EATING,
                        PetVisualState.DEAD, PetVisualState.THINKING,
                        PetVisualState.TALKING)
        if state in pause_states:
            self._walk.pause()
        elif state in _ACTIVE_STATES:
            self._walk.resume()
        elif state == PetVisualState.EGG:
            self._walk.pause()

    # ── 슬롯: PoopSystem ─────────────────────────────────────────────

    def on_poop_spawned(self, idx: int, x: int, y: int) -> None:
        from ui.poop_widget import PoopWidget
        w = PoopWidget(idx, x, y)
        if self._poop_system is not None:
            w.clicked.connect(self._poop_system.clean_poop)
        w.show()
        self._poop_widgets[idx] = w

    def on_poop_removed(self, idx: int) -> None:
        if idx in self._poop_widgets:
            self._poop_widgets.pop(idx).deleteLater()

    # ── 마우스 호버 → 수치 표시 ─────────────────────────────────────

    def enterEvent(self, event):
        state = self._state_machine._state_data
        bubble_visible = self._speech_bubble is not None and self._speech_bubble.isVisible()
        self._stats_overlay.show_near(
            self.x(), self.y(), self.width(),
            hunger=state.hunger,
            stress=state.stress,
            bubble_visible=bubble_visible,
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._stats_overlay.hide()
        super().leaveEvent(event)

    # ── 마우스 이벤트 ────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            state = self._renderer._state
            if state == PetVisualState.EGG:
                self._state_machine.force_hatch()
                return
            if state in (PetVisualState.HATCHING, PetVisualState.DEAD):
                return
            self._drag_start_pos = event.globalPosition().toPoint()
            self._drag_pos = self._drag_start_pos
            self._walk.pause()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self._drag_pos = event.globalPosition().toPoint()
            new_pos = self.pos() + delta
            if not self._walk.is_valid_position(new_pos.x(), new_pos.y()):
                return
            self.move(new_pos)
            self._walk.set_position(new_pos.x(), new_pos.y())

    def mouseReleaseEvent(self, event):
        if self._drag_pos is not None:
            moved = (event.globalPosition().toPoint() -
                     self._drag_start_pos).manhattanLength()
            self._drag_pos = None
            self._drag_start_pos = None
            if moved < 5:
                self._state_machine.on_click()
            elif self._renderer._state in _ACTIVE_STATES:
                self._walk.resume()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        state = self._renderer._state

        alive = state not in _DEAD_STATES
        ai_busy = state in (PetVisualState.THINKING, PetVisualState.TALKING)
        chat_open = self._chat_dialog is not None and self._chat_dialog.isVisible()

        feed_action = menu.addAction("먹이주기")
        feed_action.setEnabled(alive)
        feed_action.triggered.connect(self._open_feed_dialog)

        talk_action = menu.addAction("펫에게 말 걸기")
        talk_action.setEnabled(
            alive and self._ai_available and not ai_busy and not chat_open
        )
        talk_action.triggered.connect(self._open_talk_input)

        assistant_action = menu.addAction("AI 어시스턴트")
        assistant_action.setEnabled(self._ai_available and not ai_busy)
        assistant_action.triggered.connect(self._open_chat_dialog)

        clean_action = menu.addAction("청소")
        clean_action.setEnabled(alive and bool(self._poop_widgets))
        clean_action.triggered.connect(self._clean_poops)

        menu.addSeparator()
        menu.addAction("이동 영역 설정", self._start_area_editor)
        if self._config.data.movement_area:
            menu.addAction("이동 영역 초기화", self._clear_area)
        menu.addSeparator()
        menu.addAction("설정", self._open_settings)
        menu.addAction("종료", QApplication.quit)
        menu.exec(event.globalPos())

    # ── 내부 슬롯 ───────────────────────────────────────────────────

    def _on_direction_changed(self, facing_right: bool) -> None:
        self._renderer.set_facing(facing_right)
        self._update_mask()

    def _on_position_changed(self, x: int, y: int) -> None:
        self.move(x, y)
        if self._speech_bubble and self._speech_bubble.isVisible():
            self._speech_bubble.update_position(self.geometry())

    def moveEvent(self, event):
        super().moveEvent(event)
        if self._speech_bubble and self._speech_bubble.isVisible():
            self._speech_bubble.update_position(self.geometry())

    def _open_talk_input(self) -> None:
        from ui.talk_dialog import TalkInputDialog
        pet_name = self._config.data.pet_name
        dlg = TalkInputDialog(pet_name=pet_name, parent=self)
        dlg.talk_submitted.connect(self._on_talk_submitted)
        dlg.exec()

    def _on_talk_submitted(self, text: str) -> None:
        if not self._client or not self._pet_conversation:
            return
        self._state_machine.start_thinking()
        if self._speech_bubble is None:
            from ui.speech_bubble import SpeechBubble
            self._speech_bubble = SpeechBubble()
            self._speech_bubble.closed.connect(self._on_bubble_closed)
        self._speech_bubble.show_typing(self.geometry())
        self._pet_conversation.add_user(text)

        state = self._state_machine._state_data
        pet_name = self._config.data.pet_name
        system = (
            f"너는 {pet_name}이야. "
            f"현재 배부름 수치는 {state.hunger}/100 (100에 가까울수록 배부름), "
            f"스트레스 수치는 {state.stress}/100 (0에 가까울수록 편안함)이야. "
            "귀엽고 짧게, 100자 이내로 대답해줘. 이모지 사용 가능."
        )
        self._client.reply_ready.connect(self._on_pet_reply)
        self._client.error_occurred.connect(self._on_ai_error)
        self._client.request(self._pet_conversation.messages, system)

    def _on_pet_reply(self, text: str) -> None:
        # 연결 해제 (일회성 슬롯으로 사용)
        try:
            self._client.reply_ready.disconnect(self._on_pet_reply)
            self._client.error_occurred.disconnect(self._on_ai_error)
        except RuntimeError:
            pass
        self._pet_conversation.add_assistant(text)
        self._state_machine.start_talking()
        if self._stress_mgr:
            self._stress_mgr.adjust(-5)
        if self._speech_bubble:
            self._speech_bubble.show_text(text, self.geometry())

    def _on_ai_error(self, msg: str) -> None:
        try:
            self._client.reply_ready.disconnect(self._on_pet_reply)
            self._client.error_occurred.disconnect(self._on_ai_error)
        except RuntimeError:
            pass
        self._state_machine.end_talking()
        self._show_bubble(f"앗, 연결이 안 돼요 😢\n{msg}")

    def _on_bubble_closed(self) -> None:
        self._state_machine.end_talking()

    def on_random_event(self, msg: str) -> None:
        state = self._renderer._state
        blocked = (PetVisualState.THINKING, PetVisualState.TALKING,
                   PetVisualState.EGG, PetVisualState.HATCHING, PetVisualState.DEAD)
        if state in blocked:
            return
        self._show_bubble(msg)

    def on_stress_message(self, msg: str) -> None:
        state = self._renderer._state
        blocked = (PetVisualState.THINKING, PetVisualState.TALKING,
                   PetVisualState.EGG, PetVisualState.HATCHING, PetVisualState.DEAD)
        if state in blocked:
            return
        self._show_bubble(msg)

    def on_click_message(self, msg: str) -> None:
        state = self._renderer._state
        if state in (PetVisualState.EGG, PetVisualState.HATCHING, PetVisualState.DEAD,
                     PetVisualState.THINKING, PetVisualState.TALKING):
            return
        self._show_bubble(msg)

    def _show_bubble(self, msg: str) -> None:
        if self._speech_bubble is None:
            from ui.speech_bubble import SpeechBubble
            self._speech_bubble = SpeechBubble()
            self._speech_bubble.closed.connect(self._on_bubble_closed)
        self._speech_bubble.show_text(msg, self.geometry())

    def _open_chat_dialog(self) -> None:
        from ui.chat_dialog import ChatDialog
        if self._chat_dialog and self._chat_dialog.isVisible():
            self._chat_dialog.activateWindow()
            return
        self._state_machine._transition(PetVisualState.TALKING)
        self._chat_dialog = ChatDialog(
            client=self._client,
            conversation=self._assistant_conversation,
            pet_name=self._config.data.pet_name,
            parent=self,
        )
        self._chat_dialog.dialog_closed.connect(self._on_chat_closed)
        self._chat_dialog.show()

    def _on_chat_closed(self) -> None:
        self._state_machine.end_talking()

    def _open_feed_dialog(self) -> None:
        from ui.feed_dialog import FeedDialog
        dlg = FeedDialog(hunger=self._state_machine._state_data.hunger,
                         parent=self)
        dlg.feed_confirmed.connect(self._state_machine.feed)
        dlg.exec()

    def _start_area_editor(self) -> None:
        from ui.area_editor import AreaEditor
        existing = self._config.data.movement_area or None
        self._area_editor = AreaEditor(existing_points=existing)
        self._area_editor.area_confirmed.connect(self._on_area_confirmed)
        self._area_editor.show()
        self._area_editor.activateWindow()

    def _on_area_confirmed(self, points: list) -> None:
        self._config.data.movement_area = [[p[0], p[1]] for p in points]
        self._config.save()
        self._walk.set_area([(p[0], p[1]) for p in points] if points else None)

    def _clear_area(self) -> None:
        self._config.data.movement_area = []
        self._config.save()
        self._walk.set_area(None)

    def _clean_poops(self) -> None:
        if self._poop_system:
            self._poop_system.clean_all_poops()

    def _open_settings(self) -> None:
        if self._open_settings_callback:
            self._open_settings_callback()
