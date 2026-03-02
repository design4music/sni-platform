"""Backfill summary_text_de for CTMs that have English summary but no German."""

import argparse
import asyncio
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from core.config import config
from core.llm_utils import async_check_rate_limit

HEADERS = {
    "Authorization": "Bearer %s" % config.deepseek_api_key,
    "Content-Type": "application/json",
}
CONCURRENCY = 3


async def translate_summary(client: httpx.AsyncClient, text: str) -> str | None:
    payload = {
        "model": config.llm_model,
        "messages": [
            {
                "role": "system",
                "content": "Translate the following news summary to German. "
                "Preserve paragraph structure. Return only the translation.",
            },
            {"role": "user", "content": text},
        ],
        "temperature": 0.2,
        "max_tokens": min(len(text) * 2, 4000),
    }
    try:
        for attempt in range(3):
            resp = await client.post(
                "%s/chat/completions" % config.deepseek_api_url,
                headers=HEADERS,
                json=payload,
            )
            if await async_check_rate_limit(resp, attempt):
                continue
            if resp.status_code != 200:
                return None
            break
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


async def main():
    parser = argparse.ArgumentParser(description="Backfill CTM summary_text_de")
    parser.add_argument("--limit", type=int, default=None, help="Max CTMs to translate")
    parser.add_argument("--month", default=None, help="Target month (YYYY-MM)")
    args = parser.parse_args()

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    where = "WHERE summary_text IS NOT NULL AND summary_text_de IS NULL"
    params: list = []
    if args.month:
        where += " AND month = %s"
        params.append(args.month + "-01")

    sql = (
        "SELECT id, centroid_id, track, summary_text FROM ctm %s ORDER BY month DESC"
        % where
    )
    if args.limit:
        sql += " LIMIT %s"
        params.append(args.limit)

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    total = len(rows)
    print("Found %d CTMs needing summary_text_de" % total)

    sem = asyncio.Semaphore(CONCURRENCY)
    done = 0
    errors = 0

    async with httpx.AsyncClient(timeout=60) as client:

        async def process_one(ctm_id, centroid_id, track, summary):
            nonlocal done, errors
            async with sem:
                translated = await translate_summary(client, summary)
                if translated:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE ctm SET summary_text_de = %s WHERE id = %s",
                            (translated, ctm_id),
                        )
                    conn.commit()
                    done += 1
                else:
                    errors += 1
                if (done + errors) % 10 == 0:
                    print(
                        "  Progress: %d/%d (errors: %d)"
                        % (done + errors, total, errors)
                    )

        for i in range(0, total, 10):
            batch = rows[i : i + 10]
            tasks = [process_one(cid, cent, trk, txt) for cid, cent, trk, txt in batch]
            await asyncio.gather(*tasks)

    conn.close()
    print("Done. Translated: %d, Errors: %d" % (done, errors))


if __name__ == "__main__":
    asyncio.run(main())
