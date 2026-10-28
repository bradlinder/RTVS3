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


class MockClassMeta(type):
    """Metaclass allowing class-level attributes, static methods, and constructor calls to mock gracefully."""

    def __getattr__(cls, attr: str) -> Any:
        if attr in ("instance", "currentThread"):
            return staticmethod(lambda *a, **k: None)
        return DynamicMock()


class DynamicMock(metaclass=MockClassMeta):
    def __init__(self, *args, **kwargs):
        self._dict_store = {}
        self._items = {}
        self._flags = 37
        self._row_count = 0
        self._text = str(args[0]) if args and isinstance(args[0], (str, int, float)) else ""
        self._enabled = True
        self._checked = False
        self._visible = True
        self.itemChanged = DummySignal()

    def column(self):
        return getattr(self, "_col", 0)

    def row(self):
        return getattr(self, "_row", 0)

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

    def isEnabled(self):
        return getattr(self, "_enabled", True)

    def setEnabled(self, val):
        self._enabled = bool(val)

    def isChecked(self):
        return getattr(self, "_checked", False)

    def setChecked(self, val):
        self._checked = bool(val)

    def isVisible(self):
        return getattr(self, "_visible", True)

    def setVisible(self, val):
        self._visible = bool(val)

    def show(self):
        self._visible = True

    def hide(self):
        self._visible = False

    def setWindowModality(self, modality):
        self._modality = modality

    def windowModality(self):
        return getattr(self, "_modality", 0)

    def accept(self):
        pass

    def reject(self):
        pass

    def exec_(self):
        return 1

    def exec(self):
        return 1

    def __int__(self):
        return 0

    def __index__(self):
        return 0

    def __float__(self):
        return 0.0

    def __or__(self, other):
        val = getattr(self, "_flags", None)
        if val is not None and isinstance(other, int):
            return int(val) | other
        if isinstance(other, int):
            return int(self) | other
        return self

    def __ror__(self, other):
        return self.__or__(other)

    def __and__(self, other):
        val = getattr(self, "_flags", None)
        if val is not None and isinstance(other, int):
            return other & int(val)
        if isinstance(other, int):
            return other & int(self)
        return self

    def __rand__(self, other):
        return self.__and__(other)

    def __invert__(self):
        return self

    def __xor__(self, other):
        return self

    def __contains__(self, item):
        return item in self.__dict__.get("_dict_store", {})

    def count(self, *a, **k):
        return getattr(self, "_row_count", len(getattr(self, "_items", {})))

    def __ge__(self, other):
        try:
            return int(self) >= int(other)
        except Exception:
            return False

    def __gt__(self, other):
        try:
            return int(self) > int(other)
        except Exception:
            return False

    def __le__(self, other):
        try:
            return int(self) <= int(other)
        except Exception:
            return False

    def __lt__(self, other):
        try:
            return int(self) < int(other)
        except Exception:
            return False

    def __iter__(self):
        return iter(self.__dict__.get("_dict_store", {}))

    def __setitem__(self, key, val):
        if "_dict_store" not in self.__dict__:
            self._dict_store = {}
        self._dict_store[key] = val

    def __getitem__(self, key):
        store = self.__dict__.get("_dict_store")
        if store is not None and key in store:
            return store[key]
        return DynamicMock()

    def setFlags(self, flags):
        self._flags = int(flags)

    def flags(self):
        return self.__dict__.get("_flags", 37)

    def setRowCount(self, count):
        self._row_count = int(count)

    def rowCount(self, *a, **k):
        return self.__dict__.get("_row_count", 0)

    def setText(self, val):
        self._text = str(val)
        table = getattr(self, "_table", None)
        if table is not None and hasattr(table, "itemChanged"):
            table.itemChanged.emit(self)

    def text(self, *a, **k):
        return self.__dict__.get("_text", "")

    def setData(self, role, val):
        if "_role_data" not in self.__dict__:
            self._role_data = {}
        self._role_data[role] = val

    def data(self, role=0):
        return self.__dict__.get("_role_data", {}).get(role, None)

    def setItem(self, row, col, item):
        if "_items" not in self.__dict__:
            self._items = {}
        if item is not None and isinstance(item, DynamicMock):
            item._table = self
            item._row = row
            item._col = col
        self._items[(row, col)] = item

    def item(self, row, col):
        store = self.__dict__.get("_items")
        if store is not None and (row, col) in store:
            return store[(row, col)]
        return None

    def setCurrentCell(self, row, col):
        self._current_row = row
        self._current_col = col

    def currentRow(self):
        return self.__dict__.get("_current_row", 0)

    def currentColumn(self):
        return self.__dict__.get("_current_col", 0)

    def setItemDelegateForColumn(self, col, delegate):
        if "_column_delegates" not in self.__dict__:
            self._column_delegates = {}
        self._column_delegates[col] = delegate
        if hasattr(delegate, "commitData") and hasattr(delegate.commitData, "connect"):
            def _on_commit(editor):
                row = self.currentRow()
                it = self.item(row, col)
                if it and hasattr(editor, "text"):
                    it.setText(editor.text())
            delegate.commitData.connect(_on_commit)

    def itemDelegateForColumn(self, col):
        return self.__dict__.get("_column_delegates", {}).get(col, None)

    def addTab(self, widget, label=""):
        if "_tabs" not in self.__dict__:
            self._tabs = []
        self._tabs.append((widget, label))
        self._row_count = len(self._tabs)
        return len(self._tabs) - 1

    def editItem(self, item):
        col = getattr(item, "_col", 0)
        delegate = self.itemDelegateForColumn(col)
        editor = None
        if delegate and hasattr(delegate, "createEditor"):
            idx_mock = DynamicMock()
            idx_mock.column = lambda: col
            idx_mock.row = lambda: getattr(item, "_row", 0)
            editor = delegate.createEditor(self, None, idx_mock)
        if not editor:
            editor = DummyQLineEdit(self)
        if hasattr(editor, "setText") and hasattr(item, "text"):
            editor.setText(item.text())
        if hasattr(editor, "installEventFilter") and delegate:
            editor.installEventFilter(delegate)
        self._current_editor = editor
        if "_children" not in self.__dict__:
            self._children = []
        self._children.append(editor)
        return editor

    def findChild(self, cls, *args, **kwargs):
        for ch in self.__dict__.get("_children", []):
            if isinstance(ch, cls):
                return ch
        editor = self.__dict__.get("_current_editor")
        if editor and (isinstance(editor, cls) or getattr(cls, "__name__", "") == "QLineEdit"):
            return editor
        return None

    def installEventFilter(self, filter_obj):
        if "_event_filters" not in self.__dict__:
            self._event_filters = []
        self._event_filters.append(filter_obj)

    def removeEventFilter(self, filter_obj):
        if "_event_filters" in self.__dict__ and filter_obj in self._event_filters:
            self._event_filters.remove(filter_obj)

    def value(self, *args, **kwargs):
        if len(args) > 1:
            return args[1]
        if "default" in kwargs:
            return kwargs["default"]
        if "d" in kwargs:
            return kwargs["d"]
        return DynamicMock()


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

        mock_cls = type(name, (DynamicMock,), {})
        setattr(self, name, mock_cls)
        return mock_cls


