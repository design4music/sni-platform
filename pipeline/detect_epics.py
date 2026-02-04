"""
Auto-detect cross-centroid epics from tag co-occurrence.

Finds tags that bridge across many centroids, pulls events sharing
those tags, and presents candidates for human review.

Usage:
    # List candidate epic signals
    python -m pipeline.detect_epics

    # Explore a specific candidate
    python -m pipeline.detect_epics --tag place:greenland

    # Exclude false positives by event number
    python -m pipeline.detect_epics --tag place:greenland --exclude 5,12,18
"""

import argparse
import sys
from collections import defaultdict

import psycopg2

from core.config import config

# Tags that are too generic to anchor an epic
NOISE_TAGS = {
    "person:trump",
    "person:macron",
    "person:putin",
    "org:eu",
    "org:nato",
    "org:un",
    "topic:tariffs",
    "topic:trade",
    "topic:oil",
    "topic:gold",
    "topic:security",
    "topic:peace",
    "topic:ceasefire",
    "place:washington",
    "place:moscow",
    "place:beijing",
    "place:london",
    "place:paris",
    "place:brussels",
}


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


BRIDGE_QUERY = """
WITH event_tags AS (
    SELECT e.id, unnest(e.tags) AS tag, c.centroid_id,
           e.source_batch_count
    FROM events_v3 e
    JOIN ctm c ON e.ctm_id = c.id
    WHERE e.tags IS NOT NULL
      AND e.source_batch_count >= %s
)
SELECT tag,
       count(DISTINCT centroid_id) AS centroid_spread,
       count(*) AS event_count,
       sum(source_batch_count) AS total_sources
FROM event_tags
GROUP BY tag
HAVING count(DISTINCT centroid_id) >= %s
ORDER BY count(DISTINCT centroid_id) DESC, sum(source_batch_count) DESC
"""

EVENTS_BY_TAG_QUERY = """
SELECT e.id, e.title, e.tags, e.source_batch_count, e.date,
       c.centroid_id, c.track
FROM events_v3 e
JOIN ctm c ON e.ctm_id = c.id
WHERE %s = ANY(e.tags)
  AND e.source_batch_count >= %s
ORDER BY e.source_batch_count DESC
"""


def find_bridge_tags(min_sources=5, min_centroids=5):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(BRIDGE_QUERY, (min_sources, min_centroids))
        rows = cur.fetchall()
    finally:
        conn.close()

    # Filter noise
    results = []
    for tag, spread, count, sources in rows:
        if tag not in NOISE_TAGS:
            results.append((tag, spread, count, sources))
    return results


def explore_tag(tag, min_sources=3):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(EVENTS_BY_TAG_QUERY, (tag, min_sources))
        rows = cur.fetchall()
    finally:
        conn.close()
    return rows


def compute_tag_cohesion(events, anchor_tag):
    """Score how well each event fits the epic by shared tags with peers."""
    # Collect all tags across events (excluding anchor and noise)
    all_tags = defaultdict(int)
    event_tags = {}
    for ev in events:
        eid = ev[0]
        tags = set(ev[2] or []) - NOISE_TAGS - {anchor_tag}
        event_tags[eid] = tags
        for t in tags:
            all_tags[t] += 1

    # Core tags = appear in 30%+ of events
    threshold = max(2, len(events) * 0.3)
    core_tags = {t for t, c in all_tags.items() if c >= threshold}

    # Score each event: how many core tags it shares
    scores = {}
    for eid, tags in event_tags.items():
        overlap = tags & core_tags
        scores[eid] = len(overlap)

    return scores, core_tags


def print_candidates(bridge_tags):
    print("=" * 70)
    print("EPIC DETECTOR: candidate bridge signals")
    print("=" * 70)
    print()
    print("  %-25s %6s %6s %8s" % ("TAG", "SPREAD", "EVENTS", "SOURCES"))
    print("  " + "-" * 50)
    for tag, spread, count, sources in bridge_tags:
        print("  %-25s %6d %6d %8d" % (tag, spread, count, sources))
    print()
    print("Run with --tag <tag> to explore a candidate.")
    print()


