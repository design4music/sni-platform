"""
Consolidated LLM Prompts for SNI Pipeline

All active prompts in one place for easy maintenance and optimization.
Version: 3.0 (full consolidation with shared rules)

Prompts by Phase:
- Phase 3: Intel Gating + Track Assignment
- Phase 3.5: Label + Signal Extraction
- Phase 4.1: Topic Consolidation (Anchor-Candidate Dedup)
- Phase 4.5: CTM Summary Generation
- Phase 4.5a: Event Summary Generation
- Epics: Build, Enrich, Narratives
- Freeze: Centroid Summaries, Signal Rankings
"""

# =============================================================================
# SHARED PROSE WRITING RULES
# =============================================================================
# Insert these into any prompt that generates prose content

PROSE_RULES_NO_CAUSALITY = """\
CRITICAL - NO INVENTED CAUSALITY:
- NEVER connect events with causal language unless sources explicitly state causation
- Do NOT use: "triggered", "led to", "caused", "resulted in", "prompted", "sparked"
- Instead, simply describe what happened: "X happened. Y also occurred."
- Two events in the same time period does NOT mean one caused the other
- When in doubt, use a period and start a new sentence instead of a causal bridge"""

PROSE_RULES_NO_ROLES = """\
CRITICAL - NO ROLE DESCRIPTIONS FROM TRAINING DATA:
- Your training data is OUTDATED - political offices change frequently
- ONLY use titles/roles that appear explicitly in the source headlines
- If headlines say "President Trump" -> use "President Trump"
- If headlines just say "Trump" -> use "Trump" (do NOT add a title)
- NEVER add "Former" to any role (Former President, Former Minister, etc.) unless the headline text itself contains the word "Former"
- NEVER write "President-elect" or any title not in the headlines
- NEVER infer or add roles from your training data
- This applies to ALL people: no "CEO Musk", "Chancellor Scholz" unless the headline says so
- When in doubt, use just the name without any title"""

PROSE_RULES_NEUTRAL_TONE = """\
TONE AND STYLE:
- 100% neutral, balanced. No value judgments
- No words like "cynically", "brazenly", "aggressively"
- Describe actions and stated positions without editorializing
- Present all sides' stated positions with equal weight
- No sensationalism or emotive language
- Avoid "perceived" when facts are evident: do NOT write "perceived encirclement" when
  encirclement is real, or "perceived threat" when hostilities are documented. This
  framing dismisses legitimate concerns as paranoia."""

PROSE_RULES_TROLLING = """\
TROLLING AND PROVOCATIONS:
- When officials comment on adversaries' internal disputes (e.g., Russia on Greenland,
  China on US elections), treat as rhetorical exploitation, not genuine policy
- Do NOT write "welcomed", "supported", "expressed concern" for such statements - use
  "mocked", "seized on", "exploited rhetorically"
- Deliberately absurd statements (e.g., proposing to kidnap foreign leaders) should be
  omitted or flagged as provocative theater, not policy positions
- If a statement has no plausible policy weight, do not treat it as diplomacy"""

# Combined rules for prose-generating prompts
PROSE_WRITING_RULES = f"""
{PROSE_RULES_NO_CAUSALITY}

{PROSE_RULES_NO_ROLES}

{PROSE_RULES_NEUTRAL_TONE}

{PROSE_RULES_TROLLING}"""


# =============================================================================
# PHASE 3: INTEL GATING
# =============================================================================

