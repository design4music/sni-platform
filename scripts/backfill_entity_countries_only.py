"""
Backfill entity_countries for titles in February CTMs.

Sends only the title text to LLM with a minimal entity_countries prompt.
Updates ONLY title_labels.entity_countries, preserving all other fields.

Usage:
    python scripts/backfill_entity_countries_only.py --month 2026-02-01
    python scripts/backfill_entity_countries_only.py --month 2026-02-01 --dry-run
    python scripts/backfill_entity_countries_only.py --month 2026-02-01 --batch-size 50 --concurrency 3
"""

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import psycopg2

from core.config import config

# Minimal prompt - only entity_countries extraction
SYSTEM_PROMPT = """\
You extract entity-country mappings from news headlines.

For each headline, return a JSON object mapping entity names to ISO 2-letter country codes.

Your goal: identify any signal that reliably attributes a headline to specific countries.

WHAT TO EXTRACT:
1. COUNTRY ADJECTIVES in any language, any grammatical form, any script.
   Examples: "French president"->FR, "ukrainischen Truppen"->UA, "brasileira"->BR.
   This includes declined, conjugated, or transliterated forms. Use your knowledge of all languages.
2. NAMED POLITICIANS -> country of office (e.g. MACRON->FR, MODI->IN, TRUMP->US, MERZ->DE)
3. COMPANIES -> headquarters country (e.g. TSMC->TW, SAMSUNG->KR, BOEING->US)
4. SUB-NATIONAL PLACES -> parent country (e.g. Gaza->PS, Crimea->UA, Greenland->DK, Bavaria->DE)
5. MILITARY SYSTEMS -> owner country (e.g. S-400->RU, F-35->US, Starlink->US)
6. IGOs -> org code (NATO->NATO, EU->EU, UN->UN, BRICS->BRICS)
7. ARMED GROUPS -> territory code (HAMAS->PS, HEZBOLLAH->LB, HOUTHIS->YE, WAGNER->RU)

SPECIAL RULES:
- Europe/European in any language or script -> always use code "EU"
- South Africa is a country -> ZA (not a continent reference)

SKIP (do NOT include):
- Country names themselves (US, China, France, etc.) - only include entities that HINT at a country
- Continent names (Africa, Asia, Americas) in any language - these are not countries

Return empty object {} if no entities found.

OUTPUT FORMAT:
Return a JSON array. Each element corresponds to the headline with that index number.
[
  {"idx": 1, "entity_countries": {"TRUMP": "US", "MACRON": "FR"}},
  {"idx": 2, "entity_countries": {}},
  ...
]
"""


def get_titles(conn, month: str) -> list[dict]:
    """Get titles in CTMs for the given month that have labels."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT t.id, t.title_display
        FROM titles_v3 t
        JOIN title_assignments ta ON ta.title_id = t.id
        JOIN ctm c ON ta.ctm_id = c.id
        JOIN title_labels tl ON tl.title_id = t.id
        WHERE c.month = %s
        ORDER BY t.id
    """,
        (month,),
    )
    rows = cur.fetchall()
    cur.close()
    return [{"id": r[0], "title_display": r[1]} for r in rows]


def call_llm(titles_batch: list[dict]) -> str:
    """Call LLM with entity_countries-only prompt."""
    lines = ["Extract entity-country mappings for these headlines:", ""]
    for i, t in enumerate(titles_batch, 1):
        lines.append("{}. {}".format(i, t["title_display"]))
    lines.append("")
    lines.append("Return JSON array with entity_countries for each headline.")
    user_prompt = "\n".join(lines)

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
        "max_tokens": 2000,
    }

    for attempt in range(3):
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(
                    "{}/chat/completions".format(config.deepseek_api_url),
                    headers=headers,
                    json=payload,
                )
                if resp.status_code != 200:
                    raise Exception(
                        "API error: {} - {}".format(resp.status_code, resp.text[:200])
                    )
                return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2**attempt)
            print("  Retry {}: {}".format(attempt + 1, e))


