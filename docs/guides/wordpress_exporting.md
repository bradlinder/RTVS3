# WordPress Exporting & Setup Guide

This guide details how to configure RTVS3 to publish story drafts, podcast enclosures, and YouTube embeds directly to your WordPress website.

---

## 1. Creating a WordPress Application Password

To communicate securely with your WordPress site without sharing your master account password, RTVS3 uses standard **WordPress Application Passwords**.

### Step-by-Step in WordPress:
1. Log in to your WordPress admin dashboard (e.g., `https://yoursite.com/wp-admin`).
2. Navigate to **Users > Profile** (or click your name in the top right corner).
3. Scroll down to the **Application Passwords** section.
4. In the **New Application Password Name** field, type a label such as `RTVS3 Desktop` or `Story Segmenter`.
5. Click **Add New Application Password**.
6. WordPress will display a 24-character generated password formatted with spaces (e.g., `abcd efgh ijkl mnop qrst uvwx`).
7. **Copy this password immediately** (WordPress only displays it once).

> **Tip:** Application Passwords can be revoked at any time from your WordPress profile without changing your primary WordPress login password.

---

## 2. Entering Credentials in RTVS3

You can save your WordPress credentials in preferences so you only need to enter them once:

1. In RTVS3, go to **Settings > Preferences...** (or press **Ctrl+P** / **Cmd+P** on macOS).
2. Click the **WordPress** tab on the left.

![WordPress Preferences Credentials](../images/wordpress_preferences_credentials.png)

3. Fill in your details:
   - **Site URL**: The full web address of your WordPress homepage (e.g., `https://example-news-station.com`). Both `https://` and trailing slash variations are handled automatically.
   - **Username**: Your WordPress administrative or author username (e.g., `newsroom_editor`).
   - **App Password**: Paste the 24-character password generated in Step 1.
4. Click **Test Connection**. RTVS3 contacts your site's REST API. When successful, your site title and authenticated user permissions are confirmed.
5. Click **Save Preferences**.

---

## 3. Opening WordPress Export & Choosing a Workflow Mode

When starting a backfill project from an older episode—or after segmenting a new broadcast—you can begin in two ways:

- **Starting a Backfill Project from the File Menu (`File > Open Remote Episode > From Existing WordPress Post...`)**:
  1. Go to **File > Open Remote Episode > From Existing WordPress Post...** at the top of the File menu (also available under **File > Publishing & Plugins**). For already-uploaded YouTube video shows, choose **File > Open Remote Episode > From YouTube Video...** (**Ctrl+Alt+Y**), which also supports linking an existing WordPress post for Update Mode.
  2. Paste an existing WordPress episode URL or a direct `.mp3` URL and click **Fetch Info** to preview its Post ID, original publication date, and detected MP3 enclosure.
  3. Choose whether to **Download and load MP3 from WordPress episode / URL** (stored in the **Managed Remote Media Cache** with automatic LRU capping and 1-click project re-download) or **Use local audio file from computer** (`Browse...`), then click **Load Episode**. RTVS3 loads the audio and pre-configures your project in **Update Existing Episode & Backfill Stories** mode with the episode's original date, title, authors, categories, and preserved excerpt.
  4. After exporting to WordPress, cached remote downloads are marked as exported for LRU priority, and the completion dialog offers an optional **Free Cached Media** button if you want to reclaim disk space immediately.
- **Opening the WordPress Export Panel (`Ctrl+E` / `File > Export...`)**:
  1. Press **Ctrl+E** (or go to **File > Export...**).
  2. In the **Export Destination** bar at the top, select **WordPress Draft Post**.

![WordPress Content Tab](../images/wordpress_export_content_tab.png)

