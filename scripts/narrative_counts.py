"""Effective attributed-title count per narratives_v2 row.

Atomic narratives count their own `title_narratives` rows. Theater narratives
carry no fn_anchor bundle and never attribute titles directly -- their count is
the roll-up the FN page renders (THEATER_ROLLUP_SQL in
`apps/frontend/lib/friction-nodes.ts`): distinct titles attributed to a MEMBER
ATOMIC narrative of the same stance sign, whose publisher is in the theater
narrative's publisher bloc.

Reading title_narratives alone reports 0 for every theater narrative, which
would misclassify all of them as dead. Shared by the P0(a) and P0(c) artifacts.
"""

from __future__ import annotations

ATOMIC_COUNT_SQL = """
    SELECT n.id, COUNT(tn.title_id)::int AS c
      FROM narratives_v2 n
      LEFT JOIN title_narratives tn ON tn.narrative_id = n.id
     WHERE n.is_active
     GROUP BY n.id
"""

THEATER_COUNT_SQL = """
    SELECT COUNT(DISTINCT t.id)::int AS c
      FROM title_narratives tn
      JOIN narratives_v2 an ON an.id = tn.narrative_id
      JOIN friction_nodes afn ON afn.id = an.fn_id
      JOIN titles_v3 t ON t.id = tn.title_id
     WHERE afn.id = ANY(%(members)s) AND afn.fn_type = 'atomic'
       AND an.stance IS NOT NULL AND sign(an.stance)::int = sign(%(stance)s::int)
       AND t.publisher_name = ANY(%(publishers)s)
"""


def effective_counts(cur, rows: list[dict]) -> dict[str, int]:
    """rows need: id, fn_type, stance, publishers, member_fn_ids."""
    cur.execute(ATOMIC_COUNT_SQL)
    counts = {r["id"]: r["c"] for r in cur.fetchall()}

    for r in rows:
        if r["fn_type"] != "theater":
            continue
        members = r.get("member_fn_ids") or []
        publishers = r.get("publishers") or []
        if not members or not publishers or r["stance"] is None:
            counts[r["id"]] = 0
            continue
        cur.execute(
            THEATER_COUNT_SQL,
            {"members": members, "stance": r["stance"], "publishers": publishers},
        )
        counts[r["id"]] = cur.fetchone()["c"]
    return counts
