# Changelog

## v3.9.63-beta
- **Complete Drag-and-Drop Restoration Across All Native Targets (`timeline_widgets.py`, `timeline_overview_widget.py`, `transcript_editor.py`, `RadioTVSegmenter.py`)**:
  - **Comprehensive Widget-Level Event Coverage**: Implemented missing `dragMoveEvent` alongside `dragEnterEvent` and `dropEvent` across `TimelineCanvas`, `TimelineWidget`, and `TimelineOverviewBar`, ensuring continuous mouse movement over the timeline canvas does not cause Windows OLE to drop to `DROPEFFECT_NONE` (?? cursor).
  - **Direct-to-Canvas Audio Ingestion (`timeline_widgets.py`)**: Restored `self.setAcceptDrops(True)` and direct `extract_dropped_file_paths(event.mimeData())` handling on `TimelineCanvas`, emitting `mediaDropped` directly into `_handle_dropped_media_or_project`.
  - **Transcript Window File Dropping (`transcript_editor.py`)**: Wired `InteractiveTranscriptEdit`'s `dragEnterEvent`, `dragMoveEvent`, and `dropEvent` with `extract_dropped_file_paths` so dropping audio/video files directly into the transcript area reliably opens them.
  - **Top-Level Fallback Acceptance (`RadioTVSegmenter.py`)**: Enabled `self.setAcceptDrops(True)` and clean drag events on `MainWindow` as a universal drop target for window borders and background areas.

## v3.9.62-beta
- **Dual-Target Native Drag-and-Drop Restoration for Timeline & Transcript (`playback_controller.py`, `RadioTVSegmenter.py`, `timeline_widgets.py`, `timeline_overview_widget.py`, `transcript_editor.py`, `build_installer.py`)**:
  - **De-overengineered Architecture & Global Interceptor Pruning (`playback_controller.py`, `RadioTVSegmenter.py`)**: Completely removed the application-wide `eventFilter` drag interception in `playback_controller.py` that was consuming events at the `QApplication` level, as well as `MainWindow` drop handlers and `win32_dnd.py` message filter collisions.
  - **Direct-to-Widget Timeline Ingestion (`timeline_widgets.py`, `timeline_overview_widget.py`)**: Restored the clean, native Qt widget-level drop handling on `TimelineCanvas` and `TimelineWidget` using standard `event.mimeData().hasUrls()` and `event.acceptProposedAction()`, dispatching dropped file paths directly to `mediaDropped` and `load_media_file`.
  - **Direct-to-Widget Transcript Ingestion (`transcript_editor.py`)**: Standardized `TranscriptEditor`'s `dragEnterEvent` and `dropEvent` to accept dropped audio/video media files and project archives natively, matching the visual empty-state invitation card (*"Drop an Audio or Video File Here to Begin"*).
  - **Native OLE Integrity**: Preserved unhindered OLE communication between Windows Explorer and Qt's Windows platform plugin (`qwindows.dll`), eliminating drop cursor rejections across installed desktop environments.
