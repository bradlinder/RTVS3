"""Radio & TV Story Segmenter — Story & Full Episode Export Pipeline.

Orchestrates batch multi-format export pipelines for:
- Full Episode export
- Selected Stories export
- All Stories export
- Combined Full Episode & All Stories export
Handles progress reporting, cancellation, and metadata integration.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox, QProgressDialog

from core_utils import safe_filename, safe_process_events, format_time
from export_dialogs import show_export_completion_dialog
from export.pdf import TranscriptPdfWriter
from export.docx import create_story_docx
from speaker_palette import SpeakerColorAssigner
from export.subtitles import generate_cue_sheet, generate_youtube_chapters
from export.timeline import (
    generate_reaper_project,
    generate_samplitude_edl,
    generate_audacity_labels,
    generate_audition_xml,
    generate_daw_marker_csv,
)


class ExportStoryPipelineMixin:
    """Provides story batch export and full episode export orchestration."""

    def _export_story_files(
        self,
        stories_with_indices: List[Tuple[int, Any]],
        formats: Dict[str, bool],
        base: str,
        options: Dict[str, Any],
        directory: str,
        start_idx: int = 0,
        total_batch: Optional[int] = None,
        is_custom_location: bool = False,
    ) -> bool:
        self.is_exporting = True
        try:
            return self._do_export_story_files(
                stories_with_indices,
                formats,
                base,
                options,
                directory,
                start_idx=start_idx,
                total_batch=total_batch,
                is_custom_location=is_custom_location,
            )
        except Exception as exc:
            if "Export cancelled by user" in str(exc) or getattr(self, "export_cancelled", False):
                if hasattr(self, "log_activity"):
                    self.log_activity("[EXPORT] Export operation stopped by user.")
                return False
            raise
        finally:
            self.is_exporting = False

    def _do_export_story_files(
        self,
        stories_with_indices: List[Tuple[int, Any]],
        formats: Dict[str, bool],
        base: str,
        options: Dict[str, Any],
        directory: str,
        start_idx: int = 0,
        total_batch: Optional[int] = None,
        is_custom_location: bool = False,
    ) -> bool:
        out = Path(directory)
        settings_store = getattr(self, "settings_store", None)
        create_bundle = True
        if settings_store:
            create_bundle = str(settings_store.value("create_project_subfolders", "true")).lower() in {"1", "true", "yes"}

        if create_bundle and not is_custom_location:
            transcripts_out = out / "Transcripts"
            media_out = out / "Media"
            transcripts_out.mkdir(parents=True, exist_ok=True)
            if formats.get("media"):
                media_out.mkdir(parents=True, exist_ok=True)
        else:
            transcripts_out = out
            media_out = out

        languages_to_export = []
        src_code = self.source_language_code() if hasattr(self, "source_language_code") else "en"
        batch_direction = options.get("translation_direction")
        if batch_direction and options.get("include_spanish", False) and hasattr(self, "translation_export_spec"):
            source_code, target_code, target_suffix = self.translation_export_spec(options)
            languages_to_export.append((source_code, ""))
            if hasattr(self, "get_translation_item") and self.get_translation_item(source_code, target_code):
                languages_to_export.append((target_code, target_suffix))
        else:
            if src_code == "es":
                if options.get("include_spanish", True):
                    languages_to_export.append(("es", ""))
                if options.get("include_english", False):
                    has_trans = self.has_spanish_translation() if hasattr(self, "has_spanish_translation") else False
                    if has_trans:
                        languages_to_export.append(("en", "_en"))
            else:
                if options.get("include_english", True):
                    languages_to_export.append(("en", ""))
                if options.get("include_spanish", False):
                    has_es = self.has_spanish_translation() if hasattr(self, "has_spanish_translation") else (
                        self.translation_is_current(self.translation_key("en", "es")) if hasattr(self, "translation_is_current") else False
                    )
                    if has_es:
                        languages_to_export.append(("es", "_es"))

        audio_file = getattr(self, "audio_file", None)
        doc_base = base if base else (safe_filename(audio_file.stem) if audio_file else "Story")
        total_stories = total_batch if total_batch is not None else len(stories_with_indices)

        for i, (idx, story) in enumerate(stories_with_indices):
            if getattr(self, "export_cancelled", False):
                if hasattr(self, "log_activity"):
                    self.log_activity("[EXPORT] Export operation stopped by user.")
                return False

            story_title = story.title.strip() if getattr(story, "title", None) else f"Story {idx + 1}"
            current_count = start_idx + i + 1
            pct = int(((start_idx + i) / max(1, total_stories)) * 100)

            # Update inline top-of-window header indicators
            if hasattr(self, "set_processing_stage"):
                self.set_processing_stage("Exporting Stories", f"{current_count} of {total_stories}: '{story_title}'")
            if hasattr(self, "update_processing_progress"):
                self.update_processing_progress(pct, f"Exporting {story_title}...")
            safe_process_events()

            story_slug = safe_filename(story.title) if getattr(story, "title", None) else f"Story_{idx + 1:02d}"
            story_base = f"{doc_base}_{idx + 1:02d}_{story_slug}" if getattr(story, "title", None) else f"{doc_base}_{idx + 1:02d}"
            segments = self.transcript_for_range(story.start, story.end)

            for lang_code, suffix in languages_to_export:
                file_base = f"{story_base}{suffix}"
                batch_direction = options.get("translation_direction")
                source_code = self.translation_export_spec(options)[0] if (batch_direction and hasattr(self, "translation_export_spec")) else src_code
                if lang_code == source_code:
                    blocks = self.build_story_blocks(segments) if segments else []
                else:
                    batch_direction = options.get("translation_direction")
                    if batch_direction and hasattr(self, "translation_export_spec"):
                        source_code, target_code, _target_suffix = self.translation_export_spec(options)
                        item = self.get_translation_item(source_code, target_code) if hasattr(self, "get_translation_item") else None
                    else:
                        item = self.get_spanish_translation_item() if hasattr(self, "get_spanish_translation_item") else (
                            getattr(self, "translations", {}).get("en-es") or getattr(self, "translations", {}).get("en_es") or {}
                        )
                    trans_segs = item.get("segments", []) if item else []
                    source_segs = self.transcript.get("segments", []) if getattr(self, "transcript", None) else []
                    curr_spk_blocks = []
                    for s_idx, t_seg in enumerate(trans_segs):
                        source_seg = source_segs[s_idx] if s_idx < len(source_segs) else {}
                        s_start = float(t_seg.get("start", source_seg.get("start", 0.0)))
                        s_end = float(t_seg.get("end", source_seg.get("end", s_start + 1.0)))
                        if s_end <= story.start or s_start >= story.end:
                            continue
                        spk = self.get_effective_speaker_name(s_idx, source_seg) if hasattr(self, "get_effective_speaker_name") and source_seg else ""
                        curr_spk_blocks.append({
                            "speaker": spk,
                            "text": t_seg.get("text", "").strip(),
                            "start": s_start,
                            "end": s_end,
                            "_source_index": s_idx,
                        })
                    blocks = self.build_story_blocks(curr_spk_blocks) if curr_spk_blocks else []

                # Export TXT
                include_millis = bool(options.get("include_milliseconds", options.get("show_milliseconds", getattr(self, "show_milliseconds", False))))
                if formats.get("txt"):
                    txt_file = transcripts_out / f"{file_base}.txt"
                    with open(txt_file, "w", encoding="utf-8") as f:
                        source_name = audio_file.name if audio_file else "Text-only project"
                        lang_label = " (Spanish)" if lang_code == "es" else (" (English)" if lang_code == "en" else "")
                        f.write(f"{story_title}{lang_label}\n{source_name} ({format_time(story.start, include_millis)} - {format_time(story.end, include_millis)})\n")
                        meta = getattr(story, "metadata", {}) or {}
                        wp_meta = meta.get("wordpress", {}) if isinstance(meta.get("wordpress"), dict) else {}
                        author_val = meta.get("author") or wp_meta.get("manual_author") or ""
                        if not author_val and isinstance(wp_meta.get("author_names"), list):
                            author_val = ", ".join(wp_meta["author_names"])
                        if author_val:
                            f.write(f"Author: {author_val}\n")
                        excerpt_val = meta.get("excerpt") or wp_meta.get("excerpt") or ""
                        if excerpt_val:
                            f.write(f"Excerpt: {excerpt_val}\n")
                        f.write("=" * 70 + "\n\n")
                        last_speaker = None
                        for block in blocks:
                            speaker = (block.get("speaker") or "").strip() if options.get("include_speakers", True) else ""
                            p_text = block.get("text", "").strip()
                            if not p_text:
                                continue
                            prefix = ""
                            if options.get("include_timestamps") and block.get("start") is not None:
                                prefix = f"[{format_time(block['start'], include_millis)}] "
                            is_speaker_change = block.get("is_speaker_change", (speaker != last_speaker))
                            if speaker and is_speaker_change and speaker != last_speaker:
                                prefix += f"{speaker}: "
                                last_speaker = speaker
                            f.write(f"{prefix}{p_text}\n")

                            if options.get("include_comments", options.get("include_notes", True)):
                                src_idx = block.get("_source_index")
                                source_segs = self.transcript.get("segments", []) if getattr(self, "transcript", None) else []
                                seg_comment = ""
                                if src_idx is not None and 0 <= src_idx < len(source_segs):
                                    seg_comment = (source_segs[src_idx].get("comments") or source_segs[src_idx].get("notes", "")).strip()
                                elif "comments" in block or "notes" in block:
                                    seg_comment = str(block.get("comments") or block.get("notes", "")).strip()
                                if seg_comment:
                                    f.write(f"   [Comment: {seg_comment}]\n")
                            f.write("\n")

                # Export DOCX
                if formats.get("docx"):
                    docx_file = transcripts_out / f"{file_base}.docx"
                    create_story_docx(
                        title=story_title,
                        blocks=blocks,
                        output_path=docx_file,
                        media_name=audio_file.name if audio_file else "",
                        start_time=story.start,
                        end_time=story.end,
                        include_speakers=options.get("include_speakers", True),
                        include_timestamps=options.get("include_timestamps", True),
                        include_milliseconds=include_millis,
                        include_comments=options.get("include_comments", options.get("include_notes", True)),
                        include_highlights=options.get("include_highlights", True),
                        lang_code=lang_code,
                        source_segments=(self.transcript.get("segments", []) if getattr(self, "transcript", None) else None),
                        color_speakers=options.get("color_speakers", options.get("colorize_speakers", False)),
                    )

                # Export PDF
                if formats.get("pdf"):
                    pdf_file = transcripts_out / f"{file_base}.pdf"
                    lang_label = " (Spanish)" if lang_code == "es" else (" (English)" if lang_code == "en" else "")
                    header_title = f"{story_title}{lang_label}"
                    rec_info = f"Recording: {audio_file.name} ({format_time(story.start, include_millis)} - {format_time(story.end, include_millis)})" if audio_file else None
                    pdf_writer = TranscriptPdfWriter(doc_title=header_title)
                    pdf_writer.add_header(header_title, rec_info)

                    last_speaker = None
                    color_spk_opt = options.get("color_speakers", options.get("colorize_speakers", False))
                    color_assigner = SpeakerColorAssigner() if color_spk_opt else None

                    for block in blocks:
                        speaker = (block.get("speaker") or "").strip() if options.get("include_speakers", True) else ""
                        p_text = block.get("text", "").strip()
                        if not p_text:
                            continue
                        t_stamp = ""
                        if options.get("include_timestamps") and "start" in block and block["start"] is not None:
                            t_stamp = f"[{format_time(block['start'], include_millis)}]"
                        is_speaker_change = block.get("is_speaker_change", (speaker != last_speaker))
                        effective_speaker = speaker if (speaker and is_speaker_change and speaker != last_speaker) else ""
                        if effective_speaker:
                            last_speaker = speaker

                        seg_comment = ""
                        if options.get("include_comments", options.get("include_notes", True)):
                            src_idx = block.get("_source_index")
                            source_segs = self.transcript.get("segments", []) if getattr(self, "transcript", None) else []
                            if src_idx is not None and 0 <= src_idx < len(source_segs):
                                seg_comment = (source_segs[src_idx].get("comments") or source_segs[src_idx].get("notes", "")).strip()
                            elif "comments" in block or "notes" in block:
                                seg_comment = str(block.get("comments") or block.get("notes", "")).strip()

                        spk_rgb = color_assigner.get_pdf_rgb(effective_speaker) if (color_assigner and effective_speaker) else None
                        pdf_writer.add_paragraph(
                            text=p_text,
                            speaker=effective_speaker,
                            timestamp=t_stamp,
                            comment=seg_comment,
                            highlight=(bool(seg_comment) and options.get("include_highlights", True)),
                            speaker_rgb=spk_rgb,
                        )
                    with open(pdf_file, "wb") as pf:
                        pf.write(pdf_writer.get_pdf_bytes())

                # Export Subtitles
                if formats.get("srt"):
                    self.write_subtitles(blocks, transcripts_out / f"{file_base}.srt", "srt", options.get("include_speakers", True))
                if formats.get("vtt"):
                    self.write_subtitles(blocks, transcripts_out / f"{file_base}.vtt", "vtt", options.get("include_speakers", True))

            # Export Media Clip
            if formats.get("media") and audio_file:
                media_file = media_out / f"{story_base}{audio_file.suffix.lower()}"
                apply_fades = bool(options.get("apply_audio_fades", True))
                f_in = getattr(story, "fade_in", 0.0) if apply_fades else 0.0
                f_out = getattr(story, "fade_out", 0.0) if apply_fades else 0.0
                try:
                    self.extract_media(story.start, story.end, media_file, fade_in=f_in, fade_out=f_out)
                except RuntimeError as exc:
                    if "Export cancelled by user" in str(exc) or getattr(self, "export_cancelled", False):
                        if hasattr(self, "log_activity"):
                            self.log_activity("[EXPORT] Export operation stopped by user.")
                        return False
                    raise

                # Embed ID3 tags if exported media is MP3
                if media_file.suffix.lower() == ".mp3" and media_file.is_file():
                    try:
                        import datetime
                        from id3_editor import write_id3_tags
                        st_title = getattr(story, "title", "") or getattr(story, "suggestion", "") or f"Story {idx}"
                        st_spk = getattr(story, "speaker", "") or getattr(story, "speaker_label", "") or ""
                        write_id3_tags(
                            str(media_file),
                            {
                                "title": st_title,
                                "artist": st_spk,
                                "album": base,
                                "track": str(idx),
                                "year": str(datetime.datetime.now().year),
                                "composer": "Radio & TV Segmenter",
                            },
                        )
                    except Exception:
                        pass

        # Export CUE sheet and tracklist if requested
        if formats.get("cue") and stories_with_indices:
            stories_subset = [s for _, s in stories_with_indices]
            cue_file = transcripts_out / f"{base}.cue"
            album_title = base
            media_name = audio_file.name if audio_file else ""
            cue_text = generate_cue_sheet(stories_subset, media_name, album_title)
            with open(cue_file, "w", encoding="utf-8") as f:
                f.write(cue_text)

        if formats.get("tracklist") and stories_with_indices:
            stories_subset = [s for _, s in stories_with_indices]
            chapters_file = transcripts_out / f"{base}_chapters.txt"
            chapters_text = generate_youtube_chapters(stories_subset)
            with open(chapters_file, "w", encoding="utf-8") as f:
                f.write(chapters_text)

        unselected_mode = options.get("unselected_audio_mode", "exclude")
        tot_dur = float(getattr(self, "duration", 0.0) or getattr(self, "audio_duration", 0.0) or 0.0)

        if formats.get("rpp") and stories_with_indices:
            stories_subset = [s for _, s in stories_with_indices]
            rpp_file = transcripts_out / f"{base}.rpp"
            media_name = audio_file.name if audio_file else ""
            apply_fades = bool(options.get("apply_audio_fades", True))
            rpp_text = generate_reaper_project(stories_subset, media_name, base, apply_fades=apply_fades, total_duration=tot_dur, unselected_audio_mode=unselected_mode)
            with open(rpp_file, "w", encoding="utf-8") as f:
                f.write(rpp_text)

        if formats.get("edl") and stories_with_indices:
            stories_subset = [s for _, s in stories_with_indices]
            edl_file = transcripts_out / f"{base}.edl"
            media_name = audio_file.name if audio_file else ""
            apply_fades = bool(options.get("apply_audio_fades", True))
            edl_text = generate_samplitude_edl(stories_subset, media_name, base, apply_fades=apply_fades, total_duration=tot_dur, unselected_audio_mode=unselected_mode)
            with open(edl_file, "w", encoding="utf-8") as f:
                f.write(edl_text)

        if formats.get("audacity") and stories_with_indices:
            stories_subset = [s for _, s in stories_with_indices]
            audacity_file = transcripts_out / f"{base}_labels.txt"
            aud_text = generate_audacity_labels(stories_subset, total_duration=tot_dur, unselected_audio_mode=unselected_mode)
            with open(audacity_file, "w", encoding="utf-8") as f:
                f.write(aud_text)

        if formats.get("audition_xml") and stories_with_indices:
            stories_subset = [s for _, s in stories_with_indices]
            xml_file = transcripts_out / f"{base}.xml"
            media_name = audio_file.name if audio_file else ""
            xml_text = generate_audition_xml(stories_subset, media_name, base, total_duration=tot_dur, unselected_audio_mode=unselected_mode)
            with open(xml_file, "w", encoding="utf-8") as f:
                f.write(xml_text)

        if formats.get("daw_csv") and stories_with_indices:
            stories_subset = [s for _, s in stories_with_indices]
            csv_file = transcripts_out / f"{base}_markers.csv"
            csv_text = generate_daw_marker_csv(stories_subset, total_duration=tot_dur, unselected_audio_mode=unselected_mode)
            with open(csv_file, "w", encoding="utf-8") as f:
                f.write(csv_text)

        return True

    def export_selected_stories(
        self,
        custom_formats: Optional[Dict[str, bool]] = None,
        custom_base: Optional[str] = None,
        custom_options: Optional[Dict[str, Any]] = None,
        directory: Optional[str] = None,
        is_custom_location: bool = False,
    ):
        indices = getattr(self, "current_selected_story_indices", [])
        is_music = getattr(self, "story_detection_mode", "voice") == "music"
        term = "Song" if is_music else "Story"
        term_plural = "Songs" if is_music else "Stories"
        stories = getattr(self, "stories", [])
        if not indices:
            QMessageBox.warning(self, f"No {term} Selected", f"Please select one or more {term_plural.lower()} to export.")
            return
        stories_to_export = [(i, stories[i]) for i in indices if 0 <= i < len(stories)]
        if not stories_to_export:
            QMessageBox.warning(self, f"No {term} Selected", f"No valid {term_plural.lower()} are currently selected.")
            return

        project_file = getattr(self, "project_file", None)
        audio_file = getattr(self, "audio_file", None)
        base = custom_base or (safe_filename(project_file.stem if project_file else (audio_file.stem if audio_file else "export")))
        if directory is None:
            if project_file and ((project_file.parent / "Transcripts").is_dir() or (project_file.parent / "Media").is_dir()):
                project_dir, _, _, chosen_base = self.prepare_export_directories()
            else:
                dialog_dir = self._dialog_directory() if hasattr(self, "_dialog_directory") else str(Path.home())
                parent_dir = QFileDialog.getExistingDirectory(self, "Choose Export Location", dialog_dir)
                if not parent_dir:
                    return
                project_dir, _, _, chosen_base = self.prepare_export_directories(parent_dir, default_name=base, prompt_user=True)
            if not project_dir:
                return
            directory = str(project_dir)
            base = chosen_base

        formats = custom_formats or {"txt": True, "docx": True, "pdf": True, "srt": False, "vtt": False, "media": False}
        options = custom_options or {"include_speakers": True, "include_timestamps": False, "include_english": True, "include_spanish": False}

        self.export_cancelled = False
        if hasattr(self, "cancel_button"):
            self.cancel_button.show()

        try:
            success = self._export_story_files(stories_to_export, formats, base, options, directory, is_custom_location=is_custom_location)
            if success and not self.export_cancelled:
                if hasattr(self, "update_processing_progress"):
                    self.update_processing_progress(100, "Export complete.")
                if hasattr(self, "log_activity"):
                    self.log_activity(f"[EXPORT] Exported {len(stories_to_export)} selected {term.lower()}(s) to {directory}")
                show_export_completion_dialog(self, "Export Complete", f"Exported {len(stories_to_export)} {term.lower()}(s) to:\n{directory}", directory)
        except Exception as exc:
            if "Export cancelled by user" in str(exc) or getattr(self, "export_cancelled", False):
                if hasattr(self, "log_activity"):
                    self.log_activity("[EXPORT] Export operation stopped by user.")
                return
            if hasattr(self, "log_activity"):
                self.log_activity(f"[ERROR] Selected stories export failed: {exc}")
            QMessageBox.critical(self, "Export Error", str(exc))
        finally:
            if hasattr(self, "set_processing_stage"):
                self.set_processing_stage(None)
            if hasattr(self, "cancel_button"):
                self.cancel_button.hide()

    def export_all_stories(
        self,
        custom_formats: Optional[Dict[str, bool]] = None,
        custom_base: Optional[str] = None,
        custom_options: Optional[Dict[str, Any]] = None,
        directory: Optional[str] = None,
        is_custom_location: bool = False,
    ):
        is_music = getattr(self, "story_detection_mode", "voice") == "music"
        term = "Song" if is_music else "Story"
        term_plural = "Songs" if is_music else "Stories"
        stories = getattr(self, "stories", [])
        if not stories:
            QMessageBox.warning(self, f"No {term_plural}", f"There are no {term_plural.lower()} in this project to export.")
            return

        project_file = getattr(self, "project_file", None)
        audio_file = getattr(self, "audio_file", None)
        base = custom_base or (safe_filename(project_file.stem if project_file else (audio_file.stem if audio_file else "export")))
        if directory is None:
            if project_file and ((project_file.parent / "Transcripts").is_dir() or (project_file.parent / "Media").is_dir()):
                project_dir, _, _, chosen_base = self.prepare_export_directories()
            else:
                dialog_dir = self._dialog_directory() if hasattr(self, "_dialog_directory") else str(Path.home())
                parent_dir = QFileDialog.getExistingDirectory(self, "Choose Export Location", dialog_dir)
                if not parent_dir:
                    return
                project_dir, _, _, chosen_base = self.prepare_export_directories(parent_dir, default_name=base, prompt_user=True)
            if not project_dir:
                return
            directory = str(project_dir)
            base = chosen_base

        formats = custom_formats or {"txt": True, "docx": True, "pdf": True, "srt": False, "vtt": False, "media": False}
        options = custom_options or {"include_speakers": True, "include_timestamps": False, "include_english": True, "include_spanish": False}

        stories_to_export = list(enumerate(stories))
        self.export_cancelled = False
        if hasattr(self, "cancel_button"):
            self.cancel_button.show()

        try:
            success = self._export_story_files(stories_to_export, formats, base, options, directory, is_custom_location=is_custom_location)
            if success and not self.export_cancelled:
                if hasattr(self, "update_processing_progress"):
                    self.update_processing_progress(100, "Export complete.")
                if hasattr(self, "log_activity"):
                    self.log_activity(f"[EXPORT] Exported all {len(stories_to_export)} {term_plural.lower()} to {directory}")
                show_export_completion_dialog(self, "Export Complete", f"Exported all {len(stories_to_export)} {term_plural.lower()} to:\n{directory}", directory)
        except Exception as exc:
            if "Export cancelled by user" in str(exc) or getattr(self, "export_cancelled", False):
                if hasattr(self, "log_activity"):
                    self.log_activity("[EXPORT] Export operation stopped by user.")
                return
            if hasattr(self, "log_activity"):
                self.log_activity(f"[ERROR] All stories export failed: {exc}")
            QMessageBox.critical(self, "Export Error", str(exc))
        finally:
            if hasattr(self, "set_processing_stage"):
                self.set_processing_stage(None)
            if hasattr(self, "cancel_button"):
                self.cancel_button.hide()

    def export_full_and_all_stories(
        self,
        custom_formats: Optional[Dict[str, bool]] = None,
        custom_base: Optional[str] = None,
        custom_options: Optional[Dict[str, Any]] = None,
        directory: Optional[str] = None,
        is_custom_location: bool = False,
    ):
        project_file = getattr(self, "project_file", None)
        audio_file = getattr(self, "audio_file", None)
        base = custom_base or (safe_filename(project_file.stem if project_file else (audio_file.stem if audio_file else "export")))
        if directory is None:
            if project_file and ((project_file.parent / "Transcripts").is_dir() or (project_file.parent / "Media").is_dir()):
                project_dir, _, _, chosen_base = self.prepare_export_directories()
            else:
                dialog_dir = self._dialog_directory() if hasattr(self, "_dialog_directory") else str(Path.home())
                parent_dir = QFileDialog.getExistingDirectory(self, "Choose Export Location", dialog_dir)
                if not parent_dir:
                    return
                project_dir, _, _, chosen_base = self.prepare_export_directories(parent_dir, default_name=base, prompt_user=True)
            if not project_dir:
                return
            directory = str(project_dir)
            base = chosen_base

        formats = custom_formats or {"txt": True, "docx": True, "pdf": True, "srt": False, "vtt": False, "media": False}
        options = custom_options or {"include_speakers": True, "include_timestamps": False, "include_english": True, "include_spanish": False}
        stories = getattr(self, "stories", [])
        stories_to_export = list(enumerate(stories)) if stories else []
        total_items = 1 + len(stories_to_export)

        self.export_cancelled = False
        if hasattr(self, "cancel_button"):
            self.cancel_button.show()

        is_music = getattr(self, "story_detection_mode", "voice") == "music"
        term_plural = "Songs" if is_music else "Stories"

        try:
            if hasattr(self, "set_processing_stage"):
                self.set_processing_stage(f"Exporting Full & {term_plural}", f"1 of {total_items}: Full Episode")
            if hasattr(self, "update_processing_progress"):
                self.update_processing_progress(0, "Exporting full episode...")
            safe_process_events()

            ok = self.export_full_episode(
                custom_formats=formats,
                custom_base=base,
                custom_options=options,
                directory=directory,
                show_completion=False,
                is_custom_location=is_custom_location,
            )

            if ok and not self.export_cancelled and stories_to_export:
                self._export_story_files(
                    stories_to_export,
                    formats,
                    base,
                    options,
                    directory,
                    start_idx=1,
                    total_batch=total_items,
                    is_custom_location=is_custom_location,
                )

            if not self.export_cancelled:
                if hasattr(self, "update_processing_progress"):
                    self.update_processing_progress(100, "Export complete.")
                if hasattr(self, "log_activity"):
                    self.log_activity(f"[EXPORT] Exported full episode and all {term_plural.lower()} to {directory}")
                show_export_completion_dialog(self, "Export Complete", f"Exported full episode and {term_plural.lower()} to:\n{directory}", directory)
        except Exception as exc:
            if "Export cancelled by user" in str(exc) or getattr(self, "export_cancelled", False):
                if hasattr(self, "log_activity"):
                    self.log_activity("[EXPORT] Export operation stopped by user.")
                return
            if hasattr(self, "log_activity"):
                self.log_activity(f"[ERROR] Full & story export failed: {exc}")
            QMessageBox.critical(self, "Export Error", str(exc))
        finally:
            if hasattr(self, "set_processing_stage"):
                self.set_processing_stage(None)
            if hasattr(self, "cancel_button"):
                self.cancel_button.hide()

    def export_full_episode(
        self,
        custom_formats: Optional[Dict[str, bool]] = None,
        custom_base: Optional[str] = None,
        custom_options: Optional[Dict[str, Any]] = None,
        directory: Optional[str] = None,
        show_completion: bool = True,
        progress_dialog: Optional[QProgressDialog] = None,
        progress_value: int = 0,
        is_custom_location: bool = False,
    ) -> bool:
        transcript = getattr(self, "transcript", None)
        audio_file = getattr(self, "audio_file", None)
        if not transcript and not audio_file:
            QMessageBox.warning(self, "Nothing to Export", "There is no transcript or media available to export.")
            return False
        if custom_formats is None or custom_base is None or custom_options is None:
            choice = self._choose_export_formats("Export Full Episode")
            if not choice:
                return False
            formats, base, options = choice
        else:
            formats, base, options = custom_formats, custom_base, custom_options

        project_file = getattr(self, "project_file", None)
        if directory is None:
            dialog_dir = self._dialog_directory() if hasattr(self, "_dialog_directory") else str(Path.home())
            parent_dir = QFileDialog.getExistingDirectory(self, "Choose Export Location", dialog_dir)
            if not parent_dir:
                return False
            project_dir, _, _, chosen_base = self.prepare_export_directories(parent_dir, default_name=base, prompt_user=True)
            if not project_dir:
                return False
            directory = str(project_dir)
            base = chosen_base

        out = Path(directory)
        settings_store = getattr(self, "settings_store", None)
        create_bundle = True
        if settings_store:
            create_bundle = str(settings_store.value("create_project_subfolders", "true")).lower() in {"1", "true", "yes"}

        if create_bundle and not is_custom_location:
            transcripts_out = out / "Transcripts"
            media_out = out / "Media"
            transcripts_out.mkdir(parents=True, exist_ok=True)
            if formats.get("media"):
                media_out.mkdir(parents=True, exist_ok=True)
        else:
            transcripts_out = out
            media_out = out

        created_local_dialog = False
        if progress_dialog is None:
            progress_dialog = QProgressDialog("Preparing export...", "Cancel", 0, 1, self)
            progress_dialog.setWindowTitle("Exporting Files")
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setValue(0)
            if hasattr(progress_dialog, "canceled"):
                progress_dialog.canceled.connect(self.cancel_export)
            progress_dialog.show()
            safe_process_events()
            created_local_dialog = True

        try:
            languages_to_export = []
            src_code = self.source_language_code() if hasattr(self, "source_language_code") else "en"
            batch_direction = options.get("translation_direction")
            if batch_direction and options.get("include_spanish", False) and hasattr(self, "translation_export_spec"):
                source_code, target_code, target_suffix = self.translation_export_spec(options)
                languages_to_export.append((source_code, ""))
                if hasattr(self, "get_translation_item") and self.get_translation_item(source_code, target_code):
                    languages_to_export.append((target_code, target_suffix))
            else:
                if src_code == "es":
                    if options.get("include_spanish", True):
                        languages_to_export.append(("es", ""))
                    if options.get("include_english", False):
                        has_trans = self.has_spanish_translation() if hasattr(self, "has_spanish_translation") else False
                        if has_trans:
                            languages_to_export.append(("en", "_en"))
                else:
                    if options.get("include_english", True):
                        languages_to_export.append(("en", ""))
                    if options.get("include_spanish", False):
                        has_es = self.has_spanish_translation() if hasattr(self, "has_spanish_translation") else (
                            self.translation_is_current(self.translation_key("en", "es")) if hasattr(self, "translation_is_current") else False
                        )
                        if has_es:
                            languages_to_export.append(("es", "_es"))

            doc_title = base if base else (safe_filename(audio_file.stem) if audio_file else "Transcript")

            if progress_dialog is not None:
                if progress_dialog.wasCanceled():
                    if hasattr(self, "log_activity"):
                        self.log_activity("[EXPORT] Export canceled by user.")
                    return False
                progress_dialog.setLabelText(f"Exporting Full Episode: '{doc_title}'...")
                progress_dialog.setValue(progress_value)
                safe_process_events()

            for lang_code, suffix in languages_to_export:
                file_base = f"{base}{suffix}"

                batch_direction = options.get("translation_direction")
                source_code = self.translation_export_spec(options)[0] if (batch_direction and hasattr(self, "translation_export_spec")) else src_code
                if lang_code == source_code:
                    segments = transcript.get("segments", []) if transcript else []
                    blocks = self.build_story_blocks(segments) if segments else []
                else:
                    batch_direction = options.get("translation_direction")
                    if batch_direction and hasattr(self, "translation_export_spec"):
                        source_code, target_code, _target_suffix = self.translation_export_spec(options)
                        item = self.get_translation_item(source_code, target_code) if hasattr(self, "get_translation_item") else None
                    else:
                        item = self.get_spanish_translation_item() if hasattr(self, "get_spanish_translation_item") else (
                            getattr(self, "translations", {}).get("en-es") or getattr(self, "translations", {}).get("en_es") or {}
                        )
                    trans_segs = item.get("segments", []) if item else []
                    source_segs = transcript.get("segments", []) if transcript else []
                    curr_spk_blocks = []
                    for idx, t_seg in enumerate(trans_segs):
                        source_seg = source_segs[idx] if idx < len(source_segs) else {}
                        t_start = float(t_seg.get("start", source_seg.get("start", 0.0)))
                        t_end = float(t_seg.get("end", source_seg.get("end", t_start + 1.0)))
                        spk = self.get_effective_speaker_name(idx, source_seg) if hasattr(self, "get_effective_speaker_name") and source_seg else ""
                        curr_spk_blocks.append({
                            "speaker": spk,
                            "text": t_seg.get("text", "").strip(),
                            "start": t_start,
                            "end": t_end,
                            "_source_index": idx,
                        })
                    blocks = self.build_story_blocks(curr_spk_blocks) if curr_spk_blocks else []

                include_millis = bool(options.get("include_milliseconds", options.get("show_milliseconds", getattr(self, "show_milliseconds", False))))

                # Export TXT to Transcripts subfolder
                if formats.get("txt"):
                    txt_file = transcripts_out / f"{file_base}.txt"
                    with open(txt_file, "w", encoding="utf-8") as f:
                        source_name = audio_file.name if audio_file else "Text-only project"
                        lang_label = " (Spanish)" if lang_code == "es" else (" (English)" if lang_code == "en" else "")
                        f.write(f"{doc_title}{lang_label}\n{source_name}\n" + "=" * 70 + "\n\n")

                        diar = getattr(self, "diarization", None)
                        if diar and lang_code == "en":
                            number = diar.get("num_speakers", 0)
                            f.write(f"Speaker detection: {number} speaker(s) detected.\n\n")

                        last_speaker = None
                        for block in blocks:
                            speaker = (block.get("speaker") or "").strip() if options.get("include_speakers", True) else ""
                            paragraph_text = block.get("text", "").strip()
                            if not paragraph_text:
                                continue

                            prefix = ""
                            if options.get("include_timestamps") and block.get("start") is not None:
                                prefix = f"[{format_time(block['start'], include_millis)}] "
                            is_speaker_change = block.get("is_speaker_change", (speaker != last_speaker))
                            if speaker and is_speaker_change and speaker != last_speaker:
                                prefix += f"{speaker}: "
                                last_speaker = speaker

                            f.write(f"{prefix}{paragraph_text}\n")

                            if options.get("include_comments", options.get("include_notes", True)):
                                src_idx = block.get("_source_index")
                                source_segs = transcript.get("segments", []) if transcript else []
                                seg_comment = ""
                                if src_idx is not None and 0 <= src_idx < len(source_segs):
                                    seg_comment = (source_segs[src_idx].get("comments") or source_segs[src_idx].get("notes", "")).strip()
                                elif "comments" in block or "notes" in block:
                                    seg_comment = str(block.get("comments") or block.get("notes", "")).strip()
                                if seg_comment:
                                    f.write(f"   [Comment: {seg_comment}]\n")
                            f.write("\n")

                # Export DOCX to Transcripts subfolder
                if formats.get("docx"):
                    docx_file = transcripts_out / f"{file_base}.docx"
                    tot_dur = float(getattr(self, "duration", 0.0) or getattr(self, "audio_duration", 0.0) or 0.0)
                    try:
                        create_story_docx(
                            title=doc_title,
                            blocks=blocks,
                            output_path=docx_file,
                            media_name=audio_file.name if audio_file else "",
                            start_time=0.0,
                            end_time=tot_dur,
                            include_speakers=options.get("include_speakers", True),
                            include_timestamps=options.get("include_timestamps", True),
                            include_milliseconds=include_millis,
                            include_comments=options.get("include_comments", options.get("include_notes", True)),
                            include_highlights=options.get("include_highlights", True),
                            lang_code=lang_code,
                            source_segments=(transcript.get("segments", []) if transcript else None),
                            color_speakers=options.get("color_speakers", options.get("colorize_speakers", False)),
                        )
                    except Exception as docx_exc:
                        if hasattr(self, "log_activity"):
                            self.log_activity(f"[ERROR] Failed to export DOCX for full episode ({lang_code}): {docx_exc}")

                # Export PDF to Transcripts subfolder
                if formats.get("pdf"):
                    pdf_file = transcripts_out / f"{file_base}.pdf"
                    lang_label = " (Spanish)" if lang_code == "es" else (" (English)" if lang_code == "en" else "")
                    header_title = f"{doc_title}{lang_label}"
                    rec_info = f"Recording: {audio_file.name}" if audio_file else None
                    pdf_writer = TranscriptPdfWriter(doc_title=header_title)
                    pdf_writer.add_header(header_title, rec_info)

                    if blocks:
                        last_speaker = None
                        color_spk_opt = options.get("color_speakers", options.get("colorize_speakers", False))
                        color_assigner = SpeakerColorAssigner() if color_spk_opt else None

                        for block in blocks:
                            speaker = (block.get("speaker") or "").strip() if options.get("include_speakers", True) else ""
                            paragraph_text = block.get("text", "").strip()
                            if not paragraph_text:
                                continue

                            t_stamp = ""
                            if options.get("include_timestamps") and "start" in block and block["start"] is not None:
                                t_stamp = f"[{format_time(block['start'], include_millis)}]"

                            is_speaker_change = block.get("is_speaker_change", (speaker != last_speaker))
                            effective_speaker = speaker if (speaker and is_speaker_change and speaker != last_speaker) else ""
                            if effective_speaker:
                                last_speaker = speaker

                            seg_comment = ""
                            if options.get("include_comments", options.get("include_notes", True)):
                                src_idx = block.get("_source_index")
                                source_segs = transcript.get("segments", []) if transcript else []
                                if src_idx is not None and 0 <= src_idx < len(source_segs):
                                    seg_comment = (source_segs[src_idx].get("comments") or source_segs[src_idx].get("notes", "")).strip()
                                elif "comments" in block or "notes" in block:
                                    seg_comment = str(block.get("comments") or block.get("notes", "")).strip()

                            spk_rgb = color_assigner.get_pdf_rgb(effective_speaker) if (color_assigner and effective_speaker) else None
                            pdf_writer.add_paragraph(
                                text=paragraph_text,
                                speaker=effective_speaker,
                                timestamp=t_stamp,
                                comment=seg_comment,
                                highlight=(bool(seg_comment) and options.get("include_highlights", True)),
                                speaker_rgb=spk_rgb,
                            )
                    with open(pdf_file, "wb") as pf:
                        pf.write(pdf_writer.get_pdf_bytes())

                # Export Subtitles to Transcripts subfolder
                if formats.get("srt"):
                    self.write_subtitles(blocks, transcripts_out / f"{file_base}.srt", "srt", options.get("include_speakers", True))
                if formats.get("vtt"):
                    self.write_subtitles(blocks, transcripts_out / f"{file_base}.vtt", "vtt", options.get("include_speakers", True))

            # Export Media to Media subfolder
            if formats.get("media"):
                if not audio_file:
                    raise RuntimeError("Media export is unavailable because this project has no imported media file.")
                media_file = media_out / f"{base}{audio_file.suffix.lower()}"
                cancel_chk = lambda: bool(getattr(self, "export_cancelled", False) or (progress_dialog and progress_dialog.wasCanceled()))
                dur = float(getattr(self, "duration", 0.0) or getattr(self, "audio_duration", 0.0) or 0.0)
                try:
                    self.extract_media(0, dur, media_file, cancel_check=cancel_chk)
                except RuntimeError as exc:
                    if "Export cancelled by user" in str(exc) or getattr(self, "export_cancelled", False) or (progress_dialog and progress_dialog.wasCanceled()):
                        if hasattr(self, "log_activity"):
                            self.log_activity("[EXPORT] Export operation stopped by user.")
                        return False
                    raise

            # Export CUE sheet and Tracklist/Chapters if requested
            stories = getattr(self, "stories", None)
            if formats.get("cue") and stories:
                cue_file = transcripts_out / f"{base}.cue"
                album_title = base
                media_name = audio_file.name if audio_file else ""
                cue_text = generate_cue_sheet(stories, media_name, album_title)
                with open(cue_file, "w", encoding="utf-8") as f:
                    f.write(cue_text)

            if formats.get("tracklist") and stories:
                chapters_file = transcripts_out / f"{base}_chapters.txt"
                chapters_text = generate_youtube_chapters(stories)
                with open(chapters_file, "w", encoding="utf-8") as f:
                    f.write(chapters_text)

            unselected_mode = options.get("unselected_audio_mode", "exclude")
            tot_dur = float(getattr(self, "duration", 0.0) or getattr(self, "audio_duration", 0.0) or 0.0)

            if formats.get("rpp") and stories:
                rpp_file = transcripts_out / f"{base}.rpp"
                media_name = audio_file.name if audio_file else ""
                apply_fades = bool(options.get("apply_audio_fades", True))
                rpp_text = generate_reaper_project(stories, media_name, base, apply_fades=apply_fades, total_duration=tot_dur, unselected_audio_mode=unselected_mode)
                with open(rpp_file, "w", encoding="utf-8") as f:
                    f.write(rpp_text)

            if formats.get("edl") and stories:
                edl_file = transcripts_out / f"{base}.edl"
                media_name = audio_file.name if audio_file else ""
                apply_fades = bool(options.get("apply_audio_fades", True))
                edl_text = generate_samplitude_edl(stories, media_name, base, apply_fades=apply_fades, total_duration=tot_dur, unselected_audio_mode=unselected_mode)
                with open(edl_file, "w", encoding="utf-8") as f:
                    f.write(edl_text)

            if formats.get("audacity") and stories:
                audacity_file = transcripts_out / f"{base}_labels.txt"
                aud_text = generate_audacity_labels(stories, total_duration=tot_dur, unselected_audio_mode=unselected_mode)
                with open(audacity_file, "w", encoding="utf-8") as f:
                    f.write(aud_text)

            if formats.get("audition_xml") and stories:
                xml_file = transcripts_out / f"{base}.xml"
                media_name = audio_file.name if audio_file else ""
                xml_text = generate_audition_xml(stories, media_name, base, total_duration=tot_dur, unselected_audio_mode=unselected_mode)
                with open(xml_file, "w", encoding="utf-8") as f:
                    f.write(xml_text)

            if formats.get("daw_csv") and stories:
                csv_file = transcripts_out / f"{base}_markers.csv"
                csv_text = generate_daw_marker_csv(stories, total_duration=tot_dur, unselected_audio_mode=unselected_mode)
                with open(csv_file, "w", encoding="utf-8") as f:
                    f.write(csv_text)

            if progress_dialog is not None and created_local_dialog:
                progress_dialog.setValue(1)
                safe_process_events()

            if hasattr(self, "log_activity"):
                self.log_activity(f"[EXPORT] Exported full episode to {out}")
            if show_completion and not (progress_dialog and progress_dialog.wasCanceled()):
                show_export_completion_dialog(self, "Export Complete", f"Exported to:\n{out}", str(out))
            return True
        except Exception as exc:
            if "Export cancelled by user" in str(exc) or getattr(self, "export_cancelled", False) or (progress_dialog and progress_dialog.wasCanceled()):
                if hasattr(self, "log_activity"):
                    self.log_activity("[EXPORT] Export operation stopped by user.")
                return False
            if hasattr(self, "log_activity"):
                self.log_activity(f"[ERROR] Full episode export failed: {exc}")
            QMessageBox.critical(self, "Export Error", str(exc))
            return False
        finally:
            if created_local_dialog and progress_dialog is not None:
                progress_dialog.close()

    def perform_stories_export(
        self,
        target_stories: Optional[List[Any]] = None,
        custom_formats: Optional[Dict[str, bool]] = None,
        custom_base: Optional[str] = None,
        custom_options: Optional[Dict[str, Any]] = None,
        directory: Optional[str] = None,
        show_completion: bool = False,
        is_custom_location: bool = False,
    ) -> bool:
        stories = target_stories if target_stories is not None else getattr(self, "stories", [])
        if not stories:
            return False
        project_file = getattr(self, "project_file", None)
        audio_file = getattr(self, "audio_file", None)
        base = custom_base or (safe_filename(project_file.stem if project_file else (audio_file.stem if audio_file else "export")))
        formats = custom_formats or {"txt": True, "docx": True, "pdf": True, "srt": False, "vtt": False, "media": False}
        options = custom_options or {"include_speakers": True, "include_timestamps": False, "include_english": True, "include_spanish": False}
        stories_to_export = list(enumerate(stories))
        success = self._export_story_files(stories_to_export, formats, base, options, directory, is_custom_location=is_custom_location)
        if show_completion and success:
            show_export_completion_dialog(self, "Export Complete", f"Exported {len(stories_to_export)} stories to {directory}", directory)
        return success

    def export_youtube_manual_package(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render and package zero-auth manual YouTube export (MP4, thumbnail, SRT, metadata .txt)."""
        if hasattr(self, "_handle_youtube_export_result"):
            return self._handle_youtube_export_result(export_data)
        return {}
