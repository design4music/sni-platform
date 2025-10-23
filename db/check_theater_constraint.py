"""Check current theater constraint"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def check_theater_constraint():
    with get_db_session() as session:
        # Get constraint definition
        result = session.execute(
            text(
                """
            SELECT conname, pg_get_constraintdef(c.oid) as definition
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            WHERE t.relname = 'event_families'
            AND conname = 'chk_primary_theater';
        """
            )
        ).fetchone()

        if result:
            print(f"Constraint: {result[0]}")
            print(f"Definition: {result[1]}")
        else:
            print("No chk_primary_theater constraint found")


if __name__ == "__main__":
    check_theater_constraint()
