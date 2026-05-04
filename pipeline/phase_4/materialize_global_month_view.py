"""Materialize per-(month, locale) GlobalMonthView blobs into
mv_global_month_view.

Backs the /trending page. Replaces 2 live queries (getGlobalMonthView +
getActiveNarrativesGlobal) with a single PK lookup. Frontend reads the
blob and renders.

Frozen-skip optimization: once every CTM in the target month has
is_frozen=true AND the MV row for both locales exists, the month is
immutable and skipped on subsequent runs. After April freeze, only
May refreshes; ~80% compute saved per cycle.

Staleness gate: skips refresh if the table was updated within
--max-age-hours (default 12). --force bypasses both the staleness
gate AND the frozen-skip.
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
DICE_THRESHOLD = 0.3
TOP_N_PER_TRACK = 5
TOP_FETCH_LIMIT = 10
NARRATIVES_LIMIT = 10
CALENDAR_EVENT_PAGE_MIN_SOURCES = 5
DAY_TOP_LIMIT = 10
DAY_TOP_FETCH_LIMIT = 40
FASTEST_GROWING_LIMIT = 12
FASTEST_GROWING_FETCH_LIMIT = 48
FASTEST_GROWING_MIN_RECENT = 3
FASTEST_GROWING_MIN_TOTAL = 5
# Active signal types only — commodities/policies/systems were retired
# from extraction (see pipeline/phase_3_1/extract_labels.py). Trending
# sidebar shows persons/orgs/places/named_events.
SIGNAL_COLUMNS = ("persons", "orgs", "places", "named_events")
SIGNALS_TOP_PER_TYPE = 5

# Ported from lib/queries.ts so dedup matches frontend semantics.
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
    return {
        w
        for w in _TOKEN_RE.findall(text.lower())
        if len(w) > 1 and w not in CARD_STOP_WORDS and w not in CARD_UBIQUITOUS
    }


def dice(a, b):
    if not a or not b:
        return 0.0
    return (2.0 * len(a & b)) / (len(a) + len(b))


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
        "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_global_month_view"
    )
    row = cur.fetchone()
    age = row[0] if row else None
    return age is None or age >= max_age_hours


def list_targets(cur):
    """Return list of (month_str, all_frozen) tuples for months with promoted
    events. all_frozen=True iff every ctm row for that month is frozen."""
    cur.execute(
        """SELECT c.month::text AS month_str,
                  bool_and(c.is_frozen) AS all_frozen
             FROM ctm c
             JOIN events_v3 e ON e.ctm_id = c.id
            WHERE e.is_promoted = true AND e.merged_into IS NULL
            GROUP BY c.month
            ORDER BY c.month"""
    )
    return cur.fetchall()


def existing_keys(cur):
    """Set of (month_str, locale) keys already in the MV."""
    cur.execute("SELECT month::text, locale FROM mv_global_month_view")
    return {tuple(r) for r in cur.fetchall()}


# ─── per-target SQL fetches ─────────────────────────────────────────────


def fetch_stripe(cur, month):
    cur.execute(
        """SELECT e.date::text, c.track, SUM(e.source_batch_count)::int
             FROM events_v3 e
             JOIN ctm c ON c.id = e.ctm_id
            WHERE c.month = %s
              AND e.is_promoted = true AND e.merged_into IS NULL
            GROUP BY e.date, c.track""",
        (month,),
    )
    return cur.fetchall()


def fetch_top_per_track(cur, month, locale):
    """Top-N promoted events per track globally, locale-aware title."""
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
                       c.centroid_id,
                       cv.label AS centroid_label,
                       ROW_NUMBER() OVER (
                           PARTITION BY c.track
                           ORDER BY e.source_batch_count DESC, e.date DESC, e.id
                       ) AS rnk
                  FROM events_v3 e
                  JOIN ctm c ON c.id = e.ctm_id
                  JOIN centroids_v3 cv ON cv.id = c.centroid_id
                 WHERE c.month = %s
                   AND e.is_promoted = true
                   AND e.merged_into IS NULL
                   AND e.is_catchall = false
            )
            SELECT track, event_id, date, title, source_batch_count,
                   centroid_id, centroid_label
              FROM ranked WHERE rnk <= %s
             ORDER BY track, rnk"""
    cur.execute(sql, (month, TOP_FETCH_LIMIT))
    return cur.fetchall()


