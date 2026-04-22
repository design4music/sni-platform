"""One-shot repair: swap anchors in sibling groups where the canonical
(merged_into IS NULL) is non-promoted but at least one absorbed member
is promoted. Caused by a tiebreak bug in the initial reconciler pass.

Promoted events should be canonical because they are what the rest of
the frontend (centroid pages, track pages, calendar) actually shows.

Usage:
    python -m pipeline.phase_4.fix_bad_anchors --month 2026-04 --dry-run
    python -m pipeline.phase_4.fix_bad_anchors --all-months
"""

import argparse
import io
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.config import config  # noqa: E402


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def find_swaps(conn, month):
    """For each bad group, return (old_anchor_id, new_anchor_id,
    old_anchor_centroid_label, new_anchor_centroid_label)."""
    sql = """
        WITH bad AS (
            SELECT a.id AS old_anchor, cv_a.label AS old_label
            FROM events_v3 a
            JOIN ctm c_a ON c_a.id = a.ctm_id
            JOIN centroids_v3 cv_a ON cv_a.id = c_a.centroid_id
            WHERE a.merged_into IS NULL
              AND NOT a.is_promoted
              AND to_char(a.date, 'YYYY-MM') = %s
              AND EXISTS (
                SELECT 1 FROM events_v3 e
                WHERE e.merged_into = a.id AND e.is_promoted
              )
        ),
        picks AS (
            SELECT b.old_anchor, b.old_label,
                   (SELECT e.id FROM events_v3 e
                     WHERE e.merged_into = b.old_anchor AND e.is_promoted
                     ORDER BY e.source_batch_count DESC, e.id ASC
                     LIMIT 1) AS new_anchor
            FROM bad b
        )
        SELECT p.old_anchor::text, p.old_label,
               p.new_anchor::text, cv_n.label AS new_label
          FROM picks p
          JOIN events_v3 e_n ON e_n.id = p.new_anchor
          JOIN ctm c_n ON c_n.id = e_n.ctm_id
          JOIN centroids_v3 cv_n ON cv_n.id = c_n.centroid_id
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, (month,))
        return cur.fetchall()


def bulk_swap(conn, swaps, month):
    if not swaps:
        print(f"[{month}] no bad anchors to swap")
        return 0

    print(f"[{month}] bulk-swapping {len(swaps)} groups...")
    with conn.cursor() as cur:
        # Staging table: one row per swap.
        cur.execute(
            """
            CREATE TEMP TABLE _anchor_swaps (
                old_anchor UUID PRIMARY KEY,
                new_anchor UUID NOT NULL,
                old_label  TEXT NOT NULL,
                new_label  TEXT NOT NULL
            ) ON COMMIT DROP
        """
        )
        buf = io.StringIO()
        for s in swaps:
            buf.write(
                f"{s['old_anchor']}\t{s['new_anchor']}\t{s['old_label']}\t{s['new_label']}\n"
            )
        buf.seek(0)
        cur.copy_expert(
            "COPY _anchor_swaps (old_anchor, new_anchor, old_label, new_label) FROM STDIN",
            buf,
        )

        # 1) Move event_v3_titles from old_anchor -> new_anchor
        print(f"[{month}] step 1: moving title links old->new...")
        cur.execute(
            """
            INSERT INTO event_v3_titles (event_id, title_id)
            SELECT DISTINCT s.new_anchor, ev.title_id
              FROM event_v3_titles ev
              JOIN _anchor_swaps s ON s.old_anchor = ev.event_id
             ON CONFLICT (event_id, title_id) DO NOTHING
        """
        )
        print(f"[{month}]   inserted {cur.rowcount}")
        cur.execute(
            """
            DELETE FROM event_v3_titles ev
             USING _anchor_swaps s
             WHERE ev.event_id = s.old_anchor
        """
        )
        print(f"[{month}]   deleted {cur.rowcount} from old anchors")

        # 2) Flip merged_into on new anchors (NULL), old anchors (-> new)
        print(f"[{month}] step 2: flipping merged_into...")
        cur.execute(
            """
            UPDATE events_v3 e
               SET merged_into = NULL,
                   absorbed_centroids = NULL  -- overwritten in step 3
              FROM _anchor_swaps s
             WHERE e.id = s.new_anchor
        """
        )
        cur.execute(
            """
            UPDATE events_v3 e
               SET merged_into = s.new_anchor
              FROM _anchor_swaps s
             WHERE e.id = s.old_anchor
        """
        )

        # 3) Re-point other absorbed events from old_anchor -> new_anchor
        print(f"[{month}] step 3: re-pointing siblings...")
        cur.execute(
            """
            UPDATE events_v3 e
               SET merged_into = s.new_anchor
              FROM _anchor_swaps s
             WHERE e.merged_into = s.old_anchor
               AND e.id <> s.new_anchor
        """
        )
        print(f"[{month}]   re-pointed {cur.rowcount} siblings")

        # 4) Rebuild absorbed_centroids on new anchors:
        #    union of: old_anchor's label + all sibling labels + anything
        #    old_anchor had in its absorbed_centroids, minus new_anchor's label.
        print(f"[{month}] step 4: rebuilding absorbed_centroids...")
        cur.execute(
            """
            UPDATE events_v3 e
               SET absorbed_centroids = sub.labels
              FROM (
                SELECT s.new_anchor AS anchor_id,
                       ARRAY(
                         SELECT DISTINCT label
                           FROM (
                             -- old anchor's label
                             SELECT s.old_label AS label
                             UNION ALL
                             -- siblings' centroid labels (merged into new)
                             SELECT cv.label
                               FROM events_v3 sib
                               JOIN ctm c ON c.id = sib.ctm_id
                               JOIN centroids_v3 cv ON cv.id = c.centroid_id
                              WHERE sib.merged_into = s.new_anchor
                                AND sib.id <> s.old_anchor
                             UNION ALL
                             -- old anchor's prior absorbed_centroids
                             SELECT unnest(COALESCE(oa.absorbed_centroids, '{}'::text[]))
                               FROM events_v3 oa
                              WHERE oa.id = s.old_anchor
                           ) t
                          WHERE label IS NOT NULL
                            AND label <> s.new_label
                          ORDER BY label
                       ) AS labels
                  FROM _anchor_swaps s
              ) sub
             WHERE e.id = sub.anchor_id
        """
        )

        # 5) Clear absorbed_centroids on the now-absorbed old anchors
        cur.execute(
            """
            UPDATE events_v3 e
               SET absorbed_centroids = NULL
              FROM _anchor_swaps s
             WHERE e.id = s.old_anchor
        """
        )

        # 6) Recompute source_batch_count on new anchors (and old, now absorbed)
        print(f"[{month}] step 5: recomputing source_batch_count...")
        cur.execute(
            """
            UPDATE events_v3 e
               SET source_batch_count = COALESCE(sub.cnt, 0)
              FROM (
                SELECT s.new_anchor AS eid, COUNT(*)::int AS cnt
                  FROM _anchor_swaps s
                  LEFT JOIN event_v3_titles ev ON ev.event_id = s.new_anchor
                 GROUP BY s.new_anchor
              ) sub
             WHERE e.id = sub.eid
        """
        )
        cur.execute(
            """
            UPDATE events_v3 e
               SET source_batch_count = COALESCE(sub.cnt, 0)
              FROM (
                SELECT s.old_anchor AS eid, COUNT(*)::int AS cnt
                  FROM _anchor_swaps s
                  LEFT JOIN event_v3_titles ev ON ev.event_id = s.old_anchor
                 GROUP BY s.old_anchor
              ) sub
             WHERE e.id = sub.eid
        """
        )

    conn.commit()
    print(f"[{month}] committed.")
    return len(swaps)


def refresh_mv(conn, month):
    from pipeline.phase_4.materialize_event_triples import _materialize_month

    with conn.cursor() as cur:
        _materialize_month(cur, month)
    conn.commit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month")
    ap.add_argument("--all-months", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-mv-refresh", action="store_true")
    args = ap.parse_args()

    if not (args.month or args.all_months):
        ap.error("pass --month YYYY-MM or --all-months")

    conn = get_conn()
    try:
        if args.all_months:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT to_char(month, 'YYYY-MM')
                      FROM ctm ORDER BY 1
                """
                )
                months = [r[0] for r in cur.fetchall()]
        else:
            months = [args.month]

        for m in months:
            swaps = find_swaps(conn, m)
            print(f"[{m}] found {len(swaps)} bad-anchor groups")
            if args.dry_run:
                for s in swaps[:5]:
                    print(
                        f"  example: {s['old_label']} ({s['old_anchor'][:8]}) "
                        f"<- should be -> {s['new_label']} ({s['new_anchor'][:8]})"
                    )
                continue

            n = bulk_swap(conn, swaps, m)
            if not args.no_mv_refresh and n > 0:
                print(f"[{m}] refreshing mv_event_triples...")
                refresh_mv(conn, m)
                print(f"[{m}] mv_event_triples refreshed.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
