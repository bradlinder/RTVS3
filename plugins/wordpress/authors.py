"""Pure-Python helpers for WordPress user and PublishPress Author ID mapping."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Tuple

__all__ = [
    "count_selected_authors",
    "expand_legacy_author_term_ids",
    "extract_checked_author_ids",
    "is_author_item_selected",
    "resolve_selected_author_names",
]


def _pos_int(val: Any) -> int:
    try:
        iv = int(val)
        return iv if iv > 0 else 0
    except (TypeError, ValueError):
        return 0


def _dedupe_pos_ints(values: Iterable[Any]) -> List[int]:
    out: List[int] = []
    seen: set[int] = set()
    for val in (values or ()):
        iv = _pos_int(val)
        if iv > 0 and iv not in seen:
            seen.add(iv)
            out.append(iv)
    return out


def extract_checked_author_ids(checked_authors: Sequence[Dict[str, Any]]) -> Tuple[List[int], List[int]]:
    """Split checked author entries into WordPress ``author_ids`` and PublishPress ``author_term_ids``.

    Mapped WordPress Users (``is_guest=False`` with a PublishPress ``term_id``) populate
    both ``author_ids`` and ``author_term_ids`` so PublishPress preserves all selected authors
    when mixed with Guest Authors or additional mapped users. Guest Authors only populate
    ``author_term_ids`` and never leak their ``term_id`` into WordPress ``author_ids``.
    """
    author_ids: List[int] = []
    author_term_ids: List[int] = []
    seen_users: set[int] = set()
    seen_terms: set[int] = set()

    for data in (checked_authors or ()):
        if not isinstance(data, dict):
            continue
        is_guest = bool(data.get("is_guest", False))
        tid = _pos_int(data.get("term_id"))
        aid = _pos_int(data.get("id"))
        if is_guest and tid <= 0:
            tid = aid
        if tid > 0 and tid not in seen_terms:
            seen_terms.add(tid)
            author_term_ids.append(tid)

        if not is_guest:
            uid = _pos_int(data.get("user_id")) or aid
            if uid > 0 and uid not in seen_users:
                seen_users.add(uid)
                author_ids.append(uid)

    return author_ids, author_term_ids


def is_author_item_selected(
    author: Dict[str, Any],
    author_ids: Iterable[Any],
    author_term_ids: Iterable[Any],
) -> bool:
    """Return True if an author item matches the post's selected user/PublishPress term IDs."""
    if not isinstance(author, dict):
        return False

    term_set = set(_dedupe_pos_ints(author_term_ids))
    auth_set = set(_dedupe_pos_ints(author_ids))

    is_guest = bool(author.get("is_guest", False))
    tid = _pos_int(author.get("term_id"))
    aid = _pos_int(author.get("id"))
    uid = _pos_int(author.get("user_id")) or aid

    # PublishPress ppma_author terms are authoritative whenever present on the post.
    if term_set and (tid > 0 or is_guest):
        return (tid or aid) in term_set

    if is_guest:
        return False
    return uid in auth_set


def resolve_selected_author_names(
    cached_authors: Sequence[Dict[str, Any]],
    author_ids: Iterable[Any],
    author_term_ids: Iterable[Any],
) -> List[str]:
    """Return display names for cached author entries selected on a post."""
    names: List[str] = []
    seen: set[str] = set()
    for author in (cached_authors or ()):
        if not is_author_item_selected(author, author_ids, author_term_ids):
            continue
        name = str(author.get("name") or ("Guest" if author.get("is_guest") else "User")).strip()
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def count_selected_authors(author_ids: Iterable[Any], author_term_ids: Iterable[Any]) -> int:
    """Return distinct selected author count without double-counting mapped WP/PublishPress users."""
    term_set = set(_dedupe_pos_ints(author_term_ids))
    if term_set:
        return len(term_set)
    return len(set(_dedupe_pos_ints(author_ids)))


def expand_legacy_author_term_ids(
    author_ids: Iterable[Any],
    author_term_ids: Iterable[Any],
    cached_authors: Sequence[Dict[str, Any]],
) -> Tuple[List[int], List[int]]:
    """Backfill PublishPress ``term_id`` entries when legacy project data only stored ``author_ids``."""
    clean_auth = _dedupe_pos_ints(author_ids)
    clean_terms = _dedupe_pos_ints(author_term_ids)
    if clean_terms or not clean_auth or not cached_authors:
        return clean_auth, clean_terms

    auth_set = set(clean_auth)
    expanded_terms: List[int] = []
    seen_terms: set[int] = set()
    for author in cached_authors:
        if not isinstance(author, dict) or author.get("is_guest"):
            continue
        uid = _pos_int(author.get("user_id")) or _pos_int(author.get("id"))
        tid = _pos_int(author.get("term_id"))
        if uid in auth_set and tid > 0 and tid not in seen_terms:
            seen_terms.add(tid)
            expanded_terms.append(tid)

    return clean_auth, expanded_terms
