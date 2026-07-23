"""P1 seed -- generate the DRAFT `db/registry/narrative_positions.yaml`.

Turns the P0e position clustering into the registry that P1 reconciles into the
`positions` table + `narratives_v2.position_id`. Adds the two proposals the DG-0
review needs, both mechanical and both reviewable as a diff:

  META (primary + secondary): the P0a scorer (kNN over v1's human meta labels +
  meta-signal cosine) scores each CARD; a position's meta is the score summed
  across its cards. primary = top, secondary = runner-up when within the same
  relative margin used in P0a. Populated now (DG-0 #4).

  OWNER (owner_centroids[]): who ASSERTS the position, from MEASURED publisher
  countries -- each card's publishers -> feeds.country_code -> a centroid,
  home-country-restricted on domestic friction nodes (so foreign wires covering
  someone else's fight don't get counted as owners). EU-27 publisher countries
  collapse to NON-STATE-EU to avoid a 15-way European split. A centroid is listed
  as an owner when it carries >= OWNER_SHARE of the position's resolved
  publishers (min one, cap OWNER_MAX). This is a PROPOSAL -- the real owner is an
  editorial/extracted label, verified against country-owner document sources.

Regenerating preserves any human edits (meta/owner/name/claim) already made in
the file, keyed by position id. Read-only against the DB. Writes no table.

Usage:
  python scripts/gen_narrative_positions.py
"""

from __future__ import annotations

import collections
import sys
from pathlib import Path

import psycopg2
import yaml
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config  # noqa: E402
from scripts.narrative_archetype_clustering import (  # noqa: E402
    DEFAULT_MARGIN,
    Tfidf,
    score,
    toks,
)
from scripts.narrative_coalitions import (  # noqa: E402
    _norm,
    domestic_fns,
    publisher_countries,
)
from scripts.narrative_positions_draft import POSITIONS  # noqa: E402

ROOT = Path(__file__).parent.parent
OUT = ROOT / "db" / "registry" / "narrative_positions.yaml"
COALITIONS = ROOT / "db" / "registry" / "coalitions.yaml"

OWNER_SHARE = 0.25  # a centroid must carry this share of a position's publishers
OWNER_MAX = 4  # never propose more owners than this

HEADER = """\
# Narrative positions -- the position/card model (NARRATIVE_CONSOLIDATION_SPEC.md v2)
#
# A POSITION is the universal narrative core: a claim + stance that recurs across
# friction nodes. This file is the source of truth for the `positions` table and
# for `narratives_v2.position_id` (the card -> position link). Reconciled by the
# P1 script; never edit those columns directly.
#
# STATUS: {status}
#   `meta`/`meta_secondary` and `owner_centroids` are MECHANICAL PROPOSALS
#   (see scripts/gen_narrative_positions.py). Meta scorer LOO accuracy vs v1's
#   human labels is 68%. Owner is derived from measured publisher countries.
#   Both are starting points for DG-0 review, not approved. Nothing writes to the
#   DB until DG-0 is signed off and `status` reads `approved`.
#
# HOW TO REVIEW (DG-0 #2 meta, #3 owner)
#   Per position: accept/replace `meta` + `meta_secondary`; accept/correct
#   `owner_centroids`; fix `name`/`claim` wording; move a card between positions
#   in `cards` if mis-grouped. Card membership (the P0e clustering) is already
#   accepted -- edits here are corrections, not a from-scratch pass.
#
# Regenerating preserves human edits keyed by position id (name/claim/meta/
# meta_secondary/owner_centroids). Only the mechanical proposals for untouched
# fields and the card lists are recomputed.
"""


def _scalar(s: str) -> str:
    """One-line YAML scalar, never wrapped. A JSON string is a valid YAML flow
    scalar, and json.dumps adds no document-end marker (safe_dump does)."""
    import json

    return json.dumps(s, ensure_ascii=True)


def load_existing() -> dict:
    if not OUT.exists():
        return {}
    doc = yaml.safe_load(OUT.read_text(encoding="utf-8")) or {}
    return {p["id"]: p for p in doc.get("positions", [])}


def build_iso_to_centroid(cur) -> dict[str, str]:
    """ISO country code -> owner centroid. A major country maps to its own
    single-country centroid (DE -> EUROPE-GERMANY); a small one that only lives
    inside a regional group maps to that group (EE -> EUROPE-BALTIC), per the
    design principle that only high-coverage actors get their own centroid. When
    an ISO sits in several groups, the smallest (most specific) wins."""
    cur.execute(
        "SELECT id, iso_codes FROM centroids_v3 WHERE is_active AND iso_codes IS NOT NULL"
    )
    rows = [(r["id"], list(r["iso_codes"])) for r in cur.fetchall()]
    iso2c: dict[str, str] = {}
    all_isos = {i for _, isos in rows for i in isos}
    for iso in all_isos:
        holders = [(cid, isos) for cid, isos in rows if iso in isos]
        # single-country centroid wins; else the smallest group; deterministic tie-break
        holders.sort(key=lambda h: (len(h[1]), h[0]))
        iso2c[iso] = holders[0][0]
    return iso2c


