#!/usr/bin/env python3
"""
Create pairs30 table for anchored-rare seeds logic
"""

import psycopg2


def main():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="narrative_intelligence",
        user="postgres",
        password="postgres",
    )

    cur = conn.cursor()

    # Drop and recreate pairs30 table
    cur.execute("DROP TABLE IF EXISTS pairs30")

    print("Creating pairs30 table for co-occurrence patterns...")

    cur.execute(
        """
        CREATE TABLE pairs30 AS
        SELECT 
            a.token as tok_a,
            b.token as tok_b,
            COUNT(DISTINCT a.article_id) as co_doc
        FROM article_core_keywords a
        JOIN article_core_keywords b ON a.article_id = b.article_id AND a.token < b.token
        GROUP BY a.token, b.token
        HAVING COUNT(DISTINCT a.article_id) >= 5
    """
    )

    # Create index for fast lookups
    cur.execute("CREATE INDEX idx_pairs30_lookup ON pairs30(tok_a, tok_b)")

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM pairs30")
    count = cur.fetchone()[0]

    print(f"Created pairs30 with {count:,} token pairs (co_doc >= 5)")

    # Show some sample pairs
    cur.execute(
        "SELECT tok_a, tok_b, co_doc FROM pairs30 ORDER BY co_doc DESC LIMIT 10"
    )
    print("\nTop co-occurring pairs:")
    for tok_a, tok_b, co_doc in cur.fetchall():
        print(f"  {tok_a} + {tok_b} ({co_doc} docs)")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
