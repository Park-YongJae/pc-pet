# PC-PET — Claude Code Context

## 프로젝트 개요

Windows 데스크탑 가상 펫 애플리케이션. 투명 오버레이 윈도우 위에 도형 캐릭터(추후 스프라이트)가 표시되며, 배고픔·스트레스 시뮬레이션과 Claude AI 대화 기능을 갖춘다.

## 기술 스택

- **언어**: Python 3.11+
- **UI**: PySide6 (Qt 6.x) — 투명 오버레이, 항상 위 표시, QPainter 렌더링
- **AI**: anthropic SDK (`claude-haiku-4-5` 기본)
- **플랫폼 추상화**: `core/platform_utils.py` — Windows(pywin32) / macOS(ctypes+Cocoa) 분기
- **API 키 저장**: `keyring` — OS 키체인에 암호화 저장 (Windows: Credential Manager, macOS: Keychain)
- **설정**: JSON 파일 (`data/config.json`)

## 폴더 구조

```
pc-pet/
├── main.py                  # 진입점, QApplication + 시스템 트레이
├── core/
│   ├── app.py               # 앱 초기화
│   ├── config.py            # config.json 로드/저장
│   └── state_machine.py     # 캐릭터 FSM
├── ui/
│   ├── pet_window.py        # 메인 투명 오버레이 윈도우
│   ├── sprite_renderer.py   # 도형/스프라이트 렌더링 + 애니메이션
│   ├── speech_bubble.py     # 말풍선 위젯
│   ├── chat_dialog.py       # AI 대화창 (펫 모드 + 어시스턴트 모드)
│   ├── feed_dialog.py       # 먹이주기 창
│   └── settings_dialog.py   # 설정창 (API 키, 모델, 이름 등)
├── ai/
│   ├── claude_client.py     # anthropic SDK 래퍼, 스트리밍 응답
│   └── conversation.py      # 대화 히스토리 (세션 내)
├── game/
│   ├── pet_stats.py         # hunger(0~100), stress(0~100) 관리
│   ├── hunger_timer.py      # 1시간당 10 감소 타이머
│   ├── stress_manager.py    # 스트레스 증감 로직
│   ├── poop_system.py       # 똥 생성(1~3시간 랜덤)·제거·스트레스 연동
│   └── walk_controller.py   # 화면 전체 배회 랜덤 이동, 경계 처리
├── assets/
│   ├── sprites/             # PNG (현재 비어 있음, 도형으로 대체)
│   └── fonts/
├── data/
│   ├── config.json          # 앱 설정
│   └── pet_state.json       # 펫 상태 (git 제외)
└── requirements.txt
```

## 핵심 설계 원칙

### 투명 오버레이 윈도우
```python
flags = (Qt.WindowType.FramelessWindowHint |
         Qt.WindowType.WindowStaysOnTopHint |
         Qt.WindowType.Tool)
widget.setWindowFlags(flags)
widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
```
- 비캐릭터 영역(투명 픽셀) 클릭은 바탕화면으로 통과
- 픽셀 알파값 체크 후 `event.ignore()` 처리

### 플랫폼 추상화 (`core/platform_utils.py`)
플랫폼별 네이티브 API를 이 파일에 집중. 다른 모듈은 이 함수만 호출.

```python
import platform

def set_click_through(window, enable: bool):
    if platform.system() == "Windows":
        _windows_click_through(window, enable)
    elif platform.system() == "Darwin":
        _mac_click_through(window, enable)

def _windows_click_through(window, enable):
    import win32gui, win32con
    hwnd = int(window.winId())
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    if enable:
        style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
    else:
        style &= ~win32con.WS_EX_TRANSPARENT
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)

def _mac_click_through(window, enable):
    import ctypes, ctypes.util
    objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
    # NSWindow.setIgnoresMouseEvents_(enable)
```

`requirements.txt`에서 `pywin32`는 Windows 전용으로 조건부 설치:
```
pywin32==306 ; sys_platform == "win32"
```

### 캐릭터 FSM 상태 목록
```
EGG → HATCHING → IDLE
IDLE ↔ WALKING (랜덤 배회)
IDLE → REACT_HAPPY / REACT_ANNOYED / REACT_ANGRY (클릭 횟수)
IDLE/HUNGRY → EATING → IDLE (먹이주기)
배고픔<70 → HUNGRY 표시
배고픔=0 또는 스트레스=100 → DEAD → EGG
IDLE → THINKING → TALKING → IDLE (AI 대화)
```

### 사망 조건
- `hunger == 0` OR `stress == 100` → DEAD 상태 전환

### 스트레스 증가 원인
- 방치 30분마다 +5
- REACT_ANNOYED +3, REACT_ANGRY +8
- 똥 방치 30분마다 개당 +5
- 배고픔 < 30일 때 +3/시간

### 스트레스 감소 원인
- REACT_HAPPY -5, EATING 완료 -10, AI 대화 -5, 똥 제거 -8

### 10종 펫 (MVP 도형 표현)
인덱스 1~10, 각각 다른 도형·색상 조합. `pet_stats.py`에 `PET_TYPES` 딕셔너리로 정의.

### AI 클라이언트
```python
# ai/claude_client.py
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
# 스트리밍: client.messages.stream(...)
# 펫 모드: system prompt로 100자 이내 귀여운 답변 강제
# 어시스턴트 모드: system prompt 없음
```

## 데이터 파일

**data/config.json** — 앱 설정 (git 포함)
```json
{
  "pet_name": "냥이",
  "model": "claude-haiku-4-5",
  "hunger_decrease_rate": 10,
  "sound_enabled": false,
  "always_on_top": true
}
```

**data/pet_state.json** — 런타임 상태 (git 제외)
```json
{
  "pet_type": 1,
  "is_alive": true,
  "hunger": 100,
  "stress": 0,
  "last_saved": "ISO8601",
  "total_deaths": 0,
  "poops": []
}
```

## 개발 규칙

- 주석은 WHY가 명확할 때만 작성 (WHAT 설명 주석 금지)
- 에러 처리는 시스템 경계(API 호출, 파일 I/O)에만
- MVP 우선: 스프라이트 없이 도형으로 먼저 동작 확인 후 교체
- **커밋은 기능 단위로 분리** (예: 투명 윈도우, 클릭 반응, 배고픔 시스템, AI 연동 등 각각 별도 커밋)
- **개발은 항상 `PLAN.md` 순서를 따라 진행** — 항목 완료 시 즉시 `- [ ]` → `- [x]` 체크

## 개발 환경 시작

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## GitHub

https://github.com/Park-YongJae/pc-pet
