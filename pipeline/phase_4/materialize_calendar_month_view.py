"""Materialize per-(centroid, track, month, locale) CalendarMonthView blobs
into mv_calendar_month_view.

Backs both /c/[id]/t/[track] (CTM monthly view) and
/c/[id]/t/[track]/[date] (day-canonical sub-route) — they share the same
data backbone. Frontend reads via single PK lookup.

Two correctness improvements baked in:
  - Top-20 clusters per day cap (hard-enforced; the pipeline-side
    promotion drifted past 20 because it's one-way and never demotes).
  - Frozen-month skip: once ctm.is_frozen=true and an MV row exists,
    that (centroid, track, month, locale) is immutable and skipped on
    every subsequent run. Drops compute by ~80% per cycle once all
    historical months are frozen.

Staleness gate: skips refresh if the table was updated within
--max-age-hours (default 12). --force bypasses both the staleness
gate AND the frozen-skip (use after a JSONB shape change).
"""

import argparse
import calendar
import json
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

DEFAULT_MAX_AGE_HOURS = 12
LOCALES = ("en", "de")
TOP_CLUSTERS_PER_DAY = 20  # frontend hard cap (pipeline drift safety)
CALENDAR_EVENT_PAGE_MIN_SOURCES = 5


def get_connection():
    return psycopg2.connect(
        **config.db_connect_kwargs(),
    )


def is_stale(cur, max_age_hours):
    cur.execute(
        "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_calendar_month_view"
    )
    row = cur.fetchone()
    age = row[0] if row else None
    return age is None or age >= max_age_hours


def list_targets(cur):
    """Return list of (ctm_id, centroid_id, track, month_str, is_frozen) for
    every CTM that has at least one promoted event."""
    cur.execute(
        """SELECT c.id::text, c.centroid_id, c.track, c.month::text, c.is_frozen
             FROM ctm c
            WHERE EXISTS (
                SELECT 1 FROM events_v3 e
                 WHERE e.ctm_id = c.id AND e.is_promoted = true
                   AND e.merged_into IS NULL
            )
            ORDER BY c.centroid_id, c.track, c.month"""
    )
    return cur.fetchall()


def existing_keys(cur):
    """Set of (centroid_id, track, month_str, locale) tuples already in the MV."""
    cur.execute(
        "SELECT centroid_id, track, month::text, locale FROM mv_calendar_month_view"
    )
    return {tuple(r) for r in cur.fetchall()}


# ─── per-target SQL fetches ─────────────────────────────────────────────


def fetch_clusters(cur, ctm_id, locale):
    """Top-20 promoted events per day for this CTM, locale-aware title.

    The ROW_NUMBER cap belongs in SQL — both for efficiency (don't ship
    unused rows) and for the JSONB to carry a clean cap. Cluster order
    inside a day stays source_count DESC.
    """
    title_expr = "COALESCE(e.title_de, e.title)" if locale == "de" else "e.title"
    sql = f"""WITH ranked AS (
                SELECT
                    e.id::text AS id,
                    e.date::text AS first_date,
                    COALESCE(e.last_active::text, e.date::text) AS last_date,
                    COALESCE(
                        {title_expr},
                        (SELECT t2.title_display FROM event_v3_titles evt2
                         JOIN titles_v3 t2 ON t2.id = evt2.title_id
                         WHERE evt2.event_id = e.id
                         ORDER BY t2.pubdate_utc ASC LIMIT 1)
                    ) AS title,
                    e.source_batch_count,
                    e.event_type,
                    e.bucket_key,
                    EXISTS(
                        SELECT 1 FROM narratives n
                         WHERE n.entity_type = 'event' AND n.entity_id = e.id
                    ) AS has_narratives,
                    ROW_NUMBER() OVER (
                        PARTITION BY e.date
                        ORDER BY e.source_batch_count DESC, e.id
                    ) AS rnk
                FROM events_v3 e
                WHERE e.ctm_id = %s
                  AND e.is_promoted = true
                  AND e.is_catchall = false
                  AND e.merged_into IS NULL
            )
            SELECT id, first_date, last_date, title, source_batch_count,
                   event_type, bucket_key, has_narratives
              FROM ranked
             WHERE rnk <= %s
             ORDER BY first_date ASC, source_batch_count DESC"""
    cur.execute(sql, (ctm_id, TOP_CLUSTERS_PER_DAY))
    return cur.fetchall()


