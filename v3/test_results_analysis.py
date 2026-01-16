"""
Analyze Phase 2 and Phase 3 test results
"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def analyze_phase2():
    """Analyze Phase 2 centroid matching results"""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            # Centroid distribution
            cur.execute(
                """
                SELECT
                    c.label,
                    c.class,
                    COUNT(DISTINCT t.id) as title_count
                FROM titles_v3 t,
                     LATERAL unnest(t.centroid_ids) cid
                JOIN centroids_v3 c ON c.id = cid
                WHERE t.processing_status = 'assigned'
                GROUP BY c.label, c.class
                ORDER BY title_count DESC
                LIMIT 25;
            """
            )

            print("=" * 70)
            print("TOP 25 CENTROIDS BY TITLE COUNT")
            print("=" * 70)
            print(f'{"Centroid":<35} {"Class":<12} {"Titles":<8}')
            print("-" * 70)

            for label, cls, count in cur.fetchall():
                print(f"{label:<35} {cls:<12} {count:<8}")

            # Multi-centroid stats
            cur.execute(
                """
                SELECT
                    array_length(centroid_ids, 1) as num_centroids,
                    COUNT(*) as title_count
                FROM titles_v3
                WHERE processing_status = 'assigned'
                  AND centroid_ids IS NOT NULL
                GROUP BY array_length(centroid_ids, 1)
                ORDER BY num_centroids;
            """
            )

            print()
            print("=" * 70)
            print("MULTI-CENTROID DISTRIBUTION")
            print("=" * 70)
            print(f'{"# Centroids":<15} {"# Titles":<10}')
            print("-" * 70)

            for num, count in cur.fetchall():
                print(f"{num:<15} {count:<10}")

            # Overall stats
            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE processing_status = 'assigned') as assigned,
                    COUNT(*) FILTER (WHERE processing_status = 'pending') as pending,
                    COUNT(*) as total
                FROM titles_v3;
            """
            )

            assigned, pending, total = cur.fetchone()

            print()
            print("=" * 70)
            print("OVERALL PHASE 2 STATUS")
            print("=" * 70)
            print(f"Total titles:    {total}")
            print(f"Assigned:        {assigned} ({assigned*100/total:.1f}%)")
            print(f"Pending:         {pending} ({pending*100/total:.1f}%)")

    finally:
        conn.close()


def analyze_phase3():
    """Analyze Phase 3 track assignment results"""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            # Track distribution by centroid
            cur.execute(
                """
                SELECT
                    c.label,
                    c.class,
                    t.track,
                    COUNT(*) as count
                FROM titles_v3 t
                JOIN LATERAL unnest(t.centroid_ids) cid ON true
                JOIN centroids_v3 c ON c.id = cid
                WHERE t.track IS NOT NULL
                GROUP BY c.label, c.class, t.track
                ORDER BY count DESC
                LIMIT 30;
            """
            )

            print()
            print("=" * 80)
            print("TOP 30 CENTROID-TRACK COMBINATIONS")
            print("=" * 80)
            print(f'{"Centroid":<30} {"Class":<12} {"Track":<25} {"Count":<8}')
            print("-" * 80)

            for label, cls, track, count in cur.fetchall():
                print(f"{label:<30} {cls:<12} {track:<25} {count:<8}")

            # Track distribution overall
            cur.execute(
                """
                SELECT
                    track,
                    COUNT(*) as count
                FROM titles_v3
                WHERE track IS NOT NULL
                GROUP BY track
                ORDER BY count DESC;
            """
            )

            print()
            print("=" * 70)
            print("TRACK DISTRIBUTION (OVERALL)")
            print("=" * 70)
            print(f'{"Track":<35} {"Count":<10}')
            print("-" * 70)

            for track, count in cur.fetchall():
                print(f"{track:<35} {count:<10}")

            # CTM stats
            cur.execute(
                """
                SELECT
                    COUNT(*) as total_ctms,
                    AVG(title_count) as avg_titles_per_ctm,
                    MIN(title_count) as min_titles,
                    MAX(title_count) as max_titles
                FROM ctm
                WHERE title_count > 0;
            """
            )

            total, avg, min_t, max_t = cur.fetchone()

            print()
            print("=" * 70)
            print("CTM STATISTICS")
            print("=" * 70)
            print(f"Total CTMs:          {total}")
            print(f"Avg titles/CTM:      {avg:.2f}")
            print(f"Min titles:          {min_t}")
            print(f"Max titles:          {max_t}")

    finally:
        conn.close()


if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("# V3 PIPELINE TEST RESULTS ANALYSIS")
    print("#" * 70)

    analyze_phase2()

    # Check if Phase 3 has run
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM titles_v3 WHERE track IS NOT NULL")
        phase3_count = cur.fetchone()[0]

    conn.close()

    if phase3_count > 0:
        analyze_phase3()
    else:
        print("\n(Phase 3 not yet run - no track assignments to analyze)")
