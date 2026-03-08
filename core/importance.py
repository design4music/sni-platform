"""Event importance scoring for WorldBrief pipeline.

Computes importance scores at two levels:
- Title-level: after Phase 3.1, using label data + title metadata (no DB queries)
- Event-level: after Phase 4, aggregating title scores + event-level features
"""

import re

from core.config import (
    ACTION_CLASS_SEVERITY,
    ESCALATION_ACTION_CLASSES,
    EXECUTIVE_ACTOR_PATTERNS,
    SIGNAL_TYPES,
)

# ---------------------------------------------------------------------------
# Scale / casualty language patterns (Feature 5)
# ---------------------------------------------------------------------------

_CASUALTY_VERBS = (
    r"killed|killing|kills|dead|die|dies|died|wounded|injured|displaced|missing"
    r"|massacred|slaughtered|executed"
)

# Pattern A: NUMBER ... VERB  ("160 children killed", "at least 50 dead")
_CASUALTY_RE_A = re.compile(
    r"\b(\d{2,})\s+(?:\w+\s+){0,3}" r"(" + _CASUALTY_VERBS + r")\b",
    re.IGNORECASE,
)

# Pattern B: VERB NUMBER  ("killing 160", "kills 30", "wounded 12")
_CASUALTY_RE_B = re.compile(
    r"\b(" + _CASUALTY_VERBS + r")\s+(?:\w+\s+){0,2}" r"(\d{2,})\b",
    re.IGNORECASE,
)

# High-severity standalone keywords
_SCALE_KEYWORDS = frozenset(
    {
        "state of emergency",
        "martial law",
        "declaration of war",
        "declares war",
        "declared war",
        "invasion",
        "invades",
        "invaded",
        "coup",
        "genocide",
        "massacre",
        "nuclear strike",
        "nuclear attack",
        "ethnic cleansing",
        "war crimes",
        "chemical attack",
        "airstrike",
        "airstrikes",
        "bombing",
        "bombed",
        "assassination",
        "assassinated",
    }
)

# Medium-severity keywords
_SCALE_KEYWORDS_MEDIUM = frozenset(
    {
        "earthquake",
        "tsunami",
        "hurricane",
        "typhoon",
        "cyclone",
        "famine",
        "pandemic",
        "epidemic",
        "collapse",
        "crashed",
        "explosion",
        "hostages",
        "kidnapped",
        "abducted",
        "siege",
        "ceasefire",
        "truce",
        "surrender",
        "capitulation",
    }
)


def _score_scale_language(title: str) -> float:
    """Score title for casualty/scale language. Returns 0.0-1.0."""
    title_lower = title.lower()

    # Casualty pattern with numbers (both orderings)
    count = None
    m = _CASUALTY_RE_A.search(title)
    if m:
        count = int(m.group(1))
    else:
        m = _CASUALTY_RE_B.search(title)
        if m:
            count = int(m.group(2))

    if count is not None:
        if count >= 100:
            return 1.0
        if count >= 10:
            return 0.7
        return 0.4

    # High-severity keywords
    for kw in _SCALE_KEYWORDS:
        if kw in title_lower:
            return 0.8

    # Medium-severity keywords
    for kw in _SCALE_KEYWORDS_MEDIUM:
        if kw in title_lower:
            return 0.4

    return 0.0


# ---------------------------------------------------------------------------
# Title-level scoring (Feature 2, 3, 5, 6, 9)
# ---------------------------------------------------------------------------


