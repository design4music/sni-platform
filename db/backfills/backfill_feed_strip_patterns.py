"""
Backfill strip_patterns for feeds table.

Auto-generates initial patterns from feed name and domain.
These can then be manually curated.

Usage:
    python db/backfill_feed_strip_patterns.py          # Dry run
    python db/backfill_feed_strip_patterns.py --write  # Apply changes
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from core.config import config

# Patterns that should never be added (important orgs)
PROTECTED = {
    "EU",
    "UN",
    "AU",
    "NATO",
    "IMF",
    "WHO",
    "WTO",
    "OPEC",
    "BRICS",
    "G7",
    "G20",
    "ASEAN",
    "FED",
    "ECB",
    "BOJ",
    "PBOC",
    "DOJ",
    "FBI",
    "CIA",
    "NSA",
    "SEC",
    "FDA",
    "EPA",
    "IT",
    "AI",
    "US",
    "UK",
}


def derive_patterns(name: str, domain: str) -> list:
    """Derive strip patterns from feed name and domain."""
    patterns = set()

    if not name:
        return []

    # 1. Full name uppercase
    patterns.add(name.upper())

    # 2. Acronym for multi-word names
    words = [w for w in name.split() if w and w[0].isalpha()]
    if len(words) >= 2:
        acronym = "".join(w[0].upper() for w in words)
        if len(acronym) >= 2 and acronym not in PROTECTED:
            patterns.add(acronym)

    # 3. Domain base name
    if domain:
        base = re.sub(
            r"\.(com|org|net|co|uk|au|in|cn|jp|de|fr|it|es|br|ru|za|ng|pk|bd|lk|eg|tr|ir|sa|ae|il|kr|my|sg|ph|vn|th|id|mx|ar|cl|pe).*$",
            "",
            domain,
        )
        if base and base.upper() != name.upper() and base.upper() not in PROTECTED:
            patterns.add(base.upper())

    # Remove protected patterns
    patterns = {p for p in patterns if p not in PROTECTED}

    # Limit to 3 patterns
    return sorted(patterns)[:3]


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def backfill(write: bool = False):
    conn = get_connection()
    cur = conn.cursor()

    # Get all feeds
    cur.execute(
        "SELECT id, name, source_domain, strip_patterns FROM feeds ORDER BY name"
    )
    feeds = cur.fetchall()

    print("Processing %d feeds..." % len(feeds))

    updates = []
    for feed_id, name, domain, existing in feeds:
        if existing:
            # Skip if already has patterns
            continue

        patterns = derive_patterns(name, domain)
        if patterns:
            updates.append((feed_id, name, patterns))

    print("\nGenerated patterns for %d feeds:" % len(updates))
    for feed_id, name, patterns in updates[:20]:
        print("  %s -> %s" % (name, patterns))
    if len(updates) > 20:
        print("  ... and %d more" % (len(updates) - 20))

    if write and updates:
        print("\nWriting to database...")
        for feed_id, name, patterns in updates:
            cur.execute(
                "UPDATE feeds SET strip_patterns = %s WHERE id = %s",
                (patterns, feed_id),
            )
        conn.commit()
        print("Updated %d feeds" % len(updates))
    elif not write:
        print("\n(Dry run - use --write to apply)")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Apply changes")
    args = parser.parse_args()

    backfill(write=args.write)
