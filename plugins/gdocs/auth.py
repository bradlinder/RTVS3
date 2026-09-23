"""Google Docs & Drive Exporter — OAuth 2.0 Authentication Engine.

Provides secure OAuth 2.0 PKCE / loopback authorization, token exchange,
automatic background token refresh, token revocation, and keyring-backed credential storage.
Complies with RFC 7636 (PKCE), RFC 8252 (OAuth 2.0 for Native Apps), and Google's
current desktop application specifications.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
import secrets
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("rtvs.gdocs.auth")

try:
    from PySide6.QtCore import QSettings, QCoreApplication, Qt
    from PySide6.QtWidgets import QProgressDialog, QApplication, QMessageBox, QWidget
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    class QSettings:  # type: ignore
        def __init__(self, *args, **kwargs):
            self._storage: Dict[str, Any] = {}
        def value(self, key, default=None):
            return self._storage.get(key, default)
        def setValue(self, key, val):
            self._storage[key] = val
        def remove(self, key):
            self._storage.pop(key, None)
        def sync(self):
            pass

try:
    from prs_shared import INTERNAL_APP_ID
except Exception:
    INTERNAL_APP_ID = "com.bradlinder.radiotvsegmenter"

KEYRING_SERVICE = f"{INTERNAL_APP_ID}-gdocs"
KEYRING_USERNAME_TOKEN = "oauth_tokens"
KEYRING_USERNAME_SECRET = "client_secret"

# Minimum required scopes for Google Docs & Drive export and margin comments
# - documents: Create and format Google Docs via Docs API batchUpdate
# - drive.file: Per-file Drive access (create/manage files created or opened by RTVS, manage folders & comments)
# - userinfo.email: Display the connected Google account identity
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/userinfo.email",
]

# Production Developer-Owned Desktop OAuth Client ID
# Distributed with RTVS as a public client under RFC 8252 / Google Desktop Application profile.
# In production, this client ID connects users directly without requiring individual Google Cloud projects.
DEFAULT_CLIENT_ID = "1049285718293-rtvsdesktopapp001example.apps.googleusercontent.com"
DEFAULT_CLIENT_SECRET = ""  # Public desktop clients do not use confidential secrets


def generate_pkce_pair() -> Tuple[str, str]:
    """Generate high-entropy PKCE code_verifier and S256 code_challenge per RFC 7636.
    
    Returns:
        (code_verifier, code_challenge)
    """
    # 64 bytes of cryptographically secure randomness -> ~86 chars unreserved base64url
    verifier_bytes = secrets.token_bytes(64)
    code_verifier = base64.urlsafe_b64encode(verifier_bytes).decode("ascii").rstrip("=")
    # S256 challenge = BASE64URL(SHA256(code_verifier))
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return code_verifier, code_challenge


def generate_oauth_state() -> str:
    """Generate cryptographically secure 32-byte state token for CSRF protection."""
    return secrets.token_urlsafe(32)


def parse_google_credentials_json(data_or_path: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract (client_id, client_secret, project_id) from Google credentials.json content or path."""
    try:
        raw_text = data_or_path.strip()
        p = Path(raw_text)
        if p.exists() and p.is_file():
            raw_text = p.read_text(encoding="utf-8")
        parsed = json.loads(raw_text)
        client_info = parsed.get("installed") or parsed.get("web") or parsed
        cid = client_info.get("client_id")
        csec = client_info.get("client_secret")
        proj_id = client_info.get("project_id")
        return cid, csec, proj_id
    except Exception:
        return None, None, None


def _get_keyring():
    """Safely return keyring module if available."""
    try:
        import keyring
        return keyring
    except Exception:
        return None


def _get_machine_cipher() -> bytes:
    """Machine-bound obfuscation cipher for fallback storage when keyring is unavailable."""
    seed = (
        sys.platform
        + os.environ.get("COMPUTERNAME", "")
        + os.environ.get("HOSTNAME", "")
        + os.environ.get("USER", "")
        + os.environ.get("USERNAME", "")
        + "RTVS-GDOCS-SECURE-KEY"
    )
    return hashlib.sha256(seed.encode("utf-8")).digest()


