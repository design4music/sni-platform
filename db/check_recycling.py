"""
Check recycling bin and P3.5a validation results
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def check_recycling():
    with get_db_session() as session:
        print("\n=== P3.5a VALIDATION RESULTS ===\n")

        # Check recycling bin
        recycling_count = session.execute(
            text(
                """
            SELECT COUNT(*) FROM titles
            WHERE processing_status = 'recycling'
        """
            )
        ).scalar()
        print(f"Titles in recycling bin: {recycling_count}")

        if recycling_count > 0:
            print("\nSample of recycled titles:")
            sample = session.execute(
                text(
                    """
                SELECT id, title_display, processing_status
                FROM titles
                WHERE processing_status = 'recycling'
                LIMIT 5
            """
                )
            ).fetchall()

            for row in sample:
                print(f"  {str(row.id)[:8]}... - {row.title_display[:60]}...")

        # Count all processing statuses
        print("\nAll processing statuses:")
        statuses = session.execute(
            text(
                """
            SELECT processing_status, COUNT(*) as count
            FROM titles
            GROUP BY processing_status
            ORDER BY count DESC
        """
            )
        ).fetchall()

        for row in statuses:
            status_name = row.processing_status or "NULL"
            print(f"  {status_name}: {row.count:,}")

        # Check if validation ran by looking at logs pattern
        print("\n=== TITLE ACCOUNTING ===")

        strategic_total = session.execute(
            text(
                """
            SELECT COUNT(*) FROM titles WHERE gate_keep = true
        """
            )
        ).scalar()

        assigned = session.execute(
            text(
                """
            SELECT COUNT(*) FROM titles WHERE processing_status = 'assigned'
        """
            )
        ).scalar()

        recycling = session.execute(
            text(
                """
            SELECT COUNT(*) FROM titles WHERE processing_status = 'recycling'
        """
            )
        ).scalar()

        pending = session.execute(
            text(
                """
            SELECT COUNT(*) FROM titles WHERE processing_status = 'pending'
        """
            )
        ).scalar()

        print(f"Total strategic titles: {strategic_total:,}")
        print(f"  Assigned: {assigned:,}")
        print(f"  Recycling: {recycling:,}")
        print(f"  Pending: {pending:,}")
        print(f"  Other: {strategic_total - assigned - recycling - pending:,}")


if __name__ == "__main__":
    check_recycling()
