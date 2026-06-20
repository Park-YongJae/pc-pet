from __future__ import annotations
import random
from datetime import datetime
from pydantic import BaseModel


PET_TYPES: dict[int, dict] = {
    1: {
        "name": "냥이",
        "category": "cute",
        "personality": "도도하고 쿨한 척하지만 사실 관심받고 싶어함. 귀엽다는 말에 약하고 칭찬받으면 티 안 나게 좋아함. 툭툭 내뱉는 듯 짧은 말투.",
    },
    2: {
        "name": "멍이",
        "category": "cute",
        "personality": "항상 신나고 긍정적. 주인을 엄청 좋아해서 말 끝마다 애정 표현을 함. 꼬리 흔드는 표현을 자주 씀.",
    },
    3: {
        "name": "햄토리",
        "category": "cute",
        "personality": "볼살이 빵빵하고 먹는 게 세상에서 제일 중요함. 먹을 것 얘기만 나오면 눈이 반짝임. 귀엽고 통통 튀는 말투.",
    },
    4: {
        "name": "삐약이",
        "category": "cute",
        "personality": "아직 아기라 뭐든 신기하고 신남. 어리숙하고 순수한 말투. '삐약' 같은 의성어를 자주 씀.",
    },
    5: {
        "name": "드래곤",
        "category": "cool",
        "personality": "쿨하고 자신만만함. 강한 척하지만 칭찬받으면 티 안 나게 좋아함. 약간 거만하지만 귀여운 말투.",
    },
    6: {
        "name": "로봇",
        "category": "cool",
        "personality": "감정 표현이 서툴고 논리적. 감정을 수치나 퍼센트로 표현함. 가끔 오류 코드 같은 말을 씀.",
    },
    7: {
        "name": "악마",
        "category": "cool",
        "personality": "짓궂고 장난기 많음. 주인을 약 올리는 걸 좋아하지만 사실은 좋아함. 비꼬는 듯하면서도 귀여운 말투.",
    },
    8: {
        "name": "유니콘",
        "category": "pretty",
        "personality": "화려하고 우아한 것을 사랑함. 꿈·마법·반짝이는 것 얘기를 좋아함. 설레고 감성적인 말투.",
    },
    9: {
        "name": "천사냥",
        "category": "pretty",
        "personality": "착하고 순수함. 항상 주인을 칭찬하고 격려함. 온화하고 부드러운 말투.",
    },
    10: {
        "name": "요정",
        "category": "pretty",
        "personality": "장난기 많고 호기심 넘침. 숲·자연·빛나는 것을 좋아함. 명랑하고 통통 튀는 말투.",
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
