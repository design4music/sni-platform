"""Check CTM table schema"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config

conn = psycopg2.connect(
    host=config.db_host,
    port=config.db_port,
    database=config.db_name,
    user=config.db_user,
    password=config.db_password,
)

with conn.cursor() as cur:
    cur.execute(
        """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'ctm'
        ORDER BY ordinal_position
    """
    )
    print("CTM Table Schema:")
    print("=" * 60)
    for row in cur.fetchall():
        print(f"{row[0]:25} {row[1]:20} nullable={row[2]}")

    print("\nCTM Sample Data:")
    print("=" * 60)
    cur.execute(
        """
        SELECT id, centroid_id, track, month, title_count,
               events_digest, summary_text, is_frozen
        FROM ctm
        LIMIT 5
    """
    )
    for row in cur.fetchall():
        print(f"\nID: {row[0]}")
        print(f"  Centroid: {row[1]}")
        print(f"  Track: {row[2]}")
        print(f"  Month: {row[3]}")
        print(f"  Title Count: {row[4]}")
        print(f"  Events Digest: {row[5]}")
        print(f"  Summary: {row[6]}")
        print(f"  Frozen: {row[7]}")

conn.close()
