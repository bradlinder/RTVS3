# Changelog

## v3.9.84-beta
- **WordPress Post List Indicator Placement & Story Duplicate Title Elimination (`plugins/wordpress/wp_post_builder.py`, `plugins/wordpress/youtube_embed.py`, `plugins/wordpress/wp_tab_widget.py`, `scripts/capture_guide_screenshots.py`, `docs/images/`)**:
  - **Start-of-Title Indicator Placement (`plugins/wordpress/youtube_embed.py`)**: Positioned media badges (`[A]`, `[Img]`, `[YT]`, `[Pod]`) consistently across all post types (Full Episodes and Stories alike) directly after the item identifier and before the post headline (e.g. `Story 1 [A]: Demonstrators push for more funding...` and `Full Episode [Pod, Img]: November 11, 2026 (Block by Block)`). Ensures badges are immediately visible without horizontal scrolling or truncation.
  - **Duplicate Story Title Bug Fix (`plugins/wordpress/wp_post_builder.py`)**: Fixed an issue where story definitions in `build_wp_post_items` concatenated `f": {st.title}"` into `item["task_label"]`, causing the post list formatter to display the story title twice (e.g. `Story 1: Title [A]: Title`). Standardized `task_label` to clean identifiers (`Story 1`, `Story 2`).
  - **Defensive Prefix Normalization (`plugins/wordpress/youtube_embed.py`, `plugins/wordpress/wp_post_builder.py`)**: Added defensive regex/prefix stripping to ensure legacy saved projects or cached sessions containing concatenated titles in `task_label` are cleanly normalized to `Story N` and indexed under both keys without title repetition.
  - **Editor Header Formatting Parity (`plugins/wordpress/wp_tab_widget.py`)**: Updated `_load_post_editor_state` and `_on_title_edited` so the post editor panel header displays clean, informative labels (`Post Settings: Story 1: Title` or `Post Settings: Full Episode`) in real time as titles are modified.
  - **Updated Documentation Screenshots (`scripts/capture_guide_screenshots.py`, `docs/images/`)**: Regenerated `wordpress_posts_list_badges.png` and WordPress dialog screenshots reflecting the corrected badge order and clean story headlines.

## v3.9.83-beta
- **User Guide Screenshot Alignment, Correct Media Tab Captures & Dedicated Tab Previews (`scripts/capture_guide_screenshots.py`, `docs/guides/wordpress_exporting.md`, `docs/images/`, `embedded_guides.py`)**:
  - **Media Tab Capture Correction (`scripts/capture_guide_screenshots.py`, `docs/images/wordpress_export_media_tab.png`)**: Corrected tab index in the automated screenshot generator from index 3 (Publishing & Formatting) to index 2 (the actual Media tab). `wordpress_export_media_tab.png` now accurately displays the YouTube video link input, 16:9 placement controls, featured image grabber, and audio/podcast attachment options.
  - **Dedicated Screenshots for Every Editor Tab (`docs/images/`)**: Added dedicated, pixel-accurate screenshots for all WordPress post configuration tabs:
    - `wordpress_export_content_tab.png`: Tab 1 (Post Content) showing Title, Excerpt, and Custom Notice.
    - `wordpress_export_taxonomy_tab.png`: Tab 2 (Authors & Taxonomy) showing Author and Category lists with filters.
    - `wordpress_export_media_tab.png`: Tab 3 (Media) showing YouTube link, Thumbnail grabber, and Audio settings.
    - `wordpress_export_publishing_tab.png`: Tab 4 (Publishing & Formatting) showing Languages and Episode Cross-Linking.
  - **Documentation Placement Synchronized (`docs/guides/wordpress_exporting.md`, `embedded_guides.py`)**: Aligned image markdown embeds so each tab's screenshot appears directly beneath its own dedicated heading.