def fetch_themes(cur, month):
    """Per-track theme aggregation across all centroids in the month."""
    cur.execute(
        """WITH labels AS (
              SELECT c.track, tl.sector, tl.subject, COUNT(*) AS cnt
                FROM events_v3 e
                JOIN ctm c ON c.id = e.ctm_id
                JOIN event_v3_titles evt ON evt.event_id = e.id
                JOIN title_labels tl ON tl.title_id = evt.title_id
               WHERE c.month = %s
                 AND e.is_promoted = true AND e.merged_into IS NULL
                 AND tl.sector IS NOT NULL AND tl.sector <> 'NON_STRATEGIC'
               GROUP BY c.track, tl.sector, tl.subject
            )
            SELECT track, sector, subject, cnt::int,
                   SUM(cnt) OVER (PARTITION BY track)::int AS track_total
              FROM labels
             ORDER BY track, cnt DESC, sector, subject""",
        (month,),
    )
    return cur.fetchall()


def fetch_per_track_totals(cur, month):
    cur.execute(
        """SELECT c.track,
                  COUNT(DISTINCT e.id)::int AS event_count,
                  COALESCE(SUM(e.source_batch_count), 0)::int AS source_count
             FROM events_v3 e
             JOIN ctm c ON c.id = e.ctm_id
            WHERE c.month = %s
              AND e.is_promoted = true AND e.merged_into IS NULL
            GROUP BY c.track""",
        (month,),
    )
    return cur.fetchall()


def fetch_global_totals(cur, month):
    cur.execute(
        """SELECT COUNT(DISTINCT c.centroid_id)::int
             FROM events_v3 e JOIN ctm c ON c.id = e.ctm_id
            WHERE c.month = %s AND e.is_promoted = true AND e.merged_into IS NULL""",
        (month,),
    )
    row = cur.fetchone()
    return int(row[0]) if row else 0


def fetch_nav(cur, month):
    cur.execute(
        """(SELECT TO_CHAR(month, 'YYYY-MM'), true
              FROM ctm WHERE month < %s
              ORDER BY month DESC LIMIT 1)
           UNION ALL
           (SELECT TO_CHAR(month, 'YYYY-MM'), false
              FROM ctm WHERE month > %s
              ORDER BY month ASC LIMIT 1)""",
        (month, month),
    )
    prev_month = None
    next_month = None
    for m, is_prev in cur.fetchall():
        if is_prev:
            prev_month = m
        else:
            next_month = m
    return prev_month, next_month


def fetch_active_narratives(cur, month, locale):
    """Top N strategic narratives by event count for this month."""
    cur.execute(
        """SELECT sn.id, sn.name, sn.name_de, sn.claim, sn.claim_de,
                  sn.actor_centroid,
                  COUNT(DISTINCT e.id)::int AS event_count
             FROM event_strategic_narratives esn
             JOIN events_v3 e ON e.id = esn.event_id
             JOIN ctm c ON c.id = e.ctm_id
             JOIN strategic_narratives sn ON sn.id = esn.narrative_id
            WHERE c.month = %s
              AND e.merged_into IS NULL
              AND sn.is_active = true
            GROUP BY sn.id, sn.name, sn.name_de, sn.claim, sn.claim_de, sn.actor_centroid
            ORDER BY event_count DESC, sn.name
            LIMIT %s""",
        (month, NARRATIVES_LIMIT),
    )
    out = []
    for r in cur.fetchall():
        nid, name, name_de, claim, claim_de, actor, count = r
        out.append(
            {
                "id": nid,
                "name": name_de if (locale == "de" and name_de) else name,
                "claim": claim_de if (locale == "de" and claim_de) else claim,
                "actor_centroid": actor,
                "event_count": int(count),
            }
        )
    return out


