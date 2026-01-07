import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "v3" / "taxonomy_tools"))
from common import get_db_connection

conn = get_db_connection()

print("Clearing titles_v3 and related tables...")
print("=" * 60)

try:
    with conn.cursor() as cur:
        # Check current counts
        cur.execute("SELECT COUNT(*) FROM titles_v3")
        titles_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM title_assignments")
        assignments_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM ctm")
        ctm_count = cur.fetchone()[0]

        print("Current counts:")
        print(f"  titles_v3: {titles_count}")
        print(f"  title_assignments: {assignments_count}")
        print(f"  ctm: {ctm_count}")
        print()

        # Truncate (CASCADE will handle title_assignments via foreign key)
        print("Truncating tables...")
        cur.execute("TRUNCATE titles_v3 CASCADE")
        cur.execute("TRUNCATE ctm CASCADE")

    conn.commit()
    print("SUCCESS: All data cleared")

except Exception as e:
    conn.rollback()
    print(f"ERROR: {e}")
    sys.exit(1)
finally:
    conn.close()
