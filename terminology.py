"""Model-independent terminology and glossary support.

The glossary is deliberately kept outside any ASR or translation engine.
It provides:
- canonical spelling normalization for every transcription backend;
- multi-variant source mapping (comma/semicolon-separated alternate spellings);
- optional case-sensitive matching (`match_case`);
- two-pass contextual proper-noun resolution (multi-word phonetic matching +
  project-scoped single-word co-reference propagation with ambiguity guards);
- persistent parsing of the legacy ``source -> preferred`` format;
- protected proper-noun rules for translation workers.

Legacy glossary entries remain valid. New code may also store dictionaries
with ``source``, ``preferred``, ``do_not_translate``, and ``match_case`` keys.
"""
from __future__ import annotations

from difflib import SequenceMatcher
import json
import re
from typing import Any, Iterable

_WORD_EDGE_RE = re.compile(r"^([^\w]*)(.*?)([^\w]*)$", re.UNICODE | re.DOTALL)
_SENTENCE_BREAK_CHARS = set(".?!;:()[]{}\"'“”")
_NON_NAME_FOLLOWERS = {
    "and", "or", "but", "the", "a", "an", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "has",
    "have", "had", "will", "would", "can", "could", "should", "may", "might",
    "said", "says", "told", "asked", "added", "noted", "reported", "reports",
    "who", "whom", "whose", "which", "that", "this", "these", "those",
    "here", "there", "now", "then", "today", "yesterday", "tomorrow",
}


def split_source_variants(
    source_raw: Any,
    preferred: str = "",
    match_case: bool = False,
) -> list[str]:
    """Split a source field (comma/semicolon separated or list) into unique variants."""
    if isinstance(source_raw, (list, tuple)):
        parts = [str(p or "").strip() for p in source_raw]
    else:
        text = str(source_raw or "").strip()
        if not text:
            parts = []
        elif "," in text or ";" in text:
            parts = [p.strip() for p in re.split(r"[,;]+", text) if p.strip()]
        else:
            parts = [text]

    out: list[str] = []
    seen: set[str] = set()
    for part in parts:
        if not part:
            continue
        key = part if match_case else part.casefold()
        if key not in seen:
            seen.add(key)
            out.append(part)

    pref = str(preferred or "").strip()
    if pref and not out:
        out.append(pref)
    return out


def format_source_variants(
    variants: Iterable[str],
    match_case: bool = False,
) -> str:
    """Format a sequence of source variants into a clean comma-separated string."""
    cleaned = split_source_variants(list(variants), match_case=match_case)
    return ", ".join(cleaned)


def parse_glossary(raw: Any) -> list[dict[str, Any]]:
    """Return normalized glossary entries while accepting legacy list strings."""
    if raw is None or raw == "":
        return []

    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = [raw]
    if not isinstance(raw, (list, tuple)):
        raw = [raw]

    entries: list[dict[str, Any]] = []
    seen: set[tuple[str, str, bool]] = set()

    for item in raw:
        if isinstance(item, dict):
            raw_sources = item.get("sources", item.get("source", item.get("term", "")))
            preferred = str(
                item.get("preferred", item.get("target", "")) or ""
            ).strip()
            match_case = bool(item.get("match_case", item.get("case_sensitive", False)))
            variants = split_source_variants(raw_sources, preferred=preferred, match_case=match_case)
            if not preferred and variants:
                preferred = variants[0]
            source = format_source_variants(variants, match_case=match_case)
            dnt = bool(item.get("do_not_translate", item.get("protected", True)))
        else:
            text = str(item or "").strip()
            if not text:
                continue
            if "->" in text:
                src_part, preferred = (part.strip() for part in text.split("->", 1))
            else:
                src_part = preferred = text
            match_case = False
            variants = split_source_variants(src_part, preferred=preferred, match_case=False)
            source = format_source_variants(variants, match_case=False)
            dnt = True

        if not source or not preferred:
            continue
        key = (
            source if match_case else source.casefold(),
            preferred if match_case else preferred.casefold(),
            match_case,
        )
        if key in seen:
            continue
        seen.add(key)
        entries.append(
            {
                "source": source,
                "preferred": preferred,
                "do_not_translate": dnt,
                "match_case": match_case,
            }
        )

    # Longest first prevents a short term from rewriting part of a longer one.
    return sorted(entries, key=lambda x: len(str(x["source"])), reverse=True)