def fetch_small_cluster_sources(cur, small_cluster_ids):
    """For clusters that won't get their own event page (source_count < 5),
    load the source titles so users can still click through."""
    if not small_cluster_ids:
        return {}
    cur.execute(
        """SELECT et.event_id::text,
                  t.id::text,
                  t.title_display,
                  t.url_gnews,
                  t.publisher_name,
                  f.source_domain,
                  t.detected_language
             FROM event_v3_titles et
             JOIN titles_v3 t  ON t.id = et.title_id
             LEFT JOIN feeds f ON f.id = t.feed_id
            WHERE et.event_id = ANY(%s::uuid[])
            ORDER BY t.pubdate_utc ASC""",
        (small_cluster_ids,),
    )
    out = {}
    for event_id, tid, title_display, url, pub, domain, lang in cur.fetchall():
        out.setdefault(event_id, []).append(
            {
                "id": tid,
                "title_display": title_display,
                "url": url,
                "publisher_name": pub,
                "publisher_domain": domain,
                "detected_language": lang,
            }
        )
    return out


def fetch_briefs(cur, ctm_id, locale):
    """Daily brief prose per date."""
    cur.execute(
        "SELECT date::text, brief_en, brief_de FROM daily_briefs WHERE ctm_id = %s",
        (ctm_id,),
    )
    out = {}
    for date, en, de in cur.fetchall():
        out[date] = de if (locale == "de" and de) else en
    return out


def fetch_day_themes(cur, ctm_id):
    """Per-date theme segments (sector, subject, weight). Locale-invariant."""
    cur.execute(
        """WITH day_labels AS (
              SELECT e.date::text AS date, tl.sector, tl.subject, COUNT(*) AS cnt
                FROM events_v3 e
                JOIN event_v3_titles evt ON evt.event_id = e.id
                JOIN title_labels tl ON tl.title_id = evt.title_id
               WHERE e.ctm_id = %s AND e.is_promoted = true
                 AND tl.sector IS NOT NULL AND tl.sector <> 'NON_STRATEGIC'
               GROUP BY e.date, tl.sector, tl.subject
            ),
            totals AS (
              SELECT date, SUM(cnt) AS day_total FROM day_labels GROUP BY date
            )
            SELECT dl.date, dl.sector, dl.subject,
                   (dl.cnt::float / t.day_total)::float AS weight
              FROM day_labels dl
              JOIN totals t ON t.date = dl.date
             ORDER BY dl.date, dl.cnt DESC, dl.sector, dl.subject""",
        (ctm_id,),
    )
    out = {}
    for date, sector, subject, weight in cur.fetchall():
        out.setdefault(date, []).append(
            {"sector": sector, "subject": subject, "weight": float(weight)}
        )
    return out


def fetch_scope(cur, ctm_id):
    """CTM-level scope stats."""
    cur.execute(
        """SELECT COUNT(DISTINCT ta.title_id)::int,
                  COUNT(DISTINCT t.feed_id)::int
             FROM title_assignments ta
             JOIN titles_v3 t ON t.id = ta.title_id
            WHERE ta.ctm_id = %s""",
        (ctm_id,),
    )
    row = cur.fetchone() or (0, 0)
    return {"total_sources": int(row[0]), "outlet_count": int(row[1])}


def fetch_theme_chips(cur, ctm_id, limit=3):
    """Top-N dominant themes for the CTM (sector + subject)."""
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


def fetch_ctm(cur, ctm_id, locale):
    """CTM metadata (locale-aware summary_text)."""
    summary_col = (
        "COALESCE(summary_text_de, summary_text)" if locale == "de" else "summary_text"
    )
    cur.execute(
        f"""SELECT id::text, centroid_id, track, month::text, title_count,
                  {summary_col}, is_frozen
             FROM ctm WHERE id = %s""",
        (ctm_id,),
    )
    r = cur.fetchone()
    if not r:
        return None
    return {
        "id": r[0],
        "centroid_id": r[1],
        "track": r[2],
        "month": r[3],
        "title_count": r[4],
        "summary_text": r[5],
        "is_frozen": r[6],
        "events_digest": [],  # Frontend doesn't read this on the CTM page
    }


# ─── per-target assembly ────────────────────────────────────────────────


