"""
Reset database for EF Generation v2.1 testing
Deletes all Event Families and clears title assignments
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def reset_for_v21_test():
    """
    Clean slate for v2.1 testing:
    1. Delete all event_families
    2. Delete all framed_narratives
    3. Clear event_family_id from titles
    4. Reset processing_status to 'pending'
    5. Keep entities and gate_keep (Phase 2 results)
    """
    print("=" * 60)
    print("RESET DATABASE FOR EF GENERATION v2.1 TEST")
    print("=" * 60)

    with get_db_session() as session:
        # Get current state
        print("\nCurrent state:")
        ef_count = session.execute(text("SELECT COUNT(*) FROM event_families")).scalar()
        fn_count = session.execute(
            text("SELECT COUNT(*) FROM framed_narratives")
        ).scalar()
        assigned_count = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE event_family_id IS NOT NULL")
        ).scalar()
        strategic_count = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE gate_keep = true")
        ).scalar()

        print(f"  Event Families: {ef_count:,}")
        print(f"  Framed Narratives: {fn_count:,}")
        print(f"  Titles assigned to EFs: {assigned_count:,}")
        print(f"  Strategic titles: {strategic_count:,}")

        # Confirm deletion
        if ef_count > 0 or fn_count > 0 or assigned_count > 0:
            print("\n" + "=" * 60)
            print("WARNING: This will DELETE all Event Families and assignments!")
            print("=" * 60)
            response = input("Continue? (yes/no): ")
            if response.lower() != "yes":
                print("Aborted.")
                return

        # Step 1: Delete all framed_narratives
        if fn_count > 0:
            print(f"\nDeleting {fn_count:,} framed narratives...")
            session.execute(text("DELETE FROM framed_narratives"))
            print("  [OK] Framed narratives deleted")

        # Step 2: Delete all event_families
        if ef_count > 0:
            print(f"\nDeleting {ef_count:,} event families...")
            session.execute(text("DELETE FROM event_families"))
            print("  [OK] Event families deleted")

        # Step 3: Clear event_family_id from titles
        if assigned_count > 0:
            print(f"\nClearing event_family_id for {assigned_count:,} titles...")
            session.execute(
                text(
                    "UPDATE titles SET event_family_id = NULL WHERE event_family_id IS NOT NULL"
                )
            )
            print("  [OK] Title assignments cleared")

        # Step 4: Reset processing_status to 'pending' for strategic titles
        print("\nResetting processing_status for strategic titles...")
        result = session.execute(
            text(
                """
            UPDATE titles
            SET processing_status = 'pending'
            WHERE gate_keep = true
        """
            )
        )
        print(f"  [OK] Reset {result.rowcount:,} titles to 'pending' status")

        session.commit()

        # Verify final state
        print("\n" + "=" * 60)
        print("FINAL STATE")
        print("=" * 60)

        final_efs = session.execute(
            text("SELECT COUNT(*) FROM event_families")
        ).scalar()
        final_fns = session.execute(
            text("SELECT COUNT(*) FROM framed_narratives")
        ).scalar()
        final_assigned = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE event_family_id IS NOT NULL")
        ).scalar()
        final_strategic = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE gate_keep = true")
        ).scalar()
        final_entities = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE entities IS NOT NULL")
        ).scalar()

        print(f"Event Families: {final_efs:,} (should be 0)")
        print(f"Framed Narratives: {final_fns:,} (should be 0)")
        print(f"Titles assigned to EFs: {final_assigned:,} (should be 0)")
        print(f"Strategic titles (gate_keep=true): {final_strategic:,} (preserved)")
        print(f"Titles with entities: {final_entities:,} (preserved)")
        print("=" * 60)

        if final_efs == 0 and final_fns == 0 and final_assigned == 0:
            print("\n[OK] Database reset complete! Ready for v2.1 testing")
            print("\nNext step:")
            print("  python -m apps.generate.incident_processor 100")
        else:
            print("\n[WARNING] Some records not cleared properly")


if __name__ == "__main__":
    reset_for_v21_test()
