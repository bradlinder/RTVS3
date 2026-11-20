"""speaker_name_matcher.py — Headless phonetic and fuzzy cleanup for guest and speaker names.

Pure-Python module (zero PySide6 / Qt dependencies) providing:
- Case-preserving replacement helpers (e.g., ``ife -> Iffy``, ``IFE -> IFFY``)
- Broadcast-ASR phonetic normalization & Soundex similarity
- Multi-word and single-word misspelled proper-noun discovery against confirmed speakers
- Deterministic bulk replacement helpers with optional word-timing synchronization
"""
from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
import re
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple
import unicodedata

__all__ = [
    "SpeakerNameCandidate",
    "apply_bulk_text_replacements",
    "consonant_skeleton",
    "extract_confirmed_speaker_names",
    "find_misspelled_speaker_names",
    "is_generic_role_label",
    "is_generic_speaker_label",
    "name_similarity",
    "phonetic_norm",
    "phonetic_soundex",
    "preserve_case_replace",
]

_GENERIC_SPEAKER_PATTERNS = (
    re.compile(r"^speaker[\s_-]*\d+$", re.IGNORECASE),
    re.compile(r"^spk[\s_-]*\d+$", re.IGNORECASE),
    re.compile(r"^seg[\s_-]*\d+[\s_-]*speaker$", re.IGNORECASE),
    re.compile(r"^\d+$"),
)

_GENERIC_ROLE_LABELS = frozenset({
    "",
    "speaker",
    "unknown",
    "unknown speaker",
    "unassigned",
    "host",
    "co-host",
    "cohost",
    "guest",
    "interviewer",
    "interviewee",
    "reporter",
    "anchor",
    "narrator",
    "announcer",
    "caller",
    "moderator",
    "producer",
    "panelist",
})

# High-frequency everyday English words that must never be flagged as misspelled
# single-word speaker names (especially important for short names like "Iffy").
_COMMON_ENGLISH_STOPWORDS = frozenset({
    "the", "and", "for", "are", "but", "not", "you", "all", "any", "can", "had", "her", "was", "one",
    "our", "out", "day", "get", "has", "him", "his", "how", "man", "new", "now", "old", "see", "two",
    "way", "who", "boy", "did", "its", "let", "put", "say", "she", "too", "use", "iff", "off", "yet",
    "yes", "not", "far", "own", "set", "run", "ask", "try", "end", "why", "big", "few", "got", "may",
    "that", "with", "have", "this", "will", "your", "from", "they", "know", "want", "been", "good",
    "much", "some", "time", "very", "when", "come", "here", "just", "like", "long", "make", "many",
    "more", "only", "over", "such", "take", "than", "them", "well", "were", "what", "into", "year",
    "also", "back", "even", "find", "give", "most", "name", "said", "same", "tell", "work", "call",
    "case", "city", "down", "even", "feel", "five", "four", "goes", "hand", "head", "help", "high",
    "home", "hope", "hour", "idea", "keep", "kind", "last", "late", "left", "less", "life", "line",
    "live", "look", "love", "made", "main", "mean", "mind", "miss", "more", "move", "must", "near",
    "need", "next", "nine", "none", "note", "open", "part", "past", "play", "real", "rest", "rich",
    "road", "room", "safe", "said", "seen", "self", "send", "show", "side", "sign", "soon", "sort",
    "stay", "step", "stop", "sure", "talk", "team", "term", "test", "text", "then", "they", "this",
    "told", "took", "town", "true", "turn", "type", "unit", "upon", "used", "user", "view", "wait",
    "walk", "wall", "week", "went", "what", "when", "whom", "wide", "wife", "will", "wish", "word",
    "yeah", "zero", "kids", "keys", "kiss", "cash", "cost", "cast", "easy", "else", "ever", "fact",
    "about", "after", "again", "being", "below", "between", "could", "every", "first", "found",
    "great", "going", "house", "large", "learn", "might", "never", "other", "place", "plant",
    "point", "right", "small", "sound", "spell", "still", "study", "their", "there", "these",
    "thing", "think", "those", "three", "under", "water", "where", "which", "while", "world",
    "would", "write", "years", "today", "thank", "thanks", "hello", "guest", "guests", "cause",
    "cases", "close", "class", "clear", "clean", "check", "child", "chose", "chief", "chair",
    "music", "story", "stories", "show", "shows", "block", "around", "media", "radio", "philly",
    "people", "person", "really", "actually", "literally", "basically", "obviously", "probably",
    "because", "before", "behind", "should", "within", "without", "through", "another", "welcome",
    "morning", "evening", "tonight", "minutes", "seconds", "question", "questions", "answer",
    "important", "different", "community", "something", "everything", "anything", "nothing",
    "everyone", "somebody", "everybody", "understand", "remember", "interview", "conversation",
})

