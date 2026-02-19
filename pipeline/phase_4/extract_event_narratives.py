"""
Event Narrative Extraction

Single-pass LLM analysis to identify 2-5 narrative frames from high-source
events. Stores results in narratives table with entity_type='event'.

Modes:
  - Default: process events that have no narratives yet
  - --refresh: re-process events whose source_batch_count grew significantly

Usage:
    python pipeline/phase_4/extract_event_narratives.py --dry-run
    python pipeline/phase_4/extract_event_narratives.py --limit 50
    python pipeline/phase_4/extract_event_narratives.py --refresh
    python pipeline/phase_4/extract_event_narratives.py --ctm <UUID>
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config  # noqa: E402
from core.llm_utils import extract_json  # noqa: E402
from core.prompts import EVENT_NARRATIVE_SYSTEM, EVENT_NARRATIVE_USER  # noqa: E402
from pipeline.epics.build_epics import fetch_wikipedia_context  # noqa: E402
from pipeline.phase_4.extract_ctm_narratives import sample_titles  # noqa: E402

MIN_SOURCES = config.v3_p5e_min_sources
REFRESH_GROWTH = config.v3_p5e_refresh_growth


def get_db_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def fetch_events(conn, limit=50, ctm_id=None, refresh=False):
    """Fetch events eligible for narrative extraction.

    Default mode: events with no narratives yet.
    Refresh mode: events whose source_batch_count grew by >= REFRESH_GROWTH
    since narratives were last created.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        base_where = """
            e.source_batch_count >= %s
            AND e.is_catchall = false
            AND e.title IS NOT NULL
        """
        params = [MIN_SOURCES]

        # Skip frozen CTMs in daemon mode, but allow when targeting a specific CTM
        if not ctm_id:
            base_where += " AND c.is_frozen = false"

        if refresh:
            base_where += """
                AND EXISTS (
                    SELECT 1 FROM narratives n
                    WHERE n.entity_type = 'event' AND n.entity_id = e.id
                )
                AND e.source_batch_count >= (
                    SELECT COALESCE(
                        (n2.signal_stats->>'source_count_at_extraction')::int, 0
                    )
                    FROM narratives n2
                    WHERE n2.entity_type = 'event' AND n2.entity_id = e.id
                    LIMIT 1
                ) + %s
            """
            params.append(REFRESH_GROWTH)
        else:
            base_where += """
                AND NOT EXISTS (
                    SELECT 1 FROM narratives n
                    WHERE n.entity_type = 'event' AND n.entity_id = e.id
                )
            """

        if ctm_id:
            base_where += " AND e.ctm_id = %s"
            params.append(ctm_id)

        params.append(limit)
        cur.execute(
            """
            SELECT e.id, e.title, e.summary, e.source_batch_count,
                   e.ctm_id, c.centroid_id, c.track
            FROM events_v3 e
            JOIN ctm c ON c.id = e.ctm_id
            WHERE """
            + base_where
            + """
            ORDER BY e.source_batch_count DESC
            LIMIT %s
            """,
            params,
        )
        return cur.fetchall()


def fetch_event_titles(conn, event_id):
    """Fetch headlines for an event with publisher and language info."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT DISTINCT t.title_display, t.publisher_name, t.pubdate_utc,
                   t.detected_language
            FROM event_v3_titles evt
            JOIN titles_v3 t ON t.id = evt.title_id
            WHERE evt.event_id = %s
            ORDER BY t.pubdate_utc DESC
            """,
            (str(event_id),),
        )
        return cur.fetchall()


def build_titles_block(titles):
    """Format titles for LLM prompt, including date prefix."""
    lines = []
    for i, t in enumerate(titles, 1):
        pub = t.get("publisher_name") or "unknown"
        dt = t.get("pubdate_utc")
        day = str(dt)[:10] if dt else ""
        lines.append("%d. [%s][%s] %s" % (i, day, pub, t["title_display"]))
    return "\n".join(lines)


