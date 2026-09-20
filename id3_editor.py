"""ID3 Tag Editor module for Radio & TV Segmenter.

Provides full ID3v2 reading, writing, and PySide6 UI dialog for MP3 audio files.
Uses mutagen if available, with a complete pure-Python ID3v2.3 parser and writer fallback.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QImage, QCursor
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QFrame,
    QWidget,
    QApplication,
)

# Optional mutagen import
try:
    import mutagen
    from mutagen.mp3 import MP3
    from mutagen.id3 import (
        ID3,
        TIT2,
        TPE1,
        TALB,
        TDRC,
        TYER,
        TRCK,
        TCON,
        TPUB,
        TCOM,
        COMM,
        APIC,
        ID3NoHeaderError,
    )
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False


def _encode_synchsafe(size: int) -> bytes:
    """Encode an integer as a 4-byte ID3v2 synchsafe integer (7 bits per byte)."""
    b1 = (size >> 21) & 0x7F
    b2 = (size >> 14) & 0x7F
    b3 = (size >> 7) & 0x7F
    b4 = size & 0x7F
    return bytes([b1, b2, b3, b4])


def _decode_synchsafe(data: bytes) -> int:
    """Decode a 4-byte synchsafe integer."""
    if len(data) < 4:
        return 0
    return (data[0] << 21) | (data[1] << 14) | (data[2] << 7) | data[3]


def read_id3_tags(file_path: str) -> Dict[str, Any]:
    """Reads ID3 tag metadata from an MP3 file.
    
    Returns a dictionary with keys:
    - title, artist, album, year, track, genre, publisher, composer, comment
    - cover_bytes (bytes | None), cover_mime (str)
    """
    path = Path(file_path)
    tags: Dict[str, Any] = {
        "title": "",
        "artist": "",
        "album": "",
        "year": "",
        "track": "",
        "genre": "",
        "publisher": "",
        "composer": "",
        "comment": "",
        "cover_bytes": None,
        "cover_mime": "image/jpeg",
    }

    if not path.is_file():
        return tags

    if HAS_MUTAGEN:
        try:
            audio = ID3(str(path))
            tags["title"] = str(audio.get("TIT2", ""))
            tags["artist"] = str(audio.get("TPE1", ""))
            tags["album"] = str(audio.get("TALB", ""))
            
            # Year can be in TDRC or TYER
            year_frame = audio.get("TDRC") or audio.get("TYER")
            tags["year"] = str(year_frame) if year_frame else ""
            
            tags["track"] = str(audio.get("TRCK", ""))
            tags["genre"] = str(audio.get("TCON", ""))
            tags["publisher"] = str(audio.get("TPUB", ""))
            tags["composer"] = str(audio.get("TCOM", ""))

            # Comment
            comm_frames = audio.getall("COMM")
            if comm_frames:
                tags["comment"] = str(comm_frames[0].text[0]) if comm_frames[0].text else ""

            # Cover Art
            apic_frames = audio.getall("APIC")
            if apic_frames:
                tags["cover_bytes"] = apic_frames[0].data
                tags["cover_mime"] = apic_frames[0].mime
            return tags
        except Exception:
            pass  # Fall through to pure-Python parser if mutagen fails

    # Pure-Python ID3v2 Parser Fallback
    try:
        with open(path, "rb") as f:
            header = f.read(10)
            if len(header) < 10 or not header.startswith(b"ID3"):
                return tags

            version_major = header[3]
            tag_size = _decode_synchsafe(header[6:10])
            tag_data = f.read(tag_size)

            offset = 0
            while offset + 10 <= len(tag_data):
                frame_id = tag_data[offset:offset+4].decode("latin1", errors="ignore")
                if not frame_id.strip("\x00"):
                    break

                if version_major == 4:
                    frame_size = _decode_synchsafe(tag_data[offset+4:offset+8])
                else:
                    frame_size = int.from_bytes(tag_data[offset+4:offset+8], "big")

                if frame_size <= 0 or offset + 10 + frame_size > len(tag_data):
                    break

                frame_payload = tag_data[offset+10 : offset+10+frame_size]
                offset += 10 + frame_size

                # Parse text frame payload
                if frame_id in ("TIT2", "TPE1", "TALB", "TYER", "TDRC", "TRCK", "TCON", "TPUB", "TCOM"):
                    if len(frame_payload) > 1:
                        enc = frame_payload[0]
                        payload_bytes = frame_payload[1:]
                        if enc == 0:
                            val = payload_bytes.decode("latin1", errors="ignore").rstrip("\x00")
                        elif enc == 1:
                            val = payload_bytes.decode("utf-16", errors="ignore").rstrip("\x00")
                        elif enc == 2:
                            val = payload_bytes.decode("utf-16-be", errors="ignore").rstrip("\x00")
                        else:
                            val = payload_bytes.decode("utf-8", errors="ignore").rstrip("\x00")

                        field_map = {
                            "TIT2": "title",
                            "TPE1": "artist",
                            "TALB": "album",
                            "TYER": "year",
                            "TDRC": "year",
                            "TRCK": "track",
                            "TCON": "genre",
                            "TPUB": "publisher",
                            "TCOM": "composer",
                        }
                        if field_map.get(frame_id):
                            tags[field_map[frame_id]] = val

                elif frame_id == "COMM":
                    if len(frame_payload) > 4:
                        enc = frame_payload[0]
                        comm_data = frame_payload[4:]  # Skip 3-byte lang
                        # Split by null terminator (desc)
                        parts = comm_data.split(b"\x00", 1)
                        comm_text_bytes = parts[-1] if len(parts) > 1 else comm_data
                        if enc == 0:
                            tags["comment"] = comm_text_bytes.decode("latin1", errors="ignore").rstrip("\x00")
                        elif enc == 1:
                            tags["comment"] = comm_text_bytes.decode("utf-16", errors="ignore").rstrip("\x00")
                        else:
                            tags["comment"] = comm_text_bytes.decode("utf-8", errors="ignore").rstrip("\x00")

                elif frame_id == "APIC":
                    if len(frame_payload) > 2:
                        enc = frame_payload[0]
                        apic_sub = frame_payload[1:]
                        # Find MIME type null byte
                        null_idx = apic_sub.find(b"\x00")
                        if null_idx > 0:
                            mime = apic_sub[:null_idx].decode("latin1", errors="ignore")
                            rest = apic_sub[null_idx+1:]
                            if len(rest) > 1:
                                # Skip picture_type (1 byte) + description (terminated by null)
                                rest_sub = rest[1:]
                                desc_null = rest_sub.find(b"\x00")
                                if desc_null >= 0:
                                    img_data = rest_sub[desc_null+1:]
                                    tags["cover_bytes"] = img_data
                                    tags["cover_mime"] = mime or "image/jpeg"
    except Exception:
        pass

    return tags


def write_id3_tags(file_path: str, tags: Dict[str, Any]) -> None:
    """Writes or updates ID3v2 tags in an MP3 file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    if HAS_MUTAGEN:
        try:
            try:
                audio = ID3(str(path))
            except ID3NoHeaderError:
                audio = ID3()

            audio.delete(str(path))  # Replace with clean tags

            if tags.get("title"):
                audio.add(TIT2(encoding=3, text=str(tags["title"])))
            if tags.get("artist"):
                audio.add(TPE1(encoding=3, text=str(tags["artist"])))
            if tags.get("album"):
                audio.add(TALB(encoding=3, text=str(tags["album"])))
            if tags.get("year"):
                audio.add(TDRC(encoding=3, text=str(tags["year"])))
            if tags.get("track"):
                audio.add(TRCK(encoding=3, text=str(tags["track"])))
            if tags.get("genre"):
                audio.add(TCON(encoding=3, text=str(tags["genre"])))
            if tags.get("publisher"):
                audio.add(TPUB(encoding=3, text=str(tags["publisher"])))
            if tags.get("composer"):
                audio.add(TCOM(encoding=3, text=str(tags["composer"])))
            if tags.get("comment"):
                audio.add(COMM(encoding=3, lang="eng", desc="", text=str(tags["comment"])))

            if tags.get("cover_bytes"):
                audio.add(
                    APIC(
                        encoding=0,
                        mime=tags.get("cover_mime", "image/jpeg"),
                        type=3,  # Cover Front
                        desc="Cover",
                        data=tags["cover_bytes"],
                    )
                )

            audio.save(str(path), v2_version=3)
            return
        except Exception as exc:
            print(f"[ID3] mutagen write warning: {exc}, using pure-Python writer")

    # Pure-Python ID3v2.3 Writer Fallback
    with open(path, "rb") as f:
        file_bytes = f.read()

    audio_offset = 0
    if file_bytes.startswith(b"ID3") and len(file_bytes) >= 10:
        tag_size = _decode_synchsafe(file_bytes[6:10])
        audio_offset = 10 + tag_size

    raw_audio = file_bytes[audio_offset:]

    # Build ID3v2.3 frames
    frame_blocks = []

    def _build_text_frame(frame_id: str, text_val: str) -> bytes:
        if not text_val:
            return b""
        payload = b"\x03" + text_val.encode("utf-8")
        fid = frame_id.encode("latin1")
        fsize = len(payload).to_bytes(4, "big")
        flags = b"\x00\x00"
        return fid + fsize + flags + payload

    for fid, key in [
        ("TIT2", "title"),
        ("TPE1", "artist"),
        ("TALB", "album"),
        ("TYER", "year"),
        ("TRCK", "track"),
        ("TCON", "genre"),
        ("TPUB", "publisher"),
        ("TCOM", "composer"),
    ]:
        val = str(tags.get(key, "")).strip()
        if val:
            frame_blocks.append(_build_text_frame(fid, val))

    if tags.get("comment"):
        comm_val = str(tags["comment"]).strip()
        if comm_val:
            payload = b"\x03eng\x00" + comm_val.encode("utf-8")
            fsize = len(payload).to_bytes(4, "big")
            frame_blocks.append(b"COMM" + fsize + b"\x00\x00" + payload)

    if tags.get("cover_bytes"):
        img_bytes = tags["cover_bytes"]
        mime = (tags.get("cover_mime") or "image/jpeg").encode("latin1") + b"\x00"
        payload = b"\x00" + mime + b"\x03\x00" + img_bytes
        fsize = len(payload).to_bytes(4, "big")
        frame_blocks.append(b"APIC" + fsize + b"\x00\x00" + payload)

    frames_data = b"".join(frame_blocks)
    synch_size = _encode_synchsafe(len(frames_data))
    header = b"ID3\x03\x00\x00" + synch_size

    new_file_bytes = header + frames_data + raw_audio

    with open(path, "wb") as f:
        f.write(new_file_bytes)


