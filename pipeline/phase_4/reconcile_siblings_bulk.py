"""Batched version of reconcile_siblings_v4 — does all merges in one
transaction per month using staging tables. Designed for high-latency
remote DBs (Render) where per-group round-trips become the bottleneck.

Same detection logic as reconcile_siblings_v4. Same end-state. Just
the write path is bulk instead of per-group.

Usage:
    python -m pipeline.phase_4.reconcile_siblings_bulk --month 2026-02
    python -m pipeline.phase_4.reconcile_siblings_bulk --month 2026-04 --dry-run
"""

import argparse
import io
import sys
from pathlib import Path

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.config import config  # noqa: E402
from pipeline.phase_4.reconcile_siblings_v4 import (  # noqa: E402
    DEFAULT_MIN_SOURCES,
    DEFAULT_THRESHOLD,
    fetch_events,
    find_cross_centroid_groups,
)


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def bulk_merge(conn, groups, month):
    """Apply all sibling-group merges in one transaction via staging table.
    Replicates merge_sibling_group semantics across the entire batch."""
    if not groups:
        print(f"[{month}] nothing to merge")
        return 0

    # Build staging rows: (absorbed_id, anchor_id, anchor_centroid_label, absorbed_centroid_label)
    staging_rows = []  # per absorbed event
    anchor_rows = []  # per anchor event (with merged set of absorbed centroid labels)

    for g in groups:
        # Prefer: highest source_count, then promoted over unpromoted, then stable by id.
        anchor = max(
            g,
            key=lambda e: (
                e["source_batch_count"],
                1 if e.get("is_promoted") else 0,
                str(e["id"]),
            ),
        )
        absorbed = [e for e in g if e["id"] != anchor["id"]]

        absorbed_labels = set()
        for a in absorbed:
            absorbed_labels.add(a["centroid_label"])
            if a.get("absorbed_centroids"):
                absorbed_labels.update(a["absorbed_centroids"])
        absorbed_labels.discard(anchor["centroid_label"])
        if anchor.get("absorbed_centroids"):
            absorbed_labels.update(anchor["absorbed_centroids"])

        for a in absorbed:
            staging_rows.append((str(a["id"]), str(anchor["id"])))
        anchor_rows.append((str(anchor["id"]), sorted(absorbed_labels)))

    total_absorbed = len(staging_rows)
    total_anchors = len(anchor_rows)
    print(
        f"[{month}] bulk: {len(groups)} groups -> "
        f"{total_anchors} anchors, {total_absorbed} absorbed"
    )

    with conn.cursor() as cur:
        # -----------------------------------------------------------------
        # Staging: temp table holding one row per absorbed event
        # -----------------------------------------------------------------
        cur.execute(
            """
            CREATE TEMP TABLE _sibling_merges (
                absorbed_id UUID PRIMARY KEY,
                anchor_id   UUID NOT NULL
            ) ON COMMIT DROP
        """
        )
        buf = io.StringIO()
        for aid, anc in staging_rows:
            buf.write(f"{aid}\t{anc}\n")
        buf.seek(0)
        cur.copy_expert(
            "COPY _sibling_merges (absorbed_id, anchor_id) FROM STDIN",
            buf,
        )

        # Anchor absorbed_centroids lookup
        cur.execute(
            """
            CREATE TEMP TABLE _sibling_anchors (
                anchor_id UUID PRIMARY KEY,
                labels    TEXT[] NOT NULL
            ) ON COMMIT DROP
        """
        )
        from psycopg2.extras import execute_values

        execute_values(
            cur,
            "INSERT INTO _sibling_anchors (anchor_id, labels) VALUES %s",
            anchor_rows,
            template="(%s::uuid, %s::text[])",
            page_size=1000,
        )

        # -----------------------------------------------------------------
        # 1) INSERT missing (anchor_id, title_id) rows via absorbed set.
        #    Using INSERT ... ON CONFLICT handles both "anchor already has
        #    this title" and "two absorbed events share a title" cleanly.
        # -----------------------------------------------------------------
        print(f"[{month}] step 1: inserting anchor title links...")
        cur.execute(
            """
            INSERT INTO event_v3_titles (event_id, title_id)
            SELECT DISTINCT m.anchor_id, ev.title_id
              FROM event_v3_titles ev
              JOIN _sibling_merges m ON m.absorbed_id = ev.event_id
             ON CONFLICT (event_id, title_id) DO NOTHING
        """
        )
        inserted = cur.rowcount
        print(f"[{month}]   inserted {inserted} new anchor title links")

        # -----------------------------------------------------------------
        # 2) Delete all event_v3_titles on absorbed events
        # -----------------------------------------------------------------
        cur.execute(
            """
            DELETE FROM event_v3_titles ev
             USING _sibling_merges m
             WHERE ev.event_id = m.absorbed_id
        """
        )
        deleted_links = cur.rowcount
        print(f"[{month}]   deleted {deleted_links} absorbed title links")

        # -----------------------------------------------------------------
        # 3) Set merged_into on absorbed events
        # -----------------------------------------------------------------
        print(f"[{month}] step 2: setting merged_into on absorbed...")
        cur.execute(
            """
            UPDATE events_v3 e
               SET merged_into = m.anchor_id
              FROM _sibling_merges m
             WHERE e.id = m.absorbed_id
        """
        )
        print(f"[{month}]   set merged_into on {cur.rowcount} events")

        # -----------------------------------------------------------------
        # 4) Set absorbed_centroids on anchors
        # -----------------------------------------------------------------
        print(f"[{month}] step 3: setting absorbed_centroids on anchors...")
        cur.execute(
            """
            UPDATE events_v3 e
               SET absorbed_centroids = a.labels
              FROM _sibling_anchors a
             WHERE e.id = a.anchor_id
        """
        )
        print(f"[{month}]   set absorbed_centroids on {cur.rowcount} anchors")

        # -----------------------------------------------------------------
        # 5) Recompute source_batch_count on anchors
        # -----------------------------------------------------------------
        print(f"[{month}] step 4: recomputing source_batch_count on anchors...")
        cur.execute(
            """
            UPDATE events_v3 e
               SET source_batch_count = sub.cnt
              FROM (
                SELECT a.anchor_id, COUNT(*)::int AS cnt
                  FROM _sibling_anchors a
                  JOIN event_v3_titles ev ON ev.event_id = a.anchor_id
                 GROUP BY a.anchor_id
              ) sub
             WHERE e.id = sub.anchor_id
        """
        )
        print(f"[{month}]   recomputed source_batch_count on {cur.rowcount} anchors")

        # -----------------------------------------------------------------
        # 6) Invalidate stale analyses (both absorbed + anchors, same as
        #    merge_sibling_group does per-group).
        # -----------------------------------------------------------------
        print(
            f"[{month}] step 5: invalidating stale entity_analyses + stance narratives..."
        )
        cur.execute(
            """
            DELETE FROM entity_analyses
             WHERE entity_type = 'event'
               AND (entity_id IN (SELECT absorbed_id FROM _sibling_merges)
                 OR entity_id IN (SELECT anchor_id FROM _sibling_anchors))
        """
        )
        del_analyses = cur.rowcount
        cur.execute(
            """
            DELETE FROM narratives
             WHERE entity_type = 'event'
               AND extraction_method = 'stance_clustered'
               AND (entity_id IN (SELECT absorbed_id FROM _sibling_merges)
                 OR entity_id IN (SELECT anchor_id FROM _sibling_anchors))
        """
        )
        del_narratives = cur.rowcount
        print(
            f"[{month}]   deleted {del_analyses} analyses, {del_narratives} narratives"
        )

    conn.commit()
    print(f"[{month}] committed.")
    return total_absorbed


