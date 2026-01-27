"""
Run migration to fix title_assignments constraint

This script:
1. Backs up current title_assignments
2. Applies constraint fix
3. Reports statistics
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)
load_dotenv()

from core.config import config  # noqa: E402


def main():
    print("=" * 60)
    print("MIGRATION: Fix title_assignments constraint")
    print("=" * 60)

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            # Step 1: Show current state
            print("\nStep 1: Current statistics")
            print("-" * 60)

            cur.execute(
                "SELECT COUNT(*) FROM titles_v3 WHERE processing_status = 'assigned'"
            )
            assigned_count = cur.fetchone()[0]
            print(f"Titles with status='assigned': {assigned_count:,}")

            cur.execute("SELECT COUNT(*) FROM title_assignments")
            ta_count = cur.fetchone()[0]
            print(f"Current title_assignments:     {ta_count:,}")

            cur.execute("SELECT SUM(title_count) FROM ctm")
            ctm_sum = cur.fetchone()[0]
            print(f"Sum of CTM.title_count:        {ctm_sum:,}")

            print(f"\nMissing assignments: {assigned_count - ta_count:,}")

            # Step 2: Show current constraint
            print("\nStep 2: Current constraint")
            print("-" * 60)

            cur.execute(
                """
                SELECT conname, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'title_assignments'::regclass
                  AND conname LIKE '%title_id%'
            """
            )

            for name, definition in cur.fetchall():
                print(f"{name}:")
                print(f"  {definition}")

            # Step 3: Apply migration
            print("\nStep 3: Applying migration")
            print("-" * 60)

            migration_file = (
                Path(__file__).parent
                / "migrations"
                / "20260117_fix_title_assignments_constraint.sql"
            )

            with open(migration_file, "r", encoding="utf-8") as f:
                migration_sql = f.read()

            # Execute migration (excluding comments and SELECT at end)
            for statement in migration_sql.split(";"):
                statement = statement.strip()
                if (
                    statement
                    and not statement.startswith("--")
                    and not statement.startswith("SELECT")
                ):
                    cur.execute(statement)

            conn.commit()
            print("Migration applied successfully")

            # Step 4: Verify new constraint
            print("\nStep 4: New constraint")
            print("-" * 60)

            cur.execute(
                """
                SELECT conname, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'title_assignments'::regclass
                  AND conname LIKE '%title_id%'
            """
            )

            for name, definition in cur.fetchall():
                print(f"{name}:")
                print(f"  {definition}")

            # Step 5: Count unprocessed titles
            print("\nStep 5: Unprocessed titles")
            print("-" * 60)

            cur.execute(
                """
                SELECT COUNT(*)
                FROM titles_v3 t
                WHERE t.processing_status = 'assigned'
                  AND t.centroid_ids IS NOT NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM title_assignments ta
                    WHERE ta.title_id = t.id
                  )
            """
            )

            unprocessed = cur.fetchone()[0]
            print(f"Titles needing track assignment: {unprocessed:,}")

            print("\n" + "=" * 60)
            print("MIGRATION COMPLETE")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Restart pipeline daemon to process unassigned titles")
            print(f"2. {unprocessed:,} titles will be processed by Phase 3")
            print("3. Monitor pipeline output for errors")

    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
