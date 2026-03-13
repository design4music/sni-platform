"""
Cross-Centroid Sibling Detection

Finds events that are the same real-world story appearing under different
country centroids. Uses IDF-weighted tag Dice + title word Dice similarity
(same algorithm as saga chaining, but across centroids instead of within).

Events sharing a sibling_group UUID are the same story viewed from different
country lenses (e.g., Trump-Netanyahu meeting appearing under US, Israel, Iran).

Usage:
    python -m pipeline.phase_4.detect_cross_centroid_siblings --dry-run
    python -m pipeline.phase_4.detect_cross_centroid_siblings --month 2026-01
    python -m pipeline.phase_4.detect_cross_centroid_siblings --min-sources 20
"""

import argparse
import sys
import uuid
from collections import defaultdict
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config  # noqa: E402
from pipeline.phase_4.chain_event_sagas import (  # noqa: E402
    build_tag_idf,
    dice,
    title_words,
)

SIBLING_THRESHOLD = 0.40
MIN_TAG_OVERLAP = 2
MIN_SOURCES = 20


def cross_centroid_score(ev_a, ev_b, tag_idf=None):
    """Score two events for cross-centroid similarity.

    Weights title 70% / tags 30% (vs 50/50 in saga chaining)
    because cross-centroid events share the same story but
    different tag perspectives.
    """
    tags_a = set(ev_a["tags"])
    tags_b = set(ev_b["tags"])
    shared = tags_a & tags_b
    tag_overlap = len(shared)

    if tag_idf and shared:
        weighted_shared = sum(tag_idf.get(t, 1.0) for t in shared)
        weighted_total = sum(tag_idf.get(t, 1.0) for t in tags_a) + sum(
            tag_idf.get(t, 1.0) for t in tags_b
        )
        tag_dice = 2 * weighted_shared / weighted_total if weighted_total else 0.0
    else:
        tag_dice = (
            2 * tag_overlap / (len(tags_a) + len(tags_b)) if (tags_a or tags_b) else 0.0
        )

    title_dice = dice(title_words(ev_a["title"]), title_words(ev_b["title"]))

    score = 0.3 * tag_dice + 0.7 * title_dice
    return score, tag_overlap


def get_db_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def fetch_events(conn, month=None, min_sources=MIN_SOURCES):
    """Fetch events with tags, grouped by centroid."""
    sql = """
        SELECT e.id, e.title, e.tags, e.source_batch_count,
               e.sibling_group, e.ctm_id, e.absorbed_centroids,
               ctm.centroid_id, cv.label as centroid_label,
               to_char(ctm.month, 'YYYY-MM') as month
        FROM events_v3 e
        JOIN ctm ON ctm.id = e.ctm_id
        JOIN centroids_v3 cv ON cv.id = ctm.centroid_id
        WHERE e.source_batch_count >= %s
          AND e.tags IS NOT NULL
          AND array_length(e.tags, 1) >= 2
          AND e.merged_into IS NULL
    """
    params = [min_sources]
    if month:
        sql += " AND to_char(ctm.month, 'YYYY-MM') = %s"
        params.append(month)
    sql += " ORDER BY ctm.centroid_id, e.source_batch_count DESC"

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def group_by_month(events):
    """Group events by month for comparison."""
    by_month = defaultdict(list)
    for ev in events:
        by_month[ev["month"]].append(ev)
    return by_month