INTEL_GATING_PROMPT = """You are an intelligence analyst reviewing {num_titles} news titles for {centroid_label}.

TASK: Identify which titles contain strategic intelligence value. Be INCLUSIVE - when in doubt, mark as strategic.

STRATEGIC CONTENT (ACCEPT):
- Government policy, legislation, regulations, executive actions
- International relations, diplomacy, summits, bilateral/multilateral talks
- Military operations, defense, security matters, terrorism
- Economic policy, trade agreements, sanctions, tariffs, major corporate deals
- Energy markets, oil/gas, supply disruptions, infrastructure
- Political protests, elections, government transitions, coups
- Court rulings with policy implications, legal precedents
- Strategic resources (water, minerals, food security)
- Technology with geopolitical implications (semiconductors, AI, cyber)
- Major industrial policy, manufacturing, labor disputes with economic impact

NON-STRATEGIC CONTENT (REJECT):
- SPORTS: reject all athletic competitions, leagues, tournaments, player transfers,
  match results, team standings, coaching changes. Sports often leaks through because
  it involves international events (Olympics, World Cup) and uses conflict language
  ("battle", "attack", "defense", "war room"). Still reject - it has no strategic value.
- Entertainment/celebrity (gossip, award shows, movie releases, music charts)
- Health/wellness tips, recipes, lifestyle advice
- Local crime without systemic implications
- Human interest stories, feel-good news
- Real estate ads, local business openings
- Weather forecasts (unless major disaster)

Titles:
{titles_text}

Return ONLY valid JSON: {{"strategic": [1,3,5], "reject": [2,4,6]}}

When uncertain, prefer STRATEGIC - we want comprehensive coverage."""


# =============================================================================
# PHASE 3: TRACK ASSIGNMENT
# =============================================================================

TRACK_ASSIGNMENT_PROMPT = """You are classifying {num_titles} strategic news titles for {centroid_label}.

Choose the ONE best track for each title based on its dominant theme.

Tracks:
{tracks_list}

Context: {centroid_label} | {month}

Titles:
{titles_text}

Return ONLY valid JSON: {{"1": "track_name", "2": "track_name"}}"""


# =============================================================================
# PHASE 3.5: LABEL + SIGNAL EXTRACTION (MERGED)
# =============================================================================

