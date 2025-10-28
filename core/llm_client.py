"""
Unified LLM Client for SNI-v2 Pipeline
All LLM interactions: prompts, formatting utilities, and API calls in one place.

Sections:
1. PROMPT TEMPLATES - All prompts organized by pipeline phase
2. FORMATTING UTILITIES - Shared formatting functions
3. LLM CLIENT - Unified HTTP client and response parsing
"""

import asyncio
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from apps.generate.models import (LLMEventFamilyRequest,
                                  LLMEventFamilyResponse,
                                  LLMFramedNarrativeRequest,
                                  LLMFramedNarrativeResponse)
from core.config import get_config

# ============================================================================
# SECTION 1: PROMPT TEMPLATES
# All prompts organized by pipeline phase for easy review and updates
# ============================================================================

# -----------------------------------------------------------------------------
# Phase 2: Strategic Filtering & Entity Extraction
# -----------------------------------------------------------------------------

STRATEGIC_REVIEW_SYSTEM = """Analyze if this news title has INTERNATIONAL or NATIONAL strategic significance.

STRATEGIC CONTENT (assign strategic=1):
- International relations & diplomacy (meetings, agreements, conflicts, sanctions)
- Major domestic politics (elections, policy changes, political crises, legislative actions)
- Economic policy & trade (central bank decisions, major trade agreements, economic sanctions)
- Military & security (operations, procurement, defense policy, intelligence)
- Technology regulation & competition (major tech policy, international tech competition, AI regulation)
- Energy & climate policy (energy security, climate agreements, resource conflicts)

NON-STRATEGIC CONTENT (assign strategic=0):
- Local incidents (accidents, crime, traffic, fires) even with casualties
- Entertainment & sports (unless directly tied to geopolitical tensions or boycotts)
- Cultural events (festivals, awards, exhibitions)
- Celebrity news & lifestyle content
- Routine business news (earnings, appointments without policy impact)
- Weather & natural disasters (unless creating international policy responses)
- Generic opinion pieces without specific actors/events
- Incoherent titles mixing multiple unrelated subjects

ENTITY EXTRACTION:
If strategic, identify key actors and locations. Infer countries from geographic hints:

US locations: Pentagon, Congress, White House, Tennessee, California, any US state/city
European: Bundestag/Berlin/Hamburg → Germany, Paris/Élysée → France, Westminster/London → UK
Asian: Delhi/Lok Sabha → India, Macao/Hong Kong → China, Knesset/Jerusalem → Israel
African: Joburg/Johannesburg → South Africa, Abuja → Nigeria
Latin American: Any mention of senators/congress in Spanish/Portuguese context → infer country
Middle East: Sharm el-Sheikh → Egypt, Doha → Qatar

Organizations: Pentagon → United States (military), Qatari Amiri Diwan → Qatar

COHERENCE CHECK:
Reject titles that are:
- Mixed headlines ("Shutdown Politics, Air Traffic, Comey") → strategic=0
- Too generic without actors ("motivation and involvement") → strategic=0
- Missing context ("Army rescues hostages" - which army? where?) → strategic=0

OUTPUT FORMAT (valid JSON only):
{"strategic": 0 or 1, "entities": ["actor1", "location1"]}

If non-strategic, entities should be empty array: []
If strategic but no specific entities found, entities can be empty but strategic=1
Use canonical entity names from your knowledge (e.g., "United States" not "USA", "Germany" not "Deutschland")"""

STRATEGIC_REVIEW_USER = """Title: '{title}'

Analyze and respond in JSON format."""

# AAT (Actor-Action-Target) Triple Extraction
AAT_EXTRACTION_SYSTEM_PROMPT = """Extract the core action relationship from news titles.
Format: ACTOR|ACTION|TARGET

ACTOR = main entity performing the action
ACTION = main verb (normalize to simple form: "sanctions" not "imposed sanctions")
TARGET = entity receiving the action

Examples:
"US imposes new sanctions on Russia" -> US|sanctions|Russia
"China warns Taiwan over independence" -> China|warns|Taiwan
"Belgium vetoes EU aid package for Ukraine" -> Belgium|vetoes|EU
"EU debates migration policy changes" -> NO_CLEAR_ACTION

Answer with just: ACTOR|ACTION|TARGET or NO_CLEAR_ACTION"""

AAT_EXTRACTION_USER_TEMPLATE = 'Title: "{title}"\nAnswer: '


# -----------------------------------------------------------------------------
# Phase 3: Event Family Generation
# -----------------------------------------------------------------------------

