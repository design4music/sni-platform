"""
Consolidated LLM Prompts for SNI Pipeline

All active prompts in one place for easy maintenance and optimization.
Version: 4.0 (deduplicated prose rules + shared event summary preamble)

Prompts by Phase:
- Phase 3: Intel Gating + Track Assignment
- Phase 3.5: Label + Signal Extraction
- Phase 4.1: Topic Consolidation (Anchor-Candidate Dedup)
- Phase 4.3: Cross-Bucket Event Merging
- Phase 4.5: CTM Summary Generation
- Phase 4.5a: Event Summary Generation
- Epics: Build, Enrich, Narratives
- Freeze: Centroid Summaries, Signal Rankings
- Coherence Check (extraction API)
"""

# --- SHARED PROSE WRITING RULES ---

PROSE_RULES = """\
WRITING RULES:

CAUSALITY: Never invent causal links. No "triggered", "led to", "caused", "resulted in", "prompted", "sparked". Describe events separately.

ROLES: Only use titles/roles from headlines. Never add roles from training data. Never add "Former" unless headline says so. When in doubt, use name only.

TONE: 100% neutral. No value judgments, no "cynically/brazenly/aggressively". Present all sides equally. No sensationalism. Avoid "perceived" when facts are evident.

TROLLING: Treat officials' comments on adversaries' disputes as rhetorical exploitation, not policy. Use "mocked/seized on/exploited rhetorically", not "welcomed/supported". Omit absurd provocations."""

PROSE_WRITING_RULES = PROSE_RULES  # legacy alias

# --- PHASE 3: INTEL GATING ---

INTEL_GATING_PROMPT = """You are an intelligence analyst reviewing {num_titles} news titles for {centroid_label}.

TASK: Identify which titles contain strategic intelligence value. Be INCLUSIVE - when in doubt, mark as strategic.

STRATEGIC (ACCEPT): Government policy/legislation/regulations, international relations/diplomacy/summits, military/defense/security/terrorism, economic policy/trade/sanctions/tariffs, energy markets/supply disruptions, elections/protests/coups/transitions, court rulings with policy implications, strategic resources (water/minerals/food), technology with geopolitical impact (semiconductors/AI/cyber), major industrial policy/labor disputes.

NON-STRATEGIC (REJECT):
- SPORTS: reject all athletics, leagues, tournaments, player transfers, match results, standings, coaching. Sports leaks through via international events (Olympics, World Cup) and conflict language ("battle", "attack", "defense"). Still reject - no strategic value.
- Entertainment/celebrity, health/wellness tips, recipes, lifestyle
- Local crime without systemic implications, human interest stories
- Real estate ads, local business openings
- Weather forecasts (unless major disaster)

Titles:
{titles_text}

Return ONLY valid JSON: {{"strategic": [1,3,5], "reject": [2,4,6]}}

When uncertain, prefer STRATEGIC - we want comprehensive coverage."""

# --- PHASE 3: TRACK ASSIGNMENT ---

TRACK_ASSIGNMENT_PROMPT = """You are classifying {num_titles} strategic news titles for {centroid_label}.

Choose the ONE best track for each title based on its dominant theme.

Tracks:
{tracks_list}

Context: {centroid_label} | {month}

Titles:
{titles_text}

Return ONLY valid JSON: {{"1": "track_name", "2": "track_name"}}"""

# --- PHASE 3.5: LABEL + SIGNAL EXTRACTION ---

