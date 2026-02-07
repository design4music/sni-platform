"""
Monthly Signal Rankings Generator

Computes top-5 signals per type for a given month and generates
LLM context for each signal based on its top events.

For each signal value (e.g. "TRUMP" in persons):
1. Find events whose titles mention this signal
2. Rank by source count, take top 10 events
3. Sample up to 5 titles per event
4. Ask LLM for 1-2 sentence strategic context

Usage:
    python -m pipeline.freeze.generate_signal_rankings --month 2026-01 --dry-run
    python -m pipeline.freeze.generate_signal_rankings --month 2026-01 --apply
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import httpx

# Windows console encoding fix
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2

from core.config import config
from core.prompts import SIGNAL_CONTEXT_SYSTEM_PROMPT, SIGNAL_CONTEXT_USER_PROMPT

SIGNAL_COLUMNS = [
    "persons",
    "orgs",
    "places",
    "commodities",
    "policies",
    "systems",
    "named_events",
]
TOP_N = 5
# Fetch extra candidates to account for filtering
FETCH_N = 15
EVENTS_PER_SIGNAL = 10
TITLES_PER_EVENT = 5

# ========================================================================
# Exclusion / dedup rules per signal type
# ========================================================================

# Systems: exclude generic terms, keep only brands/models/weapons
SYSTEMS_GENERIC = {
    "AI",
    "drones",
    "missiles",
    "satellites",
    "rockets",
    "submarines",
    "warships",
    "fighter jets",
    "tanks",
    "artillery",
    "radar",
    "nuclear weapons",
    "cyber",
    "malware",
    "ransomware",
}

# Named events: exclude sports and non-event entries
NAMED_EVENTS_EXCLUDE = {
    "Australian Open",
    "Super Bowl",
    "World Series",
    "Olympics",
    "Grammy",
    "Grammy Awards",
    "Grammys",
    "Oscar",
    "Oscars",
    "Academy Awards",
    "Emmy",
    "Golden Globe",
    "Golden Globes",
    "Champions League",
    "World Cup",
    "Wimbledon",
    "Tour de France",
    "Nobel Peace Prize",
    "Nobel Prize",
    "Nobel",
    "Pulitzer",
}

# Named events: merge groups (first entry is canonical name)
NAMED_EVENTS_MERGE = [
    ["Davos / WEF", "Davos", "World Economic Forum", "WEF"],
]


def should_exclude(signal_type, value):
    """Check if a signal value should be excluded."""
    if signal_type == "systems":
        return value in SYSTEMS_GENERIC
    if signal_type == "named_events":
        return value in NAMED_EVENTS_EXCLUDE
    return False


def merge_named_events(items):
    """Merge duplicate named events into canonical entries."""
    merged = []
    used = set()
    for group in NAMED_EVENTS_MERGE:
        canonical = group[0]
        aliases = set(group[1:])
        total_count = 0
        found = False
        for value, count in items:
            if value in aliases:
                total_count += count
                used.add(value)
                found = True
        if found:
            merged.append((canonical, total_count))

    # Add non-merged items
    for value, count in items:
        if value not in used:
            merged.append((value, count))

    # Re-sort by count descending
    merged.sort(key=lambda x: x[1], reverse=True)
    return merged


# ========================================================================
# Prompts
# ========================================================================
# Prompts imported from core.prompts:
# SIGNAL_CONTEXT_SYSTEM_PROMPT, SIGNAL_CONTEXT_USER_PROMPT


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def compute_top_signals(conn, month: str):
    """Compute top N signals per type for the month, with filtering."""
    cur = conn.cursor()
    results = {}
    for col in SIGNAL_COLUMNS:
        cur.execute(
            """
            SELECT val, COUNT(*) as cnt
            FROM title_labels tl
            JOIN titles_v3 t ON t.id = tl.title_id
            CROSS JOIN LATERAL unnest(tl.%s) AS val
            WHERE t.pubdate_utc >= %%s::date
              AND t.pubdate_utc < (%%s::date + INTERVAL '1 month')
            GROUP BY val ORDER BY cnt DESC LIMIT %%s
        """
            % col,
            (month + "-01", month + "-01", FETCH_N),
        )
        raw = [(row[0], row[1]) for row in cur.fetchall()]

        # Apply named_events merge before filtering
        if col == "named_events":
            raw = merge_named_events(raw)

        # Filter exclusions and take top N
        filtered = [(v, c) for v, c in raw if not should_exclude(col, v)][:TOP_N]

        results[col] = filtered
    cur.close()
    return results


def get_top_events_for_signal(conn, month, signal_col, signal_value):
    """Find top events whose titles mention this signal, ranked by size."""
    # For merged named_events, search for any alias
    search_values = [signal_value]
    for group in NAMED_EVENTS_MERGE:
        if signal_value == group[0]:
            search_values = group[1:]
            break

    placeholders = ",".join(["%s"] * len(search_values))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT e.id, e.title, e.source_batch_count,
               c.centroid_id, cv.label as centroid_label
        FROM events_v3 e
        JOIN event_v3_titles et ON et.event_id = e.id
        JOIN title_labels tl ON tl.title_id = et.title_id
        JOIN titles_v3 t ON t.id = et.title_id
        JOIN ctm c ON e.ctm_id = c.id
        JOIN centroids_v3 cv ON c.centroid_id = cv.id
        WHERE t.pubdate_utc >= %%s::date
          AND t.pubdate_utc < (%%s::date + INTERVAL '1 month')
          AND tl.%s && ARRAY[%s]::text[]
        GROUP BY e.id, e.title, e.source_batch_count, c.centroid_id, cv.label
        ORDER BY e.source_batch_count DESC
        LIMIT %%s
    """
        % (signal_col, placeholders),
        (month + "-01", month + "-01", *search_values, EVENTS_PER_SIGNAL),
    )
    events = cur.fetchall()
    cur.close()
    return events