class _DummyQtMeta(type):
    def __getattr__(cls, name: str) -> Any:
        return DynamicMock()


class DummyQt(metaclass=_DummyQtMeta):
    """Mock Qt namespace constants."""
    WindowType = type("WindowType", (DynamicMock,), {
        "WindowMaximizeButtonHint": 0x00020000,
        "Window": 0x00000001,
        "WindowMinimizeButtonHint": 0x00040000,
        "WindowCloseButtonHint": 0x08000000,
    })
    WidgetAttribute = type("WidgetAttribute", (DynamicMock,), {"WA_QuitOnClose": 76})
    ItemFlag = type("ItemFlag", (int,), {
        "NoItemFlags": 0,
        "ItemIsSelectable": 1,
        "ItemIsEditable": 4,
        "ItemIsDragEnabled": 8,
        "ItemIsDropEnabled": 16,
        "ItemIsUserCheckable": 32,
        "ItemIsEnabled": 32,
    })
    AlignmentFlag = type("AlignmentFlag", (DynamicMock,), {"AlignCenter": 0x0004, "AlignLeft": 0x0001, "AlignRight": 0x0002})
    Orientation = type("Orientation", (DynamicMock,), {"Horizontal": 1, "Vertical": 2})
    CheckState = type("CheckState", (DynamicMock,), {"Checked": 2, "Unchecked": 0})
    ItemDataRole = type("ItemDataRole", (DynamicMock,), {"UserRole": 256, "DisplayRole": 0})
    AspectRatioMode = type("AspectRatioMode", (DynamicMock,), {"KeepAspectRatio": 1, "IgnoreAspectRatio": 0})
    TransformationMode = type("TransformationMode", (DynamicMock,), {"SmoothTransformation": 1, "FastTransformation": 0})
    WindowModality = type("WindowModality", (int,), {"WindowModal": 1, "ApplicationModal": 2, "NonModal": 0})
    Key = type("Key", (int,), {
        "Key_Tab": 0x01000001,
        "Key_Backtab": 0x01000002,
        "Key_Return": 0x01000004,
        "Key_Enter": 0x01000005,
        "Key_Escape": 0x01000000,
    })
    KeyboardModifier = type("KeyboardModifier", (int,), {"NoModifier": 0})
    CursorShape = type("CursorShape", (int,), {"PointingHandCursor": 13, "ArrowCursor": 0})


