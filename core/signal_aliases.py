"""
Signal deduplication: alias map + recategorization rules.

Used by:
  - scripts/apply_signal_aliases.py  (one-time backfill)
  - pipeline Phase 3 labeling        (ongoing normalization)
"""

# ---------------------------------------------------------------------------
# ALIASES: variant -> canonical (per category, case-insensitive lookup)
# ---------------------------------------------------------------------------
SIGNAL_ALIASES: dict[str, dict[str, str]] = {
    "persons": {
        "ZELENSKY": "Zelenskyy",
        "ZELENSKIY": "Zelenskyy",
        "SISI": "El-Sisi",
        "LE_PEN": "Le Pen",
    },
    "orgs": {
        "SUPREME_COURT": "Supreme Court",
        "GOLDMAN_SACHS": "Goldman Sachs",
        "ISLAMIC_STATE": "ISIS",
        "DAESH": "ISIS",
    },
    "places": {
        "Kiev": "Kyiv",
    },
    "commodities": {
        "crude oil": "oil",
        "gas": "natural gas",
        "LNG": "natural gas",
        "arms": "weapons",
        "ammunition": "weapons",
        "milk": "dairy",
        "meat": "beef",
        "cars": "vehicles",
        "electric vehicles": "vehicles",
        "diesel": "petroleum",
        "gasoline": "petroleum",
        "rare earth metals": "rare earths",
    },
    "policies": {
        "negotiations": "diplomacy",
        "peace talks": "diplomacy",
        "talks": "diplomacy",
        "peace": "diplomacy",
        "dialogue": "diplomacy",
        "deal": "diplomacy",
        "peace plan": "diplomacy",
        "de-escalation": "diplomacy",
        "nuclear talks": "nuclear deal",
        "new start": "nuclear deal",
        "trade deal": "trade agreement",
        "immigration": "migration",
        "partnership": "cooperation",
    },
    "systems": {
        "drone": "drones",
        "Grok AI": "Grok",
        "GROK": "Grok",
        "Druzhba": "Druzhba pipeline",
    },
    "named_events": {
        "Olympics": "Olympic Games",
        "Olympic": "Olympic Games",
        "Olympic Winter Games": "Olympic Games",
        "Winter Olympics": "Olympic Games",
        "Winter Games": "Olympic Games",
        "Davos": "World Economic Forum",
        "WEF": "World Economic Forum",
        "Grammy": "Grammys",
        "Munich Conference": "Munich Security Conference",
        "AI Impact Summit": "AI Summit",
        "India AI Impact Summit": "AI Summit",
    },
}

# ---------------------------------------------------------------------------
# MOVES: signals in the wrong category -> (target_category, canonical_name)
# ---------------------------------------------------------------------------
SIGNAL_MOVES: dict[str, dict[str, tuple[str, str]]] = {
    "orgs": {
        "UAE": ("places", "UAE"),
        "DeepSeek": ("systems", "DeepSeek"),
        "ChatGPT": ("systems", "ChatGPT"),
    },
}

# Build case-insensitive lookup (lowered key -> canonical)
_ALIAS_LOOKUP: dict[str, dict[str, str]] = {}
for _cat, _mapping in SIGNAL_ALIASES.items():
    _ALIAS_LOOKUP[_cat] = {k.lower(): v for k, v in _mapping.items()}

_MOVE_LOOKUP: dict[str, dict[str, tuple[str, str]]] = {}
for _cat, _mapping in SIGNAL_MOVES.items():
    _MOVE_LOOKUP[_cat] = {k.lower(): v for k, v in _mapping.items()}


def normalize_signals(
    category: str, values: list[str] | None
) -> tuple[list[str], dict[str, list[str]]]:
    """Normalize a list of signal values for a given category.

    Returns:
        (normalized_values, moves_dict)
        - normalized_values: deduplicated list with aliases resolved
        - moves_dict: {target_category: [values]} for signals that belong elsewhere
    """
    if not values:
        return [], {}

    lookup = _ALIAS_LOOKUP.get(category, {})
    move_lookup = _MOVE_LOOKUP.get(category, {})

    normalized = []
    moves: dict[str, list[str]] = {}
    seen: set[str] = set()

    for v in values:
        low = v.lower()

        # Check if this signal should move to another category
        if low in move_lookup:
            target_cat, canonical = move_lookup[low]
            moves.setdefault(target_cat, [])
            if canonical.lower() not in {x.lower() for x in moves[target_cat]}:
                moves[target_cat].append(canonical)
            continue

        # Apply alias
        canonical = lookup.get(low, v)
        if canonical.lower() not in seen:
            seen.add(canonical.lower())
            normalized.append(canonical)

    return normalized, moves
