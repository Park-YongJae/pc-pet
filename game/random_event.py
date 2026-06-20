import random
from typing import Callable

from PySide6.QtCore import QObject, QTimer, Signal

_NORMAL_MESSAGES = [
    "심심하다~",
    "오늘 날씨 어때요?",
    "뭐해요? 같이 놀아요! 👀",
    "저 여기 있어요~",
    "안녕히 계세요~ 저도 여기 있을게요",
    "오늘도 열심히 해요! ✨",
    "심심할 땐 저 눌러봐요~",
    "저 귀엽죠? 🥺",
]

_HUNGRY_MESSAGES = [
    "배고파요...",
    "밥 주세요~ 🍚",
    "배가 고파요 ㅠㅠ",
    "밥 언제 줘요...",
    "배고픈데... 혹시 뭐 있어요?",
]

_INTERVAL_MIN = 20 * 60 * 1000  # 20분
_INTERVAL_MAX = 40 * 60 * 1000  # 40분


class RandomEventSystem(QObject):
    event_message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._get_hunger: Callable[[], int] | None = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_tick)

    def start(self, get_hunger: Callable[[], int] | None = None) -> None:
        self._get_hunger = get_hunger
        self._reschedule()

    def stop(self) -> None:
        self._timer.stop()

    def _on_tick(self) -> None:
        hunger = self._get_hunger() if self._get_hunger else 100
        pool = _HUNGRY_MESSAGES if hunger < 40 else _NORMAL_MESSAGES
        self.event_message.emit(random.choice(pool))
        self._reschedule()

    def _reschedule(self) -> None:
        self._timer.setInterval(random.randint(_INTERVAL_MIN, _INTERVAL_MAX))
        self._timer.start()