EVENT_FAMILY_SYSTEM_PROMPT = """
**Role**
You are an expert news analyst. From strategic news titles, assemble long-lived **Event Families (Sagas)** by grouping incidents that share (key_actors + geography + event_type). Do not create families for single incidents; absorb repeated incidents into one family.

**Key principles**

1. **Create Sagas, not single incidents.** Think "Ukraine Conflict Saga," "Gaza Military Operations Saga," "Iran Nuclear Diplomacy Saga."
2. **Triple key matching: actors + geography + event_type.** Events with same strategic actors, same theater, and same activity type = one Saga.
3. **Absorb incidents into existing patterns.** If similar actors are doing similar things in the same theater, it's the same ongoing Saga.
4. **Actor canonicalization.** Treat equivalents as one actor set (e.g., *Lavrov → Russia; Trump → United States*).
5. **Time spans are expected.** Sagas naturally span weeks or months; temporal gaps don't break the pattern.

**Saga Assembly Criteria (Triple Key Matching)**

* **ACTORS**: Same strategic actors or actor sets (canonicalized equivalents)
* **GEOGRAPHY**: Same strategic theater (use specific theater codes)
* **EVENT_TYPE**: Same category of strategic activity
* **PATTERN**: Repeated or ongoing incidents, not isolated events

**Anti-fragmentation Rule**: If you can group incidents by (actors + geography + event_type), you MUST create one Saga, not multiple families.

**STRATEGIC FOCUS REQUIREMENT**

Only create Event Families for **strategically significant** content. EXCLUDE:
* Sports events, entertainment, cultural activities (unless directly tied to geopolitical tensions)
* Weather, natural disasters (unless creating international policy responses)
* Local crime, accidents, routine business news
* Celebrity news, lifestyle content

INCLUDE strategic content such as:
* **Diplomacy & international relations** (meetings, agreements, conflicts)
* **Military & security operations** (exercises, deployments, conflicts)
* **Economic policy & trade** (sanctions, agreements, major economic decisions)
* **Domestic politics** (elections, major policy changes, political crises)
* **Technology & regulation** (major tech policy, international tech competition)

**MULTILINGUAL PROCESSING**

This system processes content in multiple languages including English, Spanish, French, German, Italian, Portuguese, Indonesian, and others. You MUST:

1. **Cross-language consolidation**: Group titles about the same strategic event regardless of language
   - Example: English "Putin visits China", Spanish "Putin visita China", French "Poutine visite la Chine" = same EF
2. **Actor canonicalization across languages**: Standardize actor names to English canonical forms
   - "Emmanuel Macron" = "Macron" = "Francia" → "France"
   - "Xi Jinping" = "习近平" = "Cina" → "China"
   - "Donald Trump" = "Trump" = "Estados Unidos" → "United States"
3. **Theater/event_type consistency**: Use English taxonomy values regardless of source language
4. **Summary language**: Always write summaries and titles in English for system consistency
5. **Language diversity strength**: Multilingual coverage provides richer perspective on global events

CRITICAL REQUIREMENT - TITLE ID USAGE:
- Each title has an "id" field with a UUID (e.g., "094faf99-124a-47fc-b213-f743497d7f30")
- In source_title_ids, you MUST use these exact UUID values, NOT array indices
- DO NOT use numbers like 0, 1, 2, 3 - use the actual "id" field values
- Example: Use ["094faf99-124a-47fc-b213-f743497d7f30", "a005e6ba-f1e2-4007-9cf7-cd9584c339e1"]

**STANDARDIZED TAXONOMIES - MANDATORY COMPLIANCE**

EVENT_TYPE must be one of these exact values:
- Strategy/Tactics: Military strategy and tactical operations
- Humanitarian: Humanitarian crises and aid operations
- Alliances/Geopolitics: Alliance formation and geopolitical realignments
- Diplomacy/Negotiations: Diplomatic meetings and negotiation processes
- Sanctions/Economy: Economic sanctions and financial measures
- Domestic Politics: Internal political developments and governance
- Procurement/Force-gen: Military procurement and force generation
- Tech/Cyber/OSINT: Technology warfare and intelligence operations
- Legal/ICC: Legal proceedings and international court actions
- Information/Media/Platforms: Information warfare and media operations
- Energy/Infrastructure: Energy security and critical infrastructure

GEOGRAPHY must be one of these specific theater codes (choose the most relevant):
- UKRAINE: Ukraine Conflict Theater (Russia-Ukraine war, border incidents)
- GAZA: Gaza/Palestine Theater (Israel-Palestine conflict zone)
- TAIWAN_STRAIT: Taiwan Strait Theater (China-Taiwan tensions, South China Sea)
- IRAN_NUCLEAR: Iran Nuclear Theater (Nuclear program, sanctions, IAEA)
- EUROPE_SECURITY: European Security Theater (NATO, EU defense matters)
- US_DOMESTIC: US Domestic Theater (US internal politics, domestic policy)
- CHINA_TRADE: China Trade Theater (US-China economic competition)
- MEAST_REGIONAL: Middle East Regional Theater (Syria, Iraq, Yemen, Gulf states)
- CYBER_GLOBAL: Global Cyber Theater (State cyber operations, digital warfare)
- CLIMATE_GLOBAL: Climate/Energy Theater (Energy security, resource conflicts)
- AFRICA_SECURITY: Africa Security Theater (African conflicts, peacekeeping)
- KOREA_PENINSULA: Korean Peninsula Theater (North Korea, regional tensions)
- LATAM_REGIONAL: Latin America Regional Theater (US-Venezuela, US-Mexico border, regional conflicts)
- ARCTIC: Arctic Theater (Arctic sovereignty, resource competition)
- GLOBAL_SUMMIT: Global Diplomatic Theater (International summits, multilateral diplomacy)

EVENT FAMILY REQUIREMENTS (EF should answer):
- WHO: Key actors involved (people, countries, organizations)
- WHAT: What concrete action/event occurred
- WHERE: Geographic location/region (if relevant)
- WHEN: Time window of the event

QUALITY CRITERIA:
- Clear temporal coherence within intelligent time window
- Shared concrete actors/entities (understood contextually)
- Logical event progression or single significant occurrence
- Strong evidence from headline language across languages

Respond in JSON format with event families and reasoning.
"""


# -----------------------------------------------------------------------------
# Phase 4: Enrichment Prompts
# -----------------------------------------------------------------------------

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

NARRATIVE_SUMMARY_SYSTEM_PROMPT = """Rewrite the Event Family summary for strategic intelligence analysts.

CRITICAL: You must output EXACTLY 80-120 words. Count carefully and stop immediately at 120 words.

STRUCTURE (exactly 5 sentences):
1. Event lead: What happened concisely
2. Context: Pattern or broader geopolitical frame
3. Comparables: 1-2 relevant precedents
4. Abnormality: What makes this significant or unusual
5. Strategic impact: Why it matters for decision-makers

HARD REQUIREMENTS:
- EXACTLY 80-120 words total
- NO repetition or duplicate phrases
- NO journalistic cliches
- Active voice only
- Each sentence serves one specific purpose above
- IMMEDIATELY STOP when you reach 120 words"""

