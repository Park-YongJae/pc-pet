from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLineEdit, QPushButton,
    QSizePolicy, QTextBrowser, QVBoxLayout,
)


class ChatDialog(QDialog):
    dialog_closed = Signal()

    def __init__(self, client, conversation, pet_name: str, parent=None):
        super().__init__(parent)
        self._client = client
        self._conversation = conversation
        self._pet_name = pet_name

        self.setWindowTitle(f"AI 어시스턴트 — {pet_name}")
        self.setFixedSize(450, 600)
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._text = QTextBrowser()
        self._text.setReadOnly(True)
        self._text.setOpenExternalLinks(False)
        layout.addWidget(self._text)

        input_row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("메시지를 입력하세요...")
        self._input.returnPressed.connect(self._on_send)
        input_row.addWidget(self._input)

        self._send_btn = QPushButton("전송")
        self._send_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self._send_btn)
        layout.addLayout(input_row)

        if self._client:
            self._client.chunk_received.connect(self._on_chunk)
            self._client.reply_ready.connect(self._on_reply)
            self._client.error_occurred.connect(self._on_error)

    def _on_send(self) -> None:
        text = self._input.text().strip()
        if not text or not self._client:
            return
        self._input.clear()
        self._send_btn.setEnabled(False)

        self._conversation.add_user(text)
        self._append_message("user", text)
        self._append_role_header("assistant")
        self._client.request(self._conversation.messages, system=None)

    def _on_chunk(self, chunk: str) -> None:
        cursor = self._text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(chunk)
        self._text.setTextCursor(cursor)
        self._text.ensureCursorVisible()

    def _on_reply(self, text: str) -> None:
        self._conversation.add_assistant(text)
        self._send_btn.setEnabled(True)
        self._input.setFocus()
        # 줄 구분
        cursor = self._text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText("\n\n")
        self._text.setTextCursor(cursor)

    def _on_error(self, msg: str) -> None:
        self._append_message("system", f"오류: {msg}")
        self._send_btn.setEnabled(True)

    def _append_role_header(self, role: str) -> None:
        label = self._pet_name if role == "assistant" else "나"
        cursor = self._text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(f"<b>{label}:</b> ")
        self._text.setTextCursor(cursor)

    def _append_message(self, role: str, text: str) -> None:
        if role == "user":
            label = "나"
            color = "#1155CC"
        elif role == "assistant":
            label = self._pet_name
            color = "#333333"
        else:
            label = "시스템"
            color = "#AA0000"
        cursor = self._text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(
            f'<b style="color:{color}">{label}:</b> {text}<br><br>'
        )
        self._text.setTextCursor(cursor)
        self._text.ensureCursorVisible()

    def closeEvent(self, event):
        if self._client:
            try:
                self._client.chunk_received.disconnect(self._on_chunk)
                self._client.reply_ready.disconnect(self._on_reply)
                self._client.error_occurred.disconnect(self._on_error)
            except RuntimeError:
                pass
        self.dialog_closed.emit()
        super().closeEvent(event)