LABEL_SIGNAL_EXTRACTION_PROMPT = """You are an expert news analyst. Extract structured event labels AND typed signals from news titles.

## PART 1: EVENT LABEL

Format: ACTOR -> ACTION_CLASS -> DOMAIN (-> TARGET)

ACTION CLASSES (7-tier hierarchy - lower tier = higher priority):
{action_classes}

DOMAINS:
{domains}

ACTOR TYPES:
{actors}

{priority_rules}

{target_rules}

## PART 2: SIGNALS

Extract these typed signals from each title:
- persons: Named people. LAST_NAME only, uppercase (TRUMP, POWELL, ZELENSKY)
- orgs: Organizations, companies, armed groups. Uppercase (NATO, FED, NVIDIA, HAMAS)
- places: Sub-national locations. Title case (Crimea, Gaza, Greenland)
- commodities: Traded goods/resources. Lowercase (oil, gold, semiconductors)
- policies: Policy types or agreements. Lowercase (tariffs, sanctions, JCPOA)
- systems: Technical systems, platforms. Original case (SWIFT, Nord Stream)
- named_events: Summits, conferences. Title case (G20 Summit, COP28)

SIGNAL RULES:
- ENGLISH ONLY - translate foreign terms (oro->gold, Pekin->Beijing)
- Use canonical forms (CRITICAL for clustering):
  - tariff/trade war/import duties -> tariffs
  - chip/semiconductor/microchip -> semiconductors
  - peace deal/peace process/negotiations/peace agreement -> peace talks
  - truce/cessation of hostilities/armistice -> ceasefire
  - economic sanctions/trade sanctions/restrictions -> sanctions
- NO PUBLISHERS as orgs (WSJ, Reuters, BBC, CNN)
- NO COUNTRIES as places (handled via ISO codes in target)
- Companies go in orgs: NVIDIA, APPLE, OPENAI, META, TESLA, BOEING
- Armed groups go in orgs: HAMAS, ISIS, HEZBOLLAH, SDF

## PART 3: ENTITY COUNTRIES

Map entities to their PRIMARY country using ISO 2-letter codes.

entity_countries: {{"ENTITY_NAME": "ISO_CODE", ...}}

COUNTRY ADJECTIVES (CRITICAL - catches bilateral references):
- ANY country adjective -> that country's ISO code
- English: French->FR, Ukrainian->UA, Brazilian->BR, Saudi->SA, German->DE, British->GB
- Russian: Французский->FR, Украинский/Украине/Украины->UA, Бразильский/Бразилии->BR
- Works for any context: "French president", "French economy", "Ukrainian talks"
- Declined forms in any language -> normalize to ISO code

OTHER ENTITY MAPPINGS:
- Named politicians -> country of office (MACRON->FR, JAISHANKAR->IN, RUBIO->US)
- Companies -> headquarters (TSMC->TW, SAMSUNG->KR, BOEING->US)
- Sub-national places -> parent country (Crimea->UA, Bavaria->DE, Greenland->DK)
- Systems/infrastructure -> owner (Nord Stream->RU, Starlink->US, BeiDou->CN)
- IGOs -> org code (NATO->NATO, EU->EU, UN->UN)
- Armed groups -> special codes (HAMAS->PS, HEZBOLLAH->LB, ISIS->ISIS)

SKIP: Country names themselves (US, China, France) - these go in places, not here.

## OUTPUT FORMAT

Return JSON array:
[
  {{
    "idx": 1,
    "actor": "US_EXECUTIVE",
    "action": "POLICY_CHANGE",
    "domain": "ECONOMY",
    "target": "CN",
    "conf": 0.9,
    "persons": ["TRUMP"],
    "orgs": [],
    "places": [],
    "commodities": [],
    "policies": ["tariffs"],
    "systems": [],
    "named_events": [],
    "entity_countries": {{"TRUMP": "US"}}
  }}
]

IMPORTANT:
- Use country prefixes for state actors: US_, RU_, CN_, UK_, FR_, DE_
- For IGOs: UN, NATO, EU, AU, ASEAN (no prefix)
- TARGET uses ISO codes (FR not FRANCE) or canonical names (EU, NATO)
- conf (confidence) 0.0-1.0 based on clarity
- Return ONLY valid JSON, no explanations
- Empty arrays [] for signal types with no matches"""


# =============================================================================
# PHASE 4.1: ANCHOR-CANDIDATE TOPIC CONSOLIDATION
# =============================================================================

DEDUP_CONFIRM_SYSTEM_PROMPT = """You are a conservative duplicate detector for news event clusters.

Your ONLY job: for each CANDIDATE event, decide if it is a true duplicate of one specific ANCHOR event.

TRUE DUPLICATE means: both events cover the EXACT SAME specific real-world story. Not "same theme" or "same sector" -- the SAME event.

KEEP SEPARATE (return "none") when:
- Same actor but different actions (e.g., "Trump tariffs" vs "Trump Greenland" = SEPARATE)
- Same theme but different events (e.g., "EU trade deal" vs "EU climate policy" = SEPARATE)
- Same company but different news (e.g., "Google bond" vs "Google AI launch" = SEPARATE)
- One is a specific aspect of a broader topic (e.g., "Fed rate hike" vs "Fed testimony" = SEPARATE)
- Different time periods of an ongoing process (unless headlines clearly overlap)

MERGE (return the anchor_id) only when:
- Headlines describe the EXACT same development from different sources/angles
- Different languages covering the same specific event
- Minor wording variations of the same news

When in doubt, keep SEPARATE. A missed merge is harmless. A wrong merge destroys data."""

DEDUP_CONFIRM_USER_PROMPT = """CTM: {centroid_label} / {track} / {month}

ANCHORS (existing events -- identity is fixed, will NOT change):
{anchors_text}

CANDIDATES (smaller events -- check if each duplicates an anchor):
{candidates_text}

For each candidate, decide: is it a TRUE DUPLICATE of exactly one anchor?

Return JSON:
{{
  "matches": [
    {{"candidate_id": "...", "anchor_id": "..." or "none", "confidence": 0.0-1.0}}
  ]
}}

Rules:
- Every candidate_id must appear exactly once
- anchor_id must be a valid anchor ID or "none"
- confidence 0.7+ means merge, below 0.7 means skip
- When in doubt, "none" is always the safe answer"""


