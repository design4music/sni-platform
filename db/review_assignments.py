"""Review title assignments"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def review_assignments(title_ids):
    """Review assignments for specific titles"""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    with conn.cursor() as cur:
        # Get titles with their assignments
        cur.execute(
            """
            SELECT id, title_display, centroid_ids, processing_status
            FROM titles_v3
            WHERE id::text = ANY(%s)
            ORDER BY created_at DESC
        """,
            (title_ids,),
        )
        titles = cur.fetchall()

        print(f"{'='*80}")
        print("TITLE ASSIGNMENTS REVIEW")
        print(f"{'='*80}\n")

        for id, title_display, centroid_ids, status in titles:
            print(f"ID: {id}")
            print(f"Title: {title_display}")
            print(f"Status: {status}")
            print(f"Assigned centroids: {centroid_ids if centroid_ids else '(none)'}")
            print()

    conn.close()


if __name__ == "__main__":
    title_ids = [
        "79d53af7-0906-4f33-b4d4-c6b4a064db63",
        "99782e2b-e951-4110-8229-1bf219948acb",
        "340f7c94-67e8-42b6-bba5-edd9dd328ec3",
        "59668330-1619-4814-b4ab-d62319755f8e",
        "3c4302fd-3e03-40f4-86db-7b27852c7b22",
        "334766a6-47f0-415e-92b8-5cc0073eaa17",
        "3927265a-0bae-4723-8e57-cdafd2d85fcd",
        "53dc1bed-bbb1-46b8-879a-06fdbad0adf2",
        "ceb27026-70c6-4229-9ad0-3892a7b3dd01",
        "617f46a2-e2b7-4d20-b4f6-c341acc79d8e",
    ]

    review_assignments(title_ids)
