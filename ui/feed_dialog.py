from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)


class FeedDialog(QDialog):
    feed_confirmed = Signal()

    def __init__(self, hunger: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("먹이주기")
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self.setFixedSize(240, 130)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        info = QLabel(f"현재 배고픔: {hunger} / 100\n먹이를 줄까요? (+50, 최대 100)")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        feed_btn = QPushButton("🍖 먹이주기")
        feed_btn.setDefault(True)
        feed_btn.clicked.connect(self._on_feed)
        btn_row.addWidget(feed_btn)

        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)

    def _on_feed(self) -> None:
        self.feed_confirmed.emit()
        self.accept()
