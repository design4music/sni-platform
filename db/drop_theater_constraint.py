"""Drop restrictive theater constraint"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def drop_constraint():
    print("=" * 60)
    print("REMOVING RESTRICTIVE THEATER CONSTRAINT")
    print("=" * 60)

    with get_db_session() as session:
        # Drop old constraint
        print("\nDropping chk_primary_theater constraint...")
        session.execute(
            text(
                "ALTER TABLE event_families DROP CONSTRAINT IF EXISTS chk_primary_theater;"
            )
        )
        session.commit()
        print("  [OK] Constraint dropped")

        # Verify
        result = session.execute(
            text(
                """
            SELECT conname
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            WHERE t.relname = 'event_families'
            AND conname = 'chk_primary_theater';
        """
            )
        ).fetchone()

        if result:
            print("\n  [ERROR] Constraint still exists!")
        else:
            print("\n  [OK] VERIFIED: Constraint removed successfully")

    print("\n" + "=" * 60)
    print("SUCCESS")
    print("=" * 60)
    print("Theater field now accepts:")
    print("  - Country names (United States, China, Russia, etc.)")
    print("  - Bilateral patterns (US-China Relations, etc.)")
    print("  - Global (for tech/general news)")
    print("=" * 60)


if __name__ == "__main__":
    drop_constraint()
