"""P0(d) -- v1 <-> v2 narrative id collision check + draft redirect map.

NARRATIVE_CONSOLIDATION_SPEC.md P0(d), feeding DG-2 #11.

Spec B3 keeps `/narratives/[id]` as the canonical route and lets v2 ids occupy
it, on the stated assumption that v1 and v2 slugs are disjoint. This verifies
that, then drafts the 301 map: each v1 id goes to its nearest v2 successor when
one is close enough, otherwise to its meta page (spec B3's own fallback).

Successor proposal is mechanical -- TF-IDF cosine between the v1 narrative's
text and every active v2 narrative's text. Similarity is printed for every row
so a human can accept, retarget, or demote to the meta page. DG-2 #11 proposes
hand-mapping only the top ~30 by old event count and blanket-301'ing the rest;
this report ranks by exactly that number so the cut is visible.

Read-only. Writes a markdown report, touches no table.

Usage:
  python scripts/v1_v2_redirect_map.py
  python scripts/v1_v2_redirect_map.py --hand-map 30 --min-similarity 0.20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config  # noqa: E402
from scripts.narrative_archetype_clustering import Tfidf, cos, toks  # noqa: E402
from scripts.narrative_counts import effective_counts  # noqa: E402

OUT = (
    Path(__file__).parent.parent
    / "out"
    / "narrative_consolidation"
    / "P0d_redirect_map.md"
)
HAND_MAP = 30
MIN_SIMILARITY = 0.20
# Spec C4 / DG-0 #3: a narrative under this many attributed titles gets no
# standalone page. Redirecting to one would 301 into a 404.
PUBLICATION_GATE = 25


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--hand-map", type=int, default=HAND_MAP)
    p.add_argument("--min-similarity", type=float, default=MIN_SIMILARITY)
    p.add_argument("--gate", type=int, default=PUBLICATION_GATE)
    return p.parse_args()


def main():
    args = parse_args()
    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    cur = conn.cursor()

    cur.execute("SELECT id FROM strategic_narratives")
    v1_all = {r["id"] for r in cur.fetchall()}
    cur.execute("SELECT id FROM narratives_v2")
    v2_all = {r["id"] for r in cur.fetchall()}
    collisions = sorted(v1_all & v2_all)

    cur.execute(
        """SELECT s.id, s.name, s.claim, s.normative_conclusion, s.keywords,
                  s.meta_narrative_id, s.is_active,
                  COUNT(e.event_id)::int AS event_count
             FROM strategic_narratives s
             LEFT JOIN event_strategic_narratives e ON e.narrative_id = s.id
            GROUP BY s.id
            ORDER BY event_count DESC"""
    )
    v1 = [dict(r) for r in cur.fetchall()]

    cur.execute(
        """SELECT n.id, n.fn_id, n.stance, n.name_en, n.claim_en,
                  n.stance_label_en, n.framing_keywords, n.publishers,
                  f.fn_type, f.member_fn_ids
             FROM narratives_v2 n
             JOIN friction_nodes f ON f.id = n.fn_id
            WHERE n.is_active AND f.is_active"""
    )
    v2 = [dict(r) for r in cur.fetchall()]
    counts = effective_counts(cur, v2)
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
                [r["name_en"] or "", r["claim_en"] or "", r["stance_label_en"] or ""]
                + list(r["framing_keywords"] or [])
            )
        )
        for r in v2
    ]
    tf = Tfidf(v1_docs + v2_docs)
    v2_vecs = [tf.vec(d) for d in v2_docs]

    rows = []
    for r, d in zip(v1, v1_docs):
        q = tf.vec(d)
        sims = sorted(((cos(q, v), i) for i, v in enumerate(v2_vecs)), reverse=True)
        # A successor below the publication gate has no standalone page, so
        # redirecting to it would 301 into a 404. Walk down the ranking to the
        # best publishable match instead of taking the top one blindly.
        sim, i = 0.0, None
        for s, j in sims:
            if s < args.min_similarity:
                break
            if counts.get(v2[j]["id"], 0) >= args.gate:
                sim, i = s, j
                break
        usable = i is not None
        succ = v2[i] if usable else None
        rows.append(
            {
                **r,
                "sim": sim,
                "top_sim": sims[0][0],
                "succ": succ["id"] if usable else None,
                "succ_name": succ["name_en"] if usable else None,
                "succ_titles": counts.get(succ["id"], 0) if usable else 0,
                "target": (
                    "/narratives/%s" % succ["id"]
                    if usable
                    else (
                        "/narratives/meta/%s" % r["meta_narrative_id"]
                        if r["meta_narrative_id"]
                        else "/narratives"
                    )
                ),
            }
        )

    hand = rows[: args.hand_map]
    blanket = rows[args.hand_map :]
    total_events = sum(r["event_count"] for r in rows) or 1
    hand_events = sum(r["event_count"] for r in hand)

    L = []
    L.append("# P0(d) -- v1/v2 id collision check + draft redirect map")
    L.append("")
    L.append(
        "Artifact for `NARRATIVE_CONSOLIDATION_SPEC.md` P0(d), feeding "
        "**DG-2 #11**. Read-only; nothing was written."
    )
    L.append("")
    L.append("## 1. Collision check")
    L.append("")
    L.append(
        "Spec B3 keeps `/narratives/[id]` as the canonical route and lets v2 ids "
        "occupy it, on the stated assumption that the two id sets are disjoint."
    )
    L.append("")
    L.append("| | |")
    L.append("|---|---:|")
    L.append("| `strategic_narratives` ids (v1) | %d |" % len(v1_all))
    L.append("| `narratives_v2` ids (v2) | %d |" % len(v2_all))
    L.append("| **ids present in both** | **%d** |" % len(collisions))
    L.append("")
    if collisions:
        L.append(
            "**COLLISIONS -- spec B3's assumption is wrong. Resolve before cutover:**"
        )
        L.append("")
        for c in collisions:
            L.append("- `%s`" % c)
    else:
        L.append(
            "**Disjoint, as spec B3 assumed.** v2 ids can take over the route with "
            "no id remapping, and every v1 id is free to become a 301 source."
        )
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 2. Draft redirect map")
    L.append("")
    L.append(
        "Successor proposal is TF-IDF cosine between each v1 narrative's text "
        "(`name` + `claim` + `normative_conclusion` + `keywords`) and every active "
        "v2 narrative's text. Below %.2f similarity no successor is claimed and "
        "the row falls back to its meta page, per spec B3." % args.min_similarity
    )
    L.append("")
    L.append(
        "Candidates under the publication gate (%d attributed titles, spec C4) are "
        "**skipped**, not proposed: those narratives get no standalone page, so a "
        "301 to one would land on a 404. The next publishable match above the "
        "similarity floor is used instead, else the meta page." % args.gate
    )
    L.append("")
    L.append(
        "**This is mechanical and unverified.** Similarity is a lexical overlap "
        "score, not a judgment that two narratives make the same argument. Every "
        "row in the hand-map table below needs a human accept/retarget -- that is "
        "the DG-2 #11 decision."
    )
    L.append("")
    L.append(
        "Ranking is by v1 `event_strategic_narratives` count, so the top %d rows "
        "carry %.0f%% of all %s v1 event links. That is the argument for "
        "hand-mapping only these and blanket-301'ing the tail."
        % (
            args.hand_map,
            100.0 * hand_events / total_events,
            f"{total_events:,}",
        )
    )
    L.append("")
    L.append("### 2a. Hand-map candidates -- top %d by v1 event count" % args.hand_map)
    L.append("")
    L.append("| v1 id | events | sim | proposed target | v2 successor | v2 titles |")
    L.append("|---|---:|---:|---|---|---:|")
    for r in hand:
        L.append(
            "| `%s` | %d | %.2f | `%s` | %s | %d |"
            % (
                r["id"],
                r["event_count"],
                r["sim"],
                r["target"],
                (r["succ_name"] or "_(no successor -- meta page)_")[:60],
                r["succ_titles"],
            )
        )
    L.append("")
    L.append("### 2b. Tail -- blanket 301 (%d ids)" % len(blanket))
    L.append("")
    L.append(
        "DG-2 #11 proposes sending all of these to `/narratives`. The per-row "
        "proposal is listed anyway: where similarity is high the redirect costs "
        "nothing extra to make specific, and where it is low the meta page is a "
        "better landing than the index."
    )
    L.append("")
    L.append("| v1 id | events | sim | proposed target |")
    L.append("|---|---:|---:|---|")
    for r in blanket:
        L.append(
            "| `%s` | %d | %.2f | `%s` |"
            % (r["id"], r["event_count"], r["sim"], r["target"])
        )
    L.append("")
    n_meta = sum(1 for r in rows if r["succ"] is None)
    L.append("---")
    L.append("")
    L.append("## 3. Summary")
    L.append("")
    L.append("| | |")
    L.append("|---|---:|")
    L.append("| v1 ids needing a redirect | %d |" % len(rows))
    L.append("| with a proposed v2 successor | %d |" % (len(rows) - n_meta))
    L.append("| falling back to a meta page | %d |" % n_meta)
    L.append(
        "| v1 ids with zero event links | %d |"
        % sum(1 for r in rows if r["event_count"] == 0)
    )
    L.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L), encoding="utf-8")

    print("v1 ids: %d   v2 ids: %d" % (len(v1_all), len(v2_all)))
    print("COLLISIONS: %d %s" % (len(collisions), collisions or ""))
    print("with proposed v2 successor : %d" % (len(rows) - n_meta))
    print("falling back to meta page  : %d" % n_meta)
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
