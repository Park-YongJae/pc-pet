from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QPolygon, QFont, QKeyEvent
)
from PySide6.QtWidgets import QWidget, QApplication, QPushButton

_FILL   = QColor(100, 149, 237, 70)
_BORDER = QColor(100, 149, 237, 220)
_VERTEX = QColor(255, 210, 0)
_VERTEX_OTHERS = QColor(100, 149, 237)
_PREVIEW = QColor(220, 220, 220, 160)


class AreaEditor(QWidget):
    """전체화면 투명 오버레이. 클릭으로 꼭짓점을 추가해 이동 영역을 정의한다."""

    area_confirmed = Signal(list)  # [(x, y), ...] — 빈 리스트 = 영역 해제

    def __init__(self, existing_points: list[list[float]] | None = None, parent=None):
        super().__init__(parent)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self._vertices: list[QPoint] = []
        if existing_points:
            self._vertices = [QPoint(int(p[0]), int(p[1])) for p in existing_points]

        self._cursor = QPoint(0, 0)

        self._setup_buttons(screen)

    # ── 버튼 ──────────────────────────────────────────────────────

    def _setup_buttons(self, screen) -> None:
        btn_y = screen.height() - 56
        cx = screen.width() // 2

        specs = [
            ("✓  완료",   -155, self._confirm),
            ("↺  초기화", -50,  self._clear),
            ("✕  취소",    55,  self.close),
        ]
        for label, offset, slot in specs:
            btn = QPushButton(label, self)
            btn.setFixedSize(90, 36)
            btn.move(cx + offset, btn_y)
            btn.clicked.connect(slot)
            btn.setStyleSheet(
                "QPushButton { background: rgba(30,30,30,200); color: white;"
                "border: 1px solid #666; border-radius: 6px; font-size: 12px; }"
                "QPushButton:hover { background: rgba(60,60,60,220); }"
            )

    # ── 마우스 / 키보드 ────────────────────────────────────────────

    def mouseMoveEvent(self, event):
        self._cursor = event.position().toPoint()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._vertices.append(event.position().toPoint())
            self.update()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.close()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirm()
        elif key == Qt.Key.Key_Backspace and self._vertices:
            self._vertices.pop()
            self.update()

    # ── 페인트 ─────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 반투명 어두운 배경 (편집 모드 표시)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 55))

        n = len(self._vertices)

        # 폴리곤 채우기 (꼭짓점 3개 이상)
        if n >= 3:
            poly = QPolygon(self._vertices)
            painter.setBrush(QBrush(_FILL))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(poly)

        # 변(edge) 그리기
        painter.setPen(QPen(_BORDER, 2))
        for i in range(n - 1):
            painter.drawLine(self._vertices[i], self._vertices[i + 1])
        if n >= 3:
            painter.drawLine(self._vertices[-1], self._vertices[0])

        # 미리보기 선 (마지막 꼭짓점 → 커서)
        if n > 0:
            painter.setPen(QPen(_PREVIEW, 1, Qt.PenStyle.DashLine))
            painter.drawLine(self._vertices[-1], self._cursor)
            if n >= 2:
                painter.drawLine(self._vertices[0], self._cursor)

        # 꼭짓점 마커
        painter.setPen(Qt.PenStyle.NoPen)
        for i, v in enumerate(self._vertices):
            color = _VERTEX if i == 0 else _VERTEX_OTHERS
            painter.setBrush(QBrush(color))
            painter.drawEllipse(v, 7, 7)
            # 번호 표시
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.drawText(v.x() - 4, v.y() + 4, str(i + 1))
            painter.setPen(Qt.PenStyle.NoPen)

        # 안내 텍스트
        painter.setPen(QPen(QColor(255, 255, 255, 220)))
        painter.setFont(QFont("맑은 고딕", 11))
        hint = (
            f"좌클릭으로 꼭짓점 추가  |  꼭짓점: {n}개"
            "  |  Backspace: 되돌리기  |  Enter: 완료  |  Esc: 취소"
        )
        painter.drawText(
            self.rect().adjusted(0, 18, 0, 0),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            hint,
        )

    # ── 슬롯 ───────────────────────────────────────────────────────

    def _confirm(self) -> None:
        if len(self._vertices) >= 3:
            points = [(v.x(), v.y()) for v in self._vertices]
        else:
            points = []
        self.area_confirmed.emit(points)
        self.close()

    def _clear(self) -> None:
        self._vertices.clear()
        self.update()
