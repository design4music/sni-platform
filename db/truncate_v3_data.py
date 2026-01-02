"""
Safely truncate titles_v3 and ctm tables to start fresh.
PRESERVES reference data: taxonomy_v3, centroids_v3, track_configs
"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def truncate_v3_data():
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    cur = conn.cursor()

    print("=== TRUNCATING V3 DATA TABLES ===\n")

    # Check counts before
    cur.execute("SELECT COUNT(*) FROM titles_v3")
    titles_before = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM ctm")
    ctm_before = cur.fetchone()[0]

    print("Before truncation:")
    print(f"  titles_v3: {titles_before} rows")
    print(f"  ctm: {ctm_before} rows")
    print()

    # TRUNCATE (fast, resets sequences, cascades to related data)
    print("Truncating titles_v3...")
    cur.execute("TRUNCATE TABLE titles_v3 RESTART IDENTITY CASCADE")

    print("Truncating ctm...")
    cur.execute("TRUNCATE TABLE ctm RESTART IDENTITY CASCADE")

    conn.commit()
    print("Committed transaction\n")

    # Verify counts after
    cur.execute("SELECT COUNT(*) FROM titles_v3")
    titles_after = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM ctm")
    ctm_after = cur.fetchone()[0]

    # Verify reference tables untouched
    cur.execute("SELECT COUNT(*) FROM taxonomy_v3")
    taxonomy_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM centroids_v3")
    centroids_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM track_configs")
    configs_count = cur.fetchone()[0]

    print("After truncation:")
    print(f"  titles_v3: {titles_after} rows (EMPTY)")
    print(f"  ctm: {ctm_after} rows (EMPTY)")
    print()
    print("Reference tables (PRESERVED):")
    print(f"  taxonomy_v3: {taxonomy_count} entities")
    print(f"  centroids_v3: {centroids_count} centroids")
    print(f"  track_configs: {configs_count} configs")
    print()

    if titles_after == 0 and ctm_after == 0:
        print("SUCCESS: Data tables truncated cleanly")
    else:
        print("WARNING: Tables not empty after truncation!")

    cur.close()
    conn.close()


if __name__ == "__main__":
    print("This will DELETE ALL data from titles_v3 and ctm tables.")
    print("Reference tables (taxonomy, centroids, configs) will be preserved.")

    response = input("\nType 'YES' to confirm truncation: ")

    if response.strip().upper() == "YES":
        truncate_v3_data()
    else:
        print("Aborted.")
