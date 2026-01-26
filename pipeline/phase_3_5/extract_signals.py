"""
Phase 3.5b: Signal Extraction

Extracts typed signals from titles for topic clustering:
- persons: Named persons (Trump, Zelensky, Powell)
- orgs: Organizations (NATO, Federal Reserve, Gazprom)
- places: Sub-national places (Crimea, Gaza, Greenland)
- commodities: Commodities (oil, gold, wheat, LNG)
- policies: Policies/agreements (sanctions, tariffs, JCPOA)
- systems: Systems/platforms (SWIFT, S-400, Nord Stream)
- named_events: Named events (G20 Summit, COP28)

Usage:
    python pipeline/phase_3_5/extract_signals.py --ctm-id <ctm_id>
    python pipeline/phase_3_5/extract_signals.py --centroid AMERICAS-USA --track geo_economy
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

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are an expert news analyst extracting typed signals from headlines.

Extract these signal types:
- persons: Named people (politicians, executives, celebrities). Use LAST_NAME only (Trump, Biden, Zelensky, Powell, Musk)
- orgs: Organizations, companies, institutions. Use common short names (NATO, Fed, Gazprom, NVIDIA, WHO)
- places: Sub-national locations (cities, regions, disputed areas). Examples: Crimea, Gaza, Greenland, Taiwan, Hong Kong
- commodities: Traded goods/resources (oil, gold, wheat, LNG, copper, lithium)
- policies: Policy names, agreements, laws (sanctions, tariffs, JCPOA, USMCA, Green New Deal)
- systems: Technical systems, platforms, infrastructure (SWIFT, S-400, Nord Stream, Starlink)
- named_events: Named events, summits, conferences (G20 Summit, COP28, Davos, Olympics)

RULES:
- Extract ONLY entities clearly mentioned in the title
- Use SHORT canonical names (Trump not Donald Trump, Fed not Federal Reserve)
- persons: Last names only, uppercase (TRUMP, BIDEN, ZELENSKY)
- orgs: Common abbreviations uppercase (NATO, WHO, IMF, NVIDIA, TESLA)
- places: Title case (Crimea, Gaza, Taiwan)
- commodities: lowercase (oil, gold, wheat)
- policies: Title case (JCPOA, USMCA, Sanctions)
- systems: Original case (SWIFT, S-400, Nord Stream)
- named_events: Title case (G20 Summit, COP28)
- Return empty array [] if no entities of that type
- Do NOT extract countries (handled separately via ISO codes)

OUTPUT FORMAT:
Return JSON array matching input indices:
[
  {
    "idx": 1,
    "persons": ["TRUMP", "ZELENSKY"],
    "orgs": ["NATO"],
    "places": ["Crimea"],
    "commodities": [],
    "policies": ["sanctions"],
    "systems": [],
    "named_events": []
  }
]

EXAMPLES:

Title: "Trump threatens tariffs on EU over Greenland"
-> persons: ["TRUMP"], orgs: ["EU"], places: ["Greenland"], policies: ["tariffs"]

Title: "Fed raises rates amid inflation concerns"
-> persons: [], orgs: ["FED"], places: [], commodities: [], policies: []

Title: "Russia cuts gas flow through Nord Stream"
-> orgs: [], places: [], commodities: ["gas"], systems: ["Nord Stream"]

Title: "Gold prices surge as dollar weakens"
-> commodities: ["gold", "dollar"]

Title: "Zelensky meets Biden at G20 Summit"
-> persons: ["ZELENSKY", "BIDEN"], named_events: ["G20 Summit"]

Title: "NVIDIA reports record revenue from AI chips"
-> orgs: ["NVIDIA"], commodities: []

Title: "Iran nuclear deal talks resume in Vienna"
-> places: ["Vienna"], policies: ["JCPOA"]

Return ONLY valid JSON, no explanations."""


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
        "temperature": 0.1,
        "max_tokens": 4000,
    }

    for attempt in range(config.llm_retry_attempts):
        try:
            with httpx.Client(timeout=120) as client:
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


def build_user_prompt(titles_batch: list) -> str:
    """Build user prompt with numbered titles."""
    lines = ["Extract typed signals from these titles:", ""]

    for i, title in enumerate(titles_batch, 1):
        lines.append("{}. {}".format(i, title["title_display"]))

    lines.append("")
    lines.append("Return JSON array with signals for each title.")

    return "\n".join(lines)


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


def extract_signals_batch(titles_batch: list) -> list:
    """Extract signals for a batch of titles via LLM."""
    user_prompt = build_user_prompt(titles_batch)
    response = call_llm(SYSTEM_PROMPT, user_prompt)

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
            continue

        title = idx_to_title[idx]

        # Normalize arrays
        def normalize_array(arr):
            if not arr:
                return []
            return [str(x).strip() for x in arr if x]

        results.append(
            {
                "title_id": str(title["id"]),
                "persons": normalize_array(item.get("persons")),
                "orgs": normalize_array(item.get("orgs")),
                "places": normalize_array(item.get("places")),
                "commodities": normalize_array(item.get("commodities")),
                "policies": normalize_array(item.get("policies")),
                "systems": normalize_array(item.get("systems")),
                "named_events": normalize_array(item.get("named_events")),
            }
        )

    return results


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


