"""
Micro-Prompt System for EF Enrichment
Bounded, cheap prompts for canonical actors and policy status
"""

from typing import Any, Dict, List

# Micro-Prompt 1: Canonicalize + Roles + Status
CANONICALIZE_SYSTEM_PROMPT = """Extract canonical actor names, roles, and policy status from event data.

ACTORS: Use official names (countries: US/UK/RU/CN, orgs: NATO/UN/EU, people: Last Name)
ROLES: initiator|target|beneficiary|mediator
POLICY_STATUS: proposed|passed|signed|in_force|enforced|suspended|cancelled (only if clear)
TIME_SPAN: best effort start date from content

Keep it factual and concise."""

CANONICALIZE_USER_TEMPLATE = """EF: {ef_title}
TYPE: {event_type} | THEATER: {primary_theater}

KEY TITLES:
{member_titles}

Extract in JSON format:
{{
  "canonical_actors": [
    {{"name": "Official name", "role": "initiator|target|beneficiary|mediator"}}
  ],
  "policy_status": "proposed|passed|signed|in_force|enforced|suspended|cancelled|null",
  "time_span": {{"start": "YYYY-MM-DD", "end": null}},
  "why_strategic": "Brief strategic significance (≤150 chars)"
}}"""


# Micro-Prompt 2: Strategic Context (Optional)
STRATEGIC_CONTEXT_SYSTEM_PROMPT = """Provide one-line strategic context for this event family.

Focus on WHY this matters strategically:
- Regional stability impact
- Alliance/diplomatic implications
- Economic/security consequences
- Precedent-setting nature

Keep under 150 characters."""

STRATEGIC_CONTEXT_USER_TEMPLATE = """Event: {ef_title}
Theater: {primary_theater} | Type: {event_type}

Key actors: {canonical_actors}
Policy status: {policy_status}

Why is this strategically significant? (≤150 chars)"""


def build_canonicalize_prompt(
    ef_title: str,
    event_type: str,
    primary_theater: str,
    member_titles: List[Dict[str, Any]],
) -> tuple[str, str]:
    """
    Build canonicalization prompt for extracting actors, roles, and status

    Args:
        ef_title: Event Family title
        event_type: Event type classification
        primary_theater: Primary theater
        member_titles: List of member title dictionaries

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Format top 5 titles for context (sorted by date)
    sorted_titles = sorted(
        member_titles, key=lambda x: x.get("pubdate_utc", ""), reverse=True
    )[:5]

    formatted_titles = []
    for i, title in enumerate(sorted_titles, 1):
        date_str = title.get("pubdate_utc", "unknown")
        if isinstance(date_str, str) and "T" in date_str:
            date_str = date_str.split("T")[0]
        elif hasattr(date_str, "strftime"):
            date_str = date_str.strftime("%Y-%m-%d")

        formatted_titles.append(
            f"{i}. {title.get('text', title.get('title', ''))} ({date_str})"
        )

    member_titles_text = "\n".join(formatted_titles)

    system = CANONICALIZE_SYSTEM_PROMPT
    user = CANONICALIZE_USER_TEMPLATE.format(
        ef_title=ef_title,
        event_type=event_type,
        primary_theater=primary_theater,
        member_titles=member_titles_text,
    )

    return system, user


def build_strategic_context_prompt(
    ef_title: str,
    event_type: str,
    primary_theater: str,
    canonical_actors: List[str],
    policy_status: str,
) -> tuple[str, str]:
    """
    Build strategic context prompt for why_strategic field

    Args:
        ef_title: Event Family title
        event_type: Event type classification
        primary_theater: Primary theater
        canonical_actors: List of canonical actor names
        policy_status: Policy status if any

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    actors_text = ", ".join(canonical_actors) if canonical_actors else "Various"

    system = STRATEGIC_CONTEXT_SYSTEM_PROMPT
    user = STRATEGIC_CONTEXT_USER_TEMPLATE.format(
        ef_title=ef_title,
        primary_theater=primary_theater,
        event_type=event_type,
        canonical_actors=actors_text,
        policy_status=policy_status or "N/A",
    )

    return system, user


# Magnitude Extraction Patterns
MAGNITUDE_PATTERNS = {
    "money": r"(\d+(?:\.\d+)?)\s*(?:billion|bn|million|mn|trillion|tn)?\s*(?:USD|EUR|GBP|\$|€|£)",
    "energy": r"(\d+(?:\.\d+)?)\s*(GW|MW|TWh|bcm|mcm|barrels|bpd)",
    "military": r"(\d+(?:,\d+)?)\s*(troops|soldiers|personnel|aircraft|ships|tanks)",
    "casualties": r"(\d+(?:,\d+)?)\s*(dead|killed|casualties|wounded|injured|missing)",
    "percentage": r"(\d+(?:\.\d+)?)\s*%",
    "trade": r"(\d+(?:\.\d+)?)\s*(?:billion|bn|million|mn)?\s*(?:tons|tonnes|barrels)",
}


def extract_magnitudes_from_titles(
    titles: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Extract magnitude information from title text using regex patterns

    Args:
        titles: List of title dictionaries

    Returns:
        List of magnitude dictionaries
    """
    import re

    magnitudes = []

    for title in titles:
        text = title.get("text", title.get("title", ""))
        if not text:
            continue

        # Check each pattern type
        for mag_type, pattern in MAGNITUDE_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value_str = match.group(1).replace(",", "")
                    value = float(value_str)
                    unit = match.group(2) if len(match.groups()) > 1 else mag_type

                    # Normalize common abbreviations
                    if (
                        "billion" in match.group(0).lower()
                        or "bn" in match.group(0).lower()
                    ):
                        value *= 1000000000
                        unit = (
                            unit.replace("billion", "").replace("bn", "").strip()
                            or "units"
                        )
                    elif (
                        "million" in match.group(0).lower()
                        or "mn" in match.group(0).lower()
                    ):
                        value *= 1000000
                        unit = (
                            unit.replace("million", "").replace("mn", "").strip()
                            or "units"
                        )

                    magnitudes.append(
                        {
                            "value": value,
                            "unit": unit,
                            "what": f"{mag_type} mentioned in: {text[:50]}...",
                        }
                    )
                except (ValueError, IndexError):
                    continue

    # Deduplicate similar magnitudes
    unique_magnitudes = []
    seen_combinations = set()

    for mag in magnitudes:
        key = (round(mag["value"]), mag["unit"].lower())
        if key not in seen_combinations:
            seen_combinations.add(key)
            unique_magnitudes.append(mag)

    return unique_magnitudes[:3]  # Limit to 3 most relevant
