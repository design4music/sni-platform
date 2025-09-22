"""
Micro-Prompt System for EF Enrichment
Bounded, cheap prompts for canonical actors and policy status
"""

from typing import Any, Dict, List

# Micro-Prompt 1: Objectivity-First Strategic Context
CANONICALIZE_SYSTEM_PROMPT = """Extract factual strategic context WITHOUT interpretation or motive attribution.

ACTORS: Official names only (countries: US/UK/RU/CN, orgs: NATO/UN/EU, people: Last Name)
ROLES: initiator|target|beneficiary|mediator (based on actions, not intentions)
TEMPORAL_PATTERN: Frequency/timing of similar events in relevant timeframe (auto-detect scope: months to decades)
MAGNITUDE_BASELINE: Scale vs historical norm in region/domain
SYSTEMIC_CONTEXT: What broader documented trend/pattern this fits within
SOURCE_BALANCE: Confirm perspectives from all conflict parties represented
TAGS: Exactly 3 tags - 2 thematic concepts + 1 geographic region (e.g., ["climate change", "natural disasters", "Southeast Asia"])

OBJECTIVITY STANDARD: Report only what happened, not why it happened. Describe observable actions and measurable outcomes. Avoid all speculation about motivations, intentions, or strategic purposes. Present documented patterns without inferring causation."""

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
  "temporal_pattern": "Factual frequency/timing of similar events in relevant timeframe",
  "magnitude_baseline": "Scale vs historical norm in this region/domain",
  "systemic_context": "Broader documented trend this fits within",
  "why_strategic": "Objective strategic significance without interpretation (≤150 chars)",
  "tags": ["theme1", "theme2", "geographic_region"]
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


# Micro-Prompt 3: Narrative-Focused Summary Enhancement
NARRATIVE_SUMMARY_SYSTEM_PROMPT = """Rewrite the Event Family summary with a narrative intelligence focus.

TARGET AUDIENCE: Strategic intelligence analysts, policymakers, and decision-makers who need to quickly understand the strategic implications of ongoing sagas.

NARRATIVE PRINCIPLES:
- Lead with strategic significance, not chronological details
- Emphasize ongoing dynamics and tensions, not just events
- Show how this fits into larger geopolitical patterns
- Use active voice and clear, authoritative language
- Avoid technical jargon, journalistic clichés, and passive constructions

STRUCTURE:
1. Strategic significance opening (why this matters)
2. Key dynamics and actors involved
3. Current trajectory and implications

LENGTH: 150-250 words maximum. Complete sentences, no truncation."""

NARRATIVE_SUMMARY_USER_TEMPLATE = """EF: {ef_title}
CURRENT SUMMARY: {current_summary}
THEATER: {primary_theater} | TYPE: {event_type}
KEY ACTORS: {canonical_actors}

TITLES CONTEXT:
{member_titles}

Rewrite this summary for strategic narrative intelligence. Focus on the ongoing strategic saga, not individual incidents. Show why this matters for regional/global stability."""


# Micro-Prompt 4: Macro-Link & Context Assessment
MACRO_LINK_SYSTEM_PROMPT = """Identify which narrative centroid (macro-storyline) this Event Family belongs to and provide strategic context.

AVAILABLE CENTROIDS:
{available_centroids}

ASSESSMENT CRITERIA:
- MACRO_LINK: Which centroid this EF fits into based on actors, geography, and issue domain
- COMPARABLES: 2-3 strategically relevant precedents that inform current decision-making
  * TEMPORAL: Generally within 1-2 decades (unless domain has longer cycles like territorial disputes)
  * ACTORS: Same or similar actor types (not just famous historical figures)
  * CONTEXT: Similar geopolitical environment and power dynamics
  * RELEVANCE: Actionable lessons for current strategic assessment
  * AVOID: Ancient history, mythical parallels, or famous-but-irrelevant events
- ABNORMALITY: What makes this event unusual, significant, or precedent-setting

RESPONSE FORMAT: Valid JSON only, no explanation."""

