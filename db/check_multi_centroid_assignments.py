import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "v3" / "taxonomy_tools"))
from common import get_db_connection

conn = get_db_connection()

print("Multi-Centroid Title Assignments")
print("=" * 80)

with conn.cursor() as cur:
    # Find titles with multiple centroid assignments
    cur.execute(
        """
        SELECT
            ta.title_id,
            t.title_display,
            t.centroid_ids,
            COUNT(*) as assignment_count,
            ARRAY_AGG(ta.centroid_id || ': ' || ta.track) as assignments
        FROM title_assignments ta
        JOIN titles_v3 t ON ta.title_id = t.id
        GROUP BY ta.title_id, t.title_display, t.centroid_ids
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
    """
    )

    multi_titles = cur.fetchall()

    if multi_titles:
        print(f"Found {len(multi_titles)} titles with multiple centroid assignments:")
        print()

        for title_id, title_display, centroid_ids, count, assignments in multi_titles:
            # Use ASCII-safe encoding
            safe_title = title_display[:60].encode("ascii", "replace").decode("ascii")
            print(f"Title: {safe_title}")
            print(f"  ID: {title_id}")
            print(f"  Centroids in titles_v3: {centroid_ids}")
            print(f"  Assignment count: {count}")
            print("  Assignments:")
            for assignment in assignments:
                safe_assignment = assignment.encode("ascii", "replace").decode("ascii")
                print(f"    - {safe_assignment}")
            print()
    else:
        print("No multi-centroid titles found in this batch")

print()
print("Summary Statistics")
print("-" * 80)

with conn.cursor() as cur:
    # Total assignments
    cur.execute("SELECT COUNT(*) FROM title_assignments")
    total_assignments = cur.fetchone()[0]

    # Total unique titles
    cur.execute("SELECT COUNT(DISTINCT title_id) FROM title_assignments")
    unique_titles = cur.fetchone()[0]

    # Titles by assignment count
    cur.execute(
        """
        SELECT
            COUNT(*) as assignment_count,
            COUNT(DISTINCT title_id) as title_count
        FROM title_assignments
        GROUP BY title_id
        ORDER BY assignment_count DESC
    """
    )

    print(f"Total assignments: {total_assignments}")
    print(f"Unique titles: {unique_titles}")
    print(
        f"Average assignments per title: {total_assignments / unique_titles if unique_titles > 0 else 0:.2f}"
    )

conn.close()