def refresh_mv_event_triples(conn, month):
    from pipeline.phase_4.materialize_event_triples import _materialize_month

    with conn.cursor() as cur:
        _materialize_month(cur, month)
    conn.commit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True, help="YYYY-MM")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--min-sources", type=int, default=DEFAULT_MIN_SOURCES)
    ap.add_argument("--no-mv-refresh", action="store_true")
    ap.add_argument(
        "--all-events",
        action="store_true",
        help="Include non-promoted events (backfill mode)",
    )
    args = ap.parse_args()

    conn = get_connection()
    conn.autocommit = False
    try:
        events = fetch_events(
            conn,
            args.month,
            min_sources=args.min_sources,
            promoted_only=not args.all_events,
        )
        print(
            f"[{args.month}] fetched {len(events)} promoted events "
            f"(>= {args.min_sources} src)",
            flush=True,
        )

        groups = find_cross_centroid_groups(events, threshold=args.threshold)
        print(
            f"[{args.month}] detected {len(groups)} sibling groups "
            f"at threshold {args.threshold}",
            flush=True,
        )

        if args.dry_run:
            absorbable = sum(len(g) - 1 for g in groups)
            print(f"[{args.month}] [DRY RUN] would absorb {absorbable} events")
            return

        total = bulk_merge(conn, groups, args.month)
        print(f"[{args.month}] {total} events merged via bulk")

        if not args.no_mv_refresh and total > 0:
            print(f"[{args.month}] refreshing mv_event_triples...")
            refresh_mv_event_triples(conn, args.month)
            print(f"[{args.month}] mv_event_triples refreshed.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
