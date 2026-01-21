"""
Backfill matched_aliases for existing titles.

One-time script to populate matched_aliases JSONB column
for titles that already have centroid_ids assigned.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import Json, execute_batch

from core.config import config
from pipeline.phase_2.match_centroids import load_taxonomy, match_title


def backfill_aliases(batch_size=500, limit=None):
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    print("Loading taxonomy...")
    taxonomy = load_taxonomy()
    print(f"  {len(taxonomy['single_word_aliases'])} single-word aliases")

    # Count titles to process
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM titles_v3
            WHERE processing_status = 'assigned'
              AND matched_aliases IS NULL
        """
        )
        total = cur.fetchone()[0]
        print(f"\nTitles to backfill: {total}")

    if limit:
        total = min(total, limit)
        print(f"  (limited to {limit})")

    processed = 0
    updated = 0

    while processed < total:
        # Fetch batch
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title_display
                FROM titles_v3
                WHERE processing_status = 'assigned'
                  AND matched_aliases IS NULL
                LIMIT %s
            """,
                (batch_size,),
            )
            titles = cur.fetchall()

        if not titles:
            break

        # Process batch
        updates = []
        for title_id, title_text in titles:
            _, aliases, status = match_title(title_text, taxonomy)
            if aliases:
                updates.append((Json(sorted(aliases)), title_id))

        # Update batch
        if updates:
            with conn.cursor() as cur:
                execute_batch(
                    cur,
                    """
                    UPDATE titles_v3
                    SET matched_aliases = %s
                    WHERE id = %s
                """,
                    updates,
                    page_size=batch_size,
                )
            conn.commit()
            updated += len(updates)

        processed += len(titles)
        pct = (processed / total) * 100
        print(f"  Processed: {processed}/{total} ({pct:.1f}%) - Updated: {updated}")

    print(f"\nDone. Updated {updated} titles with matched_aliases.")
    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limit titles to process")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    backfill_aliases(batch_size=args.batch_size, limit=args.limit)
