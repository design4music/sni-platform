"""
Phase 4.2h: LLM review of mechanical narrative matches.

For each operational narrative, sends its matched events to the LLM
and asks which ones DON'T belong. Removes false positives.

One LLM call per narrative. ~108 calls.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor

from core.config import config
from core.llm_logger import log_llm_call
from core.llm_utils import check_rate_limit

SYSTEM_PROMPT = """You review event-narrative matches for quality.

You will receive a strategic narrative (claim + description) and a numbered list
of events that were mechanically matched to it.

Your job: identify events that DO NOT genuinely belong. An event belongs if it
directly advances, defends, or challenges the narrative's claim. An event does
NOT belong if it merely involves the same country/topic but is about something else.

Return a JSON array of event numbers to REMOVE:
  [3, 7, 12]

Return [] if all events belong. Be conservative -- only remove clear mismatches.
Return ONLY valid JSON, no other text."""


def call_llm(user_prompt, max_tokens=1000):
    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }

    for attempt in range(config.llm_retry_attempts):
        try:
            t0 = time.time()
            with httpx.Client(timeout=config.llm_timeout_seconds) as client:
                response = client.post(
                    "%s/chat/completions" % config.deepseek_api_url,
                    headers=headers,
                    json=payload,
                )
                if check_rate_limit(response, attempt):
                    continue
                if response.status_code != 200:
                    raise RuntimeError(
                        "LLM error: %d %s" % (response.status_code, response.text[:200])
                    )

                data = response.json()
                log_llm_call(
                    "narrative_review",
                    data.get("usage"),
                    int((time.time() - t0) * 1000),
                )
                text = data["choices"][0]["message"]["content"].strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                return json.loads(text)
        except json.JSONDecodeError as e:
            print("  JSON parse error (attempt %d): %s" % (attempt + 1, e))
            if attempt == config.llm_retry_attempts - 1:
                return []
        except Exception as e:
            print("  LLM error (attempt %d): %s" % (attempt + 1, e))
            if attempt < config.llm_retry_attempts - 1:
                time.sleep(config.llm_retry_backoff**attempt)
            else:
                return []
    return []


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def review_operational(dry_run=False, narrative_id=None):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get operational narratives with mechanical matches
            where_nid = ""
            params = []
            if narrative_id:
                where_nid = "AND sn.id = %s"
                params = [narrative_id]

            cur.execute(
                """
                SELECT sn.id, sn.name, sn.claim, sn.matching_guidance
                FROM strategic_narratives sn
                WHERE sn.is_active = true AND sn.tier = 'operational'
                  AND EXISTS (
                      SELECT 1 FROM event_strategic_narratives esn
                      WHERE esn.narrative_id = sn.id
                      AND (esn.matched_signals->>'method' IS NULL
                           OR esn.matched_signals->>'method' != 'llm')
                  )
                  %s
                ORDER BY sn.id
            """
                % where_nid,
                params,
            )
            narratives = cur.fetchall()
            print("Reviewing %d operational narratives..." % len(narratives))

            total_removed = 0
            total_calls = 0

            for nar in narratives:
                # Fetch mechanical matches
                cur.execute(
                    """
                    SELECT esn.event_id, e.title, e.date::text as date,
                           LEFT(e.summary, 150) as summary
                    FROM event_strategic_narratives esn
                    JOIN events_v3 e ON e.id = esn.event_id
                    WHERE esn.narrative_id = %s
                      AND (esn.matched_signals->>'method' IS NULL
                           OR esn.matched_signals->>'method' != 'llm')
                    ORDER BY e.date DESC
                """,
                    (nar["id"],),
                )
                events = cur.fetchall()
                if not events:
                    continue

                # Build prompt
                lines = []
                lines.append("NARRATIVE: %s" % nar["name"])
                lines.append("Claim: %s" % (nar["claim"] or nar["name"]))
                if nar["matching_guidance"]:
                    lines.append("About: %s" % nar["matching_guidance"])
                lines.append("")
                lines.append("MATCHED EVENTS (remove any that don't belong):")
                # Cap at 80 to stay in context
                batch = events[:80]
                for i, ev in enumerate(batch, 1):
                    snippet = ""
                    if ev["summary"]:
                        snippet = " -- %s" % ev["summary"]
                    lines.append(
                        "%d. [%s] %s%s" % (i, ev["date"], ev["title"], snippet)
                    )

                prompt = "\n".join(lines)
                total_calls += 1

                if dry_run:
                    print("  [DRY] %s: %d events to review" % (nar["id"], len(batch)))
                    continue

                to_remove = call_llm(prompt, max_tokens=500)

                if not to_remove or not isinstance(to_remove, list):
                    if total_calls % 20 == 0:
                        print(
                            "  ...%d reviewed, %d removed"
                            % (total_calls, total_removed)
                        )
                    conn.commit()
                    continue

                # Remove flagged events
                removed = 0
                for idx in to_remove:
                    if isinstance(idx, int) and 1 <= idx <= len(batch):
                        ev = batch[idx - 1]
                        cur.execute(
                            "DELETE FROM event_strategic_narratives WHERE event_id = %s AND narrative_id = %s",
                            (ev["event_id"], nar["id"]),
                        )
                        removed += cur.rowcount

                total_removed += removed
                conn.commit()

                if removed > 0:
                    print("  %s: removed %d/%d" % (nar["id"], removed, len(batch)))

                if total_calls % 20 == 0:
                    print("  ...%d reviewed, %d removed" % (total_calls, total_removed))

            # Refresh weekly activity
            cur.execute(
                """
                INSERT INTO narrative_weekly_activity (narrative_id, week, event_count)
                SELECT esn.narrative_id, date_trunc('week', e.date::date)::date::text, COUNT(*)::int
                FROM event_strategic_narratives esn JOIN events_v3 e ON e.id = esn.event_id
                GROUP BY esn.narrative_id, date_trunc('week', e.date::date)::date::text
                ON CONFLICT (narrative_id, week) DO UPDATE SET event_count = EXCLUDED.event_count
            """
            )
            conn.commit()

            print(
                "Done: %d LLM calls, %d events removed" % (total_calls, total_removed)
            )
            return total_removed
    finally:
        conn.close()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    nid = None
    for arg in sys.argv:
        if arg.startswith("--narrative="):
            nid = arg.split("=", 1)[1]
    review_operational(dry_run=dry, narrative_id=nid)
