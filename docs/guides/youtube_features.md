# YouTube Features & Chapter Generation Guide

This guide explains how to use RTVS3's YouTube features: generating video chapters for YouTube video descriptions, configuring the YouTube upload plugin, and embedding timestamped video clips into WordPress articles.

---

## 1. Generating YouTube Chapter Lists

YouTube automatically divides videos into chapters along the video player scrub bar when timestamps are included in the video description. RTVS3 converts your segmented stories directly into YouTube-formatted chapters with one click.

### Requirements for YouTube Video Chapters:
- The first chapter must begin at `00:00` (or `0:00`).
- You must have at least 3 timestamps listed in ascending order.
- Each chapter must be at least 10 seconds long.

RTVS3 guarantees all three rules are satisfied automatically.

### How to Generate & Copy Chapters:
1. Open your episode in RTVS3 and ensure stories have been detected or created.
2. Go to **File > Unified Export...** (or press **Ctrl+E**).
3. Select **YouTube Chapters** (or text export options).
4. Review the formatted preview:
   ```text
   00:00 - Introduction & Cold Open
   02:25 - Deep Dive: Renewable Energy Grid Tech
   07:40 - Battery Chemistry Breakdown
   10:15 - Audience Q&A and Credits
   ```
5. Click **Copy to Clipboard**.
6. Open your video in **YouTube Studio** (`studio.youtube.com`), navigate to the **Details** tab, and paste the chapters directly into the **Description** box.
7. Click **Save**. YouTube will automatically draw chapter markers on your video.

---

## 2. Embedding YouTube Video Segments in WordPress

When publishing articles about individual segments of a show, you can embed the main YouTube video so that it starts and stops at the exact moment of each story:

1. In RTVS3, open **File > Unified Export...** and select **WordPress**.
2. Select a story in the post list, then click the **Media** tab.
3. In the **YouTube Video Link** field, paste your YouTube video URL:
   - Supports standard watch URLs (`https://www.youtube.com/watch?v=...`)
   - Short links (`https://youtu.be/...`)
   - YouTube Studio edit URLs (`https://studio.youtube.com/video/.../edit`)
   - Live stream and Shorts links
4. Check **Stop Video at Story End**:
   - When checked, the embedded player automatically pauses playback when the segment concludes.
5. Choose **Embed Placement**:
   - **Top**: Places the video player above the transcript.
   - **Bottom**: Places the video player below the transcript.
6. When exported to WordPress, RTVS3 generates a responsive 16:9 Gutenberg player that works smoothly on mobile devices and bypasses server-side oEmbed issues on scheduled or unlisted videos.

---

## 3. Direct YouTube Video Upload Plugin

If you have the **YouTube Publisher** plugin enabled:
1. Configure your Google OAuth credentials in **Settings > Preferences... > YouTube Publisher**.
2. Go to **File > Unified Export...** and select **YouTube Upload**.
3. Set your video title, description, category, privacy status (*Public*, *Unlisted*, or *Private*), and thumbnail.
4. RTVS3 uploads your video directly to your YouTube channel with chapters pre-populated in the description.
