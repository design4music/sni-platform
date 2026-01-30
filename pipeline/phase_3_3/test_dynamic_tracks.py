"""
Test script for dynamic track configuration system

Tests:
1. Default strategic config (most centroids)
2. Tech-focused config (for SYS-TECH if linked)
3. Environment config (for SYS-CLIMATE if linked)
4. Limited config (for quiet countries if linked)
"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

from .assign_tracks import get_track_config_for_centroids, get_track_from_llm


def test_track_config_loading():
    """Test that track configs load correctly for different centroids"""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        print("=" * 70)
        print("Test: Track Config Loading")
        print("=" * 70)

        # Get some test centroids
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, label, class, track_config_id
                FROM centroids_v3
                WHERE label IN (
                    'China',
                    'Artificial Intelligence',
                    'Climate Change',
                    'Mongolia'
                )
            """
            )
            centroids = cur.fetchall()

        for centroid_id, label, cls, config_id in centroids:
            print(f"\nCentroid: {label} ({cls})")
            print(f"  Custom config: {'Yes' if config_id else 'No (using default)'}")

            # Load track config
            track_config = get_track_config_for_centroids(conn, [centroid_id])

            print(f"  Loaded config: {track_config['centroid_label']}")
            print(f"  Track count: {len(track_config['tracks'])}")
            print(f"  Tracks: {', '.join(track_config['tracks'][:3])}...")
            print(f"  Prompt length: {len(track_config['prompt'])} chars")

    finally:
        conn.close()


async def test_llm_classification():
    """Test LLM track classification with different configs"""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        print("\n" + "=" * 70)
        print("Test: LLM Track Classification")
        print("=" * 70)

        test_cases = [
            (
                "China",
                "China tests new hypersonic missile in South China Sea",
                "2024-11",
            ),
            (
                "Artificial Intelligence",
                "OpenAI releases GPT-5 with advanced reasoning capabilities",
                "2024-11",
            ),
            (
                "Climate Change",
                "UN climate summit agrees on historic fossil fuel phase-out deal",
                "2024-11",
            ),
        ]

        for centroid_label, title, month in test_cases:
            # Get centroid ID
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id FROM centroids_v3 WHERE label = %s
                """,
                    (centroid_label,),
                )
                row = cur.fetchone()

                if not row:
                    print(f"\nSkipping {centroid_label} (not found)")
                    continue

                centroid_id = row[0]

            # Get track config
            track_config = get_track_config_for_centroids(conn, [centroid_id])

            print(f"\nTest Case: {centroid_label}")
            print(f"  Title: {title}")
            print(f"  Config tracks: {len(track_config['tracks'])} options")

            # Classify
            track = await get_track_from_llm(title, track_config, month)

            print(f"  Assigned track: {track}")
            print(f"  Valid: {track in [t.lower() for t in track_config['tracks']]}")

    finally:
        conn.close()


def test_multi_centroid_priority():
    """Test track config selection when title has multiple centroids"""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        print("\n" + "=" * 70)
        print("Test: Multi-Centroid Priority Resolution")
        print("=" * 70)

        # Get centroid IDs for testing
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, label, class
                FROM centroids_v3
                WHERE label IN ('China', 'Artificial Intelligence')
            """
            )
            centroids = {row[1]: (row[0], row[2]) for row in cur.fetchall()}

        if "China" in centroids and "Artificial Intelligence" in centroids:
            china_id, china_class = centroids["China"]
            ai_id, ai_class = centroids["Artificial Intelligence"]

            # Test 1: Systemic (AI) should win over Theater (China)
            print("\nTest: AI + China (systemic should win)")
            track_config = get_track_config_for_centroids(conn, [ai_id, china_id])
            print(f"  Primary centroid: {track_config['centroid_label']}")
            print(f"  Class: {track_config['centroid_class']}")
            print(f"  Track count: {len(track_config['tracks'])}")

            # Test 2: Order shouldn't matter (systemic always wins)
            print("\nTest: China + AI (systemic should still win)")
            track_config2 = get_track_config_for_centroids(conn, [china_id, ai_id])
            print(f"  Primary centroid: {track_config2['centroid_label']}")
            print(f"  Class: {track_config2['centroid_class']}")
            print(f"  Track count: {len(track_config2['tracks'])}")

    finally:
        conn.close()


def main():
    """Run all tests"""
    print("\n" + "#" * 70)
    print("# Dynamic Track Configuration System - Test Suite")
    print("#" * 70)

    # Test 1: Config loading
    test_track_config_loading()

    # Test 2: LLM classification
    # asyncio.run(test_llm_classification())  # Uncomment to test with real LLM

    # Test 3: Multi-centroid priority
    test_multi_centroid_priority()

    print("\n" + "#" * 70)
    print("# Tests Complete")
    print("#" * 70)


if __name__ == "__main__":
    main()
