"""
Phase 3.1: Combined Label + Signal Extraction (v2)

Extracts structured event labels AND typed signals in a single LLM call.
Replaces separate extract_labels.py and extract_signals.py.

Labels: ACTOR -> ACTION_CLASS -> DOMAIN (-> TARGET)
Signals: persons, orgs, places, commodities, policies, systems, named_events

Usage:
    python pipeline/phase_3_1/extract_labels.py --max-titles 100
    python pipeline/phase_3_1/extract_labels.py --centroid "AMERICAS-USA" --track "geo_economy"
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
from core.prompts import LABEL_SIGNAL_EXTRACTION_PROMPT

# =============================================================================
# PROMPT BUILDING
# =============================================================================


def build_system_prompt() -> str:
    """Build the complete system prompt with ontology."""
    return LABEL_SIGNAL_EXTRACTION_PROMPT.format(
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
        "temperature": config.v3_p31_temperature,
        "max_tokens": config.v3_p31_max_tokens,
    }

    for attempt in range(config.llm_retry_attempts):
        try:
            with httpx.Client(timeout=config.v3_p31_timeout_seconds) as client:
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

        # Extract entity_countries (entity -> ISO code mapping)
        entity_countries = normalize_entity_countries(item.get("entity_countries", {}))

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
                # Entity country associations
                "entity_countries": entity_countries,
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


def normalize_entity_countries(raw: dict) -> dict:
    """Normalize entity_countries dict (entity -> ISO code mapping)."""
    if not raw or not isinstance(raw, dict):
        return {}

    result = {}
    for entity, code in raw.items():
        if not entity or not code:
            continue
        # Normalize entity name (uppercase for consistency)
        entity = str(entity).strip().upper()
        # Normalize ISO code (uppercase, strip)
        code = str(code).strip().upper()
        # Skip empty or invalid
        if len(code) < 2 or len(code) > 10:
            continue
        result[entity] = code

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
    backfill_entity_countries: bool = False,
    title_ids_filter: list = None,
) -> list[dict]:
    """Load titles that need label+signal extraction.

    Phase 3.1 runs before gating (Phase 3.3), so we select titles based on
    processing_status='assigned' and centroid_ids, NOT title_assignments.
    """
    cur = conn.cursor()

    # If specific title_ids provided, just load those
    if title_ids_filter:
        # Convert to list of strings if needed
        ids = [str(tid) for tid in title_ids_filter[:max_titles] if tid]
        if not ids:
            return []

        cur.execute(
            """
            SELECT t.id, t.title_display
            FROM titles_v3 t
            WHERE t.id = ANY(%s::uuid[])
            ORDER BY t.pubdate_utc DESC
            """,
            (ids,),
        )
        rows = cur.fetchall()
        return [{"id": str(r[0]), "title_display": r[1]} for r in rows]

    # Build filter conditions
    conditions = [
        "t.processing_status = 'assigned'",
        "t.centroid_ids IS NOT NULL",
    ]
    params = []

    if centroid_filter:
        conditions.append("%s = ANY(t.centroid_ids)")
        params.append(centroid_filter)

    if track_filter:
        # track_filter only works after Phase 3.3 (for re-extraction)
        conditions.append(
            "EXISTS (SELECT 1 FROM title_assignments ta"
            " WHERE ta.title_id = t.id"
            " AND ta.ctm_id IN (SELECT id FROM ctm WHERE track = %s))"
        )
        params.append(track_filter)

    limit_sql = ""
    if max_titles:
        limit_sql = "LIMIT %s"
        params.append(max_titles)

    where_sql = " AND ".join(conditions)

    if backfill_entity_countries:
        # Select titles with labels but missing entity_countries
        query = """
            SELECT t.id, t.title_display
            FROM titles_v3 t
            WHERE {}
              AND EXISTS (
                SELECT 1 FROM title_labels tl
                WHERE tl.title_id = t.id
                  AND (tl.entity_countries IS NULL OR tl.entity_countries = '{{}}'::jsonb)
              )
            ORDER BY t.pubdate_utc DESC
            {}
        """.format(
            where_sql, limit_sql
        )
    else:
        # Select titles without labels OR without signals
        query = """
            SELECT t.id, t.title_display
            FROM titles_v3 t
            WHERE {}
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
            where_sql, limit_sql
        )

    cur.execute(query, params)
    rows = cur.fetchall()

    return [{"id": str(r[0]), "title_display": r[1]} for r in rows]