LABEL_SIGNAL_EXTRACTION_PROMPT = """You are an expert news analyst. Extract structured event labels AND typed signals from news titles.

## PART 1: EVENT LABEL
Format: ACTOR -> ACTION_CLASS -> DOMAIN -> TARGET (TARGET is REQUIRED; use "NONE" for non-directed events)

ACTION CLASSES (7-tier hierarchy - lower tier = higher priority):
{action_classes}

DOMAINS:
{domains}

ACTOR TYPES:
{actors}

{priority_rules}

{target_rules}

## PART 2: SIGNALS
Extract typed signals from each title (4 categories):
- persons: LAST_NAME only, uppercase (TRUMP, POWELL, ZELENSKY)
- orgs: Organizations/companies/armed groups, uppercase (NATO, FED, NVIDIA, HAMAS, ISIS)
- places: Sub-national locations, Title case (Crimea, Gaza, Greenland). NO COUNTRIES.
- named_events: Named operations/summits/conferences, Title case (G20 Summit, COP28, Operation Epic Fury)

SIGNAL RULES:
- ENGLISH ONLY - translate foreign terms (Pekin->Beijing, Donetsk->Donetsk)
- NO PUBLISHERS as orgs (WSJ, Reuters, BBC, CNN). Companies/armed groups -> orgs.

## PART 3: ENTITY COUNTRIES
Map entities to PRIMARY country using ISO 2-letter codes: {{"ENTITY_NAME": "ISO_CODE", ...}}

COUNTRY ADJECTIVES: ANY adjective -> ISO code (French->FR, Ukrainian->UA, German->DE, British->GB). Declined forms in any language -> normalize.

ENTITY MAPPINGS: Politicians -> country of office (MACRON->FR, RUBIO->US). Companies -> HQ (TSMC->TW, BOEING->US). Sub-national places -> parent (Crimea->UA, Greenland->DK). Systems -> owner (Nord Stream->RU). IGOs -> org code (NATO->NATO). Armed groups -> special codes (HAMAS->PS, ISIS->ISIS).

SKIP: Country names themselves (US, China, France) - handled separately.

## PART 4: SECTOR + SUBJECT
Classify each title into a SECTOR (required) and SUBJECT (optional, use null if no good fit).
Pick the ONE most relevant sector and subject. These are CONTROLLED VOCABULARIES -- use ONLY these values.

SECTORS and their SUBJECTS:
- MILITARY: NUCLEAR, NAVAL, AERIAL, MISSILE, GROUND_FORCES, AIR_DEFENSE, DRONE, SPACE
- INTELLIGENCE: ESPIONAGE, SURVEILLANCE, COVERT_OPERATION
- SECURITY: TERRORISM, INSURGENCY, ORGANIZED_CRIME, CIVIL_UNREST, BORDER_SECURITY
- DIPLOMACY: TREATY, ALLIANCE, MEDIATION, RECOGNITION, HUMANITARIAN_CORRIDOR
- GOVERNANCE: ELECTION, LEGISLATION, JUDICIAL, EXECUTIVE_ACTION, CONSTITUTIONAL, CORRUPTION
- ECONOMY: TRADE, SANCTIONS, INVESTMENT, DEBT_FINANCE, CURRENCY, LABOR, TAXATION
- ENERGY_RESOURCES: OIL_GAS, RENEWABLE, MINING, RARE_EARTH, WATER, FOOD_AGRICULTURE
- TECHNOLOGY: AI, SEMICONDUCTORS, TELECOM, BIOTECH, CYBER, SOCIAL_MEDIA
- HEALTH_ENVIRONMENT: PANDEMIC, CLIMATE, POLLUTION, NATURAL_DISASTER, PUBLIC_HEALTH
- SOCIETY: MIGRATION, RELIGION, EDUCATION, MEDIA_PRESS, DEMOGRAPHICS, HUMAN_RIGHTS
- INFRASTRUCTURE: TRANSPORT, SHIPPING, CONSTRUCTION, SUPPLY_CHAIN, POWER_GRID

Examples: "Macron increases nuclear arsenal" -> MILITARY/NUCLEAR. "Oil prices surge" -> ENERGY_RESOURCES/OIL_GAS. "FBI investigates bar shooting" -> SECURITY/TERRORISM. "EU tariffs on China" -> ECONOMY/TRADE. "Carrier deployed to Mediterranean" -> MILITARY/NAVAL.

## OUTPUT
Return JSON array:
[{{"idx": 1, "actor": "US_EXECUTIVE", "action": "POLICY_CHANGE", "domain": "ECONOMY", "target": "CN", "conf": 0.9, "sector": "ECONOMY", "subject": "TRADE", "persons": ["TRUMP"], "orgs": [], "places": [], "named_events": [], "entity_countries": {{"TRUMP": "US"}}}}]

Country prefixes for state actors: US_, RU_, CN_, UK_, FR_, DE_. IGOs without prefix: UN, NATO, EU. TARGET: ISO codes or canonical names. conf 0.0-1.0. Return ONLY valid JSON. Empty arrays [] for no matches."""

