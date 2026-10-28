# Phase 5 Code Audit Findings & Actionable Checklist
**Focus Subsystems:** WordPress Plugin (`plugins/wordpress/*`), YouTube Plugin (`plugins/youtube/*`), Translation Plugin Isolation (`plugins/translation/*`), and Plugin Lifecycle Manager (`plugins/manager.py`, `plugins/installer_workers.py`).
**App Baseline:** v3.9.45-beta

---

## Executive Summary

Phase 5 audit inspected plugin boundaries, credential security, external REST API integrations, and plugin installer safety:
- **2 Critical Findings**: Unconditional top-level import of the WordPress plugin in core [`story_metadata_dialog.py`](file:///d:/rtvs3/story_metadata_dialog.py#L41) (crashing Story Settings if the plugin is deleted or disabled), and cross-domain credential leakage in the WordPress client's manual HTTP redirect loop.
- **3 High Findings**: Systemic architectural invariant violations with core modules importing directly from `plugins/`, plain text password storage in Windows Registry/QSettings when keyring and cipher fallbacks fail, and missing URL/scheme validation in the plugin download worker.
- **2 Medium Findings**: Deeply nested silent `except Exception: pass` blocks in `create_post()` quietly dropping author assignments and audio attachments, and extreme monolithic file bloat in `plugins/wordpress/client.py` (1,867 lines — the largest file in the entire repository).
- **1 Low / Hygiene Finding**: Unbuffered `data=f` streaming during raw media uploads without retry support.

---

## Actionable Fix Checklist

### Critical Severity

- [ ] **P5-01 [CRITICAL] Unconditional Core Import of WordPress Plugin Crashes `StoryMetadataDialog`**
  - **Lens:** Architectural Invariants / L1 (Bug)
  - **Location:** [`story_metadata_dialog.py:41`](file:///d:/rtvs3/story_metadata_dialog.py#L41)
  - **Evidence:**
    ```python
    from plugins.wordpress.wp_tab_widget import WordPressExportTabWidget
    ```
  - **Impact / Repro:** `story_metadata_dialog.py` is the core dialog opened when clicking "Story Settings" / "Pop Out" in the main window's Stories sidebar. It imports directly from `plugins.wordpress` at module top level without a `try ... except ImportError:` guard. If the WordPress plugin is deleted, uninstalled, or missing, opening Story Settings immediately crashes the entire application with `ModuleNotFoundError`.
  - **Suggested Fix:** Protect the import with a fallback mock or dynamic plugin lookup:
    ```python
    try:
        from plugins.wordpress.wp_tab_widget import WordPressExportTabWidget
    except ImportError:
        WordPressExportTabWidget = None
    ```
  - **Effort:** Small (S)

- [ ] **P5-02 [CRITICAL] Cross-Domain Credential Leakage in WordPress Manual HTTP Redirects**
  - **Lens:** L3 (Vulnerabilities) / Credential Hygiene
  - **Location:** [`plugins/wordpress/client.py:401-410`](file:///d:/rtvs3/plugins/wordpress/client.py#L401-L410), [`plugins/wordpress/client.py:431-436`](file:///d:/rtvs3/plugins/wordpress/client.py#L431-L436), and [`plugins/wordpress/client.py:456-461`](file:///d:/rtvs3/plugins/wordpress/client.py#L456-L461)
  - **Evidence:**
    ```python
    resp = requests.post(
        current_url,
        auth=self._get_auth(),
        json=json_data,
        ...
        allow_redirects=False,
    )
    if resp.status_code in (301, 302, 303, 307, 308) and "Location" in resp.headers:
        next_url = resp.headers["Location"]
        if not next_url.startswith(("http://", "https://")):
            next_url = urllib.parse.urljoin(current_url, next_url)
        current_url = next_url
        continue
    ```
  - **Impact / Repro:** To preserve the POST method during redirects, the WordPress client executes a manual redirect loop with `allow_redirects=False` and re-passes `auth=self._get_auth()`. However, it does **not** check whether `next_url` is on the same hostname as the original WordPress site. Normally, `requests` strips HTTP Basic Auth when redirecting cross-domain for security; this manual loop bypasses that protection and sends the username and Application Password in plaintext `Authorization: Basic ...` headers to arbitrary redirect destinations.
  - **Suggested Fix:** Verify `urllib.parse.urlparse(next_url).netloc == urllib.parse.urlparse(self.site_url).netloc` and ensure HTTPS is preserved before forwarding authentication headers.
  - **Effort:** Small (S)

---

### High Severity

- [ ] **P5-03 [HIGH] Core Modules Violating Architectural Invariant by Importing `plugins/`**
  - **Lens:** Architectural Invariants (Rule 4 of `AGENTS.md`)
  - **Location:** [`export/dialog.py:51`](file:///d:/rtvs3/export/dialog.py#L51), [`model_management.py:32`](file:///d:/rtvs3/model_management.py#L32), [`playback_preferences.py:93`](file:///d:/rtvs3/playback_preferences.py#L93), [`translation.py:24`](file:///d:/rtvs3/translation.py#L24), [`ui_dialog_launchers.py:297`](file:///d:/rtvs3/ui_dialog_launchers.py#L297), and [`preferences_tabs.py:358`](file:///d:/rtvs3/preferences_tabs.py#L358)
  - **Evidence:**
    `ARCHITECTURE.md` defines as an invariant: *"Core modules must NEVER import from plugins/."*
    Yet multiple core modules import directly from `plugins.base`, `plugins.translation.worker`, and `plugins.youtube.plugin`.
  - **Impact:** Tight coupling prevents core software from running as a clean standalone package if plugins are removed or modularized into separate distributions.
  - **Suggested Fix:** Move plugin base classes (`BasePlugin`, `PluginManifest`, `ExportDestination`) into a core module (e.g. `plugin_base.py` or `core_plugins.py`) and access plugin functionality exclusively through `PluginManager`.
  - **Effort:** Medium (M)

- [ ] **P5-04 [HIGH] Unencrypted Plaintext Password Storage in QSettings / Windows Registry**
  - **Lens:** L3 (Vulnerabilities) / Credential Hygiene
  - **Location:** [`plugins/wordpress/client.py:128-132`](file:///d:/rtvs3/plugins/wordpress/client.py#L128-L132)
  - **Evidence:**
    ```python
    if not saved_in_keyring:
        cipher = _get_wp_fallback_cipher()
        if cipher is not None:
            ...
        else:
            settings.setValue(f"wp_pass_{username}", password)
            settings.setValue(f"wp_pass_{username}_enc", False)
    ```
  - **Impact:** If system keyring is not configured and `cryptography` is unavailable, `_set_wp_password` writes the raw WordPress password directly into QSettings in cleartext, where it can be read by any local user from the Registry (`HKCU\Software\RadioTVStorySegmenter`).
  - **Suggested Fix:** Warn the user and refuse to save the password in cleartext if both keyring and local cipher encryption fail, or prompt on each session rather than storing plaintext in registry.
  - **Effort:** Small (S)

- [ ] **P5-05 [HIGH] Unvalidated URLs in Plugin Download Worker (`GitHubDownloadWorker`)**
  - **Lens:** L3 (Vulnerabilities)
  - **Location:** [`plugins/installer_workers.py:140-146`](file:///d:/rtvs3/plugins/installer_workers.py#L140-L146)
  - **Evidence:**
    ```python
    req = urllib.request.Request(self.download_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
    ```
  - **Impact:** Unlike `updater.py`, which rigorously restricts downloads to trusted GitHub domains via `_is_trusted_download_url()`, `GitHubDownloadWorker` performs no scheme or domain validation, allowing arbitrary remote package URLs to be downloaded and unzipped into the user plugins directory.
  - **Suggested Fix:** Restrict `self.download_url` to HTTPS and trusted GitHub repository URLs using `_is_trusted_download_url()`.
  - **Effort:** Small (S)

---

### Medium Severity

- [ ] **P5-06 [MEDIUM] Silent Swallowing of Author & Media Attachment Errors in `create_post()`**
  - **Lens:** L7 (Silent Error Handling) / L1 (Bug)
  - **Location:** [`plugins/wordpress/client.py:764, 771, 786, 792, 814, 825, 831`](file:///d:/rtvs3/plugins/wordpress/client.py#L764)
  - **Evidence:**
    ```python
    try:
        self.update_post(created_id, **update_payload)
    except Exception:
        pass
    ...
    try:
        self._post_request(f"{self.api_base}/media/{att_id}", json_data={"post": created_id}, timeout=10)
    except Exception:
        pass
    ```
  - **Impact:** If assigning author taxonomies (`ppma_author`) or attaching uploaded audio fails on WordPress, the errors are silently swallowed with `pass`. The user is shown a success message, but the published post lacks authors and audio attachments.
  - **Suggested Fix:** Log warnings when secondary metadata updates fail, and include partial failure warnings in the upload completion summary dialog.
  - **Effort:** Small (S)

- [ ] **P5-07 [MEDIUM] Monolithic 1,867-Line File Size: `plugins/wordpress/client.py`**
  - **Lens:** Section 10 Directive (Monolithic File Size Discipline)
  - **Location:** [`plugins/wordpress/client.py`](file:///d:/rtvs3/plugins/wordpress/client.py)
  - **Evidence:** At 1,867 lines, `client.py` is the largest file in the entire repository, violating the 1,000-line mandatory ceiling by 867 lines. It bundles the REST API client, keyring management, preferences UI, HTML rich text conversion, and the 525-line `execute_wordpress_upload` function (with 35 parameters).
  - **Suggested Fix:** Decompose in Phase 7 into `wp_client.py` (API), `wp_auth.py` (keyring/credentials), `wp_uploader.py` (upload execution), and `wp_preferences.py` (preferences UI).
  - **Effort:** Medium (M)

---

### Low / Hygiene Severity

- [ ] **P5-08 [LOW] Unbuffered `data=f` Raw Upload Stream in `upload_media()`**
  - **Lens:** L4 (Performance / Network Resilience)
  - **Location:** [`plugins/wordpress/client.py:648-654`](file:///d:/rtvs3/plugins/wordpress/client.py#L648-L654)
  - **Evidence:** Streams open file object `f` over raw HTTP POST without chunked encoding or reconnect handling.
  - **Suggested Fix:** Wrap in chunked generator with connection timeout safeguards.
  - **Effort:** Small (S)

---

## Verified Robust / Architectural Highlights

1. **Zero-Auth Assisted YouTube Publishing Architecture**:
   `plugins/youtube/export_destination.py` completely eliminates OAuth token storage and YouTube API credentials by generating standardized video, thumbnail, chapters, and description files and launching the assisted manual upload guide dialog.
2. **Safe Zip Extraction in Plugin Installation (`safe_extract_zip`)**:
   `plugins/manager.py` verifies all member filenames against destination paths (`normalized.relative_to(dest_path)`) before unpacking `.rtvs-addon` archives, preventing Zip Slip path traversal vulnerabilities.
3. **Fernet Host-Salted Password Obfuscation**:
   When keyring is unavailable, `_get_wp_fallback_cipher()` generates a machine-specific Fernet key derived from `platform.node()` and the internal app ID, preventing settings files from being copied and decrypted on another workstation.

---

## Proposed Point Release Packaging Plan

- **Release F (`v3.9.51-beta` — Plugin Security & Boundary Integrity)**:
  - Fix **P5-01**: Protect `StoryMetadataDialog` from crashing when WordPress plugin is absent.
  - Fix **P5-02**: Enforce same-domain checks and HTTPS in WordPress client manual redirect loop.
  - Fix **P5-03**: Relocate `ExportDestination` and plugin interfaces out of `plugins/` into a core interface module.
  - Fix **P5-04**: Disallow unencrypted cleartext password writes in `_set_wp_password()`.
  - Fix **P5-05**: Validate scheme and domain in `GitHubDownloadWorker`.
  - Fix **P5-06**: Report partial metadata update failures during WordPress post creation.