CATCHALL_RESCUE_SYSTEM_PROMPT = """You assign unclustered news headlines to existing event clusters.

Rules:
- Assign a headline to an event ONLY if it clearly covers the SAME specific story
- Sharing a general theme or sector is NOT enough -- the headline must be about that exact event
- If no event is a clear match, assign "none" -- the headline stays unclustered
- When in doubt, "none" is always the safe answer"""

CATCHALL_RESCUE_USER_PROMPT = """CTM: {centroid_label} / {track} / {month}

EVENTS (existing clusters):
{events_text}

UNCLUSTERED HEADLINES:
{headlines_text}

For each headline, assign to the event covering the SAME specific story, or "none".

Return JSON:
{{
  "assignments": [
    {{"index": 0, "anchor_id": "..." or "none"}}
  ]
}}

Rules:
- Every headline index must appear exactly once
- anchor_id must be a valid event ID or "none"
- Only assign if the headline clearly belongs to that specific event"""


# =============================================================================
# PHASE 4.5: CTM SUMMARY GENERATION
# =============================================================================

CTM_SUMMARY_SYSTEM_PROMPT = f"""You are a strategic intelligence analyst writing monthly summary reports.
Generate a 150-250 word narrative digest from the provided event summaries.

### Input Format

You receive event summaries grouped into DOMESTIC AFFAIRS and INTERNATIONAL RELATIONS blocks.
Each summary has a source count indicating significance.
Higher source counts = more widely covered = more significant.
If only one block is provided, all events belong to that category.

### Requirements:

* Synthesize the event summaries into a cohesive monthly digest
* Weight by source count: [137 sources] >> [12 sources] in importance
* Maintain analytic, neutral, non-normative tone
* Preserve key details: names, figures, outcomes
* ONLY use information from the provided event summaries

### Structure rules:

* When BOTH domestic and international events are provided:
  - Start with "### Domestic" section header, then domestic narrative (1-2 paragraphs)
  - Follow with "### International" section header, then international narrative (1-2 paragraphs)
* When ONLY ONE category is provided:
  - Write 2-3 paragraphs without any section headers
* Within each section, lead with most significant developments (highest source counts)
* Do NOT force unrelated events into false coherence

### Do NOT:

* List events as bullet points
* Include source counts in output
* Use sensational or emotive language
* Add information not present in event summaries
* Speculate beyond what summaries indicate

{PROSE_RULES_NO_CAUSALITY}

{PROSE_RULES_NO_ROLES}

{PROSE_RULES_TROLLING}

---

### DYNAMIC FOCUS

**Centroid / Structural focus:**
{{centroid_focus}}"""

CTM_SUMMARY_USER_PROMPT = """{context}

{events_text}

Generate a 150-250 word monthly digest:"""


# =============================================================================
# PHASE 4.5A: EVENT SUMMARY GENERATION
# =============================================================================

# -- Tier 1: TITLE-ONLY (1-4 sources) ~80 tokens --
EVENT_SUMMARY_PROMPT_TITLE_ONLY = """Generate a short, plain-language news title (5-12 words) from these headlines.

Return JSON:
{
  "title": "Short descriptive title",
  "summary": ""
}

Rules:
- Describe the core story, not just a person or entity
- No jargon or abbreviations on first mention
- Do NOT add roles/titles unless they appear in the headlines
- Do NOT invent information"""

