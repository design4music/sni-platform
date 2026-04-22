"""Cross-centroid sibling reconciliation for v4.0 day-centric events.

Adapts the legacy tag-based detector to v4 where `events_v3.tags` is empty:
scores pairs by title-word Dice only, partitions by date (not month), and
calls merge_sibling_events.merge_sibling_group for the actual write.

Usage:
    python -m pipeline.phase_4.reconcile_siblings_v4 --month 2026-01 --dry-run
    python -m pipeline.phase_4.reconcile_siblings_v4 --month 2026-01
    python -m pipeline.phase_4.reconcile_siblings_v4 --all-months
    python -m pipeline.phase_4.reconcile_siblings_v4 --month 2026-01 --threshold 0.55
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.config import config  # noqa: E402
from pipeline.phase_4.chain_event_sagas import dice, title_words  # noqa: E402
from pipeline.phase_4.merge_sibling_events import merge_sibling_group  # noqa: E402

DEFAULT_THRESHOLD = 0.55
DEFAULT_MIN_SOURCES = 1


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def fetch_events(conn, month, min_sources=DEFAULT_MIN_SOURCES, promoted_only=True):
    """Fetch unmerged events for a month with fields needed by
    merge_sibling_group. No tags requirement (v4 writes empty tags).
    When promoted_only=False, includes non-promoted events (backfill mode)."""
    promoted_clause = "AND e.is_promoted" if promoted_only else ""
    sql = f"""
        SELECT e.id, e.title, e.date, e.source_batch_count,
               e.sibling_group, e.ctm_id, e.absorbed_centroids,
               e.merged_into, e.is_promoted,
               ctm.centroid_id,
               cv.label AS centroid_label,
               to_char(e.date, 'YYYY-MM') AS month
        FROM events_v3 e
        JOIN ctm ON ctm.id = e.ctm_id
        JOIN centroids_v3 cv ON cv.id = ctm.centroid_id
        WHERE e.merged_into IS NULL
          AND e.title IS NOT NULL
          AND e.is_catchall = false
          AND e.source_batch_count >= %s
          AND to_char(e.date, 'YYYY-MM') = %s
          {promoted_clause}
        ORDER BY e.date, ctm.centroid_id
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, (min_sources, month))
        return cur.fetchall()


def find_cross_centroid_groups(events, threshold):
    """Partition by date, score cross-centroid pairs by title Dice,
    greedy-assemble groups with at most one event per centroid."""
    by_date = defaultdict(list)
    for e in events:
        by_date[e["date"]].append(e)
        e["_words"] = title_words(e["title"])

    pairs = []
    for date, lst in by_date.items():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                a, b = lst[i], lst[j]
                if a["centroid_id"] == b["centroid_id"]:
                    continue
                score = dice(a["_words"], b["_words"])
                if score >= threshold:
                    pairs.append((a, b, score))

    pairs.sort(key=lambda p: p[2], reverse=True)

    assigned = {}
    groups = {}
    for a, b, score in pairs:
        id_a, id_b = str(a["id"]), str(b["id"])
        cid_a, cid_b = a["centroid_id"], b["centroid_id"]
        grp_a = assigned.get(id_a)
        grp_b = assigned.get(id_b)
        if grp_a and grp_b:
            continue
        elif grp_a:
            if cid_b not in groups[grp_a]:
                groups[grp_a][cid_b] = b
                assigned[id_b] = grp_a
        elif grp_b:
            if cid_a not in groups[grp_b]:
                groups[grp_b][cid_a] = a
                assigned[id_a] = grp_b
        else:
            gid = id_a
            groups[gid] = {cid_a: a, cid_b: b}
            assigned[id_a] = gid
            assigned[id_b] = gid

    return [list(g.values()) for g in groups.values() if len(g) >= 2]


def run_for_month(conn, month, dry_run, threshold, min_sources, verbose=True):
    """Detect siblings for a month, merge (or dry-run-log) each group."""
    events = fetch_events(conn, month, min_sources=min_sources)
    if verbose:
        print(f"[{month}] fetched {len(events)} promoted events (>= {min_sources} src)")

    groups = find_cross_centroid_groups(events, threshold=threshold)
    if verbose:
        print(f"[{month}] found {len(groups)} sibling groups at threshold {threshold}")

    total_merged = 0
    for gi, group in enumerate(groups):
        anchor = max(group, key=lambda e: e["source_batch_count"])
        absorbed = [e for e in group if e["id"] != anchor["id"]]

        if verbose and (gi < 10 or gi % 500 == 0):
            centroids = sorted({e["centroid_label"] for e in group})
            print(f"  [{gi:4d}] {anchor['date']} | {', '.join(centroids)}")
            print(
                f"       anchor: [{anchor['centroid_label']}] "
                f"({anchor['source_batch_count']} src) "
                f"{str(anchor['title'])[:90]}"
            )
            for a in absorbed:
                print(
                    f"       <-     [{a['centroid_label']}] "
                    f"({a['source_batch_count']} src) "
                    f"{str(a['title'])[:90]}"
                )

        if dry_run:
            total_merged += len(absorbed)
            continue

        _, count = merge_sibling_group(conn, group)
        total_merged += count

    prefix = "[DRY RUN] " if dry_run else ""
    print(f"{prefix}[{month}] {len(groups)} groups, {total_merged} events merged")
    return len(groups), total_merged


def refresh_mv_event_triples(conn, month):
    """Delete + reinsert mv_event_triples rows for the given month.
    Skips events with merged_into set (via events_v3 filter - rows are still
    there but won't match on next query due to soft-delete pattern)."""
    from pipeline.phase_4.materialize_event_triples import _materialize_month

    with conn.cursor() as cur:
        _materialize_month(cur, month)
    conn.commit()


def main():
    ap = argparse.ArgumentParser(
        description="Reconcile cross-centroid sibling events (v4)"
    )
    ap.add_argument("--month", help="Single month (YYYY-MM)")
    ap.add_argument(
        "--all-months", action="store_true", help="Run for every month present in ctm"
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--min-sources", type=int, default=DEFAULT_MIN_SOURCES)
    ap.add_argument(
        "--no-mv-refresh",
        action="store_true",
        help="Skip mv_event_triples refresh after merge",
    )
    args = ap.parse_args()

    if not args.month and not args.all_months:
        ap.error("Pass --month YYYY-MM or --all-months")

    conn = get_connection()
    try:
        if args.all_months:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT DISTINCT to_char(month, 'YYYY-MM') FROM ctm ORDER BY 1"
                )
                months = [r[0] for r in cur.fetchall()]
        else:
            months = [args.month]

        for m in months:
            groups, merged = run_for_month(
                conn,
                m,
                dry_run=args.dry_run,
                threshold=args.threshold,
                min_sources=args.min_sources,
            )
            if not args.dry_run and merged > 0 and not args.no_mv_refresh:
                print(f"[{m}] refreshing mv_event_triples...")
                refresh_mv_event_triples(conn, m)
                print(f"[{m}] mv_event_triples refreshed")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
