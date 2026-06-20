from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QLabel, QLineEdit, QSlider, QVBoxLayout,
)
from PySide6.QtCore import Qt

from core.config import Config

_MODELS = [
    ("claude-haiku-4-5",  "Haiku 4.5  (빠름, 저렴)"),
    ("claude-sonnet-4-6", "Sonnet 4.6 (균형)"),
    ("claude-opus-4-8",   "Opus 4.8   (고성능)"),
]


class SettingsDialog(QDialog):
    settings_saved = Signal(object)  # AppConfig

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("설정")
        self.setMinimumWidth(360)

        form = QFormLayout()

        self._name_edit = QLineEdit(config.data.pet_name)
        form.addRow("펫 이름:", self._name_edit)

        self._model_combo = QComboBox()
        for model_id, label in _MODELS:
            self._model_combo.addItem(label, userData=model_id)
        current_idx = next(
            (i for i, (mid, _) in enumerate(_MODELS) if mid == config.data.model), 0
        )
        self._model_combo.setCurrentIndex(current_idx)
        form.addRow("모델:", self._model_combo)

        self._rate_label = QLabel(str(config.data.hunger_decrease_rate))
        self._rate_slider = QSlider(Qt.Orientation.Horizontal)
        self._rate_slider.setRange(1, 30)
        self._rate_slider.setValue(config.data.hunger_decrease_rate)
        self._rate_slider.setTickInterval(5)
        self._rate_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._rate_slider.valueChanged.connect(
            lambda v: self._rate_label.setText(str(v))
        )
        from PySide6.QtWidgets import QHBoxLayout, QWidget
        rate_row = QWidget()
        hl = QHBoxLayout(rate_row)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self._rate_slider)
        hl.addWidget(self._rate_label)
        form.addRow("배고픔 감소율 (시간당):", rate_row)

        self._api_key_edit = QLineEdit()
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_edit.setPlaceholderText("변경 시에만 입력 (저장됨)")
        form.addRow("API 키:", self._api_key_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        cfg = self._config.data
        cfg.pet_name = self._name_edit.text().strip() or cfg.pet_name
        cfg.model = self._model_combo.currentData()
        cfg.hunger_decrease_rate = self._rate_slider.value()
        self._config.save()

        new_key = self._api_key_edit.text().strip()
        if new_key:
            try:
                import keyring
                keyring.set_password("pc-pet", "anthropic_api_key", new_key)
            except Exception:
                pass

        self.settings_saved.emit(cfg)
        self.accept()