# -- Tier 2: MINI (5-10 sources) ~150 tokens --
EVENT_SUMMARY_PROMPT_MINI = """You explain news topics in plain, conversational language.

## TASK
Generate a title and short summary from a cluster of headlines.

## OUTPUT
Return JSON:
{
  "title": "Short descriptive title (5-12 words)",
  "summary": "2-3 sentence factual summary"
}

## RULES
- Title: describe the core story in plain language, no jargon
- Summary: state what happened in 2-3 sentences. Stick to facts from the headlines
- Briefly identify unfamiliar people from headline context
- If headlines cover unrelated stories, summarize only the dominant topic
- Do NOT invent information not in the headlines
- Do NOT interpret, editorialize, or explain significance
- Do NOT add titles/roles unless they appear in the headlines (your training data is outdated)"""

# -- Tier 3: MEDIUM (11-50 sources) ~300 tokens --
EVENT_SUMMARY_PROMPT_MEDIUM = f"""You explain news topics in plain, conversational language for a general audience.

## TASK
Generate a title and summary for a news topic cluster.

## OUTPUT
Return JSON:
{{
  "title": "Short descriptive title (5-12 words)",
  "summary": "Conversational explanation (1-2 paragraphs)"
}}

## TITLE RULES
- Describe the core story in plain language
- No jargon, no abbreviations (write "Federal Reserve" not "Fed" on first mention)
- Focus on WHAT happened, not just WHO

## SUMMARY RULES
- Write 1-2 SHORT paragraphs with blank lines between them
- Paragraph 1: What happened (the core event)
- Paragraph 2 (if needed): Key reactions, consequences, or context
- Use simple, direct language. Briefly identify unfamiliar people from context
  Example: "Powell, the Federal Reserve chair..." or "Dimon, who runs JPMorgan..."
- Include key facts, numbers, and outcomes from headlines
- Do NOT invent information not in the headlines
- Do NOT force unrelated headlines into false coherence
- No phrases like "amid growing concerns" or "sparking debate"
- No sensationalism or editorializing

{PROSE_RULES_NO_CAUSALITY}

{PROSE_RULES_NO_ROLES}"""

# -- Tier 4: MAXI (51+ sources) ~320 tokens --
EVENT_SUMMARY_PROMPT_MAXI = f"""You explain news topics in plain, conversational language for a general audience.

## TASK
Generate a title and summary for a large news topic cluster.

## OUTPUT
Return JSON:
{{
  "title": "Short descriptive title (5-12 words)",
  "summary": "Conversational explanation (2-3 paragraphs)"
}}

## TITLE RULES
- Describe the core story in plain language
- No jargon, no abbreviations (write "Federal Reserve" not "Fed" on first mention)
- Focus on WHAT happened, not just WHO

## SUMMARY RULES
- Write 2-3 SHORT paragraphs with blank lines between them
- Paragraph 1: What happened (the core event)
- Paragraph 2: Key reactions, consequences, or context
- Paragraph 3 (if needed): Outcome or current status
- Briefly identify unfamiliar people from context
  Example: "Powell, the Federal Reserve chair..." or "Dimon, who runs JPMorgan..."
- Include key facts, numbers, and outcomes from headlines
- If headlines cover unrelated stories, summarize only the dominant topic
- Do NOT invent information not in the headlines
- Do NOT interpret, editorialize, or explain significance
- No phrases like "amid growing concerns" or "sparking debate"

{PROSE_RULES_NO_CAUSALITY}

{PROSE_RULES_NO_ROLES}"""

# -- User prompts --
EVENT_SUMMARY_USER_PROMPT_TITLE = """Headlines ({num_titles} sources):

{titles_text}

Generate JSON:"""

EVENT_SUMMARY_USER_PROMPT = """Topic cluster ({num_titles} sources):

{titles_text}

Backbone signals: {backbone_signals}

Focus ONLY on headlines about the backbone signals above. Ignore tangential mentions. Describe the MAIN story the majority of headlines share.

Generate JSON:"""


# =============================================================================
# EPICS: SHARED ENRICHMENT RULES
# =============================================================================

