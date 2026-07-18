"""Dry-run preview: simulate title-narrative attribution using fn_anchor bundles.

Reads:
  - fn_anchor bundles from taxonomy_v3 (the new vocabulary built in Phase 2)
  - narratives_v2.framing_keywords / publishers / editorial_organ_publishers
    (still the old TEXT[] columns — narrative_anchor bundles not built yet)
  - friction_node_narratives for FN ↔ narrative links

Simulates the same attribution gates as scripts/bootstrap_friction_node.py
WITHOUT writing anything. Outputs a markdown table comparing simulated new
counts to current title_narratives counts.

Usage:
    python scripts/preview_fn_anchor_attribution.py --window-days 365
    python scripts/preview_fn_anchor_attribution.py --window-days 180 --fn iran_nuclear_program
"""

import argparse
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.config import config  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--window-days", type=int, default=365)
    p.add_argument(
        "--fn", help="Limit to one fn_id (default: all FNs with fn_anchor bundles)"
    )
    return p.parse_args()


def fetch_fn_anchor_bundles(cur):
    """fn_id -> flat list of unique aliases across all 10 languages."""
    cur.execute(
        """
        SELECT linked_id, aliases
        FROM taxonomy_v3
        WHERE taxonomy_function = 'fn_anchor' AND is_active = true
        """
    )
    out = {}
    for row in cur.fetchall():
        seen = set()
        flat = []
        for lang_aliases in (row["aliases"] or {}).values():
            for a in lang_aliases or []:
                if a and a not in seen:
                    seen.add(a)
                    flat.append(a)
        out[row["linked_id"]] = flat
    return out


def fetch_narratives_with_fn_links(cur):
    """narrative_id -> {name, type, framing, publishers, organs, linked_fn_ids: [...]}"""
    cur.execute(
        """
        SELECT n.id, n.narrative_type, n.framing_keywords, n.publishers,
               n.editorial_organ_publishers,
               array_agg(fnn.fn_id ORDER BY fnn.fn_id) AS fn_ids
        FROM narratives_v2 n
        JOIN friction_node_narratives fnn ON fnn.narrative_id = n.id
        WHERE n.is_active = true
        GROUP BY n.id, n.narrative_type, n.framing_keywords, n.publishers, n.editorial_organ_publishers
        """
    )
    return {r["id"]: r for r in cur.fetchall()}


def fetch_fn_actor_scope(cur):
    """fn_id -> centroid_ids[] (the narrow actor scope used for the attribution gate)."""
    cur.execute("SELECT id, centroid_ids FROM friction_nodes WHERE is_active = true")
    return {r["id"]: (r["centroid_ids"] or []) for r in cur.fetchall()}


def fetch_current_counts(cur):
    cur.execute(
        """
        SELECT narrative_id, COUNT(*) AS n
        FROM title_narratives
        GROUP BY narrative_id
        """
    )
    return {r["narrative_id"]: r["n"] for r in cur.fetchall()}


def simulate_count(cur, narrative, fn_anchor_terms, actor_scope, window_days):
    """Simulated title count for this narrative — runs the same gates as bootstrap
    plus the new centroid-scope gate: title.centroid_ids must overlap the union
    of actor_scope (the centroid_ids of every FN linking this narrative).
    """
    publishers = narrative["publishers"] or []
    framing = narrative["framing_keywords"] or []
    organs = narrative["editorial_organ_publishers"] or []
    is_all_in = narrative["narrative_type"] == "all_in"
    if not publishers or not fn_anchor_terms or not actor_scope:
        return 0

    cur.execute(
        """
        SELECT COUNT(*) AS n
        FROM titles_v3 t
        WHERE t.publisher_name = ANY(%(publishers)s)
          AND t.pubdate_utc > NOW() - (%(window)s || ' days')::interval
          AND t.centroid_ids && %(actor_scope)s::text[]
          AND EXISTS (
            SELECT 1 FROM unnest(%(fn_anchor)s::text[]) kw
            WHERE t.title_display ILIKE '%%' || kw || '%%'
          )
          AND (
            %(is_all_in)s
            OR t.publisher_name = ANY(%(organs)s)
            OR EXISTS (
              SELECT 1 FROM unnest(%(framing)s::text[]) kw
              WHERE t.title_display ILIKE '%%' || kw || '%%'
            )
          )
        """,
        {
            "publishers": publishers,
            "window": str(window_days),
            "actor_scope": actor_scope,
            "fn_anchor": fn_anchor_terms,
            "is_all_in": is_all_in,
            "organs": organs,
            "framing": framing,
        },
    )
    return cur.fetchone()["n"]


def main():
    args = parse_args()
    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            bundles = fetch_fn_anchor_bundles(cur)
            print(f"# fn_anchor bundles available: {sorted(bundles.keys())}")
            print(
                "# bundle sizes (aliases): "
                + ", ".join(f"{k}={len(v)}" for k, v in sorted(bundles.items()))
            )

            narratives = fetch_narratives_with_fn_links(cur)
            current = fetch_current_counts(cur)
            fn_scope = fetch_fn_actor_scope(cur)

            # Build narrative_id -> union of fn_anchor aliases across all FNs linking this narrative
            narr_anchor_union = {}
            narr_scope_union = {}
            for nid, n in narratives.items():
                seen = set()
                union = []
                scope_seen = set()
                scope_union = []
                for fn_id in n["fn_ids"] or []:
                    if fn_id in bundles:
                        for term in bundles[fn_id]:
                            if term not in seen:
                                seen.add(term)
                                union.append(term)
                    for centroid in fn_scope.get(fn_id, []):
                        if centroid not in scope_seen:
                            scope_seen.add(centroid)
                            scope_union.append(centroid)
                narr_anchor_union[nid] = union
                narr_scope_union[nid] = scope_union

            # If --fn given, filter to narratives linked to that FN
            scope_narratives = sorted(narratives.keys())
            if args.fn:
                scope_narratives = [
                    n
                    for n in scope_narratives
                    if args.fn in (narratives[n]["fn_ids"] or [])
                ]
                print(f"# filtered to FN {args.fn}: {len(scope_narratives)} narratives")

            print()
            print(
                "| narrative | type | FNs | pubs | terms | framing | scope | current | new | delta |"
            )
            print("|---|---|---|---|---|---|---|---|---|---|")
            for nid in scope_narratives:
                n = narratives[nid]
                pub_count = len(n["publishers"] or [])
                framing_count = len(n["framing_keywords"] or [])
                union_count = len(narr_anchor_union[nid])
                scope = narr_scope_union[nid]
                scope_label = ",".join(scope) if scope else "—"
                cur_count = current.get(nid, 0)
                if union_count == 0 or not scope:
                    new_count = "—"
                    delta = "no fn_anchor" if union_count == 0 else "no scope"
                else:
                    new_count_int = simulate_count(
                        cur, n, narr_anchor_union[nid], scope, args.window_days
                    )
                    delta = f"{new_count_int - cur_count:+d}"
                    new_count = str(new_count_int)
                fn_list = ",".join(n["fn_ids"] or [])
                print(
                    f"| {nid} | {n['narrative_type']} | {fn_list} | {pub_count} | {union_count} | {framing_count} | {scope_label} | {cur_count} | {new_count} | {delta} |"
                )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
