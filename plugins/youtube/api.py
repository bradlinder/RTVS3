"""YouTube Data API v3 Client & Direct Video Upload Engine.

Provides:
- OAuth 2.0 PKCE authentication for YouTube Data API v3
- Resumable video upload protocol with real-time transfer progress, speed, and ETA tracking
- Custom video thumbnail frame attachment (thumbnails.set)
- Automatic Closed Caption (.srt) track insertion (captions.insert)
- Channel identity and quota verification
"""
from __future__ import annotations

import json
import logging
import mimetypes
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("rtvs.youtube.api")

try:
    from plugins.gdocs.auth import (
        GoogleDocsAuthManager,
        generate_pkce_pair,
        generate_oauth_state,
        DEFAULT_CLIENT_ID,
        _OAuthCallbackHandler,
    )
except ImportError:
    GoogleDocsAuthManager = None
    DEFAULT_CLIENT_ID = "1049285718293-rtvsdesktopapp001example.apps.googleusercontent.com"

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
YOUTUBE_UPLOAD_BASE = "https://www.googleapis.com/upload/youtube/v3"

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/userinfo.email",
]

# Standard YouTube Video Categories
YOUTUBE_CATEGORIES = [
    ("25", "News & Politics"),
    ("24", "Entertainment"),
    ("22", "People & Blogs"),
    ("27", "Education"),
    ("28", "Science & Technology"),
    ("10", "Music"),
    ("17", "Sports"),
    ("23", "Comedy"),
    ("1", "Film & Animation"),
    ("26", "Howto & Style"),
]


class YouTubeAuthManager(GoogleDocsAuthManager):
    """Specialized OAuth 2.0 PKCE manager for YouTube Data API v3 permissions."""

    def __init__(self):
        super().__init__()
        # In multi-service mode, we request YouTube upload scopes
        self.scopes = YOUTUBE_SCOPES

    def get_authorization_url(self, port: int, state: str, code_challenge: str) -> str:
        client_id, _ = self.get_client_credentials()
        redirect_uri = f"http://127.0.0.1:{port}/callback"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


