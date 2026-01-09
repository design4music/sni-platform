"""Run migration to add summary focus line columns"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "v3" / "taxonomy_tools"))
from common import get_db_connection

migration_file = (
    Path(__file__).parent / "migrations" / "20260109_add_summary_focus_lines.sql"
)

print("Running migration: 20260109_add_summary_focus_lines.sql")
print("=" * 60)

with open(migration_file, "r", encoding="utf-8") as f:
    migration_sql = f.read()

conn = get_db_connection()

try:
    with conn.cursor() as cur:
        cur.execute(migration_sql)
    conn.commit()
    print("SUCCESS: Migration applied")
    print("- Added llm_summary_centroid_focus column")
    print("- Added llm_summary_track_focus column")
    print("- Renamed llm_prompt to llm_track_assignment")
    print()
    print("Next step: Run populate_summary_focus_lines.py")
except Exception as e:
    conn.rollback()
    print(f"ERROR: {e}")
    sys.exit(1)
finally:
    conn.close()