def load_titles_for_signals(
    conn, ctm_id: str = None, centroid: str = None, track: str = None, limit: int = None
) -> list:
    """Load titles that need signal extraction."""
    cur = conn.cursor()

    # Build subquery conditions for title_assignments filter
    ta_conditions = []
    params = []

    if ctm_id:
        ta_conditions.append("ta.ctm_id = %s")
        params.append(ctm_id)
    else:
        if centroid:
            ta_conditions.append("c.centroid_id = %s")
            params.append(centroid)
        if track:
            ta_conditions.append("c.track = %s")
            params.append(track)

    ta_where = " AND ".join(ta_conditions) if ta_conditions else "1=1"

    query = """
        SELECT t.id, t.title_display
        FROM titles_v3 t
        JOIN title_labels tl ON t.id = tl.title_id
        WHERE tl.persons IS NULL
          AND t.id IN (
            SELECT DISTINCT ta.title_id
            FROM title_assignments ta
            JOIN ctm c ON ta.ctm_id = c.id
            WHERE {}
          )
        ORDER BY t.pubdate_utc DESC
    """.format(
        ta_where
    )

    if limit:
        query += " LIMIT %s"
        params.append(limit)

    cur.execute(query, params)
    rows = cur.fetchall()

    return [{"id": str(r[0]), "title_display": r[1]} for r in rows]


def write_signals_to_db(conn, signals: list) -> int:
    """Write signals to title_labels table."""
    if not signals:
        return 0

    cur = conn.cursor()
    updated = 0

    for sig in signals:
        try:
            cur.execute(
                """
                UPDATE title_labels SET
                    persons = %s,
                    orgs = %s,
                    places = %s,
                    commodities = %s,
                    policies = %s,
                    systems = %s,
                    named_events = %s,
                    updated_at = NOW()
                WHERE title_id = %s
                """,
                (
                    sig["persons"] or None,
                    sig["orgs"] or None,
                    sig["places"] or None,
                    sig["commodities"] or None,
                    sig["policies"] or None,
                    sig["systems"] or None,
                    sig["named_events"] or None,
                    sig["title_id"],
                ),
            )
            updated += 1
        except Exception as e:
            logger.warning(
                "Failed to update signals for {}: {}".format(sig["title_id"][:8], e)
            )

    conn.commit()
    return updated


# =============================================================================
# MAIN PROCESSING
# =============================================================================


def process_batch_worker(batch_info: tuple) -> dict:
    """Worker for parallel batch processing."""
    batch_num, batch, total_batches = batch_info

    try:
        signals = extract_signals_batch(batch)
        return {
            "batch_num": batch_num,
            "success": True,
            "signals": signals,
            "count": len(signals),
        }
    except Exception as e:
        logger.error("Batch {} failed: {}".format(batch_num, e))
        return {
            "batch_num": batch_num,
            "success": False,
            "signals": [],
            "count": 0,
            "error": str(e)[:100],
        }


def process_signals(
    ctm_id: str = None,
    centroid: str = None,
    track: str = None,
    max_titles: int = None,
    dry_run: bool = False,
    batch_size: int = 20,
    concurrency: int = 3,
):
    """Main entry point for signal extraction."""
    conn = get_connection()

    # Load titles
    print("Loading titles for signal extraction...")
    titles = load_titles_for_signals(
        conn, ctm_id=ctm_id, centroid=centroid, track=track, limit=max_titles
    )

    if not titles:
        print("No titles found needing signal extraction.")
        conn.close()
        return

    print("Found {} titles needing signals".format(len(titles)))
    if dry_run:
        print("(DRY RUN - no database writes)")

    # Prepare batches
    total_batches = (len(titles) + batch_size - 1) // batch_size
    batches = []
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(titles))
        batch = titles[start_idx:end_idx]
        batches.append((batch_num + 1, batch, total_batches))

    print("Processing {} batches with {} workers...".format(total_batches, concurrency))
    print()

    # Process
    total_processed = 0
    errors = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(process_batch_worker, b): b for b in batches}

        for future in as_completed(futures):
            result = future.result()
            batch_num = result["batch_num"]

            if result["success"]:
                signals = result["signals"]
                if signals and not dry_run:
                    updated = write_signals_to_db(conn, signals)
                    total_processed += updated
                    print(
                        "Batch {}/{}: {} signals".format(
                            batch_num, total_batches, updated
                        )
                    )
                elif signals:
                    total_processed += len(signals)
                    print(
                        "Batch {}/{}: would extract {}".format(
                            batch_num, total_batches, len(signals)
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
    print("Signals extracted: {}".format(total_processed))
    print("Errors: {}".format(errors))
    print("Time: {:.1f}s ({:.1f} titles/sec)".format(elapsed, rate))

    conn.close()


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract typed signals from titles")
    parser.add_argument("--ctm-id", help="Process specific CTM")
    parser.add_argument("--centroid", help="Filter by centroid ID")
    parser.add_argument("--track", help="Filter by track")
    parser.add_argument("--max-titles", type=int, help="Limit titles to process")
    parser.add_argument("--batch-size", type=int, default=20, help="Batch size")
    parser.add_argument("--concurrency", type=int, default=3, help="Parallel workers")
    parser.add_argument(
        "--dry-run", action="store_true", help="Don't write to database"
    )

    args = parser.parse_args()

    process_signals(
        ctm_id=args.ctm_id,
        centroid=args.centroid,
        track=args.track,
        max_titles=args.max_titles,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        concurrency=args.concurrency,
    )
