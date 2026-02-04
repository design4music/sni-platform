"""
Cross-centroid epic explorer.

Finds all events matching a keyword across centroids and tracks,
groups them by perspective, and optionally synthesizes a narrative overview.

Usage:
    python -m pipeline.explore_epic greenland
    python -m pipeline.explore_epic greenland --synthesize
    python -m pipeline.explore_epic "gaza ceasefire" --min-sources 10
"""

import argparse
import sys
from collections import namedtuple

import psycopg2

from core.config import config

QUERY = """
SELECT
    e.id,
    e.title,
    e.summary,
    e.source_batch_count,
    e.tags,
    c.centroid_id,
    c.track,
    c.month
FROM events_v3 e
JOIN ctm c ON e.ctm_id = c.id
WHERE e.title ILIKE %s
  AND e.source_batch_count >= %s
ORDER BY e.source_batch_count DESC
"""

Row = namedtuple(
    "Row",
    [
        "id",
        "title",
        "summary",
        "source_batch_count",
        "tags",
        "centroid_id",
        "track",
        "month",
    ],
)


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def search_epic(keyword, min_sources=2):
    pattern = "%" + keyword + "%"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(QUERY, (pattern, min_sources))
        rows = [Row(*r) for r in cur.fetchall()]
    finally:
        conn.close()
    return rows


def group_by_centroid(rows):
    groups = {}
    for r in rows:
        cid = r.centroid_id
        if cid not in groups:
            groups[cid] = []
        groups[cid].append(r)
    return groups


def group_by_track(rows):
    groups = {}
    for r in rows:
        t = r.track
        if t not in groups:
            groups[t] = []
        groups[t].append(r)
    return groups


def print_report(keyword, rows):
    print("=" * 70)
    print("EPIC EXPLORER: %s" % keyword)
    print("=" * 70)

    total_sources = sum(r.source_batch_count for r in rows)
    by_centroid = group_by_centroid(rows)
    by_track = group_by_track(rows)

    print(
        "%d events | %d centroids | %d tracks | %d total sources"
        % (len(rows), len(by_centroid), len(by_track), total_sources)
    )
    print()

    # -- Centroid breakdown --
    print("--- BY CENTROID (perspective) ---")
    print()
    ranked = sorted(
        by_centroid.items(),
        key=lambda x: sum(r.source_batch_count for r in x[1]),
        reverse=True,
    )
    for centroid_id, events in ranked:
        src = sum(r.source_batch_count for r in events)
        print("  %s  (%d events, %d sources)" % (centroid_id, len(events), src))
        for ev in events[:3]:
            print("    [%4d] %s" % (ev.source_batch_count, ev.title))
        if len(events) > 3:
            print("    ... +%d more" % (len(events) - 3))
        print()

    # -- Track breakdown --
    print("--- BY TRACK (analytical lens) ---")
    print()
    ranked_tracks = sorted(
        by_track.items(),
        key=lambda x: sum(r.source_batch_count for r in x[1]),
        reverse=True,
    )
    for track, events in ranked_tracks:
        src = sum(r.source_batch_count for r in events)
        print("  %-30s %3d events, %5d sources" % (track, len(events), src))

    print()

    # -- Top 15 events --
    print("--- TOP 15 EVENTS (by source count) ---")
    print()
    for i, ev in enumerate(rows[:15], 1):
        print(
            "  %2d. [%4d src] %-20s | %-25s"
            % (i, ev.source_batch_count, ev.centroid_id, ev.track)
        )
        print("      %s" % ev.title)
    print()


def synthesize(keyword, rows):
    """Feed grouped data to LLM for narrative synthesis via DeepSeek."""
    import httpx

    by_centroid = group_by_centroid(rows)
    ranked = sorted(
        by_centroid.items(),
        key=lambda x: sum(r.source_batch_count for r in x[1]),
        reverse=True,
    )

    # Build a compact representation for the LLM
    lines = []
    for centroid_id, events in ranked[:15]:
        src = sum(r.source_batch_count for r in events)
        lines.append("## %s (%d events, %d sources)" % (centroid_id, len(events), src))
        for ev in events[:5]:
            lines.append("- [%d src] %s" % (ev.source_batch_count, ev.title))
            if ev.tags:
                lines.append("  tags: %s" % ev.tags)
        if len(events) > 5:
            lines.append("- ... +%d more events" % (len(events) - 5))
        lines.append("")

    corpus = "\n".join(lines)

    user_prompt = (
        'You are analyzing a cross-centroid "epic" -- a major story that spans '
        "multiple countries and analytical tracks in an international news "
        "monitoring system.\n\n"
        'Keyword: "%s"\n'
        "Data: %d events across %d centroids, %d total source articles.\n\n"
        "Each centroid represents a country or thematic lens (e.g., AMERICAS-USA "
        "sees this from the US perspective, EUROPE-NORDIC from Scandinavia, "
        "SYS-TRADE from trade policy).\n\n"
        "Below are the events grouped by centroid with their source counts "
        "(indicating media attention volume):\n\n"
        "%s\n\n"
        "Please provide:\n"
        "1. EPIC SUMMARY (2-3 sentences): What is this story about at its core?\n"
        "2. KEY PERSPECTIVES (bullet points): How do different centroids frame "
        "this story differently? What does each camp emphasize?\n"
        "3. NARRATIVE TENSIONS: Where do the perspectives clash or contradict?\n"
        "4. STORY ARC: What phases did this story go through (based on event "
        "titles)?\n"
        "5. BLIND SPOTS: What aspects might be under-covered based on the "
        "centroid distribution?\n\n"
        "Be concise and analytical. No fluff."
    ) % (
        keyword,
        len(rows),
        len(by_centroid),
        sum(r.source_batch_count for r in rows),
        corpus,
    )

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [{"role": "user", "content": user_prompt}],
        "temperature": 0.4,
        "max_tokens": 1500,
    }

    print("--- LLM SYNTHESIS ---")
    print()

    resp = httpx.post(
        "%s/chat/completions" % config.deepseek_api_url,
        headers=headers,
        json=payload,
        timeout=90,
    )

    if resp.status_code != 200:
        print("ERROR: LLM API returned %d: %s" % (resp.status_code, resp.text))
        return

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    print(content)
    print()
    print(
        "(tokens: %d in, %d out)"
        % (usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
    )


def main():
    parser = argparse.ArgumentParser(description="Cross-centroid epic explorer")
    parser.add_argument("keyword", help="Search keyword (e.g. greenland, gaza)")
    parser.add_argument(
        "--min-sources",
        type=int,
        default=2,
        help="Minimum source count per event (default: 2)",
    )
    parser.add_argument(
        "--synthesize",
        action="store_true",
        help="Run LLM synthesis on results",
    )
    args = parser.parse_args()

    rows = search_epic(args.keyword, args.min_sources)
    if not rows:
        print("No events found for '%s'" % args.keyword)
        sys.exit(0)

    print_report(args.keyword, rows)

    if args.synthesize:
        synthesize(args.keyword, rows)


if __name__ == "__main__":
    main()