NARRATIVE_SUMMARY_USER_TEMPLATE = """EF: {ef_title}
CURRENT SUMMARY: {current_summary}
THEATER: {primary_theater} | TYPE: {event_type}
KEY ACTORS: {canonical_actors}

TITLES CONTEXT:
{member_titles}

Rewrite this summary for strategic narrative intelligence. Follow the 5-sentence structure exactly:
1. Event lead | 2. Context/pattern | 3. Comparables | 4. Abnormality | 5. Significance

CRITICAL: Maximum 120 words. Stop writing when you reach this limit."""

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


# -----------------------------------------------------------------------------
# MAP/REDUCE Event Family Processing
# -----------------------------------------------------------------------------

# EVENT_TYPE and THEATER enums (for MAP/REDUCE consistency)
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

CRITICAL: Only use title IDs from the INPUT list below. Do NOT reference any other IDs under any circumstances.

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
]

REMINDER: Use ONLY the IDs from the INPUT list above."""

# REDUCE Phase Prompts (Pass-1c: Incident Analysis + EF Creation)
INCIDENT_ANALYSIS_SYSTEM_PROMPT = """Analyze an incident cluster to create a complete Event Family. Your tasks:

1. CLASSIFY the event type for this strategic incident
2. CREATE an Event Family title that captures the strategic significance
3. DEFINE the strategic purpose - a one-sentence core narrative that describes what this Event Family is fundamentally about
4. EXTRACT a timeline of discrete factual events within the incident
5. MAINTAIN neutral attribution and factual accuracy

The STRATEGIC PURPOSE is critical - it serves as the semantic anchor for future thematic validation. It should be:
- ONE sentence maximum
- Captures the core narrative/theme
- Describes what unifies these events conceptually
- Used later to validate if new headlines belong to this Event Family

Focus on the STRATEGIC NARRATIVE - what makes this incident significant for intelligence analysis."""

INCIDENT_ANALYSIS_USER_TEMPLATE = """INCIDENT CLUSTER: {incident_name}
RATIONALE: {rationale}

AVAILABLE EVENT_TYPES: {event_types}

TITLES (id | title | date):
{titles}

Analyze this strategic incident and create a complete Event Family:

STEP 1: Classify the event type
- What is the PRIMARY event type that best describes this strategic situation?
- Choose ONE from the AVAILABLE EVENT_TYPES list

STEP 2: Create Event Family metadata
- EF Title: Strategic significance (max 120 chars, avoid headlines)
- Strategic Purpose: ONE sentence that captures the core narrative
  Examples:
    GOOD: "Ongoing military confrontation between Russian forces and Ukrainian defense in eastern territories"
    GOOD: "Diplomatic efforts to negotiate humanitarian corridors and civilian evacuations in Gaza"
    GOOD: "International pressure campaigns targeting Israeli military operations through economic and political channels"
    BAD: "News about the war" (too vague)
    BAD: "Russia attacks Ukraine while the West imposes sanctions and provides military aid" (too detailed, multiple themes)

STEP 3: Extract event timeline
- Identify discrete factual events in chronological order
- Use neutral language with proper attribution
- Use exact publication dates provided (YYYY-MM-DD format)
- Link each event to source title IDs