def score_title(title_display, centroid_ids, action_class, actor, label_signals):
    """Compute title importance from already-loaded data. No DB queries.

    Args:
        title_display: headline text
        centroid_ids: list of matched centroid IDs from Phase 2
        action_class: e.g. "MILITARY_OPERATION" from title_labels
        actor: e.g. "US_EXECUTIVE" from title_labels
        label_signals: dict of signal arrays {persons: [...], orgs: [...], ...}

    Returns: (composite_score: float, components: dict)
    """
    # Feature 2: Multi-centroid convergence
    n_centroids = len(centroid_ids) if centroid_ids else 0
    centroid_convergence = min(n_centroids / 5.0, 1.0)

    # Feature 3: Action class severity
    action_severity = ACTION_CLASS_SEVERITY.get(action_class or "", 0.0)

    # Feature 5: Casualty / scale language
    scale_language = _score_scale_language(title_display or "")

    # Feature 6: Actor escalation (head of state + coercive/strategic action)
    actor_escalation = 0.0
    if actor and action_class:
        is_executive = any(p in actor for p in EXECUTIVE_ACTOR_PATTERNS)
        is_escalation_action = action_class in ESCALATION_ACTION_CLASSES
        if is_executive and is_escalation_action:
            actor_escalation = 1.0
        elif is_executive:
            actor_escalation = 0.3

    # Feature 9: Signal density (how entity-rich is this title?)
    filled = 0
    total_entities = 0
    for st in SIGNAL_TYPES:
        arr = label_signals.get(st) or []
        if arr:
            filled += 1
            total_entities += len(arr)
    signal_density = min(filled / 5.0, 1.0)  # 5+ signal types = max

    # Composite
    score = (
        0.15 * centroid_convergence
        + 0.25 * action_severity
        + 0.25 * scale_language
        + 0.20 * actor_escalation
        + 0.15 * signal_density
    )

    components = {
        "centroid_convergence": round(centroid_convergence, 3),
        "action_severity": round(action_severity, 3),
        "scale_language": round(scale_language, 3),
        "actor_escalation": round(actor_escalation, 3),
        "signal_density": round(signal_density, 3),
    }

    return round(score, 4), components


# ---------------------------------------------------------------------------
# Event-level scoring (Features 1, 4, 8 + title aggregation)
# ---------------------------------------------------------------------------


def score_event(title_rows):
    """Compute event importance from its constituent titles.

    Args:
        title_rows: list of dicts, each with:
            - importance_score (float or None)
            - publisher_name (str)
            - detected_language (str)
            - pubdate_utc (datetime)
            - track (str, from title_assignments)

    Returns: (composite_score: float, components: dict)
    """
    if not title_rows:
        return 0.0, {}

    n = len(title_rows)

    # Title score aggregate (p90 of title-level importance)
    title_scores = sorted(
        [r["importance_score"] for r in title_rows if r.get("importance_score")],
        reverse=True,
    )
    if title_scores:
        p90_idx = max(0, int(len(title_scores) * 0.1))
        title_p90 = title_scores[p90_idx]
    else:
        title_p90 = 0.0

    # Feature 1: Multi-source velocity (max titles in any 6h window)
    velocity = _compute_velocity(title_rows)

    # Feature 4: Cross-track resonance
    tracks = {r["track"] for r in title_rows if r.get("track")}
    cross_track = min((len(tracks) - 1) / 2.0, 1.0) if len(tracks) > 1 else 0.0

    # Feature 8: Source diversity
    publishers = {r["publisher_name"] for r in title_rows if r.get("publisher_name")}
    languages = {
        r["detected_language"] for r in title_rows if r.get("detected_language")
    }
    source_diversity = (
        min(len(publishers) / 10.0, 1.0) * 0.7 + min(len(languages) / 4.0, 1.0) * 0.3
    )

    # Event size factor
    size_factor = min(n / 20.0, 1.0)

    # Composite
    score = (
        0.30 * title_p90
        + 0.25 * velocity
        + 0.15 * cross_track
        + 0.15 * source_diversity
        + 0.15 * size_factor
    )

    components = {
        "title_p90": round(title_p90, 3),
        "velocity": round(velocity, 3),
        "cross_track": round(cross_track, 3),
        "source_diversity": round(source_diversity, 3),
        "size_factor": round(size_factor, 3),
        "title_count": n,
        "unique_publishers": len(publishers),
        "unique_languages": len(languages),
    }

    return round(score, 4), components


def _compute_velocity(title_rows):
    """Max number of titles arriving in any 6-hour window, normalized."""
    dates = sorted([r["pubdate_utc"] for r in title_rows if r.get("pubdate_utc")])
    if len(dates) < 2:
        return 0.0

    from datetime import timedelta

    window = timedelta(hours=6)
    max_count = 1
    for i, start in enumerate(dates):
        count = 0
        for d in dates[i:]:
            if d - start <= window:
                count += 1
            else:
                break
        if count > max_count:
            max_count = count

    return min(max_count / 10.0, 1.0)