# --- PHASE 4.1: ANCHOR-CANDIDATE TOPIC CONSOLIDATION ---

DEDUP_CONFIRM_SYSTEM_PROMPT = """You are a conservative duplicate detector for news event clusters.
Your ONLY job: for each CANDIDATE, decide if it is a true duplicate of one specific ANCHOR.
TRUE DUPLICATE = both cover the EXACT SAME real-world story (not "same theme" or "same sector").

KEEP SEPARATE (return "none"): same actor but different actions ("Trump tariffs" vs "Trump Greenland"), same theme but different events, same company but different news, one is a subset of a broader topic, different time periods (unless headlines clearly overlap).

MERGE (return anchor_id): headlines describe the EXACT same development from different sources/angles, different languages covering the same event, minor wording variations.

When in doubt, keep SEPARATE. A missed merge is harmless. A wrong merge destroys data."""

DEDUP_CONFIRM_USER_PROMPT = """CTM: {centroid_label} / {track} / {month}

ANCHORS (existing events -- identity is fixed):
{anchors_text}

CANDIDATES (check if each duplicates an anchor):
{candidates_text}

For each candidate: is it a TRUE DUPLICATE of exactly one anchor?
Return JSON: {{"matches": [{{"candidate_id": "...", "anchor_id": "..." or "none", "confidence": 0.0-1.0}}]}}
Every candidate_id must appear exactly once. confidence 0.7+ = merge. When in doubt, "none"."""

CATCHALL_RESCUE_SYSTEM_PROMPT = """You assign unclustered news headlines to existing event clusters.
Assign ONLY if headline clearly covers the SAME specific story (not just same theme/sector).
If no clear match, assign "none". When in doubt, "none" is always safe."""

CATCHALL_RESCUE_USER_PROMPT = """CTM: {centroid_label} / {track} / {month}

EVENTS (existing clusters):
{events_text}

UNCLUSTERED HEADLINES:
{headlines_text}

Assign each headline to the event covering the SAME specific story, or "none".
Return JSON: {{"assignments": [{{"index": 0, "anchor_id": "..." or "none"}}]}}
Every index must appear exactly once. Only assign if headline clearly belongs to that event."""

# --- PHASE 4.3: CROSS-BUCKET MERGE ---

MERGE_SYSTEM_PROMPT = """You identify news events that describe the SAME real-world story \
within a country's intelligence briefing.

Events may appear separate because they entered through different geographic angles \
(domestic vs bilateral) or because early clustering split them before the full picture emerged. \
Your job: find groups that are clearly the SAME story and should be merged.

MERGE when:
- Events describe the same core development from different angles (domestic vs international framing)
- Events cover the same specific action/decision but emphasize different actors involved

KEEP SEPARATE when:
- Events share a theme but cover genuinely different developments
- Events involve the same actors but different actions (e.g., "Trump tariffs" vs "Trump Greenland")
- Events are different military operations, even if part of the same war (e.g., "carrier deployment" vs "nuclear doctrine shift" vs "anti-drone systems to Cyprus" are THREE separate events)
- Events involve the same country pair but different topics
- Connection is only thematic (both about "economy" or "security" is NOT enough)
- One event is about government policy and the other about private sector activity
- Events are related sub-stories within a broader crisis but involve different specific actions or decisions

When in doubt, keep SEPARATE. A wrong merge destroys information. A missed merge is harmless.

For each merged group, also produce:
- An updated title (under 120 chars) that captures the full story
- An updated summary (2-4 sentences) written from the centroid's perspective -- \
prioritize how this story matters to and is framed by the centroid country"""

MERGE_USER_PROMPT = """CTM: {centroid_label} / {track} / {month}

Events (ID, bucket, sources, title, summary):
{events_text}

Which events describe the SAME real-world story and should be merged?
Return JSON: {{"groups": [{{"event_ids": ["id1", "id2"], "updated_title": "...", "updated_summary": "2-4 sentences."}}]}}
Only groups of 2+. If none needed: {{"groups": []}}. IDs must be valid. Each event in at most one group. updated_title under 120 chars."""

# --- PHASE 4.5: CTM SUMMARY GENERATION ---