def write_to_db(conn, results: list[dict]) -> int:
    """Write labels and signals to database."""
    if not results:
        return 0

    cur = conn.cursor()

    # Upsert with all fields including signals and entity_countries
    insert_sql = """
        INSERT INTO title_labels (
            title_id, actor, action_class, domain, target,
            label_version, confidence,
            persons, orgs, places, commodities, policies, systems, named_events,
            entity_countries
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
            entity_countries = EXCLUDED.entity_countries,
            updated_at = NOW()
    """

    inserted = 0
    for r in results:
        try:
            # Convert entity_countries dict to JSON for JSONB column
            entity_countries_json = json.dumps(r.get("entity_countries", {}))

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
                    entity_countries_json,
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


def process_batch_worker(batch_info: tuple) -> dict:
    """Worker function for concurrent batch processing."""
    batch, batch_num, total_batches = batch_info
    try:
        results = extract_batch(batch)
        return {"batch_num": batch_num, "results": results, "error": None}
    except Exception as e:
        logger.error("Batch {} failed: {}".format(batch_num, e))
        return {"batch_num": batch_num, "results": [], "error": str(e)}


def process_titles(
    max_titles: int = 200,
    batch_size: int = 25,
    centroid_filter: str = None,
    track_filter: str = None,
    concurrency: int = 1,
    backfill_entity_countries: bool = False,
    title_ids_filter: list = None,
) -> dict:
    """Process titles in batches with optional concurrency."""
    conn = get_connection()

    titles = load_titles_needing_extraction(
        conn,
        max_titles=max_titles,
        centroid_filter=centroid_filter,
        track_filter=track_filter,
        backfill_entity_countries=backfill_entity_countries,
        title_ids_filter=title_ids_filter,
    )

    if not titles:
        logger.info("No titles need extraction")
        conn.close()
        return {"processed": 0, "written": 0}

    # Prepare batches
    batches = []
    total_batches = (len(titles) + batch_size - 1) // batch_size
    for i in range(0, len(titles), batch_size):
        batch = titles[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        batches.append((batch, batch_num, total_batches))

    logger.info(
        "Processing {} titles in {} batches (concurrency={})".format(
            len(titles), total_batches, concurrency
        )
    )

    total_written = 0
    failed_batches = 0

    if concurrency == 1:
        # Sequential processing
        for batch_info in batches:
            batch, batch_num, total = batch_info
            logger.info("Batch {}/{}: {} titles".format(batch_num, total, len(batch)))
            result = process_batch_worker(batch_info)
            if result["results"]:
                written = write_to_db(conn, result["results"])
                total_written += written
                logger.info("  Wrote {} labels+signals".format(written))
            if result["error"]:
                failed_batches += 1
    else:
        # Concurrent processing
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {
                executor.submit(process_batch_worker, batch_info): batch_info[1]
                for batch_info in batches
            }

            for future in as_completed(futures):
                batch_num = futures[future]
                result = future.result()
                if result["results"]:
                    written = write_to_db(conn, result["results"])
                    total_written += written
                    logger.info(
                        "Batch {}/{}: wrote {} labels+signals".format(
                            batch_num, total_batches, written
                        )
                    )
                if result["error"]:
                    failed_batches += 1

    conn.close()

    logger.info(
        "Completed: {} written, {} failed batches".format(total_written, failed_batches)
    )
    return {
        "processed": len(titles),
        "written": total_written,
        "failed": failed_batches,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract labels and signals (v2)")
    parser.add_argument("--max-titles", type=int, default=200, help="Max titles")
    parser.add_argument("--batch-size", type=int, default=25, help="Batch size")
    parser.add_argument(
        "--concurrency", type=int, default=1, help="Concurrent batches (1-10)"
    )
    parser.add_argument("--centroid", type=str, help="Filter by centroid")
    parser.add_argument("--track", type=str, help="Filter by track")
    parser.add_argument(
        "--backfill-entity-countries",
        action="store_true",
        help="Re-extract titles missing entity_countries",
    )

    args = parser.parse_args()

    result = process_titles(
        max_titles=args.max_titles,
        batch_size=args.batch_size,
        centroid_filter=args.centroid,
        track_filter=args.track,
        concurrency=args.concurrency,
        backfill_entity_countries=args.backfill_entity_countries,
    )

    print(
        "Processed: {}, Written: {}, Failed: {}".format(
            result["processed"], result["written"], result.get("failed", 0)
        )
    )
