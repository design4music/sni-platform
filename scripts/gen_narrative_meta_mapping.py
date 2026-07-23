"""P0(b) -- generate the DRAFT `db/registry/narrative_meta_mapping.yaml`.

NARRATIVE_CONSOLIDATION_SPEC.md 3.A3 step 4: the narrative -> meta mapping is a
domain-model decision, so it lives in a git-diffable registry and is reconciled
into `narratives_v2.meta_narrative_id` by a script (that reconcile script is
P1 -- this only writes the draft).

Regenerating OVERWRITES the `archetypes:` block from the clustering proposals
but PRESERVES `overrides:`, `secondary:` and any `meta:` a human has edited on
an approved archetype. Nothing hand-entered is lost by a re-run (Rule 8).

Read-only against the database (it only reads names for the comments).

Usage:
  python scripts/gen_narrative_meta_mapping.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import psycopg2
import yaml
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config  # noqa: E402

ROOT = Path(__file__).parent.parent
PROPOSALS = ROOT / "out" / "narrative_consolidation" / "P0a_proposals.json"
OUT = ROOT / "db" / "registry" / "narrative_meta_mapping.yaml"

HEADER = """\
# Narrative -> meta-narrative mapping
#
# Source of truth for `narratives_v2.meta_narrative_id` /
# `meta_secondary_ids`. Per NARRATIVE_CONSOLIDATION_SPEC.md 3.A3 step 4 the
# mapping is a DOMAIN MODEL decision: it is authored here, reviewed in a diff,
# and reconciled into the column by a script. Never edit the column directly.
#
# STATUS: {status}
#   `archetypes` below are MECHANICAL PROPOSALS from
#   scripts/narrative_archetype_clustering.py -- a blend of kNN over v1's
#   human meta labels and each meta's own signal vocabulary. Leave-one-out
#   accuracy against v1 is {accuracy}%. They are a starting point for review,
#   NOT an approved mapping. Nothing may be written to the database until
#   DG-0 #1 is signed off and `status` here reads `approved`.
#
# HOW TO REVIEW (this is DG-0 #1)
#   Work through out/narrative_consolidation/P0a_archetypes.md. For each
#   archetype: keep `meta` or replace it, then set `approved: true`. Individual
#   narratives that do not belong with their group go in `overrides`.
#   Every active narrative is in exactly one archetype -- there is no
#   unassigned pile to clear first.
#
# RESOLUTION ORDER (what the P1 reconcile script must implement)
#   1. `overrides[narrative_id]`          -- wins over everything
#   2. the `meta` of the archetype listing that narrative in `members`
#   3. unmapped -> reconcile fails loudly; it never guesses
#
# Regenerating this file preserves `overrides`, `secondary`,
# `coalition_overrides`, and any edited `meta`/`approved` on an archetype.
# Only archetype membership is recomputed.
#
# COALITION is not authored here. It is DERIVED from each narrative's publisher
# bloc via db/registry/coalitions.yaml (that file is DG-0 #2). Only corrections
# live here, in `coalition_overrides`.
"""


def load_existing() -> dict:
    if not OUT.exists():
        return {}
    return yaml.safe_load(OUT.read_text(encoding="utf-8")) or {}


def main():
    if not PROPOSALS.exists():
        sys.exit(
            "missing %s -- run narrative_archetype_clustering.py first" % PROPOSALS
        )
    data = json.loads(PROPOSALS.read_text(encoding="utf-8"))

    conn = psycopg2.connect(**config.db_connect_kwargs(), cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute("SELECT id, name_en, fn_id, stance FROM narratives_v2 WHERE is_active")
    info = {r["id"]: dict(r) for r in cur.fetchall()}
    conn.close()

    prev = load_existing()
    prev_arch = prev.get("archetypes") or {}

    status = prev.get("status", "draft")
    lines = [
        HEADER.format(
            status="%s -- awaiting DG-0 #1" % status if status == "draft" else status,
            accuracy=data["accuracy_vs_v1_labels"],
        ),
        "version: 1",
        "status: %s" % status,
        "generated_by: scripts/gen_narrative_meta_mapping.py",
        "",
        "archetypes:",
    ]

    counts = data["counts"]
    for aid in sorted(data["archetypes"]):
        a = data["archetypes"][aid]
        keep = prev_arch.get(aid, {})
        meta = keep.get("meta", a["meta"])
        approved = keep.get("approved", False)
        titles = sum(counts.get(m, 0) for m in a["members"])
        lines.append("")
        lines.append(
            "  # %s -- %s, stance sign %+d -- %d narratives, %s titles"
            % (aid, meta, a["stance_sign"], len(a["members"]), f"{titles:,}")
        )
        lines.append("  %s:" % aid)
        lines.append("    meta: %s" % meta)
        lines.append("    stance_sign: %d" % a["stance_sign"])
        lines.append("    approved: %s" % ("true" if approved else "false"))
        lines.append("    members:")
        for m in sorted(a["members"], key=lambda x: -counts.get(x, 0)):
            n = info.get(m, {})
            lines.append(
                "      - %s%s  # %s, %d titles -- %s"
                % (
                    m,
                    " " * max(0, 44 - len(m)),
                    n.get("fn_id", "?"),
                    counts.get(m, 0),
                    (n.get("name_en") or "")[:70],
                )
            )

    lines.append("")
    lines.append(
        "# Per-narrative exceptions. Wins over the archetype. narrative_id: meta_id"
    )
    lines.append("overrides:")
    for k, v in (prev.get("overrides") or {}).items():
        lines.append("  %s: %s" % (k, v))
    if not (prev.get("overrides") or {}):
        lines.append("  {}")

    lines.append("")
    lines.append("# Secondary metas (spec 3.A2). DG-0 #4: POPULATED NOW, not deferred.")
    lines.append("# These are the narratives whose top two metas scored within the")
    lines.append("# calibrated margin -- i.e. the scorer says both genuinely apply.")
    lines.append("# A hand-edited entry here is preserved across regeneration.")
    lines.append("# narrative_id: [meta_id, ...]")
    lines.append("secondary:")
    prev_sec = prev.get("secondary") or {}
    sec = {
        k: v["meta_secondary"]
        for k, v in data["proposals"].items()
        if v.get("meta_secondary")
    }
    sec.update(prev_sec)
    for k in sorted(sec, key=lambda x: -counts.get(x, 0)):
        n = info.get(k, {})
        lines.append(
            "  %s:%s %s  # %d titles -- %s"
            % (
                k,
                " " * max(0, 44 - len(k)),
                json.dumps(sec[k]),
                counts.get(k, 0),
                (n.get("name_en") or "")[:56],
            )
        )
    if not sec:
        lines.append("  {}")

    lines.append("")
    lines.append(
        "# Coalition is DERIVED, not authored -- resolved from each narrative's"
    )
    lines.append("# publisher bloc via db/registry/coalitions.yaml. It is listed here")
    lines.append("# only so a wrong resolution can be pinned. Empty means: trust the")
    lines.append("# derivation. narrative_id: coalition_id")
    lines.append("coalition_overrides:")
    for k, v in (prev.get("coalition_overrides") or {}).items():
        lines.append("  %s: %s" % (k, v))
    if not (prev.get("coalition_overrides") or {}):
        lines.append("  {}")
    lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")

    parsed = yaml.safe_load(OUT.read_text(encoding="utf-8"))
    mapped = sum(len(a["members"]) for a in parsed["archetypes"].values())
    print("archetypes  : %d" % len(parsed["archetypes"]))
    print("mapped      : %d narratives" % mapped)
    print("secondary   : %d narratives" % len(parsed.get("secondary") or {}))
    print("overrides   : %d" % len(parsed.get("overrides") or {}))
    print("status      : %s" % parsed["status"])
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
