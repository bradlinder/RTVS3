"""Radio & TV Segmenter — Headless Qt / PySide6 Compatibility Engine.

Provides a unified zero-dependency mock shim for PySide6 in headless environments,
ensuring pure business logic, formatting, and unit tests execute cleanly without
requiring an X11/Wayland display server or installed Qt binary packages.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


class MockModule(ModuleType):
    """Dynamic mock module that automatically manufactures nested mock classes and attributes."""

    def __init__(self, name: str):
        super().__init__(name)
        self.__file__ = f"<mock_{name}>"
        self.__spec__ = None
        self.__cached__ = None
        self.__path__ = []

    def __getattr__(self, name: str) -> Any:
        if name == "__file__":
            return f"<mock_{self.__name__}>"
        if name in ("__cached__", "__spec__", "__loader__"):
            return None
        if name == "__path__":
            return []

        class DynamicMock:
            def __init__(self, *args, **kwargs):
                pass

            def __call__(self, *args, **kwargs):
                return self

            def connect(self, *a, **k):
                return None

            def disconnect(self, *a, **k):
                return None

            def emit(self, *a, **k):
                return None

            def __getattr__(self, attr):
                return DynamicMock()

        DynamicMock.__name__ = name
        setattr(self, name, DynamicMock)
        return DynamicMock


class DummyQt:
    """Mock Qt namespace constants."""
    WindowType = type("WindowType", (), {"WindowMaximizeButtonHint": 0x00020000, "Window": 0x00000001})
    AlignmentFlag = type("AlignmentFlag", (), {"AlignCenter": 0x0004, "AlignLeft": 0x0001, "AlignRight": 0x0002})
    Orientation = type("Orientation", (), {"Horizontal": 1, "Vertical": 2})
    CheckState = type("CheckState", (), {"Checked": 2, "Unchecked": 0})
    ItemDataRole = type("ItemDataRole", (), {"UserRole": 256, "DisplayRole": 0})
    AspectRatioMode = type("AspectRatioMode", (), {"KeepAspectRatio": 1, "IgnoreAspectRatio": 0})
    TransformationMode = type("TransformationMode", (), {"SmoothTransformation": 1, "FastTransformation": 0})
    WindowModality = type("WindowModality", (), {"WindowModal": 1, "ApplicationModal": 2, "NonModal": 0})


class DummyQSettings:
    """In-memory dictionary-backed QSettings fallback."""
    _store: dict = {}

    def __init__(self, *a, **k):
        pass

    def value(self, k: str, d: Any = None) -> Any:
        return self._store.get(k, d)

    def setValue(self, k: str, v: Any) -> None:
        self._store[k] = v

    def remove(self, k: str) -> None:
        self._store.pop(k, None)

    def sync(self) -> None:
        pass

    def beginGroup(self, *a):
        pass

    def endGroup(self):
        pass


class DummyQMessageBox:
    """Non-blocking headless QMessageBox stub."""
    StandardButton = type("StandardButton", (), {"Yes": 1, "No": 2, "Ok": 1, "Cancel": 0})

    @staticmethod
    def information(*args, **kwargs) -> int:
        return 1

    @staticmethod
    def warning(*args, **kwargs) -> int:
        return 1

    @staticmethod
    def critical(*args, **kwargs) -> int:
        return 1

    @staticmethod
    def question(*args, **kwargs) -> int:
        return 1


class DummyQApplication:
    """Headless QApplication stub."""

    @staticmethod
    def processEvents() -> None:
        pass

    @staticmethod
    def instance() -> Any:
        return None

    @staticmethod
    def topLevelWidgets() -> list:
        return []


class DummyQHeaderView:
    ResizeMode = type("ResizeMode", (), {"ResizeToContents": 1, "Stretch": 2, "Interactive": 0, "Fixed": 3})


class DummyQAbstractItemView:
    SelectionBehavior = type("SelectionBehavior", (), {"SelectRows": 1})
    SelectionMode = type("SelectionMode", (), {"ExtendedSelection": 3, "SingleSelection": 1, "MultiSelection": 2, "NoSelection": 0})
    EditTrigger = type("EditTrigger", (), {"NoEditTriggers": 0})


class DummyQLineEdit:
    EchoMode = type("EchoMode", (), {"Normal": 0, "Password": 2})


class DummyQFont:
    Weight = type("Weight", (), {"Bold": 75, "Normal": 50})

    def __init__(self, *args, **kwargs):
        pass


def _ensure_pyside6_fallback(force: bool = False) -> bool:
    """Ensures PySide6 modules are importable, installing the zero-dependency mock shim if unavailable."""
    # When explicitly in worker mode or forced, NEVER attempt to import PySide6.
    # In frozen PyInstaller bundles, attempting to import PySide6 when excluded triggers
    # a native libshiboken fatal error (Py_FatalError) that cannot be caught by try/except.
    is_worker = (
        force
        or os.environ.get("RTVS_WORKER_MODE") == "1"
        or "worker" in Path(sys.executable or "").stem.lower()
    )
    if not is_worker:
        try:
            import PySide6.QtCore
            import PySide6.QtNetwork
            import PySide6.QtGui
            import PySide6.QtWidgets
            import PySide6.QtMultimedia
            import PySide6.QtMultimediaWidgets
            return True
        except Exception:
            pass

    pyside6_mod = sys.modules.get("PySide6")
    if not isinstance(pyside6_mod, ModuleType):
        pyside6_mod = MockModule("PySide6")
        sys.modules["PySide6"] = pyside6_mod

    for sub in ["QtCore", "QtWidgets", "QtGui", "QtNetwork", "QtMultimedia", "QtMultimediaWidgets"]:
        full_name = f"PySide6.{sub}"
        if full_name not in sys.modules:
            mod = MockModule(full_name)
            setattr(pyside6_mod, sub, mod)
            sys.modules[full_name] = mod

    pyside6_mod.QtCore.Qt = DummyQt
    pyside6_mod.QtCore.QSettings = DummyQSettings
    pyside6_mod.QtCore.Signal = lambda *a: type("Sig", (), {"connect": lambda s, f: None, "emit": lambda s, *a: None, "disconnect": lambda s, f=None: None})()
    pyside6_mod.QtGui.QFont = DummyQFont
    pyside6_mod.QtGui.QUndoCommand = type("QUndoCommand", (), {"__init__": lambda self, *a, **k: None, "redo": lambda self: None, "undo": lambda self: None})
    pyside6_mod.QtWidgets.QMessageBox = DummyQMessageBox
    pyside6_mod.QtWidgets.QApplication = DummyQApplication
    pyside6_mod.QtWidgets.QHeaderView = DummyQHeaderView
    pyside6_mod.QtWidgets.QAbstractItemView = DummyQAbstractItemView
    pyside6_mod.QtWidgets.QLineEdit = DummyQLineEdit

    return False


__all__ = [
    "MockModule",
    "DummyQt",
    "DummyQSettings",
    "DummyQMessageBox",
    "DummyQApplication",
    "DummyQHeaderView",
    "DummyQAbstractItemView",
    "DummyQLineEdit",
    "_ensure_pyside6_fallback",
]
