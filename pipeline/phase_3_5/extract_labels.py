"""
Phase 3.5: Event Label Extraction

Extracts structured event labels from titles using ELO (Event Label Ontology) v2.0.
Labels follow: PRIMARY_ACTOR -> ACTION_CLASS -> DOMAIN (-> OPTIONAL_TARGET)

Usage:
    python pipeline/phase_3_5/extract_labels.py --max-titles 100
    python pipeline/phase_3_5/extract_labels.py --centroid "AMERICAS-USA" --track "geo_economy"
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx
import psycopg2
from loguru import logger

from core.config import config
from core.ontology import (ONTOLOGY_VERSION, PRIORITY_RULES,
                           get_action_classes_for_prompt,
                           get_actors_for_prompt, get_domains_for_prompt,
                           get_target_rules_for_prompt, validate_action_class,
                           validate_domain)

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are an expert news analyst. Your task is to extract structured event labels from news titles.

LABEL FORMAT: ACTOR -> ACTION_CLASS -> DOMAIN (-> TARGET)
- ACTOR: The primary institutional actor (with country prefix for state actors)
- ACTION_CLASS: The type of action from the ontology (see below)
- DOMAIN: The thematic domain
- TARGET: Optional target actor/entity - MUST use normalized format (see TARGET rules below)
- ACTOR_ENTITY: For generic actors (CORPORATION, ARMED_GROUP, NGO, MEDIA_OUTLET), the specific named entity

ONTOLOGY VERSION: ELO_v2.0

ACTION CLASSES (7-tier hierarchy - lower tier = higher priority):
{action_classes}

DOMAINS:
{domains}

CONTROLLED ACTOR TYPES:
{actors}

{priority_rules}

{target_rules}

EXAMPLES:

Title: "Biden signs $95 billion foreign aid package for Ukraine, Israel"
Label: US_EXECUTIVE -> RESOURCE_ALLOCATION -> FOREIGN_POLICY -> IL,UA

Title: "Fed raises interest rates by 25 basis points"
Label: US_CENTRAL_BANK -> POLICY_CHANGE -> ECONOMY

Title: "Russian forces capture key town in eastern Ukraine"
Label: RU_ARMED_FORCES -> MILITARY_OPERATION -> SECURITY -> UA

Title: "EU imposes new sanctions on Russian oil exports"
Label: EU -> SANCTION_ENFORCEMENT -> ECONOMY -> RU

Title: "Trump threatens tariffs on European countries over Greenland"
Label: US_EXECUTIVE -> ECONOMIC_PRESSURE -> FOREIGN_POLICY -> EU

Title: "Trump threatens tariffs on France over wine"
Label: US_EXECUTIVE -> ECONOMIC_PRESSURE -> FOREIGN_POLICY -> FR

Title: "Trump drops tariff threat on EU after Greenland deal"
Label: US_EXECUTIVE -> ECONOMIC_PRESSURE -> FOREIGN_POLICY -> EU

Title: "Iran sanctions tightened, affecting trading partners"
Label: US_EXECUTIVE -> SANCTION_ENFORCEMENT -> FOREIGN_POLICY -> IR

Title: "Thousands protest against pension reform in Paris"
Label: FR_POPULATION -> COLLECTIVE_PROTEST -> SOCIETY

Title: "Supreme Court strikes down affirmative action in college admissions"
Label: US_JUDICIARY -> LEGAL_RULING -> GOVERNANCE

Title: "Trump pressures Fed to lower interest rates"
Label: US_EXECUTIVE -> POLITICAL_PRESSURE -> ECONOMY -> US_CENTRAL_BANK

Title: "Nvidia reports record revenue amid AI chip demand"
Label: CORPORATION -> ECONOMIC_DISRUPTION -> ECONOMY (actor_entity: NVIDIA)

Title: "SpaceX launches new batch of Starlink satellites"
Label: CORPORATION -> INFRASTRUCTURE_DEVELOPMENT -> TECHNOLOGY (actor_entity: SPACEX)

Title: "ISIS claims responsibility for attack in Syria"
Label: ARMED_GROUP -> MILITARY_OPERATION -> SECURITY (actor_entity: ISIS)

OUTPUT FORMAT:
Return a JSON array with objects for each title:
[
  {{
    "idx": 1,
    "actor": "ACTOR_WITH_PREFIX",
    "action": "ACTION_CLASS",
    "domain": "DOMAIN",
    "target": "TARGET_OR_NULL",
    "entity": "SPECIFIC_ENTITY_OR_NULL",
    "conf": 0.9
  }}
]

IMPORTANT:
- Use country prefixes for state actors: US_, RU_, CN_, UK_, FR_, DE_, etc.
- For IGOs use: UN, NATO, EU, AU, ASEAN (no prefix)
- For unknown/unclear actors use: UNKNOWN
- TARGET MUST be normalized: use ISO codes (FR not FRANCE), canonical names (EU not EU_COUNTRIES)
- conf (confidence) should be 0.0-1.0 based on how clear the title is
- If multiple actions apply, choose the highest-tier (lowest number) action
- Return ONLY valid JSON, no explanations

ENTITY EXTRACTION RULES (CRITICAL):
- ONLY for generic actors: CORPORATION, ARMED_GROUP, NGO, MEDIA_OUTLET
- ONLY extract globally recognized brand names you know from training data
- Use the company's common stock ticker name: NVIDIA, APPLE, JPMORGAN, BOEING, META, GOOGLE, AMAZON
- Use null if: no specific company, multiple companies, or generic industry reference

VALID entities (real global brands):
  NVIDIA, APPLE, MICROSOFT, GOOGLE, AMAZON, META, TESLA, BOEING, JPMORGAN,
  GOLDMAN SACHS, BLACKROCK, OPENAI, SPACEX, NETFLIX, DISNEY, EXXON, CHEVRON

INVALID - use null instead:
  - Descriptive phrases: "tech firms", "automakers", "fund managers", "hedge funds"
  - Collectives: "Wall Street", "Silicon Valley", "Big Tech", "banks"
  - People as corporations: "Trump", "Musk", "Bezos" (use EXECUTIVE or CORPORATION with real company)
  - Unknown/generic: "startup", "private equity", "German investments"
  - Institutions: "Fed", "central bank" (use XX_CENTRAL_BANK actor instead)
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
    lines = ["Extract structured event labels for these titles:", ""]

    for i, title in enumerate(titles_batch, 1):
        text = title.get("title_display", title.get("text", ""))
        lines.append("{}. {}".format(i, text))

    lines.append("")
    lines.append(
        "Return JSON array with labels for each title (idx matches the number above)."
    )

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


def extract_labels_batch(titles_batch: list[dict]) -> list[dict]:
    """Extract labels for a batch of titles via LLM."""
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
    """Parse LLM response and validate against ontology."""
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

        # Extract and validate fields
        actor = normalize_actor(item.get("actor", "UNKNOWN"))
        action_class = item.get("action", "SECURITY_INCIDENT")
        domain = item.get("domain", "GOVERNANCE")
        target = item.get("target")
        actor_entity = item.get("entity")
        confidence = item.get("conf", 1.0)

        # Normalize actor_entity
        if actor_entity:
            actor_entity = actor_entity.upper().strip()

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

        results.append(
            {
                "title_id": title_id,
                "actor": actor,
                "action_class": action_class,
                "domain": domain,
                "target": target,
                "actor_entity": actor_entity,
                "confidence": min(max(float(confidence), 0.0), 1.0),
            }
        )

    return results


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


def load_unlabeled_titles(
    conn,
    max_titles: int = None,
    centroid_filter: str = None,
    track_filter: str = None,
) -> list[dict]:
    """Load titles that don't have labels yet."""
    cur = conn.cursor()

    # Build filter conditions for title_assignments subquery
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

    query = """
        SELECT t.id, t.title_display
        FROM titles_v3 t
        WHERE EXISTS (SELECT 1 FROM title_assignments ta WHERE {})
          AND NOT EXISTS (SELECT 1 FROM title_labels tl WHERE tl.title_id = t.id)
        ORDER BY t.pubdate_utc DESC
        {}
    """.format(
        ta_where, limit_sql
    )

    cur.execute(query, params)
    rows = cur.fetchall()

    return [{"id": str(r[0]), "title_display": r[1]} for r in rows]


