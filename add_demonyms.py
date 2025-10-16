#!/usr/bin/env python3
"""
Add demonym forms (adjectives/demonyms) to entity aliases
Examples: Israeli for Israel, Palestinians for Palestine, Chinese for China
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import text

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.database import get_db_session  # noqa: E402

# Mapping of entity_id -> demonym/additional forms to add
DEMONYM_ADDITIONS = {
    "IL": ["Israeli", "Israelis"],
    "PS": ["Palestinian", "Palestinians", "Gaza", "Gazan", "Gazans", "West Bank"],
    "CN": ["Chinese"],
    "RU": ["Russian", "Russians"],
    "US": ["American", "Americans"],
    "UK": ["British"],
    "FR": ["French"],
    "DE": ["German", "Germans"],
    "IR": ["Iranian", "Iranians"],
    "IQ": ["Iraqi", "Iraqis"],
    "SY": ["Syrian", "Syrians"],
    "TR": ["Turkish"],
    "SA": ["Saudi", "Saudis"],
    "EG": ["Egyptian", "Egyptians"],
    "IN": ["Indian", "Indians"],
    "PK": ["Pakistani", "Pakistanis"],
    "JP": ["Japanese"],
    "KR": ["Korean", "Koreans", "South Korean", "South Koreans"],
    "UA": ["Ukrainian", "Ukrainians"],
}


def add_demonyms():
    """Add demonym forms to entity English aliases"""

    with get_db_session() as session:
        total_added = 0

        for entity_id, additions in DEMONYM_ADDITIONS.items():
            # Get current aliases
            result = session.execute(
                text(
                    "SELECT name_en, aliases FROM data_entities WHERE entity_id = :entity_id"
                ),
                {"entity_id": entity_id},
            ).fetchone()

            if not result:
                print(f"Entity {entity_id} not found, skipping")
                continue

            # Parse current aliases
            current_aliases = (
                result.aliases
                if isinstance(result.aliases, dict)
                else json.loads(result.aliases)
            )

            # Add to English aliases (check if not already present)
            en_aliases = current_aliases.get("en", [])
            added = []
            for addition in additions:
                if addition not in en_aliases:
                    en_aliases.append(addition)
                    added.append(addition)

            if added:
                current_aliases["en"] = en_aliases

                # Update database
                session.execute(
                    text(
                        "UPDATE data_entities SET aliases = :aliases WHERE entity_id = :entity_id"
                    ),
                    {"aliases": json.dumps(current_aliases), "entity_id": entity_id},
                )

                print(f"Added to {entity_id} ({result.name_en}): {', '.join(added)}")
                total_added += len(added)
            else:
                print(
                    f"No new additions for {entity_id} ({result.name_en}) - already present"
                )

        session.commit()
        print(f"\n✓ Added {total_added} demonyms/aliases successfully!")


if __name__ == "__main__":
    add_demonyms()