CTM_SUMMARY_SYSTEM_PROMPT = (
    """You are a strategic intelligence analyst writing monthly summary reports.
Generate a 150-250 word narrative digest from the provided event summaries.

You receive event summaries grouped into DOMESTIC AFFAIRS and INTERNATIONAL RELATIONS blocks.
Each summary has a source count indicating significance (higher = more significant).
If only one block is provided, all events belong to that category.

Requirements:
* Synthesize into a cohesive monthly digest
* Weight by source count: [137 sources] >> [12 sources] in importance
* Maintain analytic, neutral, non-normative tone
* Preserve key details: names, figures, outcomes
* ONLY use information from the provided event summaries

Structure:
* BOTH categories provided: "### Domestic" header + 1-2 paragraphs, then "### International" header + 1-2 paragraphs
* ONE category only: 2-3 paragraphs without section headers
* Lead with most significant developments. Do NOT force unrelated events into false coherence.

Do NOT: list bullet points, include source counts, use sensational language, add info not present, speculate.

"""
    + PROSE_RULES
    + """

---
**Centroid / Structural focus:**
{centroid_focus}"""
)

CTM_SUMMARY_USER_PROMPT = """{context}

{events_text}

Generate a 150-250 word monthly digest:"""

# --- PHASE 4.5A: EVENT SUMMARY GENERATION ---

_EVENT_SUMMARY_SHARED = """\
TITLE: 5-12 words, plain language, no jargon. Focus on WHAT happened, not WHO.
Do NOT add titles/roles unless in headlines (training data outdated).
Do NOT invent information. No editorializing."""

_EVENT_SUMMARY_AUDIENCE = (
    "You explain news topics in plain, conversational language for a general audience."
)

_EVENT_SUMMARY_IDENTIFY = (
    "Briefly identify unfamiliar people from context "
    '(e.g. "Powell, the Federal Reserve chair..." or "Dimon, who runs JPMorgan...").'
)

# -- Tier 1: TITLE-ONLY (1-4 sources) --
EVENT_SUMMARY_PROMPT_TITLE_ONLY = """Generate a short, plain-language news title (5-12 words) from these headlines.

Return JSON: {"title": "Short descriptive title", "summary": ""}

Rules:
- Describe the core story, not just a person or entity
- No jargon or abbreviations on first mention
- Do NOT add roles/titles unless they appear in the headlines
- Do NOT invent information"""

# -- Tier 2: MINI (5-10 sources) --
EVENT_SUMMARY_PROMPT_MINI = (
    """You explain news topics in plain, conversational language.

TASK: Generate a title and short summary from a cluster of headlines.
OUTPUT: Return JSON: {"title": "Short descriptive title (5-12 words)", "summary": "2-3 sentence factual summary"}

RULES:
"""
    + _EVENT_SUMMARY_SHARED
    + """
- Summary: state what happened in 2-3 sentences. Stick to facts from the headlines.
- Briefly identify unfamiliar people from headline context.
- If headlines cover unrelated stories, summarize only the dominant topic."""
)

# -- Tier 3: MEDIUM (11-50 sources) --
EVENT_SUMMARY_PROMPT_MEDIUM = (
    _EVENT_SUMMARY_AUDIENCE
    + """

TASK: Generate a title and summary for a news topic cluster.
OUTPUT: Return JSON: {"title": "Short descriptive title (5-12 words)", "summary": "Conversational explanation (1-2 paragraphs)"}

RULES:
"""
    + _EVENT_SUMMARY_SHARED
    + "\n"
    + """- Write 1-2 SHORT paragraphs with blank lines between them.
- Paragraph 1: What happened (the core event).
- Paragraph 2 (if needed): Key reactions, consequences, or context.
- """
    + _EVENT_SUMMARY_IDENTIFY
    + """
- Include key facts, numbers, and outcomes from headlines.
- Do NOT force unrelated headlines into false coherence.
- No phrases like "amid growing concerns" or "sparking debate".

"""
    + PROSE_RULES
)

