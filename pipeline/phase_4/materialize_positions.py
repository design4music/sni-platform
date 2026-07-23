"""Materialize the position landing + detail blobs (SPEC v2 §5.5).

Backs /narratives (landing) and /narratives/[id] (position page). The position
is the narrative entity; narratives_v2 rows are its cards. Everything a page
needs is baked here so the frontend does PK JSONB lookups only.

  mv_positions_landing  : one row per locale  -> metas, positions, sparklines
  mv_position_detail    : one row per (position_id, locale) -> position, weekly
                          timeline, derived events, cards ("where it appears"),
                          sibling positions, cross-FN reach, primary_sources ([]).

Counts come from the derived event_positions table (title -> card -> position ->
event, per P2). Per-card match counts use narrative_counts.effective_counts so
theater cards roll up correctly. Coalition is derived at read time from card
publishers (never stored). 12h staleness gate; --force to rebuild.
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
# Local packages (core/, scripts/) are imported lazily inside the functions that
# use them -- they need ROOT on sys.path (above), and lazy imports keep the
# module-level import block clean for both standalone and daemon-package use.

DEFAULT_MAX_AGE_HOURS = 12
LOCALES = ("en", "de")
WEEKLY_DAYS = 90
EVENTS_LIMIT = 50
SIBLING_LIMIT = 10
KEYWORDS_CAP = 30


def get_connection():
    from core.config import config

    return psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)


# ---------- shared, locale-neutral fetches ----------


def centroid_labels(cur):
    cur.execute("SELECT id, label FROM centroids_v3")
    return {r["id"]: r["label"] for r in cur.fetchall()}


def position_counts(cur):
    """per position: distinct non-merged events, summed title links."""
    cur.execute(
        """
        SELECT ep.position_id,
               count(*)::int AS event_count,
               sum(ep.title_count)::int AS title_links
          FROM event_positions ep
          JOIN events_v3 ev ON ev.id = ep.event_id AND ev.merged_into IS NULL
         GROUP BY ep.position_id
    """
    )
    return {r["position_id"]: r for r in cur.fetchall()}


def position_weekly(cur):
    cur.execute(
        f"""
        SELECT ep.position_id,
               date_trunc('week', ev.date::date)::text AS week,
               sum(ep.title_count)::int AS count
          FROM event_positions ep
          JOIN events_v3 ev ON ev.id = ep.event_id AND ev.merged_into IS NULL
         WHERE ev.date >= NOW() - INTERVAL '{WEEKLY_DAYS} days'
         GROUP BY ep.position_id, week
         ORDER BY ep.position_id, week
    """
    )
    out = defaultdict(list)
    for r in cur.fetchall():
        out[r["position_id"]].append({"week": r["week"], "count": r["count"]})
    return out


def per_card_counts(cur):
    """effective attributed-title count per card (atomic direct + theater rollup)."""
    from scripts.narrative_counts import effective_counts

    cur.execute(
        """
        SELECT n.id, fn.fn_type, n.stance, n.publishers, fn.member_fn_ids
          FROM narratives_v2 n JOIN friction_nodes fn ON fn.id = n.fn_id
         WHERE n.is_active
    """
    )
    rows = [dict(r) for r in cur.fetchall()]
    return effective_counts(cur, rows)


def fetch_cards(cur, locale):
    """Position's cards ('where this position appears'), locale-aware FN name."""
    fn_name = "name_de" if locale == "de" else "name_en"
    st_label = "stance_label_de" if locale == "de" else "stance_label_en"
    cur.execute(
        f"""
        SELECT n.id, n.position_id, n.fn_id,
               COALESCE(fn.{fn_name}, fn.name_en) AS fn_name,
               fn.fn_type, n.stance,
               COALESCE(n.{st_label}, n.stance_label_en) AS stance_label,
               n.publishers, n.framing_keywords
          FROM narratives_v2 n
          JOIN friction_nodes fn ON fn.id = n.fn_id
         WHERE n.is_active AND n.position_id IS NOT NULL
         ORDER BY n.position_id
    """
    )
    return [dict(r) for r in cur.fetchall()]


def fetch_events(cur, locale):
    """Top EVENTS_LIMIT derived events per position, most-carrying first."""
    title = "COALESCE(ev.title_de, ev.title)" if locale == "de" else "ev.title"
    cur.execute(
        f"""
        WITH ranked AS (
          SELECT ep.position_id, ev.id::text AS event_id, ev.date::text AS date,
                 {title} AS title, ep.title_count,
                 ROW_NUMBER() OVER (PARTITION BY ep.position_id
                     ORDER BY ep.title_count DESC, ev.date DESC, ev.id) AS rnk
            FROM event_positions ep
            JOIN events_v3 ev ON ev.id = ep.event_id
           WHERE ev.merged_into IS NULL AND ev.title IS NOT NULL
        )
        SELECT position_id, event_id, date, title, title_count
          FROM ranked WHERE rnk <= {EVENTS_LIMIT}
         ORDER BY position_id, rnk
    """
    )
    out = defaultdict(list)
    for r in cur.fetchall():
        out[r["position_id"]].append(
            {
                "id": r["event_id"],
                "date": r["date"],
                "title": r["title"] or "",
                "title_count": r["title_count"],
            }
        )
    return out