def find_siblings(events_in_month, threshold=SIBLING_THRESHOLD):
    """Find cross-centroid sibling groups within a single month."""
    tag_idf = build_tag_idf(events_in_month)

    # Group by centroid
    by_centroid = defaultdict(list)
    for ev in events_in_month:
        by_centroid[ev["centroid_id"]].append(ev)

    centroid_ids = list(by_centroid.keys())
    if len(centroid_ids) < 2:
        return []

    # Compare events across different centroids
    matches = []
    for i, cid_a in enumerate(centroid_ids):
        for cid_b in centroid_ids[i + 1 :]:
            for ev_a in by_centroid[cid_a]:
                for ev_b in by_centroid[cid_b]:
                    score, tag_overlap = cross_centroid_score(ev_a, ev_b, tag_idf)
                    if score >= threshold and tag_overlap >= MIN_TAG_OVERLAP:
                        matches.append((ev_a, ev_b, score, tag_overlap))

    # Group by best match per centroid (no transitive chaining).
    # For each event, find its best cross-centroid match. Then build groups
    # where each centroid contributes at most one event (the best match).
    if not matches:
        return []

    # Sort by score descending -- greedily assign best pairs first
    matches.sort(key=lambda m: m[2], reverse=True)

    assigned = {}  # event_id -> group_id
    groups = defaultdict(dict)  # group_id -> {centroid_id: event}

    for ev_a, ev_b, score, _ in matches:
        id_a, id_b = str(ev_a["id"]), str(ev_b["id"])
        cid_a, cid_b = ev_a["centroid_id"], ev_b["centroid_id"]

        grp_a = assigned.get(id_a)
        grp_b = assigned.get(id_b)

        if grp_a and grp_b:
            # Both already assigned -- skip
            continue
        elif grp_a:
            # Add ev_b to ev_a's group if centroid slot is free
            if cid_b not in groups[grp_a]:
                groups[grp_a][cid_b] = ev_b
                assigned[id_b] = grp_a
        elif grp_b:
            # Add ev_a to ev_b's group if centroid slot is free
            if cid_a not in groups[grp_b]:
                groups[grp_b][cid_a] = ev_a
                assigned[id_a] = grp_b
        else:
            # New group
            gid = id_a
            groups[gid][cid_a] = ev_a
            groups[gid][cid_b] = ev_b
            assigned[id_a] = gid
            assigned[id_b] = gid

    result = []
    for gid, centroid_map in groups.items():
        if len(centroid_map) >= 2:
            result.append(list(centroid_map.values()))

    return result


def detect_and_assign(
    conn,
    month=None,
    min_sources=MIN_SOURCES,
    dry_run=False,
    threshold=SIBLING_THRESHOLD,
):
    """Main detection loop."""
    events = fetch_events(conn, month=month, min_sources=min_sources)
    print(f"Fetched {len(events)} events ({min_sources}+ sources)")

    by_month = group_by_month(events)
    total_groups = 0
    total_events = 0

    for m, month_events in sorted(by_month.items()):
        groups = find_siblings(month_events, threshold=threshold)
        if not groups:
            continue

        print(f"\n  {m}: {len(groups)} sibling group(s)")
        for group in groups:
            # Check if any already has a sibling_group
            existing_group = None
            for ev in group:
                if ev["sibling_group"]:
                    existing_group = ev["sibling_group"]
                    break

            group_id = existing_group or uuid.uuid4()
            centroids = sorted({ev["centroid_label"] for ev in group})
            sources = sum(ev["source_batch_count"] for ev in group)
            print(f"    Group {group_id}:")
            print(f"      Centroids: {', '.join(centroids)}")
            for ev in sorted(
                group, key=lambda e: e["source_batch_count"], reverse=True
            ):
                marker = "*" if ev["sibling_group"] else " "
                print(
                    f"     {marker} [{ev['centroid_label']:>15}] "
                    f"{ev['source_batch_count']:>4} src  {ev['title'][:70]}"
                )
            print(f"      Total sources: {sources}")

            if not dry_run:
                event_ids = [str(ev["id"]) for ev in group]
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE events_v3 SET sibling_group = %s::uuid WHERE id = ANY(%s::uuid[])",
                        [str(group_id), event_ids],
                    )
                conn.commit()

            total_groups += 1
            total_events += len(group)

    print(
        f"\n{'DRY RUN - ' if dry_run else ''}TOTAL: {total_groups} groups, {total_events} events"
    )
    return total_groups


def main():
    parser = argparse.ArgumentParser(description="Detect cross-centroid sibling events")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--month", help="Process single month (YYYY-MM)")
    parser.add_argument(
        "--min-sources", type=int, default=MIN_SOURCES, help="Min source count"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=SIBLING_THRESHOLD,
        help="Similarity threshold",
    )
    args = parser.parse_args()

    conn = get_db_connection()
    try:
        detect_and_assign(
            conn,
            month=args.month,
            min_sources=args.min_sources,
            dry_run=args.dry_run,
            threshold=args.threshold,
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
