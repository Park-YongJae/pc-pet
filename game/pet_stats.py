import random
from datetime import datetime
from pydantic import BaseModel


PET_TYPES: dict[int, dict] = {
    1: {
        "name": "냥이",
        "body_shape": "circle",
        "body_color": "#FF8C00",
        "ear_shape": "triangle",
        "belly_color": None,
    },
    2: {
        "name": "멍이",
        "body_shape": "circle",
        "body_color": "#8B4513",
        "ear_shape": "droopy",
        "belly_color": None,
    },
    3: {
        "name": "토순이",
        "body_shape": "circle",
        "body_color": "#F5F5F5",
        "ear_shape": "long",
        "belly_color": "#FFB6C1",
    },
    4: {
        "name": "삐약이",
        "body_shape": "circle",
        "body_color": "#FFD700",
        "ear_shape": "none",
        "belly_color": None,
    },
    5: {
        "name": "곰돌이",
        "body_shape": "circle",
        "body_color": "#D2B48C",
        "ear_shape": "round",
        "belly_color": "#F5DEB3",
    },
    6: {
        "name": "펭귄",
        "body_shape": "oval",
        "body_color": "#1C1C1C",
        "ear_shape": "none",
        "belly_color": "#FFFFFF",
    },
    7: {
        "name": "용이",
        "body_shape": "circle",
        "body_color": "#228B22",
        "ear_shape": "horn",
        "belly_color": "#90EE90",
    },
    8: {
        "name": "유령",
        "body_shape": "drop",
        "body_color": "#F0F0F0",
        "ear_shape": "none",
        "belly_color": None,
    },
    9: {
        "name": "로봇",
        "body_shape": "rect",
        "body_color": "#A9A9A9",
        "ear_shape": "none",
        "belly_color": "#C0C0C0",
    },
    10: {
        "name": "악마",
        "body_shape": "circle",
        "body_color": "#DC143C",
        "ear_shape": "horn",
        "belly_color": None,
    },
}


def select_random_type() -> int:
    return random.choice(list(PET_TYPES.keys()))


class PetState(BaseModel):
    pet_type: int = 1
    is_alive: bool = True
    hunger: int = 100
    stress: int = 0
    last_saved: str = ""
    total_deaths: int = 0
    poops: list = []

    def stamp(self) -> None:
        self.last_saved = datetime.now().isoformat()
