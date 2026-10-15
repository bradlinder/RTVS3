"""Radio & TV Story Segmenter — Media Clipper & Audio Track Renderer.

Provides media extraction routines for story clips, audio tracks, fade curve application,
FFmpeg process execution, and YouTube media clip preparation.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import webbrowser
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMessageBox

from core_utils import safe_filename, ffmpeg_path
from export.audio import export_audio_track as render_audio_track, extract_audio_clip


class ExportMediaClipperMixin:
    """Provides audio/video track rendering, story clip extraction, and YouTube media handling."""

    def cancel_export(self):
        """Flag the running export operation to halt at the next iteration."""
        if getattr(self, "is_exporting", False) or getattr(self, "export_active", False):
            self.export_cancelled = True
            if hasattr(self, "log_activity"):
                self.log_activity("[EXPORT] Cancel requested by user.")

    def extract_media(
        self,
        start: float,
        end: float,
        output_file: Any,
        fade_in: float = 0.0,
        fade_out: float = 0.0,
        cancel_check: Optional[Callable[[], bool]] = None,
    ):
        """Export a media range using the same container/format as the imported file,
        optionally applying audio fade-in and fade-out filters.
        """
        audio_file = getattr(self, "audio_file", None)
        if not audio_file:
            raise RuntimeError("No source media is loaded.")
        fades_enabled = getattr(self, "enable_audio_fades", False)
        cancel_chk = cancel_check or (lambda: bool(getattr(self, "export_cancelled", False)))
        return render_audio_track(
            source_file=audio_file,
            start=start,
            end=end,
            output_file=output_file,
            fade_in=fade_in,
            fade_out=fade_out,
            has_video=bool(getattr(self, "current_media_is_video", False)),
            fades_enabled=fades_enabled,
            cancel_check=cancel_chk,
        )

    def extract_audio(self, start: float, end: float, output_file: Any):
        """Backward-compatible helper for older project/export code."""
        audio_file = getattr(self, "audio_file", None)
        if not audio_file:
            raise RuntimeError("No source media is loaded.")
        cancel_chk = lambda: bool(getattr(self, "export_cancelled", False))
        return extract_audio_clip(audio_file, start, end, output_file, cancel_check=cancel_chk)

    def _handle_youtube_export_result(self, result: dict):
        scope = result.get("scope", "full")
        title = result.get("title", "Broadcast Video").strip()
        description = result.get("description", "").strip()
        tags = result.get("tags", "").strip()
        category = result.get("category", "25")
        privacy = result.get("privacy", "unlisted")
        thumb_mode = result.get("thumb_mode", "auto")
        thumb_file = result.get("thumb_file")
        copy_clipboard = result.get("copy_clipboard", True)
        open_browser = result.get("open_browser", True)
        open_folder = result.get("open_folder", True)
        include_subtitles = result.get("include_subtitles", True)

        # 1. Determine export directory (creating a dedicated YouTube subfolder in project directory)
        export_dir = result.get("export_dir")
        settings_store = getattr(self, "settings_store", None)
        create_bundle = True
        if settings_store:
            create_bundle = str(settings_store.value("create_project_subfolders", "true")).lower() in {"1", "true", "yes"}

        if export_dir and os.path.isdir(export_dir):
            base_dir = Path(export_dir)
            if create_bundle and base_dir.name.lower() != "youtube":
                out_dir = base_dir / "YouTube"
            else:
                out_dir = base_dir
        else:
            project_dir, _, _, _ = self.prepare_export_directories(prompt_user=False)
            if create_bundle and project_dir.name.lower() != "youtube":
                out_dir = project_dir / "YouTube"
            else:
                out_dir = project_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        base_name = safe_filename(title) or "youtube_export"

        # 2. Export Media Clip
        media_src = getattr(self, "audio_file", None)
        exported_media_path = None
        if media_src and Path(media_src).exists():
            src_path = Path(media_src)
            ext = src_path.suffix.lower() or ".mp4"
            dst_media = out_dir / f"{base_name}{ext}"

            # If exporting selected stories, cut media clip with ffmpeg
            if scope == "selected_stories":
                sel_indices = getattr(self, "current_selected_story_indices", [])
                stories = getattr(self, "stories", [])
                target_stories = [stories[i] for i in sel_indices if 0 <= i < len(stories)]
                if target_stories:
                    start_sec = min(getattr(st, "start", 0.0) for st in target_stories)
                    end_sec = max(getattr(st, "end", getattr(st, "start", 0.0) + 1.0) for st in target_stories)
                    dur = max(0.1, end_sec - start_sec)
                    ff = ffmpeg_path() or "ffmpeg"
                    cmd = [
                        ff, "-hide_banner", "-loglevel", "error", "-y",
                        "-ss", f"{start_sec:.3f}",
                        "-i", str(src_path),
                        "-t", f"{dur:.3f}",
                        "-c", "copy",
                        str(dst_media)
                    ]
                    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    try:
                        subprocess.run(cmd, capture_output=True, timeout=120, creationflags=flags)
                    except Exception:
                        shutil.copy2(str(src_path), str(dst_media))
                else:
                    shutil.copy2(str(src_path), str(dst_media))
            else:
                try:
                    if not dst_media.exists() or dst_media.resolve() != src_path.resolve():
                        shutil.copy2(str(src_path), str(dst_media))
                except Exception:
                    pass
            exported_media_path = dst_media

        # 3. Export Subtitles (.srt) if requested
        exported_sub_path = None
        if include_subtitles:
            transcript = getattr(self, "transcript", None)
            if transcript and transcript.get("segments"):
                sub_path = out_dir / f"{base_name}.srt"
                if scope == "selected_stories":
                    sel_indices = getattr(self, "current_selected_story_indices", [])
                    stories = getattr(self, "stories", [])
                    target_stories = [stories[i] for i in sel_indices if 0 <= i < len(stories)]
                    if target_stories:
                        start_sec = min(getattr(st, "start", 0.0) for st in target_stories)
                        end_sec = max(getattr(st, "end", getattr(st, "start", 0.0) + 1.0) for st in target_stories)
                        sub_segs = self.transcript_for_range(start_sec, end_sec)
                    else:
                        sub_segs = transcript.get("segments", [])
                else:
                    sub_segs = transcript.get("segments", [])

                blocks = self.build_story_blocks(sub_segs)
                self.write_subtitles(blocks, str(sub_path), fmt="srt", include_speakers=True)
                exported_sub_path = sub_path

        # 4. Export Metadata Summary file (.txt)
        meta_txt = out_dir / f"{base_name}_youtube_metadata.txt"
        with open(meta_txt, "w", encoding="utf-8") as f:
            f.write(f"TITLE:\n{title}\n\n")
            f.write(f"DESCRIPTION:\n{description}\n\n")
            f.write(f"TAGS:\n{tags}\n\n")
            f.write(f"CATEGORY ID: {category}\n")
            f.write(f"PRIVACY: {privacy}\n")
            if thumb_file:
                f.write(f"THUMBNAIL: {thumb_file}\n")
            if exported_media_path:
                f.write(f"MEDIA CLIP: {exported_media_path.name}\n")
            if exported_sub_path:
                f.write(f"SUBTITLES: {exported_sub_path.name}\n")

        # 5. Copy chapters/metadata to clipboard if requested
        if copy_clipboard and description:
            cb = QApplication.clipboard()
            if cb:
                cb.setText(description)
                if hasattr(self, "statusBar") and self.statusBar():
                    self.statusBar().showMessage("YouTube description and chapters copied to clipboard!", 4000)

        # 6. Launch browser or open folder if requested
        if open_browser:
            webbrowser.open("https://studio.youtube.com")
        if open_folder and out_dir.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(out_dir)))

        if hasattr(self, "log_activity"):
            self.log_activity(f"[YOUTUBE] Exported YouTube Studio package to {out_dir}")
        QMessageBox.information(
            self,
            "YouTube Export Complete",
            f"YouTube package prepared successfully in:\n{out_dir}\n\n"
            f"Metadata saved to '{meta_txt.name}'.\n"
            f"{'Description & chapters copied to clipboard.' if copy_clipboard else ''}",
        )