def write_labels_to_db(conn, labels: list[dict]) -> int:
    """Write labels to database with upsert."""
    if not labels:
        return 0

    cur = conn.cursor()

    insert_sql = """
        INSERT INTO title_labels (
            title_id, actor, action_class, domain, target,
            actor_entity, label_version, confidence
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (title_id) DO UPDATE SET
            actor = EXCLUDED.actor,
            action_class = EXCLUDED.action_class,
            domain = EXCLUDED.domain,
            target = EXCLUDED.target,
            actor_entity = EXCLUDED.actor_entity,
            label_version = EXCLUDED.label_version,
            confidence = EXCLUDED.confidence,
            updated_at = NOW()
    """

    inserted = 0
    for label in labels:
        try:
            cur.execute(
                insert_sql,
                (
                    label["title_id"],
                    label["actor"],
                    label["action_class"],
                    label["domain"],
                    label["target"],
                    label.get("actor_entity"),
                    ONTOLOGY_VERSION,
                    label["confidence"],
                ),
            )
            inserted += 1
        except Exception as e:
            logger.warning(
                "Failed to insert label for {}: {}".format(label["title_id"][:8], e)
            )

    conn.commit()
    return inserted


# =============================================================================
# MAIN PROCESSING
# =============================================================================


def process_batch_worker(batch_info: tuple) -> dict:
    """Worker function for parallel batch processing."""
    batch_num, batch, total_batches = batch_info

    try:
        labels = extract_labels_batch(batch)
        return {
            "batch_num": batch_num,
            "success": True,
            "labels": labels,
            "count": len(labels) if labels else 0,
        }
    except Exception as e:
        logger.error("Batch {} failed: {}".format(batch_num, e))
        return {
            "batch_num": batch_num,
            "success": False,
            "labels": [],
            "count": 0,
            "error": str(e)[:100],
        }


