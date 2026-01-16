"""Check llm_summary_track_focus column constraints and properties"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "v3" / "taxonomy_tools"))
from common import get_db_connection

conn = get_db_connection()

print("Checking llm_summary_track_focus column...")
print("=" * 60)

with conn.cursor() as cur:
    # Check column definition
    cur.execute(
        """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'track_configs'
          AND column_name = 'llm_summary_track_focus'
    """
    )

    row = cur.fetchone()
    if row:
        col_name, data_type, is_nullable, col_default = row
        print(f"Column: {col_name}")
        print(f"Type: {data_type}")
        print(f"Nullable: {is_nullable}")
        print(f"Default: {col_default}")
    else:
        print("Column not found!")

    print()

    # Check for any constraints
    cur.execute(
        """
        SELECT conname, contype, pg_get_constraintdef(oid)
        FROM pg_constraint
        WHERE conrelid = 'track_configs'::regclass
          AND conkey @> ARRAY[(
            SELECT attnum FROM pg_attribute
            WHERE attrelid = 'track_configs'::regclass
              AND attname = 'llm_summary_track_focus'
          )]
    """
    )

    constraints = cur.fetchall()
    if constraints:
        print("Constraints:")
        for name, type, definition in constraints:
            print(f"  {name} ({type}): {definition}")
    else:
        print("No constraints on this column")

    print()

    # Check current values
    cur.execute(
        """
        SELECT name,
               CASE WHEN llm_summary_track_focus IS NULL THEN 'NULL'
                    ELSE 'HAS VALUE' END as status
        FROM track_configs
        ORDER BY name
    """
    )

    print("Current values:")
    for name, status in cur.fetchall():
        print(f"  {name:25s} {status}")

conn.close()
