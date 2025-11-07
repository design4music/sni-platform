"""
Helper script to link centroids to track_configs

This script helps you assign track configurations to specific centroids.
Most centroids will use the default strategic config (NULL track_config_id).
"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def link_centroid_to_config(conn, centroid_label: str, config_name: str):
    """Link a centroid to a track config by names"""
    with conn.cursor() as cur:
        # Get config ID
        cur.execute(
            """
            SELECT id FROM track_configs WHERE name = %s
        """,
            (config_name,),
        )
        config_row = cur.fetchone()

        if not config_row:
            print(f"  ERROR: Track config '{config_name}' not found")
            return False

        config_id = config_row[0]

        # Update centroid
        cur.execute(
            """
            UPDATE centroids_v3
            SET track_config_id = %s
            WHERE label = %s
            RETURNING id, label
        """,
            (config_id, centroid_label),
        )

        result = cur.fetchone()

        if not result:
            print(f"  ERROR: Centroid '{centroid_label}' not found")
            return False

        conn.commit()
        print(
            f"  SUCCESS: Linked '{result[1]}' to track config '{config_name}'"
        )
        return True


def show_current_links(conn):
    """Display current centroid -> track_config links"""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                c.label,
                c.class,
                tc.name as config_name,
                array_length(tc.tracks, 1) as track_count
            FROM centroids_v3 c
            LEFT JOIN track_configs tc ON c.track_config_id = tc.id
            WHERE c.track_config_id IS NOT NULL
            ORDER BY c.class, c.label
        """
        )

        rows = cur.fetchall()

        if not rows:
            print("\nNo centroids linked to custom track configs yet.")
            print("All centroids are using the default strategic config.")
        else:
            print("\nCurrent centroid -> track_config links:")
            print(f"{'='*70}")
            print(f"{'Centroid':<30} {'Class':<12} {'Config':<20} {'Tracks':<8}")
            print(f"{'='*70}")
            for label, cls, config, count in rows:
                print(f"{label:<30} {cls:<12} {config:<20} {count:<8}")


def main():
    """Interactive script to link centroids to configs"""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        print("="*70)
        print("Link Centroids to Track Configs")
        print("="*70)

        # Show available configs
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT name, description, array_length(tracks, 1)
                FROM track_configs
                ORDER BY is_default DESC, name
            """
            )
            configs = cur.fetchall()

        print("\nAvailable track configs:")
        for name, desc, count in configs:
            print(f"  - {name} ({count} tracks): {desc}")

        # Show current links
        show_current_links(conn)

        print("\n" + "="*70)
        print("Example Usage:")
        print("="*70)
        print("Link Artificial Intelligence to tech_focused:")
        link_centroid_to_config(conn, "Artificial Intelligence", "tech_focused")

        print("\nLink Climate Change to environment_focused:")
        link_centroid_to_config(conn, "Climate Change", "environment_focused")

        print("\nLink Mongolia to limited_strategic:")
        link_centroid_to_config(conn, "Mongolia", "limited_strategic")

        # Show updated links
        print("\n" + "="*70)
        show_current_links(conn)

        print("\n" + "="*70)
        print("NOTE: You can edit these links directly in DBeaver:")
        print("  UPDATE centroids_v3")
        print("  SET track_config_id = (SELECT id FROM track_configs WHERE name = 'tech_focused')")
        print("  WHERE label = 'Artificial Intelligence';")
        print("="*70)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
