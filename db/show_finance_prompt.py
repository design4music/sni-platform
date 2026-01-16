import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'v3' / 'taxonomy_tools'))
from common import get_db_connection

conn = get_db_connection()
with conn.cursor() as cur:
    cur.execute("SELECT llm_prompt FROM track_configs WHERE name = 'sys-finance'")
    prompt = cur.fetchone()[0]
    print(prompt)
conn.close()
