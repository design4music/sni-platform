#!/usr/bin/env python3
"""
Reset Phase 2 Entity Enrichment (PostgreSQL only)
Clears entities while keeping title records
"""

from sqlalchemy import text

from core.database import get_db_session


def reset_phase2_postgres():
    """Reset Phase 2 entity enrichment in PostgreSQL"""

    print("=" * 60)
    print("Phase 2 Entity Enrichment Reset (PostgreSQL)")
    print("=" * 60)

    # Get counts before reset
    with get_db_session() as session:
        stats = session.execute(
            text(
                """
            SELECT
                COUNT(*) as total_titles,
                COUNT(entities) as enriched_titles,
                COUNT(CASE WHEN gate_keep = TRUE THEN 1 END) as strategic_titles
            FROM titles
        """
            )
        ).fetchone()

        print("\nBefore Reset:")
        print(f"  Total titles: {stats.total_titles}")
        print(f"  Enriched titles: {stats.enriched_titles}")
        print(f"  Strategic titles: {stats.strategic_titles}")

    # Reset PostgreSQL titles table
    print("\nResetting PostgreSQL titles table...")
    with get_db_session() as session:
        result = session.execute(
            text(
                """
            UPDATE titles
            SET gate_keep = FALSE,
                entities = NULL
            WHERE entities IS NOT NULL OR gate_keep = TRUE
        """
            )
        )
        session.commit()
        print(f"  [OK] Updated {result.rowcount} titles")

    # Verify reset
    print("\nVerifying reset...")
    with get_db_session() as session:
        stats = session.execute(
            text(
                """
            SELECT
                COUNT(*) as total_titles,
                COUNT(entities) as enriched_titles,
                COUNT(CASE WHEN gate_keep = TRUE THEN 1 END) as strategic_titles
            FROM titles
        """
            )
        ).fetchone()

        print("\nAfter Reset:")
        print(f"  Total titles: {stats.total_titles}")
        print(f"  Enriched titles: {stats.enriched_titles} (should be 0)")
        print(f"  Strategic titles: {stats.strategic_titles} (should be 0)")

    print("\n" + "=" * 60)
    print("Phase 2 PostgreSQL Reset Complete!")
    print("=" * 60)


if __name__ == "__main__":
    reset_phase2_postgres()
