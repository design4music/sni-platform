"""
Restore ONLY the titles table from backup_before_cleanup_20251015_181527.sql
Does NOT affect other tables (data_entities, taxonomy_terms, event_families, etc.)
"""

import sys
from datetime import datetime
from pathlib import Path

import psycopg2

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.config import get_config
from core.database import get_db_session


def restore_titles_from_backup():
    """
    Extract and restore titles COPY section from backup file
    """
    backup_file = Path(__file__).parent / "backup_before_cleanup_20251015_181527.sql"

    if not backup_file.exists():
        print(f"ERROR: Backup file not found: {backup_file}")
        return False

    print(f"Reading backup file: {backup_file.name}")
    print("Extracting titles data...")

    # Read the backup file and extract titles section
    with open(backup_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the titles COPY section
    titles_start = None
    titles_end = None

    for i, line in enumerate(lines):
        if line.startswith("COPY public.titles"):
            titles_start = i
            print(f"Found titles COPY at line {i+1}")

        if titles_start is not None and line.strip() == "\\.":
            titles_end = i + 1  # Include the \.
            print(f"Found end marker at line {i+1}")
            break

    if titles_start is None or titles_end is None:
        print("ERROR: Could not find titles COPY section in backup")
        return False

    titles_lines = lines[titles_start:titles_end]
    record_count = titles_end - titles_start - 2  # Subtract COPY line and \.

    print(f"\nExtracted {record_count:,} title records")
    print(f"Data size: {len(''.join(titles_lines)) / 1024 / 1024:.1f} MB")

    # Write to temp SQL file
    temp_sql = Path(__file__).parent / "temp_restore_titles.sql"
    with open(temp_sql, "w", encoding="utf-8") as f:
        f.writelines(titles_lines)

    print(f"\nTemp SQL file created: {temp_sql.name}")

    # Now restore to database using psycopg2 (COPY requires raw connection)
    print("\n" + "=" * 50)
    print("RESTORING TITLES TO DATABASE")
    print("=" * 50)

    config = get_config()

    # Connect with psycopg2 for COPY support
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        cur = conn.cursor()

        # Check current count
        cur.execute("SELECT COUNT(*) FROM titles")
        current_count = cur.fetchone()[0]
        print(f"Current titles in database: {current_count:,}")

        if current_count > 0:
            print(f"\nWARNING: {current_count} titles exist. Truncating...")
            print("Truncating titles table...")
            cur.execute("TRUNCATE TABLE titles CASCADE;")
            conn.commit()
            print("Titles table cleared.")

        # Temporarily disable ALL foreign key constraints
        print("\nDisabling foreign key constraints temporarily...")
        cur.execute(
            "ALTER TABLE titles DROP CONSTRAINT IF EXISTS titles_event_family_id_fkey;"
        )
        cur.execute("ALTER TABLE titles DROP CONSTRAINT IF EXISTS titles_feed_id_fkey;")
        conn.commit()

        # Read and execute the COPY command
        print("Restoring titles from backup...")
        with open(temp_sql, "r", encoding="utf-8") as f:
            # Read the COPY statement (first line)
            copy_statement = f.readline().strip()
            # copy_expert needs the SQL and the file handle
            cur.copy_expert(copy_statement, f)

        conn.commit()

        # Set all event_family_id to NULL (since we dropped all EFs)
        print("Clearing old event_family_id references...")
        cur.execute(
            "UPDATE titles SET event_family_id = NULL WHERE event_family_id IS NOT NULL;"
        )
        conn.commit()

        # Delete titles with missing feed_ids (feeds that no longer exist)
        print("Deleting titles with orphaned feed_id references...")
        cur.execute(
            """
            DELETE FROM titles
            WHERE feed_id IS NOT NULL
            AND feed_id NOT IN (SELECT id FROM feeds);
        """
        )
        deleted_count = cur.rowcount
        conn.commit()
        print(f"  Deleted {deleted_count:,} titles with orphaned feed references")

        # Re-create the foreign key constraints
        print("Re-creating foreign key constraints...")
        cur.execute(
            """
            ALTER TABLE titles
            ADD CONSTRAINT titles_event_family_id_fkey
            FOREIGN KEY (event_family_id) REFERENCES event_families(id) ON DELETE SET NULL;
        """
        )
        cur.execute(
            """
            ALTER TABLE titles
            ADD CONSTRAINT titles_feed_id_fkey
            FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE;
        """
        )
        conn.commit()

        # Verify restoration
        cur.execute("SELECT COUNT(*) FROM titles")
        restored_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM titles WHERE gate_keep = true")
        strategic_count = cur.fetchone()[0]

        print("\n" + "=" * 50)
        print("RESTORATION COMPLETE")
        print("=" * 50)
        print(f"Total titles restored: {restored_count:,}")
        print(f"Strategic titles (gate_keep=true): {strategic_count:,}")
        print(f"Non-strategic titles: {restored_count - strategic_count:,}")

        # Cleanup
        cur.close()
        conn.close()
        temp_sql.unlink()
        print(f"\nTemp file removed: {temp_sql.name}")

        return True

    except Exception as e:
        print(f"\nERROR during restoration: {e}")
        import traceback

        traceback.print_exc()
        conn.rollback()
        conn.close()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("TITLES TABLE RESTORATION")
    print("=" * 70)
    print("This script will restore ONLY the titles table from backup.")
    print("Other tables (data_entities, taxonomy_terms, etc.) will NOT be affected.")
    print("=" * 70 + "\n")

    success = restore_titles_from_backup()

    if success:
        print("\n" + "=" * 70)
        print("SUCCESS: Titles restored successfully!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("FAILED: Restoration did not complete")
        print("=" * 70)
        sys.exit(1)
