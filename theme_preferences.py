"""Radio & TV Story Segmenter — Theme Preferences & Styling Engine.

Manages application theme switching (Dark, Light, High Contrast),
Qt application palette assignments, high-DPI stylesheets, window titlebar styling,
and canvas token updates.
"""

import logging
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from prs_shared import transcript_text_view_stylesheet
from theme_tokens import theme_tokens_for_mode

logger = logging.getLogger(__name__)


class ThemePreferencesMixin:
    """Provides application theme switching and styling methods."""

    def set_theme(self, mode):
        app = QApplication.instance()
        if mode not in ("light", "dark", "high_contrast"):
            mode = "dark"
        self.settings_store.setValue("theme_mode", mode)
        self.transcript_view.apply_theme_style(mode)
        translation_style = transcript_text_view_stylesheet(mode)
        for view_name in ("translation_view", "bilingual_english_view", "bilingual_spanish_view"):
            view = getattr(self, view_name, None)
            if view is not None:
                view.setStyleSheet(translation_style)

        if mode == "dark":
            used_qdarktheme = False
            try:
                import qdarktheme
                from theme_qss import TARGETED_QSS
                if hasattr(qdarktheme, "setup_theme"):
                    qdarktheme.setup_theme("dark", corner_shape="rounded", additional_qss=TARGETED_QSS)
                    used_qdarktheme = True
                elif hasattr(qdarktheme, "load_stylesheet"):
                    QApplication.instance().setStyleSheet(qdarktheme.load_stylesheet("dark") + "\n" + TARGETED_QSS)
                    used_qdarktheme = True
                else:
                    used_qdarktheme = False
            except Exception:
                used_qdarktheme = False

            if not used_qdarktheme:
                try:
                    from theme_qss import TARGETED_QSS
                except Exception:
                    TARGETED_QSS = ""
                dark_palette = QPalette()
                dark_palette.setColor(QPalette.Window, QColor("#121418"))
                dark_palette.setColor(QPalette.WindowText, QColor("#f0f0f0"))
                dark_palette.setColor(QPalette.Base, QColor("#1e222b"))
                dark_palette.setColor(QPalette.AlternateBase, QColor("#2a2e39"))
                dark_palette.setColor(QPalette.ToolTipBase, QColor("#2a2e39"))
                dark_palette.setColor(QPalette.ToolTipText, QColor("#ffffff"))
                dark_palette.setColor(QPalette.Text, QColor("#ffffff"))
                dark_palette.setColor(QPalette.Button, QColor("#2a2e39"))
                dark_palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
                dark_palette.setColor(QPalette.BrightText, QColor("#ff4d4d"))
                dark_palette.setColor(QPalette.Highlight, QColor("#315c85"))
                dark_palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
                app.setPalette(dark_palette)
                app.setStyleSheet("""
                QMainWindow { background-color: #121418; color: #f0f0f0; }
                #app_surface { background-color: #121418; }
                #app_brand { font-size: 16px; font-weight: 700; color: #f0f0f0; }
                QWidget { color: #f0f0f0; }
                QLabel { color: #f0f0f0; }
                QPushButton { background-color: #2a2e39; color: #ffffff; border: 1px solid #3a3f4d; border-radius: 5px; padding: 5px 10px; font-weight: 500; }
                QPushButton:hover { border-color: #58a6ff; background-color: #343a46; }
                QPushButton:pressed { background-color: #20242c; }
                QPushButton:disabled { color: #707580; background-color: #1a1d24; border-color: #2a2e39; }
                QGroupBox { font-weight: 600; border: 1px solid #30363d; border-radius: 6px; margin-top: 8px; padding-top: 10px; color: #f0f0f0; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #f0f0f0; }
                QMenuBar { background-color: #121418; color: #f0f0f0; }
                QMenuBar::item:selected { background-color: #2a2e39; }
                QMenu { background-color: #1e222b; color: #f0f0f0; border: 1px solid #3a3f4d; }
                QMenu::item:selected { background-color: #315c85; color: #ffffff; }
                QListWidget, QListView, QTreeView, QTableView, QLineEdit, QSpinBox, QComboBox { background-color: #1e222b; color: #ffffff; border: 1px solid #3a3f4d; border-radius: 4px; padding: 4px; }
                QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border-color: #58a6ff; }
                QListWidget::item, QListView::item, QTreeView::item, QTableView::item { padding: 4px 6px; border-radius: 3px; }
                QListWidget::item:hover, QListView::item:hover, QTreeView::item:hover, QTableView::item:hover { background-color: #262c37; color: #ffffff; }
                QListWidget::item:selected, QListView::item:selected, QTreeView::item:selected, QTableView::item:selected { background-color: #315c85; color: #ffffff; }
                QListWidget::item:selected:!active, QListView::item:selected:!active, QTreeView::item:selected:!active, QTableView::item:selected:!active { background-color: #2b5278; color: #ffffff; }
                QComboBox QAbstractItemView { background-color: #1e222b; color: #ffffff; selection-background-color: #315c85; selection-color: #ffffff; border: 1px solid #3a3f4d; }
                QSlider { background: transparent; height: 22px; }
                QSlider::groove:horizontal {
                    border: 1px solid #3a3f4d;
                    height: 6px;
                    background: #1e222b;
                    border-radius: 3px;
                }
                QSlider::sub-page:horizontal {
                    background: #1f6feb;
                    border: 1px solid #388bfd;
                    height: 6px;
                    border-radius: 3px;
                }
                QSlider::add-page:horizontal {
                    background: #161920;
                    border: 1px solid #3a3f4d;
                    height: 6px;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background: #f0f0f0;
                    border: 2px solid #58a6ff;
                    width: 14px;
                    margin-top: -5px;
                    margin-bottom: -5px;
                    border-radius: 8px;
                }
                QSlider::handle:horizontal:hover {
                    background: #ffffff;
                    border-color: #79b8ff;
                }
                QSlider::handle:horizontal:pressed {
                    background: #58a6ff;
                    border-color: #ffffff;
                }
                QProgressBar {
                    border: 1px solid #3a3f4d;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #1e222b;
                    color: #ffffff;
                    font-weight: 500;
                }
                QProgressBar::chunk {
                    background-color: #1f6feb;
                    border-radius: 3px;
                }
                QScrollBar:vertical {
                    border: none;
                    background: #121418;
                    width: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #30363d;
                    min-height: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #58a6ff;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::horizontal {
                    border: none;
                    background: #121418;
                    height: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:horizontal {
                    background: #30363d;
                    min-width: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: #58a6ff;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
                QToolTip { color: #ffffff; background-color: #1f242d; border: 1px solid #4a5162; padding: 4px 8px; border-radius: 4px; font-size: 13px; }
                QCheckBox { color: #f0f0f0; spacing: 8px; font-size: 13px; }
                QCheckBox::indicator, QListWidget::indicator, QListView::indicator, QTreeView::indicator, QTableView::indicator, QAbstractItemView::indicator {
                    width: 16px;
                    height: 16px;
                    border: 1.5px solid #6b7280;
                    border-radius: 3px;
                    background-color: transparent;
                }
                QCheckBox::indicator:hover, QListWidget::indicator:hover, QListView::indicator:hover, QTreeView::indicator:hover, QTableView::indicator:hover, QAbstractItemView::indicator:hover {
                    border-color: #00e5ff;
                }
                QCheckBox::indicator:checked, QListWidget::indicator:checked, QListView::indicator:checked, QTreeView::indicator:checked, QAbstractItemView::indicator:checked {
                    border-color: #00e5ff;
                    background-color: #00e5ff;
                    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 14 14'><path fill='none' stroke='%23081018' stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round' d='M2.5 7.5l3.2 3.5 5.8-7'/></svg>");
                }
                QCheckBox::indicator:disabled, QListWidget::indicator:disabled, QListView::indicator:disabled, QTreeView::indicator:disabled, QAbstractItemView::indicator:disabled {
                    border-color: #374151;
                    background-color: transparent;
                }
                QCheckBox::indicator:checked:disabled, QListWidget::indicator:checked:disabled, QListView::indicator:checked:disabled, QTreeView::indicator:checked:disabled, QAbstractItemView::indicator:checked:disabled {
                    border-color: #4b5563;
                    background-color: #4b5563;
                    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 14 14'><path fill='none' stroke='%231f242d' stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round' d='M2.5 7.5l3.2 3.5 5.8-7'/></svg>");
                }
                QRadioButton { color: #f0f0f0; spacing: 8px; font-size: 13px; }
                QRadioButton::indicator { width: 16px; height: 16px; border: 1.5px solid #6b7280; border-radius: 8px; background-color: #1e222b; }
                QRadioButton::indicator:hover { border-color: #58a6ff; }
                QRadioButton::indicator:checked {
                    border-color: #58a6ff;
                    background-color: #1e222b;
                    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16'><circle cx='8' cy='8' r='4' fill='%2358a6ff'/></svg>");
                }
                QRadioButton::indicator:disabled { border-color: #374151; background-color: #16181d; }
                QSplitter::handle { background-color: #30363d; height: 8px; }
                QSplitter::handle:hover { background-color: #58a6ff; }
                QScrollArea { border: 1px solid #30363d; background-color: transparent; }
                QTabWidget::pane { border: 1px solid #30363d; }
                QTabBar::tab { background-color: #1e222b; color: #f0f0f0; padding: 6px 12px; border: 1px solid #30363d; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
                QTabBar::tab:selected { background-color: #2a2e39; color: #ffffff; font-weight: bold; }
                #timeline_border_frame {
                    border: 2px solid #58a6ff;
                    border-radius: 4px;
                    background-color: #181b20;
                }
                #resizable_text_grip {
                    background-color: #3e4451;
                    border: 1px solid #555d6e;
                    border-radius: 3px;
                    margin: 2px 25%;
                }
                #resizable_text_grip:hover {
                    background-color: #58a6ff;
                }
            """ + "\n" + TARGETED_QSS)
        elif mode == "light":
            light_palette = QPalette()
            light_palette.setColor(QPalette.Window, QColor("#dcdfe3"))
            light_palette.setColor(QPalette.WindowText, QColor("#22262c"))
            light_palette.setColor(QPalette.Base, QColor("#eaedf0"))
            light_palette.setColor(QPalette.AlternateBase, QColor("#e3e6ea"))
            light_palette.setColor(QPalette.ToolTipBase, QColor("#22262c"))
            light_palette.setColor(QPalette.ToolTipText, QColor("#eaedf0"))
            light_palette.setColor(QPalette.Text, QColor("#22262c"))
            light_palette.setColor(QPalette.Button, QColor("#d0d4d9"))
            light_palette.setColor(QPalette.ButtonText, QColor("#22262c"))
            light_palette.setColor(QPalette.Highlight, QColor("#2e74b5"))
            light_palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
            app.setPalette(light_palette)
            app.setStyleSheet("""
                QMainWindow { background-color: #dcdfe3; color: #22262c; }
                #app_surface { background-color: #dcdfe3; }
                #app_brand { font-size: 16px; font-weight: 700; color: #22262c; }
                QWidget { color: #22262c; }
                QLabel { color: #22262c; }
                QPushButton { background-color: #d0d4d9; color: #22262c; border: 1px solid #b2b8c0; border-radius: 5px; padding: 5px 10px; font-weight: 500; }
                QPushButton:hover { border-color: #2e74b5; background-color: #c4c9cf; }
                QPushButton:pressed { background-color: #b8bec5; }
                QPushButton:disabled { color: #78808d; background-color: #e3e6ea; border-color: #c8ccd2; }
                QGroupBox { font-weight: 600; border: 1px solid #b6bcc4; border-radius: 6px; margin-top: 8px; padding-top: 10px; color: #22262c; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #22262c; }
                QMenuBar { background-color: #e3e6ea; color: #22262c; border-bottom: 1px solid #b6bcc4; }
                QMenuBar::item:selected { background-color: #d0d4d9; }
                QMenu { background-color: #eaedf0; color: #22262c; border: 1px solid #b6bcc4; }
                QMenu::item:selected { background-color: #2e74b5; color: #ffffff; }
                QListWidget, QListView, QTreeView, QTableView, QLineEdit, QSpinBox, QComboBox, QTextEdit, QPlainTextEdit { background-color: #eaedf0; color: #22262c; border: 1px solid #b6bcc4; border-radius: 4px; padding: 4px; }
                QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus { border-color: #2e74b5; }
                QListWidget::item, QListView::item, QTreeView::item, QTableView::item { padding: 4px 6px; border-radius: 3px; }
                QListWidget::item:hover, QListView::item:hover, QTreeView::item:hover, QTableView::item:hover { background-color: #dbe0e5; color: #22262c; }
                QListWidget::item:selected, QListView::item:selected, QTreeView::item:selected, QTableView::item:selected { background-color: #2e74b5; color: #ffffff; }
                QListWidget::item:selected:!active, QListView::item:selected:!active, QTreeView::item:selected:!active, QTableView::item:selected:!active { background-color: #548cb8; color: #ffffff; }
                QComboBox QAbstractItemView { background-color: #eaedf0; color: #22262c; selection-background-color: #2e74b5; selection-color: #ffffff; border: 1px solid #b6bcc4; }
                QSlider { background: transparent; height: 22px; }
                QSlider::groove:horizontal {
                    border: 1px solid #b6bcc4;
                    height: 6px;
                    background: #d6dae0;
                    border-radius: 3px;
                }
                QSlider::sub-page:horizontal {
                    background: #2e74b5;
                    border: 1px solid #235b8f;
                    height: 6px;
                    border-radius: 3px;
                }
                QSlider::add-page:horizontal {
                    background: #e3e6ea;
                    border: 1px solid #b6bcc4;
                    height: 6px;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background: #eaedf0;
                    border: 2px solid #2e74b5;
                    width: 14px;
                    margin-top: -5px;
                    margin-bottom: -5px;
                    border-radius: 8px;
                }
                QSlider::handle:horizontal:hover {
                    background: #2e74b5;
                    border-color: #235b8f;
                }
                QSlider::handle:horizontal:pressed {
                    background: #235b8f;
                    border-color: #17426b;
                }
                QProgressBar {
                    border: 1px solid #b6bcc4;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #e3e6ea;
                    color: #22262c;
                    font-weight: 500;
                }
                QProgressBar::chunk {
                    background-color: #2e74b5;
                    border-radius: 3px;
                }
                QScrollBar:vertical {
                    border: none;
                    background: #dcdfe3;
                    width: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #b6bcc4;
                    min-height: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #9ea6b0;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::horizontal {
                    border: none;
                    background: #dcdfe3;
                    height: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:horizontal {
                    background: #b6bcc4;
                    min-width: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal:hover {
                    background: #9ea6b0;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
                QToolTip { color: #eaedf0; background-color: #22262c; border: 1px solid #3d434d; padding: 4px 8px; border-radius: 4px; font-size: 13px; }
                QCheckBox { color: #22262c; spacing: 8px; font-size: 13px; }
                QCheckBox::indicator, QListWidget::indicator, QListView::indicator, QTreeView::indicator, QTableView::indicator, QAbstractItemView::indicator {
                    width: 16px;
                    height: 16px;
                    border: 1.5px solid #78808d;
                    border-radius: 3px;
                    background-color: transparent;
                }
                QCheckBox::indicator:hover, QListWidget::indicator:hover, QListView::indicator:hover, QTreeView::indicator:hover, QTableView::indicator:hover, QAbstractItemView::indicator:hover {
                    border-color: #2e74b5;
                }
                QCheckBox::indicator:checked, QListWidget::indicator:checked, QListView::indicator:checked, QTreeView::indicator:checked, QAbstractItemView::indicator:checked {
                    border-color: #2e74b5;
                    background-color: #2e74b5;
                    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 14 14'><path fill='none' stroke='%23eaedf0' stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round' d='M2.5 7.5l3.2 3.5 5.8-7'/></svg>");
                }
                QCheckBox::indicator:disabled, QListWidget::indicator:disabled, QListView::indicator:disabled, QTreeView::indicator:disabled, QAbstractItemView::indicator:disabled {
                    border-color: #c8ccd2;
                    background-color: transparent;
                }
                QCheckBox::indicator:checked:disabled, QListWidget::indicator:checked:disabled, QListView::indicator:checked:disabled, QTreeView::indicator:checked:disabled, QAbstractItemView::indicator:checked:disabled {
                    border-color: #9ea6b0;
                    background-color: #9ea6b0;
                    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 14 14'><path fill='none' stroke='%23e3e6ea' stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round' d='M2.5 7.5l3.2 3.5 5.8-7'/></svg>");
                }
                QRadioButton { color: #22262c; spacing: 8px; font-size: 13px; }
                QRadioButton::indicator { width: 16px; height: 16px; border: 1.5px solid #78808d; border-radius: 8px; background-color: #eaedf0; }
                QRadioButton::indicator:hover { border-color: #2e74b5; }
                QRadioButton::indicator:checked {
                    border-color: #2e74b5;
                    background-color: #eaedf0;
                    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16'><circle cx='8' cy='8' r='4' fill='%232e74b5'/></svg>");
                }
                QRadioButton::indicator:disabled { border-color: #c8ccd2; background-color: #e3e6ea; }
                QSplitter::handle { background-color: #b6bcc4; height: 8px; }
                QSplitter::handle:hover { background-color: #2e74b5; }
                QScrollArea { border: 1px solid #b6bcc4; background-color: transparent; }
                QTabWidget::pane { border: 1px solid #b6bcc4; }
                QTabBar::tab { background-color: #e3e6ea; color: #22262c; padding: 6px 12px; border: 1px solid #b6bcc4; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
                QTabBar::tab:selected { background-color: #eaedf0; color: #22262c; font-weight: bold; }
                #timeline_border_frame {
                    border: 2px solid #2e74b5;
                    border-radius: 4px;
                    background-color: #e3e6ea;
                }
                #resizable_text_grip {
                    background-color: #b6bcc4;
                    border: 1px solid #9ea6b0;
                    border-radius: 3px;
                    margin: 2px 25%;
                }
                #resizable_text_grip:hover {
                    background-color: #2e74b5;
                }
            """)
        elif mode == "high_contrast":
            hc_palette = QPalette()
            hc_palette.setColor(QPalette.Window, QColor("#000000"))
            hc_palette.setColor(QPalette.WindowText, QColor("#ffffff"))
            hc_palette.setColor(QPalette.Base, QColor("#000000"))
            hc_palette.setColor(QPalette.AlternateBase, QColor("#1a1a1a"))
            hc_palette.setColor(QPalette.ToolTipBase, QColor("#ffff00"))
            hc_palette.setColor(QPalette.ToolTipText, QColor("#000000"))
            hc_palette.setColor(QPalette.Text, QColor("#ffffff"))
            hc_palette.setColor(QPalette.Button, QColor("#000000"))
            hc_palette.setColor(QPalette.ButtonText, QColor("#ffff00"))
            hc_palette.setColor(QPalette.BrightText, QColor("#00ffff"))
            hc_palette.setColor(QPalette.Highlight, QColor("#ffff00"))
            hc_palette.setColor(QPalette.HighlightedText, QColor("#000000"))
            app.setPalette(hc_palette)
            app.setStyleSheet("""
                QMainWindow { background-color: #000000; color: #ffffff; }
                #app_surface { background-color: #000000; }
                #app_brand { font-size: 16px; font-weight: 700; color: #ffff00; }
                QWidget { color: #ffffff; font-weight: 500; }
                QLabel { color: #ffffff; }
                QPushButton { background-color: #000000; color: #ffff00; border: 2px solid #ffff00; border-radius: 4px; padding: 6px 12px; font-weight: bold; }
                QPushButton:hover { background-color: #ffff00; color: #000000; border-color: #ffffff; }
                QPushButton:pressed { background-color: #cccc00; color: #000000; }
                QPushButton:disabled { color: #666666; background-color: #000000; border-color: #666666; }
                QGroupBox { font-weight: bold; border: 2px solid #ffff00; border-radius: 4px; margin-top: 10px; padding-top: 12px; color: #ffff00; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #ffff00; }
                QMenuBar { background-color: #000000; color: #ffffff; border-bottom: 2px solid #ffff00; }
                QMenuBar::item:selected { background-color: #ffff00; color: #000000; }
                QMenu { background-color: #000000; color: #ffffff; border: 2px solid #ffff00; }
                QMenu::item:selected { background-color: #ffff00; color: #000000; }
                QListWidget, QListView, QTreeView, QTableView, QLineEdit, QSpinBox, QComboBox, QTextEdit, QPlainTextEdit { background-color: #000000; color: #ffffff; border: 2px solid #ffffff; }
                QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus { border-color: #ffff00; }
                QListWidget::item, QListView::item, QTreeView::item, QTableView::item { padding: 4px 6px; }
                QListWidget::item:hover, QListView::item:hover, QTreeView::item:hover, QTableView::item:hover { background-color: #1a1a1a; color: #ffff00; }
                QListWidget::item:selected, QListView::item:selected, QTreeView::item:selected, QTableView::item:selected { background-color: #ffff00; color: #000000; font-weight: bold; }
                QListWidget::item:selected:!active, QListView::item:selected:!active, QTreeView::item:selected:!active, QTableView::item:selected:!active { background-color: #cccc00; color: #000000; font-weight: bold; }
                QComboBox QAbstractItemView { background-color: #000000; color: #ffffff; selection-background-color: #ffff00; selection-color: #000000; border: 2px solid #ffffff; }
                QSlider { background: transparent; height: 22px; }
                QSlider::groove:horizontal {
                    border: 2px solid #ffffff;
                    height: 6px;
                    background: #000000;
                    border-radius: 3px;
                }
                QSlider::sub-page:horizontal {
                    background: #ffff00;
                    border: 2px solid #ffff00;
                    height: 6px;
                    border-radius: 3px;
                }
                QSlider::add-page:horizontal {
                    background: #000000;
                    border: 2px solid #ffffff;
                    height: 6px;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background: #ffff00;
                    border: 2px solid #ffffff;
                    width: 16px;
                    margin-top: -6px;
                    margin-bottom: -6px;
                    border-radius: 9px;
                }
                QSlider::handle:horizontal:hover {
                    background: #ffffff;
                    border-color: #ffff00;
                }
                QSlider::handle:horizontal:pressed {
                    background: #00ffff;
                    border-color: #ffffff;
                }
                QProgressBar {
                    border: 2px solid #ffffff;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #000000;
                    color: #ffff00;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background-color: #ffff00;
                }
                QScrollBar:vertical {
                    border: 1px solid #ffff00;
                    background: #000000;
                    width: 12px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #ffff00;
                    min-height: 20px;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::horizontal {
                    border: 1px solid #ffff00;
                    background: #000000;
                    height: 12px;
                    margin: 0px;
                }
                QScrollBar::handle:horizontal {
                    background: #ffff00;
                    min-width: 20px;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
                QToolTip { color: #000000; background-color: #ffff00; border: 2px solid #ffffff; padding: 4px 8px; font-size: 13px; font-weight: bold; }
                QCheckBox { color: #ffffff; spacing: 8px; font-weight: bold; font-size: 13px; }
                QCheckBox::indicator, QListWidget::indicator, QListView::indicator, QTreeView::indicator, QTableView::indicator, QAbstractItemView::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #ffffff;
                    border-radius: 3px;
                    background-color: #000000;
                }
                QCheckBox::indicator:hover, QListWidget::indicator:hover, QListView::indicator:hover, QTreeView::indicator:hover, QTableView::indicator:hover, QAbstractItemView::indicator:hover {
                    border-color: #ffff00;
                }
                QCheckBox::indicator:checked, QListWidget::indicator:checked, QListView::indicator:checked, QTreeView::indicator:checked, QAbstractItemView::indicator:checked {
                    border-color: #00ffff;
                    background-color: #00ffff;
                    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 14 14'><path fill='none' stroke='%23000000' stroke-width='2.8' stroke-linecap='round' stroke-linejoin='round' d='M2.5 7.5l3.2 3.5 5.8-7'/></svg>");
                }
                QCheckBox::indicator:disabled, QListWidget::indicator:disabled, QListView::indicator:disabled, QTreeView::indicator:disabled, QAbstractItemView::indicator:disabled {
                    background-color: #222222;
                    border-color: #666666;
                }
                QRadioButton { color: #ffffff; spacing: 8px; font-weight: bold; font-size: 13px; }
                QRadioButton::indicator { width: 18px; height: 18px; border: 2px solid #ffffff; border-radius: 9px; background-color: #000000; }
                QRadioButton::indicator:hover { border-color: #ffff00; }
                QRadioButton::indicator:checked {
                    border-color: #ffff00;
                    background-color: #000000;
                    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 18 18'><circle cx='9' cy='9' r='5' fill='%23ffff00'/></svg>");
                }
                QRadioButton::indicator:disabled { border-color: #666666; background-color: #222222; }
                QSplitter::handle { background-color: #ffff00; height: 8px; }
                QSplitter::handle:hover { background-color: #00ffff; }
                QScrollArea { border: 2px solid #ffff00; background-color: transparent; }
                QTabWidget::pane { border: 2px solid #ffff00; }
                QTabBar::tab { background-color: #000000; color: #ffffff; padding: 6px 14px; border: 2px solid #ffff00; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
                QTabBar::tab:selected { background-color: #ffff00; color: #000000; font-weight: bold; }
                #timeline_border_frame {
                    border: 3px solid #ffff00;
                    border-radius: 4px;
                    background-color: #000000;
                }
                #resizable_text_grip {
                    background-color: #ffff00;
                    border: 1px solid #ffffff;
                    border-radius: 3px;
                    margin: 2px 25%;
                }
            """)

        # Re-render active views so all inline HTML tags refresh with the new theme colors
        if hasattr(self, "render_transcript") and getattr(self, "transcript", None):
            try:
                self.render_transcript()
            except Exception:
                pass

        if hasattr(self, "render_translation_view"):
            try:
                self.render_translation_view()
            except Exception:
                pass

        # The timeline's waveform/ruler/selection/story-block colors are
        # drawn directly with QPainter (theme_tokens.ThemeTokens), not QSS,
        # so they don't pick up the palette/stylesheet changes above on
        # their own -- swap in the matching token preset and repaint.
        self.tokens = theme_tokens_for_mode(mode)
        if hasattr(self, "timeline"):
            self.timeline.tokens = self.tokens
            if hasattr(self.timeline, "canvas"):
                self.timeline.canvas.tokens = self.tokens
                self.timeline.canvas.pixmap_dirty = True
                self.timeline.canvas.update()

        # Update OS title bar caption attributes and collapsible section styling across all open windows and dialogs
        from core_utils import apply_window_titlebar_theme
        try:
            for w in app.topLevelWidgets():
                apply_window_titlebar_theme(w, mode)
                from prs_shared import CollapsibleSection
                for cs in w.findChildren(CollapsibleSection):
                    cs._update_ui()
        except Exception:
            pass
