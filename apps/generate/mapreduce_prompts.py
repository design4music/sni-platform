"""
MAP/REDUCE Prompts
Minimal, optimized prompts for the MAP/REDUCE Event Family processing approach
"""

# EVENT_TYPE and THEATER enums (copied from current system for consistency)
EVENT_TYPES = [
    "Strategy/Tactics",
    "Humanitarian",
    "Alliances/Geopolitics",
    "Diplomacy/Negotiations",
    "Sanctions/Economy",
    "Domestic Politics",
    "Procurement/Force-gen",
    "Tech/Cyber/OSINT",
    "Legal/ICC",
    "Information/Media/Platforms",
    "Energy/Infrastructure",
]

THEATERS = [
    "UKRAINE",
    "GAZA",
    "TAIWAN_STRAIT",
    "IRAN_NUCLEAR",
    "EUROPE_SECURITY",
    "US_DOMESTIC",
    "CHINA_TRADE",
    "MEAST_REGIONAL",
    "CYBER_GLOBAL",
    "CLIMATE_GLOBAL",
    "AFRICA_SECURITY",
    "KOREA_PENINSULA",
    "LATAM_REGIONAL",
    "ARCTIC",
    "GLOBAL_SUMMIT",
]

# MAP Phase Prompts (Pass-1a: Classification)
CLASSIFICATION_SYSTEM_PROMPT = """Classify each title into exactly one primary_theater and one event_type from the enums provided. Output one compact JSON object per input title (JSON Lines). Use only given IDs. No external facts."""

CLASSIFICATION_USER_TEMPLATE = """EVENT_TYPES = {event_types}
THEATERS = {theaters}
Return JSON Lines only, one per title:
{{"id":"...", "primary_theater":"THEATER_ID", "event_type":"EVENT_TYPE"}}

INPUT (id | title):
{titles}"""

# REDUCE Phase Prompts (Pass-1c: EF Generation)
EF_GENERATION_SYSTEM_PROMPT = """Given one provisional EF (primary_theater + event_type) and up to 12 titles (id+title), produce a concise EF title (≤120 chars) and EF summary (≤280 chars) describing the recurring pattern (not a single incident). No outside facts."""

EF_GENERATION_USER_TEMPLATE = """EF CONTEXT: primary_theater={primary_theater}, event_type={event_type}
TITLES (id | title):
{titles}
Return JSON only: {{"ef_title":"...", "ef_summary":"..."}}"""


def format_titles_for_classification(titles: list) -> str:
    """Format titles for MAP classification prompt"""
    return "\n".join([f"{title['id']} | {title['title']}" for title in titles])


def format_titles_for_ef_generation(titles: list) -> str:
    """Format titles for REDUCE EF generation prompt"""
    return "\n".join([f"{title['id']} | {title['title']}" for title in titles])


def build_classification_prompt(titles: list) -> tuple[str, str]:
    """Build complete MAP classification prompt"""
    system = CLASSIFICATION_SYSTEM_PROMPT
    user = CLASSIFICATION_USER_TEMPLATE.format(
        event_types=EVENT_TYPES,
        theaters=THEATERS,
        titles=format_titles_for_classification(titles),
    )
    return system, user


def build_ef_generation_prompt(
    primary_theater: str, event_type: str, titles: list
) -> tuple[str, str]:
    """Build complete REDUCE EF generation prompt"""
    system = EF_GENERATION_SYSTEM_PROMPT
    user = EF_GENERATION_USER_TEMPLATE.format(
        primary_theater=primary_theater,
        event_type=event_type,
        titles=format_titles_for_ef_generation(titles),
    )
    return system, user
