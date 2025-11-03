#!/usr/bin/env python3
"""
Explore Neo4j for EF clustering insights

Shows how Neo4j can help with:
1. Actor co-occurrence clustering (Hamas/Palestine/Gaza = same story)
2. Related story detection (Israel+US, Palestine+Trump = same conflict)
3. Actor groups for normalized ef_key generation
"""

import asyncio
import os
from collections import defaultdict

from neo4j import GraphDatabase


def explore_actor_clusters():
    """Find which actors frequently co-occur in strategic titles"""

    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", os.getenv("NEO4J_PASSWORD", "sni_password_2024")),
    )

    with driver.session() as session:
        print("=" * 80)
        print("1. ENTITY CO-OCCURRENCE PATTERNS")
        print("=" * 80)
        print("Finding entity pairs that appear together frequently...\n")

        # Find entity pairs that co-occur
        result = session.run(
            """
            MATCH (t:Title {gate_keep: true})-[:HAS_ENTITY]->(e1:Entity)
            MATCH (t)-[:HAS_ENTITY]->(e2:Entity)
            WHERE e1.name < e2.name

            WITH e1, e2, COUNT(DISTINCT t) as co_occurrence_count
            WHERE co_occurrence_count >= 3

            RETURN e1.name as entity1,
                   e2.name as entity2,
                   co_occurrence_count
            ORDER BY co_occurrence_count DESC
            LIMIT 20
        """
        )

        print("Top entity pairs (3+ titles together):")
        for i, record in enumerate(result, 1):
            print(
                f"{i:2}. {record['entity1']:30} + {record['entity2']:30} = {record['co_occurrence_count']:3} titles"
            )

        print("\n" + "=" * 80)
        print("2. ACTOR NEIGHBORHOODS (Who appears with whom?)")
        print("=" * 80)
        print("Finding which entities form story clusters...\n")

        # For each entity, find its most common neighbors
        result = session.run(
            """
            MATCH (e1:Entity)<-[:HAS_ENTITY]-(t:Title {gate_keep: true})-[:HAS_ENTITY]->(e2:Entity)
            WHERE e1.name <> e2.name

            WITH e1, e2, COUNT(DISTINCT t) as co_occurrence
            WHERE co_occurrence >= 2

            WITH e1, collect({entity: e2.name, count: co_occurrence}) as neighbors
            WHERE size(neighbors) >= 2

            RETURN e1.name as entity,
                   neighbors
            ORDER BY size(neighbors) DESC
            LIMIT 10
        """
        )

        for record in result:
            entity = record["entity"]
            neighbors = record["neighbors"]
            print(f"\n{entity}:")
            for n in sorted(neighbors, key=lambda x: x["count"], reverse=True)[:5]:
                print(f"  + {n['entity']:30} ({n['count']} titles)")

        print("\n" + "=" * 80)
        print("3. POTENTIAL ACTOR GROUPS FOR EF GENERATION")
        print("=" * 80)
        print("Detecting actor clusters that could form normalized keys...\n")

        # Use community detection approach - find densely connected entity groups
        result = session.run(
            """
            // Find entities that appear together frequently
            MATCH (e1:Entity)<-[:HAS_ENTITY]-(t:Title {gate_keep: true})-[:HAS_ENTITY]->(e2:Entity)
            WHERE e1.name < e2.name

            WITH e1, e2, COUNT(DISTINCT t) as strength
            WHERE strength >= 3

            // Group by first entity to see its cluster
            WITH e1, collect({entity: e2.name, strength: strength}) as cluster
            WHERE size(cluster) >= 2

            RETURN e1.name as core_entity,
                   cluster
            ORDER BY size(cluster) DESC
            LIMIT 8
        """
        )

        clusters = {}
        for record in result:
            core = record["core_entity"]
            cluster = record["cluster"]
            clusters[core] = cluster

        print("Detected Actor Clusters:")
        for i, (core, members) in enumerate(clusters.items(), 1):
            print(f"\n{i}. {core} CLUSTER:")
            for m in sorted(members, key=lambda x: x["strength"], reverse=True):
                print(f"   + {m['entity']:30} (strength: {m['strength']})")

        print("\n" + "=" * 80)
        print("4. STORY CONNECTION EXAMPLES")
        print("=" * 80)
        print("How different actor combinations might be same story...\n")

        # Find title pairs with different actors but potentially same story
        result = session.run(
            """
            MATCH (t1:Title {gate_keep: true})-[:HAS_ENTITY]->(e1:Entity)
            MATCH (t2:Title {gate_keep: true})-[:HAS_ENTITY]->(e2:Entity)
            WHERE t1.id < t2.id
              AND e1.name <> e2.name

            // Find titles that share at least one entity
            MATCH (t1)-[:HAS_ENTITY]->(shared:Entity)<-[:HAS_ENTITY]-(t2)

            WITH t1, t2,
                 collect(DISTINCT e1.name) as t1_entities,
                 collect(DISTINCT e2.name) as t2_entities,
                 collect(DISTINCT shared.name) as shared_entities
            WHERE size(shared_entities) >= 1
              AND size(t1_entities) >= 2
              AND size(t2_entities) >= 2

            RETURN t1.title as title1,
                   t2.title as title2,
                   t1_entities[0..3] as entities1,
                   t2_entities[0..3] as entities2,
                   shared_entities
            LIMIT 5
        """
        )

        for i, record in enumerate(result, 1):
            print(f"\n{i}. POTENTIALLY SAME STORY:")
            print(f"   Title A: {record['title1'][:70]}...")
            print(f"   Entities: {', '.join(record['entities1'][:3])}")
            print(f"   Title B: {record['title2'][:70]}...")
            print(f"   Entities: {', '.join(record['entities2'][:3])}")
            print(f"   SHARED: {', '.join(record['shared_entities'])}")

        print("\n" + "=" * 80)
        print("5. SUGGESTED NORMALIZED ACTOR KEYS")
        print("=" * 80)
        print("How to use this for ef_key generation:\n")

        print("Instead of:")
        print("  ef_key = 'conflict_middle-east_Israel'")
        print("  ef_key = 'conflict_middle-east_Netanyahu'")
        print("  ef_key = 'conflict_middle-east_IDF'")
        print("  RESULT: 3 separate EFs (overfragmentation)")
        print()
        print("Use Neo4j to normalize:")
        print("  ef_key = 'conflict_middle-east_CLUSTER_ISRAEL'")
        print("  ef_key = 'conflict_middle-east_CLUSTER_ISRAEL'")
        print("  ef_key = 'conflict_middle-east_CLUSTER_ISRAEL'")
        print("  RESULT: 1 focused EF (same story)")
        print()
        print("Where CLUSTER_ISRAEL = {Israel, Netanyahu, IDF, Tel Aviv}")
        print("Where CLUSTER_PALESTINE = {Palestine, Hamas, Gaza, West Bank}")
        print("Where CLUSTER_US = {United States, Trump, Biden, Washington}")

    driver.close()


if __name__ == "__main__":
    explore_actor_clusters()
