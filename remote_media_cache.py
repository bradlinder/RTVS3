"""Headless Managed Remote Media Cache for YouTube and WordPress episode downloads.

Stores remote-downloaded media inside a dedicated cache directory with an atomic JSON
manifest, exported-first LRU size-cap eviction, active-file immunity, free-space
pre-checks, and strict path-containment guards so user-owned local files are never
modified or deleted.

Zero PySide6/Qt imports (pure Python headless engine).
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

DEFAULT_CACHE_CAP_GB: float = 10.0
CACHE_CAP_SETTING_KEY: str = "remote_media_cache_cap_gb"
CACHE_INDEX_FILENAME: str = "index.json"
MIN_DISK_HEADROOM_BYTES: int = 200 * 1024 * 1024  # 200 MB safety buffer


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso_ts(val: Optional[str]) -> float:
    if not val:
        return 0.0
    try:
        raw = str(val).strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        return datetime.fromisoformat(raw).timestamp()
    except Exception:
        return 0.0


def format_bytes_human(num_bytes: int | float) -> str:
    """Format a byte count as a readable size string (e.g. '1.42 GB', '312.5 MB')."""
    size = max(0.0, float(num_bytes or 0))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0 or unit == "TB":
            if unit == "B":
                return f"{int(round(size))} B"
            return f"{size:.2f} {unit}" if unit in ("GB", "TB") else f"{size:.1f} {unit}"
        size /= 1024.0
    return "0 B"


def _resolve_app_data_root() -> Path:
    """Resolve the writable application data directory without importing Qt."""
    try:
        from core_utils import get_app_data_dir
        return Path(get_app_data_dir())
    except Exception:
        pass
    xdg = os.environ.get("XDG_DATA_HOME") or os.environ.get("LOCALAPPDATA")
    if xdg:
        return Path(xdg) / "RadioTVStorySegmenter"
    return Path.home() / ".radio_tv_story_segmenter"


def get_remote_media_cache_dir(base_dir: Optional[Path | str] = None) -> Path:
    """Return (and create if needed) the managed remote media cache root directory."""
    if base_dir is not None:
        root = Path(base_dir).expanduser()
        root.mkdir(parents=True, exist_ok=True)
        return root.resolve()

    try:
        candidate = _resolve_app_data_root() / "remote_media_cache"
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate.resolve()
    except Exception:
        fallback = Path(tempfile.gettempdir()) / "rtvs_remote_media_cache"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback.resolve()


def is_path_inside_cache(file_path: Path | str, cache_dir: Optional[Path | str] = None) -> bool:
    """Strictly verify that ``file_path`` resides inside the managed cache directory."""
    if not file_path:
        return False
    try:
        root = get_remote_media_cache_dir(cache_dir)
        target = Path(file_path).expanduser().resolve()
        if target == root:
            return False
        common = os.path.commonpath([str(root), str(target)])
        return os.path.normcase(common) == os.path.normcase(str(root))
    except (ValueError, OSError):
        return False


def make_cache_key(provider: str, source_id: str, quality_preset: str = "") -> str:
    """Build a deterministic cache key for a remote source item."""
    prov = str(provider or "remote").strip().lower()
    sid = str(source_id or "").strip()
    qual = str(quality_preset or "").strip().lower()
    if qual:
        return f"{prov}:{sid}:{qual}"
    return f"{prov}:{sid}"


def build_remote_media_source_record(
    provider: str,
    source_url: str,
    source_id: str = "",
    quality_preset: str = "",
    cached_filename: str = "",
    cache_key: str = "",
    title: str = "",
    upload_date: str = "",
    estimated_size_bytes: int = 0,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a portable `.rtvs` `remote_media_source` metadata dictionary."""
    prov = str(provider or "").strip().lower()
    key = cache_key or make_cache_key(prov, source_id or source_url, quality_preset)
    record: Dict[str, Any] = {
        "provider": prov,
        "source_url": str(source_url or "").strip(),
        "source_id": str(source_id or "").strip(),
        "quality_preset": str(quality_preset or "").strip(),
        "cached_filename": str(cached_filename or "").strip(),
        "cache_key": key,
        "title": str(title or "").strip(),
        "upload_date": str(upload_date or "").strip(),
        "downloaded_at": _utc_now_iso(),
        "estimated_size_bytes": max(0, int(estimated_size_bytes or 0)),
    }
    if prov == "youtube" and source_id:
        record["video_id"] = str(source_id).strip()
    elif prov == "wordpress" and source_id:
        try:
            record["wp_post_id"] = int(source_id)
        except (TypeError, ValueError):
            record["wp_post_id"] = str(source_id).strip()
    if isinstance(extra, dict):
        for k, v in extra.items():
            if k not in record and v is not None:
                record[k] = v
    return record


