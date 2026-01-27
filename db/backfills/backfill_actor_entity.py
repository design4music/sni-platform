"""
Re-extract actor_entity for CORPORATION (and similar) labels using improved prompt.

This script re-labels ALL titles with ENTITY_ACTORS, not just those missing entities.
The improved prompt should produce cleaner results (no "Wall Street", "tech firms", etc.)
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

from core.config import config

# Actor types that need entity extraction
ENTITY_ACTORS = ["CORPORATION", "ARMED_GROUP", "NGO", "MEDIA_OUTLET"]


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def load_titles_for_relabeling(
    conn, max_titles: int = None, force_all: bool = False
) -> list[dict]:
    """Load titles with ENTITY_ACTORS for re-labeling."""
    cur = conn.cursor()

    placeholders = ",".join(["%s"] * len(ENTITY_ACTORS))

    # If force_all, re-label everything; otherwise only missing entities
    if force_all:
        where_clause = "tl.actor IN ({})".format(placeholders)
    else:
        where_clause = "tl.actor IN ({}) AND tl.actor_entity IS NULL".format(
            placeholders
        )

    limit_sql = "LIMIT %s" if max_titles else ""
    params = ENTITY_ACTORS + ([max_titles] if max_titles else [])

    cur.execute(
        """
        SELECT tl.title_id, t.title_display, tl.actor
        FROM title_labels tl
        JOIN titles_v3 t ON t.id = tl.title_id
        WHERE {}
        ORDER BY tl.created_at DESC
        {}
    """.format(
            where_clause, limit_sql
        ),
        params,
    )

    rows = cur.fetchall()
    return [{"id": str(r[0]), "title_display": r[1], "actor": r[2]} for r in rows]


# Improved prompt - matches the guidance in extract_labels.py
SYSTEM_PROMPT = """You extract the specific named entity from news titles about companies/organizations.

Given a title and actor type, identify the PRIMARY named entity.

RULES:
- ONLY extract globally recognized brand names
- Use common stock ticker names: NVIDIA, APPLE, JPMORGAN, BOEING, META, GOOGLE, AMAZON
- Return entity name in UPPERCASE
- Return null if NO specific company is identifiable

VALID entities (real global brands):
  NVIDIA, APPLE, MICROSOFT, GOOGLE, AMAZON, META, TESLA, BOEING, JPMORGAN,
  GOLDMAN SACHS, BLACKROCK, OPENAI, SPACEX, NETFLIX, DISNEY, EXXON, CHEVRON,
  WALMART, COSTCO, TARGET, FORD, GM, TOYOTA, SAMSUNG, TSMC, INTEL, AMD

Return null for:
  - Descriptive phrases: "tech firms", "automakers", "fund managers", "hedge funds"
  - Collectives: "Wall Street", "Silicon Valley", "Big Tech", "banks"
  - People: "Trump", "Musk", "Bezos" (these are not companies)
  - Generic: "startup", "private equity", "German investments"
  - Institutions: "Fed", "central bank" (these use XX_CENTRAL_BANK actor)

OUTPUT FORMAT:
[{"idx": 1, "entity": "NVIDIA"}, {"idx": 2, "entity": null}]

