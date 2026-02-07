"""
Fix specific outdated role descriptions in generated content.

Only targets confirmed incorrect descriptions:
- "former president Trump" -> "Trump" (Trump is current president)
- "opposition leader Merz" -> "Merz" (Merz is now Chancellor)

Usage:
    python db/scripts/fix_outdated_titles.py --dry-run
    python db/scripts/fix_outdated_titles.py --apply
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2

from core.config import config

# Only these specific patterns - confirmed incorrect
PATTERNS = [
    (r"Former U\.S\. President (Donald )?Trump", "Trump"),
    (r"former U\.S\. [Pp]resident (Donald )?Trump", "Trump"),
    (r"former [Pp]resident[- ]*(Donald )?Trump", "Trump"),
    (r"ex-[Pp]resident[- ]*(Donald )?Trump", "Trump"),
    (r"opposition leader[- ]*(Friedrich )?Merz", "Merz"),
    (r"CDU leader[- ]*(Friedrich )?Merz", "Merz"),
]

# Regular text columns
TABLES = [
    ("events_v3", "id", ["title", "summary"]),
    ("ctm", "id", ["summary_text"]),
    ("epics", "id", ["summary", "timeline"]),
    ("centroid_monthly_summaries", "id", ["summary_text"]),
]

# JSONB columns that need special handling
JSONB_TABLES = [
    ("epics", "id", "narratives"),
]


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def main():
    parser = argparse.ArgumentParser(description="Fix outdated role descriptions")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes to database"
    )
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("Please specify --dry-run or --apply")
        return

    dry_run = args.dry_run

    print("=" * 60)
    print("Fix Outdated Role Descriptions")
    print("Targets: 'former president Trump', 'opposition leader Merz'")
    print("Mode:", "DRY RUN" if dry_run else "APPLY")
    print("=" * 60)

    conn = get_connection()
    cur = conn.cursor()

    total_fixed = 0

    for table, id_col, columns in TABLES:
        for col in columns:
            cur.execute(f"SELECT {id_col}, {col} FROM {table} WHERE {col} IS NOT NULL")
            rows = cur.fetchall()

            for row_id, text in rows:
                if not text:
                    continue

                new_text = text
                matches_found = []

                for pattern, replacement in PATTERNS:
                    match = re.search(pattern, new_text, flags=re.IGNORECASE)
                    if match:
                        matches_found.append(match.group())
                    new_text, _ = re.subn(
                        pattern, replacement, new_text, flags=re.IGNORECASE
                    )

                if matches_found:
                    total_fixed += 1
                    print(f"\n[{table}.{col}] ID={row_id}")
                    for m in matches_found:
                        print(f"  - '{m}' -> fixed")

                    if not dry_run:
                        cur.execute(
                            f"UPDATE {table} SET {col} = %s WHERE {id_col} = %s",
                            (new_text, row_id),
                        )

    # Handle JSONB columns
    for table, id_col, col in JSONB_TABLES:
        cur.execute(f"SELECT {id_col}, {col} FROM {table} WHERE {col} IS NOT NULL")
        rows = cur.fetchall()

        for row_id, jsonb_data in rows:
            if not jsonb_data:
                continue

            text = json.dumps(jsonb_data)
            new_text = text
            matches_found = []

            for pattern, replacement in PATTERNS:
                match = re.search(pattern, new_text, flags=re.IGNORECASE)
                if match:
                    matches_found.append(match.group())
                new_text, _ = re.subn(
                    pattern, replacement, new_text, flags=re.IGNORECASE
                )

            if matches_found:
                total_fixed += 1
                print(f"\n[{table}.{col}] ID={row_id}")
                for m in matches_found:
                    print(f"  - '{m}' -> fixed")

                if not dry_run:
                    new_jsonb = json.loads(new_text)
                    cur.execute(
                        f"UPDATE {table} SET {col} = %s WHERE {id_col} = %s",
                        (json.dumps(new_jsonb), row_id),
                    )

    if not dry_run:
        conn.commit()

    print("\n" + "=" * 60)
    print(f"Total: {total_fixed} rows {'would be ' if dry_run else ''}fixed")

    conn.close()


if __name__ == "__main__":
    main()
