"""P0(a) — mechanical archetype clustering over active narratives_v2.

NARRATIVE_CONSOLIDATION_SPEC.md 3.A3 step 1: collapse ~400 narratives into a
small number of recurring archetypes so the meta-narrative assignment is ~30
judgment calls instead of ~400.

Clustering signal is MEASURED, not invented. The spec's grouping key names
"actor_centroids overlap", but mapping centroids to bloc labels would be
authoring the coalition vocabulary -- that is DG-0 #2 (Maksim's call) and
Rule 5 (no hardcoded taxonomies). So the bloc dimension here is derived from
publisher-set overlap, which is corpus data: two narratives carried by the
same outlets are empirically the same bloc, whatever we end up calling it.

An archetype = (publisher bloc, stance sign). Reported with the regions and
friction nodes it spans, so a human can name it and assign a meta.

Read-only. Writes a markdown report, touches no table.

Usage:
  python scripts/narrative_archetype_clustering.py
  python scripts/narrative_archetype_clustering.py --threshold 0.45
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config  # noqa: E402

OUT = (
    Path(__file__).parent.parent
    / "out"
    / "narrative_consolidation"
    / "P0a_archetypes.md"
)
DEFAULT_THRESHOLD = 0.45
MIN_PUBLISHERS = 3  # below this a publisher set is too thin to cluster on


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="average-linkage Jaccard threshold for merging blocs",
    )
    return p.parse_args()


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cluster(items: dict[str, set], threshold: float) -> list[list[str]]:
    """Agglomerative average-linkage on Jaccard. Small N, so O(n^3) is fine
    and avoids adding a scipy/sklearn dependency for one report."""
    clusters = [[k] for k in items]
    while True:
        best = (threshold, None, None)
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                sims = [
                    jaccard(items[a], items[b])
                    for a in clusters[i]
                    for b in clusters[j]
                ]
                avg = sum(sims) / len(sims)
                if avg > best[0]:
                    best = (avg, i, j)
        if best[1] is None:
            return clusters
        _, i, j = best
        clusters[i] = clusters[i] + clusters[j]
        del clusters[j]


def main():
    args = parse_args()
    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute(
        """SELECT n.id, n.fn_id, n.stance, n.name_en, n.claim_en,
                  n.publishers, n.actor_centroids,
                  f.fn_type, f.centroid_ids[1] AS region
             FROM narratives_v2 n
             JOIN friction_nodes f ON f.id = n.fn_id
            WHERE n.is_active AND f.is_active
            ORDER BY n.fn_id, n.display_order"""
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    pubs = {r["id"]: set(r["publishers"] or []) for r in rows}
    by_id = {r["id"]: r for r in rows}

    thick = {k: v for k, v in pubs.items() if len(v) >= MIN_PUBLISHERS}
    thin = [k for k in pubs if k not in thick]

    blocs = cluster(thick, args.threshold)
    blocs.sort(key=len, reverse=True)

    # archetype = (bloc index, stance sign)
    arche = defaultdict(list)
    for bi, members in enumerate(blocs):
        for nid in members:
            s = by_id[nid]["stance"] or 0
            arche[(bi, (s > 0) - (s < 0))].append(nid)

    L = []
    L.append("# P0(a) — Narrative archetype clustering")
    L.append("")
    L.append(
        "Artifact for `NARRATIVE_CONSOLIDATION_SPEC.md` §3.A3 step 1, feeding **DG-0 #1**."
    )
    L.append("Read-only; nothing was written to the database.")
    L.append("")
    L.append(
        "**Method.** Narratives are clustered by *measured publisher-set overlap* "
        "(average-linkage Jaccard, threshold %.2f), not by an invented bloc "
        "vocabulary — naming coalitions is DG-0 #2. An **archetype** is then "
        "(publisher bloc x stance sign). Assign one meta-narrative per archetype "
        "below; that is the ~%d judgment calls the spec asks for, instead of %d."
        % (args.threshold, len(arche), len(rows))
    )
    L.append("")
    L.append(
        "> Title/match counts are deliberately omitted: a full attribution rebuild "
        "was in flight when this ran, so any count here would be a moving target. "
        "Thin-narrative triage (P0c) must run after that completes."
    )
    L.append("")
    L.append("| | |")
    L.append("|---|---|")
    L.append("| active narratives | %d |" % len(rows))
    L.append("| clustered (>= %d publishers) | %d |" % (MIN_PUBLISHERS, len(thick)))
    L.append("| too thin to cluster | %d |" % len(thin))
    L.append("| publisher blocs found | %d |" % len(blocs))
    L.append("| **archetypes (bloc x sign)** | **%d** |" % len(arche))
    L.append("")
    L.append("---")
    L.append("")
    L.append("## Archetypes")
    L.append("")
    L.append(
        "Each row is one assignment decision. `meta:` is left blank for you to fill."
    )
    L.append("")

    sign_name = {1: "supportive (+)", 0: "neutral (0)", -1: "critical (-)"}
    order = sorted(arche.items(), key=lambda kv: -len(kv[1]))
    for (bi, sign), members in order:
        regions = Counter(by_id[m]["region"] for m in members)
        fns = Counter(by_id[m]["fn_id"] for m in members)
        allpubs = Counter(p for m in members for p in pubs[m])
        L.append(
            "### A%02d — bloc %d, %s — %d narratives"
            % (
                order.index(((bi, sign), members)) + 1,
                bi,
                sign_name[sign],
                len(members),
            )
        )
        L.append("")
        L.append(
            "- **top publishers**: %s"
            % ", ".join("%s (%d)" % (p, c) for p, c in allpubs.most_common(8))
        )
        L.append(
            "- **regions**: %s"
            % ", ".join("%s (%d)" % (r, c) for r, c in regions.most_common(6))
        )
        L.append(
            "- **friction nodes**: %d distinct — %s"
            % (len(fns), ", ".join(f for f, _ in fns.most_common(6)))
        )
        L.append("- `meta:` _______________")
        L.append("")
        L.append("<details><summary>%d narratives</summary>" % len(members))
        L.append("")
        for m in sorted(members, key=lambda x: by_id[x]["fn_id"]):
            r = by_id[m]
            L.append(
                "- `%s` (%s, stance %+d) — %s"
                % (m, r["fn_id"], r["stance"] or 0, (r["name_en"] or "")[:90])
            )
        L.append("")
        L.append("</details>")
        L.append("")

    if thin:
        L.append("---")
        L.append("")
        L.append(
            "## Unclustered — fewer than %d publishers (%d)"
            % (MIN_PUBLISHERS, len(thin))
        )
        L.append("")
        L.append(
            "These need individual assignment, or are candidates for the "
            "thin-narrative triage in P0(c)."
        )
        L.append("")
        for m in sorted(thin, key=lambda x: by_id[x]["fn_id"]):
            r = by_id[m]
            L.append(
                "- `%s` (%s, stance %+d, %d pubs) — %s"
                % (
                    m,
                    r["fn_id"],
                    r["stance"] or 0,
                    len(pubs[m]),
                    (r["name_en"] or "")[:80],
                )
            )
        L.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L), encoding="utf-8")
    print("active narratives : %d" % len(rows))
    print("publisher blocs   : %d" % len(blocs))
    print("ARCHETYPES        : %d  <- decisions needed at DG-0" % len(arche))
    print("unclustered (thin): %d" % len(thin))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
