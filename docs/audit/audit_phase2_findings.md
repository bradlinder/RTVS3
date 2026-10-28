# Phase 2 Code Audit Findings & Actionable Checklist
**Focus Subsystems:** Update Manager (`updater.py`), Isolated Runtime Provisioning (`runtime_manager.py`), Packaging & Installer Build (`build_installer.py`), and Inno Setup Script (`installer/Windows/RadioTVStorySegmenter.iss`).
**App Baseline:** v3.9.45-beta

---

## Executive Summary

Phase 2 audit uncovered **10 verified findings** across update distribution, subprocess execution, certificate verification, and installer scripts:
- **2 Critical Findings**: Silent execution of unverified installer binaries when releases lack explicit checksum files, and hard immediate process kill (`os._exit(0)`) discarding unsaved user project data upon updating.
- **2 High Findings**: Complete masking of network offline state and GitHub API rate limits as "Up to Date" due to an obsolete mock fallback release, and guaranteed failure of the primary Python detached update helper on frozen end-user Windows setups.
- **4 Medium Findings**: Tar extraction lacking `filter='data'` (symlink traversal exposure), fallback to unverified SSL contexts in runtime manager downloads, dangerous Inno Setup whole-directory uninstaller cleanup, and permanent accumulation of PowerShell supervisor scripts in AppData.
- **2 Low / Hygiene Findings**: Hardcoded `v2.9.6` fallback asset strings, and monolithic file size violations in all three core Phase 2 files (>1,000 lines).

---

## Actionable Fix Checklist

### Critical Severity