# -- Tier 4: MAXI (51+ sources) --
EVENT_SUMMARY_PROMPT_MAXI = (
    _EVENT_SUMMARY_AUDIENCE
    + """

TASK: Generate a title and summary for a large news topic cluster.
OUTPUT: Return JSON: {"title": "Short descriptive title (5-12 words)", "summary": "Conversational explanation (2-3 paragraphs)"}

RULES:
"""
    + _EVENT_SUMMARY_SHARED
    + "\n"
    + """- Write 2-3 SHORT paragraphs with blank lines between them.
- Paragraph 1: What happened (the core event).
- Paragraph 2: Key reactions, consequences, or context.
- Paragraph 3 (if needed): Outcome or current status.
- """
    + _EVENT_SUMMARY_IDENTIFY
    + """
- Include key facts, numbers, and outcomes from headlines.
- If headlines cover unrelated stories, summarize only the dominant topic.
- No phrases like "amid growing concerns" or "sparking debate".

"""
    + PROSE_RULES
)

EVENT_SUMMARY_USER_PROMPT_TITLE = """Headlines ({num_titles} sources):

{titles_text}

Generate JSON:"""

EVENT_SUMMARY_USER_PROMPT = """Topic cluster ({num_titles} sources):

{titles_text}

Backbone signals: {backbone_signals}

Focus ONLY on headlines about the backbone signals above. Ignore tangential mentions. Describe the MAIN story the majority of headlines share.

Generate JSON:"""

# --- EPICS: SHARED ENRICHMENT RULES ---

EPIC_ENRICH_RULES = (
    """YOU HAVE TWO SOURCES:
1. REFERENCE MATERIAL (Wikipedia) - primary source for facts, names, dates, sequence. Trust it for accuracy.
2. EVENT DATA (news titles from our platform) - shows what topics were covered and from which countries. Use for geographic spread, angles, cross-country dynamics.

Synthesize both into an accurate, well-informed narrative. When they conflict on facts (names, dates, sequence), trust the reference. When event data covers angles/countries the reference does not, include those perspectives.

NEVER use facts from your training data. Only the two sources above.

DATES: Use specific dates only when stated in reference material. Event data dates are article PUBLISH dates (lag actual events by 1+ days) - do not treat as event dates. When no exact date is available, use "in early January", "mid-month", "by late January".

"""
    + PROSE_RULES
)

# --- EPICS: FILTER ---

EPIC_FILTER_SYSTEM = """You are filtering events for a cross-centroid news epic."""

EPIC_FILTER_USER = """The anchor signals are: {anchor_tags}

Below are {event_count} events that share these tags. Some genuinely belong to the epic. Others merely mention the keywords in passing.

EVENTS:
{event_list}

For each event, respond with ONLY a JSON array:
[{{"n": 1, "keep": true}}, {{"n": 2, "keep": false}}, ...]

keep=true if the event is primarily about this story or covers a direct consequence/reaction.
keep=false if the event mentions the topic in passing or is a roundup.

Return ONLY the JSON array, no other text."""

# --- EPICS: TITLE + SUMMARY ---

EPIC_TITLE_SUMMARY_USER = """You are naming a cross-centroid news story that appeared in many countries simultaneously.

Anchor tags: {anchor_tags}
Top events:
{event_list}

Respond with exactly two lines:
TITLE: <5-12 word headline for this story>
SUMMARY: <2-3 sentence factual summary of the story>

Be concise and factual. No editorializing."""

# --- EPICS: TIMELINE, NARRATIVES, CENTROID SUMMARIES ---
# All three share the same header: enrich_rules + title + ref_block + event_list

_EPIC_HEADER = """
{enrich_rules}

Story: {title}

{ref_block}
EVENT DATA (news coverage by country):
{event_list}
"""

EPIC_TIMELINE_USER = (
    """You are writing a chronological narrative of a major news story that unfolded across multiple countries.
"""
    + _EPIC_HEADER
    + """Write a chronological narrative (3-5 paragraphs) describing how this story unfolded during the month and across geography. Use the reference material for accurate facts, names, and dates. Use the event data to understand which countries covered the story and what angles received attention. Focus on:
- Key developments and escalations
- How different countries/regions reacted
- Important turning points

Write in past tense."""
)

