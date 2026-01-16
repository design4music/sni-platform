"""
Taxonomy Tools - Restore from Snapshot

Restores taxonomy_v3 table from a snapshot JSON file.
Use this for rollback after pruning if needed.

Safety features:
- Dry-run mode shows what would change
- Only updates items present in snapshot
- Never deletes items not in snapshot
- Preserves created_at timestamps

Usage:
    python restore_taxonomy_snapshot.py --snapshot out/taxonomy_snapshots/taxonomy_full_20260105_150000.json --mode dry-run
    python restore_taxonomy_snapshot.py --snapshot out/taxonomy_snapshots/taxonomy_full_20260105_150000.json --mode apply
"""

import argparse
import json
from pathlib import Path

from common import get_db_connection


def load_snapshot(snapshot_path):
    """Load snapshot JSON file"""
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    return snapshot


def restore_taxonomy(snapshot, dry_run=True):
    """
    Restore taxonomy from snapshot.

    Updates:
    - aliases (JSONB)
    - is_active
    - is_stop_word
    - item_raw
    - centroid_ids

    Preserves:
    - id (uses snapshot id)
    - created_at (preserves original)
    - updated_at (sets to NOW())
    """
    conn = get_db_connection()

    items = snapshot["taxonomy"]

    if dry_run:
        print("\nDRY-RUN MODE: No changes will be made.")
        print(f"\nWould restore {len(items)} taxonomy items:")

        # Show first 5 items
        for item in items[:5]:
            alias_count = sum(
                len(aliases) for aliases in item.get("aliases", {}).values()
            )
            print(
                f"  {item['item_raw']}: {alias_count} aliases, active={item['is_active']}, stop_word={item['is_stop_word']}"
            )

        if len(items) > 5:
            print(f"  ... and {len(items) - 5} more items")

        return

    # Apply restoration
    updated_count = 0
    inserted_count = 0

    with conn.cursor() as cur:
        for item in items:
            # Check if item exists
            cur.execute("SELECT id FROM taxonomy_v3 WHERE id = %s", (item["id"],))
            exists = cur.fetchone()

            if exists:
                # Update existing item
                # Extract first element from centroid_ids array (snapshots have array format)
                centroid_id = item["centroid_ids"][0] if item["centroid_ids"] else None
                cur.execute(
                    """
                    UPDATE taxonomy_v3
                    SET item_raw = %s,
                        centroid_id = %s,
                        aliases = %s,
                        is_active = %s,
                        is_stop_word = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (
                        item["item_raw"],
                        centroid_id,
                        json.dumps(item["aliases"]),
                        item["is_active"],
                        item["is_stop_word"],
                        item["id"],
                    ),
                )
                updated_count += 1
            else:
                # Insert new item (shouldn't happen in rollback, but handle it)
                # Extract first element from centroid_ids array (snapshots have array format)
                centroid_id = item["centroid_ids"][0] if item["centroid_ids"] else None
                cur.execute(
                    """
                    INSERT INTO taxonomy_v3
                    (id, item_raw, centroid_id, aliases, is_active, is_stop_word, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        item["id"],
                        item["item_raw"],
                        centroid_id,
                        json.dumps(item["aliases"]),
                        item["is_active"],
                        item["is_stop_word"],
                        item.get("created_at"),
                    ),
                )
                inserted_count += 1

    conn.commit()
    conn.close()

    print("\nRestoration complete:")
    print(f"  Updated: {updated_count} items")
    print(f"  Inserted: {inserted_count} items")


def main():
    parser = argparse.ArgumentParser(description="Restore taxonomy from snapshot JSON")
    parser.add_argument(
        "--snapshot",
        required=True,
        help="Path to snapshot JSON file",
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "apply"],
        default="dry-run",
        help="Execution mode (default: dry-run)",
    )

    args = parser.parse_args()

    snapshot_path = Path(args.snapshot)

    if not snapshot_path.exists():
        print(f"ERROR: Snapshot file not found: {snapshot_path}")
        return

    print("=" * 60)
    print("TAXONOMY SNAPSHOT RESTORE")
    print("=" * 60)
    print(f"Snapshot: {snapshot_path}")
    print(f"Mode: {args.mode}")

    # Load snapshot
    print("\nLoading snapshot...")
    snapshot = load_snapshot(snapshot_path)

    print(f"  Snapshot date: {snapshot['metadata']['export_timestamp']}")
    print(f"  Total items: {snapshot['metadata']['total_items']}")
    print(f"  Stop words: {snapshot['metadata']['stop_words']}")
    print(f"  Matching terms: {snapshot['metadata']['matching_terms']}")

    # Restore
    print("\nRestoring taxonomy...")
    restore_taxonomy(snapshot, dry_run=(args.mode == "dry-run"))

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)

    if args.mode == "dry-run":
        print("\nTo apply restoration, run with: --mode apply")


if __name__ == "__main__":
    main()
