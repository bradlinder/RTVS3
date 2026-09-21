"""WordPress Plugin — Client, Credential Storage, and Upload Engine.

Contains WordPress REST API communication, keyring storage with fallback encryption,
settings dialog, and media/post upload execution.
"""
from __future__ import annotations

import html
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from prs_shared import (
    INTERNAL_APP_ID,
    PROJECT_VERSION,
    QSettings,
    ffmpeg_path,
    format_time,
    safe_filename,
)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def _get_keyring():
    """Safely return keyring module if available."""
    try:
        import keyring
        return keyring
    except Exception:
        return None


def _get_wp_fallback_cipher():
    """Best-effort symmetric cipher bound to this machine, used only for
    the QSettings fallback when no system keyring service is available.
    """
    try:
        import base64
        import hashlib
        import platform
        from cryptography.fernet import Fernet

        host_salt = f"{platform.node()}|{INTERNAL_APP_ID}|rtvs-wp-fallback".encode("utf-8")
        key = base64.urlsafe_b64encode(hashlib.sha256(host_salt).digest())
        return Fernet(key)
    except Exception:
        return None


def _get_wp_password(username: str) -> str:
    """Retrieve the stored WordPress application password."""
    if not username:
        return ""
    kr = _get_keyring()
    if kr is not None:
        try:
            pwd = kr.get_password(INTERNAL_APP_ID, f"wp_{username}")
            if pwd:
                return pwd
        except Exception:
            pass
    settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
    raw = str(settings.value(f"wp_pass_{username}", "") or "")
    if not raw:
        return ""
    is_encrypted = str(settings.value(f"wp_pass_{username}_enc", "")).lower() in {"1", "true", "yes"}
    if not is_encrypted:
        return raw
    cipher = _get_wp_fallback_cipher()
    if cipher is None:
        return ""
    try:
        return cipher.decrypt(raw.encode("ascii")).decode("utf-8")
    except Exception:
        return ""


def _set_wp_password(username: str, password: str) -> bool:
    """Store the WordPress application password securely.

    Returns True if it was saved to the system keyring, False if it fell
    back to (encrypted, where possible) local storage.
    """
    if not username:
        return False
    kr = _get_keyring()
    saved_in_keyring = False
    if kr is not None:
        try:
            kr.set_password(INTERNAL_APP_ID, f"wp_{username}", password)
            saved_in_keyring = True
        except Exception:
            pass
    settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
    if not saved_in_keyring:
        cipher = _get_wp_fallback_cipher()
        if cipher is not None:
            try:
                token = cipher.encrypt(password.encode("utf-8")).decode("ascii")
                settings.setValue(f"wp_pass_{username}", token)
                settings.setValue(f"wp_pass_{username}_enc", True)
            except Exception:
                settings.setValue(f"wp_pass_{username}", password)
                settings.setValue(f"wp_pass_{username}_enc", False)
        else:
            settings.setValue(f"wp_pass_{username}", password)
            settings.setValue(f"wp_pass_{username}_enc", False)
    else:
        # Clear fallback if saved in keyring
        settings.remove(f"wp_pass_{username}")
        settings.remove(f"wp_pass_{username}_enc")
    return saved_in_keyring


def generate_wp_excerpt(text: str, max_words: int = 55) -> str:
    """Generate a clean WordPress-style post excerpt from text (standard 55 words)."""
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"\[[^\]]+\]", " ", cleaned)
    cleaned = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\b", " ", cleaned)
    words = cleaned.split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]) + "..."