def sibling_map(cur):
    """position -> [(sibling_id, shared_fn_count)], positions sharing an FN."""
    cur.execute(
        """
        WITH pf AS (
            SELECT DISTINCT position_id, fn_id FROM narratives_v2
             WHERE is_active AND position_id IS NOT NULL
        )
        SELECT a.position_id AS src, b.position_id AS sib, count(*)::int AS shared
          FROM pf a JOIN pf b ON a.fn_id = b.fn_id AND a.position_id <> b.position_id
         GROUP BY a.position_id, b.position_id
    """
    )
    out = defaultdict(list)
    for r in cur.fetchall():
        out[r["src"]].append((r["sib"], r["shared"]))
    for k in out:
        out[k].sort(key=lambda x: (-x[1], x[0]))
    return out


# ---------- assembly ----------


def build(cur):
    """Return {locale: (landing_view, {position_id: detail_view})}."""
    from scripts.narrative_coalitions import (
        domestic_fns,
    )
    from scripts.narrative_coalitions import load_registry as load_coalitions
    from scripts.narrative_coalitions import (
        publisher_countries,
    )
    from scripts.narrative_coalitions import resolve as coalition_resolve

    clabels = centroid_labels(cur)
    counts = position_counts(cur)
    weekly = position_weekly(cur)
    card_counts = per_card_counts(cur)
    siblings = sibling_map(cur)

    # coalition inputs (locale-neutral)
    iso2c, parents = load_coalitions()
    pub2c = publisher_countries(cur)
    fn_home = domestic_fns(cur)

    result = {}
    for locale in LOCALES:
        p_name = "name_de" if locale == "de" else "name_en"
        p_claim = "claim_de" if locale == "de" else "claim_en"
        m_name = "name_de" if locale == "de" else "name"
        cur.execute(
            f"""
            SELECT p.id, COALESCE(p.{p_name}, p.name_en) AS name,
                   COALESCE(p.{p_claim}, p.claim_en) AS claim, p.stance_sign,
                   p.meta_narrative_id, p.meta_secondary_ids, p.owner_centroids,
                   COALESCE(mn.{m_name}, mn.name) AS meta_name
              FROM positions p
              LEFT JOIN meta_narratives mn ON mn.id = p.meta_narrative_id
             WHERE p.is_active
             ORDER BY p.id
        """
        )
        positions = [dict(r) for r in cur.fetchall()]
        meta_names = {}
        cur.execute(f"SELECT id, COALESCE({m_name}, name) AS n FROM meta_narratives")
        for r in cur.fetchall():
            meta_names[r["id"]] = r["n"]

        cards = fetch_cards(cur, locale)
        events = fetch_events(cur, locale)

        # coalition per card, then per position
        coal = coalition_resolve(cards, pub2c, iso2c, parents, fn_home)
        cards_by_pos = defaultdict(list)
        for c in cards:
            cards_by_pos[c["position_id"]].append(c)

        landing_positions = []
        detail = {}
        for p in positions:
            pid = p["id"]
            pcards = cards_by_pos.get(pid, [])
            cnt = counts.get(pid, {"event_count": 0, "title_links": 0})
            owner = [
                {"id": o, "label": clabels.get(o, o)} for o in p["owner_centroids"]
            ]
            secondary = [
                {"id": m, "name": meta_names.get(m, m)} for m in p["meta_secondary_ids"]
            ]

            # coalitions carrying the position (distinct primaries across cards)
            coal_tally = defaultdict(int)
            for c in pcards:
                cc = coal.get(c["id"], {}).get("coalition")
                if cc and cc != "mixed":
                    coal_tally[cc] += 1
            coalitions = [
                {"coalition": k, "cards": v}
                for k, v in sorted(coal_tally.items(), key=lambda x: -x[1])
            ]

            # normative line = strongest card (most attributed titles)
            strongest = max(
                pcards,
                key=lambda c: (card_counts.get(c["id"], 0), abs(c["stance"] or 0)),
                default=None,
            )
            keywords = []
            seen = set()
            for c in sorted(pcards, key=lambda c: -card_counts.get(c["id"], 0)):
                for kw in c["framing_keywords"] or []:
                    k = kw.lower()
                    if k not in seen:
                        seen.add(k)
                        keywords.append(kw)
            keywords = keywords[:KEYWORDS_CAP]

            card_rows = [
                {
                    "id": c["id"],
                    "fn_id": c["fn_id"],
                    "fn_name": c["fn_name"],
                    "fn_type": c["fn_type"],
                    "stance": c["stance"],
                    "stance_label": c["stance_label"],
                    "match_count": card_counts.get(c["id"], 0),
                    "publisher_count": len(c["publishers"] or []),
                    "coalition": coal.get(c["id"], {}).get("coalition"),
                }
                for c in sorted(pcards, key=lambda c: -card_counts.get(c["id"], 0))
            ]

            base = {
                "id": pid,
                "name": p["name"],
                "claim": p["claim"],
                "stance_sign": p["stance_sign"],
                "meta_narrative_id": p["meta_narrative_id"],
                "meta_name": p["meta_name"],
                "meta_secondary": secondary,
                "owner_centroids": owner,
                "coalitions": coalitions,
                "event_count": cnt["event_count"],
                "title_count": cnt["title_links"],
                "card_count": len(pcards),
                "fn_count": len({c["fn_id"] for c in pcards}),
            }

            landing_positions.append(
                {
                    **base,
                    "normative_line": strongest["stance_label"] if strongest else None,
                }
            )

            sib_rows = []
            pos_by_id = {x["id"]: x for x in positions}
            for sib_id, shared in siblings.get(pid, [])[:SIBLING_LIMIT]:
                s = pos_by_id.get(sib_id)
                if not s:
                    continue
                sib_rows.append(
                    {
                        "id": sib_id,
                        "name": s["name"],
                        "claim": s["claim"],
                        "stance_sign": s["stance_sign"],
                        "meta_narrative_id": s["meta_narrative_id"],
                        "shared_fns": shared,
                    }
                )

            detail[pid] = {
                "position": {
                    **base,
                    "normative_line": strongest["stance_label"] if strongest else None,
                    "keywords": keywords,
                },
                "weekly_activity": weekly.get(pid, []),
                "events": events.get(pid, []),
                "cards": card_rows,
                "cross_fn_reach": {
                    "fn_count": base["fn_count"],
                    "per_fn": [
                        {
                            "fn_id": c["fn_id"],
                            "fn_name": c["fn_name"],
                            "match_count": c["match_count"],
                        }
                        for c in card_rows
                    ],
                },
                "siblings": sib_rows,
                "primary_sources": [],  # P7 (official documents) -- degrades to absent
            }

        # metas for the landing rail
        cur.execute(
            f"""
            SELECT id, COALESCE({m_name}, name) AS name,
                   COALESCE(description_de, description) AS description,
                   signals, sort_order
              FROM meta_narratives ORDER BY sort_order
        """
        )
        metas = [dict(r) for r in cur.fetchall()]

        landing = {
            "meta_narratives": metas,
            "positions": landing_positions,
            "sparklines": {p["id"]: weekly.get(p["id"], []) for p in positions},
        }
        result[locale] = (landing, detail)
    return result


