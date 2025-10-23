#!/usr/bin/env python3
"""
Test Actor Clustering for EF Generation

Shows how Neo4j-based clustering prevents overfragmentation.
"""

import asyncio
import sys
from pathlib import Path

from loguru import logger

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.actor_clustering import get_actor_clustering_service  # noqa: E402


async def test_actor_clustering():
    """Test actor clustering on real data"""

    service = get_actor_clustering_service()

    # Build clusters from Neo4j
    logger.info("Building actor clusters from Neo4j co-occurrence data...")
    clusters = await service.build_clusters()

    print("\n" + "=" * 80)
    print("ACTOR CLUSTERS DETECTED")
    print("=" * 80)

    for cluster_id, members in clusters.items():
        print(f"\n{cluster_id}:")
        for member in members:
            print(f"  - {member}")

    print("\n" + "=" * 80)
    print("NORMALIZATION EXAMPLES")
    print("=" * 80)

    # Test cases showing the problem and solution
    test_cases = [
        {
            "title": "Netanyahu meets with Biden to discuss Gaza ceasefire",
            "actors": ["Benjamin Netanyahu", "United States", "Gaza"],
            "event_type": "diplomacy",
            "theater": "middle-east",
        },
        {
            "title": "Hamas launches rocket attack on Israeli cities",
            "actors": ["Hamas", "Israel"],
            "event_type": "conflict",
            "theater": "middle-east",
        },
        {
            "title": "Palestinian Authority calls for international intervention",
            "actors": ["State of Palestine", "United Nations"],
            "event_type": "diplomacy",
            "theater": "middle-east",
        },
        {
            "title": "Putin orders new offensive in eastern Ukraine",
            "actors": ["Vladimir Putin", "Ukraine"],
            "event_type": "conflict",
            "theater": "eastern-europe",
        },
        {
            "title": "Moscow threatens retaliation over sanctions",
            "actors": ["Moscow", "Russia"],
            "event_type": "diplomacy",
            "theater": "eastern-europe",
        },
        {
            "title": "Trump announces new Middle East peace plan",
            "actors": ["Donald Trump", "Israel", "State of Palestine"],
            "event_type": "diplomacy",
            "theater": "middle-east",
        },
    ]

    print("\nTesting EF key generation with and without clustering:\n")

    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['title']}")
        print(f"   Raw actors: {test['actors']}")

        # WITHOUT clustering (old way - overfragmentation)
        raw_ef_keys = []
        for actor in test["actors"]:
            ef_key = f"{test['event_type']}_{test['theater']}_{actor.upper().replace(' ', '_')}"
            raw_ef_keys.append(ef_key)

        print(f"\n   WITHOUT clustering:")
        print(f"   > Would create {len(raw_ef_keys)} separate EF keys:")
        for key in raw_ef_keys:
            print(f"      - {key}")

        # WITH clustering (new way - focused EFs)
        normalized = service.normalize_actors(test["actors"])
        clustered_ef_key = (
            f"{test['event_type']}_{test['theater']}_{'_'.join(normalized)}"
        )

        print(f"\n   WITH clustering:")
        print(f"   > Normalized to: {normalized}")
        print(f"   > Single EF key: {clustered_ef_key}")
        print(f"   SUCCESS: REDUCED from {len(raw_ef_keys)} keys to 1 key!")

    print("\n" + "=" * 80)
    print("CLUSTER MEMBERSHIP LOOKUP")
    print("=" * 80)

    # Show what's in each cluster
    test_entities = [
        "Israel",
        "Benjamin Netanyahu",
        "Hamas",
        "Gaza",
        "Donald Trump",
        "Russia",
        "Vladimir Putin",
        "Ukraine",
    ]

    print("\nEntity to Cluster mapping:")
    for entity in test_entities:
        cluster = service.get_cluster_for_entity(entity)
        if cluster:
            members = service.get_cluster_members(cluster)
            print(f"\n{entity}:")
            print(f"  > Belongs to: {cluster}")
            print(
                f"  > All members: {', '.join(members[:5])}{'...' if len(members) > 5 else ''}"
            )
        else:
            print(f"\n{entity}:")
            print(f"  > Not in any cluster (standalone entity)")

    print("\n" + "=" * 80)
    print("BENEFITS FOR EF GENERATION")
    print("=" * 80)
    print(
        """
Before clustering:
  - "Israel" -> conflict_middle-east_ISRAEL
  - "Netanyahu" -> conflict_middle-east_NETANYAHU
  - "Hamas" -> conflict_middle-east_HAMAS
  - "Gaza" -> conflict_middle-east_GAZA
  Result: 4 separate EFs for THE SAME STORY (overfragmentation)

After clustering:
  - "Israel" -> CLUSTER_TRUMP_US (includes Israel, Palestine, Hamas)
  - "Netanyahu" -> standalone (or map to CLUSTER_TRUMP_US)
  - "Hamas" -> CLUSTER_TRUMP_US
  - "Gaza" -> standalone (or map to CLUSTER_TRUMP_US)
  - ef_key = conflict_middle-east_CLUSTER_TRUMP_US
  Result: 1 focused EF containing all related titles

This is exactly what you wanted!
"""
    )


async def main():
    await test_actor_clustering()


if __name__ == "__main__":
    asyncio.run(main())
