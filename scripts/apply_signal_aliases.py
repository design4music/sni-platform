"""Apply signal alias map + recategorizations to title_labels.

Safe to re-run: idempotent (aliases applied again produce same result).
Run with --dry-run to preview counts without writing.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import execute_batch

from core.signal_aliases import normalize_signals

CATEGORIES = [
    "persons",
    "orgs",
    "places",
    "commodities",
    "policies",
    "systems",
    "named_events",
]


def main():
    parser = argparse.ArgumentParser(description="Apply signal aliases to title_labels")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without writing"
    )
    parser.add_argument(
        "--db-url",
        default="postgresql://postgres@localhost:5432/sni_v2",
        help="Database connection URL",
    )
    args = parser.parse_args()

    conn = psycopg2.connect(args.db_url)
    cur = conn.cursor()

    # Fetch all rows that have at least one signal column populated
    where = " OR ".join(f"{c} IS NOT NULL" for c in CATEGORIES)
    cur.execute(
        f"SELECT title_id, {', '.join(CATEGORIES)} FROM title_labels WHERE {where}"
    )
    rows = cur.fetchall()
    print(f"Loaded {len(rows)} rows with signals")

    updates = []
    stats = {cat: {"aliases": 0, "moves": 0} for cat in CATEGORIES}

    for row in rows:
        title_id = row[0]
        originals = {cat: row[i + 1] for i, cat in enumerate(CATEGORIES)}

        new_values = {}
        all_moves: dict[str, list[str]] = {}

        # Phase 1: normalize each category (aliases + detect moves)
        for cat in CATEGORIES:
            normalized, moves = normalize_signals(cat, originals[cat])
            new_values[cat] = normalized
            for target_cat, vals in moves.items():
                all_moves.setdefault(target_cat, [])
                all_moves[target_cat].extend(vals)

        # Phase 2: merge moved signals into target categories
        for target_cat, moved_vals in all_moves.items():
            existing = new_values.get(target_cat, [])
            seen = {v.lower() for v in existing}
            for v in moved_vals:
                if v.lower() not in seen:
                    existing.append(v)
                    seen.add(v.lower())
            new_values[target_cat] = existing

        # Check if anything changed
        changed = False
        for cat in CATEGORIES:
            old = originals[cat] or []
            new = new_values[cat]
            if old != new:
                changed = True
                if len(new) < len(old):
                    stats[cat]["aliases"] += 1
                # Check if signals were moved out of this category
                for target_cat, moved_vals in all_moves.items():
                    if any(
                        v in (originals[cat] or [])
                        for v in [
                            k
                            for k, (tc, _) in __import__(
                                "core.signal_aliases", fromlist=["SIGNAL_MOVES"]
                            )
                            .SIGNAL_MOVES.get(cat, {})
                            .items()
                        ]
                    ):
                        stats[cat]["moves"] += 1
                        break

        if changed:
            updates.append((title_id, new_values))

    print(f"\nRows to update: {len(updates)}")
    for cat in CATEGORIES:
        s = stats[cat]
        if s["aliases"] or s["moves"]:
            print(
                f"  {cat}: {s['aliases']} alias merges, {s['moves']} recategorizations"
            )

    if args.dry_run:
        print("\n[DRY RUN] No changes written.")
        conn.close()
        return

    if not updates:
        print("Nothing to update.")
        conn.close()
        return

    # Write updates
    set_clause = ", ".join(f"{cat} = %({cat})s" for cat in CATEGORIES)
    sql = f"UPDATE title_labels SET {set_clause}, updated_at = NOW() WHERE title_id = %(title_id)s"

    batch = []
    for title_id, new_values in updates:
        params = {"title_id": title_id}
        for cat in CATEGORIES:
            vals = new_values[cat]
            params[cat] = vals if vals else None
        batch.append(params)

    execute_batch(cur, sql, batch, page_size=500)
    conn.commit()
    print(f"\nUpdated {len(updates)} rows.", flush=True)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
