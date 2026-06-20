import sys
import logging

from dotenv import load_dotenv
load_dotenv()

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QColor

from core.app import App

logging.basicConfig(level=logging.WARNING)

_MUTEX = None  # 프로세스 종료 시까지 뮤텍스 핸들 유지


def _ensure_single_instance() -> None:
    global _MUTEX
    if sys.platform != "win32":
        return
    import ctypes
    _MUTEX = ctypes.windll.kernel32.CreateMutexW(None, False, "PC-PET-SingleInstance")
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        sys.exit(0)


def _make_tray_icon() -> QIcon:
    px = QPixmap(16, 16)
    px.fill(QColor("#FF8C00"))
    return QIcon(px)


def main() -> None:
    _ensure_single_instance()
    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(False)

    app = App()

    tray = QSystemTrayIcon(_make_tray_icon(), qt_app)
    menu = QMenu()

    show_action = menu.addAction("보이기/숨기기")
    show_action.triggered.connect(
        lambda: app._window.hide() if app._window.isVisible()
        else app._window.show()
    )
    settings_action = menu.addAction("설정")
    settings_action.triggered.connect(app.open_settings)
    menu.addSeparator()
    quit_action = menu.addAction("종료")
    quit_action.triggered.connect(qt_app.quit)

    tray.setContextMenu(menu)
    tray.setToolTip("PC-PET")
    tray.show()

    qt_app.aboutToQuit.connect(app.save_state)

    app.run()
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