_WORD_SPAN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ'’-]*")
_SPLIT_NAME_PARTS_RE = re.compile(r"[\s\-]+")

_SOUNDEX_MAP = {
    "b": "1", "f": "1", "p": "1", "v": "1",
    "c": "2", "g": "2", "j": "2", "k": "2", "q": "2", "s": "2", "x": "2", "z": "2",
    "d": "3", "t": "3",
    "l": "4",
    "m": "5", "n": "5",
    "r": "6",
}


@dataclass
class SpeakerNameCandidate:
    found_text: str
    suggested_name: str
    count: int
    score: float
    sample_context: str = ""
    segment_indices: List[int] = field(default_factory=list)
    match_kind: str = "full_name"


def is_generic_speaker_label(name: str) -> bool:
    """Return True if a speaker label is empty, numeric, or an auto-generated placeholder."""
    clean = str(name or "").strip()
    if not clean:
        return True
    low = clean.casefold()
    if low in {"speaker", "unknown", "unknown speaker", "unassigned"}:
        return True
    return any(pat.match(clean) for pat in _GENERIC_SPEAKER_PATTERNS)


def is_generic_role_label(name: str) -> bool:
    """Return True for placeholder speaker IDs or generic role words like 'Host' or 'Guest'."""
    if is_generic_speaker_label(name):
        return True
    return str(name or "").strip().casefold() in _GENERIC_ROLE_LABELS


def preserve_case_replace(matched: str, replacement: str) -> str:
    """Preserve uppercase/title-case style when replacing matched text with a proper noun.

    Examples:
        preserve_case_replace("ife", "Iffy") -> "Iffy"
        preserve_case_replace("IFE", "Iffy") -> "IFFY"
        preserve_case_replace("hello", "world") -> "world"
        preserve_case_replace("Hello", "world") -> "World"
        preserve_case_replace("HELLO", "world") -> "WORLD"
    """
    if not matched or not replacement:
        return replacement
    alpha_matched = "".join(ch for ch in matched if ch.isalpha())
    if not alpha_matched:
        return replacement
    if alpha_matched.isupper() and (len(alpha_matched) >= 2 or replacement.islower()):
        return replacement.upper()
    if matched.istitle() and replacement.islower():
        return replacement.title()
    return replacement


def _ascii_letters_lower(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", str(text or ""))
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z]", "", ascii_only.lower())


def phonetic_norm(token: str) -> str:
    """Normalize English/broadcast ASR consonant & vowel spellings to a canonical phonetic key."""
    s = _ascii_letters_lower(token)
    if not s:
        return ""
    s = s.replace("ph", "f")
    s = s.replace("kh", "k")
    s = s.replace("gh", "g")
    s = s.replace("ck", "k")
    s = s.replace("qu", "kw")
    s = s.replace("q", "k")
    s = s.replace("x", "ks")
    s = re.sub(r"c(?=[eiy])", "s", s)
    s = s.replace("c", "k")
    s = s.replace("z", "s")
    s = s.replace("eur", "er")
    s = s.replace("our", "er")
    s = s.replace("ee", "i")
    s = s.replace("oo", "u")
    s = s.replace("aa", "a")
    s = re.sub(r"(?:ey|ay|ie)$", "i", s)
    s = s.replace("y", "i")
    s = re.sub(r"(.)\1+", r"\1", s)
    return s


