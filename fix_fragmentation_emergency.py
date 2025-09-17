#!/usr/bin/env python3
"""
EMERGENCY: Fix unacceptable Event Family fragmentation
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def merge_trump_fragmentation():
    """Merge fragmented Trump administration EFs immediately"""

    with get_db_session() as session:
        print("=== EMERGENCY FRAGMENTATION FIX ===\n")

        # Get the fragmented Trump EFs
        trump_efs = session.execute(
            text(
                """
            SELECT id, title, key_actors, event_type, primary_theater, ef_key,
                   source_title_ids, created_at,
                   (SELECT COUNT(*) FROM titles WHERE event_family_id = ef.id) as title_count
            FROM event_families ef
            WHERE status = 'active' 
            AND ('Donald Trump' = ANY(key_actors))
            AND primary_theater = 'US_DOMESTIC'
            AND event_type = 'Domestic Politics'
            ORDER BY title_count DESC, created_at ASC
        """
            )
        ).fetchall()

        if len(trump_efs) <= 1:
            print("No fragmentation to fix")
            return

        # Keep the largest/oldest one as the master
        master_ef = trump_efs[0]
        duplicate_efs = trump_efs[1:]

        print(f"MASTER EF (keeping): {master_ef.title}")
        print(f"  ID: {master_ef.id}")
        print(f"  Titles: {master_ef.title_count}")
        print(f"  Created: {master_ef.created_at}")
        print()

        print(f"DUPLICATES TO MERGE ({len(duplicate_efs)}):")
        for dup in duplicate_efs:
            print(f"  {dup.title} ({dup.title_count} titles)")
        print()

        # Move all titles from duplicates to master
        total_moved = 0
        for dup_ef in duplicate_efs:
            # Move titles
            result = session.execute(
                text(
                    """
                UPDATE titles 
                SET event_family_id = :master_id,
                    ef_assignment_reason = 'Emergency fragmentation fix - merged into master EF',
                    ef_assignment_at = NOW()
                WHERE event_family_id = :dup_id
            """
                ),
                {"master_id": master_ef.id, "dup_id": dup_ef.id},
            )

            moved_count = result.rowcount
            total_moved += moved_count

            # Mark duplicate as merged
            session.execute(
                text(
                    """
                UPDATE event_families 
                SET status = 'merged',
                    merged_into = :master_id,
                    merge_rationale = 'Emergency fix: Identical Trump domestic policy EF fragmentation'
                WHERE id = :dup_id
            """
                ),
                {"master_id": master_ef.id, "dup_id": dup_ef.id},
            )

            print(f"  Merged {dup_ef.title}: {moved_count} titles moved")

        # Update master EF source_title_ids
        new_title_ids = session.execute(
            text(
                """
            SELECT ARRAY_AGG(id::text) as title_ids
            FROM titles 
            WHERE event_family_id = :master_id
        """
            ),
            {"master_id": master_ef.id},
        ).scalar()

        session.execute(
            text(
                """
            UPDATE event_families 
            SET source_title_ids = :title_ids,
                updated_at = NOW(),
                processing_notes = 'Emergency fragmentation fix - consolidated ' || :dup_count || ' duplicate EFs'
            WHERE id = :master_id
        """
            ),
            {
                "master_id": master_ef.id,
                "title_ids": new_title_ids or [],
                "dup_count": len(duplicate_efs),
            },
        )

        session.commit()

        print("\n✅ FRAGMENTATION FIXED!")
        print(f"  Moved {total_moved} titles to master EF")
        print(f"  Merged {len(duplicate_efs)} duplicate EFs")
        print(f"  Master EF now has {master_ef.title_count + total_moved} titles")


def check_other_fragmentation():
    """Check for other fragmentation issues"""

    with get_db_session() as session:
        print("\n=== CHECKING FOR OTHER FRAGMENTATION ===")

        # Check for other potential duplicates
        fragmentation = session.execute(
            text(
                """
            SELECT 
                primary_theater,
                event_type,
                COUNT(*) as ef_count,
                STRING_AGG(title, ' | ') as titles,
                STRING_AGG(id::text, ',') as ef_ids
            FROM event_families 
            WHERE status = 'active'
            GROUP BY primary_theater, event_type
            HAVING COUNT(*) > 2  -- More than 2 EFs with same theater+type is suspicious
            ORDER BY ef_count DESC
        """
            )
        ).fetchall()

        if fragmentation:
            print("POTENTIAL ADDITIONAL FRAGMENTATION:")
            for frag in fragmentation:
                print(
                    f"\n{frag.primary_theater} + {frag.event_type}: {frag.ef_count} EFs"
                )
                titles = frag.titles.split(" | ")
                for i, title in enumerate(titles):
                    print(f"  {i+1}. {title}")
        else:
            print("No other obvious fragmentation detected")


if __name__ == "__main__":
    merge_trump_fragmentation()
    check_other_fragmentation()
