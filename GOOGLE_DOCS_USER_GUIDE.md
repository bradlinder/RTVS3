# Google Docs & Google Drive Integration Guide

Radio & TV Story Segmenter (RTVS) allows you to export your broadcast transcripts, speaker turns, story segmentations, and editorial margin notes directly into formatted Google Docs.

---

## 1. Connecting Your Google Account

Connecting your Google account takes just one click:

1. Open **Preferences** (from the menu bar or press `Ctrl+,` / `Cmd+,`) and select **Google Docs & Drive** (or click **Export > Export to Google Docs...**).
2. Click **Connect Google Account**.
3. Your default web browser will open to Google's secure authorization page.
4. Select your Google account and review the permissions:
   - **Create and edit Google Docs**: Required to create your formatted transcripts and apply styles.
   - **Manage files created by RTVS**: Required to create documents, organize them in folders, and add editorial notes as margin comments.
5. Click **Allow** / **Continue**.
6. When the browser confirms **Authorization Successful**, close the browser tab and return to Radio & TV Story Segmenter.
7. Your account will now show as **✓ Connected**.

---

## 2. Exporting to Google Docs

When your project is ready to export:

1. Go to **File > Export > Export to Google Docs...** (or press the **Export** button in the main window).
2. Choose your export options:
   - **Document Title**: By default, RTVS names the document after your active project or media file.
   - **Language Options**: Choose between Original Language (English or Spanish), Translated Language, or both in dual-language mode.
   - **Google Drive Folder**: Export directly to the root of your Google Drive or browse to select an existing folder. You can also create a new folder directly from the dialog!
   - **Project Subfolders**: Check *Create a new subfolder for each project* to keep all exports neatly organized.
   - **Formatting Options**:
     - *Bold Speaker Labels*: Formats speakers like `JOHN DOE:` in bold.
     - *Story Chapters (Table of Contents)*: Generates H2 headings for stories so you can navigate chapters using Google Docs outline view.
     - *Timestamps*: Inserts bracketed timecodes `[00:01:23]` at paragraph breaks.
     - *Margin Comments*: Anchors editorial story notes directly into the Google Docs margin.
3. Click **Export to Google Docs**.
4. Once completed, your new document will automatically open in your web browser.

---

## 3. Disconnecting or Switching Accounts

To disconnect your Google account:
1. Open **Preferences > Google Docs & Drive** (or the Export dialog).
2. Click **Disconnect Google Account**.
3. Confirm the prompt. RTVS will clear your saved tokens locally and revoke the access grant on Google's authorization servers.

---

## 4. Privacy & Security

- **Direct Connection**: RTVS connects directly from your personal computer to Google's official APIs (`docs.googleapis.com` and `drive.googleapis.com`).
- **No Third-Party Servers**: RTVS operates entirely offline-first. There are no intermediate servers, authentication proxies, or tracking services.
- **Secure Token Storage**: Your authorization tokens are encrypted and stored in your operating system's native secure credential manager (Windows Credential Manager / macOS Keychain).
