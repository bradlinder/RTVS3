# Changelog

## v3.9.83-beta
- **User Guide Screenshot Alignment, Correct Media Tab Captures & Dedicated Tab Previews (`scripts/capture_guide_screenshots.py`, `docs/guides/wordpress_exporting.md`, `docs/images/`, `embedded_guides.py`)**:
  - **Media Tab Capture Correction (`scripts/capture_guide_screenshots.py`, `docs/images/wordpress_export_media_tab.png`)**: Corrected tab index in the automated screenshot generator from index 3 (Publishing & Formatting) to index 2 (the actual Media tab). `wordpress_export_media_tab.png` now accurately displays the YouTube video link input, 16:9 placement controls, featured image grabber, and audio/podcast attachment options.
  - **Dedicated Screenshots for Every Editor Tab (`docs/images/`)**: Added dedicated, pixel-accurate screenshots for all WordPress post configuration tabs:
    - `wordpress_export_content_tab.png`: Tab 1 (Post Content) showing Title, Excerpt, and Custom Notice.
    - `wordpress_export_taxonomy_tab.png`: Tab 2 (Authors & Taxonomy) showing Author and Category lists with filters.
    - `wordpress_export_media_tab.png`: Tab 3 (Media) showing YouTube link, Thumbnail grabber, and Audio settings.
    - `wordpress_export_publishing_tab.png`: Tab 4 (Publishing & Formatting) showing Languages and Episode Cross-Linking.
  - **Documentation Placement Synchronized (`docs/guides/wordpress_exporting.md`, `embedded_guides.py`)**: Aligned image markdown embeds so each tab's screenshot appears directly beneath its own dedicated heading.

## v3.9.82-beta
- **WordPress Post List Expandable Sidebar, Compact Prefix Indicators & Documentation Accuracy Overhaul (`plugins/wordpress/wp_ui_builder.py`, `plugins/wordpress/youtube_embed.py`, `plugins/wordpress/manifest.json`, `docs/guides/`, `embedded_guides.py`)**:
  - **Compact Start-of-Title Prefix Badges (`plugins/wordpress/youtube_embed.py`)**: Moved media and post indicators from the end of the story title to compact prefix badges directly following the story number (e.g. `Story 1 [YT, A]: Demonstrators...` or `Story 2 [Pod]: A shuttle...`). Ensures post type indicators (`[YT]` = YouTube embed, `[Pod]` = Podcast RSS enclosure, `[A]` = MP3 audio cut, `[Img]` = Featured thumbnail) are immediately visible within the first 15 characters without being pushed offscreen by long headlines.
  - **Expandable Post List Sidebar (`plugins/wordpress/wp_ui_builder.py`)**: Upgraded `wp_posts_container` from a fixed-width `QHBoxLayout` with a 220px maximum cap to a horizontal `QSplitter`. Users can freely drag the splitter divider to expand the sidebar or narrow it to their preference.
  - **User Guide Accuracy Audit (`docs/guides/`, `embedded_guides.py`)**: Thoroughly audited and corrected all 5 user guides to accurately describe current UI controls, tab titles, and workflows.
