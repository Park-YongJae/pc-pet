# PC-PET 구현 계획

PRD.md와 CLAUDE.md 기반. 각 Phase는 독립적으로 커밋 가능한 기능 단위로 구성.

---

## Phase 1 — 기반 인프라 + 투명 윈도우 + 알/부화

### 1-1. 프로젝트 뼈대 & 설정 시스템
- [x] 폴더 구조 생성 (`core/`, `ui/`, `ai/`, `game/`, `assets/`, `data/`)
- [x] `requirements.txt` 확정 (`PySide6`, `anthropic`, `keyring`, `pywin32 ; win32`)
- [x] `data/config.json` 초기 파일 생성
- [x] `core/config.py` — config.json 로드/저장 클래스

### 1-2. 플랫폼 추상화
- [x] `core/platform_utils.py` — `set_click_through()` Windows/macOS 분기
- [x] Windows: `setMask` + `WM_NCHITTEST` 기반 클릭 통과 (win32 대신 더 안정적인 방식)
- [ ] macOS: `ctypes` + `NSWindow.setIgnoresMouseEvents_`

### 1-3. 투명 오버레이 윈도우
- [x] `ui/pet_window.py` — `FramelessWindowHint | WindowStaysOnTopHint | Tool`
- [x] `WA_TranslucentBackground` 설정
- [x] 투명 픽셀 클릭 통과 (`setMask`로 OS 레벨 처리)
- [x] 드래그 이동 (`mouseMoveEvent`)

### 1-4. 알 화면 & 부화 애니메이션
- [x] `ui/sprite_renderer.py` — QPainter 기반 도형 렌더러
- [x] EGG 상태: 흰 타원 + 살짝 흔들림 (QPropertyAnimation)
- [x] HATCHING 상태: 균열 라인 애니메이션 → 캐릭터 등장
- [x] 알 클릭 시 부화 트리거

### 1-5. 10종 캐릭터 도형 정의 + IDLE 렌더링
- [x] `game/pet_stats.py` — `PET_TYPES` 딕셔너리 (1~10번, 도형·색)
- [x] IDLE 도형 렌더링 (종별 눈 깜빡임 애니메이션)
- [x] 랜덤 펫 타입 선택 로직

### 1-6. 화면 배회 이동
- [x] `game/walk_controller.py` — 2~5초마다 랜덤 방향 이동 (80px/초)
- [x] 화면 경계 감지 + 방향 전환
- [x] 좌우 이동 시 캐릭터 방향 반전 (scaleX flip)
- [x] 드래그 중 배회 일시 정지, 완료 후 재개
- [x] 사용자 정의 이동 영역 (폴리곤) — `ui/area_editor.py` + `walk_controller.set_area()`

### 1-7. 앱 진입점
- [x] `main.py` — `QApplication` + 시스템 트레이 아이콘 초기화
- [x] `core/app.py` — 앱 초기화, 모듈 연결
- [x] 종료 시 `pet_state.json` 저장

**커밋 단위**: `feat: 투명 오버레이 윈도우`, `feat: 알/부화 시스템`, `feat: 10종 캐릭터 도형`, `feat: 화면 배회 이동`

---

## Phase 2 — FSM + 게임 시스템

### 2-1. 캐릭터 FSM
- [x] `core/state_machine.py` — 상태 enum + 전환 로직
  - 상태: `EGG, HATCHING, IDLE, HUNGRY, WALKING, REACT_HAPPY, REACT_ANNOYED, REACT_ANGRY, EATING, THINKING, TALKING, DEAD`
- [x] 상태 전환 시 `sprite_renderer` 업데이트 연동

### 2-2. 클릭 반응 시스템
- [x] 클릭 카운터 (세션 내, 일정 시간 후 리셋)
- [x] 1~3회 → `REACT_HAPPY` (스트레스 -5)
- [x] 4~7회 → `REACT_ANNOYED` (스트레스 +3)
- [x] 8회+ → `REACT_ANGRY` (스트레스 +8)
- [x] 상태별 도형 시각 표현 (`sprite_renderer`에 구현)

