#!/usr/bin/env python3
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session

with get_db_session() as session:
    result = session.execute(
        text(
            """
        SELECT entity_id, name_en, aliases
        FROM data_entities
        WHERE entity_id IN ('AD', 'AE', 'TW', 'US')
        ORDER BY entity_id
    """
        )
    )

    output = []
    for row in result:
        output.append(f"\n{row.entity_id}: {row.name_en}")
        aliases_data = (
            row.aliases if isinstance(row.aliases, dict) else json.loads(row.aliases)
        )

        for lang, alias_list in aliases_data.items():
            output.append(f"  {lang}: {alias_list}")

    # Write to file to avoid console encoding issues
    with open("aliases_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print("Output written to aliases_output.txt")
