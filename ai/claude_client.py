import logging
import os

import anthropic
from PySide6.QtCore import QObject, QThread, Signal

logger = logging.getLogger(__name__)


def _load_api_key() -> str | None:
    try:
        import keyring
        key = keyring.get_password("pc-pet", "anthropic_api_key")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


def _classify_error(e: Exception) -> str:
    if isinstance(e, anthropic.AuthenticationError):
        return "API 키가 유효하지 않습니다. 설정에서 다시 확인해 주세요."
    if isinstance(e, anthropic.RateLimitError):
        return "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요."
    if isinstance(e, (anthropic.APIConnectionError, anthropic.APITimeoutError)):
        return "네트워크 연결을 확인해 주세요."
    if isinstance(e, anthropic.APIStatusError):
        return f"서버 오류 ({e.status_code}). 잠시 후 다시 시도해 주세요."
    return f"오류가 발생했습니다: {e}"


class StreamWorker(QObject):
    chunk_received = Signal(str)
    reply_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, client: anthropic.Anthropic, messages: list, system: str | None, model: str):
        super().__init__()
        self._client = client
        self._messages = messages
        self._system = system
        self._model = model

    def run(self) -> None:
        try:
            kwargs: dict = {
                "model": self._model,
                "max_tokens": 1024,
                "messages": self._messages,
            }
            if self._system:
                kwargs["system"] = self._system

            full_text = ""
            with self._client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    full_text += text
                    self.chunk_received.emit(text)
            self.reply_ready.emit(full_text)
        except Exception as e:
            logger.error("Claude API error: %s", e)
            self.error_occurred.emit(_classify_error(e))


class ClaudeClient(QObject):
    chunk_received = Signal(str)
    reply_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, model: str, parent: QObject | None = None):
        super().__init__(parent)
        self._model = model
        self._api_key = _load_api_key()
        self._client = anthropic.Anthropic(api_key=self._api_key) if self._api_key else None
        self._current_thread: QThread | None = None
        self._current_worker: StreamWorker | None = None

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def reload(self, api_key: str | None = None, model: str | None = None) -> None:
        if api_key is not None:
            self._api_key = api_key
        if model is not None:
            self._model = model
        self._client = anthropic.Anthropic(api_key=self._api_key) if self._api_key else None

    def request(self, messages: list, system: str | None = None) -> None:
        if not self._client:
            self.error_occurred.emit("API 키가 설정되지 않았습니다.")
            return
        if self._current_thread and self._current_thread.isRunning():
            logger.warning("Request already in progress, ignoring new request")
            return

        worker = StreamWorker(self._client, messages, system, self._model)
        thread = QThread(self)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.chunk_received.connect(self.chunk_received)
        worker.reply_ready.connect(self._on_reply)
        worker.error_occurred.connect(self._on_error)
        thread.finished.connect(worker.deleteLater)

        self._current_worker = worker
        self._current_thread = thread
        thread.start()

    def _on_reply(self, text: str) -> None:
        self.reply_ready.emit(text)
        self._cleanup_thread()

    def _on_error(self, msg: str) -> None:
        self.error_occurred.emit(msg)
        self._cleanup_thread()

    def _cleanup_thread(self) -> None:
        if self._current_thread:
            self._current_thread.quit()
            self._current_thread.wait()
            self._current_worker = None
            self._current_thread = None