- [ ] **P2-01 [CRITICAL] Silent Execution of Unverified Binaries When Release Lacks Checksum Asset**
  - **Lens:** L3 (Vulnerabilities) / L8 (Data Integrity)
  - **Location:** [`updater.py:840-846`](file:///d:/rtvs3/updater.py#L840-L846)
  - **Evidence:**
    ```python
    expected_sha256 = _find_release_checksum(self.release_info, self.file_name)
    if expected_sha256:
        actual = hasher.hexdigest().lower()
        if actual != expected_sha256.lower():
            temp_dest.unlink(missing_ok=True)
            self.error.emit("Downloaded file failed SHA-256 verification and was discarded.")
            return

    shutil.move(str(temp_dest), str(destination))
    cleanup_old_installers(max_to_keep=2)
    self.finished.emit(str(destination))
    ```
  - **Impact / Repro:** `_find_release_checksum()` returns `None` if the GitHub release does not explicitly include a `.sha256` or `sha256sums.txt` asset. When `expected_sha256` is `None`, the entire SHA-256 verification block is silently skipped. The downloaded binary is finalized and passed directly to `launch_and_install()` with zero cryptographic validation.
  - **Suggested Fix:** If `expected_sha256` is missing, display an explicit warning prompt asking the user to confirm installation of an unverified package, or require release packages to supply SHA-256 digests.
  - **Effort:** Small (S)

- [ ] **P2-02 [CRITICAL] `_install_and_restart()` Hard Exits (`os._exit(0)`) Discarding Unsaved Project Edits**
  - **Lens:** L1 (Bug) / L8 (Data Integrity)
  - **Location:** [`updater.py:1335-1364`](file:///d:/rtvs3/updater.py#L1335-L1364)
  - **Evidence:**
    ```python
    success = launch_and_install(self.downloaded_path, parent=self)
    if success:
        self.accept()
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                if hasattr(widget, "hide"):
                    widget.hide()
            ...
            def _force_exit_watcher():
                time.sleep(0.8)
                os._exit(0)

            threading.Thread(target=_force_exit_watcher, daemon=True).start()
            app.quit()
    ```
  - **Impact / Repro:** If a user has hours of unsaved work in the main window (`project_dirty == True`) and clicks "Restart & Install Update", `_install_and_restart()` immediately hides all windows and starts an 0.8s timer calling `os._exit(0)`. No `close_project(prompt=True)` or unsaved changes confirmation is ever triggered.
  - **Suggested Fix:** Before calling `launch_and_install()`, inspect parent/main window dirty state via `parent.close_project(prompt=True)` or prompt the user: "You have unsaved changes in your current project. Save before restarting?". If rejected, cancel the restart.
  - **Effort:** Small (S)

---

### High Severity

- [ ] **P2-03 [HIGH] Offline and Rate-Limited Update Checks Masked as "Up to Date" by Hardcoded Fallback**
  - **Lens:** L1 (Bug) / L7 (Silent Error Handling) / L5 (Confusing UI)
  - **Location:** [`updater.py:354-374`](file:///d:/rtvs3/updater.py#L354-L374) and [`updater.py:688-707`](file:///d:/rtvs3/updater.py#L688-L707)
  - **Evidence:**
    In `fetch_releases()`:
    ```python
    except Exception:
        pass

    target_repo = repo or DEFAULT_GITHUB_REPO
    return [
        {
            "tag_name": "v3.4.17",
            "name": "Radio & TV Segmenter v3.4.17",
            ...
        }
    ]
    ```
  - **Impact / Repro:** If the network is disconnected, DNS fails, or GitHub API returns HTTP 403 (rate limited), `fetch_releases()` catches the exception and returns `v3.4.17`. In `CheckUpdateWorker.run()`, `is_version_newer("v3.4.17", "3.9.45-beta")` is `False`. The worker emits `up_to_date` and displays: *"You are running the latest version!"*. The user is misled into believing they have the newest release when the network check actually failed. The HTTP 404/403/URLError handlers in `CheckUpdateWorker` are unreachable dead code.
  - **Suggested Fix:** Remove the hardcoded `v3.4.17` fallback. Let `fetch_releases()` raise or return an error object so `CheckUpdateWorker` can display genuine connection/rate-limit error messages.
  - **Effort:** Small (S)

- [ ] **P2-04 [HIGH] Primary Python Detached Update Helper Always Fails on Frozen Windows Installs**
  - **Lens:** L1 (Bug) / L4 (Performance)
  - **Location:** [`updater.py:512-513`](file:///d:/rtvs3/updater.py#L512-L513)
  - **Evidence:**
    ```python
    py_exe = sys.executable if getattr(sys, "frozen", False) is False else shutil.which("pythonw") or shutil.which("python")
    if py_exe and Path(py_exe).is_file():
        subprocess.Popen([str(py_exe), str(temp_helper_py)], ...)
    ```
  - **Impact / Repro:** For users running the installed packaged application, `sys.frozen` is `True`. End users rarely have a system Python in their `PATH`. As a result, `py_exe` evaluates to `None`, the Python helper always fails, and it triggers an avoidable exception and log warning before falling back to PowerShell.
  - **Suggested Fix:** Recognize that frozen builds lack an external Python interpreter; either package a lightweight bootstrap or invoke PowerShell directly as the primary detached mechanism on frozen Windows systems without throwing a failed Python spawn attempt.
  - **Effort:** Small (S)

---

### Medium Severity

- [ ] **P2-05 [MEDIUM] `safe_extract_tar` Lacks Python `filter='data'` Symlink Traversal Protection**
  - **Lens:** L3 (Vulnerabilities)
  - **Location:** [`core_utils.py:338-344`](file:///d:/rtvs3/core_utils.py#L338-L344) and [`runtime_manager.py:616`](file:///d:/rtvs3/runtime_manager.py#L616)
  - **Evidence:**
    ```python
    def _verify_and_extract(tf):
        for member in tf.getmembers():
            normalized = Path(os.path.abspath(os.path.join(dest_path, member.name)))
            try:
                normalized.relative_to(dest_path)
            except ValueError:
                raise PermissionError(f"Attempted path traversal in TAR member: {member.name}")
        tf.extractall(dest_path)
    ```
  - **Impact / Repro:** `normalized.relative_to(dest_path)` checks member names, but does not prevent tar symlinks from pointing outside `dest_path`. If an archive contains a symlink pointing to an arbitrary system path, subsequent files in the tarball can write through that symlink.
  - **Suggested Fix:** In Python 3.12+, pass `filter='data'` to `tf.extractall(dest_path)`. For older versions, explicitly reject members where `member.issym()` or `member.islnk()` points outside `dest_path`.
  - **Effort:** Small (S)

- [ ] **P2-06 [MEDIUM] Silent Fallback to Unverified SSL Context in `_robust_urlretrieve`**
  - **Lens:** L3 (Vulnerabilities)
  - **Location:** [`runtime_manager.py:96-101`](file:///d:/rtvs3/runtime_manager.py#L96-L101)
  - **Evidence:**
    ```python
    if ssl_ctx is None:
        try:
            ssl_ctx = ssl.create_default_context()
        except Exception:
            ssl_ctx = ssl._create_unverified_context()
    ```
  - **Impact / Repro:** If system certificate store lookup fails, `_robust_urlretrieve()` silently disables all TLS certificate verification via `_create_unverified_context()`, allowing man-in-the-middle attacks during runtime manager binary downloads.
  - **Suggested Fix:** Do not fall back to unverified contexts. Fail with an explicit error asking the user to update their root certificates or install `certifi`.
  - **Effort:** Small (S)

- [ ] **P2-07 [MEDIUM] Inno Setup `[UninstallDelete]` Recursive `{app}` Wipe**
  - **Lens:** L8 (Data Integrity) / L3 (Vulnerabilities)
  - **Location:** [`installer/Windows/RadioTVStorySegmenter.iss:67`](file:///d:/rtvs3/installer/Windows/RadioTVStorySegmenter.iss#L67)
  - **Evidence:**
    ```iss
    [UninstallDelete]
    Type: filesandordirs; Name: "{app}"
    ```
  - **Impact / Repro:** If a user installs the application into a non-isolated directory (such as `D:\` or an existing media tools folder), running the uninstaller will recursively delete the entire directory and all unrelated user files in that folder.
  - **Suggested Fix:** Remove `Type: filesandordirs; Name: "{app}"` and let Inno Setup uninstall only the files and directories that were registered during installation, or enforce that `{app}` cannot be the root of a drive or standard user folder.
  - **Effort:** Small (S)

- [ ] **P2-08 [MEDIUM] Orphaned PowerShell Supervisor Scripts in AppData**
  - **Lens:** L9 (Resource Leaks)
  - **Location:** [`updater.py:544-545`](file:///d:/rtvs3/updater.py#L544-L545)
  - **Evidence:**
    ```python
    temp_helper_ps = get_app_data_dir() / "rtvs_update_supervisor.ps1"
    temp_helper_ps.write_text(supervisor_ps, encoding="utf-8")
    ```
  - **Impact / Repro:** Unlike `rtvs_update_helper.py` which cleans itself up upon exit, `rtvs_update_supervisor.ps1` is never deleted after running.
  - **Suggested Fix:** Add `Remove-Item -Path $PSCommandPath -Force` to the end of the PowerShell supervisor script.
  - **Effort:** Small (S)

---

### Low / Hygiene Severity

- [ ] **P2-09 [LOW] Hardcoded Ancient Version String (`v2.9.6`) in Asset Fallback**
  - **Lens:** L6 (Outdated Docs / Code)
  - **Location:** [`updater.py:291`](file:///d:/rtvs3/updater.py#L291)
  - **Evidence:** `tag = target_version.strip() if target_version else "v2.9.6"`
  - **Impact:** Misleading fallback; current codebase is at `v3.9.45-beta`.
  - **Suggested Fix:** Update fallback to dynamically reference `PROJECT_VERSION`.
  - **Effort:** Small (S)

- [ ] **P2-10 [LOW] Monolithic File Size Threshold Exceeded in All Phase 2 Modules**
  - **Lens:** Section 10 Directive (Modular Architecture)
  - **Location:** `updater.py` (1,418 lines), `build_installer.py` (1,077 lines), `runtime_manager.py` (1,037 lines)
  - **Impact:** All three core Phase 2 files exceed the mandatory 1,000-line ceiling, increasing maintenance friction and token consumption.
  - **Suggested Fix:** Decompose `updater.py` into `updater/client.py`, `updater/dialog.py`, and `updater/launcher.py` via lightweight facade re-exports in Phase 7.
  - **Effort:** Medium (M)

---

## Verified Robust / Architectural Highlights

1. **Host Header and Scheme Validation (`_is_trusted_download_url`)**:
   Strictly validates that update download URLs use `https://` and originate exclusively from `github.com` or `*.githubusercontent.com`.
2. **Subprocess Execution Safety**:
   All subprocess calls in `runtime_manager.py` and `updater.py` use list-based argument vectors (`shell=False`) and pass `CREATE_NO_WINDOW` on Windows to eliminate console flashing and command injection.
3. **Detached Process Elevation (`ShellExecuteW` with `runas`)**:
   Properly detaches elevated UAC execution from parent job objects, preventing Inno Setup installers from being killed prematurely when the parent Qt app terminates.

---

## Proposed Point Release Packaging Plan

- **Release C (`v3.9.48-beta` — Updater & Installer Security)**:
  - Fix **P2-01**: Mandatory checksum validation or explicit warning for unverified release downloads.
  - Fix **P2-02**: Safeguard unsaved project work before update restart in `_install_and_restart()`.
  - Fix **P2-03**: Eliminate hardcoded `v3.4.17` fallback to allow true connection/rate-limit error display.
  - Fix **P2-04**: Direct PowerShell handoff on frozen Windows builds.
  - Fix **P2-05**: Add `filter='data'` to `safe_extract_tar` to block symlink-based traversal.
  - Fix **P2-06**: Disallow unverified SSL contexts in `_robust_urlretrieve`.
  - Fix **P2-07**: Remove whole-directory `{app}` deletion from Inno Setup script.
  - Fix **P2-08**: Self-deleting PowerShell update supervisor script.
  - Fix **P2-09**: Update fallback version string to dynamic `PROJECT_VERSION`.
