"""Materialize per-(centroid, month, locale) CentroidMonthView blobs into
mv_centroid_month_view.

Replaces the multi-query getCentroidMonthView path that ran per request.
Each materialized row contains the final CentroidMonthView shape
(activity_stripe + per-track summaries with top events + nav links),
ready for the frontend to read with a single PK lookup.

Title-word Dice de-dup of cross-day event fragments runs on the worker
side here (ported from lib/queries.ts); the frontend just renders.

Staleness gate: skips refresh if the table was updated within
--max-age-hours (default 12, matching ingestion cadence). Daemon may
call freely; the script no-ops between refreshes. Run with --force to
bypass.
"""

import argparse
import calendar
import json
import re
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

DEFAULT_MAX_AGE_HOURS = 12
LOCALES = ("en", "de")
CARD_DICE_THRESHOLD = 0.3
CARD_TOP_N = 5
CARD_FETCH_LIMIT = 10  # pre-dedup pool size per track
CALENDAR_EVENT_PAGE_MIN_SOURCES = 5

# Ported from lib/queries.ts so dedup matches the legacy frontend behavior.
CARD_STOP_WORDS = set(
    "the a an and or of to in on at for with by from as is was are be has have had not but "
    "this it its be has have had not but after over says said could new us s t "
    "will during about between into than more out up no may".split()
)

