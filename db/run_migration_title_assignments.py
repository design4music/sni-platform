import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'v3' / 'taxonomy_tools'))
from common import get_db_connection

migration_file = Path(__file__).parent / 'migrations' / 'create_title_assignments.sql'

print("Running migration: create_title_assignments.sql")
print("=" * 60)

with open(migration_file, 'r', encoding='utf-8') as f:
    migration_sql = f.read()

conn = get_db_connection()

try:
    with conn.cursor() as cur:
        cur.execute(migration_sql)
    conn.commit()
    print("SUCCESS: Migration applied")
    print("- Created title_assignments table")
    print("- Dropped track and ctm_ids columns from titles_v3")
except Exception as e:
    conn.rollback()
    print(f"ERROR: {e}")
    sys.exit(1)
finally:
    conn.close()