EPIC_NARRATIVES_USER = (
    """You are analyzing a major news story that spanned multiple countries.
"""
    + _EPIC_HEADER
    + """Identify 3-5 distinct narrative threads or angles within this story. These should be genuinely different dimensions (e.g. diplomatic, economic, military, domestic politics, legal, humanitarian). Use the reference material for accurate details and the event data to understand cross-country coverage.

Respond with ONLY a JSON array:
[{{"title": "short title", "description": "2-3 sentence description"}}, ...]

Return ONLY the JSON array, no other text."""
)

EPIC_CENTROID_SUMMARIES_USER = (
    """You are summarizing how a global news story manifested across different countries and regions.
"""
    + _EPIC_HEADER
    + """For each country/region, write a 1-2 sentence summary of the key developments from that perspective. Use the reference material for accurate details and the event data for country-specific angles.

Respond with ONLY a JSON object:
{{"CENTROID_ID": "summary text", ...}}

Use the exact centroid IDs as keys. Return ONLY the JSON, no other text."""
)

# --- EPICS: NARRATIVE EXTRACTION (TWO-PASS) ---

NARRATIVE_PASS1_SYSTEM = """You are a media-framing analyst. You identify CONTESTED ideological frames where news outlets genuinely disagree about who is right, who is wrong, who is victim, who is aggressor."""

NARRATIVE_PASS1_USER = """Epic: {epic_title}
Summary: {epic_summary}
Month: {month}

Below are {sample_count} sampled headlines from various publishers covering this epic. Each headline is prefixed with [publisher].

{titles_block}

Identify 4-5 CONTESTED narrative frames used across these headlines.

RULES:
1. Each frame MUST assign moral roles (hero/villain, victim/aggressor, right/wrong)
2. Frames MUST be mutually exclusive -- a headline fitting Frame A should NOT fit Frame B
3. Frames should cleanly SEPARATE outlets that disagree
4. Prefer fewer, sharper frames over many overlapping ones

REJECT: Neutral/analytical frames everyone agrees on, topic descriptions (e.g. "Diplomatic efforts"), frames where both sides would say "yes, that describes our view".

GOOD examples: "Russian imperial aggression" (Russia=villain) vs "NATO provocation" (West=villain), "Trump's diplomatic triumph" (Trump=hero) vs "Dangerous overreach" (Trump=reckless).

Return a JSON array of 4-5 objects:
[{{"label": "short frame name", "description": "1-sentence explanation", "moral_frame": "who is hero/villain in this frame"}}]

Return ONLY the JSON array."""

NARRATIVE_PASS2_SYSTEM = """You classify news headlines into narrative frames. Assign each headline to exactly one frame label, or "neutral" if none fits."""

NARRATIVE_PASS2_USER = """Epic: {epic_title}

Available frames:
{frame_desc}

Classify each headline below into one of the frame labels above, or "neutral" if no frame fits.

{titles_block}

Return a JSON array with one entry per headline, in the same order:
[{{"n": 1, "frame": "label or neutral"}}]

Return ONLY the JSON array."""

# --- EVENT NARRATIVE EXTRACTION (single-pass for high-source events) ---

EVENT_NARRATIVE_SYSTEM = """You are a media-framing analyst. You identify the sharpest opposing narrative frames in news coverage. Focus on who is cast as right vs wrong, aggressor vs victim."""

EVENT_NARRATIVE_USER = """Event: {event_title}
Summary: {event_summary}
{wiki_block}
Below are {title_count} headlines covering this event. Each is prefixed with [date][publisher].

{titles_block}

Identify exactly 3 OPPOSING NARRATIVE FRAMES ("whose side is this headline on?"):
Frame 1: PRO-Side-A (e.g. "X is the aggressor/threat/villain")
Frame 2: PRO-Side-B (opposing view - "X is defending itself/justified")
Frame 3: NEUTRAL/THIRD-PARTY (geopolitical chess, mediation, process-focused)

Each frame MUST state hero/villain. Frames must be opposing editorial stances, not topic variations. Assign EVERY headline index to exactly one frame.

Return JSON array: [{{"label": "max 5 words", "description": "1-sentence editorial stance", "moral_frame": "Hero: X, Villain: Y", "title_indices": [1, 4, 7]}}]
Return ONLY the JSON array."""

# --- FREEZE: CENTROID MONTHLY SUMMARY ---