def extract_narratives_llm(event, sampled, wiki_context=None):
    """Call LLM to extract narrative frames."""
    titles_block = build_titles_block(sampled)

    wiki_block = ""
    if wiki_context:
        wiki_block = "\nBackground context (from Wikipedia):\n%s\n" % wiki_context

    user_prompt = EVENT_NARRATIVE_USER.format(
        event_title=event["title"] or "",
        event_summary=event["summary"] or "",
        title_count=len(sampled),
        titles_block=titles_block,
        wiki_block=wiki_block,
    )

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": EVENT_NARRATIVE_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1000,
    }

    resp = httpx.post(
        "%s/chat/completions" % config.deepseek_api_url,
        headers=headers,
        json=payload,
        timeout=120,
    )

    if resp.status_code != 200:
        raise Exception("LLM error: %d - %s" % (resp.status_code, resp.text[:200]))

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    tok_in = usage.get("prompt_tokens", 0)
    tok_out = usage.get("completion_tokens", 0)

    frames = extract_json(content)
    return frames, tok_in, tok_out


def compute_top_sources(titles, indices):
    """Top sources from title indices."""
    sources = Counter()
    for idx in indices:
        if 0 < idx <= len(titles):
            pub = titles[idx - 1].get("publisher_name") or "unknown"
            sources[pub] += 1
    return [s for s, _ in sources.most_common(10)]