def expand_glossary_rules(glossary: Any) -> list[dict[str, Any]]:
    """Expand multi-variant glossary entries into atomic replacement rules (longest source first)."""
    entries = parse_glossary(glossary)
    expanded: list[dict[str, Any]] = []
    seen: set[tuple[str, str, bool]] = set()

    for entry in entries:
        preferred = str(entry.get("preferred", "")).strip()
        if not preferred:
            continue
        dnt = bool(entry.get("do_not_translate", True))
        match_case = bool(entry.get("match_case", False))
        variants = split_source_variants(
            entry.get("source", ""),
            preferred=preferred,
            match_case=match_case,
        )
        # When case-insensitive, also include the preferred term itself so that
        # lowercase/mixed-case occurrences of the preferred spelling are normalized.
        if not match_case and preferred.casefold() not in {v.casefold() for v in variants}:
            variants.append(preferred)

        for variant in variants:
            key = (
                variant if match_case else variant.casefold(),
                preferred if match_case else preferred.casefold(),
                match_case,
            )
            if key in seen:
                continue
            seen.add(key)
            expanded.append(
                {
                    "source": variant,
                    "preferred": preferred,
                    "do_not_translate": dnt,
                    "match_case": match_case,
                }
            )

    return sorted(expanded, key=lambda r: len(str(r["source"])), reverse=True)


def sort_glossary_entries(
    entries: Iterable[dict[str, Any]],
    mode: str = "alpha_asc",
) -> list[dict[str, Any]]:
    """Return glossary entries sorted for UI presentation without mutating replacement order."""
    items = [dict(e) for e in entries]
    if mode == "alpha_desc":
        return sorted(
            items,
            key=lambda e: (str(e.get("source", "")).casefold(), str(e.get("preferred", "")).casefold()),
            reverse=True,
        )
    if mode == "preferred_asc":
        return sorted(
            items,
            key=lambda e: (str(e.get("preferred", "")).casefold(), str(e.get("source", "")).casefold()),
        )
    if mode == "preferred_desc":
        return sorted(
            items,
            key=lambda e: (str(e.get("preferred", "")).casefold(), str(e.get("source", "")).casefold()),
            reverse=True,
        )
    if mode == "dnt_first":
        return sorted(
            items,
            key=lambda e: (
                not bool(e.get("do_not_translate", True)),
                str(e.get("source", "")).casefold(),
            ),
        )
    if mode == "match_case_first":
        return sorted(
            items,
            key=lambda e: (
                not bool(e.get("match_case", False)),
                str(e.get("source", "")).casefold(),
            ),
        )
    # Default: "alpha_asc"
    return sorted(
        items,
        key=lambda e: (str(e.get("source", "")).casefold(), str(e.get("preferred", "")).casefold()),
    )


def add_alternate_spelling(
    raw_glossary: Any,
    preferred_term: str,
    alternate_spelling: str,
    do_not_translate: bool = True,
    match_case: bool = False,
) -> list[dict[str, Any]]:
    """Add one or more alternate spellings for a preferred glossary term."""
    pref = str(preferred_term or "").strip()
    alt_variants = split_source_variants(alternate_spelling, match_case=match_case)
    entries = parse_glossary(raw_glossary)
    if not pref or not alt_variants:
        return entries

    matched_entry = None
    for entry in entries:
        if str(entry.get("preferred", "")).strip().casefold() == pref.casefold():
            matched_entry = entry
            break

    if matched_entry is not None:
        mc = bool(matched_entry.get("match_case", False))
        existing_variants = split_source_variants(
            matched_entry.get("source", ""),
            preferred=matched_entry.get("preferred", pref),
            match_case=mc,
        )
        combined = split_source_variants(
            existing_variants + alt_variants,
            preferred=matched_entry.get("preferred", pref),
            match_case=mc,
        )
        matched_entry["source"] = format_source_variants(combined, match_case=mc)
    else:
        initial_variants = split_source_variants(
            [pref] + alt_variants,
            preferred=pref,
            match_case=match_case,
        )
        entries.append(
            {
                "source": format_source_variants(initial_variants, match_case=match_case),
                "preferred": pref,
                "do_not_translate": bool(do_not_translate),
                "match_case": bool(match_case),
            }
        )

    return parse_glossary(entries)


