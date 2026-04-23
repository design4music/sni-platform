"""Phase 4.5-day: Daily brief generation (2026-04-15)

For each (ctm_id, date) where promoted_cluster_count > DAILY_BRIEF_MIN_CLUSTERS,
generate a thematic brief from today's top stories, with 1-day cross-month
lookback for identity dedup.

Pipeline per CTM:
  1. Load today's promoted events grouped by date (title + summary + source_count)
  2. For each qualifying date:
     - Fetch yesterday's promoted events for the SAME (centroid_id, track, date-1).
       Cross-month: queries by date only; previous CTM found via centroid+track.
     - Call LLM: EN + DE brief, 150-250 words each
     - Upsert into daily_briefs
"""

import argparse
import asyncio
import json
import sys
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

import httpx
import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import DAILY_BRIEF_MIN_CLUSTERS, DAY_CLOSURE_UTC_HOUR, config
from core.llm_logger import log_llm_call
from core.llm_utils import async_check_rate_limit, extract_json, fix_role_hallucinations
from core.prompts import DAILY_BRIEF_SYSTEM_PROMPT, DAILY_BRIEF_USER_PROMPT

LLM_CONCURRENCY = 4


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def load_ctm_meta(conn, ctm_id: str) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT centroid_id, track, month FROM ctm WHERE id = %s", (ctm_id,)
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("CTM not found: %s" % ctm_id)
        return {"centroid_id": row[0], "track": row[1], "month": row[2]}


