"""Per-alias precision audit for an FN's fn_anchor bundle. Read-only.

For each alias in a friction node's fn_anchor bundle, this measures -- against
REAL headlines, using the exact match semantics of bootstrap_friction_node.py --
how many titles it pulls into the FN's centroid scope and what centroids those
titles carry. Aliases whose matches are dominated by centroids OUTSIDE the FN's
own scope (or by a foreign theater's centroid) are cross-theater leak candidates.

General and FN-agnostic: same tool for every theater's atomics. Drives the
"less but better" pruning pass with data instead of intuition.

Usage:
  python scripts/audit_fn_anchor_aliases.py --fn-id ukraine_infrastructure_war
  python scripts/audit_fn_anchor_aliases.py --fn-id ukraine_battlefield --window-days 180
  python scripts/audit_fn_anchor_aliases.py --fn-id ukraine_battlefield --min-n 1 --samples 2
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config
from scripts.bootstrap_friction_node import (
    ALIAS_MATCH_EN_SQL,
    ALIAS_MATCH_OTHER_SQL,
    flatten_aliases,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fn-id", required=True)
    p.add_argument("--window-days", type=int, default=180)
    p.add_argument("--samples", type=int, default=3, help="sample titles per alias")
    p.add_argument(
        "--min-n", type=int, default=0, help="hide aliases matching < N titles"
    )
    return p.parse_args()


def region_of(centroid: str) -> str:
    return centroid.split("-", 1)[0] if centroid else "?"


def audit_alias(
    cur, kw: str, match_sql: str, centroids: list[str], window: int, samples: int
):
    cur.execute(
        f"""
        SELECT t.title_display, t.centroid_ids
        FROM titles_v3 t, LATERAL (SELECT %(kw)s::text AS kw) k
        WHERE t.centroid_ids && %(centroids)s::text[]
          AND t.pubdate_utc > NOW() - (%(window)s || ' days')::interval
          AND {match_sql}
        """,
        {"kw": kw, "centroids": centroids, "window": str(window)},
    )
    rows = cur.fetchall()
    n = len(rows)
    own = set(centroids)
    own_regions = {region_of(c) for c in own}
    # A match is "extra" if it carries any centroid outside the FN's own scope;
    # "foreign" (stronger signal) if it carries a centroid from a region the FN
    # doesn't belong to at all.
    extra = Counter()
    n_foreign = 0
    for r in rows:
        cids = r["centroid_ids"] or []
        for c in cids:
            if c not in own:
                extra[c] += 1
        if any(region_of(c) not in own_regions for c in cids):
            n_foreign += 1
    sample = [r["title_display"] for r in rows[:samples]]
    return {
        "n": n,
        "pct_foreign": (100 * n_foreign / n) if n else 0.0,
        "top_extra": extra.most_common(4),
        "sample": sample,
    }


def main() -> None:
    args = parse_args()
    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name_en, centroid_ids, primary_target FROM friction_nodes WHERE id = %s",
                (args.fn_id,),
            )
            fn = cur.fetchone()
            if not fn:
                raise SystemExit(f"FN {args.fn_id} not found")
            centroids = fn["centroid_ids"] or []
            cur.execute(
                """SELECT aliases FROM taxonomy_v3
                   WHERE taxonomy_function='fn_anchor' AND linked_id=%s AND is_active=true""",
                (args.fn_id,),
            )
            row = cur.fetchone()
            en_aliases, other_aliases = flatten_aliases(row["aliases"] if row else None)

            print(f"# fn_anchor alias audit: {fn['id']} ({fn['name_en']})")
            print(
                f"# scope centroids: {centroids}  primary_target: {fn['primary_target']}"
            )
            print(
                f"# window: {args.window_days}d   en={len(en_aliases)} other={len(other_aliases)}"
            )
            print()

            results = []
            for kw in en_aliases:
                r = audit_alias(
                    cur,
                    kw,
                    ALIAS_MATCH_EN_SQL,
                    centroids,
                    args.window_days,
                    args.samples,
                )
                results.append(("en", kw, r))
            for kw in other_aliases:
                r = audit_alias(
                    cur,
                    kw,
                    ALIAS_MATCH_OTHER_SQL,
                    centroids,
                    args.window_days,
                    args.samples,
                )
                results.append(("other", kw, r))

            # Rank: highest foreign-pull first (leak candidates), then by volume.
            results.sort(key=lambda x: (x[2]["pct_foreign"], x[2]["n"]), reverse=True)

            print("| lang | alias | n | %foreign | top extra centroids |")
            print("|---|---|---|---|---|")
            for lang, kw, r in results:
                if r["n"] < args.min_n:
                    continue
                extra = " ".join(f"{c}:{cnt}" for c, cnt in r["top_extra"]) or "-"
                print(
                    f"| {lang} | `{kw}` | {r['n']} | {r['pct_foreign']:.0f}% | {extra} |"
                )

            print("\n## Samples for high-foreign / high-volume aliases\n")
            for lang, kw, r in results:
                if r["n"] < max(args.min_n, 1):
                    continue
                if r["pct_foreign"] < 25 and r["n"] < 40:
                    continue
                print(f"- **`{kw}`** (n={r['n']}, foreign={r['pct_foreign']:.0f}%)")
                for s in r["sample"]:
                    print(f"    - {s}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
