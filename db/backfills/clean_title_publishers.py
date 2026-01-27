"""
Clean publisher artifacts from titles_v3.title_display.

Uses feeds.strip_patterns to identify and remove publisher names from titles.

Patterns handled:
- "{pattern}: Title here" -> "Title here" (prefix with colon)
- "Title here | {pattern}" -> "Title here" (suffix with pipe)
- "Title here - {pattern}" -> "Title here" (suffix with dash)
- "[{pattern}] Title here" -> "Title here" (prefix in brackets)
- "{pattern} Exclusive: Title" -> "Title" (prefix variations)
- "Exclusive | {pattern}: Title" -> "Title" (complex prefixes)

Usage:
    python db/clean_title_publishers.py                  # Dry run, show samples
    python db/clean_title_publishers.py --write          # Apply changes
    python db/clean_title_publishers.py --limit 100      # Process limited titles
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from core.config import config


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def load_strip_patterns(conn) -> set:
    """Load all strip patterns from feeds table."""
    cur = conn.cursor()
    cur.execute("SELECT strip_patterns FROM feeds WHERE strip_patterns IS NOT NULL")
    rows = cur.fetchall()

    patterns = set()
    for (arr,) in rows:
        if arr:
            for p in arr:
                patterns.add(p.upper())
                patterns.add(p)  # Keep original case too
                patterns.add(p.title())  # Title case

    return patterns


def build_cleaning_regex(patterns: set) -> list:
    """Build regex patterns for cleaning titles."""
    # Escape special regex chars in patterns
    escaped = [re.escape(p) for p in patterns if p]

    if not escaped:
        return []

    # Join patterns with OR
    pattern_group = "|".join(escaped)

    regexes = [
        # Prefix patterns: "Pattern: Title" or "Pattern - Title" or "Pattern | Title"
        (
            re.compile(r"^(?:" + pattern_group + r")\s*[:\-\|]\s*", re.IGNORECASE),
            "prefix",
        ),
        # Suffix patterns: "Title | Pattern" or "Title - Pattern"
        (
            re.compile(r"\s*[:\|\-]\s*(?:" + pattern_group + r")\s*$", re.IGNORECASE),
            "suffix",
        ),
        # Bracket prefix: "[Pattern] Title"
        (re.compile(r"^\[(?:" + pattern_group + r")\]\s*", re.IGNORECASE), "bracket"),
        # Exclusive variations: "Exclusive | Pattern:" or "Pattern Exclusive:"
        (
            re.compile(
                r"^(?:Exclusive\s*[:\|\-]\s*)?(?:"
                + pattern_group
                + r")\s*(?:Exclusive\s*)?[:\-\|]\s*",
                re.IGNORECASE,
            ),
            "exclusive",
        ),
        # Parenthesis suffix: "Title (Pattern)"
        (re.compile(r"\s*\((?:" + pattern_group + r")\)\s*$", re.IGNORECASE), "paren"),
    ]

    return regexes


def clean_title(title: str, regexes: list) -> tuple:
    """Clean a title using regex patterns.

    Returns: (cleaned_title, list of matches found)
    """
    if not title:
        return title, []

    original = title
    matches = []

    for regex, pattern_type in regexes:
        match = regex.search(title)
        if match:
            matches.append((pattern_type, match.group()))
            title = regex.sub("", title)

    # Clean up extra whitespace
    title = " ".join(title.split())

    # Don't return empty titles
    if not title.strip():
        return original, []

    return title, matches


def process_titles(write: bool = False, limit: int = None):
    """Process all titles and clean publisher artifacts."""
    conn = get_connection()
    cur = conn.cursor()

    # Load patterns
    print("Loading strip patterns from feeds...")
    patterns = load_strip_patterns(conn)
    print("Loaded %d patterns" % len(patterns))

    # Build regexes
    regexes = build_cleaning_regex(patterns)
    print("Built %d cleaning regexes" % len(regexes))

    # Get titles
    query = "SELECT id, title_display FROM titles_v3 WHERE title_display IS NOT NULL"
    if limit:
        query += " LIMIT %d" % limit

    cur.execute(query)
    titles = cur.fetchall()
    print("Processing %d titles...\n" % len(titles))

    # Process
    updates = []
    match_counts = {"prefix": 0, "suffix": 0, "bracket": 0, "exclusive": 0, "paren": 0}

    for title_id, title_display in titles:
        cleaned, matches = clean_title(title_display, regexes)

        if matches and cleaned != title_display:
            updates.append((title_id, title_display, cleaned, matches))
            for match_type, _ in matches:
                match_counts[match_type] += 1

    # Report
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print("Titles processed: %d" % len(titles))
    print("Titles to clean: %d" % len(updates))
    print("\nMatch types:")
    for match_type, count in sorted(match_counts.items(), key=lambda x: -x[1]):
        if count > 0:
            print("  %s: %d" % (match_type, count))

    # Show samples
    if updates:
        print("\n" + "-" * 70)
        print("SAMPLE CHANGES (first 30)")
        print("-" * 70)
        for title_id, original, cleaned, matches in updates[:30]:
            orig_safe = original[:70].encode("ascii", "replace").decode()
            clean_safe = cleaned[:70].encode("ascii", "replace").decode()
            match_str = ", ".join(m[1][:20] for m in matches)
            print("\nBEFORE: %s" % orig_safe)
            print("AFTER:  %s" % clean_safe)
            print("MATCH:  %s" % match_str)

        if len(updates) > 30:
            print("\n... and %d more" % (len(updates) - 30))

    # Write
    if write and updates:
        print("\n" + "=" * 70)
        print("Writing %d updates..." % len(updates))
        for title_id, original, cleaned, matches in updates:
            cur.execute(
                "UPDATE titles_v3 SET title_display = %s WHERE id = %s",
                (cleaned, title_id),
            )
        conn.commit()
        print("Done!")
    elif not write and updates:
        print("\n(Dry run - use --write to apply changes)")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clean publisher artifacts from titles"
    )
    parser.add_argument(
        "--write", action="store_true", help="Apply changes to database"
    )
    parser.add_argument("--limit", type=int, help="Limit titles to process")

    args = parser.parse_args()

    process_titles(write=args.write, limit=args.limit)
