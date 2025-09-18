#!/usr/bin/env python3
"""Quick database check script"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def check_results():
    """Check MAP/REDUCE processing results"""
    with get_db_session() as session:
        # Count assigned titles
        assigned_count = session.execute(
            text("SELECT COUNT(*) FROM titles WHERE event_family_id IS NOT NULL")
        ).scalar()

        # Count event families
        ef_count = session.execute(text("SELECT COUNT(*) FROM event_families")).scalar()

        # Count unassigned strategic titles
        unassigned_count = session.execute(
            text(
                "SELECT COUNT(*) FROM titles WHERE gate_keep = true AND event_family_id IS NULL"
            )
        ).scalar()

        # Recent activity
        recent_ef = session.execute(
            text(
                "SELECT COUNT(*) FROM event_families WHERE created_at >= NOW() - INTERVAL '10 minutes'"
            )
        ).scalar()

        recent_assignments = session.execute(
            text(
                "SELECT COUNT(*) FROM titles WHERE ef_assignment_at >= NOW() - INTERVAL '10 minutes'"
            )
        ).scalar()

        print("=== DATABASE RESULTS ===")
        print(f"Total assigned titles: {assigned_count}")
        print(f"Total Event Families: {ef_count}")
        print(f"Unassigned strategic titles: {unassigned_count}")
        print(f"Recent EFs (last 10 min): {recent_ef}")
        print(f"Recent assignments (last 10 min): {recent_assignments}")


if __name__ == "__main__":
    check_results()