def process_titles(
    max_titles: int = None,
    centroid_filter: str = None,
    track_filter: str = None,
    dry_run: bool = False,
):
    """Main entry point for label extraction with parallel processing."""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    # Get effective max_titles
    effective_max = max_titles or config.v3_p35_max_titles

    # Load titles
    logger.info("Loading unlabeled titles...")
    titles = load_unlabeled_titles(
        conn,
        max_titles=effective_max,
        centroid_filter=centroid_filter,
        track_filter=track_filter,
    )

    if not titles:
        print("No unlabeled titles found matching filters.")
        conn.close()
        return

    print("Found {} unlabeled titles".format(len(titles)))
    if dry_run:
        print("(DRY RUN - no database writes)")

    # Prepare batches
    batch_size = config.v3_p35_batch_size
    concurrency = config.v3_p35_concurrency
    total_batches = (len(titles) + batch_size - 1) // batch_size

    batches = []
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(titles))
        batch = titles[start_idx:end_idx]
        batches.append((batch_num + 1, batch, total_batches))

    print(
        "Processing {} batches with {} parallel workers...".format(
            total_batches, concurrency
        )
    )
    print()

    # Process in parallel
    total_labeled = 0
    errors = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(process_batch_worker, b): b for b in batches}

        for future in as_completed(futures):
            result = future.result()
            batch_num = result["batch_num"]

            if result["success"]:
                labels = result["labels"]
                if labels and not dry_run:
                    inserted = write_labels_to_db(conn, labels)
                    total_labeled += inserted
                    print(
                        "Batch {}/{}: {} labels".format(
                            batch_num, total_batches, inserted
                        )
                    )
                elif labels:
                    total_labeled += len(labels)
                    print(
                        "Batch {}/{}: would label {}".format(
                            batch_num, total_batches, len(labels)
                        )
                    )
            else:
                errors += 1
                print(
                    "Batch {}/{}: ERROR - {}".format(
                        batch_num, total_batches, result.get("error", "unknown")
                    )
                )

    elapsed = time.time() - start_time
    rate = len(titles) / elapsed if elapsed > 0 else 0

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("Titles processed: {}".format(len(titles)))
    print("Labels created: {}".format(total_labeled))
    print("Errors: {}".format(errors))
    print("Time: {:.1f}s ({:.1f} titles/sec)".format(elapsed, rate))
    if centroid_filter:
        print("Centroid filter: {}".format(centroid_filter))
    if track_filter:
        print("Track filter: {}".format(track_filter))

    conn.close()


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 3.5: Extract structured event labels from titles"
    )
    parser.add_argument(
        "--max-titles",
        type=int,
        help="Maximum titles to process",
    )
    parser.add_argument(
        "--centroid",
        type=str,
        help="Filter by centroid ID (e.g., AMERICAS-USA)",
    )
    parser.add_argument(
        "--track",
        type=str,
        help="Filter by track (e.g., geo_economy)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write to database, just show what would happen",
    )

    args = parser.parse_args()

    process_titles(
        max_titles=args.max_titles,
        centroid_filter=args.centroid,
        track_filter=args.track,
        dry_run=args.dry_run,
    )