### 2-3. 배고픔 시스템
- [x] `game/hunger_timer.py` — QTimer, 1시간마다 `hunger -= rate` (기본 10)
- [x] `hunger < 70` → FSM `HUNGRY` 상태 진입 (주황 테두리 + 밥그릇 텍스트)
- [x] `hunger < 30` → 스트레스 +3/시간 연동
- [x] `hunger == 0` → `DEAD` 전환
- [x] `ui/feed_dialog.py` — 먹이주기 팝업 (hunger +50, 최대 100, 스트레스 -10)
- [x] EATING 애니메이션 재생 후 IDLE 복귀

### 2-4. 스트레스 시스템
- [x] `game/stress_manager.py` — 스트레스 증감 + 단계별 시각 표현 트리거
- [x] 방치 30분마다 +5 (QTimer)
- [x] 스트레스 단계별 테두리 색 변경 (0~30: 기본, 31~60: 노랑, 61~90: 빨강, 91~99: 흔들림)
- [x] 가끔 "..." / "ㅠㅠ" / "저 힘들어요..." 말풍선 트리거 (Phase 3 말풍선 구현 후)
- [x] `stress == 100` → `DEAD` 전환

### 2-5. 똥 시스템
- [x] `game/poop_system.py` — 1~3시간 랜덤 타이머로 똥 생성
- [x] 화면 내 최대 3개 동시 표시 (갈색 원 or 💩 텍스트)
- [x] 똥 클릭 → 제거 + 스트레스 -8
- [x] 똥 방치 30분마다 개당 스트레스 +5
- [x] `pet_state.json`에 똥 위치 저장/로드

### 2-6. 사망 & 부활 사이클
- [x] DEAD 상태: 캐릭터 회색 + X눈 + 쓰러짐 애니메이션
- [x] `total_deaths` 누적 기록
- [x] DEAD → EGG 자동 전환
- [x] 부활 시 hunger=100, stress=0, 새 랜덤 펫 타입 선택

### 2-7. 상태 저장/로드
- [x] 종료 시 `data/pet_state.json` 저장 (hunger, stress, pet_type, poops, last_saved)
- [x] 재실행 시 경과 시간 계산 → 배고픔 차감 반영

**커밋 단위**: `feat: FSM 상태 기계`, `feat: 클릭 반응 시스템`, `feat: 배고픔 시스템`, `feat: 스트레스 시스템`, `feat: 똥 시스템`, `feat: 사망/부활 사이클`

---

## Phase 3 — AI 대화 + 말풍선

### 3-1. Claude API 클라이언트
- [x] `ai/claude_client.py` — `anthropic.Anthropic` 래퍼
- [x] 스트리밍 응답: `client.messages.stream(...)`
- [x] API 키 없을 때 AI 기능 비활성화 (나머지 정상 작동)
- [x] `ai/conversation.py` — 세션 내 멀티턴 히스토리 관리

### 3-2. 말풍선 위젯
- [x] `ui/speech_bubble.py` — 최대 350×150px, border-radius 12px, 80% 불투명 흰색
- [x] 타이핑 효과 (글자 하나씩 나타남, QTimer)
- [x] 캐릭터 위 좌측 기본, 화면 끝 감지 시 방향 자동 전환
- [x] 닫기 버튼 [X]

### 3-3. 펫 대화 모드
- [x] 우클릭 → "펫에게 말 걸기" → 소형 입력창 팝업
- [x] FSM: IDLE → THINKING (API 대기 중 "..." 점 애니메이션) → TALKING
- [x] 시스템 프롬프트: 100자 이내 귀여운 답변, hunger/stress 상태 주입
- [x] 답변 수신 완료 → 말풍선 표시 + 스트레스 -5
- [x] 말풍선 닫기 → IDLE 복귀

### 3-4. AI 어시스턴트 모드
- [x] `ui/chat_dialog.py` — 450×600px 확장 채팅창
- [x] 스크롤 가능한 긴 응답 표시
- [x] 시스템 프롬프트 없음 (Claude 전체 능력)
- [x] 채팅창 열린 동안 TALKING 유지, 닫으면 IDLE 복귀

**커밋 단위**: `feat: Claude API 연동`, `feat: 말풍선 위젯`, `feat: 펫 대화 모드`, `feat: AI 어시스턴트 모드`

---

