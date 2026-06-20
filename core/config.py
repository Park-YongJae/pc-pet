from __future__ import annotations
import json
import sys
from pathlib import Path
from pydantic import BaseModel


class AppConfig(BaseModel):
    pet_name: str = "냥이"
    model: str = "claude-haiku-4-5"
    hunger_decrease_rate: int = 10
    sound_enabled: bool = False
    always_on_top: bool = True
    movement_area: list[list[float]] = []  # [[x, y], ...] 빈 리스트 = 제한 없음


def _data_dir() -> Path:
    # PyInstaller .exe로 실행 중이면 exe 옆 data/ 사용
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "data"
    return Path(__file__).parent.parent / "data"


_CONFIG_PATH = _data_dir() / "config.json"


class Config:
    def __init__(self):
        self._data: AppConfig = self._load()

    def _load(self) -> AppConfig:
        if not _CONFIG_PATH.exists():
            default = AppConfig()
            self._write(default)
            return default
        try:
            with open(_CONFIG_PATH, encoding="utf-8") as f:
                return AppConfig(**json.load(f))
        except Exception:
            return AppConfig()

    def _write(self, cfg: AppConfig) -> None:
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg.model_dump(), f, ensure_ascii=False, indent=2)

    @property
    def data(self) -> AppConfig:
        return self._data

    def save(self) -> None:
        self._write(self._data)
