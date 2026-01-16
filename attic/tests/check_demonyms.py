#!/usr/bin/env python3
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session

# Check what aliases Israel and Palestine have
with get_db_session() as session:
    result = session.execute(
        text(
            """
        SELECT entity_id, name_en, aliases
        FROM data_entities
        WHERE entity_id IN ('IL', 'PS')
        ORDER BY entity_id
    """
        )
    )

    with open("demonyms_check.txt", "w", encoding="utf-8") as f:
        for row in result:
            f.write(f"\n{row.entity_id}: {row.name_en}\n")
            f.write("=" * 60 + "\n")
            aliases_data = (
                row.aliases
                if isinstance(row.aliases, dict)
                else json.loads(row.aliases)
            )

            for lang, alias_list in aliases_data.items():
                f.write(f"\n{lang}:\n")
                for alias in alias_list:
                    # Highlight demonym-like terms
                    alias_lower = alias.lower()
                    if (
                        "israel" in alias_lower
                        or "palestinian" in alias_lower
                        or "palestine" in alias_lower
                    ):
                        f.write(f"  *** '{alias}'\n")
                    else:
                        f.write(f"  '{alias}'\n")

print("Output written to demonyms_check.txt")