CARD_UBIQUITOUS = set(
    "trump biden vance us usa american america iran iranian china chinese russia "
    "russian putin netanyahu khamenei xi nato eu un".split()
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def title_words(text):
    if not text:
        return set()
    out = set()
    for w in _TOKEN_RE.findall(text.lower()):
        if len(w) > 1 and w not in CARD_STOP_WORDS and w not in CARD_UBIQUITOUS:
            out.add(w)
    return out


def dice(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return (2.0 * inter) / (len(a) + len(b))


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def is_stale(cur, max_age_hours):
    cur.execute(
        "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_centroid_month_view"
    )
    row = cur.fetchone()
    age = row[0] if row else None
    return age is None or age >= max_age_hours


def list_targets(cur):
    """Return list of (centroid_id, month_str, all_frozen) tuples for centroid
    months with promoted events. all_frozen=True iff EVERY ctm row for that
    (centroid, month) has is_frozen=true — once an MV row exists for such a
    target, it's immutable and can be skipped on subsequent runs."""
    cur.execute(
        """SELECT c.centroid_id,
                  c.month,
                  c.month::text AS month_str,
                  bool_and(c.is_frozen) AS all_frozen
             FROM ctm c
             JOIN events_v3 e ON e.ctm_id = c.id
            WHERE e.is_promoted = true AND e.merged_into IS NULL
            GROUP BY c.centroid_id, c.month
            ORDER BY c.centroid_id, c.month"""
    )
    return [(r[0], r[2], r[3]) for r in cur.fetchall()]


def existing_keys(cur):
    """Set of (centroid_id, month_str, locale) tuples already in the MV."""
    cur.execute("SELECT centroid_id, month::text, locale FROM mv_centroid_month_view")
    return {tuple(r) for r in cur.fetchall()}


def fetch_stripe(cur, centroid_id, month):
    cur.execute(
        """SELECT e.date::text, c.track, SUM(e.source_batch_count)::int
             FROM events_v3 e
             JOIN ctm c ON c.id = e.ctm_id
            WHERE c.centroid_id = %s AND c.month = %s
              AND e.is_promoted = true AND e.merged_into IS NULL
            GROUP BY e.date, c.track""",
        (centroid_id, month),
    )
    return cur.fetchall()


def fetch_top(cur, centroid_id, month, locale):
    """Top-N promoted events per track, locale-aware title coalesce."""
    title_expr = "COALESCE(e.title_de, e.title)" if locale == "de" else "e.title"
    sql = f"""WITH ranked AS (
                 SELECT c.track,
                        e.id::text AS event_id,
                        e.date::text AS date,
                        COALESCE(
                            {title_expr},
                            (SELECT t2.title_display FROM event_v3_titles evt2
                             JOIN titles_v3 t2 ON t2.id = evt2.title_id
                             WHERE evt2.event_id = e.id
                             ORDER BY t2.pubdate_utc ASC LIMIT 1)
                        ) AS title,
                        e.source_batch_count,
                        ROW_NUMBER() OVER (
                            PARTITION BY c.track
                            ORDER BY e.source_batch_count DESC, e.date DESC, e.id
                        ) AS rnk
                   FROM events_v3 e
                   JOIN ctm c ON c.id = e.ctm_id
                  WHERE c.centroid_id = %s AND c.month = %s
                    AND e.is_promoted = true AND e.merged_into IS NULL
                    AND e.is_catchall = false
              )
              SELECT track, event_id, date, title, source_batch_count
                FROM ranked WHERE rnk <= %s
               ORDER BY track, rnk"""
    cur.execute(sql, (centroid_id, month, CARD_FETCH_LIMIT))
    return cur.fetchall()


def fetch_ctms(cur, centroid_id, month):
    """Per-track CTM metadata + ctm_id (for theme chips)."""
    cur.execute(
        """SELECT c.id::text, c.track, c.title_count::int,
                  (SELECT MAX(e.date)::text FROM events_v3 e WHERE e.ctm_id = c.id)
             FROM ctm c
            WHERE c.centroid_id = %s AND c.month = %s""",
        (centroid_id, month),
    )
    return cur.fetchall()


def fetch_theme_chips(cur, ctm_id, limit=3):
    cur.execute(
        """WITH labels AS (
              SELECT tl.sector, tl.subject, COUNT(*) AS cnt
                FROM events_v3 e
                JOIN event_v3_titles evt ON evt.event_id = e.id
                JOIN title_labels tl ON tl.title_id = evt.title_id
               WHERE e.ctm_id = %s AND e.is_promoted = true
                 AND tl.sector IS NOT NULL AND tl.sector <> 'NON_STRATEGIC'
               GROUP BY tl.sector, tl.subject
            )
            SELECT sector, subject, (cnt::float / SUM(cnt) OVER ())::float
              FROM labels
             ORDER BY cnt DESC, sector, subject
             LIMIT %s""",
        (ctm_id, limit),
    )
    return [
        {"sector": r[0], "subject": r[1], "weight": float(r[2])} for r in cur.fetchall()
    ]


def fetch_nav(cur, centroid_id, month):
    """Prev / next month with coverage (any ctm row)."""
    cur.execute(
        """(SELECT month::text, true
              FROM ctm WHERE centroid_id = %s AND month < %s
              ORDER BY month DESC LIMIT 1)
           UNION ALL
           (SELECT month::text, false
              FROM ctm WHERE centroid_id = %s AND month > %s
              ORDER BY month ASC LIMIT 1)""",
        (centroid_id, month, centroid_id, month),
    )
    prev_month = None
    next_month = None
    for m, is_prev in cur.fetchall():
        if is_prev:
            prev_month = m[:7]
        else:
            next_month = m[:7]
    return prev_month, next_month


def build_activity_stripe(month_str, stripe_rows):
    """Per-day track shares; sums to ~1 when there's coverage."""
    by_date = {}
    total_by_date = {}
    for date, track, src in stripe_rows:
        by_date.setdefault(date, {})
        by_date[date][track] = by_date[date].get(track, 0) + src
        total_by_date[date] = total_by_date.get(date, 0) + src

    year, mm, _ = (int(p) for p in month_str.split("-"))
    days_in_month = calendar.monthrange(year, mm)[1]
    out = []
    for d in range(1, days_in_month + 1):
        date_str = f"{year}-{mm:02d}-{d:02d}"
        total = total_by_date.get(date_str, 0)
        track_map = by_date.get(date_str, {})
        tracks = []
        if total > 0:
            for tr, src in track_map.items():
                tracks.append({"track": tr, "weight": src / total})
            tracks.sort(key=lambda t: -t["weight"])
        out.append({"date": date_str, "total_sources": total, "tracks": tracks})
    return out


def dedup_top_events(top_rows):
    """Group top_rows by track, dedup with title-word Dice, keep CARD_TOP_N."""
    by_track = {}
    for track, event_id, date, title, src in top_rows:
        by_track.setdefault(track, []).append(
            {
                "event": {
                    "id": event_id,
                    "title": title or "",
                    "date": date,
                    "source_count": src,
                    "has_event_page": src >= CALENDAR_EVENT_PAGE_MIN_SOURCES,
                },
                "words": title_words(title),
            }
        )
    out = {}
    for track, candidates in by_track.items():
        kept = []
        for c in candidates:
            if any(dice(k["words"], c["words"]) >= CARD_DICE_THRESHOLD for k in kept):
                continue
            kept.append(c)
            if len(kept) >= CARD_TOP_N:
                break
        out[track] = [k["event"] for k in kept]
    return out


def materialize_one(cur, centroid_id, month, locale):
    """Compute the full CentroidMonthView for one (centroid, month, locale)
    and return the dict (caller upserts)."""
    stripe_rows = fetch_stripe(cur, centroid_id, month)
    top_rows = fetch_top(cur, centroid_id, month, locale)
    ctm_rows = fetch_ctms(cur, centroid_id, month)
    prev_month, next_month = fetch_nav(cur, centroid_id, month)

    activity_stripe = build_activity_stripe(month, stripe_rows)
    top_by_track = dedup_top_events(top_rows)

    tracks = []
    for ctm_id, track, title_count, last_active in ctm_rows:
        tracks.append(
            {
                "track": track,
                "title_count": title_count,
                "last_active": last_active,
                "theme_chips": fetch_theme_chips(cur, ctm_id, 3),
                "top_events": top_by_track.get(track, []),
            }
        )

    return {
        "centroid_id": centroid_id,
        "month": month,
        "activity_stripe": activity_stripe,
        "tracks": tracks,
        "prev_month": prev_month,
        "next_month": next_month,
    }


def upsert_batch(cur, rows):
    """rows: list of (centroid_id, month, locale, view_dict)"""
    if not rows:
        return 0
    execute_values(
        cur,
        """INSERT INTO mv_centroid_month_view
              (centroid_id, month, locale, view, updated_at)
           VALUES %s
           ON CONFLICT (centroid_id, month, locale) DO UPDATE
             SET view = EXCLUDED.view,
                 updated_at = EXCLUDED.updated_at""",
        [(c, m, loc, json.dumps(v)) for c, m, loc, v in rows],
        template="(%s, %s::date, %s, %s::jsonb, NOW())",
    )
    return len(rows)


def materialize(max_age_hours=DEFAULT_MAX_AGE_HOURS, force=False, batch_size=50):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if not force and not is_stale(cur, max_age_hours):
                cur.execute(
                    "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_centroid_month_view"
                )
                age = cur.fetchone()[0]
                print(
                    "Skipped: mv_centroid_month_view refreshed %.1fh ago (gate=%.1fh)"
                    % (age, max_age_hours)
                )
                return 0

            start = time.time()
            targets = list_targets(cur)
            existing = existing_keys(cur) if not force else set()

            # Skip frozen-already-materialized targets unless --force. A
            # (centroid, month) is "frozen" iff every ctm for that month has
            # is_frozen=true, AND all locale variants already exist in the MV.
            todo = []
            skipped_frozen = 0
            for centroid_id, month, all_frozen in targets:
                if all_frozen and not force:
                    if all((centroid_id, month, loc) in existing for loc in LOCALES):
                        skipped_frozen += 1
                        continue
                for locale in LOCALES:
                    todo.append((centroid_id, month, locale))

            print(
                "Targets: %d (centroid, month) pairs, %d frozen-skipped, "
                "%d rows to materialize" % (len(targets), skipped_frozen, len(todo))
            )

            batch = []
            done = 0
            for centroid_id, month, locale in todo:
                view = materialize_one(cur, centroid_id, month, locale)
                batch.append((centroid_id, month, locale, view))
                if len(batch) >= batch_size:
                    upsert_batch(cur, batch)
                    conn.commit()
                    done += len(batch)
                    batch = []
                    if done % 200 == 0:
                        print("  ... %d/%d rows" % (done, len(todo)))
            if batch:
                upsert_batch(cur, batch)
                conn.commit()
                done += len(batch)

            elapsed = time.time() - start
            print("Done: %d rows upserted (%.1fs)" % (done, elapsed))
            return done
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Materialize per-(centroid, month, locale) CentroidMonthView"
    )
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=DEFAULT_MAX_AGE_HOURS,
        help="Skip if table was refreshed within this window (default: %(default)s)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass staleness gate AND frozen-skip; refresh everything",
    )
    args = parser.parse_args()
    materialize(max_age_hours=args.max_age_hours, force=args.force)


if __name__ == "__main__":
    main()
