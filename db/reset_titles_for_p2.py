"""
Reset titles for fresh Phase 2 processing:
- Clear entities JSONB field
- Reset gate_keep to false
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def reset_titles_for_p2():
    """Clear entities and reset gate_keep for all titles"""

    print("=" * 60)
    print("RESET TITLES FOR PHASE 2 PROCESSING")
    print("=" * 60)
    print("This will:")
    print("  1. Clear all entities (set to NULL)")
    print("  2. Reset gate_keep to false for all titles")
    print("=" * 60 + "\n")

    with get_db_session() as session:
        # Get current stats
        total = session.execute(text("SELECT COUNT(*) FROM titles")).scalar()
        with_entities = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE entities IS NOT NULL")
        ).scalar()
        strategic = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE gate_keep = true")
        ).scalar()

        print("Current state:")
        print(f"  Total titles: {total:,}")
        print(f"  Titles with entities: {with_entities:,}")
        print(f"  Strategic titles (gate_keep=true): {strategic:,}\n")

        # Clear entities
        print("Clearing entities field...")
        session.execute(
            text("UPDATE titles SET entities = NULL WHERE entities IS NOT NULL")
        )
        session.commit()
        print(f"  Cleared {with_entities:,} entity records\n")

        # Reset gate_keep
        print("Resetting gate_keep to false...")
        session.execute(
            text("UPDATE titles SET gate_keep = false WHERE gate_keep = true")
        )
        session.commit()
        print(f"  Reset {strategic:,} strategic flags\n")

        # Verify
        after_entities = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE entities IS NOT NULL")
        ).scalar()
        after_strategic = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE gate_keep = true")
        ).scalar()

        print("=" * 60)
        print("RESET COMPLETE")
        print("=" * 60)
        print(f"Total titles: {total:,}")
        print(f"Titles with entities: {after_entities:,} (should be 0)")
        print(f"Strategic titles: {after_strategic:,} (should be 0)")
        print("=" * 60)

        if after_entities == 0 and after_strategic == 0:
            print("\nSUCCESS: All titles ready for fresh Phase 2 processing!")
        else:
            print("\nWARNING: Some records were not reset properly")


if __name__ == "__main__":
    reset_titles_for_p2()