def load_glossary(settings_store=None) -> list[dict[str, Any]]:
    """Load the shared glossary from the application's QSettings object."""
    try:
        if settings_store is None:
            from PySide6.QtCore import QSettings
            settings_store = QSettings("RadioTVStorySegmenter", "RadioTVStorySegmenter")
        return parse_glossary(settings_store.value("glossary", ""))
    except Exception:
        return []


def _replace_term(
    text: str,
    source: str,
    preferred: str,
    match_case: bool = False,
) -> str:
    if not text or not source:
        return text
    # Unicode-aware \w boundaries work for accented Latin names and avoid
    # changing a term embedded inside a larger word.
    flags = 0 if match_case else re.IGNORECASE
    pattern = re.compile(
        rf"(?<!\w){re.escape(source)}(?!\w)", flags
    )
    return pattern.sub(lambda _m: preferred, text)


def normalize_text(text: str, glossary: Iterable[dict[str, Any]]) -> str:
    """Canonicalize glossary terms without changing surrounding punctuation."""
    result = str(text or "")
    if not result:
        return result
    rules = expand_glossary_rules(glossary)
    for entry in rules:
        result = _replace_term(
            result,
            str(entry["source"]),
            str(entry["preferred"]),
            match_case=bool(entry.get("match_case", False)),
        )
    return result


def _phonetic_name_skeleton(token: str) -> str:
    """Compute a normalized phonetic skeleton for English/Latin proper-noun comparison."""
    s = re.sub(r"[^\w]", "", str(token or "").strip().lower())
    if not s:
        return ""
    # Normalize common name suffix & digraph variations (e.g. Kimberley / Kimberly / Kimberlei)
    for pat, rep in (
        (r"leigh$", "li"),
        (r"ley$", "li"),
        (r"lei$", "li"),
        (r"lie$", "li"),
        (r"ly$", "li"),
        (r"ie$", "i"),
        (r"ey$", "i"),
        (r"y$", "i"),
        (r"ph", "f"),
        (r"ck", "k"),
        (r"ch", "k"),
        (r"sh", "s"),
        (r"th", "t"),
    ):
        s = re.sub(pat, rep, s)
    # Collapse repeated consecutive letters (e.g. "ll" -> "l", "nn" -> "n")
    s = re.sub(r"(.)\1+", r"\1", s)
    return s


def _name_token_similarity(a: str, b: str) -> float:
    """Return orthographic + phonetic similarity [0.0, 1.0] between two name tokens."""
    a_low = str(a or "").strip().lower()
    b_low = str(b or "").strip().lower()
    if not a_low or not b_low:
        return 0.0
    if a_low == b_low:
        return 1.0
    # Require matching initial letter (or Ph/F, C/K, S/C equivalence)
    init_pair = {a_low[0], b_low[0]}
    if a_low[0] != b_low[0] and init_pair not in ({"c", "k"}, {"c", "s"}, {"f", "p"}):
        return 0.0
    if len(a_low) < 3 or len(b_low) < 3:
        return 0.0

    skel_a = _phonetic_name_skeleton(a_low)
    skel_b = _phonetic_name_skeleton(b_low)
    if skel_a and skel_a == skel_b:
        return 0.96

    raw_ratio = SequenceMatcher(None, a_low, b_low).ratio()
    skel_ratio = SequenceMatcher(None, skel_a, skel_b).ratio() if (skel_a and skel_b) else 0.0
    return max(raw_ratio, skel_ratio * 0.95)


def _split_word_affixes(raw_word: str) -> tuple[str, str, str]:
    """Split a timed word token into (leading_punct_and_space, core_word, trailing_punct)."""
    m = _WORD_EDGE_RE.match(str(raw_word or ""))
    if not m:
        return "", str(raw_word or ""), ""
    lead, core, trail = m.group(1), m.group(2), m.group(3)
    # Separate English possessive ('s / ’s) into trailing suffix so base name matches cleanly
    if core.lower().endswith(("'s", "’s")) and len(core) > 2:
        trail = core[-2:] + trail
        core = core[:-2]
    return lead, core, trail


def _has_sentence_break(trail: str) -> bool:
    """Return True if trailing punctuation marks a clause/sentence boundary."""
    return any(ch in _SENTENCE_BREAK_CHARS for ch in str(trail or ""))


