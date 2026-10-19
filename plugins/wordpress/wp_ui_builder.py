"""UI layout construction and widget setup for WordPressExportTabWidget."""
from __future__ import annotations

from typing import Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from prs_shared import (
    CollapsibleSection,
    ResizableTextEdit,
    get_active_theme_mode,
)

def setup_wp_tab_ui(self: Any):
    """Construct all controls, forms, sliders, list widgets, and collapsible panels for the WordPress export tab."""
    wp_page_layout = QVBoxLayout(self)
    wp_page_layout.setContentsMargins(0, 0, 0, 0)

    wp_scroll = QScrollArea()
    wp_scroll.setWidgetResizable(True)
    wp_scroll.setFrameShape(QFrame.Shape.NoFrame)
    wp_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    wp_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    wp_scroll_content = QWidget()
    wp_layout = QVBoxLayout(wp_scroll_content)
    wp_layout.setContentsMargins(2, 2, 2, 2)
    wp_layout.setSpacing(10)

    self.wp_info_section = CollapsibleSection("WordPress Post Configuration", self, is_expanded=True, subtitle="Title, Excerpt, Authors, Categories")
    if getattr(self, "metadata_editor_mode", False):
        wp_notice = QLabel(
            "Configure WordPress post titles, excerpts, authors, categories, and featured images "
            "for the full episode and all stories. Changes are saved directly to your project."
        )
    else:
        wp_notice = QLabel(
            "Extracts audio as <b>128 kbps MP3</b>, uploads to your WordPress Media Library, "
            "and creates a <b>Draft Post</b> with Gutenberg audio player and formatted transcript."
        )
    wp_notice.setWordWrap(True)
    self.wp_info_section.add_widget(wp_notice)

    # Master-Detail Container for Posts
    self.wp_posts_container = QHBoxLayout()
    self.wp_posts_container.setSpacing(12)

    # Left Nav: Post selector
    self.wp_post_nav_widget = QWidget()
    nav_layout = QVBoxLayout(self.wp_post_nav_widget)
    nav_layout.setContentsMargins(0, 0, 0, 0)
    nav_layout.setSpacing(6)
    nav_label = QLabel("<b>Posts to Export:</b>")
    self.wp_posts_list = QListWidget()
    self.wp_posts_list.setMinimumWidth(160)
    self.wp_posts_list.setMaximumWidth(220)
    self.wp_autofill_all_excerpts_btn = QPushButton("Auto-fill All Excerpts")
    self.wp_autofill_all_excerpts_btn.setToolTip("Auto-generate snippet (≤55 words) from transcript for every post")
    self.wp_autofill_all_excerpts_btn.clicked.connect(self._autofill_all_excerpts)

    nav_layout.addWidget(nav_label)
    nav_layout.addWidget(self.wp_posts_list, 1)
    nav_layout.addWidget(self.wp_autofill_all_excerpts_btn)
    self.wp_posts_container.addWidget(self.wp_post_nav_widget)

    # Right Pane: Detailed post editor
    self.wp_post_editor_widget = QWidget()
    editor_layout = QVBoxLayout(self.wp_post_editor_widget)
    editor_layout.setContentsMargins(0, 0, 0, 0)
    editor_layout.setSpacing(8)

    self.wp_current_post_header = QLabel("<b>Post Settings</b>")
    self.wp_current_post_header.setStyleSheet("color: #38bdf8; font-size: 12px;")
    editor_layout.addWidget(self.wp_current_post_header)

    # Title Field
    post_title_row = QHBoxLayout()
    post_title_row.addWidget(QLabel("Post Title:"))
    self.wp_title_edit = QLineEdit()
    self.wp_title_edit.textEdited.connect(self._on_title_edited)
    post_title_row.addWidget(self.wp_title_edit, 1)
    editor_layout.addLayout(post_title_row)

    # Excerpt Field
    excerpt_box = QVBoxLayout()
    excerpt_box.setSpacing(3)
    exc_hdr = QHBoxLayout()
    exc_hdr.addWidget(QLabel("Excerpt / Description (≤55 words):"))
    exc_hdr.addStretch()
    self.wp_auto_excerpt_btn = QPushButton("Generate from Story")
    self.wp_auto_excerpt_btn.setToolTip("Auto-generate excerpt from the current story's transcript")
    self.wp_auto_excerpt_btn.clicked.connect(self._auto_generate_current_excerpt)
    exc_hdr.addWidget(self.wp_auto_excerpt_btn)
    excerpt_box.addLayout(exc_hdr)

    self.wp_excerpt_edit = ResizableTextEdit()
    self.wp_excerpt_edit.setMaximumHeight(55)
    self.wp_excerpt_edit.textChanged.connect(self._on_excerpt_edited)
    excerpt_box.addWidget(self.wp_excerpt_edit)
    editor_layout.addLayout(excerpt_box)

    # Dual Column: Authors and Categories Checklist
    tax_container = QHBoxLayout()
    tax_container.setSpacing(10)

    # Author selection column
    author_col = QVBoxLayout()
    author_col.setSpacing(3)
    auth_hdr = QHBoxLayout()
    auth_hdr.addWidget(QLabel("Authors:"))
    auth_hdr.addStretch()
    self.wp_clear_authors_btn = QPushButton("Clear")
    self.wp_clear_authors_btn.setStyleSheet("padding: 1px 6px; font-size: 10px;")
    self.wp_clear_authors_btn.clicked.connect(self._clear_current_authors)
    auth_hdr.addWidget(self.wp_clear_authors_btn)
    author_col.addLayout(auth_hdr)

    self.wp_author_filter_edit = QLineEdit()
    self.wp_author_filter_edit.setPlaceholderText("Filter authors...")
    self.wp_author_filter_edit.textChanged.connect(self._filter_authors_list)
    author_col.addWidget(self.wp_author_filter_edit)

    self.wp_author_list = QListWidget()
    self.wp_author_list.setMaximumHeight(95)
    self.wp_author_list.itemChanged.connect(self._on_author_item_changed)
    author_col.addWidget(self.wp_author_list)
    tax_container.addLayout(author_col)

    # Category selection column
    cat_col = QVBoxLayout()
    cat_col.setSpacing(3)
    cat_hdr = QHBoxLayout()
    cat_hdr.addWidget(QLabel("Categories:"))
    cat_hdr.addStretch()
    self.wp_clear_cats_btn = QPushButton("Clear")
    self.wp_clear_cats_btn.setStyleSheet("padding: 1px 6px; font-size: 10px;")
    self.wp_clear_cats_btn.clicked.connect(self._clear_current_categories)
    cat_hdr.addWidget(self.wp_clear_cats_btn)
    cat_col.addLayout(cat_hdr)

    self.wp_category_filter_edit = QLineEdit()
    self.wp_category_filter_edit.setPlaceholderText("Filter categories...")
    self.wp_category_filter_edit.textChanged.connect(self._filter_categories_list)
    cat_col.addWidget(self.wp_category_filter_edit)

    self.wp_category_list = QListWidget()
    self.wp_category_list.setMaximumHeight(95)
    self.wp_category_list.itemChanged.connect(self._on_category_item_changed)
    cat_col.addWidget(self.wp_category_list)
    tax_container.addLayout(cat_col)

    editor_layout.addLayout(tax_container)

    # Featured Image Section
    self.wp_thumb_section = CollapsibleSection("Featured Image (Thumbnail)", self, is_expanded=True)
    wp_thumb_layout = QHBoxLayout()
    wp_thumb_layout.setSpacing(10)

    wp_thumb_controls = QVBoxLayout()
    wp_thumb_controls.setSpacing(6)

    self.wp_rad_thumb_none = QRadioButton("None")
    self.wp_rad_thumb_grab = QRadioButton("Grab frame from video")
    self.wp_rad_thumb_file = QRadioButton("Select custom image file...")
    self.wp_rad_thumb_none.setChecked(True)

    if not self._is_video_project:
        self.wp_rad_thumb_grab.setEnabled(False)
        self.wp_rad_thumb_grab.setText("Grab frame from video (Audio-only project)")
        self.wp_rad_thumb_grab.setToolTip("Video frame capture requires video media (audio-only file loaded)")

    wp_thumb_controls.addWidget(self.wp_rad_thumb_none)
    wp_thumb_controls.addWidget(self.wp_rad_thumb_grab)

    # In-dialog Frame Scrubber & Stepper for WordPress
    self.wp_scrub_widget = QWidget()
    wp_scrub_vbox = QVBoxLayout(self.wp_scrub_widget)
    wp_scrub_vbox.setContentsMargins(16, 2, 4, 4)
    wp_scrub_vbox.setSpacing(4)

    self.wp_scrub_slider = QSlider(Qt.Orientation.Horizontal)
    self.wp_scrub_slider.setRange(0, 10000)
    self.wp_scrub_slider.valueChanged.connect(self._on_wp_slider_value_changed)
    wp_scrub_vbox.addWidget(self.wp_scrub_slider)

    wp_stepper_row = QHBoxLayout()
    wp_stepper_row.setSpacing(4)
    self.wp_step_back_sec_btn = QPushButton("◀ -1s")
    self.wp_step_back_sec_btn.setToolTip("Step backward 1 second")
    self.wp_step_back_sec_btn.clicked.connect(lambda: self._on_wp_step(-1.0))
    self.wp_step_back_frame_btn = QPushButton("◀ -1f")
    self.wp_step_back_frame_btn.setToolTip("Step backward 1 frame (~33ms)")
    self.wp_step_back_frame_btn.clicked.connect(lambda: self._on_wp_step(-0.0333))

    self.wp_scrub_time_label = QLabel("00:00:00.000")
    self.wp_scrub_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.wp_scrub_time_label.setStyleSheet("padding: 2px 6px; background-color: #0f172a; border: 1px solid #334155; border-radius: 4px; font-family: monospace; font-size: 11px; font-weight: bold; color: #e2e8f0;")

    self.wp_step_fwd_frame_btn = QPushButton("+1f ▶")
    self.wp_step_fwd_frame_btn.setToolTip("Step forward 1 frame (~33ms)")
    self.wp_step_fwd_frame_btn.clicked.connect(lambda: self._on_wp_step(0.0333))
    self.wp_step_fwd_sec_btn = QPushButton("+1s ▶")
    self.wp_step_fwd_sec_btn.setToolTip("Step forward 1 second")
    self.wp_step_fwd_sec_btn.clicked.connect(lambda: self._on_wp_step(1.0))
    self.wp_sync_playhead_btn = QPushButton("⟳ Playhead")
    self.wp_sync_playhead_btn.setToolTip("Sync thumbnail position to the main timeline playhead")
    self.wp_sync_playhead_btn.clicked.connect(self._on_wp_sync_playhead)

    wp_stepper_row.addWidget(self.wp_step_back_sec_btn)
    wp_stepper_row.addWidget(self.wp_step_back_frame_btn)
    wp_stepper_row.addWidget(self.wp_scrub_time_label)
    wp_stepper_row.addWidget(self.wp_step_fwd_frame_btn)
    wp_stepper_row.addWidget(self.wp_step_fwd_sec_btn)
    wp_stepper_row.addWidget(self.wp_sync_playhead_btn)
    wp_stepper_row.addStretch()
    wp_scrub_vbox.addLayout(wp_stepper_row)
    self.wp_scrub_widget.setVisible(False)
    wp_thumb_controls.addWidget(self.wp_scrub_widget)

    wp_thumb_controls.addWidget(self.wp_rad_thumb_file)

    # Custom Browse Button row
    self.wp_browse_widget = QWidget()
    wp_browse_box = QHBoxLayout(self.wp_browse_widget)
    wp_browse_box.setContentsMargins(16, 2, 4, 4)
    wp_browse_box.setSpacing(6)
    self.wp_browse_thumb_btn = QPushButton("Browse Image...")
    self.wp_browse_thumb_btn.clicked.connect(self._on_wp_browse_thumb)
    wp_browse_box.addWidget(self.wp_browse_thumb_btn)
    wp_browse_box.addStretch()
    self.wp_browse_widget.setVisible(False)
    wp_thumb_controls.addWidget(self.wp_browse_widget)

    self.wp_thumb_path_label = QLabel("No image selected")
    self.wp_thumb_path_label.setStyleSheet("color: #64748b; font-size: 11px;")
    wp_thumb_controls.addWidget(self.wp_thumb_path_label)

    wp_thumb_layout.addLayout(wp_thumb_controls, stretch=2)

    wp_mode = get_active_theme_mode("dark")

    self.wp_thumb_preview_label = QLabel("No Thumbnail")
    self.wp_thumb_preview_label.setFixedSize(160, 90)
    self.wp_thumb_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if wp_mode == "light":
        self.wp_thumb_preview_label.setStyleSheet("border: 1px dashed #b6bcc4; border-radius: 4px; background-color: #eaedf0; color: #78808d; font-size: 10px;")
    elif wp_mode == "high_contrast":
        self.wp_thumb_preview_label.setStyleSheet("border: 1px dashed #ffffff; border-radius: 4px; background-color: #000000; color: #ffffff; font-size: 10px;")
    else:
        self.wp_thumb_preview_label.setStyleSheet("border: 1px dashed #475569; border-radius: 4px; background-color: #0f172a; color: #64748b; font-size: 10px;")
    wp_thumb_layout.addWidget(self.wp_thumb_preview_label, stretch=1)

    self.wp_thumb_section.add_layout(wp_thumb_layout)
    editor_layout.addWidget(self.wp_thumb_section)

    self.wp_rad_thumb_none.toggled.connect(self._on_wp_thumb_mode_changed)
    self.wp_rad_thumb_grab.toggled.connect(self._on_wp_thumb_mode_changed)
    self.wp_rad_thumb_file.toggled.connect(self._on_wp_thumb_mode_changed)

    # Bulk Actions Rows
    self.wp_bulk_box = QWidget()
    bulk_vbox = QVBoxLayout(self.wp_bulk_box)
    bulk_vbox.setContentsMargins(0, 4, 0, 4)
    bulk_vbox.setSpacing(4)

    bulk_hdr = QLabel("<b>Bulk Apply to Other Posts / Stories:</b>")
    if wp_mode == "light":
        bulk_hdr.setStyleSheet("color: #545b66; font-size: 11px;")
    elif wp_mode == "high_contrast":
        bulk_hdr.setStyleSheet("color: #ffffff; font-size: 11px;")
    else:
        bulk_hdr.setStyleSheet("color: #94a3b8; font-size: 11px;")
    bulk_vbox.addWidget(bulk_hdr)

    bulk_row1 = QHBoxLayout()
    bulk_row1.setSpacing(6)
    self.wp_apply_authors_selected_btn = QPushButton("Apply Authors to Selected Stories")
    self.wp_apply_authors_selected_btn.setToolTip("Copy this post's author selection to currently selected stories")
    self.wp_apply_authors_selected_btn.clicked.connect(self._apply_authors_to_selected_stories)

    self.wp_apply_authors_all_btn = QPushButton("Apply Authors to All Posts")
    self.wp_apply_authors_all_btn.setToolTip("Copy this post's author selection to all other posts in the queue")
    self.wp_apply_authors_all_btn.clicked.connect(self._apply_authors_to_all_posts)
    bulk_row1.addWidget(self.wp_apply_authors_selected_btn)
    bulk_row1.addWidget(self.wp_apply_authors_all_btn)
    bulk_row1.addStretch()
    bulk_vbox.addLayout(bulk_row1)

    bulk_row2 = QHBoxLayout()
    bulk_row2.setSpacing(6)
    self.wp_apply_cats_selected_btn = QPushButton("Apply Categories to Selected Stories")
    self.wp_apply_cats_selected_btn.setToolTip("Copy this post's category selection to currently selected stories")
    self.wp_apply_cats_selected_btn.clicked.connect(self._apply_categories_to_selected_stories)

    self.wp_apply_cats_all_btn = QPushButton("Apply Categories to All Posts")
    self.wp_apply_cats_all_btn.setToolTip("Copy this post's category selection to all other posts in the queue")
    self.wp_apply_cats_all_btn.clicked.connect(self._apply_categories_to_all_posts)
    bulk_row2.addWidget(self.wp_apply_cats_selected_btn)
    bulk_row2.addWidget(self.wp_apply_cats_all_btn)
    bulk_row2.addStretch()
    bulk_vbox.addLayout(bulk_row2)

    bulk_row3 = QHBoxLayout()
    bulk_row3.setSpacing(6)
    self.wp_apply_thumb_selected_btn = QPushButton("Apply Thumbnail to Selected Stories")
    self.wp_apply_thumb_selected_btn.setToolTip("Copy this post's thumbnail selection to currently selected stories")
    self.wp_apply_thumb_selected_btn.clicked.connect(self._apply_thumbnails_to_selected_stories)

    self.wp_apply_thumb_all_btn = QPushButton("Apply Thumbnail to All Posts")
    self.wp_apply_thumb_all_btn.setToolTip("Copy this post's thumbnail selection to all other posts in the queue")
    self.wp_apply_thumb_all_btn.clicked.connect(self._apply_thumbnails_to_all_posts)
    bulk_row3.addWidget(self.wp_apply_thumb_selected_btn)
    bulk_row3.addWidget(self.wp_apply_thumb_all_btn)
    bulk_row3.addStretch()
    bulk_vbox.addLayout(bulk_row3)

    editor_layout.addWidget(self.wp_bulk_box)

    self.wp_posts_container.addWidget(self.wp_post_editor_widget)
    self.wp_info_section.add_layout(self.wp_posts_container)

    self.wp_posts_list.currentRowChanged.connect(self._on_wp_post_selection_changed)

    # Load cached metadata
    self._populate_wp_export_metadata(force_refresh=False)
    self.rebuild_post_items()

    # Metadata Refresh Button Row
    meta_btn_row = QHBoxLayout()
    self.wp_refresh_meta_btn = QPushButton("Refresh WordPress Metadata")
    self.wp_refresh_meta_btn.setToolTip("Fetch fresh Author and Category lists from WordPress site")
    self.wp_refresh_meta_btn.clicked.connect(self._refresh_wp_metadata)
    meta_btn_row.addStretch()
    meta_btn_row.addWidget(self.wp_refresh_meta_btn)
    self.wp_info_section.add_layout(meta_btn_row)
    wp_layout.addWidget(self.wp_info_section)

    # Languages & Presentation
    self.wp_lang_section = CollapsibleSection("Transcript Languages & Presentation", self, is_expanded=True)
    wp_lang_checks = QHBoxLayout()
    src_code = self.main_window.source_language_code() if hasattr(self.main_window, "source_language_code") else "en"
    has_translation = False
    if hasattr(self.main_window, "get_spanish_translation_item"):
        trans_item = self.main_window.get_spanish_translation_item()
        if trans_item and isinstance(trans_item, dict):
            has_translation = bool(trans_item.get("segments"))

    if src_code == "es":
        self.wp_cb_es = QCheckBox("Spanish")
        self.wp_cb_es.setChecked(True)
        self.wp_cb_es.setEnabled(True)

        self.wp_cb_en = QCheckBox("English (Translated)")
        self.wp_cb_en.setChecked(has_translation)
        self.wp_cb_en.setEnabled(has_translation)
        if not has_translation:
            self.wp_cb_en.setToolTip("English translation is not available for this project. Generate a translation first to enable.")
    else:
        self.wp_cb_en = QCheckBox("English")
        self.wp_cb_en.setChecked(True)
        self.wp_cb_en.setEnabled(True)

        self.wp_cb_es = QCheckBox("Spanish (Translated)")
        self.wp_cb_es.setChecked(has_translation)
        self.wp_cb_es.setEnabled(has_translation)
        if not has_translation:
            self.wp_cb_es.setToolTip("Spanish translation is not available for this project. Generate a translation first to enable.")

    wp_lang_checks.addWidget(self.wp_cb_en)
    wp_lang_checks.addWidget(self.wp_cb_es)
    wp_lang_checks.addStretch()
    self.wp_lang_section.add_layout(wp_lang_checks)

    # Dual language options
    self.wp_pres_container = QWidget()
    pres_layout = QVBoxLayout(self.wp_pres_container)
    pres_layout.setContentsMargins(0, 4, 0, 0)
    pres_layout.setSpacing(6)

    prim_row = QHBoxLayout()
    prim_label = QLabel("Primary Language:")
    self.wp_primary_lang_combo = QComboBox()
    self.wp_primary_lang_combo.addItem("English", "en")
    self.wp_primary_lang_combo.addItem("Spanish", "es")
    idx = self.wp_primary_lang_combo.findData(src_code)
    if idx >= 0:
        self.wp_primary_lang_combo.setCurrentIndex(idx)
    else:
        self.wp_primary_lang_combo.setCurrentIndex(0)
    prim_row.addWidget(prim_label)
    prim_row.addWidget(self.wp_primary_lang_combo)
    prim_row.addStretch()
    pres_layout.addLayout(prim_row)

    pres_row = QHBoxLayout()
    pres_label = QLabel("Placement:")
    self.wp_pres_combo = QComboBox()
    self.wp_pres_combo.addItem("Interactive language toggle (Accordion)", "accordion")
    if src_code == "es":
        self.wp_pres_combo.addItem("Spanish first, English below", "es_first")
        self.wp_pres_combo.addItem("English first, Spanish below", "en_first")
    else:
        self.wp_pres_combo.addItem("English first, Spanish below", "en_first")
        self.wp_pres_combo.addItem("Spanish first, English below", "es_first")
    pres_row.addWidget(pres_label)
    pres_row.addWidget(self.wp_pres_combo)
    pres_row.addStretch()
    pres_layout.addLayout(pres_row)

    self.wp_accordion_pos_container = QWidget()
    acc_pos_layout = QHBoxLayout(self.wp_accordion_pos_container)
    acc_pos_layout.setContentsMargins(0, 4, 0, 4)
    acc_pos_label = QLabel("Accordion Position:")
    self.wp_accordion_pos_group = QButtonGroup(self)
    self.wp_rad_acc_top = QRadioButton("Place at top (before transcript)")
    self.wp_rad_acc_bottom = QRadioButton("Place at bottom (after transcript)")
    self.wp_accordion_pos_group.addButton(self.wp_rad_acc_top)
    self.wp_accordion_pos_group.addButton(self.wp_rad_acc_bottom)

    saved_acc_pos = str(self.settings.value("wp_accordion_pos", "top") or "top").lower()
    if saved_acc_pos == "bottom":
        self.wp_rad_acc_bottom.setChecked(True)
    else:
        self.wp_rad_acc_top.setChecked(True)

    acc_pos_layout.addWidget(acc_pos_label)
    acc_pos_layout.addWidget(self.wp_rad_acc_top)
    acc_pos_layout.addWidget(self.wp_rad_acc_bottom)
    acc_pos_layout.addStretch()
    pres_layout.addWidget(self.wp_accordion_pos_container)

    def update_wp_accordion_pos_visibility():
        is_acc = self.wp_pres_combo.currentData() == "accordion"
        self.wp_accordion_pos_container.setVisible(is_acc)

    self.wp_pres_combo.currentIndexChanged.connect(update_wp_accordion_pos_visibility)

    def on_wp_primary_lang_changed():
        p_code = self.wp_primary_lang_combo.currentData()
        prev_pres = self.wp_pres_combo.currentData()
        self.wp_pres_combo.blockSignals(True)
        self.wp_pres_combo.clear()
        self.wp_pres_combo.addItem("Interactive language toggle (Accordion)", "accordion")
        if p_code == "es":
            self.wp_pres_combo.addItem("Spanish first, English below", "es_first")
            self.wp_pres_combo.addItem("English first, Spanish below", "en_first")
        else:
            self.wp_pres_combo.addItem("English first, Spanish below", "en_first")
            self.wp_pres_combo.addItem("Spanish first, English below", "es_first")
        match_idx = self.wp_pres_combo.findData(prev_pres)
        self.wp_pres_combo.setCurrentIndex(match_idx if match_idx >= 0 else 0)
        self.wp_pres_combo.blockSignals(False)
        update_wp_accordion_pos_visibility()

    self.wp_primary_lang_combo.currentIndexChanged.connect(on_wp_primary_lang_changed)

    self.wp_lang_section.add_widget(self.wp_pres_container)

    def update_wp_pres_visibility():
        both = self.wp_cb_en.isChecked() and self.wp_cb_es.isChecked()
        self.wp_pres_container.setVisible(both)
        if both:
            update_wp_accordion_pos_visibility()

    self.wp_cb_en.toggled.connect(update_wp_pres_visibility)
    self.wp_cb_es.toggled.connect(update_wp_pres_visibility)
    update_wp_pres_visibility()
    update_wp_accordion_pos_visibility()
    wp_layout.addWidget(self.wp_lang_section)

    # Custom Notice Section
    self.wp_custom_section = CollapsibleSection("Custom Header / Footer Notice (Optional)", self, is_expanded=False)
    self.wp_custom_text_edit = ResizableTextEdit("")
    self.wp_custom_text_edit.setPlaceholderText(
        "e.g. Note: The following transcript was machine-generated and may contain some spelling errors or other inaccuracies."
    )
    self.wp_custom_text_edit.setMaximumHeight(65)
    self.wp_custom_section.add_widget(self.wp_custom_text_edit)

    wp_pos_row = QHBoxLayout()
    self.wp_pos_button_group = QButtonGroup(self)
    self.wp_rad_pos_top = QRadioButton("Place at top of post")
    self.wp_rad_pos_bottom = QRadioButton("Place at bottom of post")
    self.wp_pos_button_group.addButton(self.wp_rad_pos_top)
    self.wp_pos_button_group.addButton(self.wp_rad_pos_bottom)
    self.wp_rad_pos_top.setChecked(True)
    wp_pos_row.addWidget(self.wp_rad_pos_top)
    wp_pos_row.addWidget(self.wp_rad_pos_bottom)
    wp_pos_row.addStretch()
    self.wp_custom_section.add_layout(wp_pos_row)
    wp_layout.addWidget(self.wp_custom_section)

    # Cross-Linking Section (Full Episode & Stories)
    self.wp_crosslink_section = CollapsibleSection("Episode & Story Cross-Linking (Full Episode & All Stories)", self, is_expanded=True)
    crosslink_layout = QVBoxLayout()
    crosslink_layout.setContentsMargins(4, 4, 4, 4)
    crosslink_layout.setSpacing(6)

    self.wp_cb_link_parent = QCheckBox("Add link to Full Episode post in individual story posts")
    self.wp_cb_link_parent.setToolTip("When exporting a Full Episode along with stories, automatically adds a notice linking each story back to the parent episode post.")
    saved_link_parent = str(self.settings.value("wp_link_parent_episode", "true")).lower() in ("true", "1", "yes")
    self.wp_cb_link_parent.setChecked(saved_link_parent)
    crosslink_layout.addWidget(self.wp_cb_link_parent)

    parent_pos_row = QHBoxLayout()
    self.wp_parent_pos_group = QButtonGroup(self)
    self.wp_rad_parent_top = QRadioButton("Place at top of story post")
    self.wp_rad_parent_bottom = QRadioButton("Place at bottom of story post")
    self.wp_parent_pos_group.addButton(self.wp_rad_parent_top)
    self.wp_parent_pos_group.addButton(self.wp_rad_parent_bottom)
    saved_parent_pos = str(self.settings.value("wp_parent_episode_pos", "bottom") or "bottom").lower()
    if saved_parent_pos == "top":
        self.wp_rad_parent_top.setChecked(True)
    else:
        self.wp_rad_parent_bottom.setChecked(True)
    parent_pos_row.addWidget(self.wp_rad_parent_top)
    parent_pos_row.addWidget(self.wp_rad_parent_bottom)
    parent_pos_row.addStretch()
    crosslink_layout.addLayout(parent_pos_row)

    template_row = QHBoxLayout()
    template_row.addWidget(QLabel("Notice Text:"))
    self.wp_parent_template_edit = QLineEdit()
    self.wp_parent_template_edit.setPlaceholderText("This story was broadcast as part of {episode_link}.")
    saved_template = str(self.settings.value("wp_parent_template", "This story was broadcast as part of {episode_link}.") or "")
    self.wp_parent_template_edit.setText(saved_template)
    template_row.addWidget(self.wp_parent_template_edit)
    crosslink_layout.addLayout(template_row)

    self.wp_cb_update_parent_toc = QCheckBox("Append story index (Table of Contents) with links to Full Episode post")
    self.wp_cb_update_parent_toc.setToolTip("Once all individual stories are published, automatically updates the Full Episode post with a linked table of contents of all stories.")
    saved_update_toc = str(self.settings.value("wp_update_parent_toc", "true")).lower() in ("true", "1", "yes")
    self.wp_cb_update_parent_toc.setChecked(saved_update_toc)
    crosslink_layout.addWidget(self.wp_cb_update_parent_toc)

    self.wp_crosslink_section.add_layout(crosslink_layout)
    wp_layout.addWidget(self.wp_crosslink_section)

    # Audio & Media Attachments Section
    self.wp_media_section = CollapsibleSection("Audio & Media Attachments", self, is_expanded=True)
    media_section_layout = QVBoxLayout()
    media_section_layout.setContentsMargins(4, 4, 4, 4)
    media_section_layout.setSpacing(6)

    self.wp_cb_include_audio = QCheckBox("Include audio files in WordPress export (upload audio and embed player)")
    self.wp_cb_include_audio.setToolTip(
        "When enabled, uploads audio recordings to the WordPress Media Library and embeds an audio player in each post. "
        "When disabled, exports only transcript text (and featured images, when selected), omitting audio file uploads."
    )
    saved_inc_audio = str(self.settings.value("wp_include_audio", "true")).lower() in ("true", "1", "yes")
    self.wp_cb_include_audio.setChecked(saved_inc_audio)
    self.wp_cb_include_audio.toggled.connect(self._on_wp_include_audio_toggled)
    media_section_layout.addWidget(self.wp_cb_include_audio)

    self.wp_cb_apply_fades = QCheckBox("Apply audio fades to story clips (fade-in & fade-out)")
    self.wp_cb_apply_fades.setToolTip(
        "When enabled, renders volume fade-in and fade-out ramps into new MP3 files before uploading them to WordPress. "
        "When disabled, exports story clips without fade envelope modifications."
    )
    saved_apply_fades = str(self.settings.value("wp_apply_audio_fades", "true")).lower() in ("true", "1", "yes")
    self.wp_cb_apply_fades.setChecked(saved_apply_fades)
    self.wp_cb_apply_fades.toggled.connect(lambda chk: self.settings.setValue("wp_apply_audio_fades", chk))
    self.wp_cb_include_audio.toggled.connect(self.wp_cb_apply_fades.setEnabled)
    self.wp_cb_apply_fades.setEnabled(self.wp_cb_include_audio.isChecked())
    media_section_layout.addWidget(self.wp_cb_apply_fades)

    self.wp_media_section.add_layout(media_section_layout)
    wp_layout.addWidget(self.wp_media_section)

    if getattr(self, "metadata_editor_mode", False):
        self.wp_lang_section.setVisible(False)
        self.wp_custom_section.setVisible(False)
        self.wp_crosslink_section.setVisible(False)
        self.wp_media_section.setVisible(False)

    # Connection status footer
    wp_conn_layout = QHBoxLayout()
    self.wp_conn_status = QLabel("WordPress: Checking connection...")
    self.wp_conn_status.setStyleSheet("color: #94a3b8; font-size: 11px;")
    self.wp_settings_btn = QPushButton("WordPress Settings...")
    self.wp_settings_btn.clicked.connect(self._open_wp_settings)
    wp_conn_layout.addWidget(self.wp_conn_status)
    wp_conn_layout.addStretch()
    wp_conn_layout.addWidget(self.wp_settings_btn)
    wp_layout.addLayout(wp_conn_layout)

    self._update_wp_conn_status()
    wp_layout.addStretch()

    wp_scroll.setWidget(wp_scroll_content)
    wp_page_layout.addWidget(wp_scroll)