def fetch_signals(cur, month):
    """Top SIGNALS_TOP_PER_TYPE per signal type for the month's promoted
    events. Signal values are language-neutral entity strings — identical
    for en and de."""
    parts = []
    for col in SIGNAL_COLUMNS:
        parts.append(
            f"""(SELECT '{col}'::text AS signal_type, val AS value,
                        COUNT(DISTINCT evt.event_id)::int AS event_count
                   FROM events_v3 e
                   JOIN ctm c ON c.id = e.ctm_id
                   JOIN event_v3_titles evt ON evt.event_id = e.id
                   JOIN title_labels tl ON tl.title_id = evt.title_id
                   CROSS JOIN LATERAL unnest(COALESCE(tl.{col}, '{{}}')) AS val
                  WHERE c.month = %s
                    AND e.is_promoted = true
                    AND e.merged_into IS NULL
                    AND e.is_catchall = false
                  GROUP BY val
                  ORDER BY event_count DESC, val
                  LIMIT {SIGNALS_TOP_PER_TYPE})"""
        )
    sql = " UNION ALL ".join(parts)
    cur.execute(sql, tuple([month] * len(SIGNAL_COLUMNS)))
    out = {col: [] for col in SIGNAL_COLUMNS}
    for sig_type, value, event_count in cur.fetchall():
        out[sig_type].append(
            {"signal_type": sig_type, "value": value, "event_count": int(event_count)}
        )
    return out


def fetch_day_top_events(cur, month, locale):
    """For every day in the month, top DAY_TOP_LIMIT events ranked by 7-day
    cumulative source count ending on that day. Mirrors the live
    getGlobalDayTopEvents query, batched per month and dedup'd in Python.
    Returns dict keyed by YYYY-MM-DD."""
    title_expr = "COALESCE(e.title_de, e.title)" if locale == "de" else "e.title"
    fallback_expr = f"""COALESCE({title_expr},
                    (SELECT t2.title_display FROM event_v3_titles evt2
                     JOIN titles_v3 t2 ON t2.id = evt2.title_id
                     WHERE evt2.event_id = e.id
                     ORDER BY t2.pubdate_utc ASC LIMIT 1))"""
    sql = f"""WITH days AS (
                SELECT generate_series(
                    %s::date,
                    (%s::date + INTERVAL '1 month - 1 day')::date,
                    '1 day'::interval
                )::date AS d
              ),
              event_day_counts AS (
                SELECT evt.event_id, t.pubdate_utc::date AS src_date,
                       COUNT(*)::int AS cnt
                  FROM events_v3 e
                  JOIN ctm c ON c.id = e.ctm_id
                  JOIN event_v3_titles evt ON evt.event_id = e.id
                  JOIN titles_v3 t ON t.id = evt.title_id
                 WHERE c.month = %s
                   AND e.is_promoted = true
                   AND e.merged_into IS NULL
                   AND e.is_catchall = false
                   AND t.pubdate_utc::date BETWEEN
                       (%s::date - 6) AND
                       (%s::date + INTERVAL '1 month - 1 day')::date
                 GROUP BY evt.event_id, t.pubdate_utc::date
              ),
              event_window AS (
                SELECT d.d AS target_day, edc.event_id,
                       SUM(edc.cnt)::int AS window_sources
                  FROM days d
                  JOIN event_day_counts edc
                       ON edc.src_date BETWEEN d.d - 6 AND d.d
                 GROUP BY d.d, edc.event_id
              ),
              ranked AS (
                SELECT ew.target_day, ew.event_id, ew.window_sources,
                       ROW_NUMBER() OVER (
                           PARTITION BY ew.target_day
                           ORDER BY ew.window_sources DESC, ew.event_id
                       ) AS rnk
                  FROM event_window ew
              )
              SELECT r.target_day::text, r.event_id::text, r.window_sources,
                     {fallback_expr} AS title,
                     e.date::text AS event_date,
                     e.source_batch_count AS total_sources,
                     c.centroid_id, cv.label AS centroid_label, c.track
                FROM ranked r
                JOIN events_v3 e ON e.id = r.event_id
                JOIN ctm c ON c.id = e.ctm_id
                JOIN centroids_v3 cv ON cv.id = c.centroid_id
               WHERE r.rnk <= %s
               ORDER BY r.target_day, r.rnk"""
    cur.execute(sql, (month, month, month, month, month, DAY_TOP_FETCH_LIMIT))

    by_day = {}
    for row in cur.fetchall():
        (
            target_day,
            event_id,
            window_sources,
            title,
            event_date,
            total_sources,
            centroid_id,
            centroid_label,
            track,
        ) = row
        by_day.setdefault(target_day, []).append(
            {
                "id": event_id,
                "title": title or "",
                "centroid_id": centroid_id,
                "centroid_label": centroid_label,
                "track": track,
                "date": event_date,
                "total_sources": int(total_sources) if total_sources else 0,
                "window_sources": int(window_sources),
            }
        )

    out = {}
    for day, candidates in by_day.items():
        kept = []
        kept_words = []
        for c in candidates:
            words = title_words(c["title"])
            if any(dice(kw, words) >= DICE_THRESHOLD for kw in kept_words):
                continue
            kept.append(c)
            kept_words.append(words)
            if len(kept) >= DAY_TOP_LIMIT:
                break
        if kept:
            out[day] = kept
    return out


