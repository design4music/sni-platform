"""
Quick check of processing status after v2.1 test
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def check_status():
    with get_db_session() as session:
        print("\n=== PROCESSING STATUS CHECK ===\n")

        # Count by processing_status
        print("Processing Status Distribution (strategic titles):")
        result = session.execute(
            text(
                """
            SELECT processing_status, COUNT(*) as count
            FROM titles
            WHERE gate_keep = true
            GROUP BY processing_status
            ORDER BY count DESC
        """
            )
        ).fetchall()

        for row in result:
            print(f"  {row.processing_status or 'NULL'}: {row.count:,}")

        # Count Event Families
        ef_count = session.execute(text("SELECT COUNT(*) FROM event_families")).scalar()
        print(f"\nEvent Families: {ef_count}")

        # Check which titles are assigned to EFs
        assigned = session.execute(
            text(
                """
            SELECT COUNT(*) FROM titles
            WHERE event_family_id IS NOT NULL
        """
            )
        ).scalar()
        print(f"Titles with event_family_id: {assigned:,}")

        # Get sample of assigned titles
        if assigned > 0:
            print("\nSample of assigned titles:")
            sample = session.execute(
                text(
                    """
                SELECT id, event_family_id, processing_status
                FROM titles
                WHERE event_family_id IS NOT NULL
                LIMIT 5
            """
                )
            ).fetchall()

            for row in sample:
                print(
                    f"  Title {str(row.id)[:8]}... -> EF {str(row.event_family_id)[:8]}... (status: {row.processing_status})"
                )

        # Check EF source_title_ids
        print("\nEvent Family Title Counts:")
        ef_titles = session.execute(
            text(
                """
            SELECT id, title, ARRAY_LENGTH(source_title_ids, 1) as title_count
            FROM event_families
            ORDER BY created_at DESC
        """
            )
        ).fetchall()

        for row in ef_titles:
            print(
                f"  EF {str(row.id)[:8]}...: {row.title_count or 0} titles - {row.title[:60]}..."
            )


if __name__ == "__main__":
    check_status()