def parse_response(text: str, titles_batch: list[dict]) -> list[dict]:
    """Parse LLM response into list of {title_id, entity_countries}."""
    # Extract JSON
    data = None
    for pattern in [r"```json\s*(.*?)\s*```", r"```\s*(.*?)\s*```"]:
        m = re.search(pattern, text, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1).strip())
                break
            except json.JSONDecodeError:
                continue
    if data is None:
        try:
            data = json.loads(text.strip())
        except json.JSONDecodeError:
            m = re.search(r"\[.*\]", text, re.DOTALL)
            if m:
                data = json.loads(m.group(0))
            else:
                print("  WARNING: Could not parse response, first 300 chars:")
                print("  " + text[:300])
                return []

    if not isinstance(data, list):
        data = [data]

    # Country names to filter out (entity == country name mapped to own code)
    COUNTRY_NAMES = {
        "US",
        "USA",
        "UNITED STATES",
        "CHINA",
        "FRANCE",
        "RUSSIA",
        "GERMANY",
        "INDIA",
        "JAPAN",
        "BRAZIL",
        "UK",
        "BRITAIN",
        "IRAN",
        "IRAQ",
        "ISRAEL",
        "TURKEY",
        "CANADA",
        "AUSTRALIA",
        "MEXICO",
        "CUBA",
        "UKRAINE",
        "POLAND",
        "ITALY",
        "SPAIN",
        "EGYPT",
        "PAKISTAN",
        "NIGERIA",
        "SOUTH KOREA",
        "NORTH KOREA",
        "TAIWAN",
        "SAUDI ARABIA",
        "ARGENTINA",
        "COLOMBIA",
        "VENEZUELA",
        "CHILE",
        "PERU",
        "SOUTH AFRICA",
        "KENYA",
        "ETHIOPIA",
        "SYRIA",
        "LEBANON",
        "JORDAN",
        "QATAR",
        "YEMEN",
        "AFGHANISTAN",
        "THAILAND",
        "VIETNAM",
        "PHILIPPINES",
        "INDONESIA",
        "MALAYSIA",
        "SINGAPORE",
        "MONGOLIA",
        "GEORGIA",
        "ARMENIA",
        "AZERBAIJAN",
        "BELARUS",
        "MOLDOVA",
        "SOMALIA",
        "SUDAN",
        "LIBYA",
        "ALGERIA",
        "MOROCCO",
        "TUNISIA",
        "CONGO",
        "CAMEROON",
        "GHANA",
        "SENEGAL",
        "MALI",
        "PANAMA",
        "ECUADOR",
        "BOLIVIA",
        "PARAGUAY",
        "URUGUAY",
        "GREECE",
        "PORTUGAL",
        "NETHERLANDS",
        "BELGIUM",
        "AUSTRIA",
        "SWITZERLAND",
        "DENMARK",
        "SWEDEN",
        "NORWAY",
        "FINLAND",
        "ICELAND",
        "IRELAND",
        "CZECH REPUBLIC",
        "HUNGARY",
        "ROMANIA",
        "BULGARIA",
        "SERBIA",
        "CROATIA",
        "SLOVENIA",
        "ALBANIA",
        "MYANMAR",
        "BANGLADESH",
    }

    results = []
    for item in data:
        idx = item.get("idx", 0) - 1
        if idx < 0 or idx >= len(titles_batch):
            continue
        raw_ec = item.get("entity_countries", {})
        if not isinstance(raw_ec, dict):
            raw_ec = {}
        # Normalize and filter
        ec = {}
        for entity, code in raw_ec.items():
            if not entity or not code:
                continue
            entity = str(entity).strip().upper()
            code = str(code).strip().upper()
            if len(code) < 2 or len(code) > 10:
                continue
            # Skip country names mapped to themselves
            if entity in COUNTRY_NAMES:
                continue
            # Skip continent references (Africa/African, Asia/Asian, America/American)
            # but NOT "South Africa" (ZA) or "South African" (ZA)
            e_lower = entity.lower()
            if "south afric" in e_lower:
                ec[entity] = "ZA"
                continue
            if any(c in e_lower for c in ("afric", "asia", "americ")):
                continue
            # Europe/European in any language -> EU
            if "europ" in e_lower:
                ec[entity] = "EU"
                continue
            ec[entity] = code
        results.append(
            {
                "title_id": titles_batch[idx]["id"],
                "entity_countries": ec,
            }
        )

    return results


def update_db(conn, results: list[dict], dry_run: bool):
    """Update only entity_countries in title_labels."""
    if not results:
        return 0
    cur = conn.cursor()
    updated = 0
    for r in results:
        ec_json = json.dumps(r["entity_countries"])
        if dry_run:
            if r["entity_countries"]:
                print("    {} -> {}".format(r["title_id"][:12], ec_json))
            continue
        cur.execute(
            """
            UPDATE title_labels
            SET entity_countries = %s::jsonb
            WHERE title_id = %s
        """,
            (ec_json, r["title_id"]),
        )
        updated += cur.rowcount
    if not dry_run:
        conn.commit()
    cur.close()
    return updated


def process_batch(batch: list[dict], batch_num: int, dry_run: bool) -> dict:
    """Process a single batch: call LLM, parse, update DB."""
    try:
        response = call_llm(batch)
        results = parse_response(response, batch)
        non_empty = sum(1 for r in results if r["entity_countries"])

        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
        )
        updated = update_db(conn, results, dry_run)
        conn.close()

        return {
            "batch": batch_num,
            "total": len(batch),
            "parsed": len(results),
            "non_empty": non_empty,
            "updated": updated,
        }
    except Exception as e:
        return {"batch": batch_num, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Backfill entity_countries only (minimal LLM prompt)"
    )
    parser.add_argument("--month", required=True, help="CTM month (YYYY-MM-DD)")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument(
        "--max-titles", type=int, default=0, help="Limit titles (0=all)"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    titles = get_titles(conn, args.month)
    conn.close()

    if args.max_titles > 0:
        titles = titles[: args.max_titles]

    total = len(titles)
    batches = [
        titles[i : i + args.batch_size] for i in range(0, total, args.batch_size)
    ]

    print("Backfill entity_countries for month={}".format(args.month))
    print(
        "Titles: {}, Batches: {}, Batch size: {}, Concurrency: {}".format(
            total, len(batches), args.batch_size, args.concurrency
        )
    )
    if args.dry_run:
        print("DRY RUN - no DB writes")
    print()

    total_updated = 0
    total_non_empty = 0
    total_errors = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {
            executor.submit(process_batch, batch, i + 1, args.dry_run): i
            for i, batch in enumerate(batches)
        }
        for future in as_completed(futures):
            result = future.result()
            if "error" in result:
                total_errors += 1
                print(
                    "[Batch {}/{}] ERROR: {}".format(
                        result["batch"], len(batches), result["error"]
                    )
                )
            else:
                total_updated += result["updated"]
                total_non_empty += result["non_empty"]
                elapsed = time.time() - t0
                print(
                    "[Batch {}/{}] parsed={}, with_entities={}, updated={} ({:.0f}s)".format(
                        result["batch"],
                        len(batches),
                        result["parsed"],
                        result["non_empty"],
                        result["updated"],
                        elapsed,
                    )
                )

    elapsed = time.time() - t0
    print(
        "\nDone in {:.0f}s. Updated: {}, With entities: {}, Errors: {}".format(
            elapsed, total_updated, total_non_empty, total_errors
        )
    )


if __name__ == "__main__":
    main()