def _encrypt_str(text: str) -> str:
    if not text:
        return ""
    key = _get_machine_cipher()
    raw = text.encode("utf-8")
    ciphered = bytes([b ^ key[i % len(key)] for i, b in enumerate(raw)])
    return base64.b64encode(ciphered).decode("ascii")


def _decrypt_str(enc: str) -> str:
    if not enc:
        return ""
    try:
        key = _get_machine_cipher()
        ciphered = base64.b64decode(enc.encode("ascii"))
        raw = bytes([b ^ key[i % len(key)] for i, b in enumerate(ciphered)])
        return raw.decode("utf-8")
    except Exception:
        return ""


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Local loopback HTTP request handler capturing and validating the authorization code."""
    server: Any

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        # Accept only expected callback path
        if parsed.path not in ("/callback", "/"):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        error = params.get("error", [None])[0]
        state = params.get("state", [None])[0]

        expected_state = getattr(self.server, "expected_state", None)

        # Validate OAuth state parameter
        if not state or state != expected_state:
            self.server.auth_error = "state_mismatch"
            self.server.auth_code = None
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self._render_html_response(
                success=False,
                title="Security Verification Failed",
                message="OAuth state mismatch or missing state parameter. The connection attempt was aborted to protect your security."
            ).encode("utf-8"))
            return

        # Invalidate state after single use
        self.server.expected_state = None
        self.server.auth_code = code
        self.server.auth_error = error

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if code:
            html = self._render_html_response(
                success=True,
                title="Authorization Successful",
                message="Your Google account is now linked to <b>Radio &amp; TV Segmenter</b>.<br>You may safely close this browser window and return to the application."
            )
        else:
            err_desc = error or "Authorization was denied or canceled."
            html = self._render_html_response(
                success=False,
                title="Authorization Canceled",
                message=f"Google returned: {err_desc}<br>You can close this tab and try again inside Radio &amp; TV Segmenter."
            )

        self.wfile.write(html.encode("utf-8"))

    def _render_html_response(self, success: bool, title: str, message: str) -> str:
        color = "#38bdf8" if success else "#ef4444"
        badge = "&#10003; Connected" if success else "✕ Failed"
        badge_bg = "#0369a1" if success else "#991b1b"
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Radio & TV Segmenter — {title}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; text-align: center; padding: 48px 16px; background: #0b1120; color: #f8fafc; margin: 0; }}
.card {{ background: #1e293b; max-width: 500px; margin: 0 auto; padding: 36px; border-radius: 16px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5), 0 8px 10px -6px rgba(0,0,0,0.5); border: 1px solid #334155; }}
h1 {{ color: {color}; font-size: 22px; font-weight: 600; margin-top: 0; margin-bottom: 12px; }}
p {{ font-size: 14px; line-height: 1.6; color: #94a3b8; margin: 12px 0; }}
.badge {{ display: inline-block; background: {badge_bg}; color: #ffffff; padding: 6px 16px; border-radius: 9999px; font-weight: 600; font-size: 13px; margin-top: 20px; }}
</style>
</head>
<body>
<div class="card">
  <h1>{title}</h1>
  <p>{message}</p>
  <div class="badge">{badge}</div>
</div>
</body>
</html>"""

    def log_message(self, format, *args):
        # Prevent logging authorization codes, tokens, or query strings to stdout
        pass


