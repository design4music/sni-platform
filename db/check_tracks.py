"""Check actual track values in database"""
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
    # Get all distinct tracks
    cur.execute("""
        SELECT DISTINCT track, COUNT(*) as ctm_count
        FROM ctm
        GROUP BY track
        ORDER BY track
    """)
    tracks = cur.fetchall()

    # Get sample for SYS-CLIMATE
    cur.execute("""
        SELECT track, month, title_count
        FROM ctm
        WHERE centroid_id = 'SYS-CLIMATE'
        ORDER BY month DESC
        LIMIT 10
    """)
    climate_samples = cur.fetchall()

print("=" * 70)
print("TRACK VALUES IN DATABASE")
print("=" * 70)
for track, count in tracks:
    print(f"{track:40s} | {count} CTMs")

print("\n" + "=" * 70)
print("SAMPLE CTMs FOR SYS-CLIMATE")
print("=" * 70)
for track, month, count in climate_samples:
    print(f"{track:40s} | {month} | {count} titles")

conn.close()
