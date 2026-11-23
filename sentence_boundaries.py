"""Context-aware sentence-boundary and abbreviation detection for Radio & TV Segmenter.

Provides pure-Python classification distinguishing true terminal sentence punctuation
from pre-noun titles, honorifics, initials, connectors, date/number prefixes, and
ambiguous abbreviations across English and Spanish broadcast transcripts.
"""
from __future__ import annotations

import re
from typing import Any, Optional

# Group 1: Always pre-noun titles & honorifics (case-insensitive)
ALWAYS_PRE_NOUN_TITLES = frozenset({
    "mr.", "mrs.", "ms.", "mx.", "dr.", "prof.", "rev.", "fr.", "msgr.", "hon.",
    "messrs.", "mme.", "mlle.",
    "sra.", "srta.", "dra.", "profa.", "lic.", "ing.", "arq.", "gral.", "tte.",
    "sto.", "sta.",
})

# Group 2: Civic, political, military, legal & geographic prefixes (must be capitalized)
CAPITALIZED_PRE_NOUN_TITLES = frozenset({
    "gov.", "sen.", "rep.", "pres.", "amb.", "del.", "ald.", "det.", "supt.",
    "atty.", "insp.", "gen.", "col.", "lt.", "capt.", "sgt.", "cpl.", "maj.",
    "adm.", "cmdr.", "pvt.", "cdr.", "st.", "mt.", "ft.",
})

# Group 3a: Mid-clause connectors & Latin/reference abbreviations (case-insensitive)
MID_CLAUSE_CONNECTORS = frozenset({
    "vs.", "v.", "e.g.", "i.e.", "cf.", "approx.",
})

# Group 3b: Calendar month abbreviations (must be capitalized + followed by digit or lowercase)
MONTH_ABBREVS = frozenset({
    "jan.", "feb.", "mar.", "apr.", "jun.", "jul.", "aug.", "sep.", "sept.",
    "oct.", "nov.", "dec.",
})

# Group 3c: Number/section prefixes (only non-terminal when followed by a digit)
NUMBER_PREFIX_ABBREVS = frozenset({
    "no.", "vol.", "ch.", "fig.", "eq.", "art.", "sec.",
})

# Group 4: Ambiguous abbreviations & dotted acronyms that may end or continue a sentence
AMBIGUOUS_ABBREVS = frozenset({
    "u.s.", "u.s.a.", "u.k.", "d.c.", "e.u.", "u.n.",
    "ph.d.", "m.d.", "b.a.", "m.a.", "j.d.",
    "a.m.", "p.m.",
    "jr.", "sr.", "inc.", "corp.", "ltd.", "co.", "llc.",
    "etc.", "ave.", "blvd.", "rd.", "ln.", "ud.", "uds.",
})

_DOTTED_ACRONYM_RE = re.compile(r"^(?:[A-Za-z]\.){2,}$")
_TRAILING_CLOSERS = ' "\'\u201c\u201d\u2018\u2019\u00bb)]'
_LEADING_OPENERS = ' "\'\u201c\u2018\u00ab(['


def _extract_last_word(text: str) -> str:
    cleaned = str(text or "").strip().rstrip(_TRAILING_CLOSERS)
    if not cleaned:
        return ""
    parts = cleaned.split()
    if not parts:
        return ""
    return parts[-1].lstrip(_LEADING_OPENERS)


def is_ambiguous_abbreviation(text: str) -> bool:
    """Return True when text ends with a multi-dot acronym or sentence-finalizable abbreviation."""
    bare = _extract_last_word(text)
    if not bare or not bare.endswith("."):
        return False
    lower = bare.lower()
    if lower in AMBIGUOUS_ABBREVS:
        return True
    return bool(_DOTTED_ACRONYM_RE.fullmatch(bare))


def is_non_terminal_abbreviation(
    text: str,
    next_word: Optional[str] = None,
    language: Optional[str] = None,
) -> bool:
    """Return True when a trailing period belongs to a non-terminal abbreviation rather than sentence end."""
    bare = _extract_last_word(text)
    if not bare or not bare.endswith(".") or bare.endswith(".."):
        return False

    lower = bare.lower()
    nxt = str(next_word or "").lstrip(_LEADING_OPENERS)
    nxt_is_lower = bool(nxt and nxt[0].islower())
    nxt_is_digit = bool(nxt and nxt[0].isdigit())

    if lower in ALWAYS_PRE_NOUN_TITLES:
        return True
    if lower in CAPITALIZED_PRE_NOUN_TITLES and bare[0].isupper():
        return True
    if lower in MID_CLAUSE_CONNECTORS:
        return True
    if len(bare) == 2 and bare[0].isupper() and bare[1] == ".":
        return True
    if lower in MONTH_ABBREVS and bare[0].isupper() and (nxt_is_digit or nxt_is_lower):
        return True
    if lower in NUMBER_PREFIX_ABBREVS and nxt_is_digit:
        return True
    if lower == "sr." and bare[0].isupper() and str(language or "").strip().lower().startswith("es"):
        return True
    if is_ambiguous_abbreviation(bare):
        return nxt_is_lower
    return False


def is_sentence_end(
    text: Any,
    next_word: Optional[str] = None,
    language: Optional[str] = None,
) -> bool:
    """Return True if text terminates a sentence, honoring non-terminal abbreviations and titles."""
    cleaned = str(text or "").strip().rstrip(_TRAILING_CLOSERS)
    if not cleaned:
        return False
    if cleaned.endswith("...") or cleaned.endswith("\u2026"):
        return True
    if cleaned.endswith(("?", "!")):
        return True
    if cleaned.endswith("."):
        return not is_non_terminal_abbreviation(cleaned, next_word=next_word, language=language)
    return False


__all__ = [
    "ALWAYS_PRE_NOUN_TITLES",
    "CAPITALIZED_PRE_NOUN_TITLES",
    "MID_CLAUSE_CONNECTORS",
    "MONTH_ABBREVS",
    "NUMBER_PREFIX_ABBREVS",
    "AMBIGUOUS_ABBREVS",
    "is_ambiguous_abbreviation",
    "is_non_terminal_abbreviation",
    "is_sentence_end",
]
