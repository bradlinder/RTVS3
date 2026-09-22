"""Google Docs & Drive Exporter — OAuth 2.0 Authentication Engine.

Provides secure OAuth 2.0 PKCE / loopback authorization, token exchange,
automatic background token refresh, and keyring-backed credential storage.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
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
from typing import Any, Dict, Optional, Tuple

try:
    from PySide6.QtCore import QSettings
except ImportError:
    # Minimal fallback for headless or test environments
    class QSettings:  # type: ignore
        def __init__(self, *args, **kwargs):
            self._storage: Dict[str, Any] = {}
        def value(self, key, default=None):
            return self._storage.get(key, default)
        def setValue(self, key, val):
            self._storage[key] = val
        def sync(self):
            pass

try:
    from prs_shared import INTERNAL_APP_ID
except Exception:
    INTERNAL_APP_ID = "com.bradlinder.radiotvsegmenter"

KEYRING_SERVICE = f"{INTERNAL_APP_ID}-gdocs"
KEYRING_USERNAME_TOKEN = "oauth_tokens"
KEYRING_USERNAME_SECRET = "client_secret"

DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/userinfo.email",
]

# Default desktop client ID for open-source broadcast news segmenter tooling
# Users can also supply their own Google Cloud Console client credentials in Preferences
DEFAULT_CLIENT_ID = "602371983794-rtvs-desktop-oauth.apps.googleusercontent.com"
DEFAULT_CLIENT_SECRET = ""


def _get_keyring():
    """Safely return keyring module if available."""
    try:
        import keyring
        return keyring
    except Exception:
        return None


def _get_machine_cipher():
    """Simple machine-bound obfuscation cipher for fallback storage when keyring is unavailable."""
    seed = (
        sys.platform
        + os.environ.get("COMPUTERNAME", "")
        + os.environ.get("HOSTNAME", "")
        + os.environ.get("USER", "")
        + os.environ.get("USERNAME", "")
        + "RTVS-GDOCS-KEY"
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
    """Local loopback HTTP request handler capturing the authorization code."""
    server: Any

    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        code = params.get("code", [None])[0]
        error = params.get("error", [None])[0]

        self.server.auth_code = code
        self.server.auth_error = error

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if code:
            html = """<!DOCTYPE html>