class YouTubeApiClient:
    """Production client for YouTube Data API v3."""

    def __init__(self, auth_manager: Optional[YouTubeAuthManager] = None):
        self.auth = auth_manager or YouTubeAuthManager()

    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        token = self.auth.get_valid_access_token()
        if not token:
            raise PermissionError("Not authenticated with YouTube. Please connect your Google / YouTube account.")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
            "Accept": "application/json",
        }

    def get_channel_info(self) -> Dict[str, Any]:
        """Fetch the authenticated user's YouTube channel snippet and statistics."""
        url = f"{YOUTUBE_API_BASE}/channels?part=snippet,statistics&mine=true"
        headers = self._get_headers()
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("items", [])
                if items:
                    return items[0]
                return {}
        except Exception as exc:
            logger.warning(f"Failed to fetch YouTube channel info: {exc}")
            return {}

    def upload_video_resumable(
        self,
        video_path: str | Path,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        category_id: str = "25",
        privacy_status: str = "private",
        progress_callback: Optional[Callable[[int, int, float, float], None]] = None,
        cancel_event: Optional[Any] = None,
        chunk_size: int = 2 * 1024 * 1024,  # 2MB chunks (must be multiple of 256KB)
    ) -> Dict[str, Any]:
        """Upload video file using YouTube's Resumable Upload protocol.
        
        Args:
            video_path: Path to video file (.mp4, .mov, etc.)
            title: Video title (max 100 characters)
            description: Video description including chapters (max 5000 characters)
            tags: List of search keywords/tags
            category_id: YouTube category ID (default '25' = News & Politics)
            privacy_status: 'public', 'unlisted', or 'private'
            progress_callback: (bytes_uploaded, total_bytes, speed_bps, eta_seconds) -> None
            cancel_event: threading.Event or object with is_set()
            chunk_size: Upload chunk size in bytes (multiple of 256KB)

        Returns:
            Dict response with video resource data including 'id' and 'snippet'.
        """
        p = Path(video_path)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        total_bytes = p.stat().st_size
        mime_type, _ = mimetypes.guess_type(str(p))
        mime_type = mime_type or "video/mp4"

        # 1. Initiate Resumable Upload Session
        init_url = f"{YOUTUBE_UPLOAD_BASE}/videos?uploadType=resumable&part=snippet,status"
        init_headers = self._get_headers(content_type="application/json; charset=UTF-8")
        init_headers["X-Upload-Content-Type"] = mime_type
        init_headers["X-Upload-Content-Length"] = str(total_bytes)

        metadata_body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags or [],
                "categoryId": str(category_id),
            },
            "status": {
                "privacyStatus": privacy_status.lower(),
                "selfDeclaredMadeForKids": False,
            },
        }

        init_data = json.dumps(metadata_body).encode("utf-8")
        init_req = urllib.request.Request(init_url, data=init_data, headers=init_headers, method="POST")

        try:
            with urllib.request.urlopen(init_req, timeout=30) as resp:
                upload_url = resp.headers.get("Location")
                if not upload_url:
                    raise RuntimeError("YouTube API did not return a resumable upload location URL.")
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"YouTube Upload Initialization failed (HTTP {err.code}): {err_body}")

        # 2. Stream File in Chunks
        bytes_uploaded = 0
        start_time = time.time()

        with open(p, "rb") as vf:
            while bytes_uploaded < total_bytes:
                if cancel_event and getattr(cancel_event, "is_set", lambda: False)():
                    raise RuntimeError("Upload cancelled by user.")

                chunk = vf.read(chunk_size)
                if not chunk:
                    break

                chunk_len = len(chunk)
                start_byte = bytes_uploaded
                end_byte = bytes_uploaded + chunk_len - 1

                chunk_headers = {
                    "Content-Type": mime_type,
                    "Content-Length": str(chunk_len),
                    "Content-Range": f"bytes {start_byte}-{end_byte}/{total_bytes}",
                }

                chunk_req = urllib.request.Request(upload_url, data=chunk, headers=chunk_headers, method="PUT")

                try:
                    with urllib.request.urlopen(chunk_req, timeout=60) as resp:
                        bytes_uploaded += chunk_len
                        elapsed = max(0.1, time.time() - start_time)
                        speed = bytes_uploaded / elapsed
                        remaining_bytes = max(0, total_bytes - bytes_uploaded)
                        eta = remaining_bytes / speed if speed > 0 else 0.0

                        if progress_callback:
                            try:
                                progress_callback(bytes_uploaded, total_bytes, speed, eta)
                            except Exception:
                                pass

                        if resp.status in (200, 201):
                            res_body = resp.read().decode("utf-8")
                            return json.loads(res_body)

                except urllib.error.HTTPError as err:
                    if err.code == 308:  # 308 Resume Incomplete (expected during chunking)
                        bytes_uploaded += chunk_len
                        elapsed = max(0.1, time.time() - start_time)
                        speed = bytes_uploaded / elapsed
                        remaining_bytes = max(0, total_bytes - bytes_uploaded)
                        eta = remaining_bytes / speed if speed > 0 else 0.0

                        if progress_callback:
                            try:
                                progress_callback(bytes_uploaded, total_bytes, speed, eta)
                            except Exception:
                                pass
                    else:
                        err_body = err.read().decode("utf-8", errors="ignore")
                        raise RuntimeError(f"YouTube Upload Chunk Failed (HTTP {err.code}): {err_body}")

        return {"status": "completed", "bytes_uploaded": bytes_uploaded}

    def set_thumbnail(self, video_id: str, image_path: str | Path) -> Dict[str, Any]:
        """Upload custom thumbnail for a video."""
        p = Path(image_path)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Thumbnail image file not found: {image_path}")

        mime_type, _ = mimetypes.guess_type(str(p))
        mime_type = mime_type or "image/jpeg"

        url = f"{YOUTUBE_UPLOAD_BASE}/thumbnails/set?videoId={urllib.parse.quote(video_id)}&uploadType=media"
        headers = self._get_headers(content_type=mime_type)

        image_data = p.read_bytes()
        req = urllib.request.Request(url, data=image_data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="ignore")
            logger.warning(f"Failed to set custom thumbnail: HTTP {err.code} - {err_body}")
            raise RuntimeError(f"Failed to set thumbnail (HTTP {err.code}): {err_body}")

    def upload_caption_track(
        self,
        video_id: str,
        srt_content_or_path: str | Path,
        language: str = "en",
        name: str = "English",
        is_draft: bool = False,
    ) -> Dict[str, Any]:
        """Upload Closed Captions (.srt track) directly to the uploaded YouTube video."""
        if isinstance(srt_content_or_path, (str, Path)) and os.path.exists(str(srt_content_or_path)):
            srt_bytes = Path(srt_content_or_path).read_bytes()
        else:
            srt_bytes = str(srt_content_or_path).encode("utf-8")

        # 1. Initiate Caption Resumable Upload
        init_url = f"{YOUTUBE_UPLOAD_BASE}/captions?uploadType=resumable&part=snippet"
        init_headers = self._get_headers(content_type="application/json; charset=UTF-8")
        init_headers["X-Upload-Content-Type"] = "*/*"
        init_headers["X-Upload-Content-Length"] = str(len(srt_bytes))

        meta = {
            "snippet": {
                "videoId": video_id,
                "language": language,
                "name": name,
                "isDraft": is_draft,
            }
        }
        init_data = json.dumps(meta).encode("utf-8")
        init_req = urllib.request.Request(init_url, data=init_data, headers=init_headers, method="POST")

        with urllib.request.urlopen(init_req, timeout=30) as resp:
            upload_url = resp.headers.get("Location")
            if not upload_url:
                raise RuntimeError("YouTube API did not return caption upload URL.")

        # 2. Upload caption content
        cap_headers = {
            "Content-Type": "*/*",
            "Content-Length": str(len(srt_bytes)),
        }
        cap_req = urllib.request.Request(upload_url, data=srt_bytes, headers=cap_headers, method="PUT")
        with urllib.request.urlopen(cap_req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
