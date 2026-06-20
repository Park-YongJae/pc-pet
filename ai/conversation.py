class Conversation:
    MAX_TURNS = 20

    def __init__(self):
        self._messages: list[dict] = []

    def add_user(self, text: str) -> None:
        self._messages.append({"role": "user", "content": text})
        self._trim()

    def add_assistant(self, text: str) -> None:
        self._messages.append({"role": "assistant", "content": text})
        self._trim()

    @property
    def messages(self) -> list[dict]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def _trim(self) -> None:
        # 각 턴은 user+assistant 쌍이므로 메시지 수 기준으로 자름
        max_msgs = self.MAX_TURNS * 2
        if len(self._messages) > max_msgs:
            self._messages = self._messages[-max_msgs:]
