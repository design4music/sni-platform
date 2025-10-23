"""
Document current database state before title restoration
Captures table counts and schemas for verification
"""

import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from core.database import get_db_session


def document_current_state():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    doc_file = f"db_state_before_title_restore_{timestamp}.txt"
    doc_path = Path(__file__).parent / doc_file

    print(f"Documenting current database state: {doc_file}\n")

    with get_db_session() as session:
        # Critical tables to document
        tables = [
            "titles",
            "data_entities",
            "taxonomy_terms",
            "event_families",
            "framed_narratives",
            "feeds",
        ]

        output = []
        output.append(f"=== Database State Documentation ===")
        output.append(f"Timestamp: {timestamp}")
        output.append(f"Database: sni_v2")
        output.append(f"\n{'='*50}\n")

        print("Current table counts:")
        for table in tables:
            try:
                count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                line = f"  {table}: {count:,}"
                print(line)
                output.append(line)
            except Exception as e:
                line = f"  {table}: ERROR - {e}"
                print(line)
                output.append(line)

        # Check strategic_purpose column exists
        output.append(f"\n{'='*50}\n")
        output.append("event_families schema check:")
        try:
            col_check = session.execute(
                text(
                    """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'event_families'
                AND column_name = 'strategic_purpose';
            """
                )
            ).fetchone()

            if col_check:
                output.append(f"  strategic_purpose column: EXISTS")
                output.append(f"    Type: {col_check[1]}")
                output.append(f"    Nullable: {col_check[2]}")
                print(f"\n  strategic_purpose column: EXISTS ({col_check[1]})")
            else:
                output.append(f"  strategic_purpose column: NOT FOUND")
                print(f"\n  strategic_purpose column: NOT FOUND")
        except Exception as e:
            output.append(f"  strategic_purpose check: ERROR - {e}")
            print(f"\n  strategic_purpose check: ERROR")

        # Write to file
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write("\n".join(output))

    print(f"\n{'='*50}")
    print(f"State documented: {doc_path}")
    print(f"{'='*50}\n")

    return doc_path


if __name__ == "__main__":
    document_current_state()