def main():
    POSITIONS.pop("taiwan_one_china_recognition", None)  # P0e placeholder

    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    cur = conn.cursor()

    # ---- card data ----
    cur.execute(
        """SELECT n.id, n.fn_id, n.stance, n.name_en, n.claim_en,
                  n.stance_label_en, n.framing_keywords, n.publishers,
                  f.fn_type
             FROM narratives_v2 n JOIN friction_nodes f ON f.id = n.fn_id
            WHERE n.is_active AND f.is_active"""
    )
    cards = {r["id"]: dict(r) for r in cur.fetchall()}

    # ---- meta scorer machinery (mirror P0a) ----
    cur.execute("SELECT id, name, description, signals FROM meta_narratives")
    metas = {r["id"]: dict(r) for r in cur.fetchall()}
    cur.execute(
        """SELECT id, name, claim, normative_conclusion, keywords, meta_narrative_id
             FROM strategic_narratives
            WHERE is_active AND meta_narrative_id IS NOT NULL"""
    )
    v1 = [dict(r) for r in cur.fetchall()]

    home = domestic_fns(cur)
    pub2c = publisher_countries(cur)
    iso2centroid = build_iso_to_centroid(cur)
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
    card_docs = {
        cid: toks(
            " ".join(
                [c["name_en"] or "", c["claim_en"] or "", c["stance_label_en"] or ""]
                + list(c["framing_keywords"] or [])
            )
        )
        for cid, c in cards.items()
    }
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
    tf = Tfidf(v1_docs + list(card_docs.values()))
    v1_vecs = [tf.vec(d) for d in v1_docs]
    v1_metas = [r["meta_narrative_id"] for r in v1]
    meta_vecs = {m: tf.vec(d) for m, d in meta_docs.items()}

    def card_meta_scores(cid) -> dict[str, float]:
        return dict(score(tf.vec(card_docs[cid]), v1_vecs, v1_metas, meta_vecs))

    def position_owner(ids) -> tuple[list[str], dict]:
        tally: collections.Counter = collections.Counter()
        for cid in ids:
            c = cards[cid]
            pubs = c["publishers"] or []
            h = home.get(c["fn_id"])
            if h:
                local = [p for p in pubs if pub2c.get(_norm(p)) == h]
                if local:
                    pubs = local
            for p in pubs:
                iso = pub2c.get(_norm(p))
                cen = iso2centroid.get(iso) if iso else None
                if cen:
                    tally[cen] += 1
        total = sum(tally.values())
        if not total:
            return [], {}
        owners = [c for c, n in tally.most_common() if n / total >= OWNER_SHARE]
        if not owners:
            owners = [tally.most_common(1)[0][0]]
        return owners[:OWNER_MAX], dict(tally.most_common())

    prev = load_existing()
    status = "draft"
    if prev:
        # status lives at doc level; re-read it
        doc = yaml.safe_load(OUT.read_text(encoding="utf-8")) or {}
        status = doc.get("status", "draft")

    lines = [
        HEADER.format(
            status="%s -- awaiting DG-0" % status if status == "draft" else status
        ),
        "version: 1",
        "status: %s" % status,
        "generated_by: scripts/gen_narrative_positions.py",
        "",
        "positions:",
    ]

    stats = {"secondary": 0, "owner_multi": 0, "owner_none": 0}
    ordered = sorted(POSITIONS.items(), key=lambda kv: -len(kv[1][2]))
    for pid, (name, sign, ids) in ordered:
        keep = prev.get(pid, {})
        # meta: sum card score vectors
        agg: collections.Counter = collections.Counter()
        for cid in ids:
            for m, s in card_meta_scores(cid).items():
                agg[m] += s
        ranked = agg.most_common()
        top, second = ranked[0], (ranked[1] if len(ranked) > 1 else ("", 0.0))
        rel = (top[1] - second[1]) / top[1] if top[1] else 0.0
        meta = keep.get("meta", top[0])
        if "meta_secondary" in keep:
            meta_secondary = keep["meta_secondary"] or []
        else:
            meta_secondary = [second[0]] if (rel < DEFAULT_MARGIN and second[0]) else []
        owners, breakdown = position_owner(ids)
        owners = keep.get("owner_centroids", owners)
        if meta_secondary:
            stats["secondary"] += 1
        if len(owners) > 1:
            stats["owner_multi"] += 1
        if not owners:
            stats["owner_none"] += 1

        fns = sorted({cards[c]["fn_id"] for c in ids})
        lines.append("")
        lines.append(
            "  # %d cards / %d friction nodes | owner tally: %s"
            % (
                len(ids),
                len(fns),
                ", ".join("%s:%d" % (k, v) for k, v in list(breakdown.items())[:6]),
            )
        )
        lines.append("  - id: %s" % pid)
        lines.append("    name_en: %s" % _scalar(name))
        lines.append("    name_de: %s  # TODO translate" % "''")
        lines.append("    claim_en: %s" % _scalar(name))
        lines.append("    claim_de: %s  # TODO translate" % "''")
        lines.append("    stance_sign: %d" % sign)
        lines.append("    meta: %s" % meta)
        lines.append(
            "    meta_secondary: %s"
            % yaml.safe_dump(meta_secondary, default_flow_style=True).strip()
        )
        lines.append(
            "    owner_centroids: %s"
            % yaml.safe_dump(owners, default_flow_style=True).strip()
        )
        lines.append("    cards:")
        for cid in sorted(ids, key=lambda x: (cards[x]["fn_id"], x)):
            lines.append(
                "      - %s%s  # %s, stance %+d"
                % (
                    cid,
                    " " * max(0, 44 - len(cid)),
                    cards[cid]["fn_id"],
                    cards[cid]["stance"] or 0,
                )
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    parsed = yaml.safe_load(OUT.read_text(encoding="utf-8"))
    ncards = sum(len(p["cards"]) for p in parsed["positions"])
    print("positions        : %d" % len(parsed["positions"]))
    print("cards mapped      : %d" % ncards)
    print("with secondary    : %d" % stats["secondary"])
    print("owner multi/none  : %d / %d" % (stats["owner_multi"], stats["owner_none"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
