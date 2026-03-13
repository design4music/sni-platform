"""
Phase 4.4: Cross-Centroid Sibling Event Merging

Detects events about the same story across different centroids and merges them
using the existing merged_into soft-delete pattern. The anchor event absorbs
titles from siblings, gains absorbed_centroids metadata, and siblings become
invisible (merged_into IS NOT NULL).

Usage:
    python -m pipeline.phase_4.merge_sibling_events --dry-run
    python -m pipeline.phase_4.merge_sibling_events --month 2026-03
    python -m pipeline.phase_4.merge_sibling_events --month 2026-03 --dry-run
"""

import argparse
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import config  # noqa: E402
from pipeline.phase_4.detect_cross_centroid_siblings import (  # noqa: E402
    MIN_SOURCES,
    SIBLING_THRESHOLD,
    fetch_events,
    find_siblings,
    group_by_month,
)


def get_connection():
    import psycopg2

    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def merge_sibling_group(conn, group):
    """Merge a detected sibling group. group = list of event dicts."""
    anchor = max(group, key=lambda e: e["source_batch_count"])
    absorbed = [e for e in group if e["id"] != anchor["id"]]
    absorbed_ids = [str(e["id"]) for e in absorbed]

    # Collect centroid names: from absorbed events + any they previously absorbed
    absorbed_centroids = set()
    for e in absorbed:
        absorbed_centroids.add(e["centroid_label"])
        # If absorbed event was itself an anchor with absorbed_centroids, inherit them
        if e.get("absorbed_centroids"):
            absorbed_centroids.update(e["absorbed_centroids"])
    # Don't include anchor's own centroid
    absorbed_centroids.discard(anchor["centroid_label"])
    # Also keep any existing absorbed_centroids on the anchor
    if anchor.get("absorbed_centroids"):
        absorbed_centroids.update(anchor["absorbed_centroids"])
    absorbed_centroids = sorted(absorbed_centroids)

    with conn.cursor() as cur:
        # Re-link titles (avoid duplicates)
        for aid in absorbed_ids:
            cur.execute(
                """UPDATE event_v3_titles SET event_id = %s
                   WHERE event_id = %s::uuid
                   AND title_id NOT IN (
                       SELECT title_id FROM event_v3_titles WHERE event_id = %s
                   )""",
                (str(anchor["id"]), aid, str(anchor["id"])),
            )
            cur.execute(
                "DELETE FROM event_v3_titles WHERE event_id = %s::uuid",
                (aid,),
            )

        # Soft-delete absorbed events
        cur.execute(
            "UPDATE events_v3 SET merged_into = %s WHERE id = ANY(%s::uuid[])",
            (str(anchor["id"]), absorbed_ids),
        )

        # Store absorbed centroid names on anchor
        cur.execute(
            "UPDATE events_v3 SET absorbed_centroids = %s WHERE id = %s",
            (absorbed_centroids, str(anchor["id"])),
        )

        # Recalc source_batch_count
        cur.execute(
            "UPDATE events_v3 SET source_batch_count = "
            "(SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s) "
            "WHERE id = %s",
            (str(anchor["id"]), str(anchor["id"])),
        )

        # Invalidate stale analyses for absorbed events
        cur.execute(
            "DELETE FROM entity_analyses WHERE entity_type = 'event' AND entity_id = ANY(%s::uuid[])",
            (absorbed_ids,),
        )
        cur.execute(
            "DELETE FROM narratives WHERE entity_type = 'event' AND entity_id = ANY(%s::uuid[]) "
            "AND extraction_method = 'stance_clustered'",
            (absorbed_ids,),
        )
        # Invalidate anchor analysis too (source data changed)
        cur.execute(
            "DELETE FROM entity_analyses WHERE entity_type = 'event' AND entity_id = %s",
            (str(anchor["id"]),),
        )
        cur.execute(
            "DELETE FROM narratives WHERE entity_type = 'event' AND entity_id = %s "
            "AND extraction_method = 'stance_clustered'",
            (str(anchor["id"]),),
        )

    conn.commit()
    return str(anchor["id"]), len(absorbed)


def merge_siblings_for_month(
    conn, month_events, dry_run=False, threshold=SIBLING_THRESHOLD
):
    """Detect and merge sibling events for a list of events in one month."""
    groups = find_siblings(month_events, threshold)
    # Filter: only groups where no event is already merged
    groups = [g for g in groups if all(e.get("merged_into") is None for e in g)]

    total_merged = 0
    for group in groups:
        anchor = max(group, key=lambda e: e["source_batch_count"])
        absorbed = [e for e in group if e["id"] != anchor["id"]]
        centroids = sorted({e["centroid_label"] for e in group})

        print("  Group: {}".format(", ".join(centroids)))
        print(
            "    Anchor: [{}] {} ({} src)".format(
                anchor["centroid_label"],
                str(anchor["title"])[:60],
                anchor["source_batch_count"],
            )
        )
        for a in absorbed:
            print(
                "    <- [{}] {} ({} src)".format(
                    a["centroid_label"], str(a["title"])[:60], a["source_batch_count"]
                )
            )

        if dry_run:
            total_merged += len(absorbed)
            continue

        anchor_id, count = merge_sibling_group(conn, group)
        total_merged += count

    return {"groups": len(groups), "merged": total_merged}


def run_sibling_merge(
    conn=None,
    month=None,
    dry_run=False,
    min_sources=MIN_SOURCES,
    threshold=SIBLING_THRESHOLD,
    max_months=None,
):
    """Main entry point. Detects and merges cross-centroid siblings."""
    own_conn = conn is None
    if own_conn:
        conn = get_connection()

    try:
        total_groups = 0
        total_merged = 0
        pass_num = 0

        while True:
            pass_num += 1
            events = fetch_events(conn, month=month, min_sources=min_sources)
            if pass_num == 1:
                print(
                    "Phase 4.4: {} events ({} + sources)".format(
                        len(events), min_sources
                    )
                )

            by_month = group_by_month(events)
            months = sorted(by_month.keys(), reverse=True)
            if max_months:
                months = months[:max_months]

            pass_merged = 0
            for m in months:
                month_events = by_month[m]
                result = merge_siblings_for_month(
                    conn, month_events, dry_run=dry_run, threshold=threshold
                )
                if result["groups"] > 0:
                    print(
                        "  {}: {} groups, {} merged".format(
                            m, result["groups"], result["merged"]
                        )
                    )
                total_groups += result["groups"]
                total_merged += result["merged"]
                pass_merged += result["merged"]

            # Stop if no merges happened this pass (or dry-run)
            if pass_merged == 0 or dry_run:
                break
            print(
                "  Pass {}: merged {} -- re-scanning...".format(pass_num, pass_merged)
            )

        prefix = "DRY RUN - " if dry_run else ""
        print(
            "Phase 4.4: {}{} groups, {} events merged".format(
                prefix, total_groups, total_merged
            )
        )
        return total_merged
    finally:
        if own_conn:
            conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Phase 4.4: Cross-Centroid Sibling Merge"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--month", help="Process single month (YYYY-MM)")
    parser.add_argument("--min-sources", type=int, default=MIN_SOURCES)
    parser.add_argument("--threshold", type=float, default=SIBLING_THRESHOLD)
    args = parser.parse_args()

    run_sibling_merge(
        month=args.month,
        dry_run=args.dry_run,
        min_sources=args.min_sources,
        threshold=args.threshold,
    )


if __name__ == "__main__":
    main()
