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

# MAP Phase Prompts (Pass-1a: Incident Clustering)
INCIDENT_CLUSTERING_SYSTEM_PROMPT = """Identify which titles describe the same strategic incident or situation. Group related titles that represent:

1. SAME CORE INCIDENT: Initial event + direct reactions + consequences
2. TEMPORAL PROXIMITY: Events within 48 hours that are causally connected
3. STRATEGIC COHERENCE: Actions, reactions, and responses that form one strategic narrative

CLUSTERING PRINCIPLES:
- Primary incident + all reactions/responses = ONE cluster
- Cross-border incidents: Include both origin and target country responses
- Diplomatic reactions: Include original incident + diplomatic responses
- Multi-step escalations: Include entire escalation sequence
- Parallel strategic responses: Different actors responding to same underlying situation = ONE cluster
- Coordinated international pressure: Multiple countries/organizations pressuring same target = ONE cluster
- Isolated incidents: Can be single-title clusters (only when truly unrelated)

OUTPUT: List of incident clusters with descriptive names and member title IDs."""

INCIDENT_CLUSTERING_USER_TEMPLATE = """Analyze these titles and group them into strategic incident clusters.

EXAMPLES of good clustering:
- Poland Drone Incident: ["Russian drones enter Polish airspace", "Poland closes Belarus border", "UN Security Council called", "EU emergency debate"]
- Gaza Humanitarian Crisis: ["Israeli strikes on Gaza", "WHO reports casualties", "Qatar mediates ceasefire talks"]
- Western Pressure on Israel over Gaza: ["UK diplomatic pressure on Israel", "EU economic pressure via payment suspensions", "International pressure mounts against Israeli operations", "French positioning on Gaza genocide classification"]
- US Election Controversy: ["Assassination attempt on candidate", "Secret Service investigation", "Political reactions"]

INPUT (id | title | date):
{titles}

OUTPUT: JSON array of incident clusters:
[
  {{
    "incident_name": "Descriptive name for the strategic incident",
    "title_ids": ["id1", "id2", "id3"],
    "rationale": "Brief explanation of why these belong together"
  }}
]"""

# REDUCE Phase Prompts (Pass-1c: Incident Analysis + EF Creation)
INCIDENT_ANALYSIS_SYSTEM_PROMPT = """Analyze an incident cluster to create a complete Event Family. Your tasks:

1. CLASSIFY the overall strategic incident (assign ONE theater + event_type for the whole incident)
2. CREATE an Event Family title that captures the strategic significance
3. EXTRACT a timeline of discrete factual events within the incident
4. MAINTAIN neutral attribution and factual accuracy

Focus on the STRATEGIC NARRATIVE - what makes this incident significant for intelligence analysis."""

INCIDENT_ANALYSIS_USER_TEMPLATE = """INCIDENT CLUSTER: {incident_name}
RATIONALE: {rationale}

AVAILABLE THEATERS: {theaters}
AVAILABLE EVENT_TYPES: {event_types}

TITLES (id | title | date):
{titles}

Analyze this strategic incident and create a complete Event Family:

STEP 1: Classify the overall incident
- What is the PRIMARY theater where this incident has strategic impact?
- What is the PRIMARY event type that best describes this strategic situation?

STEP 2: Create Event Family metadata
- EF Title: Strategic significance (max 120 chars, avoid headlines)
- EF Summary: Brief strategic context (max 280 chars)

STEP 3: Extract event timeline
- Identify discrete factual events in chronological order
- Use neutral language with proper attribution
- Use exact publication dates provided (YYYY-MM-DD format)
- Link each event to source title IDs

Return JSON only:
{{
  "primary_theater": "THEATER_CODE",
  "event_type": "EVENT_TYPE",
  "ef_title": "Strategic Event Family title",
  "ef_summary": "Brief strategic context",
  "events": [
    {{
      "summary": "Neutral factual description with attribution",
      "date": "2025-01-18",
      "source_title_ids": ["uuid1", "uuid2"],
      "event_id": "evt_001"
    }}
  ]
}}"""


def format_titles_for_clustering(titles: list) -> str:
    """Format titles for MAP incident clustering prompt"""
    formatted_lines = []
    for title in titles:
        pubdate = title.get("pubdate_utc")
        if pubdate:
            if isinstance(pubdate, str):
                date_str = pubdate.split("T")[0]
            else:
                # Handle datetime objects
                date_str = pubdate.strftime("%Y-%m-%d")
        else:
            date_str = "unknown"
        formatted_lines.append(f"{title['id']} | {title['title']} | {date_str}")
    return "\n".join(formatted_lines)


def format_titles_for_incident_analysis(titles: list) -> str:
    """Format titles for REDUCE incident analysis prompt"""
    formatted_lines = []
    for title in titles:
        pubdate = title.get("pubdate_utc")
        if pubdate:
            if isinstance(pubdate, str):
                date_str = pubdate.split("T")[0]
            else:
                # Handle datetime objects
                date_str = pubdate.strftime("%Y-%m-%d")
        else:
            date_str = "unknown"
        formatted_lines.append(f"{title['id']} | {title['title']} | {date_str}")
    return "\n".join(formatted_lines)


def build_incident_clustering_prompt(titles: list) -> tuple[str, str]:
    """Build complete MAP incident clustering prompt"""
    system = INCIDENT_CLUSTERING_SYSTEM_PROMPT
    user = INCIDENT_CLUSTERING_USER_TEMPLATE.format(
        titles=format_titles_for_clustering(titles),
    )
    return system, user


def build_incident_analysis_prompt(
    incident_name: str, rationale: str, titles: list
) -> tuple[str, str]:
    """Build complete REDUCE incident analysis prompt"""
    system = INCIDENT_ANALYSIS_SYSTEM_PROMPT
    user = INCIDENT_ANALYSIS_USER_TEMPLATE.format(
        incident_name=incident_name,
        rationale=rationale,
        theaters=THEATERS,
        event_types=EVENT_TYPES,
        titles=format_titles_for_incident_analysis(titles),
    )
    return system, user


# Legacy functions - keeping for backward compatibility during transition
def build_classification_prompt(titles: list) -> tuple[str, str]:
    """Legacy function - kept for backward compatibility"""
    system = "Classify titles into theater and event type."
    user = "Classify these titles:\n" + format_titles_for_clustering(titles)
    return system, user