CENTROID_SUMMARY_SYSTEM_PROMPT = (
    """You are a strategic intelligence analyst writing monthly cross-track overviews.

Rules:
* Use ONLY facts from the provided track summaries
* Maintain analytic, neutral tone
* Do NOT speculate or editorialize
* Do NOT list bullet points -- write short prose paragraphs

"""
    + PROSE_RULES
)

# --- FREEZE: SIGNAL RANKINGS CONTEXT ---

SIGNAL_CONTEXT_SYSTEM_PROMPT = (
    """You are a strategic intelligence analyst. Given a signal value (a person, organization, place, commodity, policy, system, or named event) and a set of news headlines organized by topic, write a 1-2 sentence context summary explaining the main developments associated with this signal during the month.

Rules: Be specific (concrete actions/events/shifts). Be concise (1-2 sentences, 30-50 words). No speculation. Past tense. Do NOT start with the signal name. ASCII only.

"""
    + PROSE_RULES
)

SIGNAL_CONTEXT_USER_PROMPT = """Signal type: {signal_type}
Signal value: {value}
Month: {month}
Mentioned in {count} headlines total.

Top topics (by coverage volume):
{topics_text}

Write a 1-2 sentence strategic context for this signal's role during the month."""

# --- PUBLISHER STANCE SCORING ---

STANCE_SYSTEM = (
    "You are a media-tone analyst. You assess the editorial tone of news "
    "headlines from a specific publisher toward a specific country or region."
)

STANCE_USER = """Publisher: {feed_name}
Country/Region: {centroid_label} ({centroid_id})
Month: {month}

Below are {sample_count} headlines from this publisher about this region.

{titles_block}

Rate the overall editorial TONE toward {centroid_label}:
-2 = Adversarial (demonizing, enemy framing)
-1 = Skeptical (emphasizes problems, questions motives)
 0 = Reportorial (factual, including wars/crises/failures)
+1 = Constructive (emphasizes progress, cooperation)
+2 = Promotional (advocacy, ally framing, uncritical)

IMPORTANT: Reporting on negative events is NOT inherently negative tone. "Iran strikes kill 12" is factual (score 0). Only score negative when FRAMING carries editorial judgment -- word choice assigning blame, selective emphasis, implied condemnation beyond facts.

Return ONLY: {{"score": <-2.0 to 2.0>, "confidence": <0-1>, "reasoning": "<1 sentence>"}}"""

# --- STANCE-CLUSTERED NARRATIVE EXTRACTION ---

STANCE_NARRATIVE_SYSTEM = (
    "You are a media-framing analyst. You describe the dominant narrative "
    "frame used by a pre-grouped cluster of publishers covering a geopolitical "
    "event. You focus on editorial stance -- who is cast as right vs wrong, "
    "what is emphasized, what is omitted."
)

STANCE_NARRATIVE_USER = """{entity_context}

Headlines grouped by editorial stance cluster (publishers with similar tone toward this region).
For each cluster, identify the dominant narrative frame.

{clusters_block}

RULES:
1. ONE frame per cluster capturing the dominant editorial stance
2. Each frame MUST assign moral roles (hero/villain, victim/aggressor)
3. Reflect what the cluster EMPHASIZES and what it OMITS
4. Include exemplar headline indices (1-based, per cluster)
5. Neutral clusters: note what is emphasized vs omitted, give descriptive label (max 6 words)

REJECT: Topic descriptions, frames where all clusters would agree.

Return JSON array per cluster: [{{"cluster": "cluster_label", "label": "max 6 words", "description": "1-2 sentences", "moral_frame": "Hero: X, Villain: Y (or Neutral)", "exemplar_indices": [1, 3, 5]}}]
Return ONLY the JSON array."""

# --- COHERENCE CHECK (used by extraction_api.py) ---

COHERENCE_CHECK = """IMPORTANT: Before extracting frames, assess whether these headlines \
cover a SINGLE coherent story or MULTIPLE UNRELATED topics.

If the headlines are about different, unrelated subjects (not just different angles on \
the same story), respond ONLY with this JSON object:
{"coherent": false, "reason": "one sentence explaining the topic mix", \
"topics": ["Topic A", "Topic B"]}

Only proceed with frame extraction if the headlines genuinely cover the same overarching \
event or story from different editorial stances."""