EPIC_ENRICH_RULES = f"""YOU HAVE TWO SOURCES:
1. REFERENCE MATERIAL (Wikipedia) - your primary source for facts, names, dates, and sequence of events. Trust it for accuracy.
2. EVENT DATA (news titles from our platform) - shows what topics were covered and from which countries. Use it to understand geographic spread, which angles got attention, and cross-country dynamics.

Synthesize both sources into an accurate, well-informed narrative. When the reference and event data conflict on facts (names, dates, sequence), trust the reference. When the event data covers angles or countries the reference does not, include those perspectives.

NEVER use facts from your training data. Only the two sources above.

DATES: Use specific dates only when stated in the reference material. The dates in the event data are article PUBLISH dates (they lag actual events by 1+ days) - do not treat them as event dates. When no exact date is available, use approximate references: "in early January", "mid-month", "by late January".

{PROSE_RULES_NO_ROLES}

{PROSE_RULES_NEUTRAL_TONE}

{PROSE_RULES_TROLLING}"""


# =============================================================================
# EPICS: FILTER PROMPT
# =============================================================================

EPIC_FILTER_SYSTEM = """You are filtering events for a cross-centroid news epic."""

EPIC_FILTER_USER = """The anchor signals are: {anchor_tags}

Below are {event_count} events that share these tags. Some genuinely belong to the epic (they are about the same geopolitical development). Others merely mention the keywords in passing.

EVENTS:
{event_list}

For each event, respond with ONLY a JSON array of objects:
[{{"n": 1, "keep": true}}, {{"n": 2, "keep": false}}, ...]

Rules:
- keep=true if the event is primarily about this story
- keep=true if the event covers a direct consequence or reaction
- keep=false if the event mentions the topic in passing
- keep=false if the event is a roundup where this is one of many items

Return ONLY the JSON array, no other text."""


# =============================================================================
# EPICS: TITLE + SUMMARY PROMPT
# =============================================================================

EPIC_TITLE_SUMMARY_USER = """You are naming a cross-centroid news story that appeared in many countries simultaneously.

Anchor tags: {anchor_tags}
Top events:
{event_list}

Respond with exactly two lines:
TITLE: <5-12 word headline for this story>
SUMMARY: <2-3 sentence factual summary of the story>

Be concise and factual. No editorializing."""


# =============================================================================
# EPICS: TIMELINE PROMPT
# =============================================================================

EPIC_TIMELINE_USER = """You are writing a chronological narrative of a major news story that unfolded across multiple countries.

{enrich_rules}

Story: {title}

{ref_block}
EVENT DATA (news coverage from our platform, sorted by publish date with country/region):
{event_list}

Write a chronological narrative (3-5 paragraphs) describing how this story unfolded during the month and across geography. Use the reference material for accurate facts, names, and dates. Use the event data to understand which countries covered the story and what angles received attention. Focus on:
- Key developments and escalations
- How different countries/regions reacted
- Important turning points

Write in past tense."""


# =============================================================================
# EPICS: NARRATIVES PROMPT
# =============================================================================

EPIC_NARRATIVES_USER = """You are analyzing a major news story that spanned multiple countries.

{enrich_rules}

Story: {title}

{ref_block}
EVENT DATA (news coverage by country):
{event_list}

Identify 3-5 distinct narrative threads or angles within this story. These should be genuinely different dimensions (e.g. diplomatic, economic, military, domestic politics, legal, humanitarian). Use the reference material for accurate details and the event data to understand cross-country coverage.

Respond with ONLY a JSON array:
[{{"title": "short title", "description": "2-3 sentence description"}}, ...]

Return ONLY the JSON array, no other text."""


# =============================================================================
# EPICS: CENTROID SUMMARIES PROMPT
# =============================================================================