def fetch_fastest_growing(cur, month, locale):
    """Mirror getFastestGrowingEvents but enriched: includes summary,
    iso_codes, top_signals, date, last_active so the homepage carousel
    can render rich cards from the same MV row.

    Cross-centroid title-Dice dedup applied in Python (matches live
    query behavior). Limit 12 (homepage carousel size)."""
    title_expr = "COALESCE(e.title_de, e.title)" if locale == "de" else "e.title"
    summary_expr = (
        "COALESCE(e.summary_de, e.summary)" if locale == "de" else "e.summary"
    )
    sql = f"""WITH recent AS (
                SELECT evt.event_id, COUNT(*)::int AS recent_7d_sources
                  FROM event_v3_titles evt
                  JOIN titles_v3 t ON t.id = evt.title_id
                 WHERE t.pubdate_utc >= NOW() - INTERVAL '7 days'
                 GROUP BY evt.event_id
              )
              SELECT e.id::text AS id,
                     COALESCE(
                       {title_expr},
                       (SELECT t2.title_display FROM event_v3_titles evt2
                        JOIN titles_v3 t2 ON t2.id = evt2.title_id
                        WHERE evt2.event_id = e.id
                        ORDER BY t2.pubdate_utc DESC LIMIT 1)
                     ) AS title,
                     LEFT({summary_expr}, 200) AS summary,
                     e.date::text AS date,
                     COALESCE(e.last_active, e.date)::text AS last_active,
                     e.source_batch_count AS total_sources,
                     r.recent_7d_sources,
                     c.centroid_id, cv.label AS centroid_label,
                     cv.iso_codes, c.track,
                     -- top 3 signals across persons + orgs (matches the
                     -- old getTrendingEvents pattern). Returned as
                     -- 'type:value' strings for the carousel pill renderer.
                     (SELECT array_agg(sig_type || ':' || val ORDER BY cnt DESC)
                        FROM (
                          SELECT sig_type, val, COUNT(*) AS cnt FROM (
                            SELECT 'persons' AS sig_type,
                                   unnest(COALESCE(tl.persons, '{{}}')) AS val
                              FROM event_v3_titles evt
                              JOIN title_labels tl ON tl.title_id = evt.title_id
                             WHERE evt.event_id = e.id
                             UNION ALL
                            SELECT 'orgs' AS sig_type,
                                   unnest(COALESCE(tl.orgs, '{{}}')) AS val
                              FROM event_v3_titles evt
                              JOIN title_labels tl ON tl.title_id = evt.title_id
                             WHERE evt.event_id = e.id
                          ) expanded
                          GROUP BY sig_type, val
                          ORDER BY cnt DESC LIMIT 3
                        ) sub
                     ) AS top_signals
                FROM events_v3 e
                JOIN ctm c ON c.id = e.ctm_id
                JOIN centroids_v3 cv ON cv.id = c.centroid_id
                JOIN recent r ON r.event_id = e.id
               WHERE c.month = %s
                 AND e.is_promoted = true
                 AND e.merged_into IS NULL
                 AND e.is_catchall = false
                 AND e.source_batch_count >= %s
                 AND r.recent_7d_sources >= %s
               ORDER BY r.recent_7d_sources DESC, e.source_batch_count DESC
               LIMIT %s"""
    cur.execute(
        sql,
        (
            month,
            FASTEST_GROWING_MIN_TOTAL,
            FASTEST_GROWING_MIN_RECENT,
            FASTEST_GROWING_FETCH_LIMIT,
        ),
    )

    candidates = []
    for row in cur.fetchall():
        (
            event_id,
            title,
            summary,
            date,
            last_active,
            total_sources,
            recent_7d,
            centroid_id,
            centroid_label,
            iso_codes,
            track,
            top_signals,
        ) = row
        candidates.append(
            {
                "id": event_id,
                "title": title or "",
                "summary": summary,
                "date": date,
                "last_active": last_active,
                "total_sources": int(total_sources),
                "recent_7d_sources": int(recent_7d),
                "growth_ratio": (
                    float(recent_7d) / float(total_sources) if total_sources else 0.0
                ),
                "centroid_id": centroid_id,
                "centroid_label": centroid_label,
                "iso_codes": list(iso_codes) if iso_codes else [],
                "track": track,
                "top_signals": list(top_signals) if top_signals else [],
            }
        )

    # Cross-centroid title-Dice dedup, matches the live query's behavior.
    kept = []
    kept_words = []
    for c in candidates:
        words = title_words(c["title"])
        if any(dice(kw, words) >= DICE_THRESHOLD for kw in kept_words):
            continue
        kept.append(c)
        kept_words.append(words)
        if len(kept) >= FASTEST_GROWING_LIMIT:
            break
    return kept