### Choosing Workflow Mode & Publication Date:
At the top of **WordPress Post Configuration**, select a **Workflow Mode**:
- **Create New Episode & Stories (Default)**: Creates new WordPress posts (defaulting to **Draft** status) for your episode and/or selected stories.
- **Update Existing Episode & Backfill Stories**: Updates an existing episode page in-place by URL without changing its permalink slug, Post ID (`<guid>`), or **Published** status; preserves its existing MP3 file and Seriously Simple Podcasting (Castos) RSS feed metadata (`Replace existing Full Episode MP3 file and Seriously Simple Podcasting metadata` unchecked by default); moves any existing page text into the WordPress **Excerpt** field (preserving podcast show notes and archive teasers); replaces the page body with the formatted transcript and linked story index; and creates backdated **Draft** posts with segmented MP3 clips for each individual story. Keep **Include audio files for new Story clips (existing Full Episode MP3 preserved)** checked on the **Media** tab so the new Story posts receive audio players without re-uploading the Full Episode MP3.

In **both modes**, use the shared scheduling & status bar:
- **Publication Date**: Enter a custom date/time (`YYYY-MM-DD` or `YYYY-MM-DD HH:MM`) to apply to the Full Episode and all Stories in the export, or leave blank to use the current date and time. In Update mode, this auto-fills with the fetched episode's original publication date.
- **Full Episode / Stories Status**: Choose `Draft` or `Published` independently for the Full Episode (defaults to **Published (Keep Live)** in Update mode) and Story posts (defaults to **Draft**). When a live Full Episode links to draft stories in its *Stories in this Episode* Table of Contents, RTVS3 automatically assigns clean story slugs and canonical `{site_url}/{slug}/` links instead of temporary `?p=` draft preview URLs.

### Choosing Export Scope:
In the **Export Scope** dropdown, choose which posts you want to generate:
- **Custom Selection**: Opens the checkable **Items to Export:** sidebar on the left (**Full Episode** at the top plus every segment, with live `(X of Y)` counts and **Select All** / **Clear** controls). Check any combination—such as the Full Episode plus a chosen subset of segments—to export them in one pass with automatic parent-episode cross-linking and a filtered Table of Contents.
- **All Segments**: Generates separate draft posts for every detected segment.
- **Full Episode**: Generates one post containing the complete episode transcript.
- **Full Episode & All Segments**: Generates one master episode post plus individual segment posts.

---

## 4. Customizing Individual Post Details Across the 4 Tabs

Under **WordPress Post Configuration**, select any post in the left-hand **Posts to Export:** list (or in the shared **Items to Export:** sidebar when **Custom Selection** is active). The divider between the post list and the editor pane is an expandable splitter that you can drag to widen the sidebar.

Configure each post across the 4 editor tabs:

### Tab 1: Post Content
- **Post Title**: The headline of the WordPress draft post.
- **Post Excerpt / Teaser**: A concise summary of the segment used for article previews, RSS feeds, and social cards. Click **Generate from Story** to automatically extract a snippet (≤55 words) from the transcript.
- **Custom Notice / Disclaimer**: An optional notice (e.g., *"This segment aired on Radio One on Nov 4"*) prepended or appended to the article.
- **Offline Spellcheck**: Title, Excerpt, and Custom Notice fields underline unrecognized words automatically; right-click any flagged word for suggestions, **Add '<word>' to Glossary**, or **Ignore (This Session)** (Glossary terms and confirmed project speakers are allowlisted).

### Tab 2: Authors & Taxonomy

![WordPress Authors & Taxonomy Tab](../images/wordpress_export_taxonomy_tab.png)

- **Authors**: Search, filter, and check registered **WordPress Users** and **PublishPress Guest Authors** to assign bylines (you can mix WordPress Users and Guest Authors cleanly on the same post). When updating an existing post, checking one or more authors overwrites the post's existing authors, whereas leaving Authors unchecked preserves the authors already assigned on WordPress.
- **Categories**: Search, filter, and assign one or more WordPress categories (e.g., *News*, *Interviews*, *Local*). When editing a segment, check **Apply to all stories (excludes Full Episode)** to copy your selected categories across every segment without altering the Full Episode's categories.
- **Tags**: Enter comma-separated tag keywords.

### Tab 3: Media

![WordPress Media Tab](../images/wordpress_export_media_tab.png)