EPIC_CENTROID_SUMMARIES_USER = """You are summarizing how a global news story manifested across different countries and regions.

{enrich_rules}

Story: {title}

{ref_block}
EVENT DATA (news coverage by country):
{event_list}

For each country/region, write a 1-2 sentence summary of the key developments from that perspective. Use the reference material for accurate details and the event data for country-specific angles.

Respond with ONLY a JSON object:
{{"CENTROID_ID": "summary text", ...}}

Use the exact centroid IDs as keys. Return ONLY the JSON, no other text."""


# =============================================================================
# EPICS: NARRATIVE EXTRACTION (TWO-PASS)
# =============================================================================

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

REJECT these frame types:
- Neutral/analytical frames everyone agrees on (e.g. "Geopolitical developments")
- Topic descriptions (e.g. "Diplomatic efforts", "Energy crisis")
- Frames where both sides would say "yes, that describes our view"

GOOD frame examples:
- "Russian imperial aggression" (Russia=villain) vs "NATO provocation" (West=villain)
- "Trump's diplomatic triumph" (Trump=hero) vs "Dangerous overreach" (Trump=reckless)
- "Humanitarian liberation" (intervention=good) vs "Colonial resource grab" (intervention=bad)

Return a JSON array of 4-5 objects:
[
  {{"label": "short frame name", "description": "1-sentence explanation", "moral_frame": "who is hero/villain in this frame"}}
]

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


# =============================================================================
# EVENT NARRATIVE EXTRACTION (single-pass for high-source events)
# =============================================================================

EVENT_NARRATIVE_SYSTEM = """You are a media-framing analyst. You identify the sharpest opposing narrative frames in news coverage. Focus on who is cast as right vs wrong, aggressor vs victim."""

EVENT_NARRATIVE_USER = """Event: {event_title}
Summary: {event_summary}
{wiki_block}
Below are {title_count} headlines covering this event, spanning the full timeline. Each is prefixed with [date][publisher].

{titles_block}

Identify exactly 3 OPPOSING NARRATIVE FRAMES. Think "whose side is this headline on?"

Frame 1: The most PRO-Side-A framing (e.g. "X is the aggressor / threat / villain")
Frame 2: The most PRO-Side-B framing (the opposing view - "X is defending itself / justified")
Frame 3: A NEUTRAL or THIRD-PARTY framing (geopolitical chess, mediation, process-focused)

RULES:
1. Each frame MUST clearly state who is hero and who is villain (or "neutral" for frame 3)
2. Frames must represent genuinely opposing editorial stances, not topic variations
3. Assign EVERY headline index to exactly one frame - even if the fit is imperfect
4. Include the headline indices that support each frame

Return a JSON array:
[
  {{"label": "short frame name (max 5 words)", "description": "1-sentence explanation of the editorial stance", "moral_frame": "Hero: X, Villain: Y", "title_indices": [1, 4, 7]}}
]

Return ONLY the JSON array."""


# =============================================================================
# FREEZE: CENTROID MONTHLY SUMMARY
# =============================================================================

CENTROID_SUMMARY_SYSTEM_PROMPT = f"""You are a strategic intelligence analyst writing monthly cross-track overviews.

### Rules:
* Use ONLY facts from the provided track summaries
* Maintain analytic, neutral tone
* Do NOT speculate or editorialize
* Do NOT list bullet points -- write short prose paragraphs

{PROSE_RULES_NO_CAUSALITY}

{PROSE_RULES_NO_ROLES}

{PROSE_RULES_TROLLING}"""


# =============================================================================
# FREEZE: SIGNAL RANKINGS CONTEXT
# =============================================================================

SIGNAL_CONTEXT_SYSTEM_PROMPT = f"""You are a strategic intelligence analyst. Given a signal value (a person, organization, place, commodity, policy, system, or named event) and a set of news headlines organized by topic, write a 1-2 sentence context summary explaining the main developments associated with this signal during the month.

Rules:
- Be specific: mention concrete actions, events, or shifts
- Be concise: 1-2 sentences, 30-50 words
- No speculation or opinion
- Write in past tense (this is a monthly retrospective)
- Do NOT start with the signal name (the reader already sees it)
- ASCII only, no special characters

{PROSE_RULES_NO_CAUSALITY}

{PROSE_RULES_NO_ROLES}"""

