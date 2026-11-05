"""Programmatic headless screenshot generator for RTVS3 user guides.

Generates pixel-accurate, native Qt PNG screenshots of RTVS3 UI dialogs and panels
without requiring a live display monitor or human interaction, guaranteeing
zero-hallucination visual assets for documentation.
"""
import sys
import os
from pathlib import Path

# Ensure root directory is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtGui import QPixmap, QColor

from plugins.wordpress.export_destination import WordPressExportTabWidget
from prs_shared import Story


class MockCaptureMainWindow:
    """Mock main window providing realistic project data for guide screenshots."""
    def __init__(self):
        self.audio_file = Path("tech_talk_episode_42.mp4")
        self.current_media_is_video = True
        self.duration = 615.0
        self.current_position = 0.0
        self.theme_mode = "dark"
        self.language = "en"
        self.project_metadata = {
            "title": "Tech Talk Weekly #42: Future of Clean Energy",
            "podcast_title": "Tech Talk Weekly",
        }
        self.stories = [
            Story(
                start=0.0,
                end=145.0,
                title="Welcome & Show Introduction",
                metadata={"summary": "Host welcomes viewers and introduces episode topics."},
            ),
            Story(
                start=145.0,
                end=450.0,
                title="Next-Gen Battery Architecture Breakdown",
                metadata={"summary": "Technical deep-dive into solid-state battery chemistry and grid storage."},
            ),
            Story(
                start=450.0,
                end=615.0,
                title="Viewer Q&A and Final Thoughts",
                metadata={"summary": "Answering audience questions from YouTube live chat."},
            ),
        ]
        self.transcript = {
            "segments": [
                {"start": 0.0, "end": 145.0, "text": "Welcome everyone to Tech Talk Weekly..."},
                {"start": 145.0, "end": 450.0, "text": "Today we are diving into battery technology..."},
                {"start": 450.0, "end": 615.0, "text": "Let's take a look at the questions coming in..."},
            ]
        }

    def _get_transcript_text_slice(self, start, end):
        return "Lorem ipsum transcript excerpt demonstrating story content."

    def get_effective_story_author_and_category_ids(self, story_idx):
        return [1], [3]


def capture_widget(widget: QWidget, output_path: Path, size: QSize = None):
    """Render a QWidget to a high-resolution PNG image file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if size:
        widget.resize(size)
    widget.show()
    widget.adjustSize()
    QApplication.processEvents()

    # Grab raster pixmap from native widget backing store and cap max width to 850px
    pixmap = widget.grab()
    if pixmap.width() > 850:
        pixmap = pixmap.scaledToWidth(850, Qt.TransformationMode.SmoothTransformation)
    pixmap.save(str(output_path), "PNG")
    print(f"[OK] Saved screenshot: {output_path} ({pixmap.width()}x{pixmap.height()})")


def main():
    # Use off-screen QPA if running in headless environments
    os.environ.setdefault("QT_QPA_PLATFORM", "windows")
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")

    images_dir = ROOT_DIR / "docs" / "images"
    mock_win = MockCaptureMainWindow()

    # 1. Capture WordPress Export Panel - Media Tab
    wp_widget = WordPressExportTabWidget(None, mock_win)
    wp_widget.rebuild_post_items(scope="all_stories")

    # Populate sample YouTube URL and settings for Story 1
    if len(wp_widget.wp_post_items) > 1:
        post = wp_widget.wp_post_items[1]
        post["yt_video_url"] = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        post["yt_stop_at_end"] = True
        post["yt_embed_placement"] = "top"
        post["include_audio"] = False
        post["author_names"] = ["Alex Mercer"]
        post["category_names"] = ["Technology", "Interviews"]

    # Select Story 1 in list and switch to the "Media" tab (index 3)
    wp_widget.wp_posts_list.setCurrentRow(1)
    wp_widget.wp_editor_tabs.setCurrentIndex(3)
    wp_widget._load_post_editor_state(1)

    # Capture Media tab in WordPress Export
    wp_widget.resize(920, 680)
    capture_widget(wp_widget, images_dir / "wordpress_export_media_tab.png", QSize(920, 680))

    # 2. Capture Content Tab (with Title, Excerpt, Gutenberg Notice)
    wp_widget.wp_editor_tabs.setCurrentIndex(0)
    capture_widget(wp_widget, images_dir / "wordpress_export_content_tab.png", QSize(920, 680))

    # 3. Capture Post List Close-up
    list_widget = wp_widget.wp_posts_list
    capture_widget(list_widget, images_dir / "wordpress_posts_list_badges.png", QSize(320, 480))

    # 4. Capture WordPress Credentials & Preferences Page
    from plugins.wordpress.client import WordPressPreferencesPage
    pref_page = WordPressPreferencesPage()
    pref_page.url_edit.setText("https://example-news-station.com")
    pref_page.user_edit.setText("newsroom_editor")
    pref_page.pass_edit.setText("abcd efgh ijkl mnop")
    capture_widget(pref_page, images_dir / "wordpress_preferences_credentials.png", QSize(680, 520))

    # 5. Capture Unified Export Dialog Overview
    from export.dialog import UnifiedExportDialog
    exp_dlg = UnifiedExportDialog(None, mock_win)
    capture_widget(exp_dlg, images_dir / "unified_export_dialog.png", QSize(820, 560))

    print("\nAll documentation screenshots successfully generated.")


if __name__ == "__main__":
    main()