class ID3TagEditorDialog(QDialog):
    """PySide6 GUI Dialog for viewing, editing, auto-filling, and saving ID3 tags on MP3 files."""

    def __init__(self, parent: Optional[QWidget] = None, mp3_path: Optional[str] = None):
        super().__init__(parent)
        self.main_window = parent
        self.mp3_path = mp3_path or ""
        self.cover_bytes: Optional[bytes] = None
        self.cover_mime: str = "image/jpeg"

        self.setWindowTitle("ID3 Tag Editor (MP3) — Radio & TV Segmenter")
        self.setMinimumWidth(560)
        self.resize(620, 640)

        self._build_ui()

        # If a path was passed or active audio is an MP3, auto-load
        if self.mp3_path and Path(self.mp3_path).is_file():
            self.path_edit.setText(str(Path(self.mp3_path).resolve()))
            self.load_tags_from_file()
        elif self.main_window and hasattr(self.main_window, "audio_file") and self.main_window.audio_file:
            cand = str(self.main_window.audio_file)
            if cand.lower().endswith(".mp3") and Path(cand).is_file():
                self.mp3_path = cand
                self.path_edit.setText(str(Path(cand).resolve()))
                self.load_tags_from_file()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header Title
        header_lbl = QLabel("MP3 Metadata & ID3 Tag Editor")
        header_lbl.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(header_lbl)

        # File Selector Row
        file_box = QGroupBox("Selected MP3 File")
        file_layout = QHBoxLayout(file_box)
        file_layout.setContentsMargins(10, 10, 10, 10)
        file_layout.setSpacing(8)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select an MP3 file to view or edit ID3 tags...")
        self.path_edit.setReadOnly(True)
        file_layout.addWidget(self.path_edit, 1)

        browse_btn = QPushButton("Browse MP3...")
        browse_btn.clicked.connect(self._browse_mp3)
        file_layout.addWidget(browse_btn)

        if self.main_window and hasattr(self.main_window, "audio_file") and self.main_window.audio_file:
            load_active_btn = QPushButton("Use Active Audio")
            load_active_btn.setToolTip("Load current active audio file from workspace")
            load_active_btn.clicked.connect(self._load_active_audio)
            file_layout.addWidget(load_active_btn)

        layout.addWidget(file_box)

        # Tag Form Fields
        form_box = QGroupBox("ID3v2 Metadata Fields")
        form_layout = QFormLayout(form_box)
        form_layout.setContentsMargins(12, 14, 12, 14)
        form_layout.setSpacing(10)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Track Title / Story Name (TIT2)")
        form_layout.addRow("Title:", self.title_edit)

        self.artist_edit = QLineEdit()
        self.artist_edit.setPlaceholderText("Artist / Speaker / Station Host (TPE1)")
        form_layout.addRow("Artist / Host:", self.artist_edit)

        self.album_edit = QLineEdit()
        self.album_edit.setPlaceholderText("Album / Broadcast / Show Title (TALB)")
        form_layout.addRow("Album / Show:", self.album_edit)

        year_track_row = QHBoxLayout()
        self.year_edit = QLineEdit()
        self.year_edit.setPlaceholderText("2026")
        self.year_edit.setMaximumWidth(120)
        year_track_row.addWidget(self.year_edit)

        year_track_row.addWidget(QLabel("Track / No.:"))
        self.track_edit = QLineEdit()
        self.track_edit.setPlaceholderText("1/1")
        self.track_edit.setMaximumWidth(100)
        year_track_row.addWidget(self.track_edit)
        year_track_row.addStretch()

        form_layout.addRow("Year & Track:", year_track_row)

        genre_pub_row = QHBoxLayout()
        self.genre_combo = QComboBox()
        self.genre_combo.setEditable(True)
        self.genre_combo.addItems([
            "Broadcast",
            "News",
            "Podcast",
            "Speech",
            "Talk Radio",
            "Interview",
            "Journalism",
            "Audiobook",
            "Music",
            "Other",
        ])
        genre_pub_row.addWidget(self.genre_combo, 1)

        genre_pub_row.addWidget(QLabel("Publisher / Call Sign:"))
        self.pub_edit = QLineEdit()
        self.pub_edit.setPlaceholderText("Station / Network (TPUB)")
        genre_pub_row.addWidget(self.pub_edit, 1)

        form_layout.addRow("Genre & Publisher:", genre_pub_row)

        self.composer_edit = QLineEdit()
        self.composer_edit.setPlaceholderText("Producer / Segment Editor (TCOM)")
        form_layout.addRow("Composer / Editor:", self.composer_edit)

        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Description, story summary, or segment comments (COMM)...")
        self.comment_edit.setMaximumHeight(75)
        form_layout.addRow("Comments:", self.comment_edit)

        layout.addWidget(form_box)

        # Cover Art Section
        art_box = QGroupBox("Cover Artwork (APIC)")
        art_layout = QHBoxLayout(art_box)
        art_layout.setContentsMargins(12, 10, 12, 10)

        self.art_preview = QLabel("No Cover Art")
        self.art_preview.setFixedSize(96, 96)
        self.art_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.art_preview.setStyleSheet("border: 1px dashed #aaa; border-radius: 4px; color: #777; font-size: 11px;")
        art_layout.addWidget(self.art_preview)

        art_btn_vbox = QVBoxLayout()
        art_btn_vbox.setSpacing(6)

        load_art_btn = QPushButton("Choose Image...")
        load_art_btn.clicked.connect(self._browse_cover_art)
        art_btn_vbox.addWidget(load_art_btn)

        clear_art_btn = QPushButton("Remove Art")
        clear_art_btn.clicked.connect(self._clear_cover_art)
        art_btn_vbox.addWidget(clear_art_btn)

        art_btn_vbox.addStretch()
        art_layout.addLayout(art_btn_vbox, 1)

        layout.addWidget(art_box)

        # Status & Action Buttons
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("font-size: 12px; color: #555;")
        layout.addWidget(self.status_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        if self.main_window:
            autofill_btn = QPushButton("⚡ Auto-Fill from Project")
            autofill_btn.setToolTip("Auto-populate tags using active project name, story titles, and speaker labels")
            autofill_btn.clicked.connect(self._autofill_from_project)
            btn_row.addWidget(autofill_btn)

        btn_row.addStretch()

        self.save_btn = QPushButton("Save ID3 Tags")
        self.save_btn.setStyleSheet("font-weight: bold; padding: 6px 18px;")
        self.save_btn.clicked.connect(self.save_tags)
        btn_row.addWidget(self.save_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _browse_mp3(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select MP3 File",
            str(Path.home()),
            "MP3 Audio Files (*.mp3);;All Files (*.*)",
        )
        if file_path:
            self.mp3_path = file_path
            self.path_edit.setText(str(Path(file_path).resolve()))
            self.load_tags_from_file()

    def _load_active_audio(self):
        if self.main_window and hasattr(self.main_window, "audio_file") and self.main_window.audio_file:
            path_str = str(self.main_window.audio_file)
            if not path_str.lower().endswith(".mp3"):
                QMessageBox.information(
                    self,
                    "Non-MP3 Active Audio",
                    f"The active audio file '{Path(path_str).name}' is not an MP3 file.\n\n"
                    "ID3 tags are supported on MP3 files. Please select or export an MP3 file.",
                )
                return
            self.mp3_path = path_str
            self.path_edit.setText(str(Path(path_str).resolve()))
            self.load_tags_from_file()

    def load_tags_from_file(self):
        if not self.mp3_path or not Path(self.mp3_path).is_file():
            return

        tags = read_id3_tags(self.mp3_path)
        self.title_edit.setText(tags.get("title", ""))
        self.artist_edit.setText(tags.get("artist", ""))
        self.album_edit.setText(tags.get("album", ""))
        self.year_edit.setText(tags.get("year", ""))
        self.track_edit.setText(tags.get("track", ""))

        genre = tags.get("genre", "")
        if genre:
            idx = self.genre_combo.findText(genre)
            if idx >= 0:
                self.genre_combo.setCurrentIndex(idx)
            else:
                self.genre_combo.setCurrentText(genre)

        self.pub_edit.setText(tags.get("publisher", ""))
        self.composer_edit.setText(tags.get("composer", ""))
        self.comment_edit.setPlainText(tags.get("comment", ""))

        self.cover_bytes = tags.get("cover_bytes")
        self.cover_mime = tags.get("cover_mime") or "image/jpeg"
        self._update_art_preview()

        self.status_lbl.setText(f"✓ Loaded tags from: {Path(self.mp3_path).name}")
        self.status_lbl.setStyleSheet("font-size: 12px; color: #2e7d32; font-weight: bold;")

    def _update_art_preview(self):
        if self.cover_bytes:
            pixmap = QPixmap()
            if pixmap.loadFromData(self.cover_bytes):
                scaled = pixmap.scaled(
                    96, 96,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.art_preview.setPixmap(scaled)
                self.art_preview.setText("")
                return
        self.art_preview.setPixmap(QPixmap())
        self.art_preview.setText("No Cover Art")

    def _browse_cover_art(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cover Image",
            str(Path.home()),
            "Image Files (*.jpg *.jpeg *.png *.webp);;All Files (*.*)",
        )
        if file_path and Path(file_path).is_file():
            try:
                with open(file_path, "rb") as f:
                    self.cover_bytes = f.read()

                suffix = Path(file_path).suffix.lower()
                if suffix in (".png",):
                    self.cover_mime = "image/png"
                elif suffix in (".webp",):
                    self.cover_mime = "image/webp"
                else:
                    self.cover_mime = "image/jpeg"

                self._update_art_preview()
                self.status_lbl.setText("✓ New cover art selected (unsaved)")
            except Exception as exc:
                QMessageBox.warning(self, "Image Error", f"Failed to load image:\n{exc}")

    def _clear_cover_art(self):
        self.cover_bytes = None
        self._update_art_preview()
        self.status_lbl.setText("Cover art removed (unsaved)")

    def _autofill_from_project(self):
        if not self.main_window:
            return

        import datetime
        now_year = str(datetime.datetime.now().year)
        self.year_edit.setText(now_year)
        self.composer_edit.setText("Radio & TV Segmenter")

        # Project name or media name
        proj_name = ""
        if hasattr(self.main_window, "project_file") and self.main_window.project_file:
            proj_name = Path(self.main_window.project_file).stem
        elif hasattr(self.main_window, "audio_file") and self.main_window.audio_file:
            proj_name = Path(self.main_window.audio_file).stem

        if proj_name:
            self.album_edit.setText(proj_name)

        # Collect story titles and speakers from main window
        stories = getattr(self.main_window, "stories", [])
        if stories:
            first_story = stories[0]
            title_cand = getattr(first_story, "title", "") or getattr(first_story, "suggestion", "")
            if title_cand:
                self.title_edit.setText(title_cand)

            speakers = set()
            for s in stories:
                spk = getattr(s, "speaker", "") or getattr(s, "speaker_label", "")
                if spk and spk.lower() not in ("unknown", "speaker"):
                    speakers.add(spk)

            if speakers:
                self.artist_edit.setText(", ".join(sorted(speakers)))

            self.track_edit.setText(f"1/{len(stories)}")

            # Auto comment with story outline
            summary_lines = [f"Stories in Broadcast ({len(stories)} total):"]
            for idx, st in enumerate(stories[:5], 1):
                st_title = getattr(st, "title", "") or f"Story {idx}"
                summary_lines.append(f"{idx}. {st_title}")
            if len(stories) > 5:
                summary_lines.append(f"... and {len(stories)-5} more stories.")
            self.comment_edit.setPlainText("\n".join(summary_lines))
        elif proj_name and not self.title_edit.text():
            self.title_edit.setText(proj_name)

        self.status_lbl.setText("⚡ Auto-filled metadata from active project!")
        self.status_lbl.setStyleSheet("font-size: 12px; color: #1976d2; font-weight: bold;")

    def save_tags(self):
        if not self.mp3_path or not Path(self.mp3_path).is_file():
            QMessageBox.warning(self, "Invalid File", "Please select a valid MP3 file before saving tags.")
            return

        tags = {
            "title": self.title_edit.text().strip(),
            "artist": self.artist_edit.text().strip(),
            "album": self.album_edit.text().strip(),
            "year": self.year_edit.text().strip(),
            "track": self.track_edit.text().strip(),
            "genre": self.genre_combo.currentText().strip(),
            "publisher": self.pub_edit.text().strip(),
            "composer": self.composer_edit.text().strip(),
            "comment": self.comment_edit.toPlainText().strip(),
            "cover_bytes": self.cover_bytes,
            "cover_mime": self.cover_mime,
        }

        try:
            write_id3_tags(self.mp3_path, tags)
            self.status_lbl.setText(f"✓ Successfully saved ID3 tags to: {Path(self.mp3_path).name}")
            self.status_lbl.setStyleSheet("font-size: 13px; color: #2e7d32; font-weight: bold;")
            QMessageBox.information(
                self,
                "ID3 Tags Saved",
                f"ID3v2 tags successfully written to:\n{self.mp3_path}",
            )
        except Exception as exc:
            self.status_lbl.setText(f"Error saving ID3 tags: {exc}")
            self.status_lbl.setStyleSheet("font-size: 12px; color: #d32f2f;")
            QMessageBox.critical(self, "Save Error", f"Failed to write ID3 tags to MP3 file:\n{exc}")