class WordPressClient:
    """Client for WordPress REST API using Application Passwords."""

    def __init__(self, site_url: str, username: str, password: str):
        self.site_url = site_url.rstrip("/")
        self.username = username
        self.password = password.strip()
        self.api_base = f"{self.site_url}/wp-json/wp/v2"

    def _get_auth(self):
        return (self.username, self.password)

    def test_connection(self) -> tuple[bool, str]:
        """Test credentials against /wp/v2/users/me or /wp/v2/posts."""
        import requests
        try:
            url = f"{self.api_base}/users/me"
            resp = requests.get(url, auth=self._get_auth(), timeout=12)
            if resp.status_code == 200:
                user_data = resp.json()
                name = user_data.get("name", self.username)
                return True, f"Connected successfully as '{name}'."
            elif resp.status_code in (401, 403):
                return False, f"Authentication failed (HTTP {resp.status_code}): Invalid username or application password."
            else:
                return False, f"WordPress server returned HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as exc:
            return False, f"Connection failed: {exc}"

    def get_categories(self) -> list[dict]:
        """Fetch post categories from WordPress."""
        import requests
        try:
            url = f"{self.api_base}/categories"
            params = {"per_page": 100, "_fields": "id,name,slug,parent"}
            resp = requests.get(url, auth=self._get_auth(), params=params, timeout=15)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []

    def get_authors(self) -> list[dict]:
        """Fetch PublishPress Authors profiles, including guest authors without users."""
        import requests

        authors: list[dict] = []
        seen: set[int] = set()

        def add_author(item: dict, default_guest: bool = False) -> None:
            try:
                term_id = int(item.get("term_id", item.get("id")))
            except (TypeError, ValueError):
                return
            if term_id in seen:
                return
            name = item.get("display_name") or item.get("name")
            if isinstance(name, dict):
                name = name.get("rendered", "")
            if not name:
                return
            try:
                user_id = int(item.get("user_id") or 0)
            except (TypeError, ValueError):
                user_id = 0
            is_guest = bool(item.get("is_guest", default_guest)) or user_id == 0
            seen.add(term_id)
            authors.append({
                "id": user_id or term_id,
                "term_id": term_id,
                "user_id": user_id,
                "name": str(name),
                "slug": item.get("slug", ""),
                "type": "Guest Author" if is_guest else "PublishPress Author",
                "is_guest": is_guest,
            })

        # PublishPress Authors is the authoritative source.
        try:
            for page in range(1, 11):
                resp = requests.get(
                    f"{self.site_url}/wp-json/publishpress-authors/v1/authors",
                    auth=self._get_auth(),
                    params={"per_page": 100, "page": page}, timeout=15,
                )
                if resp.status_code != 200:
                    break
                data = resp.json()
                if isinstance(data, dict):
                    data = data.get("authors", data.get("data", []))
                if not isinstance(data, list) or not data:
                    break
                for item in data:
                    if isinstance(item, dict):
                        add_author(item)
                if len(data) < 100:
                    break
        except Exception:
            pass

        # Fallback for installations exposing the author taxonomy directly.
        if not authors:
            for taxonomy in ("author", "ppma_author"):
                try:
                    resp = requests.get(
                        f"{self.api_base}/{taxonomy}", auth=self._get_auth(),
                        params={"per_page": 100}, timeout=15,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    add_author(item, default_guest=True)
                    if authors:
                        break
                except Exception:
                    continue

        # Final fallback for standard sites without PublishPress Authors.
        if not authors:
            try:
                resp = requests.get(
                    f"{self.api_base}/users", auth=self._get_auth(),
                    params={"per_page": 100, "_fields": "id,name,slug"}, timeout=15,
                )
                if resp.status_code == 200:
                    for u in resp.json():
                        try:
                            uid = int(u.get("id"))
                        except (TypeError, ValueError):
                            continue
                        authors.append({
                            "id": uid, "term_id": None, "user_id": uid,
                            "name": u.get("name", ""), "slug": u.get("slug", ""),
                            "type": "WP User", "is_guest": False,
                        })
            except Exception:
                pass
        return authors

    def upload_media(self, file_path: str, filename: str | None = None) -> dict:
        """Upload media using WordPress's standard multipart API, with raw fallback."""
        import mimetypes
        import requests
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Media file not found: {file_path}")
        upload_filename = filename or path.name
        mime_type = mimetypes.guess_type(upload_filename)[0] or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if path.suffix.lower() == ".mp3":
            mime_type = "audio/mpeg"
        elif path.suffix.lower() == ".wav":
            mime_type = "audio/wav"
        url = f"{self.api_base}/media"
        errors = []

        try:
            with open(path, "rb") as f:
                resp = requests.post(
                    url, auth=self._get_auth(),
                    files={"file": (upload_filename, f, mime_type)},
                    headers={"Accept": "application/json"}, timeout=180,
                )
            if resp.status_code in (200, 201):
                return resp.json()
            errors.append(f"multipart HTTP {resp.status_code}: {resp.text[:500]}")
        except Exception as exc:
            errors.append(f"multipart exception: {exc}")

        # Raw upload fallback
        try:
            headers = {
                "Accept": "application/json",
                "Content-Disposition": f'attachment; filename="{upload_filename}"',
                "Content-Type": mime_type,
                "Content-Length": str(path.stat().st_size),
            }
            with open(path, "rb") as f:
                resp = requests.post(url, auth=self._get_auth(), headers=headers, data=f, timeout=180)
            if resp.status_code in (200, 201):
                return resp.json()
            errors.append(f"raw HTTP {resp.status_code}: {resp.text[:500]}")
        except Exception as exc:
            errors.append(f"raw exception: {exc}")
        raise RuntimeError("WordPress Media upload failed (" + "; ".join(errors) + ")")

    def create_post(
        self,
        title: str,
        content: str,
        excerpt: str = "",
        status: str = "draft",
        category_ids: list[int] | None = None,
        author_ids: list[int] | None = None,
        author_term_ids: list[int] | None = None,
        featured_media_id: int | None = None,
    ) -> dict:
        """Create a post in WordPress."""
        import requests
        payload: dict[str, Any] = {
            "title": title,
            "content": content,
            "excerpt": excerpt,
            "status": status,
        }
        if category_ids:
            payload["categories"] = category_ids
        if author_ids:
            payload["author"] = author_ids[0]
        if author_term_ids:
            payload["ppma_author"] = [int(term_id) for term_id in author_term_ids]
        if featured_media_id:
            payload["featured_media"] = int(featured_media_id)

        url = f"{self.api_base}/posts"
        resp = requests.post(url, auth=self._get_auth(), json=payload, timeout=30)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"WordPress Post creation failed (HTTP {resp.status_code}): {resp.text[:300]}")
        return resp.json()


