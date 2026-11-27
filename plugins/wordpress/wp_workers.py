"""Background QThread worker for publishing individual WordPress stories."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QThread, Signal

if TYPE_CHECKING:
    from plugins.wordpress.client import WordPressClient


class WordPressPublishWorker(QThread):
    """Background thread that uploads featured media and publishes a WordPress post."""

    finished_signal = Signal(bool, str, object)

    def __init__(
        self,
        client: WordPressClient,
        title: str,
        content: str,
        excerpt: str,
        status: str,
        image_path: Optional[str],
        image_caption: str = "",
        image_alt_text: str = "",
    ):
        super().__init__()
        self.client = client
        self.title = title
        self.content = content
        self.excerpt = excerpt
        self.status = status
        self.image_path = image_path
        self.image_caption = str(image_caption or "")
        self.image_alt_text = str(image_alt_text or "")

    def run(self):
        try:
            featured_media_id = None
            if self.image_path and Path(self.image_path).exists():
                upload_res = self.client.upload_media(self.image_path)
                featured_media_id = upload_res.get("id")
                cap = self.image_caption.strip()
                alt = self.image_alt_text.strip()
                if featured_media_id and (cap or alt) and hasattr(self.client, "update_media_metadata"):
                    try:
                        self.client.update_media_metadata(
                            int(featured_media_id),
                            caption=cap or None,
                            alt_text=alt or None,
                        )
                    except Exception:
                        pass

            # Create post
            post_res = self.client.create_post(
                title=self.title,
                content=self.content,
                excerpt=self.excerpt,
                status=self.status,
            )

            # If featured media was uploaded, attach it
            if featured_media_id and post_res.get("id"):
                import requests
                post_id = post_res["id"]
                url = f"{self.client.api_base}/posts/{post_id}"
                requests.post(url, auth=self.client._get_auth(), json={"featured_media": featured_media_id}, timeout=20)
                post_res["featured_media"] = featured_media_id

            self.finished_signal.emit(True, "Success", post_res)
        except Exception as exc:
            self.finished_signal.emit(False, str(exc), None)


class YouTubeThumbnailFetchWorker(QThread):
    """Background thread that downloads and caches a YouTube video's default thumbnail."""

    finished_signal = Signal(str, str)

    def __init__(self, video_id: str, thumbnail_url: str = "", timeout: float = 8.0):
        super().__init__()
        self.video_id = str(video_id or "").strip()
        self.thumbnail_url = str(thumbnail_url or "").strip()
        self.timeout = float(timeout)

    def run(self):
        try:
            if self.isInterruptionRequested():
                self.finished_signal.emit(self.video_id, "")
                return
            from plugins.wordpress.wp_thumbnail_defaults import ensure_youtube_thumbnail_cached

            cached = ensure_youtube_thumbnail_cached(
                self.video_id,
                thumbnail_url=self.thumbnail_url,
                timeout=self.timeout,
            )
            self.finished_signal.emit(self.video_id, str(cached) if cached else "")
        except Exception:
            self.finished_signal.emit(self.video_id, "")


__all__ = ["WordPressPublishWorker", "YouTubeThumbnailFetchWorker"]
