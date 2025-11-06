"""Copy titles from v2 titles table to v3 titles_v3 table"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def copy_titles_to_v3(max_titles=None):
    """Copy titles from titles to titles_v3"""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    with conn.cursor() as cur:
        # Check existing titles_v3 count
        cur.execute("SELECT COUNT(*) FROM titles_v3")
        existing_count = cur.fetchone()[0]
        print(f"Existing titles_v3: {existing_count}")

        # Get titles from v2 table
        limit_clause = f"LIMIT {max_titles}" if max_titles else ""
        cur.execute(
            f"""
            SELECT
                title_display,
                url_gnews,
                publisher_name,
                pubdate_utc,
                detected_language
            FROM titles
            WHERE title_display IS NOT NULL
            ORDER BY pubdate_utc DESC
            {limit_clause}
        """
        )
        titles = cur.fetchall()

        print(f"Found {len(titles)} titles to copy")

        if not titles:
            print("No titles to copy!")
            return

        # Insert into titles_v3
        inserted = 0
        for (
            title_display,
            url_gnews,
            publisher_name,
            pubdate_utc,
            detected_language,
        ) in titles:
            try:
                cur.execute(
                    """
                    INSERT INTO titles_v3 (
                        title_display,
                        url_gnews,
                        publisher_name,
                        pubdate_utc,
                        detected_language,
                        processing_status
                    )
                    VALUES (%s, %s, %s, %s, %s, 'pending')
                """,
                    (
                        title_display,
                        url_gnews,
                        publisher_name,
                        pubdate_utc,
                        detected_language,
                    ),
                )
                inserted += 1
            except Exception as e:
                print(f"Error inserting title: {e}")
                continue

        conn.commit()

        # Verify
        cur.execute("SELECT COUNT(*) FROM titles_v3")
        final_count = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM titles_v3 WHERE processing_status = 'pending'"
        )
        pending_count = cur.fetchone()[0]

    conn.close()

    print(f"\n{'='*60}")
    print("COPY COMPLETE")
    print(f"{'='*60}")
    print(f"Inserted:            {inserted}")
    print(f"Total titles_v3:     {final_count}")
    print(f"Pending processing:  {pending_count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Copy titles from v2 to v3")
    parser.add_argument(
        "--max-titles", type=int, help="Maximum number of titles to copy"
    )

    args = parser.parse_args()

    copy_titles_to_v3(max_titles=args.max_titles)
