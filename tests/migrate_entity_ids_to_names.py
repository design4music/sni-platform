#!/usr/bin/env python3
"""
Migration Script: Convert entity_ids to name_en in titles.entities

Backfills existing titles that have entity_ids (US, IL, PS, IN, AG, etc.)
with their canonical name_en values (United States, Israel, State of Palestine, etc.)
"""

import json
from typing import Dict, List

from sqlalchemy import text

from core.database import get_db_session

print("=" * 80)
print("MIGRATION: Convert entity_ids to name_en in titles.entities")
print("=" * 80)


def load_entity_id_to_name_mapping() -> Dict[str, str]:
    """Load mapping of entity_id -> name_en from data_entities table"""
    mapping = {}

    with get_db_session() as session:
        query = """
        SELECT entity_id, name_en
        FROM data_entities
        ORDER BY entity_id;
        """

        results = session.execute(text(query)).fetchall()
        for row in results:
            mapping[row.entity_id] = row.name_en

    print(f"\nLoaded {len(mapping)} entity_id -> name_en mappings")
    return mapping


def convert_entities_array(
    entities_json: List[str], mapping: Dict[str, str]
) -> List[str]:
    """
    Convert entity_ids in entities array to name_en values

    Args:
        entities_json: Current entities array (may contain mix of entity_ids and name_en)
        mapping: entity_id → name_en mapping

    Returns:
        Converted entities array with all name_en values
    """
    if not entities_json:
        return entities_json

    converted = []
    changes = []

    for entity in entities_json:
        # Check if this is an entity_id that needs conversion
        if entity in mapping:
            name_en = mapping[entity]
            # Only convert if entity_id != name_en (e.g., "US" != "United States")
            if entity != name_en:
                converted.append(name_en)
                changes.append(f"{entity} -> {name_en}")
            else:
                # Already correct (e.g., "EU" == "EU", "NATO" == "NATO")
                converted.append(entity)
        else:
            # Not in mapping - might be already converted or unmatched
            # Keep as-is
            converted.append(entity)

    return converted, changes


def migrate_titles():
    """Migrate all titles with entity_ids to name_en"""

    # Load entity_id → name_en mapping
    mapping = load_entity_id_to_name_mapping()

    stats = {
        "total_titles": 0,
        "titles_updated": 0,
        "entities_converted": 0,
        "no_changes": 0,
    }

    with get_db_session() as session:
        # Get all titles with entities
        query = """
        SELECT id, title_display, entities
        FROM titles
        WHERE entities IS NOT NULL AND entities != '[]'
        ORDER BY created_at DESC;
        """

        results = session.execute(text(query)).fetchall()
        stats["total_titles"] = len(results)

        print(f"\nProcessing {stats['total_titles']} titles with entities...")
        print("-" * 80)

        for row in results:
            title_id = row.id
            title_display = row.title_display
            entities = row.entities  # Already parsed as list by psycopg2

            # Convert entities
            converted, changes = convert_entities_array(entities, mapping)

            if changes:
                # Update title with converted entities
                update_query = """
                UPDATE titles
                SET entities = :entities
                WHERE id = :title_id;
                """

                session.execute(
                    text(update_query),
                    {"entities": json.dumps(converted), "title_id": title_id},
                )

                stats["titles_updated"] += 1
                stats["entities_converted"] += len(changes)

                # Handle Unicode encoding for Windows console
                try:
                    print(f"\nUpdated: {title_display[:60]}")
                except UnicodeEncodeError:
                    safe_title = (
                        title_display[:60].encode("ascii", "ignore").decode("ascii")
                    )
                    print(f"\nUpdated: {safe_title}")

                for change in changes:
                    print(f"  {change}")
            else:
                stats["no_changes"] += 1

        # Commit all changes
        session.commit()

    return stats


if __name__ == "__main__":
    print("\nStarting migration...")

    stats = migrate_titles()

    print("\n" + "=" * 80)
    print("MIGRATION COMPLETE")
    print("=" * 80)
    print(f"Total titles processed: {stats['total_titles']}")
    print(f"Titles updated: {stats['titles_updated']}")
    print(f"Entities converted: {stats['entities_converted']}")
    print(f"Titles with no changes: {stats['no_changes']}")
    print("=" * 80)

    if stats["titles_updated"] > 0:
        print(
            f"\nSUCCESS: Converted {stats['entities_converted']} entity_ids to name_en"
        )
    else:
        print("\nSUCCESS: No entity_ids found - all entities already use name_en")
