from __future__ import annotations
import platform
import logging

logger = logging.getLogger(__name__)


def init_mac_window(window) -> None:
    """macOS Tool 윈도우의 hidesOnDeactivate를 끔 — 다른 앱 클릭해도 사라지지 않게."""
    if platform.system() != "Darwin":
        return
    try:
        import ctypes
        import ctypes.util
        libobjc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
        libobjc.sel_registerName.restype = ctypes.c_void_p
        libobjc.sel_registerName.argtypes = [ctypes.c_char_p]
        msg = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(
            ("objc_msgSend", libobjc)
        )
        msg_bool = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool)(
            ("objc_msgSend", libobjc)
        )
        ns_view = ctypes.c_void_p(int(window.winId()))
        ns_window = msg(ns_view, libobjc.sel_registerName(b"window"))
        if not ns_window:
            return
        msg_bool(ctypes.c_void_p(ns_window),
                 libobjc.sel_registerName(b"setHidesOnDeactivate:"), False)
    except Exception as e:
        logger.warning("macOS hidesOnDeactivate 설정 실패: %s", e)


def set_click_through(window, enable: bool) -> None:
    sys = platform.system()
    if sys == "Windows":
        _windows_click_through(window, enable)
    elif sys == "Darwin":
        _mac_click_through(window, enable)


def _windows_click_through(window, enable: bool) -> None:
    try:
        import win32gui
        import win32con
        hwnd = int(window.winId())
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if enable:
            style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
        else:
            style &= ~win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
    except Exception as e:
        logger.warning("Windows click-through failed: %s", e)


def _mac_click_through(window, enable: bool) -> None:
    try:
        import ctypes
        import ctypes.util

        libobjc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))

        libobjc.sel_registerName.restype = ctypes.c_void_p
        libobjc.sel_registerName.argtypes = [ctypes.c_char_p]

        # objc_msgSend — 반환값만 있는 호출 (인자 없음)
        msg = ctypes.CFUNCTYPE(
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        )(("objc_msgSend", libobjc))

        # objc_msgSend — bool 인자 호출
        msg_bool = ctypes.CFUNCTYPE(
            None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool
        )(("objc_msgSend", libobjc))

        ns_view = ctypes.c_void_p(int(window.winId()))

        # NSView → NSWindow
        sel_window = libobjc.sel_registerName(b"window")
        ns_window = msg(ns_view, sel_window)
        if not ns_window:
            logger.warning("macOS: NSWindow을 가져올 수 없음")
            return

        # [nsWindow setIgnoresMouseEvents: enable]
        sel_ignore = libobjc.sel_registerName(b"setIgnoresMouseEvents:")
        msg_bool(ctypes.c_void_p(ns_window), sel_ignore, enable)

    except Exception as e:
        logger.warning("macOS click-through 설정 실패: %s", e)