class DummyQEvent(DynamicMock):
    Type = type("Type", (int,), {
        "KeyPress": 6,
        "KeyRelease": 7,
    })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._type = args[0] if len(args) > 0 else 6

    def type(self):
        return self._type


class DummyQKeyEvent(DynamicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._type = args[0] if len(args) > 0 else 6
        self._key = args[1] if len(args) > 1 else 0

    def type(self):
        return self._type

    def key(self):
        return self._key


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

    def clear(self) -> None:
        self._store.clear()

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
    _pending_callbacks: list = []

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def processEvents(cls) -> None:
        cbs = list(cls._pending_callbacks)
        cls._pending_callbacks.clear()
        for cb in cbs:
            try:
                cb()
            except Exception:
                pass

    @classmethod
    def sendEvent(cls, receiver, event) -> bool:
        filters = getattr(receiver, "_event_filters", [])
        for f in filters:
            try:
                if hasattr(f, "eventFilter") and f.eventFilter(receiver, event):
                    return True
            except Exception:
                pass
        return False

    @staticmethod
    def instance() -> Any:
        return DummyQApplication

    @staticmethod
    def topLevelWidgets() -> list:
        return []


class DummyQTimer(DynamicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = DummySignal()

    def start(self, *a, **k):
        pass

    def stop(self):
        pass

    @staticmethod
    def singleShot(ms: int, callback: Callable) -> None:
        DummyQApplication._pending_callbacks.append(callback)


class DummyQHeaderView:
    ResizeMode = type("ResizeMode", (DynamicMock,), {"ResizeToContents": 1, "Stretch": 2, "Interactive": 0, "Fixed": 3})


class DummyQAbstractItemView:
    SelectionBehavior = type("SelectionBehavior", (DynamicMock,), {"SelectRows": 1, "SelectColumns": 2, "SelectItems": 0})
    SelectionMode = type("SelectionMode", (DynamicMock,), {"ExtendedSelection": 3, "SingleSelection": 1, "MultiSelection": 2, "NoSelection": 0, "ContiguousSelection": 4})
    EditTrigger = type("EditTrigger", (DynamicMock,), {"NoEditTriggers": 0, "DoubleClicked": 2, "SelectedClicked": 4, "EditKeyPressed": 8, "AnyKeyPressed": 16, "AllEditTriggers": 31})
    ScrollMode = type("ScrollMode", (DynamicMock,), {"ScrollPerItem": 0, "ScrollPerPixel": 1})


class DummyQStyledItemDelegate(DynamicMock):
    EndEditHint = type("EndEditHint", (DynamicMock,), {"NoHint": 0, "EditNextItem": 1, "EditPreviousItem": 2, "SubmitModelCache": 3, "RevertModelCache": 4})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commitData = DummySignal()
        self.closeEditor = DummySignal()


class DummyQLineEdit(DynamicMock):
    EchoMode = type("EchoMode", (), {"Normal": 0, "Password": 2})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text = ""

    def setText(self, val):
        self._text = str(val)

    def text(self, *a, **k):
        return getattr(self, "_text", "")

    def selectAll(self):
        pass


class DummyQFont:
    Weight = type("Weight", (), {"Bold": 75, "Normal": 50})

    def __init__(self, *args, **kwargs):
        pass


class DummySignal:
    def __init__(self, *args, **kwargs):
        self._callbacks = []

    def connect(self, callback):
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def disconnect(self, callback=None):
        if callback is None:
            self._callbacks.clear()
        elif callback in self._callbacks:
            self._callbacks.remove(callback)

    def emit(self, *args, **kwargs):
        for cb in list(self._callbacks):
            try:
                cb(*args, **kwargs)
            except Exception:
                pass


class DummyQComboBox(DynamicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._items = []
        self._current_index = 0
        self.currentIndexChanged = DummySignal()

    def addItem(self, text: str, userData: Any = None):
        self._items.append((text, userData))

    def addItems(self, texts):
        for t in texts:
            self._items.append((t, None))

    def count(self) -> int:
        return len(self._items)

    def itemData(self, index: int, role: Any = None) -> Any:
        if 0 <= index < len(self._items):
            return self._items[index][1]
        return None

    def itemText(self, index: int) -> str:
        if 0 <= index < len(self._items):
            return str(self._items[index][0])
        return ""

    def currentIndex(self) -> int:
        return self._current_index if self._items else -1

    def setCurrentIndex(self, index: int):
        self._current_index = index

    def findData(self, data: Any, role: Any = None) -> int:
        for idx, (t, d) in enumerate(self._items):
            if d == data:
                return idx
        return -1

    def findText(self, text: str) -> int:
        for idx, (t, d) in enumerate(self._items):
            if str(t) == str(text):
                return idx
        return -1
        self.currentIndexChanged.emit(index)

    def currentText(self) -> str:
        idx = self.currentIndex()
        return self.itemText(idx) if idx >= 0 else ""

    def currentData(self, role: Any = None) -> Any:
        idx = self.currentIndex()
        return self.itemData(idx) if idx >= 0 else None

    def clear(self):
        self._items.clear()
        self._current_index = 0

    def setEnabled(self, val):
        pass

    def isEnabled(self) -> bool:
        return True

    def setStyleSheet(self, val):
        pass


class DummyQDoubleSpinBox:
    def __init__(self, *args, **kwargs):
        self._val = 0.0
        self.valueChanged = DummySignal()

    def value(self) -> float:
        return float(self._val)

    def setValue(self, v: float):
        self._val = float(v)
        self.valueChanged.emit(self._val)

    def setRange(self, mn: float, mx: float):
        pass

    def setSingleStep(self, s: float):
        pass

    def setSuffix(self, s: str):
        pass

    def setEnabled(self, val):
        pass

    def isEnabled(self) -> bool:
        return True

    def setStyleSheet(self, val):
        pass


class DummyQSpinBox:
    def __init__(self, *args, **kwargs):
        self._val = 0
        self.valueChanged = DummySignal()

    def value(self) -> int:
        return int(self._val)

    def setValue(self, v: int):
        self._val = int(v)
        self.valueChanged.emit(self._val)

    def setRange(self, mn: int, mx: int):
        pass

    def setSingleStep(self, s: int):
        pass

    def setSuffix(self, s: str):
        pass

    def setEnabled(self, val):
        pass

    def isEnabled(self) -> bool:
        return True

    def setStyleSheet(self, val):
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
    pyside6_mod.QtCore.QTimer = DummyQTimer
    pyside6_mod.QtCore.QEvent = DummyQEvent
    pyside6_mod.QtGui.QKeyEvent = DummyQKeyEvent
    pyside6_mod.QtCore.Signal = lambda *a: type("Sig", (), {"connect": lambda s, f: None, "emit": lambda s, *a: None, "disconnect": lambda s, f=None: None})()
    pyside6_mod.QtGui.QFont = DummyQFont
    pyside6_mod.QtGui.QUndoCommand = type("QUndoCommand", (), {"__init__": lambda self, *a, **k: None, "redo": lambda self: None, "undo": lambda self: None})
    pyside6_mod.QtWidgets.QMessageBox = DummyQMessageBox
    pyside6_mod.QtWidgets.QApplication = DummyQApplication
    pyside6_mod.QtCore.QCoreApplication = DummyQApplication
    pyside6_mod.QtWidgets.QHeaderView = DummyQHeaderView
    pyside6_mod.QtWidgets.QAbstractItemView = DummyQAbstractItemView
    pyside6_mod.QtWidgets.QStyledItemDelegate = DummyQStyledItemDelegate
    pyside6_mod.QtWidgets.QAbstractItemDelegate = DummyQStyledItemDelegate
    pyside6_mod.QtWidgets.QLineEdit = DummyQLineEdit
    pyside6_mod.QtWidgets.QComboBox = DummyQComboBox
    pyside6_mod.QtWidgets.QDoubleSpinBox = DummyQDoubleSpinBox
    pyside6_mod.QtWidgets.QSpinBox = DummyQSpinBox

    return False


__all__ = [
    "MockModule",
    "DummyQt",
    "DummyQSettings",
    "DummyQMessageBox",
    "DummyQApplication",
    "DummyQTimer",
    "DummyQHeaderView",
    "DummyQAbstractItemView",
    "DummyQLineEdit",
    "DummyQComboBox",
    "DummyQDoubleSpinBox",
    "DummyQSpinBox",
    "_ensure_pyside6_fallback",
]