def _voice_neutral(pnorm: str) -> str:
    """Map voiced consonants to their unvoiced counterparts for final-stop resilience (e.g. Fahad/fahat)."""
    return pnorm.replace("d", "t").replace("b", "p").replace("g", "k").replace("v", "f")


def consonant_skeleton(token: str) -> str:
    """Keep initial letter plus non-vowel skeleton after phonetic normalization."""
    p = phonetic_norm(token)
    if not p:
        return ""
    head = p[0]
    tail = "".join(ch for ch in p[1:] if ch not in "aeiou")
    return re.sub(r"(.)\1+", r"\1", head + tail)


def phonetic_soundex(token: str) -> str:
    """Compute Soundex over phonetic_norm(token) so C/K/Q and PH/F share buckets."""
    p = phonetic_norm(token)
    if not p:
        return ""
    first = p[0].upper()
    digits: List[str] = []
    last_code = _SOUNDEX_MAP.get(p[0], "")
    for ch in p[1:]:
        code = _SOUNDEX_MAP.get(ch, "")
        if code:
            if code != last_code:
                digits.append(code)
            last_code = code
        else:
            # Treat h/w as transparent in classic Soundex while vowels separate identical codes
            if ch not in ("h", "w"):
                last_code = ""
    return (first + "".join(digits) + "000")[:4]


def name_similarity(candidate: str, target: str) -> float:
    """Return [0.0, 1.0] similarity blending spelling, phonetic folding, consonant skeleton, and Soundex."""
    c_raw = _ascii_letters_lower(candidate)
    t_raw = _ascii_letters_lower(target)
    if not c_raw or not t_raw:
        return 0.0
    if c_raw == t_raw:
        return 1.0

    c_phon = phonetic_norm(c_raw)
    t_phon = phonetic_norm(t_raw)
    if c_phon == t_phon and c_phon:
        return 0.99

    if _voice_neutral(c_phon) == _voice_neutral(t_phon) and c_phon:
        return 0.96

    raw_ratio = SequenceMatcher(None, c_raw, t_raw).ratio()
    phon_ratio = SequenceMatcher(None, c_phon, t_phon).ratio() if (c_phon and t_phon) else 0.0
    skel_c = consonant_skeleton(c_raw)
    skel_t = consonant_skeleton(t_raw)
    skel_ratio = SequenceMatcher(None, skel_c, skel_t).ratio() if (skel_c and skel_t) else 0.0
    sdx_c = phonetic_soundex(c_raw)
    sdx_t = phonetic_soundex(t_raw)
    soundex_same = bool(sdx_c and sdx_c == sdx_t)

    score = max(raw_ratio, phon_ratio * 0.98)
    if soundex_same:
        phonetic_blend = (0.40 * phon_ratio) + (0.35 * skel_ratio) + 0.25
        score = max(score, min(0.95, phonetic_blend))
    elif skel_c == skel_t and len(skel_c) >= 2:
        score = max(score, 0.88 * max(phon_ratio, 0.72) + 0.12)

    return round(min(1.0, max(0.0, score)), 4)


