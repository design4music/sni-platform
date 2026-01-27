"""
Phase 3.5: Combined Label + Signal Extraction (v2)

Extracts structured event labels AND typed signals in a single LLM call.
Replaces separate extract_labels.py and extract_signals.py.

Labels: ACTOR -> ACTION_CLASS -> DOMAIN (-> TARGET)
Signals: persons, orgs, places, commodities, policies, systems, named_events

Usage:
    python pipeline/phase_3_5/extract_labels.py --max-titles 100
    python pipeline/phase_3_5/extract_labels.py --centroid "AMERICAS-USA" --track "geo_economy"
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx
import psycopg2
from loguru import logger

from core.config import config
from core.ontology import (
    ONTOLOGY_VERSION,
    PRIORITY_RULES,
    get_action_classes_for_prompt,
    get_actors_for_prompt,
    get_domains_for_prompt,
    get_target_rules_for_prompt,
    validate_action_class,
    validate_domain,
)

# =============================================================================
# SYSTEM PROMPT (MERGED LABELS + SIGNALS)
# =============================================================================

SYSTEM_PROMPT = """You are an expert news analyst. Extract structured event labels AND typed signals from news titles.

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
- Use canonical forms: tariff/trade war->tariffs, chip/semiconductor->semiconductors
- NO PUBLISHERS as orgs (WSJ, Reuters, BBC, CNN)
- NO COUNTRIES as places (handled via ISO codes in target)
- Companies go in orgs: NVIDIA, APPLE, OPENAI, META, TESLA, BOEING
- Armed groups go in orgs: HAMAS, ISIS, HEZBOLLAH, SDF

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
    "named_events": []
  }}
]

## EXAMPLES

Title: "Trump threatens tariffs on EU over Greenland"
-> actor: US_EXECUTIVE, action: ECONOMIC_PRESSURE, domain: FOREIGN_POLICY, target: EU
-> persons: ["TRUMP"], orgs: ["EU"], places: ["Greenland"], policies: ["tariffs"]

Title: "Fed raises interest rates by 25 basis points"
-> actor: US_CENTRAL_BANK, action: POLICY_CHANGE, domain: ECONOMY, target: null
-> persons: [], orgs: ["FED"], policies: []

Title: "Nvidia reports record revenue amid AI chip demand"
-> actor: CORPORATION, action: ECONOMIC_DISRUPTION, domain: ECONOMY, target: null
-> orgs: ["NVIDIA"], commodities: ["semiconductors"]

Title: "ISIS claims responsibility for attack in Syria"
-> actor: ARMED_GROUP, action: MILITARY_OPERATION, domain: SECURITY, target: SY
-> orgs: ["ISIS"], places: []

Title: "Gold prices hit record high amid uncertainty"
-> actor: UNKNOWN, action: MARKET_MOVEMENT, domain: ECONOMY, target: null
-> commodities: ["gold"]

Title: "Zelensky meets Biden at G20 Summit"
-> actor: UA_EXECUTIVE, action: DIPLOMATIC_ENGAGEMENT, domain: FOREIGN_POLICY, target: US
-> persons: ["ZELENSKY", "BIDEN"], named_events: ["G20 Summit"]

Title: "Russia cuts gas flow through Nord Stream"
-> actor: RU_EXECUTIVE, action: ECONOMIC_PRESSURE, domain: ECONOMY, target: EU
-> commodities: ["gas"], systems: ["Nord Stream"]