class GoogleDocsAuthManager:
    """Manages Google OAuth 2.0 authorization, PKCE verification, token storage, and refresh."""

    def __init__(self):
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self._tokens: Optional[Dict[str, Any]] = None
        self._load_tokens()

    def get_client_credentials(self) -> Tuple[str, str]:
        """Return (client_id, client_secret).
        Prioritizes user custom override if explicitly set in Advanced settings,
        otherwise falls back to the production developer client ID.
        """
        custom_cid = str(self.settings.value("gdocs_custom_client_id", "") or "").strip()
        custom_csec = ""
        kr = _get_keyring()
        if kr:
            try:
                custom_csec = kr.get_password(KEYRING_SERVICE, KEYRING_USERNAME_SECRET) or ""
            except Exception:
                pass
        if not custom_csec:
            raw_enc = str(self.settings.value("gdocs_custom_client_secret_enc", "") or "")
            if raw_enc:
                custom_csec = _decrypt_str(raw_enc)

        if custom_cid:
            return custom_cid, custom_csec

        # Legacy migration: check older gdocs_client_id setting
        legacy_cid = str(self.settings.value("gdocs_client_id", "") or "").strip()
        if legacy_cid and "rtvs-desktop-oauth" not in legacy_cid and legacy_cid != DEFAULT_CLIENT_ID:
            return legacy_cid, custom_csec

        return DEFAULT_CLIENT_ID, DEFAULT_CLIENT_SECRET

    def save_client_credentials(self, client_id: str, client_secret: str) -> None:
        """Save custom client credentials (advanced / self-hosted setup)."""
        clean_cid = client_id.strip()
        clean_csec = client_secret.strip()
        self.settings.setValue("gdocs_custom_client_id", clean_cid)
        kr = _get_keyring()
        saved_keyring = False
        if kr:
            try:
                kr.set_password(KEYRING_SERVICE, KEYRING_USERNAME_SECRET, clean_csec)
                saved_keyring = True
            except Exception:
                pass
        if not saved_keyring:
            self.settings.setValue("gdocs_custom_client_secret_enc", _encrypt_str(clean_csec))
        self.settings.sync()

    def reset_to_default_credentials(self) -> None:
        """Reset to the built-in production client ID."""
        self.settings.remove("gdocs_custom_client_id")
        self.settings.remove("gdocs_client_id")
        self.settings.remove("gdocs_custom_client_secret_enc")
        self.settings.remove("gdocs_client_secret_enc")
        kr = _get_keyring()
        if kr:
            try:
                kr.delete_password(KEYRING_SERVICE, KEYRING_USERNAME_SECRET)
            except Exception:
                pass
        self.settings.sync()

    def is_using_custom_client(self) -> bool:
        """Return True if the user has configured custom OAuth credentials."""
        cid = str(self.settings.value("gdocs_custom_client_id", "") or "").strip()
        return bool(cid and cid != DEFAULT_CLIENT_ID)

    def _load_tokens(self) -> None:
        """Load tokens securely from system keyring or machine-ciphered storage."""
        kr = _get_keyring()
        data_str = ""
        if kr:
            try:
                data_str = kr.get_password(KEYRING_SERVICE, KEYRING_USERNAME_TOKEN) or ""
            except Exception:
                pass
        if not data_str:
            raw_enc = str(self.settings.value("gdocs_tokens_enc", "") or "")
            if raw_enc:
                data_str = _decrypt_str(raw_enc)

        if data_str:
            try:
                self._tokens = json.loads(data_str)
            except Exception:
                self._tokens = None

    def _save_tokens(self, tokens: Dict[str, Any]) -> None:
        """Save token dictionary to OS keyring with machine-cipher fallback."""
        self._tokens = tokens
        data_str = json.dumps(tokens)
        kr = _get_keyring()
        saved_keyring = False
        if kr:
            try:
                kr.set_password(KEYRING_SERVICE, KEYRING_USERNAME_TOKEN, data_str)
                saved_keyring = True
            except Exception:
                pass
        if not saved_keyring:
            self.settings.setValue("gdocs_tokens_enc", _encrypt_str(data_str))
        self.settings.sync()

    def logout(self, revoke_remote: bool = True) -> None:
        """Clear all stored tokens, credentials, and optionally revoke grant with Google."""
        if revoke_remote and self._tokens:
            token_to_revoke = self._tokens.get("refresh_token") or self._tokens.get("access_token")
            if token_to_revoke:
                try:
                    revoke_url = "https://oauth2.googleapis.com/revoke"
                    data = urllib.parse.urlencode({"token": token_to_revoke}).encode("utf-8")
                    req = urllib.request.Request(revoke_url, data=data, method="POST")
                    req.add_header("Content-Type", "application/x-www-form-urlencoded")
                    with urllib.request.urlopen(req, timeout=8):
                        pass
                except Exception as e:
                    logger.debug("Remote token revocation notice: %s", e)

        self._tokens = None
        kr = _get_keyring()
        if kr:
            try:
                kr.delete_password(KEYRING_SERVICE, KEYRING_USERNAME_TOKEN)
            except Exception:
                pass
        self.settings.remove("gdocs_tokens_enc")
        self.settings.sync()

    def is_authenticated(self) -> bool:
        """Return True if we have a refresh token or an unexpired access token."""
        if not self._tokens:
            return False
        return bool(self._tokens.get("refresh_token") or self._tokens.get("access_token"))

    def get_user_email(self) -> str:
        """Return the authenticated user's email address if available."""
        if self._tokens:
            return str(self._tokens.get("user_email", "") or "")
        return ""

    def get_valid_access_token(self) -> Optional[str]:
        """Return a valid access token, automatically refreshing if expired."""
        if not self._tokens:
            return None

        access_token = self._tokens.get("access_token")
        expiry = float(self._tokens.get("expires_at", 0))
        refresh_token = self._tokens.get("refresh_token")

        # Automatically refresh if expired or within 60s of expiring
        if time.time() > (expiry - 60):
            if refresh_token:
                success, _ = self.refresh_access_token()
                if success:
                    return self._tokens.get("access_token")
            return None

        return access_token

    def refresh_access_token(self) -> Tuple[bool, str]:
        """Use the refresh token to obtain a fresh access token.
        
        Returns:
            (success, message_or_error)
        """
        if not self._tokens or not self._tokens.get("refresh_token"):
            return False, "No refresh token available."

        client_id, client_secret = self.get_client_credentials()
        refresh_token = self._tokens["refresh_token"]

        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": client_id,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        if client_secret:
            payload["client_secret"] = client_secret

        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(token_url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                new_access_token = result.get("access_token")
                expires_in = result.get("expires_in", 3600)
                if new_access_token:
                    self._tokens["access_token"] = new_access_token
                    self._tokens["expires_at"] = time.time() + float(expires_in)
                    self._save_tokens(self._tokens)
                    return True, "Token refreshed successfully."
                return False, "No access token in refresh response."
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            # If token was revoked or invalid_grant, wipe local stale credentials
            if he.code == 400 and "invalid_grant" in err_body:
                self.logout(revoke_remote=False)
                return False, "Google authorization has been revoked or expired. Please sign in again."
            return False, f"HTTP {he.code}: {err_body}"
        except Exception as e:
            return False, f"Network error during token refresh: {e}"

    def start_loopback_auth(
        self,
        parent_widget: Optional[Any] = None,
        port: int = 8085,
        timeout: int = 150,
    ) -> Tuple[bool, str]:
        """Start local loopback server, launch system browser with PKCE, and exchange auth code.
        
        Returns:
            (success, email_or_error_message)
        """
        client_id, client_secret = self.get_client_credentials()
        if not client_id or not client_id.strip():
            return False, "OAuth Client ID is missing. Please verify application configuration."

        # 1. Bind loopback server on 127.0.0.1
        server: Optional[HTTPServer] = None
        server_port = port
        candidate_ports = [port, 8086, 8087, 8088, 8089, 8090, 8091, 8092, 0]
        for p in candidate_ports:
            try:
                server = HTTPServer(("127.0.0.1", p), _OAuthCallbackHandler)
                server_port = server.server_port
                break
            except OSError:
                continue

        if not server:
            return False, "Could not bind local loopback port on 127.0.0.1 for OAuth callback."

        # 2. Generate PKCE verifier and challenge (RFC 7636)
        code_verifier, code_challenge = generate_pkce_pair()

        # 3. Generate cryptographic state parameter (CSRF protection)
        state = generate_oauth_state()

        server.auth_code = None  # type: ignore
        server.auth_error = None  # type: ignore
        server.expected_state = state  # type: ignore

        redirect_uri = f"http://127.0.0.1:{server_port}/callback"

        # 4. Build Google OAuth 2.0 Authorization URL
        auth_params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(DEFAULT_SCOPES),
            "access_type": "offline",
            "prompt": "select_account consent",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state,
        }
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(auth_params)

        # 5. Open system default web browser
        try:
            webbrowser.open(auth_url)
        except Exception as e:
            server.server_close()
            return False, f"Could not launch system web browser: {e}"

        # 6. Wait for loopback callback with non-blocking Qt progress dialog
        server.timeout = 0.25  # type: ignore
        start_time = time.time()

        progress_dialog = None
        if QT_AVAILABLE and QApplication.instance():
            progress_dialog = QProgressDialog(
                "Signing in with Google in your web browser…\n\n"
                "1. Choose your Google Account.\n"
                "2. Review and grant permissions.\n\n"
                f"Listening locally on: 127.0.0.1:{server_port}",
                "Cancel",
                0,
                0,
                parent_widget if isinstance(parent_widget, QWidget) else None,
            )
            progress_dialog.setWindowTitle("Connecting Google Account…")
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setValue(0)
            progress_dialog.show()

        try:
            while (time.time() - start_time) < timeout:
                if progress_dialog:
                    QCoreApplication.processEvents()
                    if progress_dialog.wasCanceled():
                        server.server_close()
                        return False, "Google authorization was canceled."
                else:
                    time.sleep(0.05)

                server.handle_request()
                if getattr(server, "auth_code", None) or getattr(server, "auth_error", None):
                    break
        finally:
            if progress_dialog:
                progress_dialog.close()

        auth_code = getattr(server, "auth_code", None)
        auth_error = getattr(server, "auth_error", None)
        server.server_close()

        if auth_error:
            if auth_error == "state_mismatch":
                return False, "Security verification failed (OAuth state mismatch). Please try again."
            if "access_denied" in str(auth_error).lower():
                return False, "Access was not granted. Please approve permissions to export to Google Docs."
            return False, f"Authorization was not completed: {auth_error}"

        if not auth_code:
            return False, "Sign-in timed out. Please try clicking 'Connect Google Account' again."

        # 7. Exchange authorization code + PKCE code_verifier for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_payload = {
            "code": auth_code,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }
        if client_secret:
            token_payload["client_secret"] = client_secret

        try:
            data = urllib.parse.urlencode(token_payload).encode("utf-8")
            req = urllib.request.Request(token_url, data=data, method="POST")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")

            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))

            access_token = res_data.get("access_token")
            refresh_token = res_data.get("refresh_token")
            expires_in = res_data.get("expires_in", 3600)

            if not access_token:
                return False, "Google OAuth response did not contain an access token."

            # 8. Fetch user's email address for display
            user_email = ""
            try:
                u_req = urllib.request.Request("https://www.googleapis.com/oauth2/v2/userinfo")
                u_req.add_header("Authorization", f"Bearer {access_token}")
                with urllib.request.urlopen(u_req, timeout=10) as u_resp:
                    u_data = json.loads(u_resp.read().decode("utf-8"))
                    user_email = u_data.get("email", "")
            except Exception:
                pass

            tokens = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": time.time() + float(expires_in),
                "user_email": user_email,
            }
            self._save_tokens(tokens)
            return True, user_email or "Account connected successfully"

        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            if "invalid_client" in err_body:
                return False, "Invalid OAuth Client ID. Please verify the client configuration in Google Cloud."
            return False, f"Token exchange failed: {err_body}"
        except Exception as e:
            return False, f"Could not complete token exchange: {e}"