## Phase 4 — UI 마무리 + 시스템 트레이 + 설정

### 4-1. 우클릭 컨텍스트 메뉴
- [x] `pet_window.py`에 `contextMenuEvent` 구현
- [x] 메뉴: 먹이주기 / 펫에게 말 걸기 / AI 어시스턴트 / 청소 / 구분선 / 설정 / 종료
- [x] "청소" → 모든 똥 일괄 제거

### 4-2. 시스템 트레이
- [x] `main.py`에 `QSystemTrayIcon` 설정
- [x] 트레이 우클릭 메뉴 (설정, 종료)
- [x] 창 숨기기/보이기 토글

### 4-3. 설정창
- [x] `ui/settings_dialog.py` — API 키 입력 (마스킹), 모델 선택, 배고픔 감소율 슬라이더, 펫 이름 변경
- [x] API 키 → `keyring`으로 OS 키체인 저장/불러오기
- [x] 설정 변경 → `config.json` 즉시 저장

**커밋 단위**: `feat: 우클릭 메뉴`, `feat: 시스템 트레이`, `feat: 설정창`

---

## Phase 5 — 통합 테스트 & 안정화

### 5-1. 통합 테스트
- [x] Windows 10/11 전체 흐름 테스트 (알 → 부화 → 배회 → 먹이주기 → AI 대화 → 사망 → 재시작)
- [x] 재시작 후 상태 복원 (경과 시간 배고픔 차감) 검증
- [x] 화면 가장자리 경계 처리 확인
- [x] 투명 클릭 통과 동작 확인

### 5-2. 안정화
- [x] API 오류 / 네트워크 끊김 처리 (`ai/claude_client.py` — 오류 분류 + 한국어 메시지)
- [x] `pet_state.json` 손상 시 초기화 fallback (`.json.bak` 백업 후 리셋)
- [x] 메모리 누수 점검 (QTimer, 스트리밍 스레드) — `thread.finished → worker.deleteLater` 추가

### 5-3. 이후 작업 (Post-MVP)
- [x] 실제 스프라이트 PNG 교체 (`assets/sprites/`)
- [x] 캐릭터가 먼저 말 걸기 (`game/random_event.py` — 20~40분 간격 랜덤 메시지)
- [x] PyInstaller `.exe` 빌드 (`pc-pet.spec` 스펙 파일 생성)
- [x] macOS 구현 (`_mac_click_through` ctypes ObjC 런타임) — 맥북에서 테스트 필요

---

## 파일-기능 매핑 요약

| 파일 | Phase | 주요 기능 |
|---|---|---|
| `core/config.py` | 1-1 | config.json 로드/저장 |
| `core/platform_utils.py` | 1-2 | 클릭 통과 Windows/macOS 분기 |
| `core/state_machine.py` | 2-1 | FSM 상태 전환 |
| `core/app.py` | 1-7 | 앱 초기화 |
| `ui/pet_window.py` | 1-3 | 투명 오버레이, 드래그, 우클릭 메뉴 |
| `ui/sprite_renderer.py` | 1-4~5 | QPainter 도형 렌더링, 애니메이션 |
| `ui/speech_bubble.py` | 3-2 | 말풍선 타이핑 위젯 |
| `ui/chat_dialog.py` | 3-4 | AI 어시스턴트 채팅창 |
| `ui/feed_dialog.py` | 2-3 | 먹이주기 팝업 |
| `ui/settings_dialog.py` | 4-3 | 설정창, keyring 연동 |
| `ai/claude_client.py` | 3-1 | anthropic 스트리밍 래퍼 |
| `ai/conversation.py` | 3-1 | 멀티턴 히스토리 |
| `game/pet_stats.py` | 1-5 | PET_TYPES 딕셔너리, 수치 관리 |
| `game/hunger_timer.py` | 2-3 | QTimer 배고픔 감소 |
| `game/stress_manager.py` | 2-4 | 스트레스 증감 로직 |
| `game/poop_system.py` | 2-5 | 똥 생성/제거/스트레스 연동 |
| `game/walk_controller.py` | 1-6 | 랜덤 배회 이동, 경계 처리 |
| `main.py` | 1-7 | QApplication, 시스템 트레이 |
