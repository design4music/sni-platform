"""Quick check of titles table count"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def check_titles():
    with get_db_session() as session:
        # Check total titles
        total = session.execute(text("SELECT COUNT(*) as count FROM titles;")).scalar()
        print(f"Total titles in database: {total:,}")

        # Check with gate_keep=true
        strategic = session.execute(
            text("SELECT COUNT(*) as count FROM titles WHERE gate_keep = true;")
        ).scalar()
        print(f"Strategic titles (gate_keep=true): {strategic:,}")

        # Check assigned vs unassigned
        assigned = session.execute(
            text(
                "SELECT COUNT(*) as count FROM titles WHERE event_family_id IS NOT NULL;"
            )
        ).scalar()
        print(f"Titles with EF assignment: {assigned:,}")
        print(f"Unassigned strategic titles: {strategic - assigned:,}")


if __name__ == "__main__":
    check_titles()
