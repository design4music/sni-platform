import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'v3' / 'taxonomy_tools'))
from common import get_db_connection

conn = get_db_connection()

print("=" * 60)
print("TRACK CONFIGURATIONS")
print("=" * 60)

with conn.cursor() as cur:
    # Get all track configs
    cur.execute("""
        SELECT name, tracks, is_default, llm_prompt
        FROM track_configs
        ORDER BY is_default DESC, name
    """)

    for row in cur.fetchall():
        name, tracks, is_default, llm_prompt = row
        config_type = "DEFAULT" if is_default else "CUSTOM"
        print(f"\n{config_type}: {name}")
        print(f"  Tracks: {tracks}")

        # Check if prompt mentions finance_sovereign_state
        if 'finance' in llm_prompt.lower() and 'sovereign' in llm_prompt.lower():
            print("  ^^ PROMPT mentions 'finance' and 'sovereign' ^^")
            print(f"  Prompt excerpt: {llm_prompt[:200]}...")

# Check which centroid had the invalid track issue
print("\n" + "=" * 60)
print("CHECKING TITLES WITH finance_markets TRACK")
print("=" * 60)

with conn.cursor() as cur:
    cur.execute("""
        SELECT t.id, t.title_display, t.centroid_ids, t.track, t.created_at
        FROM titles_v3 t
        WHERE t.track = 'finance_markets'
        ORDER BY t.created_at DESC
        LIMIT 5
    """)

    for row in cur.fetchall():
        title_id, title_display, centroid_ids, track, created_at = row
        print(f"\nTitle: {title_display[:60]}")
        print(f"  Centroids: {centroid_ids}")
        print(f"  Track: {track}")

conn.close()
