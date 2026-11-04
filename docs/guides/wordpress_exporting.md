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

1. In RTVS3, go to **Settings > Preferences...** (or press **Ctrl+,**).
2. Click the **WordPress** tab on the left.

![WordPress Preferences Credentials](../images/wordpress_preferences_credentials.png)

3. Fill in your details:
   - **Site URL**: The full web address of your WordPress homepage (e.g., `https://example-news-station.com`). Both `https://` and trailing slash variations are handled automatically.
   - **Username**: Your WordPress administrative or author username (e.g., `newsroom_editor`).
   - **App Password**: Paste the 24-character password generated in Step 1.
4. Click **Test Connection**. RTVS3 contacts your site's REST API. When successful, your site title and authenticated user permissions are confirmed.
5. Click **Save Preferences**.

---

## 3. Configuring WordPress Post Drafts

When your episode has been segmented into stories, open the export dialog by pressing **Ctrl+E** (**File > Unified Export...**) and select **WordPress** on the left.

![WordPress Content Tab](../images/wordpress_export_content_tab.png)

### Choosing Export Scope:
In the top-right toolbar, choose which posts you want to generate:
- **Full Episode**: Generates one post containing the complete episode transcript.
- **All Stories**: Generates separate draft posts for every detected story.
- **Selected Stories**: Generates drafts only for the stories currently highlighted in the Stories list.
- **Full and All Stories**: Generates one master episode post plus individual story posts.

---

## 4. Customizing Individual Post Details

Select any post from the left-hand post list to customize its attributes across the 4 editor tabs:

### 1. Content Tab
- **Title**: The headline of the WordPress draft.
- **Excerpt**: A concise summary of the story used for article previews, RSS feeds, and social cards.
- **Custom Disclaimer**: An optional notice (e.g., *"This story aired on Radio One on Nov 4"*) prepended or appended to the article.

### 2. Organization Tab
- **Authors**: Assign one or more registered WordPress authors to the post.
- **Categories**: Select WordPress categories (e.g., *News*, *Interviews*, *Local*).
- **Tags**: Add comma-separated tag keywords.

### 3. Media & Images Tab
- **Featured Image**: Choose an extracted video thumbnail frame or custom image to set as the post's featured banner.

### 4. Media Tab

![WordPress Media Tab](../images/wordpress_export_media_tab.png)

- **YouTube Video Link**: Paste a YouTube watch link, short link, or studio edit link. RTVS3 calculates story start and end timestamps automatically.
- **Stop Video at Story End**: When checked, the player stops when the segment finishes.
- **Embed Placement**: Choose whether the responsive 16:9 player appears at the **Top** (above transcript) or **Bottom** (below transcript).
- **Include Audio Files**:
  - For audio radio projects, checking this extracts an MP3 cut and uploads it to the WordPress Media Library.
  - For video shows, this defaults to unchecked because the YouTube embed already provides full audio.
  - If unchecked, audio fade processing is automatically bypassed.
- **Podcast Enclosure**: Check this to format the audio upload with standard RSS podcast enclosures so podcast aggregator plugins (such as Seriously Simple Podcasting or PowerPress) detect the episode.

---

## 5. Left-Hand Post List Badges & Tooltips

As you configure posts, the left-hand list displays compact badges showing exactly what each post will contain:

![WordPress Post List Badges](../images/wordpress_posts_list_badges.png)

- **`[YouTube]`**: A responsive YouTube embed with story timestamps is enabled.
- **`[Podcast]`**: Podcast RSS enclosure tags are configured.
- **`[Audio]`**: An MP3 audio file will be uploaded.
- **`[Image]`**: A featured image or video thumbnail will be uploaded.
- Hover your mouse over any post in the list to view a multi-line tooltip detailing exact start/end seconds, author names, and categories.

---

## 6. Uploading Drafts to WordPress

Click **Export to WordPress** at the bottom of the dialog:
- RTVS3 uploads media files and creates **Draft** posts on your WordPress site.
- Posts are created in draft status so you or your editorial team can review and preview them before publishing them live to the public.
- When upload completes, a clickable link takes you directly to the WordPress post editor.
