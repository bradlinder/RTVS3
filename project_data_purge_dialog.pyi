# project_data_purge_dialog.pyi — Typing and Interface Stub for project_data_purge_dialog
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from ui_layout import make_dialog_maximizable

class ProjectDataPurgeDialog(QDialog):

    def __init__(self, parent=..., is_es=...):
        ...

    def _init_ui(self):
        ...

    def _set_all_checked(self, checked: bool):
        ...

    def _update_purge_button_state(self):
        ...

    def get_purge_options(self) -> dict[str, bool]:
        ...
