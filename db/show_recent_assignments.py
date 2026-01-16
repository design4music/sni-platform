"""Show recently assigned titles"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def show_recent_assignments(limit=10):
    """Show most recently assigned titles"""
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
            SELECT id, title_display, centroid_ids, processing_status, updated_at
            FROM titles_v3
            WHERE processing_status = 'assigned'
            ORDER BY updated_at DESC
            LIMIT %s
        """,
            (limit,),
        )
        titles = cur.fetchall()

        print(f"{'='*80}")
        print(f"MOST RECENT {limit} ASSIGNED TITLES")
        print(f"{'='*80}\n")

        for id, title_display, centroid_ids, status, updated_at in titles:
            print(f"Title: {title_display}")
            print(f"ID: {id}")
            print(f"Assigned centroids: {centroid_ids if centroid_ids else '(none)'}")
            print(f"Updated: {updated_at}")
            print()

    conn.close()


if __name__ == "__main__":
    show_recent_assignments(10)