def extract_confirmed_speaker_names(main_win: Any) -> List[str]:
    """Collect confirmed non-generic speaker display names from a project window or state object."""
    if not main_win:
        return []
    candidates: List[str] = []
    transcript = getattr(main_win, "transcript", None)
    segments = transcript.get("segments", []) if isinstance(transcript, dict) else []
    get_eff = getattr(main_win, "get_effective_speaker_name", None)
    for idx, seg in enumerate(segments):
        if callable(get_eff):
            eff = get_eff(idx, seg)
        else:
            eff = seg.get("speaker", "")
        if eff:
            candidates.append(str(eff).strip())

    spk_names = getattr(main_win, "speaker_names", None)
    if isinstance(spk_names, dict):
        for val in spk_names.values():
            if val:
                candidates.append(str(val).strip())

    seen: Set[str] = set()
    result: List[str] = []
    for name in candidates:
        if len(name) < 3 or is_generic_role_label(name):
            continue
        key = name.casefold()
        if key not in seen:
            seen.add(key)
            result.append(name)
    return result


def _split_name_parts(name: str) -> List[str]:
    return [p for p in _SPLIT_NAME_PARTS_RE.split(str(name or "").strip()) if len(p) >= 2]


def _make_context_snippet(text: str, start: int, end: int, radius: int = 28) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    snippet = text[left:right].replace("\n", " ").strip()
    if left > 0:
        snippet = "..." + snippet
    if right < len(text):
        snippet = snippet + "..."
    return snippet


def _span_overlaps(span: Tuple[int, int], covered: Sequence[Tuple[int, int]]) -> bool:
    s0, e0 = span
    return any(not (e0 <= s1 or s0 >= e1) for s1, e1 in covered)


def _needs_case_or_spelling_fix(found_phrase: str, target_name: str) -> bool:
    if found_phrase == target_name:
        return False
    if found_phrase.upper() == target_name.upper():
        return False
    # Exact letters ignoring hyphen/spaces (e.g. "raquel ramseur webb" -> needs Fix!)
    return True


def _phrase_similarity(found_words: Sequence[str], target_parts: Sequence[str]) -> float:
    if not found_words or not target_parts:
        return 0.0
    if len(found_words) == len(target_parts):
        part_scores = [name_similarity(fw, tp) for fw, tp in zip(found_words, target_parts)]
        min_part = min(part_scores)
        avg_part = sum(part_scores) / len(part_scores)
        joined_found = "".join(_ascii_letters_lower(w) for w in found_words)
        joined_target = "".join(_ascii_letters_lower(t) for t in target_parts)
        joined_sim = name_similarity(joined_found, joined_target)
        # Require at least one strong anchor match (>= 0.85) so two random words do not trigger
        if max(part_scores) < 0.85 or min_part < 0.58:
            return 0.0
        return round((0.65 * avg_part) + (0.35 * joined_sim), 4)
    return 0.0


