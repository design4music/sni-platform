"""Clean titles for fresh Phase 2 + Phase 3 run"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def clean_titles():
    print("=" * 60)
    print("PREPARING TITLES FOR FRESH PHASE 2 + PHASE 3 RUN")
    print("=" * 60)

    with get_db_session() as session:
        # Get current state
        stats = session.execute(
            text(
                """
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN entities IS NOT NULL THEN 1 END) as with_entities,
                COUNT(CASE WHEN gate_keep = true THEN 1 END) as strategic,
                COUNT(CASE WHEN event_family_id IS NOT NULL THEN 1 END) as assigned
            FROM titles;
        """
            )
        ).fetchone()

        print("\nCurrent state:")
        print(f"  Total titles: {stats[0]:,}")
        print(f"  With entities: {stats[1]:,}")
        print(f"  Strategic (gate_keep=true): {stats[2]:,}")
        print(f"  Assigned to EF: {stats[3]:,}")

        # Clear entities
        if stats[1] > 0:
            print(f"\nClearing entities for {stats[1]:,} titles...")
            session.execute(
                text("UPDATE titles SET entities = NULL WHERE entities IS NOT NULL")
            )
            print("  [OK] Entities cleared")

        # Reset gate_keep to false
        if stats[2] > 0:
            print(f"\nResetting gate_keep to false for {stats[2]:,} titles...")
            session.execute(
                text("UPDATE titles SET gate_keep = false WHERE gate_keep = true")
            )
            print("  [OK] gate_keep reset")

        # Clear event_family_id
        if stats[3] > 0:
            print(f"\nClearing event_family_id for {stats[3]:,} titles...")
            session.execute(
                text(
                    "UPDATE titles SET event_family_id = NULL WHERE event_family_id IS NOT NULL"
                )
            )
            print("  [OK] event_family_id cleared")

        session.commit()

        # Verify final state
        final = session.execute(
            text(
                """
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN entities IS NOT NULL THEN 1 END) as with_entities,
                COUNT(CASE WHEN gate_keep = true THEN 1 END) as strategic,
                COUNT(CASE WHEN event_family_id IS NOT NULL THEN 1 END) as assigned
            FROM titles;
        """
            )
        ).fetchone()

        print("\n" + "=" * 60)
        print("FINAL STATE")
        print("=" * 60)
        print(f"Total titles: {final[0]:,}")
        print(f"With entities: {final[1]:,} (should be 0)")
        print(f"Strategic (gate_keep=true): {final[2]:,} (should be 0)")
        print(f"Assigned to EF: {final[3]:,} (should be 0)")
        print("=" * 60)

        if final[1] == 0 and final[2] == 0 and final[3] == 0:
            print("\n[OK] Titles ready for fresh Phase 2 + Phase 3 run!")
            print("\nNext steps:")
            print("  1. python -m apps.filter.main --max-titles 100")
            print(
                "  2. python -m apps.generate.incident_processor run-incident-processing 50"
            )
        else:
            print("\n[WARNING] Some fields not cleared properly")


if __name__ == "__main__":
    clean_titles()
