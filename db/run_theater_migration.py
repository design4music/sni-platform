"""Run theater constraint migration"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def run_migration():
    migration_file = (
        Path(__file__).parent / "migrations" / "20251022_update_theater_constraint.sql"
    )

    print("=" * 60)
    print("UPDATING THEATER CONSTRAINT FOR MULTI-THEATER SYSTEM")
    print("=" * 60)

    with open(migration_file, "r") as f:
        sql = f.read()

    with get_db_session() as session:
        # Execute migration
        print("\nExecuting migration...")

        # Split by statements (simple approach)
        statements = [
            s.strip()
            for s in sql.split(";")
            if s.strip() and not s.strip().startswith("--")
        ]

        for stmt in statements:
            if stmt.upper().startswith("SELECT"):
                # Verification query
                result = session.execute(text(stmt))
                print("\nVerification:")
                for row in result:
                    print(f"  {row[0]}: {row[1]}")
            elif stmt:
                session.execute(text(stmt))
                print(f"  ✓ Executed: {stmt[:60]}...")

        session.commit()

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print("Theater constraint updated to support:")
    print("  - Country names (United States, China, Russia, etc.)")
    print("  - Bilateral patterns (US-China Relations, Russia-Ukraine Conflict, etc.)")
    print("  - Global (for tech/general news)")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