def find_misspelled_speaker_names(
    segments: Sequence[Dict[str, Any]],
    confirmed_names: Sequence[str],
    min_score: float = 0.76,
) -> List[SpeakerNameCandidate]:
    """Scan transcript segments for likely ASR misspellings of confirmed speaker names."""
    clean_confirmed = [str(n).strip() for n in confirmed_names if str(n).strip() and not is_generic_role_label(n)]
    if not segments or not clean_confirmed:
        return []

    multi_targets: List[Tuple[str, List[str]]] = []
    single_targets: List[Tuple[str, str]] = []
    seen_single: Set[str] = set()
    confirmed_token_cf: Set[str] = set()

    for full_name in clean_confirmed:
        parts = _split_name_parts(full_name)
        for p in parts:
            confirmed_token_cf.add(p.casefold())
        if len(parts) >= 2:
            multi_targets.append((full_name, parts))
        for p in parts:
            if len(p) >= 3 and p.casefold() not in _COMMON_ENGLISH_STOPWORDS:
                key = f"{p.casefold()}->{p}"
                if key not in seen_single:
                    seen_single.add(key)
                    single_targets.append((p, p))

    grouped: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def _record_hit(found: str, target: str, score: float, seg_idx: int, context: str, kind: str) -> None:
        key = (found.casefold(), target)
        entry = grouped.get(key)
        if entry is None:
            grouped[key] = {
                "variant_counts": {found: 1},
                "suggested_name": target,
                "count": 1,
                "score": score,
                "sample_context": context,
                "segment_indices": [seg_idx],
                "match_kind": kind,
            }
        else:
            entry["count"] += 1
            entry["variant_counts"][found] = entry["variant_counts"].get(found, 0) + 1
            if score > entry["score"]:
                entry["score"] = score
            if seg_idx not in entry["segment_indices"]:
                entry["segment_indices"].append(seg_idx)

    for seg_idx, seg in enumerate(segments):
        text = str(seg.get("text", "") or "")
        if not text:
            continue
        word_matches = [(m.group(0), m.start(), m.end()) for m in _WORD_SPAN_RE.finditer(text)]
        if not word_matches:
            continue

        # Flatten hyphenated words for multi-word window matching while preserving original offsets
        covered_spans: List[Tuple[int, int]] = []

        # Phase 1: Multi-word full guest/host names first
        for target_name, target_parts in sorted(multi_targets, key=lambda item: -len(item[1])):
            n_parts = len(target_parts)
            # Match either consecutive word tokens (n_parts) or hyphen-split expansions
            for i in range(len(word_matches)):
                window_words: List[str] = []
                end_word_idx = i
                for j in range(i, min(len(word_matches), i + n_parts)):
                    tok = word_matches[j][0]
                    sub_parts = _split_name_parts(tok)
                    window_words.extend(sub_parts if sub_parts else [tok])
                    end_word_idx = j
                    if len(window_words) >= n_parts:
                        break
                if len(window_words) != n_parts:
                    continue
                if all(_ascii_letters_lower(w) in _COMMON_ENGLISH_STOPWORDS for w in window_words):
                    continue
                span = (word_matches[i][1], word_matches[end_word_idx][2])
                if _span_overlaps(span, covered_spans):
                    continue
                found_phrase = text[span[0]:span[1]]
                if not _needs_case_or_spelling_fix(found_phrase, target_name):
                    if _phrase_similarity(window_words, target_parts) >= 0.99:
                        covered_spans.append(span)
                    continue
                score = _phrase_similarity(window_words, target_parts)
                if score >= max(0.74, min_score - 0.02):
                    covered_spans.append(span)
                    _record_hit(
                        found=found_phrase,
                        target=target_name,
                        score=score,
                        seg_idx=seg_idx,
                        context=_make_context_snippet(text, span[0], span[1]),
                        kind="full_name",
                    )

        # Phase 2: Single-word distinct proper nouns outside covered multi-word spans
        for cand_word, s_pos, e_pos in word_matches:
            if _span_overlaps((s_pos, e_pos), covered_spans):
                continue
            cand_clean = _ascii_letters_lower(cand_word)
            if len(cand_clean) < 3 or cand_clean in _COMMON_ENGLISH_STOPWORDS:
                continue
            # If the word already matches ANY confirmed speaker token cleanly in casing, leave it alone
            if cand_clean in confirmed_token_cf:
                matching_proper = [t for t, _ in single_targets if t.casefold() == cand_clean]
                if any(cand_word == t or cand_word.upper() == t.upper() for t in matching_proper):
                    continue

            best_target = None
            best_score = 0.0
            for target_tok, _ in single_targets:
                if abs(len(cand_clean) - len(_ascii_letters_lower(target_tok))) > 3:
                    continue
                req = 0.82 if len(cand_clean) == 3 else max(0.78, min_score)
                sim = name_similarity(cand_word, target_tok)
                if sim < req:
                    continue
                c_pn = phonetic_norm(cand_word)
                t_pn = phonetic_norm(target_tok)
                first_agree = bool(c_pn and t_pn and c_pn[0] == t_pn[0])
                phon_sim = SequenceMatcher(None, c_pn, t_pn).ratio() if (c_pn and t_pn) else 0.0
                if not first_agree and phon_sim < 0.85:
                    continue
                if sim > best_score:
                    best_score = sim
                    best_target = target_tok

            if best_target and _needs_case_or_spelling_fix(cand_word, best_target):
                _record_hit(
                    found=cand_word,
                    target=best_target,
                    score=best_score,
                    seg_idx=seg_idx,
                    context=_make_context_snippet(text, s_pos, e_pos),
                    kind="part_name",
                )

    candidates: List[SpeakerNameCandidate] = []
    for entry in grouped.values():
        rep_found = max(entry["variant_counts"].items(), key=lambda kv: kv[1])[0]
        candidates.append(
            SpeakerNameCandidate(
                found_text=rep_found,
                suggested_name=entry["suggested_name"],
                count=entry["count"],
                score=entry["score"],
                sample_context=entry["sample_context"],
                segment_indices=entry["segment_indices"],
                match_kind=entry["match_kind"],
            )
        )

    candidates.sort(
        key=lambda c: (0 if c.match_kind == "full_name" else 1, -c.count, -c.score, c.found_text.lower())
    )
    return candidates


