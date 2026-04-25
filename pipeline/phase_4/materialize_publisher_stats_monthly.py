"""Materialize per-(outlet, month) publisher analytics into
mv_publisher_stats_monthly.

Mirrors materialize_publisher_stats.py but restricts the title window to
a single calendar month. Drops dow_distribution / peak_hour (kept
aggregate-only) and narrative_frame_count (retired in D-071).

Usage:
    python -m pipeline.phase_4.materialize_publisher_stats_monthly --month 2026-03
    python -m pipeline.phase_4.materialize_publisher_stats_monthly --month 2026-03 --feed Lenta.ru
    python -m pipeline.phase_4.materialize_publisher_stats_monthly --backfill 2026-01,2026-02,2026-03,2026-04
"""

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from pipeline.phase_4.materialize_publisher_stats import (  # noqa: E402
    _gini,
    _herfindahl,
    _load_publisher_map,
    _top_n,
    get_connection,
)

MIN_TITLES_FOR_MONTH = 10


def _month_bounds(month: str) -> tuple[str, str]:
    """'2026-03' -> ('2026-03-01', '2026-04-01')."""
    y, m = month.split("-")
    y, m = int(y), int(m)
    if m == 12:
        ny, nm = y + 1, 1
    else:
        ny, nm = y, m + 1
    return ("%04d-%02d-01" % (y, m), "%04d-%02d-01" % (ny, nm))


def _compute_monthly_stats(cur, feed_name, month, publisher_map):
    """Compute per-month analytics for a single feed. Returns stats dict or None."""
    variants = publisher_map.get(feed_name, [])
    pub_names = [feed_name] + variants
    placeholders = ",".join(["%s"] * len(pub_names))
    start, end = _month_bounds(month)

    cur.execute(
        f"""
        SELECT t.publisher_name, t.detected_language, t.pubdate_utc,
               ta.centroid_id, ta.track,
               tl.actor, tl.action_class, tl.domain,
               tl.persons, tl.orgs, tl.places
        FROM titles_v3 t
        JOIN title_assignments ta ON ta.title_id = t.id
        LEFT JOIN title_labels tl ON tl.title_id = t.id
        WHERE t.publisher_name IN ({placeholders})
          AND t.pubdate_utc >= %s::date
          AND t.pubdate_utc <  %s::date
        """,
        pub_names + [start, end],
    )
    rows = cur.fetchall()
    if len(rows) < MIN_TITLES_FOR_MONTH:
        return None

    title_count = len(rows)

    # Track distribution
    track_counter = Counter(r["track"] for r in rows if r["track"])
    track_total = sum(track_counter.values())
    track_distribution = (
        {t: round(c / track_total, 3) for t, c in track_counter.most_common()}
        if track_total
        else {}
    )

    # Geographic focus
    centroid_counter = Counter(r["centroid_id"] for r in rows if r["centroid_id"])
    geo_hhi = _herfindahl(centroid_counter)
    geo_gini = _gini(list(centroid_counter.values()))
    top_centroids = _top_n(centroid_counter, 10)

    # Actors
    actor_counter = Counter(r["actor"] for r in rows if r["actor"])
    top_actors = _top_n(actor_counter, 10)

    # Action class distribution
    action_counter = Counter(r["action_class"] for r in rows if r["action_class"])
    action_total = sum(action_counter.values())
    action_distribution = (
        {a: round(c / action_total, 3) for a, c in action_counter.most_common()}
        if action_total
        else {}
    )

    # Domain distribution
    domain_counter = Counter(r["domain"] for r in rows if r["domain"])
    domain_total = sum(domain_counter.values())
    domain_distribution = (
        {d: round(c / domain_total, 3) for d, c in domain_counter.most_common()}
        if domain_total
        else {}
    )

    # Language distribution
    lang_counter = Counter(
        r["detected_language"] for r in rows if r["detected_language"]
    )
    lang_total = sum(lang_counter.values())
    language_distribution = (
        {la: round(c / lang_total, 3) for la, c in lang_counter.most_common(5)}
        if lang_total
        else {}
    )

    # Signal richness: avg persons/orgs/places per title
    person_counts = [len(r["persons"] or []) for r in rows]
    org_counts = [len(r["orgs"] or []) for r in rows]
    place_counts = [len(r["places"] or []) for r in rows]
    signal_richness = round(
        (sum(person_counts) + sum(org_counts) + sum(place_counts)) / title_count, 2
    )

    return {
        "title_count": title_count,
        "centroid_count": len(centroid_counter),
        "track_distribution": track_distribution,
        "geo_hhi": geo_hhi,
        "geo_gini": geo_gini,
        "top_centroids": top_centroids,
        "top_actors": top_actors,
        "action_distribution": action_distribution,
        "domain_distribution": domain_distribution,
        "language_distribution": language_distribution,
        "signal_richness": signal_richness,
    }


def materialize_month(month, feed_name=None):
    """Compute and upsert publisher stats for a given month."""
    start, _ = _month_bounds(month)
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            publisher_map = _load_publisher_map(cur)
            if feed_name:
                feeds = [{"name": feed_name}]
            else:
                cur.execute(
                    "SELECT name FROM feeds WHERE is_active = true ORDER BY name"
                )
                feeds = cur.fetchall()
            print("Month %s: processing %d feeds" % (month, len(feeds)), flush=True)
            written = 0
            skipped = 0
            for f in feeds:
                name = f["name"]
                stats = _compute_monthly_stats(cur, name, month, publisher_map)
                if stats is None:
                    skipped += 1
                    continue
                cur.execute(
                    """
                    INSERT INTO mv_publisher_stats_monthly (feed_name, month, stats, updated_at)
                    VALUES (%s, %s::date, %s, NOW())
                    ON CONFLICT (feed_name, month) DO UPDATE
                    SET stats = EXCLUDED.stats, updated_at = NOW()
                    """,
                    (name, start, json.dumps(stats)),
                )
                written += 1
            conn.commit()
            print(
                "  %s: %d written, %d skipped (< %d titles)"
                % (month, written, skipped, MIN_TITLES_FOR_MONTH),
                flush=True,
            )
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", help="Single month YYYY-MM")
    parser.add_argument("--feed", help="Limit to one feed")
    parser.add_argument(
        "--backfill",
        help="Comma-separated months, e.g. 2026-01,2026-02,2026-03,2026-04",
    )
    args = parser.parse_args()

    if args.backfill:
        months = [m.strip() for m in args.backfill.split(",") if m.strip()]
    elif args.month:
        months = [args.month]
    else:
        parser.error("Provide --month or --backfill")
        return

    t0 = time.time()
    for m in months:
        materialize_month(m, feed_name=args.feed)
    print("Done in %.1fs" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
