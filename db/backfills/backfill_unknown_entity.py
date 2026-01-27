"""
Re-extract actor_entity for UNKNOWN labels to identify subject topics.

This script re-labels UNKNOWN titles to extract:
- STOCK_MARKET for stock/market news
- GOLD, SILVER, OIL, DOLLAR for commodity/currency news
- Reclassifies company-focused titles to CORPORATION with entity
"""

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx
import psycopg2

from core.config import config


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def load_unknown_titles(
    conn, max_titles: int = None, action_filter: str = None
) -> list[dict]:
    """Load titles with UNKNOWN actor for re-labeling."""
    cur = conn.cursor()

    where_clause = "tl.actor = 'UNKNOWN'"
    params = []

    if action_filter:
        where_clause += " AND tl.action_class = %s"
        params.append(action_filter)

    limit_sql = ""
    if max_titles:
        limit_sql = "LIMIT %s"
        params.append(max_titles)

    cur.execute(
        """
        SELECT tl.title_id, t.title_display, tl.action_class
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
    return [
        {"id": str(r[0]), "title_display": r[1], "action_class": r[2]} for r in rows
    ]


SYSTEM_PROMPT = """You analyze news titles to identify the primary subject when the actor is unclear.

Given titles currently labeled as UNKNOWN actor, determine:
1. If about a SPECIFIC COMPANY -> change actor to CORPORATION with entity name
2. If about STOCK MARKET/indices -> keep UNKNOWN, entity = STOCK_MARKET
3. If about a COMMODITY price -> keep UNKNOWN, entity = commodity name
4. If no clear subject -> keep UNKNOWN, entity = null

RULES:
- STOCK_MARKET: stock exchange, NYSE, Nasdaq, Dow Jones, S&P 500, market rally, stocks, Wall Street trading, bourse
- GOLD: gold prices, gold rally, bullion, precious metals (gold focus)
- SILVER: silver prices, silver rally
- OIL: oil prices, crude, petroleum, Brent, WTI
- DOLLAR: US dollar, dollar index, greenback, dollar strength/weakness
- BITCOIN: bitcoin, crypto prices, cryptocurrency markets

For CORPORATION reclassification:
- Only if a SPECIFIC named company is the subject
- Use stock ticker names: NVIDIA, APPLE, JPMORGAN, MORGAN STANLEY, GOLDMAN SACHS, etc.
- NOT for generic "tech firms", "banks", "Wall Street" (these are STOCK_MARKET or null)

OUTPUT FORMAT:
[{"idx": 1, "actor": "UNKNOWN", "entity": "STOCK_MARKET"}, {"idx": 2, "actor": "CORPORATION", "entity": "JPMORGAN"}, {"idx": 3, "actor": "UNKNOWN", "entity": null}]

Return ONLY valid JSON, no explanations."""


def build_user_prompt(titles_batch: list[dict]) -> str:
    """Build user prompt for entity extraction."""
    lines = ["Identify the primary subject for these UNKNOWN-actor titles:", ""]

    for i, title in enumerate(titles_batch, 1):
        lines.append("{}. {}".format(i, title["title_display"]))

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
        "max_tokens": 1500,
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


def parse_response(response: str, titles_batch: list[dict]) -> dict:
    """Parse entity extraction response. Returns {title_id: (actor, entity)}."""
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
        actor = item.get("actor", "UNKNOWN")
        entity = item.get("entity")
        if idx and 1 <= idx <= len(titles_batch):
            title_id = titles_batch[idx - 1]["id"]
            # Normalize
            if actor:
                actor = actor.upper().strip()
            if entity and str(entity).lower() != "null":
                entity = entity.upper().strip()
            else:
                entity = None
            results[title_id] = (actor, entity)

    return results


def update_labels_in_db(conn, updates: dict) -> tuple[int, int]:
    """Update actor and actor_entity in database. Returns (updated, reclassified)."""
    if not updates:
        return 0, 0

    cur = conn.cursor()
    updated = 0
    reclassified = 0

    for title_id, (actor, entity) in updates.items():
        cur.execute(
            """
            UPDATE title_labels
            SET actor = %s, actor_entity = %s, updated_at = NOW()
            WHERE title_id = %s
        """,
            (actor, entity, title_id),
        )
        updated += cur.rowcount
        if actor == "CORPORATION":
            reclassified += 1

    conn.commit()
    return updated, reclassified


def process_batch(batch_info: tuple) -> dict:
    """Process a batch of titles."""
    batch_num, batch, total_batches = batch_info

    try:
        user_prompt = build_user_prompt(batch)
        response = call_llm(user_prompt)
        updates = parse_response(response, batch)

        # Count stats
        entity_count = sum(1 for (a, e) in updates.values() if e is not None)
        corp_count = sum(1 for (a, e) in updates.values() if a == "CORPORATION")

        return {
            "batch_num": batch_num,
            "success": True,
            "updates": updates,
            "total": len(updates),
            "with_entity": entity_count,
            "reclassified": corp_count,
        }
    except Exception as e:
        return {
            "batch_num": batch_num,
            "success": False,
            "updates": {},
            "total": 0,
            "with_entity": 0,
            "reclassified": 0,
            "error": str(e)[:100],
        }


def main():
    parser = argparse.ArgumentParser(
        description="Re-extract entity for UNKNOWN actor titles"
    )
    parser.add_argument("--max-titles", type=int, help="Maximum titles to process")
    parser.add_argument(
        "--action", type=str, help="Filter by action_class (e.g., ECONOMIC_DISRUPTION)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Don't write to database"
    )
    parser.add_argument("--batch-size", type=int, default=25, help="Batch size")
    parser.add_argument("--concurrency", type=int, default=3, help="Parallel workers")
    args = parser.parse_args()

    conn = get_connection()

    print("Loading UNKNOWN titles for entity extraction...")
    titles = load_unknown_titles(conn, args.max_titles, args.action)

    if not titles:
        print("No titles to process.")
        conn.close()
        return

    print("Found {} UNKNOWN titles".format(len(titles)))
    if args.action:
        print("Action filter: {}".format(args.action))
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
    total_with_entity = 0
    total_reclassified = 0
    errors = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {executor.submit(process_batch, b): b for b in batches}

        for future in as_completed(futures):
            result = future.result()
            batch_num = result["batch_num"]

            if result["success"]:
                updates = result["updates"]

                if not args.dry_run:
                    update_labels_in_db(conn, updates)

                total_processed += result["total"]
                total_with_entity += result["with_entity"]
                total_reclassified += result["reclassified"]

                print(
                    "Batch {}/{}: {} processed, {} with entity, {} -> CORPORATION".format(
                        batch_num,
                        total_batches,
                        result["total"],
                        result["with_entity"],
                        result["reclassified"],
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
    print("With entity (STOCK_MARKET, GOLD, etc.): {}".format(total_with_entity))
    print("Reclassified to CORPORATION: {}".format(total_reclassified))
    print(
        "Still UNKNOWN with null entity: {}".format(total_processed - total_with_entity)
    )
    print("Errors: {}".format(errors))
    print("Time: {:.1f}s".format(elapsed))

    conn.close()


if __name__ == "__main__":
    main()