def print_epic(tag, events, exclude_nums=None):
    exclude_nums = exclude_nums or set()

    scores, core_tags = compute_tag_cohesion(events, tag)

    # Collect centroids
    centroids = set()
    included = []
    excluded = []

    print("=" * 70)
    print("EPIC CANDIDATE: %s" % tag)
    print("=" * 70)
    print()

    if core_tags:
        sorted_core = sorted(
            core_tags, key=lambda t: -sum(1 for ev in events if t in set(ev[2] or []))
        )
        print("Core co-occurring tags: %s" % ", ".join(sorted_core[:10]))
        print()

    print("  %3s %4s  %-20s %-25s %s" % ("#", "SRC", "CENTROID", "TRACK", "TITLE"))
    print("  " + "-" * 90)

    for i, ev in enumerate(events, 1):
        eid, title, tags, src, date, centroid, track = ev
        cohesion = scores.get(eid, 0)

        marker = " "
        if i in exclude_nums:
            marker = "X"
            excluded.append(ev)
        else:
            included.append(ev)
            centroids.add(centroid)

        # Flag low-cohesion events
        warn = ""
        if cohesion == 0 and len(core_tags) > 0:
            warn = " [?]"

        print(
            " %s%3d [%3d] %-20s %-25s %s%s"
            % (marker, i, src, centroid, track, title[:70], warn)
        )

    print()

    # Summary
    inc_sources = sum(ev[3] for ev in included)
    print(
        "Included: %d events | %d centroids | %d sources"
        % (len(included), len(centroids), inc_sources)
    )
    if excluded:
        print("Excluded: %d events" % len(excluded))
    print()

    # Per-centroid signal fingerprint
    print("--- CENTROID SIGNALS ---")
    print()
    centroid_tags = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for ev in included:
        centroid = ev[5]
        for t in ev[2] or []:
            if t != tag and t not in NOISE_TAGS:
                centroid_tags[centroid][t][0] += ev[3]
                centroid_tags[centroid][t][1] += 1

    # Count global tag frequency for distinctiveness
    global_freq = defaultdict(int)
    for cid, tags in centroid_tags.items():
        for t in tags:
            global_freq[t] += 1

    sorted_centroids = sorted(
        centroid_tags.items(),
        key=lambda x: sum(v[0] for v in x[1].values()),
        reverse=True,
    )

    for centroid, tags in sorted_centroids:
        top = sorted(tags.items(), key=lambda x: x[1][0], reverse=True)[:6]
        parts = []
        for t, (weight, count) in top:
            marker = "*" if global_freq[t] <= 3 else ""
            parts.append("%s%s(%d)" % (marker, t, count))
        print("  %-20s %s" % (centroid, "  ".join(parts)))

    print()
    print("  * = distinctive (<=3 centroids)")
    print("  [?] = low cohesion with core tags")
    print()

    return included, excluded


def llm_filter(tag, events):
    """Ask DeepSeek to classify which events belong to this epic."""
    import httpx

    # Build numbered list of titles for the LLM
    lines = []
    for i, ev in enumerate(events, 1):
        eid, title, tags, src, date, centroid, track = ev
        lines.append("%d. [%s | %s] %s" % (i, centroid, track, title))

    event_list = "\n".join(lines)

    prompt = (
        "You are filtering events for a cross-centroid news epic.\n\n"
        "The anchor signal is: %s\n"
        "Below are %d events that contain this tag. Some genuinely belong "
        "to the epic (they are about the same geopolitical development). "
        "Others merely mention the keyword in passing alongside unrelated "
        "topics.\n\n"
        "EVENTS:\n%s\n\n"
        "For each event, respond with ONLY a JSON array of objects:\n"
        '[{"n": 1, "keep": true}, {"n": 2, "keep": false}, ...]\n\n'
        "Rules:\n"
        "- keep=true if the event is primarily about the %s story\n"
        "- keep=true if the event covers a direct consequence or reaction "
        "to the %s story (e.g. sanctions, protests, diplomatic fallout)\n"
        "- keep=false if the event is about a different topic that merely "
        "mentions %s in passing\n"
        "- keep=false if the event is a news roundup where %s is one of "
        "many unrelated items\n\n"
        "Return ONLY the JSON array, no other text."
    ) % (tag, len(events), event_list, tag, tag, tag, tag)

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 2000,
    }

    print("Running LLM filter on %d events..." % len(events))

    resp = httpx.post(
        "%s/chat/completions" % config.deepseek_api_url,
        headers=headers,
        json=payload,
        timeout=90,
    )

    if resp.status_code != 200:
        print("ERROR: LLM API returned %d: %s" % (resp.status_code, resp.text))
        return set()

    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})

    # Parse JSON response
    import json

    # Strip markdown fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]

    try:
        decisions = json.loads(content)
    except json.JSONDecodeError:
        print("ERROR: Could not parse LLM response as JSON")
        print("Raw response: %s" % content[:500])
        return set()

    exclude = set()
    for d in decisions:
        if not d.get("keep", True):
            exclude.add(d["n"])

    print(
        "LLM verdict: %d keep, %d exclude (tokens: %d in, %d out)"
        % (
            len(events) - len(exclude),
            len(exclude),
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )
    )
    print()

    return exclude


def main():
    parser = argparse.ArgumentParser(description="Detect cross-centroid epics")
    parser.add_argument("--tag", help="Explore a specific bridge tag")
    parser.add_argument(
        "--exclude",
        help="Comma-separated event numbers to exclude (e.g. 5,12,18)",
    )
    parser.add_argument(
        "--min-sources",
        type=int,
        default=5,
        help="Min sources per event (default: 5)",
    )
    parser.add_argument(
        "--min-centroids",
        type=int,
        default=5,
        help="Min centroid spread for bridge detection (default: 5)",
    )
    parser.add_argument(
        "--filter",
        action="store_true",
        help="Use LLM to auto-filter false positives",
    )
    args = parser.parse_args()

    if args.tag:
        events = explore_tag(args.tag, min_sources=args.min_sources)
        if not events:
            print("No events found for tag '%s'" % args.tag)
            sys.exit(0)

        exclude = set()
        if args.exclude:
            exclude = {int(x.strip()) for x in args.exclude.split(",")}

        if args.filter:
            llm_exclude = llm_filter(args.tag, events)
            exclude = exclude | llm_exclude

        print_epic(args.tag, events, exclude)
    else:
        bridge_tags = find_bridge_tags(args.min_sources, args.min_centroids)
        if not bridge_tags:
            print("No bridge signals found.")
            sys.exit(0)
        print_candidates(bridge_tags)


if __name__ == "__main__":
    main()