def is_stale(cur, table, max_age_hours):
    cur.execute(
        f"SELECT EXTRACT(EPOCH FROM (NOW()-MAX(updated_at)))/3600 AS age FROM {table}"
    )
    row = cur.fetchone()
    age = row["age"] if row else None
    return age is None or age >= max_age_hours


def materialize(max_age_hours=DEFAULT_MAX_AGE_HOURS, force=False):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if not force and not is_stale(cur, "mv_position_detail", max_age_hours):
                print("Skipped: mv_position_detail fresh (gate=%.1fh)" % max_age_hours)
                return 0
            start = time.time()
            built = build(cur)

            execute_values(
                cur,
                """INSERT INTO mv_positions_landing (locale, view, updated_at)
                   VALUES %s ON CONFLICT (locale) DO UPDATE
                     SET view = EXCLUDED.view, updated_at = EXCLUDED.updated_at""",
                [(loc, json.dumps(landing)) for loc, (landing, _) in built.items()],
                template="(%s, %s::jsonb, NOW())",
            )
            detail_rows = [
                (pid, loc, json.dumps(view))
                for loc, (_, detail) in built.items()
                for pid, view in detail.items()
            ]
            execute_values(
                cur,
                """INSERT INTO mv_position_detail (position_id, locale, view, updated_at)
                   VALUES %s ON CONFLICT (position_id, locale) DO UPDATE
                     SET view = EXCLUDED.view, updated_at = EXCLUDED.updated_at""",
                detail_rows,
                template="(%s, %s, %s::jsonb, NOW())",
            )
            conn.commit()
            print(
                "Done: %d landing rows, %d detail rows (%.1fs)"
                % (len(built), len(detail_rows), time.time() - start)
            )
            return len(detail_rows)
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description="Materialize position landing + detail")
    ap.add_argument("--max-age-hours", type=float, default=DEFAULT_MAX_AGE_HOURS)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    materialize(max_age_hours=args.max_age_hours, force=args.force)


if __name__ == "__main__":
    main()