def _discover_project_contextual_rules(
    segments: list[Any],
    base_entries: list[dict[str, Any]],
    expanded_rules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Two-pass project-scoped proper-noun discovery and single-word co-reference resolution.

    Pass 1: Scans the transcript for multi-word protected proper nouns (both exact
            glossary source matches and close phonetic multi-word matches like
            'Kimberley Davis' -> 'Kimberlei Davis').
    Pass 2: For any multi-word proper noun confirmed present in this specific project
            (via Pass 1 or speaker labels), propagates single-word first/last name
            variants (e.g. standalone 'Kimberley' -> 'Kimberlei') across this project
            unless a conflicting full name (e.g. 'Kimberley Johnson') is also present.
    """
    multi_word_proper: list[dict[str, Any]] = []
    for entry in base_entries:
        if not entry.get("do_not_translate", True):
            continue
        pref = str(entry.get("preferred", "")).strip()
        pref_tokens = pref.split()
        if len(pref_tokens) >= 2 and all(any(c.isalpha() for c in t) for t in pref_tokens):
            multi_word_proper.append(entry)

    if not multi_word_proper:
        return []

    # Collect all word sequences and speaker names across the project
    all_token_sequences: list[list[tuple[str, str]]] = []
    project_speakers: set[str] = set()

    for seg in segments:
        if not isinstance(seg, dict):
            continue
        spk = str(seg.get("speaker", "") or "").strip()
        if spk:
            project_speakers.add(spk.casefold())

        words = seg.get("words")
        if words and all(isinstance(w, dict) and "word" in w for w in words):
            seq: list[tuple[str, str]] = []
            for w in words:
                _, core, trail = _split_word_affixes(str(w.get("word", "")))
                if core:
                    seq.append((core, trail))
            if seq:
                all_token_sequences.append(seq)
        else:
            raw_txt = str(seg.get("text", "") or "")
            if raw_txt:
                seq = []
                for raw_tok in raw_txt.split():
                    _, core, trail = _split_word_affixes(raw_tok)
                    if core:
                        seq.append((core, trail))
                if seq:
                    all_token_sequences.append(seq)

    dynamic_rules: list[dict[str, Any]] = []
    confirmed_entries: list[tuple[dict[str, Any], set[tuple[str, str]]]] = []

    # Pass 1: Detect which multi-word proper nouns appear in this project
    for entry in multi_word_proper:
        pref = str(entry["preferred"]).strip()
        pref_tokens = pref.split()
        n_tok = len(pref_tokens)
        match_case = bool(entry.get("match_case", False))
        explicit_variants = [
            v.split()
            for v in split_source_variants(entry.get("source", ""), preferred=pref, match_case=match_case)
            if len(v.split()) == n_tok
        ]

        is_confirmed = pref.casefold() in project_speakers
        observed_token_mappings: set[tuple[str, str]] = set()

        # Seed token mappings from explicit multi-word alternate spellings (if any)
        for var_tokens in explicit_variants:
            for v_tok, p_tok in zip(var_tokens, pref_tokens):
                if v_tok.casefold() != p_tok.casefold():
                    observed_token_mappings.add((v_tok, p_tok))

        for seq in all_token_sequences:
            if len(seq) < n_tok:
                continue
            for idx in range(len(seq) - n_tok + 1):
                window = seq[idx : idx + n_tok]
                # Ensure no sentence break inside the multi-word window
                if any(_has_sentence_break(window[k][1]) for k in range(n_tok - 1)):
                    continue
                win_tokens = [w[0] for w in window]

                # Check 1A: Exact match against explicit multi-word source variants
                matched_explicit = False
                for var_tokens in explicit_variants:
                    if match_case:
                        if win_tokens == var_tokens:
                            matched_explicit = True
                            break
                    else:
                        if [t.casefold() for t in win_tokens] == [t.casefold() for t in var_tokens]:
                            matched_explicit = True
                            break
                if matched_explicit:
                    is_confirmed = True
                    for w_tok, p_tok in zip(win_tokens, pref_tokens):
                        if w_tok.casefold() != p_tok.casefold():
                            observed_token_mappings.add((w_tok, p_tok))
                    continue

                # Check 1B: Phonetic / near-orthographic multi-word proper noun match
                # Require at least one capitalized token in the transcript window
                if not any(t[0].isupper() for t in win_tokens if t):
                    continue
                sims = [_name_token_similarity(w_tok, p_tok) for w_tok, p_tok in zip(win_tokens, pref_tokens)]
                # Require at least one exact token match (e.g. surname 'Davis') or all >= 0.88,
                # and every token >= 0.80 similarity.
                has_anchor = any(w_tok.casefold() == p_tok.casefold() for w_tok, p_tok in zip(win_tokens, pref_tokens))
                if all(s >= 0.80 for s in sims) and (has_anchor or all(s >= 0.88 for s in sims)):
                    is_confirmed = True
                    phrase_src = " ".join(win_tokens)
                    dynamic_rules.append(
                        {
                            "source": phrase_src,
                            "preferred": pref,
                            "do_not_translate": True,
                            "match_case": False,
                        }
                    )
                    for w_tok, p_tok in zip(win_tokens, pref_tokens):
                        if w_tok.casefold() != p_tok.casefold():
                            observed_token_mappings.add((w_tok, p_tok))

        if is_confirmed:
            confirmed_entries.append((entry, observed_token_mappings))

    if not confirmed_entries:
        return dynamic_rules

    # Pass 2: Project-scoped single-word co-reference propagation with ambiguity guard
    for entry, observed_mappings in confirmed_entries:
        pref = str(entry["preferred"]).strip()
        pref_tokens = pref.split()
        first_pref = pref_tokens[0]
        valid_surnames = {t.casefold() for t in pref_tokens[1:]}

        # Also scan transcript for standalone phonetic variants of first_pref (e.g. "Kimberley")
        for seq in all_token_sequences:
            for core_tok, _ in seq:
                if (
                    core_tok
                    and core_tok[0].isupper()
                    and core_tok.casefold() != first_pref.casefold()
                    and _name_token_similarity(core_tok, first_pref) >= 0.82
                ):
                    observed_mappings.add((core_tok, first_pref))

        for src_tok, target_pref_tok in observed_mappings:
            # Ambiguity Guard: Check if src_tok is followed in this transcript by a
            # DIFFERENT capitalized surname (e.g. "Kimberley Johnson" vs "Kimberlei Davis").
            has_conflict = False
            if target_pref_tok == first_pref and valid_surnames:
                for seq in all_token_sequences:
                    for idx in range(len(seq) - 1):
                        cur_w, cur_trail = seq[idx]
                        nxt_w, _ = seq[idx + 1]
                        if _has_sentence_break(cur_trail):
                            continue
                        if cur_w.casefold() == src_tok.casefold() and nxt_w and nxt_w[0].isupper():
                            nxt_low = nxt_w.casefold()
                            if (
                                nxt_low not in valid_surnames
                                and nxt_low not in _NON_NAME_FOLLOWERS
                                and all(_name_token_similarity(nxt_w, p_sur) < 0.80 for p_sur in pref_tokens[1:])
                            ):
                                has_conflict = True
                                break
                    if has_conflict:
                        break

            if not has_conflict:
                dynamic_rules.append(
                    {
                        "source": src_tok,
                        "preferred": target_pref_tok,
                        "do_not_translate": True,
                        "match_case": False,
                    }
                )

    return dynamic_rules


def _normalize_timed_words(
    words: list[Any],
    rules: list[dict[str, Any]],
) -> list[Any]:
    """Apply both multi-word and single-word glossary rules across timed word dicts."""
    out = [dict(w) if isinstance(w, dict) else w for w in words]
    n_words = len(out)
    if n_words == 0:
        return out

    multi_rules: list[tuple[list[str], list[str], bool]] = []
    single_rules: list[dict[str, Any]] = []
    for r in rules:
        src_str = str(r.get("source", "")).strip()
        pref_str = str(r.get("preferred", "")).strip()
        if not src_str or not pref_str:
            continue
        src_parts = src_str.split()
        if len(src_parts) >= 2:
            multi_rules.append((src_parts, pref_str.split(), bool(r.get("match_case", False))))
        else:
            single_rules.append(r)

    # 1. Apply multi-word rules across consecutive timed words
    if multi_rules:
        for src_parts, pref_parts, match_case in multi_rules:
            win_len = len(src_parts)
            if win_len > n_words:
                continue
            i = 0
            while i <= n_words - win_len:
                window_dicts = out[i : i + win_len]
                if not all(isinstance(w, dict) and "word" in w for w in window_dicts):
                    i += 1
                    continue

                affixes = [_split_word_affixes(str(w["word"])) for w in window_dicts]
                # Do not match across sentence punctuation breaks
                if any(_has_sentence_break(affixes[k][2]) for k in range(win_len - 1)):
                    i += 1
                    continue

                cores = [a[1] for a in affixes]
                is_match = (
                    (cores == src_parts)
                    if match_case
                    else ([c.casefold() for c in cores] == [s.casefold() for s in src_parts])
                )
                if is_match:
                    if len(pref_parts) == win_len:
                        for k in range(win_len):
                            lead, _, trail = affixes[k]
                            window_dicts[k]["word"] = f"{lead}{pref_parts[k]}{trail}"
                    else:
                        # Fallback when word count of preferred differs from source
                        lead0, _, _ = affixes[0]
                        _, _, trail_last = affixes[-1]
                        window_dicts[0]["word"] = f"{lead0}{' '.join(pref_parts)}{trail_last}"
                        for k in range(1, win_len):
                            window_dicts[k]["word"] = ""
                    i += win_len
                else:
                    i += 1

    # 2. Apply single-word rules to each word token
    if single_rules:
        for w in out:
            if isinstance(w, dict) and "word" in w and str(w["word"]):
                w["word"] = normalize_text(w["word"], single_rules)

    return out


def normalize_transcript(transcript: dict[str, Any], glossary=None) -> dict[str, Any]:
    """Normalize transcript text and word labels for every ASR backend."""
    if not isinstance(transcript, dict):
        return transcript
    base_entries = parse_glossary(glossary) if glossary is not None else load_glossary()
    if not base_entries:
        return transcript

    expanded_rules = expand_glossary_rules(base_entries)
    raw_segments = transcript.get("segments", []) or []

    # Discover project-scoped phonetic & co-reference rules (Two-Pass Engine)
    contextual_rules = _discover_project_contextual_rules(
        raw_segments,
        base_entries,
        expanded_rules,
    )
    active_rules = expand_glossary_rules(base_entries + contextual_rules)

    # Copy only the structures we mutate; callers retain the rest of the payload.
    result = dict(transcript)
    segments = []
    for segment in raw_segments:
        if not isinstance(segment, dict):
            segments.append(segment)
            continue
        seg = dict(segment)
        raw_words = segment.get("words", []) or []
        if raw_words:
            words = _normalize_timed_words(raw_words, active_rules)
            seg["words"] = words
        else:
            words = []

        if "text" in seg:
            # Prefer rebuilding from timed words when available so the
            # displayed segment and its word-level representation agree.
            if words and all(isinstance(w, dict) and "word" in w for w in words):
                joined = " ".join(
                    str(w["word"]).strip() for w in words if str(w.get("word", "")).strip()
                ).strip()
                seg["text"] = normalize_text(joined, active_rules)
            else:
                seg["text"] = normalize_text(seg["text"], active_rules)
        segments.append(seg)

    result["segments"] = segments
    result["text"] = " ".join(
        str(s.get("text", "")).strip()
        for s in segments
        if isinstance(s, dict) and str(s.get("text", "")).strip()
    )
    return result


def translation_rules(glossary=None) -> list[dict[str, Any]]:
    """Return only entries explicitly marked as protected for translation."""
    rules = expand_glossary_rules(glossary) if glossary is not None else expand_glossary_rules(load_glossary())
    return [r for r in rules if r.get("do_not_translate", True)]


def replace_term(
    text: str,
    source: str,
    preferred: str,
    match_case: bool = False,
) -> str:
    """Public replacement helper for translation workers."""
    return _replace_term(text, source, preferred, match_case=match_case)


def split_protected_text(text: str, glossary=None) -> list[tuple[str, bool]]:
    """Split text into translatable and protected pieces.

    Protected glossary terms are deliberately removed from the text sent to a
    translation engine.  This is stronger than translating the whole sentence
    and trying to repair the output afterward: a protected term can never be
    translated because it is never presented to the model.
    """
    text = str(text or "")
    rules = translation_rules(glossary) if glossary is not None else translation_rules()
    if not text or not rules:
        return [(text, False)] if text else []

    # Longest-first rules prevent a shorter protected term from consuming part
    # of a longer one.  Use Unicode-aware word boundaries.
    alternatives = [str(r["source"]) for r in rules if str(r.get("source", "")).strip()]
    if not alternatives:
        return [(text, False)]
    pattern = re.compile(
        r"(?<!\w)(?:" + "|".join(re.escape(x) for x in alternatives) + r")(?!\w)",
        re.IGNORECASE,
    )
    by_exact: dict[str, str] = {}
    by_casefold: dict[str, str] = {}
    for r in rules:
        src = str(r["source"])
        pref = str(r["preferred"])
        if r.get("match_case", False):
            by_exact.setdefault(src, pref)
        else:
            by_casefold.setdefault(src.casefold(), pref)

    pieces: list[tuple[str, bool]] = []
    last = 0
    for match in pattern.finditer(text):
        source = match.group(0)
        if source in by_exact:
            preferred = by_exact[source]
        elif source.casefold() in by_casefold:
            preferred = by_casefold[source.casefold()]
        else:
            # Matched case-insensitively against a match_case=True rule; leave unprotected
            continue

        if match.start() > last:
            pieces.append((text[last:match.start()], False))
        pieces.append((preferred, True))
        last = match.end()
    if last < len(text):
        pieces.append((text[last:], False))
    return pieces or [(text, False)]


def export_glossary_to_json(glossary: list[dict[str, Any]]) -> str:
    """Serialize glossary entries to formatted JSON string."""
    entries = parse_glossary(glossary)
    return json.dumps(entries, indent=2, ensure_ascii=False)


def export_glossary_to_csv(glossary: list[dict[str, Any]]) -> str:
    """Serialize glossary entries to standard CSV string."""
    import csv
    import io

    entries = parse_glossary(glossary)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["source", "preferred", "do_not_translate", "match_case"])
    for entry in entries:
        writer.writerow([
            entry.get("source", ""),
            entry.get("preferred", ""),
            "true" if entry.get("do_not_translate", True) else "false",
            "true" if entry.get("match_case", False) else "false",
        ])
    return output.getvalue()


def import_glossary_from_text(raw_text: str) -> list[dict[str, Any]]:
    """Parse glossary entries from JSON, CSV, TSV, or plain text lines."""
    import csv
    import io

    raw_text = str(raw_text or "").strip()
    if not raw_text:
        return []

    # Attempt 1: Standard JSON parsing
    if raw_text.startswith("[") or raw_text.startswith("{"):
        try:
            return parse_glossary(json.loads(raw_text))
        except Exception:
            pass

    # Attempt 2: CSV / TSV with headers or delimiters
    delimiter = "\t" if "\t" in raw_text.splitlines()[0] else ","
    try:
        reader = csv.reader(io.StringIO(raw_text), delimiter=delimiter)
        rows = list(reader)
        if rows:
            first_row = [c.strip().lower() for c in rows[0]]
            has_header = any(
                h in first_row
                for h in ("source", "preferred", "term", "translation", "do_not_translate", "match_case")
            )
            data_rows = rows[1:] if has_header else rows
            entries: list[dict[str, Any]] = []
            for row in data_rows:
                if not row or not any(cell.strip() for cell in row):
                    continue
                if len(row) >= 4:
                    src = row[0].strip()
                    pref = row[1].strip() or src
                    dnt = row[2].strip().lower() not in ("false", "0", "no", "n")
                    mc = row[3].strip().lower() in ("true", "1", "yes", "y")
                    if src:
                        entries.append(
                            {
                                "source": src,
                                "preferred": pref,
                                "do_not_translate": dnt,
                                "match_case": mc,
                            }
                        )
                elif len(row) == 3:
                    src = row[0].strip()
                    pref = row[1].strip() or src
                    dnt = row[2].strip().lower() not in ("false", "0", "no", "n")
                    if src:
                        entries.append({"source": src, "preferred": pref, "do_not_translate": dnt})
                elif len(row) == 2:
                    src = row[0].strip()
                    pref = row[1].strip() or src
                    if src:
                        entries.append({"source": src, "preferred": pref, "do_not_translate": True})
                elif len(row) == 1:
                    line = row[0].strip()
                    if line:
                        if "->" in line:
                            s, p = (x.strip() for x in line.split("->", 1))
                            entries.append({"source": s, "preferred": p, "do_not_translate": True})
                        else:
                            entries.append({"source": line, "preferred": line, "do_not_translate": True})
            if entries:
                return parse_glossary(entries)
    except Exception:
        pass

    # Attempt 3: Line-by-line fallback
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    return parse_glossary(lines)