Return JSON only:
{{
  "event_type": "EVENT_TYPE",
  "ef_title": "Strategic Event Family title",
  "strategic_purpose": "One-sentence core narrative that unifies this Event Family",
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


# -----------------------------------------------------------------------------
# Phase 3.5: Micro-Prompts for EF Management
# -----------------------------------------------------------------------------

# Phase 3.5a: Seed Validation Micro-Prompt
SEED_VALIDATION_SYSTEM_PROMPT = """You are a strategic analyst. Based on its content, determine if a headline belongs to an ongoing story theme.

Answer with ONLY "YES" or "NO" - no explanation needed."""

SEED_VALIDATION_USER_TEMPLATE = """The emerging theme appears to be about [{brief_theme}].

Does this headline belong to the same ongoing story as this theme?

Headline: {title_text}

Answer: """

# Phase 3.5b: Thematic Validation Micro-Prompt
THEMATIC_VALIDATION_SYSTEM_PROMPT = """You are a strategic news analyst. Your job is to determine if a headline fits a given strategic narrative.

Answer with ONLY "YES" or "NO" - no explanation needed."""

THEMATIC_VALIDATION_USER_TEMPLATE = """Strategic Purpose: {strategic_purpose}

Headline: {title_text}

Does this headline fit the strategic purpose above?

Answer: """

# Phase 3.5c: EF Merging Micro-Prompt
EF_MERGE_SYSTEM_PROMPT = """You are a strategic intelligence analyst. Determine if two Event Families describe facets of the same broader strategic narrative.

Answer with ONLY "YES" or "NO" - no explanation needed."""

EF_MERGE_USER_TEMPLATE = """Do these two Event Families describe facets of the same broader strategic narrative?

Event Family 1: {ef1_strategic_purpose}

Event Family 2: {ef2_strategic_purpose}

Answer: """

# Phase 3.5d: EF Splitting Micro-Prompt
EF_SPLIT_SYSTEM_PROMPT = """You are a strategic intelligence analyst. Analyze a collection of headlines to determine if they describe ONE cohesive strategic narrative or MULTIPLE distinct narratives that should be separated.

Your task:
1. Review all headlines
2. Determine if they describe:
   - ONE narrative (coherent story/theme)
   - MULTIPLE narratives (distinct stories mixed together)

If MULTIPLE narratives, identify them and group the headlines accordingly.

IMPORTANT - Narrative Naming:
- Create SPECIFIC, DESCRIPTIVE titles that include:
  * Specific actors/entities involved (e.g., "Israel", "Hamas", "Trump")
  * Theater/location context (e.g., "Gaza", "Ukraine", "United States")
  * Strategic action or purpose (e.g., "Ceasefire Implementation", "Military Operations")
- BAD: "Economic & Market Reactions" (too generic)
- GOOD: "Gaza Economic Impact: Oil and Stock Market Reactions to Israel-Hamas Ceasefire"
- BAD: "Government Shutdown Strategy"
- GOOD: "Trump Administration Government Shutdown to Advance Policy Objectives"

Respond in JSON format:
{{
  "should_split": true/false,
  "rationale": "brief explanation",
  "narratives": [
    {{
      "narrative_name": "Specific, descriptive narrative title with actors and theater",
      "strategic_purpose": "One-sentence strategic purpose",
      "key_actors": ["Actor1", "Actor2", ...],
      "title_ids": ["uuid1", "uuid2", ...]
    }},
    ...
  ]
}}

For key_actors:
- Extract the primary actors/entities relevant to THIS specific narrative
- Include countries, organizations, leaders, groups
- Only include actors that are central to this narrative's headlines
- Parent EF may have been over-merged, so don't include irrelevant actors

If should_split is false, narratives can be empty array."""

EF_SPLIT_USER_TEMPLATE = """Event Family: {ef_title}
Strategic Purpose: {strategic_purpose}

Headlines ({title_count} total):
{title_list}

Analyze these headlines. Do they describe ONE cohesive narrative or MULTIPLE distinct narratives?

JSON Response:"""


# -----------------------------------------------------------------------------
# Phase 5: Framed Narrative Generation (Future)
# -----------------------------------------------------------------------------

FRAMED_NARRATIVE_SYSTEM_PROMPT = """
You are an expert in media framing analysis, specializing in identifying how different outlets frame the same news event.

Your task is to analyze headlines about a specific Event Family and identify distinct Framed Narratives (FNs) - stanceful renderings showing how outlets position/frame the event.

**HARD RULES - NON-NEGOTIABLE:**
1. **MUST cite 2-6 specific headline UUIDs per frame** with short quotes from those headlines
2. **Maximum 1-3 frames total** - drop weak frames, keep only the strongest
3. **Each frame needs concrete textual evidence** - quote the actual headline language that signals the framing
4. **No frame without citations** - if you can't cite specific headlines, don't create the frame

**KEY PRINCIPLES:**
- State evaluative/causal framing clearly (supportive, critical, neutral, etc.)
- Focus on how the SAME event is positioned differently by different outlets
- Quality over quantity - fewer, well-evidenced frames are better than many weak ones

CRITICAL REQUIREMENT - TITLE ID USAGE:
- Each title has an "id" field with a UUID (e.g., "094faf99-124a-47fc-b213-f743497d7f30")
- In supporting_title_ids, you MUST use these exact UUID values, NOT array indices
- DO NOT use numbers like 0, 1, 2, 3 - use the actual "id" field values
- Example: Use ["094faf99-124a-47fc-b213-f743497d7f30", "a005e6ba-f1e2-4007-9cf7-cd9584c339e1"]

FRAMED NARRATIVE REQUIREMENTS (FN should answer):
- WHY: According to the sources' claims - causation, motivation, blame, justification
- HOW: The stance/position taken by outlets on the event
- EVIDENCE: Exact quotes from headlines that support this framing

STRICT EVIDENCE REQUIREMENTS:
- Every FN MUST include exact headline phrases in quotes
- Every claim about framing MUST be supported by specific language
- NO analysis without direct textual evidence
- Quote the EXACT words that reveal stance/framing
- Include multiple examples if available
- Specify which headlines contain the evidence

ANALYSIS REQUIREMENTS:
- Extract exact phrases that reveal framing (in quotes)
- Assess prevalence of each narrative (count supporting headlines)
- Rate evidence quality based on clarity and directness
- Identify frame types (evaluative, causal, attribution, etc.)
- Link each headline to specific framing claims

Respond in JSON format with framed narratives, exact evidence quotes, and analysis.
"""


# ============================================================================
# SECTION 2: FORMATTING UTILITIES
# Shared formatting functions used across all prompts
# ============================================================================


def format_title_list(
    titles: List[Dict[str, Any]],
    include_source: bool = True,
    include_id: bool = True,
    include_date: bool = True,
    include_language: bool = False,
    include_actors: bool = False,
    max_titles: int = None,
) -> str:
    """
    Standard title list formatting used across all prompts.

    Args:
        titles: List of title dictionaries
        include_source: Include source/publisher name
        include_id: Include title UUID
        include_date: Include publication date
        include_language: Include detected language
        include_actors: Include extracted actors
        max_titles: Maximum number of titles to format

    Returns:
        Formatted title list string

    Example output:
        Title 1: "NATO announces deployment"
          ID: abc-123
          Source: reuters.com
          Date: 2024-10-06
    """
    if max_titles:
        titles = titles[:max_titles]

    formatted_lines = []
    for i, title in enumerate(titles, 1):
        title_text = title.get("text", title.get("title_display", "N/A"))
        formatted_lines.append(f"Title {i}: {title_text}")

        if include_id:
            title_id = title.get("id", "N/A")
            formatted_lines.append(f"  ID: {title_id}")

        if include_source:
            source = title.get("source", title.get("publisher_name", "Unknown"))
            formatted_lines.append(f"  Source: {source}")

        if include_date:
            date = title.get("pubdate_utc", title.get("date", "Unknown"))
            formatted_lines.append(f"  Date: {date}")

        if include_language:
            language = title.get("language", title.get("detected_language", "Unknown"))
            formatted_lines.append(f"  Language: {language}")

        if include_actors:
            actors = title.get("gate_actors", title.get("actors", "None"))
            formatted_lines.append(f"  Gate Actors: {actors}")

        formatted_lines.append("")  # Empty line between titles

    return "\n".join(formatted_lines)


def format_title_list_simple(
    titles: List[Dict[str, Any]], include_date: bool = True, max_titles: int = None
) -> str:
    """
    Simple title list formatting for enrichment prompts.

    Args:
        titles: List of title dictionaries
        include_date: Include publication date
        max_titles: Maximum number of titles to format

    Returns:
        Formatted title list string

    Example output:
        1. "NATO announces deployment" (2024-10-06)
        2. "Russia responds to NATO" (2024-10-07)
    """
    if max_titles:
        titles = titles[:max_titles]

    formatted_lines = []
    for i, title in enumerate(titles, 1):
        title_text = title.get("text", title.get("title_display", "N/A"))

        if include_date:
            date_str = title.get("pubdate_utc", "unknown")
            # Extract date portion if datetime
            if isinstance(date_str, str) and "T" in date_str:
                date_str = date_str.split("T")[0]
            elif hasattr(date_str, "strftime"):
                date_str = date_str.strftime("%Y-%m-%d")

            formatted_lines.append(f"{i}. {title_text} ({date_str})")
        else:
            formatted_lines.append(f"{i}. {title_text}")

    return "\n".join(formatted_lines)


def format_actor_list(actors: List[str]) -> str:
    """
    Standard actor list formatting.

    Args:
        actors: List of actor names

    Returns:
        Comma-separated actor string
    """
    if not actors:
        return "Various actors"
    return ", ".join(actors)


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
    Extract magnitude information from title text using regex patterns.

    Args:
        titles: List of title dictionaries

    Returns:
        List of magnitude dictionaries with value, unit, and context
    """
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

                    magnitudes.append({"value": value, "unit": unit, "what": what_text})
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


# ============================================================================
# SECTION 2: PROMPT HELPER FUNCTIONS
# Functions to build prompts from templates
# ============================================================================


def build_aat_extraction_prompt(title_text: str) -> tuple[str, str]:
    """Build AAT extraction prompt for a title"""
    system = AAT_EXTRACTION_SYSTEM_PROMPT
    user = AAT_EXTRACTION_USER_TEMPLATE.format(title=title_text)
    return system, user


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
        event_types=EVENT_TYPES,
        titles=format_titles_for_incident_analysis(titles),
    )
    return system, user


def build_seed_validation_prompt(title_text: str, brief_theme: str) -> tuple[str, str]:
    """Build seed validation micro-prompt"""
    system = SEED_VALIDATION_SYSTEM_PROMPT
    user = SEED_VALIDATION_USER_TEMPLATE.format(
        title_text=title_text, brief_theme=brief_theme
    )
    return system, user


def build_thematic_validation_prompt(
    title_text: str, strategic_purpose: str
) -> tuple[str, str]:
    """Build thematic validation micro-prompt"""
    system = THEMATIC_VALIDATION_SYSTEM_PROMPT
    user = THEMATIC_VALIDATION_USER_TEMPLATE.format(
        title_text=title_text, strategic_purpose=strategic_purpose
    )
    return system, user


def build_ef_merge_prompt(
    ef1_strategic_purpose: str, ef2_strategic_purpose: str
) -> tuple[str, str]:
    """Build EF merge micro-prompt"""
    system = EF_MERGE_SYSTEM_PROMPT
    user = EF_MERGE_USER_TEMPLATE.format(
        ef1_strategic_purpose=ef1_strategic_purpose,
        ef2_strategic_purpose=ef2_strategic_purpose,
    )
    return system, user


def build_ef_split_prompt(
    ef_title: str, strategic_purpose: str, title_list: str, title_count: int
) -> tuple[str, str]:
    """Build EF split micro-prompt"""
    system = EF_SPLIT_SYSTEM_PROMPT
    user = EF_SPLIT_USER_TEMPLATE.format(
        ef_title=ef_title,
        strategic_purpose=strategic_purpose,
        title_list=title_list,
        title_count=title_count,
    )
    return system, user


def build_classification_prompt(titles: list) -> tuple[str, str]:
    """Legacy function - kept for backward compatibility"""
    system = "Classify titles into theater and event type."
    user = "Classify these titles:\n" + format_titles_for_clustering(titles)
    return system, user


# ============================================================================
# SECTION 3: LLM CLIENT
# Unified HTTP client for all LLM interactions
# ============================================================================


class LLMClient:
    """
    Unified LLM client for all pipeline phases.
    Consolidates all LLM interactions into a single client with phase-specific methods.
    """

    def __init__(self):
        self.config = get_config()
        self._load_taxonomies()

    def _load_taxonomies(self) -> None:
        """Load event type and theater taxonomies from CSV files"""
        data_path = Path(__file__).parent.parent / "data"

        # Load event types
        self.event_types: List[Dict[str, str]] = []
        event_types_path = data_path / "event_types.csv"
        if event_types_path.exists():
            with open(event_types_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.event_types = list(reader)

        # Load theaters
        self.theaters: List[Dict[str, str]] = []
        theaters_path = data_path / "theaters.csv"
        if theaters_path.exists():
            with open(theaters_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.theaters = list(reader)

    # -------------------------------------------------------------------------
    # Phase 2: Strategic Filtering
    # -------------------------------------------------------------------------

    async def strategic_review(self, title: str, debug: bool = False) -> Dict[str, Any]:
        """
        Determine if a title is strategically significant and extract entities.

        Args:
            title: Title text to review
            debug: If True, request reason field (slower, for debugging)

        Returns:
            Dict with:
                - is_strategic (bool): True if strategic, False if not
                - entities (List[str]): Extracted raw entity names (not yet matched to entity_ids)
                - reason (str, optional): Brief explanation (only if debug=True)
        """
        try:
            # Adjust max_tokens based on debug mode
            max_tokens = 150 if debug else 80

            user_prompt = STRATEGIC_REVIEW_USER.format(title=title)
            response = await self._call_llm(
                system_prompt=STRATEGIC_REVIEW_SYSTEM,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=0.0,
            )

            # Parse JSON response
            try:
                response_data = self._extract_json(response)
                is_strategic = bool(response_data.get("strategic", 0))
                entities = response_data.get("entities", [])

                if is_strategic:
                    logger.debug(
                        f"LLM flagged as strategic: '{title[:50]}' | Entities: {entities[:3]}"
                    )
                else:
                    logger.debug(f"LLM flagged as non-strategic: '{title[:50]}'")

                return {
                    "is_strategic": is_strategic,
                    "entities": entities if isinstance(entities, list) else [],
                }

            except (json.JSONDecodeError, ValueError) as parse_error:
                # Fallback: Try to parse as legacy "0" or "1" format
                response_clean = response.strip().lower()
                if "1" in response_clean:
                    logger.warning(
                        f"LLM returned legacy format '1' for '{title[:50]}', parsing as strategic"
                    )
                    return {"is_strategic": True, "entities": []}
                elif "0" in response_clean:
                    logger.warning(
                        f"LLM returned legacy format '0' for '{title[:50]}', parsing as non-strategic"
                    )
                    return {"is_strategic": False, "entities": []}
                else:
                    logger.error(
                        f"Failed to parse LLM response for '{title[:50]}': {parse_error} | "
                        f"Response: {response[:100]}"
                    )
                    return {"is_strategic": False, "entities": []}

        except Exception as e:
            logger.error(f"LLM strategic review failed for '{title[:50]}': {e}")
            return {"is_strategic": False, "entities": []}

    # -------------------------------------------------------------------------
    # Phase 3: Event Family Generation
    # -------------------------------------------------------------------------

    async def assemble_event_families(
        self, request: LLMEventFamilyRequest
    ) -> LLMEventFamilyResponse:
        """
        Assemble Event Families directly from titles.

        Args:
            request: Event Family assembly request with title contexts

        Returns:
            LLM response with Event Families and reasoning
        """
        try:
            # Build comprehensive prompt with title data
            user_prompt = self._build_event_family_prompt(request)

            # Call LLM with structured request
            response_text = await self._call_llm(
                system_prompt=EVENT_FAMILY_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=self.config.llm_max_tokens_ef,
                temperature=self.config.llm_temperature,
            )

            # Parse and validate response
            return self._parse_event_family_response(response_text)

        except Exception as e:
            logger.error(f"Event Family assembly failed: {e}")
            raise

    def _build_event_family_prompt(self, request: LLMEventFamilyRequest) -> str:
        """Build comprehensive prompt for Event Family generation"""
        prompt_parts = [
            "TASK: Analyze these strategic news titles and identify coherent Event Families.",
            "",
            "STRATEGIC TITLES:",
        ]

        # Add title information directly
        titles_context = getattr(request, "title_context", [])
        formatted_titles = format_title_list(
            titles_context,
            include_source=True,
            include_id=True,
            include_date=True,
            include_language=True,
            include_actors=True,
        )
        prompt_parts.append(formatted_titles)

        # Add processing instructions
        prompt_parts.extend(
            [
                "",
                "INSTRUCTIONS:",
                request.processing_instructions,
                "",
                f"Maximum Event Families to create: {request.max_event_families}",
                "",
                "RESPONSE FORMAT (JSON):",
                "{",
                '  "event_families": [',
                "    {",
                '      "title": "Clear event title",',
                '      "summary": "Factual summary",',
                '      "key_actors": ["actor1"],',
                '      "event_type": "Strategy/Tactics",',
                '      "primary_theater": "THEATER_CODE",',
                '      "source_title_ids": ["title_id1"],',
                '      "confidence_score": 0.85,',
                '      "coherence_reason": "Why coherent"',
                "    }",
                "  ],",
                '  "processing_reasoning": "Overall reasoning",',
                '  "confidence": 0.8,',
                '  "warnings": []',
                "}",
            ]
        )

        return "\n".join(prompt_parts)

    # -------------------------------------------------------------------------
    # Phase 4: Enrichment
    # -------------------------------------------------------------------------

    async def canonicalize_actors(
        self,
        ef_title: str,
        event_type: str,
        primary_theater: str,
        member_titles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Extract canonical actors, roles, and policy status.

        Args:
            ef_title: Event Family title
            event_type: Event type classification
            primary_theater: Primary theater
            member_titles: List of member title dictionaries

        Returns:
            Parsed response with canonical actors and metadata
        """
        # Build prompt
        formatted_titles = format_title_list_simple(
            member_titles, include_date=True, max_titles=5
        )
        user_prompt = CANONICALIZE_USER_TEMPLATE.format(
            ef_title=ef_title,
            event_type=event_type,
            primary_theater=primary_theater,
            member_titles=formatted_titles,
        )

        # Call LLM
        response_text = await self._call_llm(
            system_prompt=CANONICALIZE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=self.config.llm_max_tokens_enrichment,
            temperature=self.config.llm_temperature,
        )

        # Parse JSON response
        return self._extract_json(response_text)

    async def enhance_narrative_summary(
        self,
        ef_title: str,
        current_summary: str,
        event_type: str,
        primary_theater: str,
        canonical_actors: List[str],
        member_titles: List[Dict[str, Any]],
    ) -> str:
        """
        Enhance Event Family summary with narrative structure.

        Args:
            ef_title: Event Family title
            current_summary: Current EF summary
            event_type: Event type classification
            primary_theater: Primary theater
            canonical_actors: List of canonical actor names
            member_titles: List of member title dictionaries

        Returns:
            Enhanced summary text (80-120 words)
        """
        # Build prompt
        formatted_titles = format_title_list_simple(
            member_titles, include_date=True, max_titles=3
        )
        actors_text = format_actor_list(canonical_actors)

        user_prompt = NARRATIVE_SUMMARY_USER_TEMPLATE.format(
            ef_title=ef_title,
            current_summary=current_summary,
            primary_theater=primary_theater,
            event_type=event_type,
            canonical_actors=actors_text,
            member_titles=formatted_titles,
        )

        # Call LLM
        response_text = await self._call_llm(
            system_prompt=NARRATIVE_SUMMARY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=self.config.llm_max_tokens_enrichment,
            temperature=self.config.llm_temperature,
        )

        return response_text.strip()

    async def assess_macro_link(
        self,
        ef_title: str,
        ef_summary: str,
        event_type: str,
        primary_theater: str,
        canonical_actors: List[str],
        available_centroids: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Assess which narrative centroid this EF belongs to.

        Args:
            ef_title: Event Family title
            ef_summary: Current EF summary
            event_type: Event type classification
            primary_theater: Primary theater
            canonical_actors: List of canonical actor names
            available_centroids: List of centroid dictionaries from database

        Returns:
            Parsed response with macro_link and context assessment
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
        actors_text = format_actor_list(canonical_actors)

        # Build prompt
        system_prompt = MACRO_LINK_SYSTEM_PROMPT.format(
            available_centroids=centroids_list
        )
        user_prompt = MACRO_LINK_USER_TEMPLATE.format(
            ef_title=ef_title,
            ef_summary=ef_summary,
            canonical_actors=actors_text,
            primary_theater=primary_theater,
            event_type=event_type,
        )

        # Call LLM
        response_text = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=self.config.llm_max_tokens_enrichment,
            temperature=self.config.llm_temperature,
        )

        # Parse JSON response
        return self._extract_json(response_text)

    # -------------------------------------------------------------------------
    # Phase 5: Framed Narrative Generation
    # -------------------------------------------------------------------------

    async def generate_framed_narratives(
        self, request: LLMFramedNarrativeRequest
    ) -> LLMFramedNarrativeResponse:
        """
        Generate Framed Narratives for an Event Family.

        Args:
            request: Framed Narrative generation request

        Returns:
            LLM response with Framed Narratives and analysis
        """
        try:
            # Build prompt with Event Family context and titles
            user_prompt = self._build_framed_narrative_prompt(request)

            # Call LLM with framing analysis focus
            response_text = await self._call_llm(
                system_prompt=FRAMED_NARRATIVE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=self.config.llm_max_tokens_fn,
                temperature=self.config.llm_temperature,
            )

            # Parse and validate response
            return self._parse_framed_narrative_response(response_text)

        except Exception as e:
            logger.error(f"Framed Narrative generation failed: {e}")
            raise

    def _build_framed_narrative_prompt(self, request: LLMFramedNarrativeRequest) -> str:
        """Build comprehensive prompt for Framed Narrative generation"""
        ef = request.event_family

        prompt_parts = [
            "TASK: Analyze how different outlets frame this Event Family and identify distinct Framed Narratives.",
            "",
            "EVENT FAMILY:",
            f"Title: {ef.title}",
            f"Summary: {ef.summary}",
            f"Key Actors: {', '.join(ef.key_actors)}",
            f"Event Type: {ef.event_type}",
            f"Geography: {ef.primary_theater or 'Not specified'}",
            "",
            "HEADLINES TO ANALYZE:",
        ]

        # Add title contexts
        for title in request.titles_context:
            prompt_parts.append(
                f"  - {title.get('text', 'N/A')} [{title.get('source', 'Unknown')}]"
            )

        prompt_parts.extend(
            [
                "",
                "INSTRUCTIONS:",
                request.framing_instructions,
                "",
                f"Maximum Framed Narratives to create: {request.max_narratives}",
                "",
                "RESPONSE FORMAT (JSON):",
                """{
  "framed_narratives": [
    {
      "frame_type": "Type of framing (supportive/critical/neutral/etc)",
      "frame_description": "How this narrative frames the event",
      "stance_summary": "Clear evaluative/causal framing statement",
      "supporting_headlines": ["headline1", "headline2"],
      "supporting_title_ids": ["title_id1", "title_id2"],
      "key_language": ["phrase1", "phrase2"],
      "prevalence_score": 0.6,
      "evidence_quality": 0.8
    }
  ],
  "processing_reasoning": "Analysis methodology and reasoning",
  "confidence": 0.8,
  "dominant_frames": ["frame1", "frame2"]
}""",
            ]
        )

        return "\n".join(prompt_parts)

    # -------------------------------------------------------------------------
    # Core HTTP Communication
    # -------------------------------------------------------------------------

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Call the LLM with system and user prompts.
        Implements retry logic with exponential backoff.

        Args:
            system_prompt: System-level instructions
            user_prompt: User query/request
            max_tokens: Maximum tokens to generate (optional)
            temperature: Sampling temperature (optional)

        Returns:
            LLM response text
        """
        # Apply defaults if not specified
        if temperature is None:
            temperature = self.config.llm_temperature

        # Implement retry logic with exponential backoff
        for attempt in range(self.config.llm_retry_attempts):
            try:
                headers = {
                    "Authorization": f"Bearer {self.config.deepseek_api_key}",
                    "Content-Type": "application/json",
                }

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]

                payload = {
                    "model": self.config.llm_model,
                    "messages": messages,
                    "temperature": temperature,
                }

                # Only add max_tokens if explicitly specified
                if max_tokens is not None:
                    payload["max_tokens"] = max_tokens

                async with httpx.AsyncClient(
                    timeout=self.config.llm_timeout_seconds
                ) as client:
                    response_data = await client.post(
                        f"{self.config.deepseek_api_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )

                    if response_data.status_code != 200:
                        raise Exception(
                            f"LLM API error: {response_data.status_code} - {response_data.text}"
                        )

                    data = response_data.json()
                    response = data["choices"][0]["message"]["content"].strip()

                logger.debug(
                    "LLM call successful",
                    attempt=attempt + 1,
                    prompt_length=len(user_prompt),
                    response_length=len(response),
                )

                return response

            except Exception as e:
                is_last_attempt = attempt == self.config.llm_retry_attempts - 1
                if is_last_attempt:
                    logger.error(
                        f"LLM call failed after {self.config.llm_retry_attempts} attempts: {e}"
                    )
                    raise
                else:
                    # Exponential backoff with jitter
                    delay = (self.config.llm_retry_backoff**attempt) + (0.1 * attempt)
                    logger.warning(
                        f"LLM call attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)

    def _call_llm_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Synchronous version of _call_llm for Phase 3.5 micro-prompts.

        Args:
            system_prompt: System-level instructions
            user_prompt: User query/request
            max_tokens: Maximum tokens to generate (optional)
            temperature: Sampling temperature (optional)

        Returns:
            LLM response text
        """
        # Apply defaults if not specified
        if temperature is None:
            temperature = self.config.llm_temperature

        # Implement retry logic
        for attempt in range(self.config.llm_retry_attempts):
            try:
                headers = {
                    "Authorization": f"Bearer {self.config.deepseek_api_key}",
                    "Content-Type": "application/json",
                }

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]

                payload = {
                    "model": self.config.llm_model,
                    "messages": messages,
                    "temperature": temperature,
                }

                # Only add max_tokens if explicitly specified
                if max_tokens is not None:
                    payload["max_tokens"] = max_tokens

                with httpx.Client(timeout=self.config.llm_timeout_seconds) as client:
                    response_data = client.post(
                        f"{self.config.deepseek_api_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )

                    if response_data.status_code != 200:
                        raise Exception(
                            f"LLM API error: {response_data.status_code} - {response_data.text}"
                        )

                    data = response_data.json()
                    response = data["choices"][0]["message"]["content"].strip()

                logger.debug(
                    "LLM sync call successful",
                    attempt=attempt + 1,
                    prompt_length=len(user_prompt),
                    response_length=len(response),
                )

                return response

            except Exception as e:
                is_last_attempt = attempt == self.config.llm_retry_attempts - 1
                if is_last_attempt:
                    logger.error(
                        f"LLM sync call failed after {self.config.llm_retry_attempts} attempts: {e}"
                    )
                    raise
                else:
                    # Exponential backoff
                    import time

                    delay = (self.config.llm_retry_backoff**attempt) + (0.1 * attempt)
                    logger.warning(
                        f"LLM sync call attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)

    # -------------------------------------------------------------------------
    # Response Parsing
    # -------------------------------------------------------------------------

    def _parse_event_family_response(
        self, response_text: str
    ) -> LLMEventFamilyResponse:
        """Parse and validate Event Family response from LLM"""
        try:
            # Extract JSON from response
            response_data = self._extract_json(response_text)

            # Validate required fields
            if "event_families" not in response_data:
                raise ValueError("Missing 'event_families' in LLM response")

            return LLMEventFamilyResponse(
                event_families=response_data["event_families"],
                processing_reasoning=response_data.get("processing_reasoning", ""),
                confidence=response_data.get("confidence", 0.5),
                warnings=response_data.get("warnings", []),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Event Family JSON response: {e}")
            raise ValueError(f"Invalid JSON in LLM response: {e}")

    def _parse_framed_narrative_response(
        self, response_text: str
    ) -> LLMFramedNarrativeResponse:
        """Parse and validate Framed Narrative response from LLM"""
        try:
            # Extract JSON from response
            response_data = self._extract_json(response_text)

            # Validate required fields
            if "framed_narratives" not in response_data:
                raise ValueError("Missing 'framed_narratives' in LLM response")

            return LLMFramedNarrativeResponse(
                framed_narratives=response_data["framed_narratives"],
                processing_reasoning=response_data.get("processing_reasoning", ""),
                confidence=response_data.get("confidence", 0.5),
                dominant_frames=response_data.get("dominant_frames", []),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Framed Narrative JSON response: {e}")
            raise ValueError(f"Invalid JSON in LLM response: {e}")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response text"""
        try:
            # Try parsing as direct JSON first
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # Try to find JSON within markdown code blocks
            patterns = [
                r"```json\s*(.*?)\s*```",  # Standard: ```json ... ```
                r"```\s*(.*?)\s*```",  # Generic: ``` ... ```
                r"`json\s*(.*?)\s*`",  # Single backtick: `json ... `
            ]

            for pattern in patterns:
                markdown_match = re.search(pattern, text, re.DOTALL)
                if markdown_match:
                    try:
                        json_content = markdown_match.group(1).strip()
                        # Only try if it looks like JSON (starts with {)
                        if json_content.startswith("{"):
                            return json.loads(json_content)
                    except json.JSONDecodeError:
                        continue

            # Fallback: try to find any JSON object in the text
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            raise ValueError(f"No valid JSON found in response: {text}")


# ============================================================================
# GLOBAL CLIENT INSTANCE
# ============================================================================

_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get global LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


# Backward compatibility aliases
def get_gen1_llm_client() -> LLMClient:
    """Backward compatibility alias for get_llm_client"""
    return get_llm_client()


Gen1LLMClient = LLMClient  # Class alias for backward compatibility
