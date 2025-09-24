#!/usr/bin/env python3
"""
Remove over-engineered database fields that are never read by application logic.

Removes:
- gate_score, gate_actor_hit, gate_at, gate_reason (P2 filtering - only gate_keep is needed)
- ef_assignment_confidence, ef_assignment_reason, ef_assignment_at (P3 processing - only event_family_id is needed)

These fields contained hard-coded values and meaningless boilerplate text that no code ever reads.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database import get_db_session
from sqlalchemy import text

def run_migration():
    """Remove over-engineered fields from titles table"""
    with get_db_session() as session:
        print("Removing over-engineered fields from titles table...")

        # First, drop dependent views that reference gate_score
        print("  Dropping dependent views...")
        try:
            session.execute(text("DROP VIEW IF EXISTS strategic_titles"))
            print("  Dropped view: strategic_titles")
        except Exception as e:
            print(f"  Warning: Could not drop view strategic_titles: {e}")

        try:
            session.execute(text("DROP VIEW IF EXISTS legacy_strategic_titles"))
            print("  Dropped view: legacy_strategic_titles")
        except Exception as e:
            print(f"  Warning: Could not drop view legacy_strategic_titles: {e}")

        # Remove gate fields (keep only gate_keep boolean)
        gate_fields = ["gate_score", "gate_actor_hit", "gate_at", "gate_reason"]
        for field in gate_fields:
            try:
                session.execute(text(f"ALTER TABLE titles DROP COLUMN IF EXISTS {field}"))
                print(f"  Removed {field}")
            except Exception as e:
                print(f"  Warning: Could not remove {field}: {e}")

        # Remove EF assignment fields (keep only event_family_id)
        ef_fields = ["ef_assignment_confidence", "ef_assignment_reason", "ef_assignment_at"]
        for field in ef_fields:
            try:
                session.execute(text(f"ALTER TABLE titles DROP COLUMN IF EXISTS {field}"))
                print(f"  Removed {field}")
            except Exception as e:
                print(f"  Warning: Could not remove {field}: {e}")

        session.commit()
        print("Migration completed successfully.")
        print("Simplified schema keeps only essential fields: gate_keep (boolean), event_family_id (FK)")

if __name__ == "__main__":
    run_migration()