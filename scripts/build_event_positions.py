"""P2: rebuild the event_positions derived table (SPEC v2 §5.4, D-100).

A title carries a position via its card (title_narratives -> position_id for
atomic cards; the theater roll-up for theater cards), and belongs to events via
event_v3_titles. event_positions is that roll-up, per event. Fully derived:
this script DELETEs and re-INSERTs every row in one transaction, so a re-run is
idempotent.

Verification: the per-card distinct-title counts implied by the derivation must
equal narrative_counts.effective_counts (the trusted atomic + theater-rollup
logic the FN page uses). If they diverge, the derivation predicates drifted --
fail loud, write nothing.

  python scripts/build_event_positions.py
  python scripts/build_event_positions.py --verify-only
"""

import argparse
import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.narrative_counts import effective_counts  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# title -> position contribution set, unioned over the two card paths. DISTINCT
# (title_id, position_id) so a title hitting two cards of the SAME position counts
# once. Predicates mirror narrative_counts.THEATER_COUNT_SQL exactly.
TITLE_POSITION_CTE = """
    WITH title_position AS (
        SELECT DISTINCT tn.title_id, n.position_id
          FROM title_narratives tn
          JOIN narratives_v2 n ON n.id = tn.narrative_id
          JOIN friction_nodes fn ON fn.id = n.fn_id
         WHERE n.position_id IS NOT NULL AND n.is_active AND fn.fn_type = 'atomic'
        UNION
        SELECT DISTINCT tn.title_id, tcard.position_id
          FROM narratives_v2 tcard
          JOIN friction_nodes tfn ON tfn.id = tcard.fn_id AND tfn.fn_type = 'theater'
          JOIN narratives_v2 an ON an.fn_id = ANY(tfn.member_fn_ids)
                                AND an.stance IS NOT NULL
                                AND sign(an.stance) = sign(tcard.stance)
          JOIN friction_nodes afn ON afn.id = an.fn_id AND afn.fn_type = 'atomic'
          JOIN title_narratives tn ON tn.narrative_id = an.id
          JOIN titles_v3 t ON t.id = tn.title_id
                           AND t.publisher_name = ANY(tcard.publishers)
         WHERE tcard.position_id IS NOT NULL AND tcard.is_active
           AND tcard.stance IS NOT NULL
    )
"""

REBUILD_SQL = (
    TITLE_POSITION_CTE
    + """
    INSERT INTO event_positions (event_id, position_id, title_count)
    SELECT evt.event_id, tp.position_id, COUNT(DISTINCT tp.title_id)::int
      FROM title_position tp
      JOIN event_v3_titles evt ON evt.title_id = tp.title_id
     GROUP BY evt.event_id, tp.position_id
"""
)

# per-card distinct-title counts implied by the same predicates (card-keyed),
# for the reconciliation check against effective_counts.
CARD_TITLES_SQL = """
    WITH card_titles AS (
        SELECT n.id AS card_id, tn.title_id
          FROM title_narratives tn
          JOIN narratives_v2 n ON n.id = tn.narrative_id
          JOIN friction_nodes fn ON fn.id = n.fn_id
         WHERE n.is_active AND fn.fn_type = 'atomic'
        UNION
        SELECT tcard.id AS card_id, tn.title_id
          FROM narratives_v2 tcard
          JOIN friction_nodes tfn ON tfn.id = tcard.fn_id AND tfn.fn_type = 'theater'
          JOIN narratives_v2 an ON an.fn_id = ANY(tfn.member_fn_ids)
                                AND an.stance IS NOT NULL
                                AND sign(an.stance) = sign(tcard.stance)
          JOIN friction_nodes afn ON afn.id = an.fn_id AND afn.fn_type = 'atomic'
          JOIN title_narratives tn ON tn.narrative_id = an.id
          JOIN titles_v3 t ON t.id = tn.title_id
                           AND t.publisher_name = ANY(tcard.publishers)
         WHERE tcard.is_active AND tcard.stance IS NOT NULL
    )
    SELECT card_id, COUNT(DISTINCT title_id)::int AS c
      FROM card_titles GROUP BY card_id
"""


def connect():
    load_dotenv(ROOT / ".env")
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def verify(cur):
    """Per-card derivation counts must equal effective_counts. Returns mismatches."""
    cur.execute(CARD_TITLES_SQL)
    derived = {r["card_id"]: r["c"] for r in cur.fetchall()}

    cur.execute(
        """
        SELECT n.id, fn.fn_type, n.stance, n.publishers, fn.member_fn_ids
          FROM narratives_v2 n JOIN friction_nodes fn ON fn.id = n.fn_id
         WHERE n.is_active
    """
    )
    rows = [dict(r) for r in cur.fetchall()]
    trusted = effective_counts(cur, rows)

    mismatches = []
    for cid, tc in trusted.items():
        dc = derived.get(cid, 0)
        if dc != tc:
            mismatches.append((cid, dc, tc))
    return mismatches, len(rows)


def rebuild_event_positions(conn, verify_first=True):
    """Full idempotent rebuild of event_positions. Reuses an open connection so
    the daemon can call it inside run_fn_refresh after link_titles. Returns a
    summary dict. Raises on reconciliation failure (writes nothing)."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if verify_first:
        mismatches, ncards = verify(cur)
        if mismatches:
            raise RuntimeError(
                f"event_positions reconcile failed: {len(mismatches)}/{ncards} "
                f"cards diverge, e.g. {mismatches[:5]}"
            )
    cur.execute("DELETE FROM event_positions")
    cur.execute(REBUILD_SQL)
    n = cur.rowcount
    conn.commit()
    cur.execute(
        """
        SELECT count(*) AS rows, count(DISTINCT position_id) AS positions,
               count(DISTINCT event_id) AS events, sum(title_count) AS title_links,
               max(title_count) AS max_tc
          FROM event_positions
    """
    )
    return dict(cur.fetchone(), inserted=n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()

    conn = connect()
    cur = conn.cursor()

    mismatches, ncards = verify(cur)
    if mismatches:
        print(
            f"RECONCILE FAILED: {len(mismatches)}/{ncards} cards diverge "
            "(derived != effective_counts):"
        )
        for cid, dc, tc in mismatches[:20]:
            print(f"  {cid}: derived={dc} effective={tc}")
        raise SystemExit(1)
    print(f"reconcile OK: {ncards} cards, derived counts == effective_counts")

    if args.verify_only:
        conn.close()
        return

    s = rebuild_event_positions(conn, verify_first=False)
    print(
        f"rebuilt event_positions: {s['rows']} rows "
        f"({s['inserted']} inserted), {s['positions']} positions, {s['events']} events, "
        f"{s['title_links']} title-links, max title_count={s['max_tc']}"
    )
    conn.close()


if __name__ == "__main__":
    main()
