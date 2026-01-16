import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'v3' / 'taxonomy_tools'))
from common import get_db_connection

conn = get_db_connection()

title_ids = ['9d5647cf-7385-45f5-92ff-65100a7acca4', '74bcb60f-dd18-4033-806c-0d0121da9466']

with conn.cursor() as cur:
    cur.execute("""
        SELECT id, title_display, centroid_ids, track, ctm_ids
        FROM titles_v3
        WHERE id = ANY(%s::uuid[])
    """, (title_ids,))

    rows = cur.fetchall()
    print('Problem titles:')
    print('=' * 80)
    for row in rows:
        print(f'ID: {row[0]}')
        print(f'Title: {row[1]}')
        print(f'Centroids: {row[2]}')
        print(f'Track: {row[3]}')
        print(f'CTM IDs: {row[4]}')
        print('-' * 80)

conn.close()
