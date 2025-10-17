#!/usr/bin/env python3
"""
Clear all Entity nodes and MENTIONS relationships from Neo4j
Keep Title nodes intact
"""

import os

from neo4j import GraphDatabase

# Neo4j connection from environment
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "sni_password_2024")

print("=" * 60)
print("Clear Neo4j Entities")
print("=" * 60)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

try:
    with driver.session() as session:
        # Count entities before deletion
        result = session.run(
            """
            MATCH (e:Entity)
            RETURN count(e) as entity_count
        """
        )
        record = result.single()
        entity_count = record["entity_count"] if record else 0

        # Count MENTIONS relationships
        result = session.run(
            """
            MATCH ()-[r:MENTIONS]->()
            RETURN count(r) as mention_count
        """
        )
        record = result.single()
        mention_count = record["mention_count"] if record else 0

        print("\nBefore Clear:")
        print(f"  Entity nodes: {entity_count}")
        print(f"  MENTIONS relationships: {mention_count}")

        # Delete all Entity nodes (this will cascade delete MENTIONS relationships)
        print("\nDeleting entities...")
        session.run(
            """
            MATCH (e:Entity)
            DETACH DELETE e
        """
        )

        # Verify deletion
        result = session.run(
            """
            MATCH (e:Entity)
            RETURN count(e) as entity_count
        """
        )
        record = result.single()
        remaining = record["entity_count"] if record else 0

        print("\nAfter Clear:")
        print(f"  Entity nodes: {remaining}")
        print("\n[OK] Neo4j entities cleared!")

except Exception as e:
    print(f"\n[ERROR] Failed to clear Neo4j: {e}")

finally:
    driver.close()

print("=" * 60)