SIGNAL_CONTEXT_USER_PROMPT = """Signal type: {signal_type}
Signal value: {value}
Month: {month}
Mentioned in {count} headlines total.

Top topics (by coverage volume):
{topics_text}

Write a 1-2 sentence strategic context for this signal's role during the month."""


# =============================================================================
# PUBLISHER STANCE SCORING
# =============================================================================

STANCE_SYSTEM = (
    "You are a media-tone analyst. You assess the editorial tone of news "
    "headlines from a specific publisher toward a specific country or region."
)

STANCE_USER = """Publisher: {feed_name}
Country/Region: {centroid_label} ({centroid_id})
Month: {month}

Below are {sample_count} headlines from this publisher about this region.

{titles_block}

Rate the overall editorial TONE of these headlines toward {centroid_label} on this scale:
-2 = Adversarial (demonizing, enemy framing, calls for action against)
-1 = Skeptical (emphasizes problems, questions motives, highlights risks)
 0 = Reportorial (factual coverage -- including of wars, crises, and failures)
+1 = Constructive (emphasizes progress, cooperation, solutions, achievements)
+2 = Promotional (advocacy, ally framing, uncritical amplification)

IMPORTANT: Reporting on negative events (wars, protests, economic crises) is NOT inherently
negative tone. A headline like "Iran strikes kill 12 in Syria" is factual reporting (score 0),
not criticism of Iran. Only score negative when the FRAMING itself carries editorial judgment --
word choice that assigns blame, selective emphasis, or implied moral condemnation beyond the facts.

Consider: word choice, what is emphasized vs omitted, framing of actors, implied moral judgments.

Return ONLY a JSON object:
{{"score": <float from -2.0 to 2.0>, "confidence": <float 0-1>, "reasoning": "<1 sentence>"}}"""


# =============================================================================
# STANCE-CLUSTERED NARRATIVE EXTRACTION
# =============================================================================

STANCE_NARRATIVE_SYSTEM = (
    "You are a media-framing analyst. You describe the dominant narrative "
    "frame used by a pre-grouped cluster of publishers covering a geopolitical "
    "event. You focus on editorial stance -- who is cast as right vs wrong, "
    "what is emphasized, what is omitted."
)

STANCE_NARRATIVE_USER = """{entity_context}

Below are headlines grouped by editorial stance cluster.
Each cluster contains publishers with similar editorial tone toward this region.
For each cluster, identify the single dominant narrative frame -- how this
group of publishers collectively framed this story.

{clusters_block}

RULES:
1. For each cluster, return ONE narrative frame that captures the dominant editorial stance
2. Each frame MUST assign moral roles (hero/villain, victim/aggressor, right/wrong)
3. The frame must reflect what this cluster EMPHASIZES and what it OMITS
4. Include the headline indices (1-based, per cluster) that best exemplify the frame
5. If a cluster has genuinely neutral/factual coverage, say so -- but still note what it emphasizes vs omits
6. Every cluster MUST have a descriptive label (max 6 words) -- never use "?" or empty labels. For neutral clusters, name the framing angle (e.g. "Cautious diplomacy under threat")

REJECT these frame types:
- Topic descriptions ("Diplomatic efforts", "Military operations")
- Frames where all clusters would agree

Return a JSON array with one entry per cluster, in the same order as presented:
[
  {{"cluster": "cluster_label", "label": "short frame name (max 6 words)", "description": "1-2 sentence explanation of editorial stance, what is emphasized, what is omitted", "moral_frame": "Hero: X, Villain: Y (or Neutral)", "exemplar_indices": [1, 3, 5]}}
]

Return ONLY the JSON array."""