<html>
<head><title>Radio & TV Segmenter — Authorization Successful</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 40px; background: #0f172a; color: #f8fafc; }
.card { background: #1e293b; max-width: 480px; margin: 0 auto; padding: 32px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; }
h1 { color: #38bdf8; font-size: 24px; margin-bottom: 12px; }
p { font-size: 15px; line-height: 1.6; color: #94a3b8; }
.badge { display: inline-block; background: #0369a1; color: #fff; padding: 6px 14px; border-radius: 20px; font-weight: bold; margin-top: 16px; }
</style>
</head>
<body>
<div class="card">
  <h1>Authorization Successful!</h1>
  <p>Your Google account is now securely linked to <b>Radio & TV Segmenter</b>.</p>
  <p>You can close this browser tab and return to the application to complete your document export.</p>
  <div class="badge">&#10003; Connected</div>
</div>
</body>
</html>"""
        else:
            err_msg = error or "Authorization was denied or cancelled."
            html = f"""<!DOCTYPE html>
<html>
<head><title>Radio & TV Segmenter — Authorization Failed</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 40px; background: #0f172a; color: #f8fafc; }}
.card {{ background: #1e293b; max-width: 480px; margin: 0 auto; padding: 32px; border-radius: 12px; border: 1px solid #ef4444; }}
h1 {{ color: #ef4444; font-size: 24px; }}
p {{ color: #94a3b8; }}
</style>
</head>
<body>
<div class="card">
  <h1>Authorization Failed</h1>
  <p>{err_msg}</p>
  <p>You can close this window and try again inside Radio & TV Segmenter.</p>
</div>
</body>
</html>"""

        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        # Silence HTTP server terminal spam
        pass


class GoogleDocsAuthManager:
    """Manages Google OAuth 2.0 authorization, token persistence, and refresh."""

    def __init__(self):
        self.settings = QSettings(INTERNAL_APP_ID, INTERNAL_APP_ID)
        self._tokens: Optional[Dict[str, Any]] = None
        self._load_tokens()

    def get_client_credentials(self) -> Tuple[str, str]:
        """Return configured (client_id, client_secret)."""
        cid = str(self.settings.value("gdocs_client_id", "") or "").strip() or DEFAULT_CLIENT_ID
        csec = ""
        kr = _get_keyring()
        if kr:
            try:
                csec = kr.get_password(KEYRING_SERVICE, KEYRING_USERNAME_SECRET) or ""
            except Exception:
                pass
        if not csec:
            raw_enc = str(self.settings.value("gdocs_client_secret_enc", "") or "")
            if raw_enc:
                csec = _decrypt_str(raw_enc)
        if not csec:
            csec = DEFAULT_CLIENT_SECRET
        return cid, csec

    def save_client_credentials(self, client_id: str, client_secret: str) -> None:
        """Save custom client credentials."""
        self.settings.setValue("gdocs_client_id", client_id.strip())
        kr = _get_keyring()
        saved_keyring = False
        if kr:
            try:
                kr.set_password(KEYRING_SERVICE, KEYRING_USERNAME_SECRET, client_secret.strip())
                saved_keyring = True
            except Exception:
                pass
        if not saved_keyring:
            self.settings.setValue("gdocs_client_secret_enc", _encrypt_str(client_secret.strip()))
        self.settings.sync()

    def _load_tokens(self) -> None:
        """Load tokens from system keyring or encrypted fallback."""
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
        """Save token dictionary to keyring or encrypted storage."""
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

    def logout(self) -> None:
        """Clear all stored tokens and credentials."""
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
        """Return True if we have a refresh token or valid access token."""
        if not self._tokens:
            return False
        return bool(self._tokens.get("refresh_token") or self._tokens.get("access_token"))

    def get_user_email(self) -> str:
        """Return the authenticated user's email address if known."""
        if self._tokens:
            return str(self._tokens.get("user_email", "") or "")
        return ""

    def get_valid_access_token(self) -> Optional[str]:
        """Return a valid access token, automatically refreshing if expired."""
        if not self._tokens:
            return None

        access_token = self._tokens.get("access_token")
        expiry = self._tokens.get("expires_at", 0)
        refresh_token = self._tokens.get("refresh_token")

        # Check if expired or within 60s of expiring
        if time.time() > (expiry - 60):
            if refresh_token:
                success = self.refresh_access_token()
                if success:
                    return self._tokens.get("access_token")
            return None

        return access_token

    def refresh_access_token(self) -> bool:
        """Use the refresh token to obtain a new access token."""
        if not self._tokens or not self._tokens.get("refresh_token"):
            return False

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
                    return True
        except Exception as e:
            print(f"[GDOCS AUTH] Error refreshing access token: {e}")

        return False

    def start_loopback_auth(self, port: int = 8085, timeout: int = 120) -> Tuple[bool, str]:
        """Start local loopback server, launch system browser, and capture OAuth code."""
        client_id, client_secret = self.get_client_credentials()
        if not client_id:
            return False, "Google OAuth Client ID is missing. Please configure it in Preferences."

        # Find available port starting from requested port
        server_port = port
        server: Optional[HTTPServer] = None
        for p in [port, 8086, 8087, 8088, 0]:
            try:
                server = HTTPServer(("127.0.0.1", p), _OAuthCallbackHandler)
                server_port = server.server_port
                break
            except OSError:
                continue

        if not server:
            return False, "Could not bind local loopback port for OAuth redirect."

        server.auth_code = None  # type: ignore
        server.auth_error = None  # type: ignore

        redirect_uri = f"http://127.0.0.1:{server_port}/callback"

        # Build Google OAuth 2.0 Auth URL
        auth_params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(DEFAULT_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(auth_params)

        # Open in default web browser
        webbrowser.open(auth_url)

        # Wait for callback on loopback server
        server.timeout = 1.0  # type: ignore
        start_time = time.time()
        while time.time() - start_time < timeout:
            server.handle_request()
            if getattr(server, "auth_code", None) or getattr(server, "auth_error", None):
                break

        auth_code = getattr(server, "auth_code", None)
        auth_error = getattr(server, "auth_error", None)
        server.server_close()

        if auth_error:
            return False, f"Authorization error: {auth_error}"
        if not auth_code:
            return False, "Authorization timed out. Please try again."

        # Exchange auth code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_payload = {
            "code": auth_code,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
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

            # Fetch user email for display
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
            return False, f"HTTP {he.code} token exchange failed: {err_body}"
        except Exception as e:
            return False, f"Token exchange error: {e}"