def delete_event_narratives(conn, event_id):
    """Delete existing narratives for an event (used before refresh)."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM narratives WHERE entity_type = 'event' AND entity_id = %s",
            (str(event_id),),
        )
        deleted = cur.rowcount
    conn.commit()
    return deleted


def save_narratives(conn, event_id, frames, titles, source_batch_count):
    """Save extracted frames to narratives table."""
    saved = 0
    stats_json = json.dumps({"source_count_at_extraction": source_batch_count})

    with conn.cursor() as cur:
        for frame in frames:
            label = frame.get("label", "").strip()
            if not label:
                continue

            indices = frame.get("title_indices", [])
            title_count = len(indices)
            top_sources = compute_top_sources(titles, indices)

            sample_titles = []
            for idx in indices[:15]:
                if 0 < idx <= len(titles):
                    t = titles[idx - 1]
                    sample_titles.append(
                        {
                            "title": t["title_display"],
                            "publisher": t.get("publisher_name") or "",
                        }
                    )

            cur.execute(
                """
                INSERT INTO narratives
                    (entity_type, entity_id, label, description, moral_frame,
                     title_count, top_sources, sample_titles, signal_stats)
                VALUES ('event', %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (entity_id, label) DO UPDATE SET
                    description = EXCLUDED.description,
                    moral_frame = EXCLUDED.moral_frame,
                    title_count = EXCLUDED.title_count,
                    top_sources = EXCLUDED.top_sources,
                    sample_titles = EXCLUDED.sample_titles,
                    signal_stats = EXCLUDED.signal_stats
                """,
                (
                    str(event_id),
                    label,
                    frame.get("description"),
                    frame.get("moral_frame"),
                    title_count,
                    top_sources,
                    json.dumps(sample_titles),
                    stats_json,
                ),
            )
            saved += 1

    conn.commit()
    return saved


def process_event_list(conn, events, refresh=False):
    """Process a list of events through narrative extraction.

    Returns dict with events, narratives, failed counts.
    """
    results = {"events": 0, "narratives": 0, "failed": 0}
    total_tok_in = 0
    total_tok_out = 0

    for i, event in enumerate(events, 1):
        print(
            "\n[%d/%d] %s (%d sources)"
            % (i, len(events), event["title"][:70], event["source_batch_count"])
        )

        titles = fetch_event_titles(conn, event["id"])
        if len(titles) < 10:
            print("  Skipping: only %d titles" % len(titles))
            results["failed"] += 1
            continue

        sampled = sample_titles(titles, time_stratify=True)
        lang_counts = Counter(t.get("detected_language") or "?" for t in sampled)
        top_langs = ", ".join("%s:%d" % (lg, c) for lg, c in lang_counts.most_common(5))
        # Count date coverage
        day_set = set()
        for t in sampled:
            dt = t.get("pubdate_utc")
            if dt:
                day_set.add(str(dt)[:10])
        print(
            "  %d titles, sampled %d (%s) spanning %d days"
            % (len(titles), len(sampled), top_langs, len(day_set))
        )

        # Fetch Wikipedia context for richer framing analysis
        wiki_context = None
        try:
            wiki_context = fetch_wikipedia_context(event["title"], [], month_str=None)
            if wiki_context:
                print("  Wikipedia context: %d chars" % len(wiki_context))
            else:
                print("  No Wikipedia context found")
        except Exception as e:
            print("  Wikipedia fetch failed: %s" % e)

        try:
            frames, tok_in, tok_out = extract_narratives_llm(
                event, sampled, wiki_context
            )
            total_tok_in += tok_in
            total_tok_out += tok_out
        except Exception as e:
            print("  ERROR: %s" % e)
            results["failed"] += 1
            continue

        if not frames or not isinstance(frames, list):
            print("  No frames extracted")
            results["failed"] += 1
            continue

        if refresh:
            deleted = delete_event_narratives(conn, event["id"])
            print("  Deleted %d old narratives" % deleted)

        saved = save_narratives(
            conn, event["id"], frames, sampled, event["source_batch_count"]
        )
        results["events"] += 1
        results["narratives"] += saved

        print("  -> %d narrative frames saved" % saved)
        for f in frames:
            print(
                "     [%s] %s (%d titles)"
                % (
                    f["label"],
                    f.get("description", "")[:60],
                    len(f.get("title_indices", [])),
                )
            )

    print(
        "\nComplete: %d events, %d narratives, %d failed"
        % (results["events"], results["narratives"], results["failed"])
    )
    print("Tokens: %d in, %d out" % (total_tok_in, total_tok_out))
    return results


def process_event_narratives(limit=50):
    """Daemon-callable entry point. Runs both new + refresh passes."""
    conn = get_db_connection()
    total = {"events": 0, "narratives": 0, "failed": 0}

    # Pass 1: new events without narratives
    new_events = fetch_events(conn, limit=limit)
    if new_events:
        print("New events: %d eligible" % len(new_events))
        r = process_event_list(conn, new_events, refresh=False)
        for k in total:
            total[k] += r[k]

    # Pass 2: refresh events with significant growth
    refresh_events = fetch_events(conn, limit=limit, refresh=True)
    if refresh_events:
        print("\nRefresh events: %d eligible" % len(refresh_events))
        r = process_event_list(conn, refresh_events, refresh=True)
        for k in total:
            total[k] += r[k]

    if not new_events and not refresh_events:
        print("No events need narrative extraction")

    conn.close()
    return total


def main():
    parser = argparse.ArgumentParser(
        description="Extract narrative frames from high-source events"
    )
    parser.add_argument("--limit", type=int, default=50, help="Max events to process")
    parser.add_argument("--ctm", type=str, help="Filter by CTM ID")
    parser.add_argument(
        "--refresh", action="store_true", help="Re-extract events with source growth"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be processed"
    )
    args = parser.parse_args()

    mode = "refresh" if args.refresh else "new"
    print("Event Narrative Extraction [%s mode]" % mode)
    print("=" * 50)

    conn = get_db_connection()

    events = fetch_events(conn, args.limit, args.ctm, refresh=args.refresh)
    print("Found %d events eligible for narrative extraction" % len(events))

    if not events:
        print("Nothing to process")
        conn.close()
        return

    if args.dry_run:
        print("\nDry run - would process:")
        for e in events:
            print(
                "  - [%d sources] %s / %s: %s"
                % (
                    e["source_batch_count"],
                    e["centroid_id"],
                    e["track"],
                    e["title"][:60],
                )
            )
        conn.close()
        return

    process_event_list(conn, events, refresh=args.refresh)
    conn.close()


if __name__ == "__main__":
    main()