def get_sample_titles_for_event(
    conn, event_id, signal_col, signal_value, limit=TITLES_PER_EVENT
):
    """Get sample titles for an event, filtered to those mentioning the signal."""
    search_values = [signal_value]
    for group in NAMED_EVENTS_MERGE:
        if signal_value == group[0]:
            search_values = group[1:]
            break

    placeholders = ",".join(["%s"] * len(search_values))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT t.title_display
        FROM event_v3_titles et
        JOIN titles_v3 t ON t.id = et.title_id
        JOIN title_labels tl ON tl.title_id = t.id
        WHERE et.event_id = %%s
          AND tl.%s && ARRAY[%s]::text[]
        ORDER BY t.pubdate_utc DESC
        LIMIT %%s
    """
        % (signal_col, placeholders),
        (event_id, *search_values, limit),
    )
    titles = [row[0] for row in cur.fetchall()]
    cur.close()
    return titles


def build_topics_text(conn, month, signal_col, signal_value):
    """Build formatted text of top events + sample titles for a signal."""
    events = get_top_events_for_signal(conn, month, signal_col, signal_value)
    if not events:
        return "(no events found)"

    parts = []
    for i, (eid, etitle, src_count, cent_id, cent_label) in enumerate(events, 1):
        titles = get_sample_titles_for_event(conn, eid, signal_col, signal_value)
        if not titles:
            continue
        header = "Topic %d: %s [%s, %d sources]" % (
            i,
            etitle or "(untitled)",
            cent_label,
            src_count or 0,
        )
        title_lines = "\n".join("  - %s" % t for t in titles)
        parts.append("%s\n%s" % (header, title_lines))

    return "\n\n".join(parts)


async def generate_context(month, signal_type, value, count, topics_text):
    """Call LLM to generate context for one signal."""
    user_msg = SIGNAL_CONTEXT_USER_PROMPT.format(
        signal_type=signal_type,
        value=value,
        month=month,
        count=count,
        topics_text=topics_text,
    )

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": SIGNAL_CONTEXT_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.3,
        "max_tokens": 150,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "%s/chat/completions" % config.deepseek_api_url,
            headers=headers,
            json=payload,
        )
        if resp.status_code != 200:
            raise Exception("LLM error: %d - %s" % (resp.status_code, resp.text))

        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


def save_rankings(conn, month, rankings):
    """Insert or update rankings into the table."""
    cur = conn.cursor()
    # Clear existing rankings for this month first
    cur.execute(
        "DELETE FROM monthly_signal_rankings WHERE month = %s", (month + "-01",)
    )
    for signal_type, items in rankings.items():
        for rank, (value, count, context) in enumerate(items, 1):
            cur.execute(
                """
                INSERT INTO monthly_signal_rankings
                    (month, signal_type, value, rank, count, context)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (month, signal_type, value)
                DO UPDATE SET rank = EXCLUDED.rank,
                              count = EXCLUDED.count,
                              context = EXCLUDED.context,
                              created_at = NOW()
            """,
                (month + "-01", signal_type, value, rank, count, context),
            )
    conn.commit()
    cur.close()


async def main():
    parser = argparse.ArgumentParser(description="Generate monthly signal rankings")
    parser.add_argument("--month", required=True, help="YYYY-MM format")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print results without saving"
    )
    parser.add_argument("--apply", action="store_true", help="Save to database")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("ERROR: specify --dry-run or --apply")
        sys.exit(1)

    conn = get_connection()

    print("Computing top signals for %s..." % args.month)
    top_signals = compute_top_signals(conn, args.month)

    total = sum(len(v) for v in top_signals.values())
    print("Found %d signals across %d categories" % (total, len(SIGNAL_COLUMNS)))

    rankings = {}
    processed = 0

    for signal_type in SIGNAL_COLUMNS:
        items = top_signals.get(signal_type, [])
        if not items:
            continue

        rankings[signal_type] = []
        for value, count in items:
            processed += 1
            print(
                "\n[%d/%d] %s: %s (%d mentions)"
                % (processed, total, signal_type, value, count)
            )

            topics_text = build_topics_text(conn, args.month, signal_type, value)

            if args.dry_run:
                print("  Top events preview:")
                for line in topics_text.split("\n")[:6]:
                    print("    %s" % line)
                rankings[signal_type].append((value, count, None))
            else:
                context = await generate_context(
                    args.month, signal_type, value, count, topics_text
                )
                print("  Context: %s" % context)
                rankings[signal_type].append((value, count, context))

    if args.apply:
        save_rankings(conn, args.month, rankings)
        print("\nSaved %d signal rankings to database." % processed)
    else:
        print("\nDry run complete. Use --apply to save.")

    conn.close()


if __name__ == "__main__":
    asyncio.run(main())