class RemoteMediaCacheManager:
    """Manages cached YouTube and WordPress remote downloads with LRU size limits."""

    def __init__(self, cache_dir: Optional[Path | str] = None):
        self.cache_dir: Path = get_remote_media_cache_dir(cache_dir)
        self.index_path: Path = self.cache_dir / CACHE_INDEX_FILENAME
        self._entries: Dict[str, Dict[str, Any]] = {}
        self.load_index()

    def get_provider_dir(self, provider: str) -> Path:
        """Return a safe subdirectory inside the cache root for a specific provider."""
        clean = "".join(ch for ch in str(provider or "remote").lower() if ch.isalnum() or ch in ("_", "-")) or "remote"
        sub = (self.cache_dir / clean).resolve()
        if not is_path_inside_cache(sub, self.cache_dir):
            raise ValueError(f"Invalid cache provider directory: {provider}")
        sub.mkdir(parents=True, exist_ok=True)
        return sub

    def load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load and reconcile index.json against actual files on disk."""
        raw_entries: Dict[str, Dict[str, Any]] = {}
        if self.index_path.exists():
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                if isinstance(payload, dict) and isinstance(payload.get("entries"), dict):
                    raw_entries = payload["entries"]
            except Exception:
                raw_entries = {}

        reconciled: Dict[str, Dict[str, Any]] = {}
        changed = False
        for key, item in raw_entries.items():
            if not isinstance(item, dict):
                changed = True
                continue
            fp_raw = str(item.get("file_path") or "").strip()
            if not fp_raw or not is_path_inside_cache(fp_raw, self.cache_dir):
                changed = True
                continue
            fp = Path(fp_raw)
            if not fp.exists() or not fp.is_file():
                changed = True
                continue
            try:
                actual_size = fp.stat().st_size
            except OSError:
                changed = True
                continue
            entry = dict(item)
            entry["cache_key"] = str(key)
            entry["file_path"] = str(fp.resolve())
            if entry.get("size_bytes") != actual_size:
                entry["size_bytes"] = actual_size
                changed = True
            reconciled[str(key)] = entry

        self._entries = reconciled
        if changed:
            self.save_index()
        return self._entries

    def save_index(self) -> None:
        """Atomically persist index.json using temp-file + fsync + os.replace."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "updated_at": _utc_now_iso(),
            "entries": self._entries,
        }
        tmp_path = self.index_path.with_suffix(".json.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass
        os.replace(tmp_path, self.index_path)

    def _normalize_protected_set(self, protected_paths: Iterable[Path | str] = ()) -> Set[str]:
        out: Set[str] = set()
        for p in protected_paths or ():
            if not p:
                continue
            try:
                out.add(os.path.normcase(str(Path(p).expanduser().resolve())))
            except Exception:
                out.add(os.path.normcase(str(p)))
        return out

    def get_entry(self, cache_key: str) -> Optional[Dict[str, Any]]:
        self.load_index()
        item = self._entries.get(str(cache_key or ""))
        return dict(item) if item else None

    def find_entry_by_path(self, file_path: Path | str) -> Optional[Dict[str, Any]]:
        if not file_path:
            return None
        self.load_index()
        try:
            norm = os.path.normcase(str(Path(file_path).expanduser().resolve()))
        except Exception:
            norm = os.path.normcase(str(file_path))
        for item in self._entries.values():
            if os.path.normcase(str(item.get("file_path") or "")) == norm:
                return dict(item)
        return None

    def get_existing_cached_file(self, cache_key: str, touch: bool = True) -> Optional[Path]:
        """Return the existing cached Path for ``cache_key`` (instant cache-hit reuse)."""
        self.load_index()
        item = self._entries.get(str(cache_key or ""))
        if not item:
            return None
        fp = Path(item["file_path"])
        if not fp.exists() or not fp.is_file() or not is_path_inside_cache(fp, self.cache_dir):
            return None
        if touch:
            item["last_accessed_at"] = _utc_now_iso()
            self.save_index()
        return fp

    def register_download(
        self,
        cache_key: str,
        file_path: Path | str,
        provider: str,
        source_url: str,
        source_id: str = "",
        quality_preset: str = "",
        title: str = "",
        upload_date: str = "",
        project_path: str = "",
    ) -> Dict[str, Any]:
        """Register (or update) a downloaded remote file inside the managed cache."""
        resolved = Path(file_path).expanduser().resolve()
        if not is_path_inside_cache(resolved, self.cache_dir):
            raise ValueError(
                f"Refusing to register file outside managed cache directory: {resolved}"
            )
        if not resolved.exists() or not resolved.is_file():
            raise FileNotFoundError(f"Cached media file not found: {resolved}")

        self.load_index()
        now = _utc_now_iso()
        existing = self._entries.get(str(cache_key), {})
        linked = list(existing.get("linked_project_paths") or [])
        if project_path and project_path not in linked:
            linked.append(str(project_path))

        entry: Dict[str, Any] = {
            "cache_key": str(cache_key),
            "file_path": str(resolved),
            "filename": resolved.name,
            "provider": str(provider or "").strip().lower(),
            "source_url": str(source_url or "").strip(),
            "source_id": str(source_id or "").strip(),
            "quality_preset": str(quality_preset or "").strip(),
            "title": str(title or existing.get("title") or resolved.stem).strip(),
            "upload_date": str(upload_date or existing.get("upload_date") or "").strip(),
            "size_bytes": int(resolved.stat().st_size),
            "created_at": existing.get("created_at") or now,
            "last_accessed_at": now,
            "last_exported_at": existing.get("last_exported_at") or "",
            "export_targets": list(existing.get("export_targets") or []),
            "linked_project_paths": linked,
        }
        self._entries[str(cache_key)] = entry
        self.save_index()
        return dict(entry)

    def mark_accessed(self, file_path_or_key: Path | str) -> bool:
        """Refresh ``last_accessed_at`` for an entry matched by key or path."""
        self.load_index()
        key = str(file_path_or_key or "")
        entry = self._entries.get(key)
        if entry is None:
            found = self.find_entry_by_path(file_path_or_key)
            if found:
                entry = self._entries.get(found["cache_key"])
        if entry is None:
            return False
        entry["last_accessed_at"] = _utc_now_iso()
        self.save_index()
        return True

    def mark_exported(self, file_path_or_key: Path | str, export_target: str = "wordpress") -> bool:
        """Mark a cached media entry as exported so LRU eviction prefers it first."""
        self.load_index()
        key = str(file_path_or_key or "")
        entry = self._entries.get(key)
        if entry is None:
            found = self.find_entry_by_path(file_path_or_key)
            if found:
                entry = self._entries.get(found["cache_key"])
        if entry is None:
            return False
        now = _utc_now_iso()
        entry["last_exported_at"] = now
        entry["last_accessed_at"] = now
        targets = list(entry.get("export_targets") or [])
        if export_target and export_target not in targets:
            targets.append(str(export_target))
        entry["export_targets"] = targets
        self.save_index()
        return True

    def link_project(self, file_path_or_key: Path | str, project_path: Path | str) -> bool:
        """Associate a saved `.rtvs` project path with a cached media entry."""
        if not project_path:
            return False
        self.load_index()
        key = str(file_path_or_key or "")
        entry = self._entries.get(key)
        if entry is None:
            found = self.find_entry_by_path(file_path_or_key)
            if found:
                entry = self._entries.get(found["cache_key"])
        if entry is None:
            return False
        p_str = str(Path(project_path).expanduser().resolve())
        linked = list(entry.get("linked_project_paths") or [])
        if p_str not in linked:
            linked.append(p_str)
            entry["linked_project_paths"] = linked
            self.save_index()
        return True

    def list_entries(self) -> List[Dict[str, Any]]:
        """Return all cached entries sorted newest-accessed first."""
        self.load_index()
        items = [dict(v) for v in self._entries.values()]
        items.sort(key=lambda e: _parse_iso_ts(e.get("last_accessed_at")), reverse=True)
        return items

    def get_total_size_bytes(self) -> int:
        self.load_index()
        return sum(int(e.get("size_bytes") or 0) for e in self._entries.values())

    def get_stats(self, cap_gb: Optional[float] = None) -> Dict[str, Any]:
        entries = self.list_entries()
        total_bytes = sum(int(e.get("size_bytes") or 0) for e in entries)
        exported_bytes = sum(int(e.get("size_bytes") or 0) for e in entries if e.get("last_exported_at"))
        by_provider: Dict[str, Dict[str, int]] = {}
        for e in entries:
            prov = str(e.get("provider") or "other")
            bucket = by_provider.setdefault(prov, {"count": 0, "bytes": 0})
            bucket["count"] += 1
            bucket["bytes"] += int(e.get("size_bytes") or 0)
        cap_bytes = int(round(float(cap_gb) * (1024 ** 3))) if (cap_gb is not None and float(cap_gb) > 0) else 0
        return {
            "cache_dir": str(self.cache_dir),
            "count": len(entries),
            "total_bytes": total_bytes,
            "exported_bytes": exported_bytes,
            "cap_gb": float(cap_gb) if cap_gb is not None else 0.0,
            "cap_bytes": cap_bytes,
            "by_provider": by_provider,
        }

    def check_disk_space(self, estimated_bytes: int, cap_gb: Optional[float] = None) -> Dict[str, Any]:
        """Check free disk space and cache cap before starting a large download."""
        est = max(0, int(estimated_bytes or 0))
        try:
            free_bytes = int(shutil.disk_usage(self.cache_dir).free)
        except OSError:
            free_bytes = 0

        headroom = max(MIN_DISK_HEADROOM_BYTES, int(est * 0.10))
        low_disk = bool(est > 0 and free_bytes > 0 and free_bytes < (est + headroom))

        cap_bytes = int(round(float(cap_gb) * (1024 ** 3))) if (cap_gb is not None and float(cap_gb) > 0) else 0
        exceeds_cap = bool(cap_bytes > 0 and est > cap_bytes)

        warnings: List[str] = []
        if low_disk:
            warnings.append(
                f"Low disk space: this download is estimated at {format_bytes_human(est)}, "
                f"and only {format_bytes_human(free_bytes)} is free on the cache drive."
            )
        if exceeds_cap:
            warnings.append(
                f"This single download ({format_bytes_human(est)}) is larger than your current "
                f"Remote Media Cache cap ({format_bytes_human(cap_bytes)}). The active file will "
                f"not be evicted while open, but older cached files will be pruned to make room."
            )
        return {
            "estimated_bytes": est,
            "free_bytes": free_bytes,
            "cap_bytes": cap_bytes,
            "low_disk_space": low_disk,
            "exceeds_cap": exceeds_cap,
            "warnings": warnings,
        }

    def delete_entry(
        self,
        cache_key: str,
        protected_paths: Iterable[Path | str] = (),
    ) -> Tuple[bool, int, str]:
        """Safely delete a single cached file by key, respecting path-jail and active-file guards."""
        self.load_index()
        entry = self._entries.get(str(cache_key or ""))
        if not entry:
            return False, 0, "Cache entry not found."

        fp_str = str(entry.get("file_path") or "")
        if not is_path_inside_cache(fp_str, self.cache_dir):
            return False, 0, "Refused to delete path outside managed cache."

        protected = self._normalize_protected_set(protected_paths)
        norm_fp = os.path.normcase(str(Path(fp_str).expanduser().resolve()))
        if norm_fp in protected:
            return False, 0, "Cannot delete media file currently open in the active project."

        fp = Path(fp_str)
        size = int(entry.get("size_bytes") or 0)
        try:
            if fp.exists():
                size = max(size, int(fp.stat().st_size))
                fp.unlink()
        except OSError as exc:
            return False, 0, f"Could not delete cached file: {exc}"

        self._entries.pop(str(cache_key), None)
        self.save_index()
        return True, size, ""

    def enforce_size_cap(
        self,
        cap_gb: float = DEFAULT_CACHE_CAP_GB,
        protected_paths: Iterable[Path | str] = (),
    ) -> Dict[str, Any]:
        """Evict cached files when total size exceeds ``cap_gb`` (0 or negative = Unlimited).

        Eviction order:
        1. Exported entries first, oldest ``last_accessed_at`` first.
        2. Unexported entries second, oldest ``last_accessed_at`` first.
        Files in ``protected_paths`` (active open project media) are never evicted.
        """
        self.load_index()
        if cap_gb is None or float(cap_gb) <= 0:
            return {
                "deleted_count": 0,
                "freed_bytes": 0,
                "deleted_keys": [],
                "remaining_bytes": self.get_total_size_bytes(),
            }

        cap_bytes = int(round(float(cap_gb) * (1024 ** 3)))
        total_bytes = self.get_total_size_bytes()
        if total_bytes <= cap_bytes:
            return {
                "deleted_count": 0,
                "freed_bytes": 0,
                "deleted_keys": [],
                "remaining_bytes": total_bytes,
            }

        protected = self._normalize_protected_set(protected_paths)

        # Sort candidates: exported first (0), unexported second (1), then oldest last_accessed_at
        candidates = list(self._entries.values())
        candidates.sort(
            key=lambda e: (
                0 if e.get("last_exported_at") else 1,
                _parse_iso_ts(e.get("last_accessed_at")),
                _parse_iso_ts(e.get("created_at")),
            )
        )

        deleted_keys: List[str] = []
        freed_bytes = 0
        for entry in candidates:
            if total_bytes <= cap_bytes:
                break
            fp_str = str(entry.get("file_path") or "")
            if not is_path_inside_cache(fp_str, self.cache_dir):
                continue
            norm_fp = os.path.normcase(str(Path(fp_str).expanduser().resolve()))
            if norm_fp in protected:
                continue
            fp = Path(fp_str)
            sz = int(entry.get("size_bytes") or 0)
            try:
                if fp.exists():
                    sz = max(sz, int(fp.stat().st_size))
                    fp.unlink()
                self._entries.pop(entry["cache_key"], None)
                deleted_keys.append(entry["cache_key"])
                freed_bytes += sz
                total_bytes = max(0, total_bytes - sz)
            except OSError:
                continue

        if deleted_keys:
            self.save_index()
        return {
            "deleted_count": len(deleted_keys),
            "freed_bytes": freed_bytes,
            "deleted_keys": deleted_keys,
            "remaining_bytes": self.get_total_size_bytes(),
        }

    def clear_cache(
        self,
        exported_only: bool = False,
        protected_paths: Iterable[Path | str] = (),
    ) -> Dict[str, Any]:
        """Manually clear exported-only or all non-open cached remote media files."""
        self.load_index()
        protected = self._normalize_protected_set(protected_paths)
        deleted_keys: List[str] = []
        skipped_protected = 0
        freed_bytes = 0

        for key, entry in list(self._entries.items()):
            if exported_only and not entry.get("last_exported_at"):
                continue
            fp_str = str(entry.get("file_path") or "")
            if not is_path_inside_cache(fp_str, self.cache_dir):
                continue
            norm_fp = os.path.normcase(str(Path(fp_str).expanduser().resolve()))
            if norm_fp in protected:
                skipped_protected += 1
                continue
            fp = Path(fp_str)
            sz = int(entry.get("size_bytes") or 0)
            try:
                if fp.exists():
                    sz = max(sz, int(fp.stat().st_size))
                    fp.unlink()
                self._entries.pop(key, None)
                deleted_keys.append(key)
                freed_bytes += sz
            except OSError:
                continue

        if deleted_keys:
            self.save_index()
        return {
            "deleted_count": len(deleted_keys),
            "freed_bytes": freed_bytes,
            "skipped_protected": skipped_protected,
            "remaining_bytes": self.get_total_size_bytes(),
        }


__all__ = [
    "DEFAULT_CACHE_CAP_GB",
    "CACHE_CAP_SETTING_KEY",
    "CACHE_INDEX_FILENAME",
    "format_bytes_human",
    "get_remote_media_cache_dir",
    "is_path_inside_cache",
    "make_cache_key",
    "build_remote_media_source_record",
    "RemoteMediaCacheManager",
]
