"""Restore gate_keep flags for titles that have entities"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def restore_gate_keep():
    print("=" * 60)
    print("RESTORING GATE_KEEP FLAGS")
    print("=" * 60)

    with get_db_session() as session:
        # Set gate_keep=true for all titles with entities
        # (These were marked as strategic by Phase 2)
        print("\nSetting gate_keep=true for titles with entities...")

        result = session.execute(
            text(
                """
            UPDATE titles
            SET gate_keep = true
            WHERE entities IS NOT NULL
            AND gate_keep = false;
        """
            )
        )

        updated = result.rowcount
        session.commit()

        print(f"  Updated: {updated} titles")

        # Verify
        stats = session.execute(
            text(
                """
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN gate_keep = true THEN 1 END) as strategic,
                COUNT(CASE WHEN entities IS NOT NULL THEN 1 END) as with_entities,
                COUNT(CASE WHEN event_family_id IS NOT NULL THEN 1 END) as assigned
            FROM titles;
        """
            )
        ).fetchone()

        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)
        print(f"Total titles: {stats[0]:,}")
        print(f"Strategic (gate_keep=true): {stats[1]:,}")
        print(f"With entities: {stats[2]:,}")
        print(f"Assigned to EF: {stats[3]:,}")
        print(f"Unassigned strategic: {stats[1] - stats[3]:,}")
        print("=" * 60)

        if stats[1] > 0:
            print("\n[OK] Ready for Phase 3 processing!")
        else:
            print("\n[WARNING] No strategic titles found")


if __name__ == "__main__":
    restore_gate_keep()
