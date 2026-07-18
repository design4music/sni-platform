"""
Show title-level data for the top epic (by total_sources) in a given month.

Joins: epic_events -> events_v3 -> event_v3_titles -> titles_v3
       events_v3 -> ctm (for centroid_id)

Usage:
    python -m scripts.epic_title_sample               # default 2026-01
    python -m scripts.epic_title_sample --month 2025-12
"""

import argparse
import sys

import psycopg2

from core.config import config

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def safe_str(s):
    """Return ASCII-safe version of a string."""
    if not s:
        return ""
    return s.encode("ascii", errors="replace").decode("ascii")


def main():
    parser = argparse.ArgumentParser(description="Epic title-level sample")
    parser.add_argument("--month", default="2026-01", help="Month (YYYY-MM)")
    parser.add_argument("--limit", type=int, default=20, help="Sample size")
    args = parser.parse_args()

    month_date = args.month + "-01"
    conn = get_connection()
    cur = conn.cursor()

    # Step 1: pick top epic by total_sources
    cur.execute(
        """
        SELECT id, slug, title, total_sources, event_count, centroid_count
        FROM epics
        WHERE month = %s
        ORDER BY total_sources DESC
        LIMIT 1
        """,
        (month_date,),
    )
    epic = cur.fetchone()
    if not epic:
        print("No epics found for month %s" % args.month)
        conn.close()
        return

    epic_id, slug, epic_title, total_sources, event_count, centroid_count = epic

    print("=" * 90)
    print("TOP EPIC: %s" % safe_str(epic_title))
    print(
        "Slug: %s  |  Events: %d  |  Centroids: %d  |  Total sources: %d"
        % (slug, event_count, centroid_count, total_sources)
    )
    print("=" * 90)
    print()

    # Step 2: count total titles for this epic
    cur.execute(
        """
        SELECT COUNT(DISTINCT t.id)
        FROM epic_events ee
        JOIN events_v3 e ON ee.event_id = e.id
        JOIN event_v3_titles evt ON evt.event_id = e.id
        JOIN titles_v3 t ON t.id = evt.title_id
        WHERE ee.epic_id = %s
        """,
        (epic_id,),
    )
    total_titles = cur.fetchone()[0]
    print("Total distinct titles in this epic: %d" % total_titles)
    print()

    # Step 3: sample titles with publisher and centroid
    cur.execute(
        """
        SELECT
            t.title_display,
            t.publisher_name,
            c.centroid_id,
            e.source_batch_count,
            t.pubdate_utc::date AS pub_date
        FROM epic_events ee
        JOIN events_v3 e ON ee.event_id = e.id
        JOIN ctm c ON e.ctm_id = c.id
        JOIN event_v3_titles evt ON evt.event_id = e.id
        JOIN titles_v3 t ON t.id = evt.title_id
        WHERE ee.epic_id = %s
        ORDER BY e.source_batch_count DESC, t.pubdate_utc DESC
        LIMIT %s
        """,
        (epic_id, args.limit),
    )

    rows = cur.fetchall()

    print("Sample of %d titles (ordered by event source count):" % len(rows))
    print("-" * 90)
    fmt = "%-3s %-80s %-25s %-22s %s"
    print(fmt % ("#", "TITLE", "PUBLISHER", "CENTROID", "DATE"))
    print("-" * 90)

    for i, (title_text, publisher, centroid_id, src_count, pub_date) in enumerate(
        rows, 1
    ):
        raw = safe_str(title_text) if title_text else "(no title)"
        trunc = (raw[:77] + "...") if len(raw) > 80 else raw
        pub = safe_str(publisher)[:25] if publisher else "(unknown)"
        cid = (centroid_id or "?")[:22]
        dt = str(pub_date) if pub_date else "?"
        print(fmt % (i, trunc, pub, cid, dt))

    print("-" * 90)
    conn.close()


if __name__ == "__main__":
    main()
