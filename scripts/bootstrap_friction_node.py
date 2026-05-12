"""Friction-node attribution bootstrap.

Populates event_friction_nodes + title_narratives for a single friction
node, reading all per-FN configuration from the database. NOT pipeline-
integrated — this is curation infrastructure, run interactively when:
  - a new friction node is added
  - a friction node's narratives or publishers change materially
  - keyword tuning lands on a related narrative

Usage:
  python scripts/bootstrap_friction_node.py --fn-id iran_nuclear_program
  python scripts/bootstrap_friction_node.py --fn-id iran_nuclear_program --window-days 90

Inputs read from DB:
  friction_nodes.centroid_ids
    Default actor-scope for event + title attribution.

  taxonomy_v3 (taxonomy_function='fn_anchor', linked_id=fn.id)
    Multi-lingual alias bundle used as the topic gate.

  narratives_v2  (1-to-1 with friction_nodes via fn_id)
    Per-narrative attribution rule: publisher cohort, framing-keyword
    fingerprint, and optional scope_centroid_ids override.

Side effects:
  - DELETEs all existing event_friction_nodes rows for the FN
  - DELETEs all existing title_narratives rows for the FN's narratives
  - INSERTs the new attribution sets
  - Idempotent: re-runs produce the same result
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--fn-id", required=True, help="friction_nodes.id")
    p.add_argument(
        "--window-days",
        type=int,
        default=180,
        help="title + event window for attribution (default 180)",
    )
    return p.parse_args()


def fetch_fn(cur, fn_id: str) -> dict:
    cur.execute(
        """SELECT id, name_en, fn_type, centroid_ids
             FROM friction_nodes
            WHERE id = %s AND is_active = true""",
        (fn_id,),
    )
    row = cur.fetchone()
    if not row:
        raise SystemExit(f"friction_node id={fn_id} not found or inactive")
    return row


def fetch_narratives(cur, fn_id: str) -> list[dict]:
    cur.execute(
        """SELECT id, name_en, publishers, framing_keywords, scope_centroid_ids
             FROM narratives_v2
            WHERE fn_id = %s AND is_active = true
            ORDER BY display_order""",
        (fn_id,),
    )
    return cur.fetchall()


def link_events(cur, fn: dict, window_days: int) -> int:
    """Apply the FN's event gate to populate event_friction_nodes.

    Uses the same shape as title attribution:
      - centroid scope: ANY member title of the event must overlap fn.centroid_ids
      - topic gate: event canonical title matches any fn_anchor bundle alias
    """
    fn_centroid_ids = fn["centroid_ids"] or []
    if not fn_centroid_ids:
        raise SystemExit(
            f"FN {fn['id']} has no centroid_ids configured; cannot scope event attribution"
        )

    # Fetch the fn_anchor bundle aliases (flattened across all 10 languages).
    cur.execute(
        """SELECT aliases FROM taxonomy_v3
           WHERE taxonomy_function = 'fn_anchor'
             AND linked_id = %s
             AND is_active = true""",
        (fn["id"],),
    )
    row = cur.fetchone()
    aliases: list[str] = []
    seen: set[str] = set()
    if row and row["aliases"]:
        for lang_aliases in row["aliases"].values():
            for a in lang_aliases or []:
                if a and a not in seen:
                    seen.add(a)
                    aliases.append(a)
    if not aliases:
        raise SystemExit(f"FN {fn['id']} has no fn_anchor bundle in taxonomy_v3")

    cur.execute(
        "DELETE FROM event_friction_nodes WHERE fn_id = %s",
        (fn["id"],),
    )

    cur.execute(
        """INSERT INTO event_friction_nodes (event_id, fn_id)
           SELECT e.id, %(fn_id)s
             FROM events_v3 e
            WHERE e.is_promoted = true
              AND e.merged_into IS NULL
              AND e.date > (CURRENT_DATE - (%(window)s || ' days')::interval)
              AND EXISTS (
                SELECT 1 FROM event_v3_titles et
                JOIN titles_v3 t ON t.id = et.title_id
                WHERE et.event_id = e.id
                  AND t.centroid_ids && %(centroids)s::text[]
              )
              AND EXISTS (
                SELECT 1 FROM unnest(%(aliases)s::text[]) kw
                WHERE e.title ILIKE '%%' || kw || '%%'
              )
           ON CONFLICT (event_id, fn_id) DO NOTHING""",
        {
            "fn_id": fn["id"],
            "window": str(window_days),
            "centroids": fn_centroid_ids,
            "aliases": aliases,
        },
    )
    return cur.rowcount


def link_titles(
    cur, fn: dict, narratives: list[dict], window_days: int
) -> dict[str, int]:
    """Apply per-narrative title attribution rules.

    Each narrative's titles must:
      - come from a publisher in narrative.publishers
      - mention any alias from the FN's fn_anchor bundle in taxonomy_v3
      - have centroid_ids overlapping narrative.scope_centroid_ids
        (or fn.centroid_ids when the narrative has no override)

    For fn_type='theater' (catch-all), titles already attributed to any
    atomic FN are excluded — atomic FNs claim their content first.
    """
    narrative_ids = [n["id"] for n in narratives]
    if not narrative_ids:
        return {}

    # FN-level alias bundle (taxonomy_v3 fn_anchor row for this FN).
    cur.execute(
        """SELECT aliases FROM taxonomy_v3
           WHERE taxonomy_function = 'fn_anchor'
             AND linked_id = %s
             AND is_active = true""",
        (fn["id"],),
    )
    row = cur.fetchone()
    aliases: list[str] = []
    seen: set[str] = set()
    if row and row["aliases"]:
        for lang_aliases in row["aliases"].values():
            for a in lang_aliases or []:
                if a and a not in seen:
                    seen.add(a)
                    aliases.append(a)

    cur.execute(
        "DELETE FROM title_narratives WHERE narrative_id = ANY(%s)",
        (narrative_ids,),
    )

    is_theater = fn.get("fn_type") == "theater"
    counts: dict[str, int] = {}
    for n in narratives:
        publishers = n["publishers"] or []
        framing = n["framing_keywords"] or []
        centroids = n["scope_centroid_ids"] or fn["centroid_ids"] or []

        if not publishers or not aliases or not centroids:
            counts[n["id"]] = 0
            continue

        cur.execute(
            """INSERT INTO title_narratives (title_id, narrative_id)
               SELECT t.id, %(narrative_id)s
                 FROM titles_v3 t
                WHERE t.publisher_name = ANY(%(publishers)s)
                  AND t.pubdate_utc > NOW() - (%(window)s || ' days')::interval
                  AND t.centroid_ids && %(centroids)s::text[]
                  AND EXISTS (SELECT 1 FROM unnest(%(aliases)s::text[]) kw
                               WHERE t.title_display ILIKE '%%' || kw || '%%')
                  AND (
                       cardinality(%(framing)s::text[]) = 0
                    OR EXISTS (SELECT 1 FROM unnest(%(framing)s::text[]) kw
                                WHERE t.title_display ILIKE '%%' || kw || '%%')
                  )
                  AND (NOT %(is_theater)s OR NOT EXISTS (
                      SELECT 1
                        FROM title_narratives tn2
                        JOIN narratives_v2 n2 ON n2.id = tn2.narrative_id
                        JOIN friction_nodes fn2 ON fn2.id = n2.fn_id
                       WHERE tn2.title_id = t.id
                         AND fn2.fn_type = 'atomic'
                  ))
               ON CONFLICT (title_id, narrative_id) DO NOTHING""",
            {
                "narrative_id": n["id"],
                "publishers": publishers,
                "window": str(window_days),
                "centroids": list(centroids),
                "aliases": aliases,
                "framing": framing,
                "is_theater": is_theater,
            },
        )
        counts[n["id"]] = cur.rowcount

    return counts


def main() -> None:
    args = parse_args()
    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            fn = fetch_fn(cur, args.fn_id)
            print(f"FN: {fn['id']} ({fn['name_en']})")

            narratives = fetch_narratives(cur, args.fn_id)
            print(f"Narratives linked: {len(narratives)}")
            for n in narratives:
                pubs = len(n["publishers"] or [])
                framing = len(n["framing_keywords"] or [])
                scope = "scoped" if n["scope_centroid_ids"] else "inherits-fn"
                print(f"  - {n['id']} pubs={pubs} framing={framing} [{scope}]")

            if fn.get("fn_type") == "theater":
                # Theaters have no event markers (events live on the atomic FNs
                # they group). Title attribution still happens via the theater's
                # narratives + bundle.
                print("\nfn_type=theater — skipping event_friction_nodes step.")
            else:
                n_events = link_events(cur, fn, args.window_days)
                print(f"\nevent_friction_nodes inserted: {n_events}")

            counts = link_titles(cur, fn, narratives, args.window_days)
            print("title_narratives inserted:")
            for nid, c in counts.items():
                print(f"  - {nid}: {c}")

        conn.commit()
        print("\nCommitted.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
