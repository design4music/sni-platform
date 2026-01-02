import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def check_table_status():
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    cur = conn.cursor()

    print("=== CURRENT DATABASE STATE ===\n")

    # Check titles_v3
    cur.execute(
        """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN processing_status = 'pending' THEN 1 END) as pending,
            COUNT(CASE WHEN processing_status = 'assigned' THEN 1 END) as assigned,
            COUNT(CASE WHEN processing_status = 'enriched' THEN 1 END) as enriched,
            MIN(created_at) as oldest,
            MAX(created_at) as newest
        FROM titles_v3
    """
    )
    row = cur.fetchone()
    print("titles_v3:")
    print(f"  Total rows: {row[0]}")
    print(f"  Status breakdown: pending={row[1]}, assigned={row[2]}, enriched={row[3]}")
    print(f"  Date range: {row[4]} to {row[5]}")
    print()

    # Check ctm
    cur.execute(
        """
        SELECT
            COUNT(*) as total,
            SUM(title_count) as total_title_links,
            COUNT(CASE WHEN events_digest IS NOT NULL AND events_digest::text != '[]' THEN 1 END) as with_events,
            COUNT(CASE WHEN summary_text IS NOT NULL THEN 1 END) as with_summary,
            MIN(created_at) as oldest,
            MAX(created_at) as newest
        FROM ctm
    """
    )
    row = cur.fetchone()
    print("ctm:")
    print(f"  Total CTMs: {row[0]}")
    print(f"  Total title links: {row[1]}")
    print(f"  With events: {row[2]}")
    print(f"  With summary: {row[3]}")
    print(f"  Date range: {row[4]} to {row[5]}")
    print()

    # Check reference tables (should NOT be touched)
    cur.execute("SELECT COUNT(*) FROM taxonomy_v3")
    print(f"taxonomy_v3: {cur.fetchone()[0]} entities (PRESERVE)")

    cur.execute("SELECT COUNT(*) FROM centroids_v3")
    print(f"centroids_v3: {cur.fetchone()[0]} centroids (PRESERVE)")

    cur.execute("SELECT COUNT(*) FROM track_configs")
    print(f"track_configs: {cur.fetchone()[0]} configs (PRESERVE)")

    cur.close()
    conn.close()


if __name__ == "__main__":
    check_table_status()
