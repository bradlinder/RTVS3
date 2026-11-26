"""WordPress Publisher Plugin for Radio & TV Segmenter.

Allows direct publishing of audio/video stories to WordPress with
custom excerpt, author assignment, categories, and custom featured image
(local file or video frame grab at playhead/story timestamp).
"""
from __future__ import annotations

from typing import Any, Callable, List

from plugins.base import BasePlugin, PluginManifest
from plugins.wordpress.wp_post_builder import capture_video_frame
from plugins.wordpress.wp_publish_dialog import WordPressPublishDialog
from plugins.wordpress.wp_workers import WordPressPublishWorker


class Plugin(BasePlugin):
    """WordPress Plugin implementation hooking into RTVS."""

    def __init__(self, manifest: PluginManifest, app: Any = None):
        super().__init__(manifest, app)

    def on_load(self) -> bool:
        return True

    def get_export_destinations(self) -> List[Any]:
        from plugins.wordpress.export_destination import WordPressExportDestination
        return [WordPressExportDestination(self)]

    def get_file_open_actions(self) -> List[tuple[str, Callable]]:
        return [
            ("Open Existing WordPress Episode...", self.open_load_existing_episode_dialog),
        ]

    def get_remote_open_actions(self) -> List[tuple[str, Callable]]:
        return [
            ("From Existing WordPress Post...", self.open_load_existing_episode_dialog),
        ]

    def can_redownload_remote_source(self, source_meta: dict) -> bool:
        return isinstance(source_meta, dict) and str(source_meta.get("provider") or "").strip().lower() == "wordpress"

    def redownload_remote_source(self, source_meta: dict, parent: Any = None):
        from plugins.wordpress.episode_lookup import download_wp_episode_audio
        audio_url = str(source_meta.get("audio_url") or source_meta.get("source_url") or "").strip()
        if not audio_url:
            return None
        post_info = {
            "id": source_meta.get("wp_post_id") or source_meta.get("source_id") or "episode",
            "slug": source_meta.get("slug") or "",
            "title": source_meta.get("title") or "WordPress Episode",
            "url": str(source_meta.get("source_url") or ""),
            "audio_url": audio_url,
            "date_display": str(source_meta.get("upload_date") or ""),
        }
        return download_wp_episode_audio(post_info, main_window=self.app)

    def get_export_actions(self) -> List[tuple[str, Callable]]:
        def _open_export():
            if hasattr(self.app, "open_unified_export_dialog"):
                self.app.open_unified_export_dialog(initial_dest="wordpress")
            else:
                self.open_publish_dialog(parent=self.app)

        return [
            ("Publish to WordPress...", _open_export),
            ("Load Existing WordPress Episode...", self.open_load_existing_episode_dialog),
        ]

    def open_load_existing_episode_dialog(self) -> None:
        from plugins.wordpress.episode_updater import prompt_load_existing_wp_episode_dialog
        prompt_load_existing_wp_episode_dialog(self.app, parent=self.app)

    def get_story_actions(self, story: Any = None) -> List[tuple[str, Callable]]:
        return [
            ("WordPress Post & Story Settings...", lambda: self.open_post_metadata_dialog(parent=self.app, story=story)),
            ("Export Story to WordPress / CMS...", lambda: self.open_publish_dialog(parent=self.app, story=story)),
        ]

    def create_story_metadata_widget(self, parent: Any = None) -> Any:
        # WordPress post configuration is managed via Preferences and Export destinations, not in the Stories panel
        return None

    def on_story_selected(self, story: Any = None) -> None:
        pass

    def get_preferences_widget(self, parent: Any = None) -> Any:
        from plugins.wordpress.client import WordPressPreferencesPage
        return WordPressPreferencesPage(parent=parent, app=self.app)

    def open_publish_dialog(self, parent: Any = None, story: Any = None):
        dlg = WordPressPublishDialog(self, parent=parent or self.app, story=story)
        dlg.exec()

    def open_post_metadata_dialog(self, parent: Any = None, story: Any = None):
        from plugins.wordpress.export_destination import WordPressPostMetadataDialog
        target_idx = None
        if story and hasattr(self.app, "stories"):
            try:
                target_idx = self.app.stories.index(story)
            except Exception:
                target_idx = None
        dlg = WordPressPostMetadataDialog(parent=parent or self.app, main_window=self.app, target_story_index=target_idx)
        dlg.exec()


__all__ = [
    "Plugin",
    "WordPressPublishDialog",
    "WordPressPublishWorker",
    "capture_video_frame",
]
