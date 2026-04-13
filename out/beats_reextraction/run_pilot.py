"""Runner: re-extract 99 pilot titles under ELO v3.0 prompt."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg2

from core.config import get_config
from pipeline.phase_3_1.extract_labels import process_titles

cfg = get_config()
conn = psycopg2.connect(
    host=cfg.db_host,
    port=cfg.db_port,
    database=cfg.db_name,
    user=cfg.db_user,
    password=cfg.db_password,
)
cur = conn.cursor()
cur.execute("SELECT title_id::text FROM beats_pilot_100 ORDER BY title_id")
ids = [r[0] for r in cur.fetchall()]
conn.close()

print(f"Loaded {len(ids)} pilot title_ids", flush=True)
print("Running Phase 3.1 extraction under ELO v3.0 prompt...", flush=True)

result = process_titles(
    max_titles=200,
    batch_size=25,
    concurrency=4,
    title_ids_filter=ids,
)
print(f"Result: {result}", flush=True)
