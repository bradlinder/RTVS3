"""shortcuts/widgets.py — Interactive Key Sequence Recorder and Input widgets."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QLineEdit

from shortcuts.schema import _get_shortcuts_theme_mode, format_sequence_display


class KeySequenceRecorderEdit(QLineEdit):
    """Interactive input widget that captures key presses and formats them into a shortcut sequence."""

    keySequenceChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.is_recording = False
        self.current_seq = ""
        self.setPlaceholderText("Click here and press shortcut keys...")
        self.setStyleSheet(
            "QLineEdit { font-weight: bold; padding: 5px 8px; border-radius: 4px; border: 1px solid #475569; }"
        )

    def set_sequence(self, seq_str: str):
        self.current_seq = seq_str or ""
        self.setText(format_sequence_display(self.current_seq))

    def get_sequence(self) -> str:
        return self.current_seq

    def start_recording(self):
        self.is_recording = True
        self.setText("Press desired key combination (or Esc to cancel)...")
        tm = _get_shortcuts_theme_mode()
        if tm == "light":
            self.setStyleSheet(
                "QLineEdit { font-weight: bold; padding: 5px 8px; border-radius: 4px; "
                "border: 2px solid #2e74b5; background-color: #eaedf0; color: #205493; }"
            )
        elif tm == "high_contrast":
            self.setStyleSheet(
                "QLineEdit { font-weight: bold; padding: 5px 8px; border-radius: 4px; "
                "border: 2px solid #ffff00; background-color: #000000; color: #ffff00; }"
            )
        else:
            self.setStyleSheet(
                "QLineEdit { font-weight: bold; padding: 5px 8px; border-radius: 4px; "
                "border: 2px solid #3b82f6; background-color: #1e293b; color: #60a5fa; }"
            )
        self.setFocus()

    def stop_recording(self):
        self.is_recording = False
        tm = _get_shortcuts_theme_mode()
        if tm == "light":
            self.setStyleSheet(
                "QLineEdit { font-weight: bold; padding: 5px 8px; border-radius: 4px; border: 1px solid #b6bcc4; }"
            )
        elif tm == "high_contrast":
            self.setStyleSheet(
                "QLineEdit { font-weight: bold; padding: 5px 8px; border-radius: 4px; border: 1px solid #ffffff; }"
            )
        else:
            self.setStyleSheet(
                "QLineEdit { font-weight: bold; padding: 5px 8px; border-radius: 4px; border: 1px solid #475569; }"
            )
        self.setText(format_sequence_display(self.current_seq))

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if not self.is_recording:
            self.start_recording()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if not self.is_recording:
            self.start_recording()

    def focusOutEvent(self, event):
        if self.is_recording:
            self.stop_recording()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if not self.is_recording:
            super().keyPressEvent(event)
            return

        key = event.key()

        # Ignore standalone modifier keys while user is holding them down
        if key in (
            Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta,
            Qt.Key.Key_AltGr, Qt.Key.Key_Super_L, Qt.Key.Key_Super_R,
            getattr(Qt.Key, "Key_Hyper_L", 0), getattr(Qt.Key, "Key_Hyper_R", 0)
        ):
            event.accept()
            return

        # Pressing Escape cancels recording without changing the current shortcut
        if key == Qt.Key.Key_Escape:
            self.stop_recording()
            self.clearFocus()
            event.accept()
            return

        # Pressing Backspace or Delete while recording clears the shortcut
        mod_flags = event.modifiers()
        has_ctrl_or_alt = bool(mod_flags & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.MetaModifier))
        if key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete) and not has_ctrl_or_alt:
            self.current_seq = "None"
            self.stop_recording()
            self.clearFocus()
            self.keySequenceChanged.emit("None")
            event.accept()
            return

        # Safely determine active modifier prefixes without converting KeyboardModifiers object to int
        mod_prefix = []
        if bool(mod_flags & Qt.KeyboardModifier.ControlModifier):
            mod_prefix.append("Ctrl")
        if bool(mod_flags & Qt.KeyboardModifier.AltModifier):
            mod_prefix.append("Alt")
        if bool(mod_flags & Qt.KeyboardModifier.ShiftModifier):
            mod_prefix.append("Shift")
        if bool(mod_flags & Qt.KeyboardModifier.MetaModifier):
            mod_prefix.append("Meta")

        # Convert the pressed key into a standard portable text representation
        key_seq_single = QKeySequence(key)
        key_text = key_seq_single.toString(QKeySequence.SequenceFormat.PortableText)
        if not key_text:
            key_text = chr(key) if 32 <= key <= 126 else f"Key_{key}"

        if mod_prefix:
            new_seq_str = "+".join(mod_prefix + [key_text])
        else:
            new_seq_str = key_text

        # Canonicalize via QKeySequence validation
        test_seq = QKeySequence(new_seq_str)
        if test_seq.toString():
            new_seq_str = test_seq.toString(QKeySequence.SequenceFormat.PortableText)

        self.current_seq = new_seq_str
        self.stop_recording()
        self.clearFocus()
        self.keySequenceChanged.emit(self.current_seq)
        event.accept()
