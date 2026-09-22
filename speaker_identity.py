"""
Radio & TV Segmenter
Robust acoustic speaker identification using WeSpeaker embeddings.

This module is deliberately independent of the diarization engine.

Diarization answers:
    "Which acoustic regions belong together?"

Speaker identification answers:
    "Which of those regions sound like this known speaker?"

The two operations should not share the same cluster centroid.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

import math


VECTOR_DIMENSION = 256

# A reference profile should not be built from hundreds of turns.
MAX_PROFILE_SAMPLES = 8

# Minimum number of acoustically similar samples to use when available.
MIN_PROFILE_SAMPLES = 2

# Baseline similarity required for an external candidate sample to participate
# in iterative profile refinement. WeSpeaker 256-d embeddings in broadcast
# audio frequently have a 0.65-0.72 cross-speaker floor. Never allow candidates
# below 0.80 to dilute an explicitly confirmed reference voice.
DEFAULT_SEED_SIMILARITY = 0.80

# Minimum separation between a target match and its strongest competing
# profile.
DEFAULT_MATCH_MARGIN = 0.04


@dataclass
class VoiceMatch:
    similarity: float
    margin: float
    target_similarity: float
    competitor_similarity: float


def _as_vector(value) -> Optional[List[float]]:
    if not isinstance(value, (list, tuple)):
        return None

    try:
        vector = [float(x) for x in value]
    except (TypeError, ValueError):
        return None

    if len(vector) != VECTOR_DIMENSION:
        return None

    norm = math.sqrt(sum(x * x for x in vector))
    if norm <= 1e-9:
        return None

    return [x / norm for x in vector]


def cosine_similarity(
    a: Optional[Sequence[float]],
    b: Optional[Sequence[float]],
) -> float:
    """
    Cosine similarity for already-normalized or arbitrary vectors.

    Returns 0.0 when either vector is invalid.
    """
    va = _as_vector(a)
    vb = _as_vector(b)

    if va is None or vb is None:
        return 0.0

    return max(
        -1.0,
        min(1.0, sum(x * y for x, y in zip(va, vb))),
    )


def normalize_vector(vector: Sequence[float]) -> Optional[List[float]]:
    return _as_vector(vector)


def centroid(vectors: Iterable[Sequence[float]]) -> Optional[List[float]]:
    """
    Calculate a normalized centroid from valid embeddings.

    Every vector is normalized before averaging so a high-energy sample
    cannot dominate the profile.
    """
    valid = []

    for vector in vectors:
        normalized = _as_vector(vector)
        if normalized is not None:
            valid.append(normalized)

    if not valid:
        return None

    result = [
        sum(vector[i] for vector in valid)
        for i in range(VECTOR_DIMENSION)
    ]

    return _as_vector(result)


def robust_reference_profile(
    seed_vectors: Sequence[Sequence[float]],
    candidate_vectors: Sequence[Sequence[float]] = (),
    *,
    max_samples: int = MAX_PROFILE_SAMPLES,
    min_samples: int = MIN_PROFILE_SAMPLES,
    seed_similarity: float = DEFAULT_SEED_SIMILARITY,
) -> Tuple[Optional[List[float]], List[int]]:
    """
    Build a speaker profile without blindly averaging an existing cluster.

    Algorithm:
      1. Start with explicitly supplied reference vectors.
      2. Build an initial centroid strictly from reference vectors.
      3. Score candidate vectors against that centroid using a strict similarity gate.
      4. Keep only candidates that match the reference with high confidence.
      5. Recalculate the centroid.
      6. Perform one more refinement pass.

    This prevents an incorrectly assigned speaker from poisoning the profile.
    """
    initial = []

    for vector in seed_vectors:
        normalized = _as_vector(vector)
        if normalized is not None:
            initial.append(normalized)

    if not initial:
        return None, []

    profile = centroid(initial)

    if profile is None:
        return None, []

    if not candidate_vectors:
        return profile, []

    scored = []

    for idx, vector in enumerate(candidate_vectors):
        normalized = _as_vector(vector)

        if normalized is None:
            continue

        similarity = cosine_similarity(profile, normalized)

        # Candidate must pass strict threshold to be considered same speaker
        if similarity >= seed_similarity:
            scored.append((similarity, idx, normalized))

    scored.sort(key=lambda item: item[0], reverse=True)

    selected = scored[:max_samples]

    if len(selected) >= min_samples:
        profile_vectors = initial + [item[2] for item in selected]
    else:
        # Retain explicit references rather than pulling questionable material
        profile_vectors = initial

    refined = centroid(profile_vectors)

    if refined is None:
        return profile, [item[1] for item in selected]

    # One additional pass to prune candidates that drifted from refined centroid
    rescored = []

    for similarity, idx, vector in selected:
        new_similarity = cosine_similarity(refined, vector)
        if new_similarity >= seed_similarity:
            rescored.append((new_similarity, idx, vector))

    rescored.sort(key=lambda item: item[0], reverse=True)

    refined_selection = rescored[:max_samples]

    if len(refined_selection) >= min_samples:
        final_vectors = initial + [item[2] for item in refined_selection]
        final_profile = centroid(final_vectors)

        if final_profile is not None:
            return (
                final_profile,
                [item[1] for item in refined_selection],
            )

    return refined, [item[1] for item in refined_selection]


def compare_against_profiles(
    vector: Sequence[float],
    target_profile: Sequence[float],
    competitor_profiles: Sequence[Sequence[float]] = (),
) -> VoiceMatch:
    """
    Compare a candidate against the target speaker and all competing profiles.
    """
    target_similarity = cosine_similarity(vector, target_profile)

    competitor_similarity = 0.0

    for profile in competitor_profiles:
        competitor_similarity = max(
            competitor_similarity,
            cosine_similarity(vector, profile),
        )

    # Margin reflects distance ahead of the closest competitor
    margin = target_similarity - competitor_similarity

    return VoiceMatch(
        similarity=target_similarity,
        margin=margin,
        target_similarity=target_similarity,
        competitor_similarity=competitor_similarity,
    )


def is_confident_match(
    result: VoiceMatch,
    *,
    threshold: float = 0.78,
    margin: float = DEFAULT_MATCH_MARGIN,
    has_competitors: bool = True,
) -> bool:
    """
    Require both:
      target similarity >= threshold
      AND (if competitors are known) target similarity sufficiently exceeds them.
    """
    if result.target_similarity < threshold:
        return False

    if has_competitors and result.margin < margin:
        return False

    return True