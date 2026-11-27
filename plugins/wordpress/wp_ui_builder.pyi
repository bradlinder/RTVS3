# wp_ui_builder.pyi — Typing and Interface Stub for wp_ui_builder
from __future__ import annotations
from __future__ import annotations
import html
from typing import Any, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton, QRadioButton, QScrollArea, QSizePolicy, QSlider, QSplitter, QStackedWidget, QTabWidget, QTextEdit, QVBoxLayout, QWidget
from prs_shared import CollapsibleSection, get_active_theme_mode, get_story_vocabulary

def setup_wp_tab_ui(self: Any):
    ...

def _format_excluded_role_label(tab_widget: Any, role_value: Optional[int]) -> str:
    ...

def show_wp_excluded_placeholder(tab_widget: Any, role_value: Optional[int]) -> None:
    ...

def hide_wp_excluded_placeholder(tab_widget: Any) -> None:
    ...

def include_excluded_item_in_export(tab_widget: Any) -> bool:
    ...

def sync_wp_excluded_state_for_sidebar(tab_widget: Any, ext_sidebar: bool, fallback_row: int=...) -> Optional[int]:
    ...