def load_today_events_by_date(conn, ctm_id: str) -> dict:
    """Return {date: [{source_count, title, summary}...]} for promoted events only."""
    by_date: dict = defaultdict(list)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT date, source_batch_count, title, summary
              FROM events_v3
             WHERE ctm_id = %s AND is_promoted = true
             ORDER BY date, source_batch_count DESC
            """,
            (ctm_id,),
        )
        for d, src, title, summary in cur.fetchall():
            by_date[d].append(
                {
                    "source_count": src,
                    "title": title or "",
                    "summary": summary or "",
                }
            )
    return dict(by_date)


def load_yesterday_titles(
    conn, centroid_id: str, track: str, yesterday: object
) -> list:
    """Cross-month lookback: promoted event titles from yesterday (centroid+track scoped)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT e.source_batch_count, e.title
              FROM events_v3 e
              JOIN ctm c ON c.id = e.ctm_id
             WHERE c.centroid_id = %s
               AND c.track = %s
               AND e.date = %s
               AND e.is_promoted = true
             ORDER BY e.source_batch_count DESC
            """,
            (centroid_id, track, yesterday),
        )
        return [{"source_count": r[0], "title": r[1] or ""} for r in cur.fetchall()]


def format_today_stories(events: list) -> str:
    lines = []
    for ev in events:
        title = ev["title"].strip()
        summary = (ev["summary"] or "").strip().replace("\n", " ")
        if summary:
            lines.append("[%d] %s. %s" % (ev["source_count"], title, summary))
        else:
            lines.append("[%d] %s" % (ev["source_count"], title))
    return "\n".join(lines)


def format_yesterday_block(yday: list) -> str:
    if not yday:
        return ""
    lines = "\n".join("[%d] %s" % (y["source_count"], y["title"].strip()) for y in yday)
    return "\n\nYESTERDAY (dedup reference, titles only):\n" + lines


async def call_llm(payload: dict) -> dict:
    import time as _time

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=120) as client:
        for attempt in range(3):
            t0 = _time.time()
            response = await client.post(
                "%s/chat/completions" % config.deepseek_api_url,
                headers=headers,
                json=payload,
            )
            if await async_check_rate_limit(response, attempt):
                continue
            if response.status_code != 200:
                raise RuntimeError(
                    "LLM error %d: %s" % (response.status_code, response.text[:200])
                )
            data = response.json()
            log_llm_call(
                "daily_brief", data.get("usage"), int((_time.time() - t0) * 1000)
            )
            return extract_json(data["choices"][0]["message"]["content"])
        raise RuntimeError("LLM retries exhausted")


async def generate_brief(
    date: object,
    today_events: list,
    yesterday_titles: list,
) -> dict:
    today_text = format_today_stories(today_events)
    yesterday_block = format_yesterday_block(yesterday_titles)
    user_prompt = DAILY_BRIEF_USER_PROMPT.format(
        date=date.isoformat(),
        today_count=len(today_events),
        today_stories_text=today_text,
        yesterday_block=yesterday_block,
    )
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": DAILY_BRIEF_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 1500,
    }
    result = await call_llm(payload)

    # Parse blocks array → join with double newline for storage
    blocks = result.get("blocks") or []
    en_parts = []
    de_parts = []
    for block in blocks:
        en = fix_role_hallucinations((block.get("en") or "").strip())
        de = (block.get("de") or "").strip()
        if en:
            en_parts.append(en)
        if de:
            de_parts.append(de)

    # Fallback: if LLM returned old single-string format
    if not en_parts and result.get("brief_en"):
        en_parts = [fix_role_hallucinations(result["brief_en"].strip())]
        de_parts = [(result.get("brief_de") or "").strip()]

    return {
        "brief_en": "\n\n".join(en_parts),
        "brief_de": "\n\n".join(de_parts) or None,
    }


def compute_themes(conn, ctm_id: str, date) -> list:
    """Mechanical theme aggregation from title_labels of promoted clusters."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tl.sector, tl.subject, COUNT(*) AS weight
              FROM events_v3 e
              JOIN event_v3_titles et ON et.event_id = e.id
              JOIN title_labels tl ON tl.title_id = et.title_id
             WHERE e.ctm_id = %s AND e.date = %s AND e.is_promoted = true
               AND tl.sector IS NOT NULL AND tl.sector != 'NON_STRATEGIC'
             GROUP BY tl.sector, tl.subject
             ORDER BY weight DESC
             LIMIT 4
            """,
            (ctm_id, date),
        )
        rows = cur.fetchall()
    if not rows:
        return []
    total = sum(r[2] for r in rows)
    return [
        {"sector": r[0], "subject": r[1], "weight": round(r[2] / total, 2)}
        for r in rows
    ]


async def process_ctm(ctm_id: str) -> dict:
    conn = get_conn()
    try:
        meta = load_ctm_meta(conn, ctm_id)
        by_date = load_today_events_by_date(conn, ctm_id)

        # Day-closure gate: a day is "closed" when UTC clock passes
        # DAY_CLOSURE_UTC_HOUR (default 08:00) the following day. This covers
        # all practical timezones (US West Coast = UTC-8).
        from datetime import datetime, timezone

        now_utc = datetime.now(timezone.utc)
        # A day D is closed if now >= D+1 at DAY_CLOSURE_UTC_HOUR UTC
        # Equivalently: D <= today - 1 day, BUT only after the hour threshold
        cutoff = (now_utc - timedelta(hours=DAY_CLOSURE_UTC_HOUR)).date()
        qualifying = [
            (d, evs)
            for d, evs in by_date.items()
            if len(evs) > DAILY_BRIEF_MIN_CLUSTERS and d < cutoff
        ]
        qualifying.sort(key=lambda x: x[0])
        print(
            "  %s/%s/%s: %d days with >%d promoted"
            % (
                meta["centroid_id"],
                meta["track"],
                meta["month"],
                len(qualifying),
                DAILY_BRIEF_MIN_CLUSTERS,
            )
        )

        sem = asyncio.Semaphore(LLM_CONCURRENCY)
        written = 0

        async def run_one(date, today_evs):
            nonlocal written
            async with sem:
                yday = load_yesterday_titles(
                    conn, meta["centroid_id"], meta["track"], date - timedelta(days=1)
                )
                try:
                    result = await generate_brief(date, today_evs, yday)
                except Exception as e:
                    print("  brief fail %s: %s" % (date, e))
                    return
                themes = compute_themes(conn, ctm_id, date)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO daily_briefs
                            (ctm_id, date, brief_en, brief_de,
                             promoted_cluster_count, coherent, themes, generated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (ctm_id, date) DO UPDATE
                           SET brief_en = EXCLUDED.brief_en,
                               brief_de = EXCLUDED.brief_de,
                               promoted_cluster_count = EXCLUDED.promoted_cluster_count,
                               coherent = EXCLUDED.coherent,
                               themes = EXCLUDED.themes,
                               generated_at = NOW()
                        """,
                        (
                            ctm_id,
                            date,
                            result["brief_en"],
                            result["brief_de"] or None,
                            len(today_evs),
                            True,
                            json.dumps(themes) if themes else None,
                        ),
                    )
                conn.commit()
                written += 1

        tasks = [run_one(d, evs) for d, evs in qualifying]
        if tasks:
            await asyncio.gather(*tasks)

        return {"qualifying": len(qualifying), "written": written}
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ctm-id", required=True)
    args = parser.parse_args()
    stats = asyncio.run(process_ctm(args.ctm_id))
    print("DONE", stats)


if __name__ == "__main__":
    main()
