from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout
)


class TalkInputDialog(QDialog):
    talk_submitted = Signal(str)

    def __init__(self, pet_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{pet_name}에게 말 걸기")
        self.setFixedSize(300, 110)
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(QLabel(f"💬 {pet_name}에게 한 마디:"))

        self._input = QLineEdit()
        self._input.setPlaceholderText("메시지 입력...")
        self._input.returnPressed.connect(self._on_submit)
        layout.addWidget(self._input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        send_btn = QPushButton("전송")
        send_btn.clicked.connect(self._on_submit)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(send_btn)
        layout.addLayout(btn_row)

    def _on_submit(self) -> None:
        text = self._input.text().strip()
        if text:
            self.talk_submitted.emit(text)
            self.accept()
