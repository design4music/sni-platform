"""
Taxonomy Tools - Export Snapshot

Exports full taxonomy to JSON for:
- Safety backups before pruning
- Git diffing to track changes
- Quick restore if needed

Usage:
    python export_taxonomy_snapshot.py
    python export_taxonomy_snapshot.py --centroid-id SYS-TECH
    python export_taxonomy_snapshot.py --out custom_path.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from common import get_db_connection


def export_taxonomy(centroid_id=None):
    """
    Export taxonomy_v3 table to dict structure.

    Returns:
        dict with metadata and taxonomy items
    """
    conn = get_db_connection()

    with conn.cursor() as cur:
        if centroid_id:
            # Filter by specific centroid
            cur.execute(
                """
                SELECT id, item_raw, centroid_id, aliases, is_active, is_stop_word,
                       created_at, updated_at
                FROM taxonomy_v3
                WHERE is_active = true
                  AND centroid_id = %s
                ORDER BY item_raw
                """,
                (centroid_id,),
            )
        else:
            # All active taxonomy items
            cur.execute(
                """
                SELECT id, item_raw, centroid_id, aliases, is_active, is_stop_word,
                       created_at, updated_at
                FROM taxonomy_v3
                WHERE is_active = true
                ORDER BY item_raw
                """
            )

        taxonomy_items = cur.fetchall()

    conn.close()

    # Format items
    items = []
    for (
        id,
        item_raw,
        centroid_id,
        aliases,
        is_active,
        is_stop_word,
        created_at,
        updated_at,
    ) in taxonomy_items:
        items.append(
            {
                "id": str(id),
                "item_raw": item_raw,
                "centroid_ids": (
                    [centroid_id] if centroid_id else []
                ),  # Keep as array for backward compat
                "aliases": aliases if aliases else {},
                "is_active": is_active,
                "is_stop_word": is_stop_word,
                "created_at": created_at.isoformat() if created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None,
            }
        )

    # Build snapshot with metadata
    snapshot = {
        "metadata": {
            "export_timestamp": datetime.utcnow().isoformat(),
            "centroid_filter": centroid_id,
            "total_items": len(items),
            "stop_words": sum(1 for item in items if item["is_stop_word"]),
            "matching_terms": sum(1 for item in items if not item["is_stop_word"]),
        },
        "taxonomy": items,
    }

    return snapshot


def main():
    parser = argparse.ArgumentParser(
        description="Export taxonomy snapshot for safety and review"
    )
    parser.add_argument(
        "--centroid-id",
        help="Specific centroid ID (e.g., SYS-TECH). Omit for full export.",
    )
    parser.add_argument(
        "--out",
        help="Output file path. Default: out/taxonomy_snapshots/<timestamp>.json",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("TAXONOMY SNAPSHOT EXPORT")
    print("=" * 60)
    print(f"Centroid filter: {args.centroid_id or 'NONE (full export)'}")

    # Determine output path
    if args.out:
        out_file = Path(args.out)
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        centroid_suffix = f"_{args.centroid_id}" if args.centroid_id else "_full"
        out_dir = Path(__file__).parent.parent.parent / "out" / "taxonomy_snapshots"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"taxonomy{centroid_suffix}_{timestamp}.json"

    print(f"Output: {out_file}")

    # Export taxonomy
    print("\nExporting taxonomy...")
    snapshot = export_taxonomy(args.centroid_id)

    print(f"  Total items: {snapshot['metadata']['total_items']}")
    print(f"  Stop words: {snapshot['metadata']['stop_words']}")
    print(f"  Matching terms: {snapshot['metadata']['matching_terms']}")

    # Write to file
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    print(f"\nWrote: {out_file}")
    print(f"Size: {out_file.stat().st_size / 1024:.1f} KB")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)
    print("\nTo restore this snapshot:")
    print("  1. Review the JSON file")
    print("  2. Use database migration script or manual SQL updates")
    print("  3. Compare with current state using git diff")


if __name__ == "__main__":
    main()