# ─── per-target assembly ────────────────────────────────────────────────


def build_activity_stripe(month_str, stripe_rows):
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
    """Group top_rows by track, dedup with title-word Dice, keep TOP_N."""
    by_track = {}
    for track, eid, date, title, src, centroid_id, centroid_label in top_rows:
        by_track.setdefault(track, []).append(
            {
                "event": {
                    "id": eid,
                    "title": title or "",
                    "date": date,
                    "centroid_id": centroid_id,
                    "centroid_label": centroid_label,
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
            if any(dice(k["words"], c["words"]) >= DICE_THRESHOLD for k in kept):
                continue
            kept.append(c)
            if len(kept) >= TOP_N_PER_TRACK:
                break
        out[track] = [k["event"] for k in kept]
    return out


def materialize_one(cur, month, locale):
    stripe_rows = fetch_stripe(cur, month)
    if not stripe_rows:
        return None
    top_rows = fetch_top_per_track(cur, month, locale)
    theme_rows = fetch_themes(cur, month)
    per_track_rows = fetch_per_track_totals(cur, month)
    active_centroids = fetch_global_totals(cur, month)
    prev_month, next_month = fetch_nav(cur, month)
    active_narratives = fetch_active_narratives(cur, month, locale)
    signals = fetch_signals(cur, month)
    day_top_events = fetch_day_top_events(cur, month, locale)
    fastest_growing = fetch_fastest_growing(cur, month, locale)

    activity_stripe = build_activity_stripe(month, stripe_rows)
    top_by_track = dedup_top_events(top_rows)

    # Theme chips per track: top-3.
    chips_by_track = {}
    for track, sector, subject, cnt, track_total in theme_rows:
        chips = chips_by_track.setdefault(track, [])
        if len(chips) < 3 and track_total > 0:
            chips.append(
                {"sector": sector, "subject": subject, "weight": cnt / track_total}
            )

    totals_by_track = {r[0]: (int(r[1]), int(r[2])) for r in per_track_rows}

    track_order = []
    seen = set()
    for r in stripe_rows:
        if r[1] not in seen:
            seen.add(r[1])
            track_order.append(r[1])
    for r in top_rows:
        if r[0] not in seen:
            seen.add(r[0])
            track_order.append(r[0])

    tracks = []
    for tr in track_order:
        ec, sc = totals_by_track.get(tr, (0, 0))
        tracks.append(
            {
                "track": tr,
                "event_count": ec,
                "source_count": sc,
                "theme_chips": chips_by_track.get(tr, []),
                "top_events": top_by_track.get(tr, []),
            }
        )

    total_events = sum(t["event_count"] for t in tracks)
    total_sources = sum(t["source_count"] for t in tracks)

    return {
        "month": month,
        "activity_stripe": activity_stripe,
        "tracks": tracks,
        "active_centroid_count": active_centroids,
        "total_events": total_events,
        "total_sources": total_sources,
        "prev_month": prev_month,
        "next_month": next_month,
        "active_narratives": active_narratives,
        "signals": signals,
        "day_top_events": day_top_events,
        "fastest_growing": fastest_growing,
    }


def upsert_batch(cur, rows):
    if not rows:
        return 0
    execute_values(
        cur,
        """INSERT INTO mv_global_month_view (month, locale, view, updated_at)
           VALUES %s
           ON CONFLICT (month, locale) DO UPDATE
             SET view = EXCLUDED.view, updated_at = EXCLUDED.updated_at""",
        [(m, loc, json.dumps(v)) for m, loc, v in rows],
        template="(%s::date, %s, %s::jsonb, NOW())",
    )
    return len(rows)


def materialize(max_age_hours=DEFAULT_MAX_AGE_HOURS, force=False, batch_size=10):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if not force and not is_stale(cur, max_age_hours):
                cur.execute(
                    "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600 FROM mv_global_month_view"
                )
                age = cur.fetchone()[0]
                print(
                    "Skipped: mv_global_month_view refreshed %.1fh ago (gate=%.1fh)"
                    % (age, max_age_hours)
                )
                return 0

            start = time.time()
            targets = list_targets(cur)
            existing = existing_keys(cur) if not force else set()

            todo = []
            skipped_frozen = 0
            for month, all_frozen in targets:
                if all_frozen and not force:
                    if all((month, loc) in existing for loc in LOCALES):
                        skipped_frozen += 1
                        continue
                for locale in LOCALES:
                    todo.append((month, locale))

            print(
                "Targets: %d months, %d frozen-skipped, %d rows to materialize"
                % (len(targets), skipped_frozen, len(todo))
            )

            batch = []
            done = 0
            for month, locale in todo:
                view = materialize_one(cur, month, locale)
                if view is None:
                    continue
                batch.append((month, locale, view))
                if len(batch) >= batch_size:
                    upsert_batch(cur, batch)
                    conn.commit()
                    done += len(batch)
                    batch = []
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
        description="Materialize per-(month, locale) GlobalMonthView blobs"
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
