"""
speaker_profiles.py — Persistent Station Voice Profile Manager & Storage Engine.

Provides:
- StationVoiceProfile: Data class representing an acoustic voice identity vector and metadata.
- StationVoiceProfileStore: Thread-safe persistent JSON storage in application data directory.
- ManageVoiceProfilesDialog: Lazy backward-compatible re-export from ``speaker_profiles_dialog``.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from core_utils import get_app_data_dir, safe_replace
from speaker_identity import (
    _as_vector,
    centroid,
    cosine_similarity,
)

__all__ = [
    "StationVoiceProfile",
    "StationVoiceProfileStore",
    "ManageVoiceProfilesDialog",
]


@dataclass
class StationVoiceProfile:
    id: str
    name: str
    vector: List[float]
    sample_count: int = 1
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    notes: str = ""
    source_media: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Optional["StationVoiceProfile"]:
        if not isinstance(data, dict):
            return None
        vec = _as_vector(data.get("vector"))
        if vec is None:
            return None
        return cls(
            id=str(data.get("id", "") or f"spk_{int(time.time() * 1000)}"),
            name=str(data.get("name", "Unknown Voice")).strip() or "Unknown Voice",
            vector=vec,
            sample_count=int(data.get("sample_count", 1) or 1),
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
            notes=str(data.get("notes", "")),
            source_media=str(data.get("source_media", "")),
        )


class StationVoiceProfileStore:
    """Persistent storage manager for recurring station voice acoustic profiles."""

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            self.storage_dir = Path(get_app_data_dir())
        else:
            self.storage_dir = Path(storage_dir)
        self.file_path = self.storage_dir / "voice_profiles.json"
        self._profiles: Dict[str, StationVoiceProfile] = {}
        self.load()

    def get_profiles_file_path(self) -> Path:
        return self.file_path

    def load(self) -> None:
        self._profiles.clear()
        if not self.file_path.exists():
            return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    prof = StationVoiceProfile.from_dict(item)
                    if prof:
                        self._profiles[prof.id] = prof
            elif isinstance(data, dict) and "profiles" in data:
                for item in data["profiles"]:
                    prof = StationVoiceProfile.from_dict(item)
                    if prof:
                        self._profiles[prof.id] = prof
        except Exception:
            pass

    def save(self) -> bool:
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = self.file_path.with_name(self.file_path.name + ".tmp")
            payload = {
                "version": 1,
                "count": len(self._profiles),
                "profiles": [p.to_dict() for p in self._profiles.values()],
            }
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            safe_replace(tmp_path, self.file_path)
            return True
        except Exception:
            return False

    def list_profiles(self) -> List[StationVoiceProfile]:
        return sorted(self._profiles.values(), key=lambda p: p.name.lower())

    def get_profile(self, profile_id: str) -> Optional[StationVoiceProfile]:
        return self._profiles.get(profile_id)

    def find_profile_by_name(self, name: str) -> Optional[StationVoiceProfile]:
        target = name.strip().lower()
        for p in self._profiles.values():
            if p.name.strip().lower() == target:
                return p
        return None

    def add_or_update_profile(
        self,
        name: str,
        vector: Sequence[float],
        sample_count: int = 1,
        notes: str = "",
        source_media: str = "",
        profile_id: Optional[str] = None,
    ) -> Optional[StationVoiceProfile]:
        norm_vec = _as_vector(vector)
        if norm_vec is None:
            return None
        clean_name = name.strip() or "Unnamed Voice"

        if profile_id and profile_id in self._profiles:
            prof = self._profiles[profile_id]
            prof.name = clean_name
            # If updating with additional turns, blend centroids
            if sample_count > 1:
                blended = centroid([prof.vector, norm_vec])
                if blended:
                    prof.vector = blended
            else:
                prof.vector = norm_vec
            prof.sample_count = max(prof.sample_count, sample_count)
            prof.updated_at = time.time()
            if notes:
                prof.notes = notes
            if source_media:
                prof.source_media = source_media
            self.save()
            return prof

        # Check existing by name
        existing = self.find_profile_by_name(clean_name)
        if existing:
            existing.vector = norm_vec
            existing.sample_count = max(existing.sample_count, sample_count)
            existing.updated_at = time.time()
            if notes:
                existing.notes = notes
            if source_media:
                existing.source_media = source_media
            self.save()
            return existing

        pid = profile_id or f"spk_{int(time.time() * 1000)}"
        prof = StationVoiceProfile(
            id=pid,
            name=clean_name,
            vector=norm_vec,
            sample_count=sample_count,
            created_at=time.time(),
            updated_at=time.time(),
            notes=notes,
            source_media=source_media,
        )
        self._profiles[pid] = prof
        self.save()
        return prof

    def remove_profile(self, profile_id: str) -> bool:
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            self.save()
            return True
        return False

    def clear(self) -> None:
        self._profiles.clear()
        self.save()

    def match_vector(
        self,
        vector: Sequence[float],
        threshold: float = 0.78,
        min_margin: float = 0.04,
    ) -> Optional[Tuple[StationVoiceProfile, float, float]]:
        """
        Compare an unknown candidate vector against all saved voice profiles.
        Returns (best_profile, similarity, margin) if a confident match is found, else None.
        """
        vec = _as_vector(vector)
        if vec is None or not self._profiles:
            return None

        profiles = list(self._profiles.values())
        if len(profiles) == 1:
            sim = cosine_similarity(vec, profiles[0].vector)
            if sim >= threshold:
                return profiles[0], sim, 1.0
            return None

        best_p = None
        best_sim = -1.0
        second_sim = -1.0

        for p in profiles:
            sim = cosine_similarity(vec, p.vector)
            if sim > best_sim:
                second_sim = best_sim
                best_sim = sim
                best_p = p
            elif sim > second_sim:
                second_sim = sim

        margin = best_sim - max(0.0, second_sim)
        if best_sim >= threshold and margin >= min_margin and best_p is not None:
            return best_p, best_sim, margin
        return None



def __getattr__(name: str):
    if name == "ManageVoiceProfilesDialog":
        from speaker_profiles_dialog import ManageVoiceProfilesDialog
        return ManageVoiceProfilesDialog
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
