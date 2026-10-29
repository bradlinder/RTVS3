# ui_menus.pyi — Typing and Interface Stub for ui_menus
from __future__ import annotations
from __future__ import annotations
import json
import logging
import sys
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QActionGroup, QColor, QFont, QIcon, QKeySequence
from PySide6.QtWidgets import QApplication, QCheckBox, QColorDialog, QComboBox, QDialog, QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QScrollArea, QSlider, QSplitter, QStatusBar, QTableWidget, QTableWidgetItem, QTextEdit, QToolBar, QToolButton, QVBoxLayout, QWidget
from prs_shared import APP_DISPLAY_NAME, PROJECT_VERSION, ffmpeg_path, ffprobe_path, format_time, platform_seq, safe_filename

class PersistentMenu(QMenu):

    def addMenu(self, *args, **kwargs):
        ...

    def mouseReleaseEvent(self, event):
        ...

class UiMenusMixin:

    def build_menus(self):
        ...

    def apply_user_shortcuts(self):
        ...

    def _refresh_recent_projects_menu(self):
        ...

    def _check_external_dependencies(self):
        ...

    def _sync_undo_redo_actions(self):
        ...

    def _remember_directory(self, path):
        ...

    def update_processing_menu_status(self):
        ...

    def refresh_plugin_menus(self):
        ...
