import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "v3" / "taxonomy_tools"))
from common import get_db_connection

conn = get_db_connection()

print("=" * 80)
print("FULL PIPELINE SUMMARY")
print("=" * 80)
print()

# Phase 1 & 2 stats
with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM titles_v3")
    total_titles = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM titles_v3 WHERE processing_status = 'assigned'")
    assigned = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM titles_v3 WHERE processing_status = 'blocked_stopword'"
    )
    blocked_stopword = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM titles_v3 WHERE processing_status = 'blocked_llm'"
    )
    blocked_llm = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM titles_v3 WHERE processing_status = 'out_of_scope'"
    )
    oos = cur.fetchone()[0]

print("Phase 1-2 (Ingestion + Centroid Matching):")
print(f"  Total titles ingested: {total_titles}")
print(
    f"  Matched to centroids: {assigned + blocked_llm} ({(assigned + blocked_llm) / total_titles * 100:.1f}%)"
)
print(f"  Blocked by stop words: {blocked_stopword}")
print(f"  Out of scope: {oos}")
print()

# Phase 3 stats
with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM title_assignments")
    total_assignments = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT title_id) FROM title_assignments")
    titles_with_tracks = cur.fetchone()[0]

    cur.execute(
        """
        SELECT centroid_id, COUNT(*) as count
        FROM title_assignments
        GROUP BY centroid_id
        ORDER BY count DESC
        LIMIT 5
    """
    )
    top_centroids = cur.fetchall()

print("Phase 3 (Intel Gating + Track Assignment):")
print(
    f"  Titles with strategic value: {titles_with_tracks} ({titles_with_tracks / (assigned + blocked_llm) * 100:.1f}%)"
)
print(f"  Rejected by LLM intel gating: {blocked_llm}")
print(f"  Total track assignments: {total_assignments}")
print(
    f"  Avg assignments per strategic title: {total_assignments / titles_with_tracks:.2f}"
)
print()

print("Top 5 Centroids by Track Assignments:")
for centroid_id, count in top_centroids:
    print(f"  {centroid_id}: {count} assignments")
print()

# Multi-centroid analysis
with conn.cursor() as cur:
    cur.execute(
        """
        SELECT
            COUNT(*) as assignment_count,
            COUNT(DISTINCT title_id) as title_count
        FROM (
            SELECT title_id, COUNT(*) as cnt
            FROM title_assignments
            GROUP BY title_id
        ) subq
        WHERE cnt > 1
    """
    )
    multi_result = cur.fetchone()
    multi_assignments, multi_titles = multi_result if multi_result else (0, 0)

print("Multi-Centroid Behavior:")
print(
    f"  Titles assigned to multiple centroids: {multi_titles} ({multi_titles / titles_with_tracks * 100:.1f}%)"
)
print(f"  Extra assignments from multi-centroid: {multi_assignments}")
print()

# Track distribution
with conn.cursor() as cur:
    cur.execute(
        """
        SELECT track, COUNT(*) as count
        FROM title_assignments
        GROUP BY track
        ORDER BY count DESC
        LIMIT 10
    """
    )
    top_tracks = cur.fetchall()

print("Top 10 Tracks Assigned:")
for track, count in top_tracks:
    safe_track = track.encode("ascii", "replace").decode("ascii")
    print(f"  {safe_track}: {count}")
print()

# CTM stats
with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM ctm")
    total_ctms = cur.fetchone()[0]

    cur.execute("SELECT SUM(title_count) FROM ctm")
    total_title_count = cur.fetchone()[0] or 0

print("CTM (Centroid-Track-Month) Summary:")
print(f"  Total CTMs created: {total_ctms}")
print(f"  Total title count in CTMs: {total_title_count}")
print()

print("=" * 80)

conn.close()
