"""Win32 Native Drag-and-Drop and UIPI Elevation Bridge.

Provides a robust, dual-layer drag-and-drop mechanism for Windows desktop
environments. In addition to Qt's standard OLE drag-and-drop, this module
wires low-level Win32 WM_DROPFILES message filters and a native event filter
to bypass Windows UIPI (User Interface Privilege Isolation) restrictions when
the application is run with elevated privileges or installed in Program Files.
"""

from __future__ import annotations

import sys
import time
from typing import Any, List, Optional

from PySide6.QtCore import QAbstractNativeEventFilter, QObject, QTimer
from PySide6.QtWidgets import QApplication, QWidget

# Win32 Constants
WM_COPYDATA = 0x004A
WM_COPYGLOBALDATA = 0x0049
WM_DROPFILES = 0x0233
MSGFLT_ALLOW = 1


class Win32DropNativeEventFilter(QAbstractNativeEventFilter):
    """Native event filter intercepting Win32 WM_DROPFILES messages.

    Bypasses UIPI elevation barriers and Qt OLE suppression by reading
    dropped file paths directly from the shell HDROP handle.
    """

    def __init__(self, target_window: QWidget):
        super().__init__()
        self.target_window = target_window
        self._last_drop_time = 0.0
        self._last_drop_files: List[str] = []

    def nativeEventFilter(self, event_type: Any, message: Any) -> tuple[bool, int]:
        if sys.platform != "win32" or not message:
            return False, 0

        # We only process Windows generic/dispatcher messages
        if event_type not in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            return False, 0

        try:
            import ctypes
            from ctypes import wintypes

            class _MSG(ctypes.Structure):
                _fields_ = [
                    ("hwnd", wintypes.HWND),
                    ("message", wintypes.UINT),
                    ("wParam", wintypes.WPARAM),
                    ("lParam", wintypes.LPARAM),
                    ("time", wintypes.DWORD),
                    ("pt_x", wintypes.LONG),
                    ("pt_y", wintypes.LONG),
                ]

            addr = int(message)
            if not addr:
                return False, 0

            msg = _MSG.from_address(addr)
            if msg.message == WM_DROPFILES:
                hdrop = msg.wParam
                shell32 = ctypes.windll.shell32
                file_count = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
                paths: List[str] = []
                for i in range(file_count):
                    buf_len = shell32.DragQueryFileW(hdrop, i, None, 0)
                    if buf_len > 0:
                        buf = ctypes.create_unicode_buffer(buf_len + 1)
                        shell32.DragQueryFileW(hdrop, i, buf, buf_len + 1)
                        if buf.value:
                            paths.append(buf.value)
                shell32.DragFinish(hdrop)

                # Deduplicate rapid duplicate events (e.g. within 0.5s)
                now = time.time()
                if paths and (now - self._last_drop_time > 0.5 or paths != self._last_drop_files):
                    self._last_drop_time = now
                    self._last_drop_files = list(paths)
                    if hasattr(self.target_window, "_handle_dropped_media_or_project"):
                        # Defer slightly to avoid blocking the Win32 message pump
                        QTimer.singleShot(
                            0,
                            lambda p=paths: self.target_window._handle_dropped_media_or_project(p),
                        )
                return True, 0
        except Exception:
            pass

        return False, 0


def init_ole_sta() -> bool:
    """Ensure early Single-Threaded Apartment (STA) COM initialization on Windows.

    Must be called before any third-party native libraries can initialize COM
    in Multi-Threaded Apartment (MTA) mode, which would break Qt OLE drag-and-drop.
    """
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        # OleInitialize initializes COM as STA and enables OLE services
        hr = ctypes.windll.ole32.OleInitialize(None)
        # S_OK (0) or S_FALSE (1) indicates success
        return hr in (0, 1)
    except Exception:
        return False


def setup_win32_window_drag_drop(window: QWidget) -> Optional[Win32DropNativeEventFilter]:
    """Configure Win32 message filters and native drop handler for the main window.

    Enables DragAcceptFiles, unblocks WM_DROPFILES/WM_COPYDATA across UIPI privilege
    levels via ChangeWindowMessageFilterEx, and installs a QAbstractNativeEventFilter.
    """
    if sys.platform != "win32" or window is None:
        return None

    try:
        import ctypes

        hwnd = int(window.winId())
        if not hwnd:
            return None

        # 1. Enable Win32 DragAcceptFiles for the native window handle
        ctypes.windll.shell32.DragAcceptFiles(hwnd, True)

        # 2. Whitelist drop messages through Windows UIPI filter (for elevated processes)
        user32 = ctypes.windll.user32
        if hasattr(user32, "ChangeWindowMessageFilterEx"):
            user32.ChangeWindowMessageFilterEx(hwnd, WM_DROPFILES, MSGFLT_ALLOW, None)
            user32.ChangeWindowMessageFilterEx(hwnd, WM_COPYDATA, MSGFLT_ALLOW, None)
            user32.ChangeWindowMessageFilterEx(hwnd, WM_COPYGLOBALDATA, MSGFLT_ALLOW, None)

        # 3. Install QAbstractNativeEventFilter on QApplication instance
        app = QApplication.instance()
        if app is not None:
            native_filter = Win32DropNativeEventFilter(window)
            app.installNativeEventFilter(native_filter)
            return native_filter
    except Exception:
        pass

    return None
