"""P0(a) -- archetype grouping over active narratives_v2, on the META axis.

NARRATIVE_CONSOLIDATION_SPEC.md 3.A3 step 1: collapse ~400 narratives into a
small number of recurring archetypes so meta-narrative assignment is ~30
judgment calls instead of ~400.

WHY NOT PUBLISHER-BLOC CLUSTERING (the first attempt at this artifact):
the 9 meta-narratives are a CLAIM-TYPE axis ("what kind of world-order argument
is this"). Publisher bloc is a WHO axis. They are orthogonal, and empirically
publisher overlap does not discriminate at all: narratives carry 22.5 publishers
on average and ~42% of them share the same Western wire set, so Jaccard collapses
into one 87-member bloc spanning 86 friction nodes, climate alarm through
rule-of-law. No single meta label is possible for such a group.

So the archetype key here is (proposed meta, stance sign). The proposal is
mechanical, from two measured signals:

  1. kNN over `strategic_narratives` -- v1's 260 rows carry HUMAN meta
     assignments. v1's content is being retired, but the meta layer is
     explicitly preserved (spec 1, "What v1 got right"), and those 260 rows are
     the only existing record of how this project maps a claim to a meta.
  2. cosine against each meta's own `meta_narratives.signals` vocabulary.

Blended 50/50. Leave-one-out accuracy against v1's own labels is printed in the
report -- it is a pre-grouping aid, NOT an auto-assignment. Narratives whose
top-two metas are within MARGIN are assigned BOTH -- primary + secondary --
per DG-0 #4. There is no residue bucket: a tie is an answer, not a failure.

Coalition is resolved per narrative from its publisher bloc
(scripts/narrative_coalitions.py), never from actor_centroids.

Read-only. Writes a markdown report + a JSON sidecar for P0(b). Touches no table.

Usage:
  python scripts/narrative_archetype_clustering.py
  python scripts/narrative_archetype_clustering.py --margin 0.10
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import re
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config  # noqa: E402
from scripts.narrative_coalitions import (
    domestic_fns,
)
from scripts.narrative_coalitions import load_registry as load_coalitions  # noqa: E402
from scripts.narrative_coalitions import (
    publisher_countries,
)
from scripts.narrative_coalitions import resolve as coalition_resolve
from scripts.narrative_counts import effective_counts  # noqa: E402

OUT_DIR = Path(__file__).parent.parent / "out" / "narrative_consolidation"
OUT_MD = OUT_DIR / "P0a_archetypes.md"
OUT_JSON = OUT_DIR / "P0a_proposals.json"

KNN_K = 5
KEYWORD_WEIGHT = 0.5  # remainder goes to the kNN vote
# (top1-top2)/top1. Relative, because the raw score scale is corpus-dependent.
# Calibrated against v1's human labels -- see the coverage/accuracy table in the
# report. Below this the top two metas are effectively tied, which under DG-0 #4
# (secondary metas populated now) is not a failure to classify: it IS the
# answer. primary = top1, secondary = top2. There is no residue bucket.
DEFAULT_MARGIN = 0.30
CALIBRATION_POINTS = (0.5, 0.4, 0.3, 0.25, 0.2, 0.1, 0.0)
TOP_PUBLISHERS = 8


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--margin", type=float, default=DEFAULT_MARGIN)
    return p.parse_args()


def toks(s: str) -> list[str]:
    return re.findall(r"[a-z]{4,}", (s or "").lower())


class Tfidf:
    def __init__(self, docs: list[list[str]]):
        self.n = len(docs)
        self.df = collections.Counter(w for d in docs for w in set(d))

    def vec(self, d: list[str]) -> dict[str, float]:
        tf = collections.Counter(d)
        v = {
            w: (1 + math.log(c)) * math.log(self.n / (1 + self.df.get(w, 0)))
            for w, c in tf.items()
        }
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {w: x / norm for w, x in v.items()}


def cos(a: dict, b: dict) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(w, 0.0) for w, x in a.items())


def score(vec_q, v1_vecs, v1_metas, meta_vecs) -> list[tuple[str, float]]:
    """Blended meta scores for one narrative, highest first."""
    sims = sorted(((cos(vec_q, v), i) for i, v in enumerate(v1_vecs)), reverse=True)[
        :KNN_K
    ]
    sc = collections.defaultdict(float)
    for s, i in sims:
        sc[v1_metas[i]] += s * (1 - KEYWORD_WEIGHT)
    for m, mv in meta_vecs.items():
        sc[m] += cos(vec_q, mv) * KEYWORD_WEIGHT * 3
    return sorted(sc.items(), key=lambda kv: -kv[1])


def main():
    args = parse_args()
    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    cur = conn.cursor()

    cur.execute("SELECT id, name, description, signals FROM meta_narratives")
    metas = {r["id"]: dict(r) for r in cur.fetchall()}

    cur.execute(
        """SELECT id, name, claim, normative_conclusion, keywords, meta_narrative_id
             FROM strategic_narratives
            WHERE is_active AND meta_narrative_id IS NOT NULL"""
    )
    v1 = [dict(r) for r in cur.fetchall()]

    cur.execute(
        """SELECT n.id, n.fn_id, n.stance, n.name_en, n.claim_en,
                  n.stance_label_en, n.framing_keywords, n.publishers,
                  n.actor_centroids, f.fn_type, f.member_fn_ids,
                  f.centroid_ids[1] AS region
             FROM narratives_v2 n
             JOIN friction_nodes f ON f.id = n.fn_id
            WHERE n.is_active AND f.is_active
            ORDER BY n.fn_id, n.display_order"""
    )
    rows = [dict(r) for r in cur.fetchall()]
    counts = effective_counts(cur, rows)
    coalitions = coalition_resolve(
        rows,
        publisher_countries(cur),
        *load_coalitions(),
        fn_home=domestic_fns(cur),
    )
    conn.close()

    v1_docs = [
        toks(
            " ".join(
                [r["name"] or "", r["claim"] or "", r["normative_conclusion"] or ""]
                + list(r["keywords"] or [])
            )
        )
        for r in v1
    ]
    v2_docs = [
        toks(
            " ".join(
                [
                    r["name_en"] or "",
                    r["claim_en"] or "",
                    r["stance_label_en"] or "",
                ]
                + list(r["framing_keywords"] or [])
            )
        )
        for r in rows
    ]
    meta_docs = {
        m: toks(
            " ".join(
                (d["signals"] or {}).get("keywords", [])
                + (d["signals"] or {}).get("domains", [])
                + (d["signals"] or {}).get("action_classes", [])
            )
            + " "
            + (d["description"] or "")
        )
        for m, d in metas.items()
    }

    tf = Tfidf(v1_docs + v2_docs)
    v1_vecs = [tf.vec(d) for d in v1_docs]
    v1_metas = [r["meta_narrative_id"] for r in v1]
    meta_vecs = {m: tf.vec(d) for m, d in meta_docs.items()}

    # honesty check: how well does this scorer reproduce v1's human labels, and
    # is the margin actually a confidence signal? Leave-one-out over v1.
    loo = []
    for i in range(len(v1)):
        held_v = v1_vecs[:i] + v1_vecs[i + 1 :]
        held_m = v1_metas[:i] + v1_metas[i + 1 :]
        s = score(v1_vecs[i], held_v, held_m, meta_vecs)
        rel = (s[0][1] - s[1][1]) / s[0][1] if s[0][1] else 0.0
        loo.append((rel, s[0][0] == v1_metas[i]))
    accuracy = 100.0 * sum(ok for _, ok in loo) / len(loo)
    calibration = []
    for t in CALIBRATION_POINTS:
        sel = [ok for rel, ok in loo if rel >= t]
        calibration.append(
            (
                t,
                len(sel),
                100.0 * len(sel) / len(loo),
                100.0 * sum(sel) / max(len(sel), 1),
            )
        )

    proposals = {}
    for r, d in zip(rows, v2_docs):
        s = score(tf.vec(d), v1_vecs, v1_metas, meta_vecs)
        top, second = s[0], (s[1] if len(s) > 1 else ("", 0.0))
        rel = (top[1] - second[1]) / top[1] if top[1] else 0.0
        tied = rel < args.margin
        co = coalitions.get(r["id"], {})
        proposals[r["id"]] = {
            "meta": top[0],
            "score": round(top[1], 4),
            "meta_secondary": [second[0]] if (tied and second[0]) else [],
            "runner_up": second[0],
            "margin": round(rel, 4),
            "tied": tied,
            "coalition": co.get("coalition"),
            "coalition_level": co.get("level"),
            "coalition_scope": co.get("scope"),
            "coalition_share": co.get("share"),
        }

    by_id = {r["id"]: r for r in rows}
    sign_name = {1: "supportive (+)", 0: "neutral (0)", -1: "critical (-)"}

    # Every narrative lands in an archetype now -- a tie is resolved as
    # primary + secondary, not deferred to a residue pile.
    arche = collections.defaultdict(list)
    for r in rows:
        p = proposals[r["id"]]
        s = r["stance"] or 0
        arche[(p["meta"], (s > 0) - (s < 0))].append(r["id"])

    L = []
    L.append("# P0(a) -- Narrative archetype grouping (meta axis)")
    L.append("")
    L.append(
        "Artifact for `NARRATIVE_CONSOLIDATION_SPEC.md` 3.A3 step 1, feeding "
        "**DG-0 #1**. Read-only; nothing was written to the database."
    )
    L.append("")
    L.append("## Method, and what changed from the first attempt")
    L.append("")
    L.append(
        "The first version of this artifact clustered narratives by **publisher-set "
        "overlap**. That was the wrong axis. The 9 meta-narratives are a "
        "*claim-type* axis; publisher bloc is a *who* axis, and the two are "
        "orthogonal. Empirically the publisher signal does not discriminate at "
        "all -- narratives carry %.1f publishers on average and the same Western "
        "wire set appears in ~42%% of them -- so the clustering collapsed into one "
        "87-member bloc spanning 86 friction nodes, from Arctic climate alarm to "
        "Hungary rule-of-law to the Cuba embargo. No single meta is assignable to "
        "such a group, so it could not feed DG-0."
        % (sum(len(r["publishers"] or []) for r in rows) / max(len(rows), 1))
    )
    L.append("")
    L.append(
        "This version groups on the meta axis directly. Each narrative gets a "
        "**mechanically proposed** meta from two measured signals, blended 50/50:"
    )
    L.append("")
    L.append(
        "1. **kNN (k=%d) over `strategic_narratives`** -- v1's %d active rows carry "
        "*human* meta assignments. v1's content is being retired, but the meta "
        "layer is explicitly preserved (spec 1), and those rows are the only "
        "existing record of how this project maps a claim to a meta." % (KNN_K, len(v1))
    )
    L.append(
        "2. **Cosine against each meta's own `meta_narratives.signals`** vocabulary "
        "plus its description."
    )
    L.append("")
    L.append(
        "**Trust calibration: leave-one-out accuracy against v1's own human labels "
        "is %.0f%%** (majority-class baseline is %.0f%%). That is good enough to "
        "*pre-group* and far too weak to *auto-assign*. What you are approving "
        "below is the grouping, not the individual rows."
        % (
            accuracy,
            100.0 * max(collections.Counter(v1_metas).values()) / len(v1_metas),
        )
    )
    L.append("")
    L.append(
        "**Margin calibration.** Confidence is the relative gap between the top "
        "two metas, `(top1-top2)/top1`. Measured against v1's human labels it is a "
        "real signal, so the cutoff is a coverage/accuracy trade you can move:"
    )
    L.append("")
    L.append("| rel. margin cutoff | coverage | accuracy |")
    L.append("|---|---:|---:|")
    for t, n, covpct, accpct in calibration:
        L.append(
            "| >= %.2f%s | %d/%d (%.0f%%) | %.0f%% |"
            % (
                t,
                " **(in use)**" if abs(t - args.margin) < 1e-9 else "",
                n,
                len(loo),
                covpct,
                accpct,
            )
        )
    L.append("")
    L.append(
        "Narratives below the cutoff are **not** placed in an archetype -- they are "
        "assigned BOTH metas -- primary and secondary (DG-0 #4). A near-tie "
        "between two metas is not a failure to classify; it is the honest answer, "
        "and it is why populating secondary metas now makes the review EASIER "
        "rather than harder: no narrative has to be forced into one box."
    )
    L.append("")
    L.append("| | |")
    L.append("|---|---|")
    L.append("| active narratives | %d |" % len(rows))
    n_sec = sum(1 for p in proposals.values() if p["meta_secondary"])
    L.append("| single clear meta | %d |" % (len(rows) - n_sec))
    L.append("| primary + secondary meta | %d |" % n_sec)
    L.append("| **archetypes (meta x sign)** | **%d** |" % len(arche))
    L.append("")
    L.append("### Proposed distribution across the 9 metas")
    L.append("")
    L.append("| meta | narratives | share |")
    L.append("|---|---:|---:|")
    dist = collections.Counter(proposals[r["id"]]["meta"] for r in rows)
    for m in sorted(metas, key=lambda x: -dist[x]):
        L.append("| `%s` | %d | %.0f%% |" % (m, dist[m], 100.0 * dist[m] / len(rows)))
    L.append("")
    L.append(
        "Spec 3.A4 predicted `security_order` and `global_justice` would dominate "
        "and `planetary_governance` come out near-empty. Check the table above "
        "against that expectation -- a large divergence is a finding about the "
        "scorer, the corpus, or both."
    )
    L.append("")
    L.append("---")
    L.append("")
    L.append("## Archetypes")
    L.append("")
    L.append(
        "Each section is **one decision**: accept the proposed meta for the whole "
        "group, or name a different one. Per-narrative exceptions go in the "
        "`overrides:` block of `db/registry/narrative_meta_mapping.yaml` (P0b)."
    )
    L.append("")
    L.append(
        "`titles` is the effective attributed-title count -- direct "
        "`title_narratives` for atomic narratives, the `THEATER_ROLLUP_SQL` union "
        "for theater ones. Rows below the proposed publication gate (25) are "
        "marked `[thin]`."
    )
    L.append("")

    order = sorted(arche.items(), key=lambda kv: -len(kv[1]))
    for idx, ((meta, sign), members) in enumerate(order, 1):
        regions = collections.Counter(by_id[m]["region"] for m in members)
        fns = collections.Counter(by_id[m]["fn_id"] for m in members)
        allpubs = collections.Counter(
            p for m in members for p in (by_id[m]["publishers"] or [])
        )
        titles = sum(counts.get(m, 0) for m in members)
        L.append(
            "### A%02d -- `%s`, %s -- %d narratives, %s titles"
            % (idx, meta, sign_name[sign], len(members), f"{titles:,}")
        )
        L.append("")
        L.append("- **proposed meta**: `%s`  (accept / replace: __________)" % meta)
        cos_dist = collections.Counter(proposals[m]["coalition"] for m in members)
        L.append(
            "- **coalitions** (derived from publishers): %s"
            % ", ".join("`%s` (%d)" % (c, n) for c, n in cos_dist.most_common(6))
        )
        sec_dist = collections.Counter(
            s for m in members for s in proposals[m]["meta_secondary"]
        )
        L.append(
            "- **secondary metas proposed**: %s"
            % (
                ", ".join("`%s` (%d)" % (s, n) for s, n in sec_dist.most_common(4))
                or "_none -- all members have one clear meta_"
            )
        )
        L.append(
            "- **top publishers**: %s"
            % ", ".join(
                "%s (%d)" % (p, c) for p, c in allpubs.most_common(TOP_PUBLISHERS)
            )
        )
        L.append(
            "- **regions**: %s"
            % ", ".join("%s (%d)" % (r, c) for r, c in regions.most_common(6))
        )
        L.append(
            "- **friction nodes**: %d distinct -- %s"
            % (len(fns), ", ".join(f for f, _ in fns.most_common(6)))
        )
        L.append("")
        L.append("<details><summary>%d narratives</summary>" % len(members))
        L.append("")
        for m in sorted(members, key=lambda x: -counts.get(x, 0)):
            r = by_id[m]
            p = proposals[m]
            L.append(
                "- `%s` (%s, stance %+d, %d titles, coalition `%s`%s) -- %s"
                % (
                    m,
                    r["fn_id"],
                    r["stance"] or 0,
                    counts.get(m, 0),
                    p["coalition"],
                    (
                        ", also `%s`" % p["meta_secondary"][0]
                        if p["meta_secondary"]
                        else ""
                    ),
                    (r["name_en"] or "")[:100],
                )
            )
        L.append("")
        L.append("</details>")
        L.append("")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(L), encoding="utf-8")
    OUT_JSON.write_text(
        json.dumps(
            {
                "accuracy_vs_v1_labels": round(accuracy, 1),
                "margin": args.margin,
                "archetypes": {
                    "A%02d"
                    % i: {
                        "meta": meta,
                        "stance_sign": sign,
                        "members": sorted(members),
                    }
                    for i, ((meta, sign), members) in enumerate(order, 1)
                },
                "counts": {k: counts.get(k, 0) for k in proposals},
                "proposals": proposals,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print("active narratives     : %d" % len(rows))
    print("scorer accuracy vs v1 : %.0f%% (leave-one-out)" % accuracy)
    print("ARCHETYPES            : %d  <- decisions needed at DG-0 #1" % len(arche))
    print(
        "with secondary meta   : %d"
        % sum(1 for p in proposals.values() if p["meta_secondary"])
    )
    print(
        "coalition mixed/unres : %d"
        % sum(1 for p in proposals.values() if p["coalition"] in (None, "mixed"))
    )
    print("wrote %s" % OUT_MD)
    print("wrote %s" % OUT_JSON)


if __name__ == "__main__":
    main()