class WordPressSettingsDialog(QDialog):
    """Dialog for entering and testing WordPress site credentials."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WordPress Connection Settings")
        self.setMinimumWidth(480)
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        desc = QLabel(
            "Configure your WordPress site connection using an <b>Application Password</b>.<br>"
            "To generate one in WordPress: go to <i>Users &gt; Profile &gt; Application Passwords</i>."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        group = QGroupBox("WordPress Credentials")
        form = QFormLayout(group)

        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://yoursite.com")
        self.url_edit.setText(str(self.settings.value("wp_site_url", "") or ""))

        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("your_username")
        current_user = str(self.settings.value("wp_username", "") or "")
        self.user_edit.setText(current_user)

        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setPlaceholderText("xxxx xxxx xxxx xxxx")
        if current_user:
            self.pass_edit.setText(_get_wp_password(current_user))

        form.addRow("Site URL:", self.url_edit)
        form.addRow("Username:", self.user_edit)
        form.addRow("App Password:", self.pass_edit)
        layout.addWidget(group)

        # Default Custom Header / Footer Text
        custom_group = QGroupBox("Default Custom Text / Disclaimer (Optional)")
        cg_layout = QVBoxLayout(custom_group)

        self.custom_text_edit = QTextEdit()
        self.custom_text_edit.setPlaceholderText(
            "e.g. Note: The following transcript was machine-generated and may contain some spelling errors or other inaccuracies."
        )
        self.custom_text_edit.setMaximumHeight(65)
        self.custom_text_edit.setPlainText(str(self.settings.value("wp_custom_text", "") or ""))
        cg_layout.addWidget(self.custom_text_edit)

        pos_row = QHBoxLayout()
        self.pos_button_group = QButtonGroup(self)
        self.rad_pos_top = QRadioButton("Place at top of post")
        self.rad_pos_bottom = QRadioButton("Place at bottom of post")
        self.pos_button_group.addButton(self.rad_pos_top)
        self.pos_button_group.addButton(self.rad_pos_bottom)
        saved_pos = str(self.settings.value("wp_custom_text_pos", "top") or "top").lower()
        if saved_pos == "bottom":
            self.rad_pos_bottom.setChecked(True)
        else:
            self.rad_pos_top.setChecked(True)
        pos_row.addWidget(self.rad_pos_top)
        pos_row.addWidget(self.rad_pos_bottom)
        pos_row.addStretch()
        cg_layout.addLayout(pos_row)

        opt_layout = QVBoxLayout()
        self.chk_no_snippet = QCheckBox("Hide from Google & search engine snippets (data-nosnippet)")
        self.chk_no_excerpt = QCheckBox("Exclude this text from WordPress post excerpts")
        self.chk_no_snippet.setChecked(
            str(self.settings.value("wp_custom_text_no_snippet", "true")).lower() in ("true", "1", "yes")
        )
        self.chk_no_excerpt.setChecked(
            str(self.settings.value("wp_custom_text_no_excerpt", "true")).lower() in ("true", "1", "yes")
        )
        opt_layout.addWidget(self.chk_no_snippet)
        opt_layout.addWidget(self.chk_no_excerpt)
        cg_layout.addLayout(opt_layout)

        layout.addWidget(custom_group)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        btn_box = QHBoxLayout()
        self.test_btn = QPushButton("Test Connection")
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")

        btn_box.addWidget(self.test_btn)
        btn_box.addStretch()
        btn_box.addWidget(self.save_btn)
        btn_box.addWidget(self.cancel_btn)
        layout.addLayout(btn_box)

        self.test_btn.clicked.connect(self._test_connection)
        self.save_btn.clicked.connect(self._save_settings)
        self.cancel_btn.clicked.connect(self.reject)

    def _test_connection(self):
        url = self.url_edit.text().strip()
        user = self.user_edit.text().strip()
        pwd = self.pass_edit.text().strip()
        if not url or not user or not pwd:
            QMessageBox.warning(self, "Incomplete Settings", "Please enter Site URL, Username, and Password first.")
            return

        self.test_btn.setEnabled(False)
        self.status_label.setText("Testing connection...")
        self.status_label.setStyleSheet("color: #888888;")
        self.repaint()

        client = WordPressClient(url, user, pwd)
        ok, msg = client.test_connection()
        self.test_btn.setEnabled(True)
        if ok:
            self.status_label.setText(f"✓ {msg}")
            self.status_label.setStyleSheet("color: #2ea44f; font-weight: bold;")
        else:
            self.status_label.setText(f"✗ {msg}")
            self.status_label.setStyleSheet("color: #e06c75;")

    def _save_settings(self):
        url = self.url_edit.text().strip()
        user = self.user_edit.text().strip()
        pwd = self.pass_edit.text().strip()

        self.settings.setValue("wp_site_url", url)
        self.settings.setValue("wp_username", user)
        self.settings.setValue("wp_custom_text", self.custom_text_edit.toPlainText())
        self.settings.setValue("wp_custom_text_pos", "bottom" if self.rad_pos_bottom.isChecked() else "top")
        self.settings.setValue("wp_custom_text_no_snippet", self.chk_no_snippet.isChecked())
        self.settings.setValue("wp_custom_text_no_excerpt", self.chk_no_excerpt.isChecked())
        if user and pwd:
            saved_in_keyring = _set_wp_password(user, pwd)
            if not saved_in_keyring:
                QMessageBox.warning(
                    self,
                    "System Credential Storage Unavailable",
                    "Your operating system's secure credential storage (keyring) is not "
                    "available on this machine, so the WordPress application password has "
                    "been saved locally instead, encrypted with a key derived from this "
                    "machine.",
                )

        self.accept()


def get_wp_client() -> WordPressClient | None:
    """Instantiate WordPressClient from stored settings if configured."""
    settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
    url = str(settings.value("wp_site_url", "") or "").strip()
    user = str(settings.value("wp_username", "") or "").strip()
    pwd = _get_wp_password(user) if user else ""
    if url and user and pwd:
        return WordPressClient(url, user, pwd)
    return None


class WordPressPreferencesPage(QWidget):
    """Preferences page widget for WordPress integration inside the application Preferences dialog."""

    def __init__(self, parent: Any = None, app: Any = None):
        super().__init__(parent)
        self.app = app
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        desc = QLabel(
            "Configure your WordPress site connection using an <b>Application Password</b>.<br>"
            "To generate one in WordPress: go to <i>Users &gt; Profile &gt; Application Passwords</i>."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.orig_url = str(self.settings.value("wp_site_url", "") or "").strip()
        self.orig_user = str(self.settings.value("wp_username", "") or "").strip()
        self.orig_pwd = _get_wp_password(self.orig_user) if self.orig_user else ""

        cred_group = QGroupBox("WordPress Credentials")
        form = QFormLayout(cred_group)
        self.url_edit = QLineEdit(self.orig_url)
        self.url_edit.setPlaceholderText("https://yoursite.com")
        self.user_edit = QLineEdit(self.orig_user)
        self.user_edit.setPlaceholderText("your_username")
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setPlaceholderText("xxxx xxxx xxxx xxxx")
        if self.orig_pwd:
            self.pass_edit.setText(self.orig_pwd)

        form.addRow("Site URL:", self.url_edit)
        form.addRow("Username:", self.user_edit)
        form.addRow("App Password:", self.pass_edit)
        layout.addWidget(cred_group)

        custom_group = QGroupBox("Default Custom Text / Disclaimer (Optional)")
        cg_layout = QVBoxLayout(custom_group)
        self.custom_text_edit = QTextEdit()
        self.custom_text_edit.setPlaceholderText(
            "e.g. Note: The following transcript was machine-generated and may contain some spelling errors or other inaccuracies."
        )
        self.custom_text_edit.setMaximumHeight(65)
        self.custom_text_edit.setPlainText(str(self.settings.value("wp_custom_text", "") or ""))
        cg_layout.addWidget(self.custom_text_edit)

        pos_row = QHBoxLayout()
        self.pos_button_group = QButtonGroup(self)
        self.rad_pos_top = QRadioButton("Place at top of post")
        self.rad_pos_bottom = QRadioButton("Place at bottom of post")
        self.pos_button_group.addButton(self.rad_pos_top)
        self.pos_button_group.addButton(self.rad_pos_bottom)
        saved_pos = str(self.settings.value("wp_custom_text_pos", "top") or "top").lower()
        if saved_pos == "bottom":
            self.rad_pos_bottom.setChecked(True)
        else:
            self.rad_pos_top.setChecked(True)
        pos_row.addWidget(self.rad_pos_top)
        pos_row.addWidget(self.rad_pos_bottom)
        pos_row.addStretch()
        cg_layout.addLayout(pos_row)

        opt_layout = QVBoxLayout()
        self.chk_no_snippet = QCheckBox("Hide from Google & search engine snippets (data-nosnippet)")
        self.chk_no_snippet.setToolTip(
            "Wraps custom text in data-nosnippet and Google search engine directives so search engines index the story but exclude this notice from search result summaries."
        )
        self.chk_no_excerpt = QCheckBox("Exclude this text from WordPress post excerpts")
        self.chk_no_excerpt.setToolTip(
            "Prevents this notice from appearing in automated WordPress theme excerpts or post list teasers."
        )
        self.chk_no_snippet.setChecked(
            str(self.settings.value("wp_custom_text_no_snippet", "true")).lower() in ("true", "1", "yes")
        )
        self.chk_no_excerpt.setChecked(
            str(self.settings.value("wp_custom_text_no_excerpt", "true")).lower() in ("true", "1", "yes")
        )
        opt_layout.addWidget(self.chk_no_snippet)
        opt_layout.addWidget(self.chk_no_excerpt)
        cg_layout.addLayout(opt_layout)

        layout.addWidget(custom_group)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self._test_connection)
        layout.addWidget(self.test_btn)
        layout.addStretch()

    def _test_connection(self):
        url = self.url_edit.text().strip()
        user = self.user_edit.text().strip()
        pwd = self.pass_edit.text().strip()
        if not url or not user or not pwd:
            QMessageBox.warning(self, "Incomplete Settings", "Please enter Site URL, Username, and Password first.")
            return
        self.test_btn.setEnabled(False)
        self.status_label.setText("Testing connection...")
        self.status_label.setStyleSheet("color: #888888;")
        self.repaint()
        client = WordPressClient(url, user, pwd)
        ok, msg = client.test_connection()
        self.test_btn.setEnabled(True)
        if ok:
            self.status_label.setText(f"✓ {msg}")
            self.status_label.setStyleSheet("color: #2ea44f; font-weight: bold;")
        else:
            self.status_label.setText(f"✗ {msg}")
            self.status_label.setStyleSheet("color: #e06c75;")

    def save_preferences(self, dialog=None):
        wp_url = self.url_edit.text().strip()
        wp_user = self.user_edit.text().strip()
        wp_pwd = self.pass_edit.text().strip()

        if wp_url != self.orig_url:
            self.settings.setValue("wp_site_url", wp_url)
        if wp_user != self.orig_user:
            self.settings.setValue("wp_username", wp_user)

        self.settings.setValue("wp_custom_text", self.custom_text_edit.toPlainText())
        self.settings.setValue("wp_custom_text_pos", "bottom" if self.rad_pos_bottom.isChecked() else "top")
        self.settings.setValue("wp_custom_text_no_snippet", self.chk_no_snippet.isChecked())
        self.settings.setValue("wp_custom_text_no_excerpt", self.chk_no_excerpt.isChecked())

        if wp_user and wp_pwd and (wp_user != self.orig_user or wp_pwd != self.orig_pwd):
            saved_in_keyring = _set_wp_password(wp_user, wp_pwd)
            if not saved_in_keyring and dialog:
                QMessageBox.warning(
                    dialog,
                    "System Credential Storage Unavailable",
                    "Your operating system's secure credential storage (keyring) is not "
                    "available on this machine, so the WordPress application password has "
                    "been saved locally instead, encrypted with a key derived from this "
                    "machine.",
                )


def execute_wordpress_upload(
    main_window: Any,
    client: WordPressClient,
    post_title: str,
    post_excerpt: str,
    start: float | None,
    end: float | None,
    task_label: str,
    include_english: bool,
    include_spanish: bool,
    spanish_presentation: str,
    primary_language: str,
    author_ids: list[int] | None = None,
    author_term_ids: list[int] | None = None,
    category_ids: list[int] | None = None,
    show_completion_dialog: bool = False,
    media_filename: str | None = None,
    progress_callback=None,
    featured_image_path: str | None = None,
) -> dict:
    """Extract media clip, upload to WordPress media library, and create draft post."""
    def report_progress(step: int, description: str) -> None:
        if progress_callback:
            try:
                progress_callback(step, 4, description)
            except Exception:
                pass

    audio_src = getattr(main_window, "audio_file", None)
    if not audio_src or not Path(audio_src).exists():
        raise RuntimeError("No media file is loaded in the active project to export.")

    media_url = ""
    featured_media_id = None

    # Upload featured image if selected
    if featured_image_path and Path(featured_image_path).is_file():
        try:
            report_progress(1, "Uploading featured image…")
            img_item = client.upload_media(featured_image_path, filename=Path(featured_image_path).name)
            featured_media_id = img_item.get("id")
        except Exception as exc:
            if hasattr(main_window, "log_activity"):
                main_window.log_activity(f"[WORDPRESS WARNING] Failed to upload featured image: {exc}")

    # Prepare media file
    report_progress(1, "Preparing audio for WordPress…")
    temp_audio = None
    temp_dir = None
    try:
        target_media = str(audio_src)
        source_suffix = Path(audio_src).suffix.lower()
        duration = getattr(main_window, "duration", 0)
        needs_clip = start is not None and end is not None and (start > 0 or end < duration)
        needs_mp3 = source_suffix == ".wav"

        if needs_clip or needs_mp3:
            report_progress(1, "Converting audio to MP3…")
            temp_dir = Path(tempfile.mkdtemp(prefix="rtvs_wp_"))
            base = Path(safe_filename(media_filename or post_title or "audio_clip")).stem
            if needs_clip:
                temp_audio = temp_dir / f"{base}_{int(start or 0)}_{int(end or 0)}.mp3"
            else:
                temp_audio = temp_dir / f"{base}.mp3"
            ff = ffmpeg_path()
            if not ff:
                raise RuntimeError("FFmpeg is required to convert audio for WordPress export, but FFmpeg was not found.")
            cmd = [str(ff), "-y"]
            if needs_clip:
                cmd.extend(["-ss", str(max(0.0, float(start or 0.0)))])
            cmd.extend(["-i", str(audio_src)])
            if needs_clip and end is not None:
                clip_dur = max(0.0, float(end) - float(start or 0.0))
                cmd.extend(["-t", str(clip_dur)])
            cmd.extend(["-vn", "-c:a", "libmp3lame", "-b:a", "192k", str(temp_audio)])
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            res = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags)
            if res.returncode != 0 or not temp_audio.exists() or temp_audio.stat().st_size == 0:
                raise RuntimeError(f"FFmpeg audio preparation failed: {res.stderr[:300]}")
            target_media = str(temp_audio)

        # Upload Media to WordPress
        report_progress(2, "Uploading audio to WordPress media library…")
        upload_name = media_filename or f"{safe_filename(post_title or 'audio')}.mp3"
        media_item = client.upload_media(target_media, filename=upload_name)
        media_url = media_item.get("source_url") or media_item.get("guid", {}).get("rendered", "")
        if not media_url:
            raise RuntimeError("WordPress upload succeeded but media URL could not be resolved.")
    finally:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

    # 3. Prepare Post Content
    report_progress(3, "Preparing post content and formatting transcript…")
    content_parts = []
    is_video = bool(getattr(main_window, "current_media_is_video", False))
    if media_url:
        if is_video:
            content_parts.append(
                f'<!-- wp:video -->\n<figure class="wp-block-video"><video controls src="{media_url}"></video></figure>\n<!-- /wp:video -->'
            )
        else:
            content_parts.append(
                f'<!-- wp:audio -->\n<figure class="wp-block-audio"><audio controls src="{media_url}"></audio></figure>\n<!-- /wp:audio -->'
            )

    # Transcript extraction
    full_transcript = getattr(main_window, "transcript", []) or []
    clip_transcript = []
    if start is not None and end is not None:
        for seg in full_transcript:
            seg_start = seg.get("start", 0.0)
            seg_end = seg.get("end", 0.0)
            if (seg_start >= start and seg_start <= end) or (seg_end >= start and seg_end <= end) or (seg_start <= start and seg_end >= end):
                clip_transcript.append(seg)
    else:
        clip_transcript = full_transcript

    def language_blocks(lang_code: str):
        blocks = []
        for seg in clip_transcript:
            text = ""
            if lang_code == "en":
                text = seg.get("text", "").strip()
            elif lang_code == "es":
                text = seg.get("translations", {}).get("es", "").strip()
            if not text:
                continue
            speaker = seg.get("speaker", "").strip()
            speaker_prefix = f"<strong>{html.escape(speaker)}:</strong> " if speaker else ""
            escaped_text = html.escape(text)
            blocks.append(f"<!-- wp:paragraph -->\n<p>{speaker_prefix}{escaped_text}</p>\n<!-- /wp:paragraph -->")
        return blocks

    en_blocks = language_blocks("en") if include_english else []
    es_blocks = language_blocks("es") if include_spanish else []

    def append_blocks(blocks):
        content_parts.extend(blocks)

    if en_blocks and es_blocks:
        if spanish_presentation == "accordion":
            if primary_language == "es":
                primary_blocks = es_blocks
                secondary_blocks = en_blocks
                btn_text = "Read in English"
            else:
                primary_blocks = en_blocks
                secondary_blocks = es_blocks
                btn_text = "Leer en Español"

            summary_btn_style = (
                "display: inline-block; padding: 8px 18px; background-color: #0073aa; "
                "color: #ffffff; border-radius: 4px; font-weight: bold; cursor: pointer; "
                "margin-bottom: 16px; user-select: none; list-style: none; outline: none;"
            )
            content_parts.append(
                f'<details class="rtvs-language-accordion" style="margin-bottom: 24px;">'
                f'<summary role="button" style="{summary_btn_style}">{btn_text}</summary>'
                f'<div class="rtvs-secondary-transcript" style="margin-top: 12px;">'
            )
            append_blocks(secondary_blocks)
            content_parts.append('</div></details>')
            append_blocks(primary_blocks)
        elif spanish_presentation == "es_first":
            append_blocks(es_blocks)
            content_parts.append('<h2>English</h2>')
            append_blocks(en_blocks)
        else:
            append_blocks(en_blocks)
            content_parts.append('<h2>Español</h2>')
            append_blocks(es_blocks)
    elif en_blocks:
        append_blocks(en_blocks)
    elif es_blocks:
        append_blocks(es_blocks)

    # Optional Custom Notice Text
    settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
    custom_text = str(settings.value("wp_custom_text", "") or "").strip()
    custom_pos = str(settings.value("wp_custom_text_pos", "top") or "top").lower()
    no_snippet = str(settings.value("wp_custom_text_no_snippet", "true")).lower() in ("true", "1", "yes")

    if custom_text:
        text_escaped = html.escape(custom_text).replace("\n\n", "</p><p>").replace("\n", "<br/>")
        inner_html = f"<p>{text_escaped}</p>"
        snippet_attr = ' data-nosnippet="true"' if no_snippet else ""
        google_wrap_start = "<!--googleoff: all-->\n" if no_snippet else ""
        google_wrap_end = "\n<!--googleon: all-->" if no_snippet else ""
        custom_html = (
            f'<!-- wp:paragraph -->\n'
            f'<div{snippet_attr} class="rtvs-custom-notice" style="font-style: italic; opacity: 0.85; margin: 16px 0;">\n'
            f'{google_wrap_start}{inner_html}{google_wrap_end}\n'
            f'</div>\n<!-- /wp:paragraph -->'
        )
        if custom_pos == "top":
            insert_idx = 1 if media_url and len(content_parts) > 0 else 0
            content_parts.insert(insert_idx, custom_html)
        else:
            content_parts.append(custom_html)

    full_content = "\n".join(content_parts)

    # 4. Create Draft Post
    report_progress(4, "Creating WordPress draft…")
    post_data = client.create_post(
        title=post_title,
        content=full_content,
        excerpt=post_excerpt,
        status="draft",
        category_ids=category_ids,
        author_ids=author_ids,
        author_term_ids=author_term_ids,
        featured_media_id=featured_media_id,
    )

    post_id = post_data.get("id")
    if hasattr(main_window, "log_activity"):
        main_window.log_activity(f"[WORDPRESS] Created Draft Post #{post_id}: '{post_title}'")
    return post_data