def apply_bulk_text_replacements(
    segments: Sequence[Dict[str, Any]],
    replacements: Sequence[Tuple[str, str]],
    preserve_case: bool = True,
    sync_words_cb: Optional[Callable[[Dict[str, Any], str], Any]] = None,
    transcript: Optional[Dict[str, Any]] = None,
    translations: Optional[Dict[str, Any]] = None,
) -> Tuple[int, int]:
    """Apply whole-word replacements across transcript segments, full text, and translations.

    Returns ``(total_occurrences_replaced, segments_modified_count)``.
    """
    cleaned_pairs: List[Tuple[str, str]] = []
    seen_pairs: Set[Tuple[str, str]] = set()
    for found, repl in replacements:
        f_str = str(found or "").strip()
        r_str = str(repl or "").strip()
        if not f_str or not r_str or f_str == r_str:
            continue
        key = (f_str.casefold(), r_str)
        if key not in seen_pairs:
            seen_pairs.add(key)
            cleaned_pairs.append((f_str, r_str))

    if not cleaned_pairs:
        return 0, 0

    cleaned_pairs.sort(key=lambda pair: -len(pair[0]))
    compiled = [
        (re.compile(rf"(?<!\w){re.escape(f_str)}(?!\w)", re.IGNORECASE), r_str)
        for f_str, r_str in cleaned_pairs
    ]

    total_hits = 0
    modified_segs = 0

    def _sub_text(raw_text: str) -> Tuple[str, int]:
        hits = 0
        updated = raw_text
        for pat, repl_target in compiled:
            if pat.search(updated):
                updated, n = pat.subn(
                    lambda m, tgt=repl_target: preserve_case_replace(m.group(0), tgt) if preserve_case else tgt,
                    updated,
                )
                hits += n
        return updated, hits

    for seg in segments:
        old_text = str(seg.get("text", "") or "")
        if not old_text:
            continue
        new_text, hits = _sub_text(old_text)
        if hits > 0 and new_text != old_text:
            seg["text"] = new_text
            if callable(sync_words_cb):
                sync_words_cb(seg, new_text)
            total_hits += hits
            modified_segs += 1

    if isinstance(transcript, dict) and isinstance(transcript.get("text"), str):
        new_full, _ = _sub_text(transcript["text"])
        transcript["text"] = new_full

    if isinstance(translations, dict):
        for t_item in translations.values():
            if not isinstance(t_item, dict):
                continue
            for t_seg in t_item.get("segments", []):
                old_t = str(t_seg.get("text", "") or "")
                if old_t:
                    new_t, _ = _sub_text(old_t)
                    if new_t != old_t:
                        t_seg["text"] = new_t
            if isinstance(t_item.get("text"), str):
                new_t_full, _ = _sub_text(t_item["text"])
                t_item["text"] = new_t_full

    return total_hits, modified_segs