MACRO_LINK_USER_TEMPLATE = """EF: {ef_title}
SUMMARY: {ef_summary}
ACTORS: {canonical_actors}
THEATER: {primary_theater}
EVENT_TYPE: {event_type}

Assess macro-link and strategic context. For comparables, focus on recent precedents with similar actors/context that inform current decision-making:
{{
  "ef_context": {{
    "macro_link": "CENTROID_ID or null",
    "comparables": [
      {{
        "event_description": "Brief description",
        "timeframe": "When occurred",
        "similarity_reason": "Why strategically comparable (actors, context, implications)"
      }}
    ],
    "abnormality": "What makes this significant/unusual or null"
  }}
}}"""


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

                    # Use first part of text for context
                    what_text = f"{mag_type}: {text}"

                    magnitudes.append(
                        {
                            "value": value,
                            "unit": unit,
                            "what": what_text,
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


def build_narrative_summary_prompt(
    ef_title: str,
    current_summary: str,
    event_type: str,
    primary_theater: str,
    canonical_actors: List[str],
    member_titles: List[Dict[str, Any]],
) -> tuple[str, str]:
    """
    Build narrative summary enhancement prompt

    Args:
        ef_title: Event Family title
        current_summary: Current EF summary
        event_type: Event type classification
        primary_theater: Primary theater
        canonical_actors: List of canonical actor names
        member_titles: List of member title dictionaries

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Format recent titles for context
    sorted_titles = sorted(
        member_titles, key=lambda x: x.get("pubdate_utc", ""), reverse=True
    )[:3]

    formatted_titles = []
    for title in sorted_titles:
        date_str = title.get("pubdate_utc", "unknown")
        if isinstance(date_str, str) and "T" in date_str:
            date_str = date_str.split("T")[0]
        elif hasattr(date_str, "strftime"):
            date_str = date_str.strftime("%Y-%m-%d")

        formatted_titles.append(
            f"- {title.get('text', title.get('title', ''))} ({date_str})"
        )

    member_titles_text = "\n".join(formatted_titles)
    actors_text = ", ".join(canonical_actors) if canonical_actors else "Various actors"

    system = NARRATIVE_SUMMARY_SYSTEM_PROMPT
    user = NARRATIVE_SUMMARY_USER_TEMPLATE.format(
        ef_title=ef_title,
        current_summary=current_summary,
        primary_theater=primary_theater,
        event_type=event_type,
        canonical_actors=actors_text,
        member_titles=member_titles_text,
    )

    return system, user


def build_macro_link_prompt(
    ef_title: str,
    ef_summary: str,
    event_type: str,
    primary_theater: str,
    canonical_actors: List[str],
    available_centroids: List[Dict[str, Any]],
) -> tuple[str, str]:
    """
    Build macro-link assessment prompt

    Args:
        ef_title: Event Family title
        ef_summary: Current EF summary
        event_type: Event type classification
        primary_theater: Primary theater
        canonical_actors: List of canonical actor names
        available_centroids: List of centroid dictionaries from database

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Format centroids for the prompt
    centroids_text = []
    for centroid in available_centroids:
        centroids_text.append(
            f"- {centroid['id']}: {centroid['label']}\n"
            f"  Keywords: {', '.join(centroid['keywords'][:5])}\n"
            f"  Actors: {', '.join(centroid['actors'][:3])}\n"
            f"  Theaters: {', '.join(centroid['theaters'])}"
        )

    centroids_list = "\n\n".join(centroids_text)
    actors_text = ", ".join(canonical_actors) if canonical_actors else "Various actors"

    system = MACRO_LINK_SYSTEM_PROMPT.format(available_centroids=centroids_list)
    user = MACRO_LINK_USER_TEMPLATE.format(
        ef_title=ef_title,
        ef_summary=ef_summary,
        canonical_actors=actors_text,
        primary_theater=primary_theater,
        event_type=event_type,
    )

    return system, user