IMPORTANT:
- Use country prefixes for state actors: US_, RU_, CN_, UK_, FR_, DE_
- For IGOs: UN, NATO, EU, AU, ASEAN (no prefix)
- TARGET uses ISO codes (FR not FRANCE) or canonical names (EU, NATO)
- conf (confidence) 0.0-1.0 based on clarity
- Return ONLY valid JSON, no explanations
- Empty arrays [] for signal types with no matches
"""


# =============================================================================
# PROMPT BUILDING
# =============================================================================


def build_system_prompt() -> str:
    """Build the complete system prompt with ontology."""
    return SYSTEM_PROMPT.format(
        action_classes=get_action_classes_for_prompt(),
        domains=get_domains_for_prompt(),
        actors=get_actors_for_prompt(),
        priority_rules=PRIORITY_RULES,
        target_rules=get_target_rules_for_prompt(),
    )


def build_user_prompt(titles_batch: list[dict]) -> str:
    """Build user prompt with numbered list of titles."""
    lines = ["Extract event labels and signals for these titles:", ""]

    for i, title in enumerate(titles_batch, 1):
        text = title.get("title_display", title.get("text", ""))
        lines.append("{}. {}".format(i, text))

    lines.append("")
    lines.append("Return JSON array with labels and signals for each title.")

    return "\n".join(lines)


# =============================================================================
# LLM INTERACTION
# =============================================================================


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call LLM API with retry logic."""
    headers = {
        "Authorization": "Bearer {}".format(config.deepseek_api_key),
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": config.v3_p35_temperature,
        "max_tokens": config.v3_p35_max_tokens,
    }

    for attempt in range(config.llm_retry_attempts):
        try:
            with httpx.Client(timeout=config.v3_p35_timeout_seconds) as client:
                response = client.post(
                    "{}/chat/completions".format(config.deepseek_api_url),
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    raise Exception(
                        "API error: {} - {}".format(
                            response.status_code, response.text[:200]
                        )
                    )

                data = response.json()
                return data["choices"][0]["message"]["content"].strip()

        except Exception as e:
            if attempt == config.llm_retry_attempts - 1:
                logger.error(
                    "LLM call failed after {} attempts: {}".format(
                        config.llm_retry_attempts, e
                    )
                )
                raise

            delay = (config.llm_retry_backoff**attempt) + (0.1 * attempt)
            logger.warning(
                "LLM attempt {} failed: {}. Retrying in {:.1f}s".format(
                    attempt + 1, e, delay
                )
            )
            time.sleep(delay)


def extract_batch(titles_batch: list[dict]) -> list[dict]:
    """Extract labels and signals for a batch of titles via LLM."""
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(titles_batch)

    response = call_llm(system_prompt, user_prompt)
    logger.debug("LLM response length: {} chars".format(len(response)))
    if len(response) < 100:
        logger.warning("Short LLM response: {}".format(response[:500]))
    return parse_llm_response(response, titles_batch)


# =============================================================================
# RESPONSE PARSING
# =============================================================================


def extract_json_from_response(text: str) -> list:
    """Extract JSON array from LLM response."""
    import re

    # Try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try markdown code block
    patterns = [
        r"```json\s*(.*?)\s*```",
        r"```\s*(.*?)\s*```",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue

    # Try to find JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError("No valid JSON found in response")


def parse_llm_response(response: str, titles_batch: list[dict]) -> list[dict]:
    """Parse LLM response and validate."""
    try:
        items = extract_json_from_response(response)
    except Exception as e:
        logger.warning("Failed to parse LLM response: {}".format(e))
        return []

    results = []
    idx_to_title = {i + 1: t for i, t in enumerate(titles_batch)}

    for item in items:
        idx = item.get("idx")
        if idx not in idx_to_title:
            logger.warning("Invalid idx {} in response".format(idx))
            continue

        title = idx_to_title[idx]
        title_id = str(title.get("id"))

        # Extract and validate label fields
        actor = normalize_actor(item.get("actor", "UNKNOWN"))
        action_class = item.get("action", "SECURITY_INCIDENT")
        domain = item.get("domain", "GOVERNANCE")
        target = item.get("target")
        confidence = item.get("conf", 1.0)

        # Validate action_class
        if not validate_action_class(action_class):
            logger.warning(
                "Invalid action_class '{}' for title {}, using SECURITY_INCIDENT".format(
                    action_class, title_id[:8]
                )
            )
            action_class = "SECURITY_INCIDENT"

        # Validate domain
        if not validate_domain(domain):
            logger.warning(
                "Invalid domain '{}' for title {}, using GOVERNANCE".format(
                    domain, title_id[:8]
                )
            )
            domain = "GOVERNANCE"

        # Extract signals (default to empty arrays)
        persons = normalize_signal_list(item.get("persons", []), uppercase=True)
        orgs = normalize_signal_list(item.get("orgs", []), uppercase=True)
        places = normalize_signal_list(item.get("places", []))
        commodities = normalize_signal_list(item.get("commodities", []), lowercase=True)
        policies = normalize_signal_list(item.get("policies", []), lowercase=True)
        systems = normalize_signal_list(item.get("systems", []))
        named_events = normalize_signal_list(item.get("named_events", []))

        results.append(
            {
                "title_id": title_id,
                # Labels
                "actor": actor,
                "action_class": action_class,
                "domain": domain,
                "target": target,
                "confidence": min(max(float(confidence), 0.0), 1.0),
                # Signals
                "persons": persons,
                "orgs": orgs,
                "places": places,
                "commodities": commodities,
                "policies": policies,
                "systems": systems,
                "named_events": named_events,
            }
        )

    return results


def normalize_signal_list(
    values: list, uppercase: bool = False, lowercase: bool = False
) -> list:
    """Normalize a list of signal values."""
    if not values or not isinstance(values, list):
        return []

    result = []
    for v in values:
        if not v or not isinstance(v, str):
            continue
        v = v.strip()
        if uppercase:
            v = v.upper()
        elif lowercase:
            v = v.lower()
        if v and v not in result:
            result.append(v)

    return result


def normalize_actor(actor_raw: str) -> str:
    """Normalize actor string (institution abstraction)."""
    if not actor_raw:
        return "UNKNOWN"

    actor = actor_raw.upper().strip()

    # Common normalizations
    normalizations = {
        "BIDEN": "US_EXECUTIVE",
        "TRUMP": "US_EXECUTIVE",
        "WHITE_HOUSE": "US_EXECUTIVE",
        "PUTIN": "RU_EXECUTIVE",
        "KREMLIN": "RU_EXECUTIVE",
        "XI": "CN_EXECUTIVE",
        "XI_JINPING": "CN_EXECUTIVE",
        "CONGRESS": "US_LEGISLATURE",
        "SENATE": "US_LEGISLATURE",
        "HOUSE": "US_LEGISLATURE",
        "PENTAGON": "US_ARMED_FORCES",
        "FED": "US_CENTRAL_BANK",
        "FEDERAL_RESERVE": "US_CENTRAL_BANK",
        "ECB": "EU_CENTRAL_BANK",
        "EUROPEAN_CENTRAL_BANK": "EU_CENTRAL_BANK",
    }

    return normalizations.get(actor, actor)


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def load_titles_needing_extraction(
    conn,
    max_titles: int = None,
    centroid_filter: str = None,
    track_filter: str = None,
) -> list[dict]:
    """Load titles that need label+signal extraction."""
    cur = conn.cursor()

    # Build filter conditions
    ta_conditions = ["ta.title_id = t.id"]
    params = []

    if centroid_filter:
        ta_conditions.append("ta.ctm_id IN (SELECT id FROM ctm WHERE centroid_id = %s)")
        params.append(centroid_filter)

    if track_filter:
        ta_conditions.append("ta.ctm_id IN (SELECT id FROM ctm WHERE track = %s)")
        params.append(track_filter)

    ta_where = " AND ".join(ta_conditions)

    limit_sql = ""
    if max_titles:
        limit_sql = "LIMIT %s"
        params.append(max_titles)

    # Select titles without labels OR without signals
    query = """
        SELECT t.id, t.title_display
        FROM titles_v3 t
        WHERE EXISTS (SELECT 1 FROM title_assignments ta WHERE {})
          AND (
            NOT EXISTS (SELECT 1 FROM title_labels tl WHERE tl.title_id = t.id)
            OR EXISTS (
                SELECT 1 FROM title_labels tl
                WHERE tl.title_id = t.id
                  AND tl.persons IS NULL
            )
          )
        ORDER BY t.pubdate_utc DESC
        {}
    """.format(
        ta_where, limit_sql
    )

    cur.execute(query, params)
    rows = cur.fetchall()

    return [{"id": str(r[0]), "title_display": r[1]} for r in rows]


def write_to_db(conn, results: list[dict]) -> int:
    """Write labels and signals to database."""
    if not results:
        return 0

    cur = conn.cursor()

    # Upsert with all fields including signals
    insert_sql = """
        INSERT INTO title_labels (
            title_id, actor, action_class, domain, target,
            label_version, confidence,
            persons, orgs, places, commodities, policies, systems, named_events
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (title_id) DO UPDATE SET
            actor = EXCLUDED.actor,
            action_class = EXCLUDED.action_class,
            domain = EXCLUDED.domain,
            target = EXCLUDED.target,
            label_version = EXCLUDED.label_version,
            confidence = EXCLUDED.confidence,
            persons = EXCLUDED.persons,
            orgs = EXCLUDED.orgs,
            places = EXCLUDED.places,
            commodities = EXCLUDED.commodities,
            policies = EXCLUDED.policies,
            systems = EXCLUDED.systems,
            named_events = EXCLUDED.named_events,
            updated_at = NOW()
    """

    inserted = 0
    for r in results:
        try:
            cur.execute(
                insert_sql,
                (
                    r["title_id"],
                    r["actor"],
                    r["action_class"],
                    r["domain"],
                    r["target"],
                    ONTOLOGY_VERSION,
                    r["confidence"],
                    r["persons"],
                    r["orgs"],
                    r["places"],
                    r["commodities"],
                    r["policies"],
                    r["systems"],
                    r["named_events"],
                ),
            )
            inserted += 1
        except Exception as e:
            logger.error(
                "Failed to insert label for {}: {}".format(r["title_id"][:8], e)
            )

    conn.commit()
    return inserted


# =============================================================================
# MAIN
# =============================================================================


def process_titles(
    max_titles: int = 200,
    batch_size: int = 25,
    centroid_filter: str = None,
    track_filter: str = None,
) -> dict:
    """Process titles in batches."""
    conn = get_connection()

    titles = load_titles_needing_extraction(
        conn,
        max_titles=max_titles,
        centroid_filter=centroid_filter,
        track_filter=track_filter,
    )

    if not titles:
        logger.info("No titles need extraction")
        conn.close()
        return {"processed": 0, "written": 0}

    logger.info("Processing {} titles in batches of {}".format(len(titles), batch_size))

    total_written = 0

    for i in range(0, len(titles), batch_size):
        batch = titles[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(titles) + batch_size - 1) // batch_size

        logger.info(
            "Batch {}/{}: {} titles".format(batch_num, total_batches, len(batch))
        )

        try:
            results = extract_batch(batch)
            written = write_to_db(conn, results)
            total_written += written
            logger.info("  Wrote {} labels+signals".format(written))
        except Exception as e:
            logger.error("Batch {} failed: {}".format(batch_num, e))

    conn.close()

    return {"processed": len(titles), "written": total_written}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract labels and signals (v2)")
    parser.add_argument("--max-titles", type=int, default=200, help="Max titles")
    parser.add_argument("--batch-size", type=int, default=25, help="Batch size")
    parser.add_argument("--centroid", type=str, help="Filter by centroid")
    parser.add_argument("--track", type=str, help="Filter by track")

    args = parser.parse_args()

    result = process_titles(
        max_titles=args.max_titles,
        batch_size=args.batch_size,
        centroid_filter=args.centroid,
        track_filter=args.track,
    )

    print("Processed: {}, Written: {}".format(result["processed"], result["written"]))