Return ONLY valid JSON, no explanations."""


def build_user_prompt(titles_batch: list[dict]) -> str:
    """Build user prompt for entity extraction."""
    lines = ["Extract the primary named entity from these titles:", ""]

    for i, title in enumerate(titles_batch, 1):
        lines.append("{}. [{}] {}".format(i, title["actor"], title["title_display"]))

    return "\n".join(lines)


def call_llm(user_prompt: str) -> str:
    """Call LLM API."""
    headers = {
        "Authorization": "Bearer {}".format(config.deepseek_api_key),
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 1000,
    }

    with httpx.Client(timeout=30) as client:
        response = client.post(
            "{}/chat/completions".format(config.deepseek_api_url),
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(
                "API error: {} - {}".format(response.status_code, response.text[:200])
            )

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


def parse_entity_response(response: str, titles_batch: list[dict]) -> dict:
    """Parse entity extraction response. Returns {title_id: entity_or_none}."""
    import re

    # Try to extract JSON
    try:
        items = json.loads(response.strip())
    except json.JSONDecodeError:
        # Try markdown code block
        match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
        if match:
            items = json.loads(match.group(1).strip())
        else:
            match = re.search(r"\[.*\]", response, re.DOTALL)
            if match:
                items = json.loads(match.group())
            else:
                return {}

    results = {}
    for item in items:
        idx = item.get("idx")
        entity = item.get("entity")
        if idx and 1 <= idx <= len(titles_batch):
            title_id = titles_batch[idx - 1]["id"]
            # Normalize: uppercase and strip, or None
            if entity and entity.lower() != "null":
                results[title_id] = entity.upper().strip()
            else:
                results[title_id] = None

    return results


def update_entities_in_db(conn, entities: dict) -> int:
    """Update actor_entity in database (can set to NULL)."""
    if not entities:
        return 0

    cur = conn.cursor()
    updated = 0

    for title_id, entity in entities.items():
        cur.execute(
            """
            UPDATE title_labels
            SET actor_entity = %s, updated_at = NOW()
            WHERE title_id = %s
        """,
            (entity, title_id),
        )
        updated += cur.rowcount

    conn.commit()
    return updated


def process_batch(batch_info: tuple) -> dict:
    """Process a batch of titles."""
    batch_num, batch, total_batches = batch_info

    try:
        user_prompt = build_user_prompt(batch)
        response = call_llm(user_prompt)
        entities = parse_entity_response(response, batch)

        # Count non-null entities
        valid_count = sum(1 for e in entities.values() if e is not None)

        return {
            "batch_num": batch_num,
            "success": True,
            "entities": entities,
            "total": len(entities),
            "valid": valid_count,
        }
    except Exception as e:
        return {
            "batch_num": batch_num,
            "success": False,
            "entities": {},
            "total": 0,
            "valid": 0,
            "error": str(e)[:100],
        }


def main():
    parser = argparse.ArgumentParser(
        description="Re-extract actor_entity for CORPORATION labels"
    )
    parser.add_argument("--max-titles", type=int, help="Maximum titles to process")
    parser.add_argument(
        "--dry-run", action="store_true", help="Don't write to database"
    )
    parser.add_argument("--batch-size", type=int, default=20, help="Batch size")
    parser.add_argument("--concurrency", type=int, default=3, help="Parallel workers")
    parser.add_argument(
        "--force-all",
        action="store_true",
        help="Re-label ALL entity actors, not just missing",
    )
    args = parser.parse_args()

    conn = get_connection()

    print("Loading titles for entity extraction...")
    titles = load_titles_for_relabeling(conn, args.max_titles, args.force_all)

    if not titles:
        print("No titles to process.")
        conn.close()
        return

    print("Found {} titles".format(len(titles)))
    if args.force_all:
        print("(FORCE ALL - re-labeling everything)")
    if args.dry_run:
        print("(DRY RUN)")

    # Prepare batches
    total_batches = (len(titles) + args.batch_size - 1) // args.batch_size
    batches = []
    for i in range(total_batches):
        start = i * args.batch_size
        end = min(start + args.batch_size, len(titles))
        batches.append((i + 1, titles[start:end], total_batches))

    print("Processing {} batches...".format(total_batches))

    total_processed = 0
    total_valid = 0
    total_null = 0
    errors = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {executor.submit(process_batch, b): b for b in batches}

        for future in as_completed(futures):
            result = future.result()
            batch_num = result["batch_num"]

            if result["success"]:
                entities = result["entities"]
                valid = result["valid"]
                null_count = result["total"] - valid

                if not args.dry_run:
                    update_entities_in_db(conn, entities)

                total_processed += result["total"]
                total_valid += valid
                total_null += null_count

                print(
                    "Batch {}/{}: {} valid, {} null".format(
                        batch_num, total_batches, valid, null_count
                    )
                )
            else:
                errors += 1
                print(
                    "Batch {}/{}: ERROR - {}".format(
                        batch_num, total_batches, result.get("error")
                    )
                )

    elapsed = time.time() - start_time

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("Titles processed: {}".format(total_processed))
    print("Valid entities: {}".format(total_valid))
    print("Null (no company): {}".format(total_null))
    print("Errors: {}".format(errors))
    print("Time: {:.1f}s".format(elapsed))

    conn.close()


if __name__ == "__main__":
    main()
