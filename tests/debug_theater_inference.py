"""Debug why all theaters are Global"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def debug_theaters():
    print("=" * 70)
    print("DEBUGGING THEATER INFERENCE")
    print("=" * 70)

    with get_db_session() as session:
        # Check entities in titles
        print("\n1. Checking entities in titles...")
        result = session.execute(
            text(
                """
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN entities IS NOT NULL THEN 1 END) as with_entities,
                COUNT(CASE WHEN entities IS NOT NULL AND jsonb_array_length(entities->'actors') > 0 THEN 1 END) as with_actors
            FROM titles
            WHERE event_family_id IS NOT NULL;
        """
            )
        ).fetchone()

        print(f"  Titles assigned to EFs: {result[0]}")
        print(f"  With entities field: {result[1]}")
        print(f"  With actors array: {result[2]}")

        # Sample entities from assigned titles
        print("\n2. Sample entities from assigned titles:")
        sample = session.execute(
            text(
                """
            SELECT
                title_display,
                entities
            FROM titles
            WHERE event_family_id IS NOT NULL
            AND entities IS NOT NULL
            LIMIT 5;
        """
            )
        ).fetchall()

        for i, row in enumerate(sample, 1):
            title = row[0][:60]
            entities = row[1]
            actors = entities.get("actors", []) if isinstance(entities, dict) else []
            print(f"\n  {i}. {title}...")
            print(f"     Actors: {actors[:5]}")

        # Check Event Families theaters
        print("\n3. Event Family theaters:")
        efs = session.execute(
            text(
                """
            SELECT
                title,
                primary_theater,
                event_type,
                (SELECT COUNT(*) FROM titles WHERE event_family_id = event_families.id) as title_count
            FROM event_families
            ORDER BY created_at DESC
            LIMIT 5;
        """
            )
        ).fetchall()

        for i, row in enumerate(efs, 1):
            print(f"\n  {i}. {row[0][:60]}...")
            print(f"     Theater: {row[1]}")
            print(f"     Type: {row[2]}")
            print(f"     Titles: {row[3]}")

        # Check if Phase 2 was run
        print("\n4. Phase 2 status check:")
        phase2_stats = session.execute(
            text(
                """
            SELECT
                COUNT(*) as total_titles,
                COUNT(CASE WHEN entities IS NOT NULL THEN 1 END) as with_entities,
                COUNT(CASE WHEN gate_keep = true THEN 1 END) as strategic
            FROM titles;
        """
            )
        ).fetchone()

        print(f"  Total titles: {phase2_stats[0]:,}")
        print(f"  With entities: {phase2_stats[1]:,}")
        print(f"  Strategic (gate_keep=true): {phase2_stats[2]:,}")

        if phase2_stats[1] == 0:
            print("\n  [ISSUE] No entities found! Phase 2 hasn't been run yet.")
            print("  Run: python -m apps.filter.main --max-titles 100")
        else:
            print(f"\n  [OK] {phase2_stats[1]:,} titles have entities")


if __name__ == "__main__":
    debug_theaters()