def materialize_one(cur, ctm_id, centroid_id, track, month_str, locale):
    """Assemble the full CalendarMonthView blob for one target."""
    ctm = fetch_ctm(cur, ctm_id, locale)
    if not ctm:
        return None

    cluster_rows = fetch_clusters(cur, ctm_id, locale)

    # Group clusters by date.
    days_map = {}
    for row in cluster_rows:
        (
            cid,
            first_date,
            last_date,
            title,
            src,
            event_type,
            bucket_key,
            has_narratives,
        ) = row
        day = days_map.get(first_date)
        if not day:
            day = {
                "date": first_date,
                "total_sources": 0,
                "cluster_count": 0,
                "daily_brief": None,
                "clusters": [],
            }
            days_map[first_date] = day
        day["clusters"].append(
            {
                "id": cid,
                "title": title,
                "source_count": src,
                "first_date": first_date,
                "last_date": last_date,
                "event_type": event_type,
                "bucket_key": bucket_key,
                "has_event_page": src >= CALENDAR_EVENT_PAGE_MIN_SOURCES,
                "is_substrate": False,
                "has_narratives": has_narratives,
            }
        )
        day["total_sources"] += src
        day["cluster_count"] += 1

    # Source titles for small clusters (<5 src) — they don't get event pages
    # so the page links to original publications instead.
    small_ids = []
    for day in days_map.values():
        for c in day["clusters"]:
            if not c["has_event_page"]:
                small_ids.append(c["id"])
    sources_by_event = fetch_small_cluster_sources(cur, small_ids)
    for day in days_map.values():
        for c in day["clusters"]:
            if not c["has_event_page"]:
                c["sources"] = sources_by_event.get(c["id"], [])

    # Daily briefs
    briefs = fetch_briefs(cur, ctm_id, locale)
    for date, brief in briefs.items():
        if date in days_map:
            days_map[date]["daily_brief"] = brief

    # Day themes (locale-invariant)
    themes_by_date = fetch_day_themes(cur, ctm_id)

    # Activity stripe — every day of month
    year, mm, _ = (int(p) for p in month_str.split("-"))
    days_in_month = calendar.monthrange(year, mm)[1]
    stripe = []
    for d in range(1, days_in_month + 1):
        date_str = f"{year}-{mm:02d}-{d:02d}"
        day_entry = days_map.get(date_str)
        stripe.append(
            {
                "date": date_str,
                "total_sources": day_entry["total_sources"] if day_entry else 0,
                "themes": themes_by_date.get(date_str, []),
            }
        )

    scope_stats = fetch_scope(cur, ctm_id)
    scope_stats["active_days"] = len(days_map)
    theme_chips = fetch_theme_chips(cur, ctm_id, 3)

    return {
        "ctm": ctm,
        "days": list(days_map.values()),
        "activity_stripe": stripe,
        "scope": scope_stats,
        "theme_chips": theme_chips,
    }


# ─── upsert ─────────────────────────────────────────────────────────────


def upsert_batch(cur, rows):
    """rows: list of (centroid_id, track, month_str, locale, view_dict)"""
    if not rows:
        return 0
    execute_values(
        cur,
        """INSERT INTO mv_calendar_month_view
              (centroid_id, track, month, locale, view, updated_at)
           VALUES %s
           ON CONFLICT (centroid_id, track, month, locale) DO UPDATE
             SET view = EXCLUDED.view,
                 updated_at = EXCLUDED.updated_at""",
        [(c, tr, m, loc, json.dumps(v)) for c, tr, m, loc, v in rows],
        template="(%s, %s, %s::date, %s, %s::jsonb, NOW())",
    )
    return len(rows)


# ─── main loop ──────────────────────────────────────────────────────────


def materialize(max_age_hours=DEFAULT_MAX_AGE_HOURS, force=False, batch_size=50):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if not force and not is_stale(cur, max_age_hours):
                cur.execute(
                    "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_calendar_month_view"
                )
                age = cur.fetchone()[0]
                print(
                    "Skipped: mv_calendar_month_view refreshed %.1fh ago (gate=%.1fh)"
                    % (age, max_age_hours)
                )
                return 0

            start = time.time()
            targets = list_targets(cur)
            existing = existing_keys(cur) if not force else set()

            # Skip frozen-already-materialized targets unless --force.
            # For a frozen CTM we need ALL locale rows to exist before skipping.
            todo = []
            skipped_frozen = 0
            for ctm_id, centroid_id, track, month_str, is_frozen in targets:
                if is_frozen and not force:
                    all_locales_present = all(
                        (centroid_id, track, month_str, loc) in existing
                        for loc in LOCALES
                    )
                    if all_locales_present:
                        skipped_frozen += 1
                        continue
                for locale in LOCALES:
                    todo.append((ctm_id, centroid_id, track, month_str, locale))

            print(
                "Targets: %d total, %d frozen-skipped, %d to materialize"
                % (len(targets), skipped_frozen, len(todo))
            )

            batch = []
            done = 0
            for ctm_id, centroid_id, track, month_str, locale in todo:
                view = materialize_one(
                    cur, ctm_id, centroid_id, track, month_str, locale
                )
                if view is None:
                    continue
                batch.append((centroid_id, track, month_str, locale, view))
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
        description="Materialize per-(centroid, track, month, locale) CalendarMonthView"
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