- **Featured Image, Caption & Alt Text**: Choose **YouTube default thumbnail** (available whenever a YouTube video is attached), **Grab frame from video**, **Select custom image file...**, or **None**, and optionally set an image **Caption** and **Alt Text** (with offline spellcheck and bulk apply across posts).
  - **YouTube-Source Defaults**: When your project was imported from a YouTube video, **Full Episode** defaults to **YouTube default thumbnail** (fetched and cached locally) and individual **segments** default to **Grab frame from video** at a representative frame strictly inside each segment's time range—captured automatically during export even if you do not visit each segment's **Media** tab. Any manual override (custom image, scrubbed frame, or **None**) is preserved.
- **YouTube Video Link**: Paste a YouTube watch link, short link, or studio URL.
  - **Automatic Segment Inheritance**: YouTube-imported projects—and projects with **Apply this YouTube URL to the full episode and all stories** enabled—automatically inherit the project's YouTube video embed at each segment's start timestamp on individual segment pages (including newly detected segments) unless explicitly cleared.
  - **Context-Aware Auto-Dimming**: Controls automatically dim when the URL field is empty and illuminate as soon as a valid video link is detected.
  - **Stop Video at Story End**: When checked, the embedded player automatically pauses playback when the segment concludes.
  - **Embed Placement**: Choose whether the responsive 16:9 player appears at the **Top** (above transcript) or **Bottom** (below transcript).
- **Include Audio Files**:
  - For radio and audio projects, checking this extracts a 128 kbps MP3 cut and uploads it to the WordPress Media Library.
  - For video shows, this defaults to unchecked because the YouTube embed already provides full audio.
  - **Apply Audio Fades**: Automatically rendered on the MP3 cut if audio inclusion is enabled.
- **Podcast Enclosure**: Check this to format the audio upload with Castos or standard RSS podcast enclosures so aggregator plugins detect the episode.

### Tab 4: Publishing & Formatting

![WordPress Publishing & Formatting Tab](../images/wordpress_export_publishing_tab.png)

- **Transcript Languages**: Select your primary spoken language and choose any translated languages to append to the post draft.
- **Episode Cross-Linking**: Automatically insert hyperlinks back to the full broadcast master post or related story segments.

---

## 5. Left-Hand Post List Prefix Indicators & Tooltips

In the **Posts to Export:** list, compact prefix tags appear immediately after the story number so you can verify each post's configuration at a glance, even when the sidebar is narrow:

![WordPress Post List Badges](../images/wordpress_posts_list_badges.png)

- **`[YT]`**: A responsive YouTube embed with story timestamps is attached.
- **`[Pod]`**: Podcast RSS enclosure tags are configured.
- **`[A]`**: An MP3 audio cut will be uploaded.
- **`[Img]`**: A featured image (YouTube default thumbnail, video frame grab, or custom image file) will be uploaded.
- **Example**: `Story 1 [YT, Img]: Demonstrators push for more funding...`
- **Hover Tooltips**: Hover your mouse over any post in the list to view a multi-line tooltip detailing exact start/end timecodes, author names, and category tags.
- **Resizable Sidebar**: Drag the vertical splitter bar between the post list and the editor tabs to expand or shrink the sidebar.

---

## 6. Uploading Drafts or Updating Existing Episodes on WordPress

Click **Export to WordPress Drafts...** (or **Update Episode & Export Story Drafts...** in Update mode) at the bottom of the dialog:
- In **Create New Episode & Stories** mode, RTVS3 authenticates via the WordPress REST API and creates **Draft** posts (or uses your selected status and optional **Publication Date**) so your editorial team can review them before publishing.
- In **Update Existing Episode & Backfill Stories** mode, RTVS3 updates the existing Full Episode post in place—keeping its original URL, **Published** status, MP3 file, and Seriously Simple Podcasting feed metadata untouched while moving original page text into the **Excerpt**—and creates backdated Story drafts with their own segmented MP3 cuts and transcripts.
- When upload completes, the summary lists every created or updated Post ID, status, and link.
