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
  friction_nodes.event_actor_markers / event_topic_markers / event_title_anchors
    Event-FN gate. An event qualifies if its canonical title matches:
      (any actor) AND (any topic) OR (any anchor)

  narratives_v2.publishers
    Outlets editorially aligned with the narrative.

  narratives_v2.narrative_type ('all_in' | 'stand_by')
    all_in: publisher-stance is sufficient, no framing-keyword check.
    stand_by: framing-keyword check applies UNLESS publisher is in
              narratives_v2.editorial_organ_publishers (intrinsic-stance
              outlets like RT/TASS/Xinhua).

  narratives_v2.framing_keywords / topic_keywords
    Framing-keyword evidence for stand-by-non-organ publisher matches.
    Topic-keyword check ensures the title is FN-relevant.

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
        """SELECT id, name_en,
                  topic_keywords,
                  event_actor_markers, event_topic_markers, event_title_anchors
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
        """SELECT n.id, n.name_en, n.narrative_type,
                  n.publishers, n.framing_keywords, n.topic_keywords,
                  n.editorial_organ_publishers
             FROM narratives_v2 n
             JOIN friction_node_narratives fnn ON fnn.narrative_id = n.id
            WHERE fnn.fn_id = %s AND n.is_active = true
            ORDER BY fnn.display_order""",
        (fn_id,),
    )
    return cur.fetchall()


def link_events(cur, fn: dict, window_days: int) -> int:
    """Apply the FN's event-title gate to populate event_friction_nodes."""
    actor_markers = fn["event_actor_markers"] or []
    topic_markers = fn["event_topic_markers"] or []
    title_anchors = fn["event_title_anchors"] or []

    if not (actor_markers or topic_markers or title_anchors):
        raise SystemExit(
            f"FN {fn['id']} has no event-title gate configured "
            "(event_actor_markers / event_topic_markers / event_title_anchors all empty)"
        )

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
              AND (
                (
                  EXISTS (SELECT 1 FROM unnest(%(actor)s::text[]) kw
                           WHERE e.title ILIKE '%%' || kw || '%%')
                  AND
                  EXISTS (SELECT 1 FROM unnest(%(topic)s::text[]) kw
                           WHERE e.title ILIKE '%%' || kw || '%%')
                )
                OR EXISTS (SELECT 1 FROM unnest(%(anchor)s::text[]) kw
                            WHERE e.title ILIKE '%%' || kw || '%%')
              )
           ON CONFLICT (event_id, fn_id) DO NOTHING""",
        {
            "fn_id": fn["id"],
            "window": str(window_days),
            "actor": actor_markers,
            "topic": topic_markers,
            "anchor": title_anchors,
        },
    )
    return cur.rowcount


def link_titles(
    cur, fn: dict, narratives: list[dict], window_days: int
) -> dict[str, int]:
    """Apply per-narrative title attribution rules.

    Each narrative's titles must:
      - come from a publisher in narrative.publishers
      - mention a topic_keyword from ANY FN this narrative is linked to
        (union, not just the FN being bootstrapped — otherwise re-running
        bootstrap on FN_X clobbers attributions earned through FN_Y for
        cross-FN narratives like multipolar / EU diplomacy / proxy axis).
      - either: narrative is all_in, OR publisher is in
        editorial_organ_publishers, OR title matches a framing keyword.
    """
    fn_topic = fn["topic_keywords"] or []
    if not fn_topic:
        raise SystemExit(
            f"FN {fn['id']} has no topic_keywords; cannot scope title attribution"
        )

    narrative_ids = [n["id"] for n in narratives]
    if not narrative_ids:
        return {}

    # Union of topic_keywords across every FN each narrative is linked to.
    # One query — fetch all FNs that link these narratives, then aggregate.
    cur.execute(
        """SELECT fnn.narrative_id, fn.topic_keywords
           FROM friction_node_narratives fnn
           JOIN friction_nodes fn ON fn.id = fnn.fn_id
           WHERE fnn.narrative_id = ANY(%s)
             AND fn.is_active = true
             AND fn.topic_keywords IS NOT NULL""",
        (narrative_ids,),
    )
    union_by_narrative: dict[str, set[str]] = {nid: set() for nid in narrative_ids}
    for row in cur.fetchall():
        nid = row["narrative_id"]
        for kw in row["topic_keywords"] or []:
            union_by_narrative[nid].add(kw)

    cur.execute(
        "DELETE FROM title_narratives WHERE narrative_id = ANY(%s)",
        (narrative_ids,),
    )

    counts: dict[str, int] = {}
    for n in narratives:
        publishers = n["publishers"] or []
        framing = n["framing_keywords"] or []
        organs = n["editorial_organ_publishers"] or []
        is_all_in = n["narrative_type"] == "all_in"
        topic_union = sorted(union_by_narrative.get(n["id"], set())) or fn_topic

        if not publishers:
            counts[n["id"]] = 0
            continue

        # Build the per-narrative INSERT.
        # Stand_by narratives that have NO framing keywords but DO have
        # editorial organs would only attach via the organ exception.
        # Stand_by with no organs and no framing = effectively zero matches
        # (publisher gates exist but framing always fails).
        cur.execute(
            """INSERT INTO title_narratives (title_id, narrative_id)
               SELECT t.id, %(narrative_id)s
                 FROM titles_v3 t
                WHERE t.publisher_name = ANY(%(publishers)s)
                  AND t.pubdate_utc > NOW() - (%(window)s || ' days')::interval
                  AND EXISTS (SELECT 1 FROM unnest(%(fn_topic)s::text[]) kw
                               WHERE t.title_display ILIKE '%%' || kw || '%%')
                  AND (
                       %(is_all_in)s
                    OR t.publisher_name = ANY(%(organs)s)
                    OR EXISTS (SELECT 1 FROM unnest(%(framing)s::text[]) kw
                                WHERE t.title_display ILIKE '%%' || kw || '%%')
                  )
               ON CONFLICT (title_id, narrative_id) DO NOTHING""",
            {
                "narrative_id": n["id"],
                "publishers": publishers,
                "window": str(window_days),
                "fn_topic": topic_union,
                "is_all_in": is_all_in,
                "organs": organs,
                "framing": framing,
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
                organs = len(n["editorial_organ_publishers"] or [])
                framing = len(n["framing_keywords"] or [])
                print(
                    f"  - {n['id']} [{n['narrative_type']}] "
                    f"pubs={pubs} organs={organs} framing={framing}"
                )

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
