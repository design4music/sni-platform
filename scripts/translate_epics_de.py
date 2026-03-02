"""Translate epic titles, summaries, and timelines to German.

Targets epics from a given month (default: 2026-02) that have English
content but no German translation yet.
"""

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


async def translate(
    client: httpx.AsyncClient, text: str, style: str = "news"
) -> str | None:
    """Translate text to German. style: 'headline' for short titles, 'news' for prose."""
    if not text or not text.strip():
        return None

    if style == "headline":
        system_msg = (
            "Translate the following news headline to German. "
            "Return only the translation, nothing else."
        )
        max_tok = 80
    else:
        system_msg = (
            "Translate the following news text to German. "
            "Preserve paragraph structure. Return only the translation."
        )
        max_tok = min(len(text) * 2, 8000)

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": text},
        ],
        "temperature": 0.2,
        "max_tokens": max_tok,
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
        return data["choices"][0]["message"]["content"].strip().strip('"')
    except Exception:
        return None


async def main():
    parser = argparse.ArgumentParser(description="Translate epics to German")
    parser.add_argument("--month", default="2026-02", help="Target month (YYYY-MM)")
    parser.add_argument("--all", action="store_true", help="Translate all months")
    args = parser.parse_args()

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    # Ensure columns exist
    with conn.cursor() as cur:
        for col in ("title_de", "summary_de", "timeline_de"):
            cur.execute("ALTER TABLE epics ADD COLUMN IF NOT EXISTS %s TEXT" % col)
    conn.commit()

    # Fetch epics needing translation
    where = "WHERE title IS NOT NULL AND title_de IS NULL"
    params = ()
    if not args.all:
        where += " AND month = %s"
        params = (args.month + "-01",)

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, summary, timeline FROM epics %s ORDER BY created_at"
            % where,
            params,
        )
        rows = cur.fetchall()

    print("Found %d epics to translate" % len(rows))

    async with httpx.AsyncClient(timeout=90) as client:
        for i, (eid, title, summary, timeline) in enumerate(rows):
            print("[%d/%d] %s" % (i + 1, len(rows), title[:60]))

            title_de = await translate(client, title, "headline")
            summary_de = await translate(client, summary, "news") if summary else None
            timeline_de = (
                await translate(client, timeline, "news") if timeline else None
            )

            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE epics SET title_de = %s, summary_de = %s, timeline_de = %s "
                    "WHERE id = %s",
                    (title_de, summary_de, timeline_de, eid),
                )
            conn.commit()

            status = []
            if title_de:
                status.append("title")
            if summary_de:
                status.append("summary")
            if timeline_de:
                status.append("timeline")
            print("  OK: %s" % ", ".join(status))

    conn.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
