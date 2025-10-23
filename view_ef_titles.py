"""View all titles belonging to an Event Family"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def view_ef_titles(ef_id: str = None, limit: int = 5):
    """
    View titles for Event Families

    Args:
        ef_id: Specific EF ID to view, or None to show recent EFs
        limit: Number of EFs to show (if ef_id is None)
    """
    with get_db_session() as session:
        if ef_id:
            # Show specific EF
            ef = session.execute(
                text(
                    """
                SELECT id, title, primary_theater, event_type, strategic_purpose
                FROM event_families
                WHERE id = :ef_id;
            """
                ),
                {"ef_id": ef_id},
            ).fetchone()

            if not ef:
                print(f"Event Family {ef_id} not found")
                return

            print("=" * 80)
            print(f"EVENT FAMILY: {ef[1]}")
            print("=" * 80)
            print(f"Theater: {ef[2]}")
            print(f"Type: {ef[3]}")
            print(f"Strategic Purpose: {ef[4]}")
            print()

            titles = session.execute(
                text(
                    """
                SELECT title_display, pubdate_utc, entities
                FROM titles
                WHERE event_family_id = :ef_id
                ORDER BY pubdate_utc DESC;
            """
                ),
                {"ef_id": ef_id},
            ).fetchall()

            print(f"TITLES ({len(titles)}):")
            print("-" * 80)
            for i, row in enumerate(titles, 1):
                title = row[0]
                date = row[1].strftime("%Y-%m-%d") if row[1] else "unknown"
                entities = row[2] if isinstance(row[2], list) else []
                print(f"\n{i}. [{date}] {title[:75]}...")
                if entities:
                    print(f"   Entities: {', '.join(entities[:5])}")

        else:
            # Show recent EFs with title counts
            print("=" * 80)
            print(f"RECENT EVENT FAMILIES (Top {limit})")
            print("=" * 80)

            efs = session.execute(
                text(
                    """
                SELECT
                    ef.id,
                    ef.title,
                    ef.primary_theater,
                    ef.event_type,
                    ef.strategic_purpose,
                    COUNT(t.id) as title_count
                FROM event_families ef
                LEFT JOIN titles t ON t.event_family_id = ef.id
                GROUP BY ef.id, ef.title, ef.primary_theater, ef.event_type, ef.strategic_purpose
                ORDER BY ef.created_at DESC
                LIMIT :limit;
            """
                ),
                {"limit": limit},
            ).fetchall()

            for i, row in enumerate(efs, 1):
                ef_id = row[0]
                title = row[1]
                theater = row[2]
                event_type = row[3]
                purpose = row[4]
                count = row[5]

                print(f"\n{i}. {title[:70]}...")
                print(f"   ID: {ef_id}")
                print(f"   Theater: {theater} | Type: {event_type}")
                print(f"   Purpose: {purpose[:90] if purpose else 'None'}...")
                print(f"   Titles: {count}")

            print("\n" + "=" * 80)
            print("To view titles for a specific EF, run:")
            print("  python view_ef_titles.py <ef_id>")
            print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ef_id = sys.argv[1]
        view_ef_titles(ef_id)
    else:
        view_ef_titles(limit=5)
