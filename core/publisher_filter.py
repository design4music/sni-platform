"""
Publisher pattern filter for signal extraction.

Auto-derives patterns from feeds table to filter publisher names
from extracted orgs/signals.
"""

import re

# Important orgs that should NEVER be filtered even if they match publisher patterns
PROTECTED_ORGS = {
    "EU",
    "UN",
    "NATO",
    "IMF",
    "WHO",
    "WTO",
    "OPEC",
    "BRICS",
    "G7",
    "G20",
    "ASEAN",
    "AU",  # African Union
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
}


def derive_publisher_patterns(name: str, domain: str) -> set:
    """Derive patterns to filter from a feed name and domain."""
    patterns = set()

    if not name:
        return patterns

    # 1. Full name (uppercase for matching)
    patterns.add(name.upper())

    # 2. Acronym from multi-word names (e.g., 'Wall Street Journal' -> 'WSJ')
    words = [w for w in name.split() if w[0].isalpha()]
    if len(words) >= 2:
        acronym = "".join(w[0].upper() for w in words)
        if len(acronym) >= 2:
            patterns.add(acronym)

    # 3. Domain name without TLD (e.g., 'nytimes.com' -> 'NYTIMES')
    if domain:
        # Remove TLD
        base = re.sub(
            r"\.(com|org|net|co|uk|au|in|cn|jp|de|fr|it|es|br|ru|za|ng|pk|bd|lk|eg|tr|ir|sa|ae|il|kr|my|sg|ph|vn|th|id|mx|ar|cl|pe).*$",
            "",
            domain,
        )
        if base and base.upper() != name.upper():
            patterns.add(base.upper())

    # 4. Base name without common suffixes
    for suffix in [" News", " World", " Online", " Digital", " Media"]:
        if name.endswith(suffix):
            base_name = name[: -len(suffix)].strip()
            patterns.add(base_name.upper())

    return patterns


def load_publisher_patterns(conn) -> set:
    """Load all publisher patterns from feeds.strip_patterns column.

    Returns set of uppercase patterns to filter from extracted orgs.
    """
    cur = conn.cursor()
    cur.execute("SELECT strip_patterns FROM feeds WHERE strip_patterns IS NOT NULL")
    rows = cur.fetchall()

    all_patterns = set()
    for (patterns,) in rows:
        if patterns:
            all_patterns.update(p.upper() for p in patterns)

    # Safety: remove protected orgs in case they were added
    all_patterns -= PROTECTED_ORGS

    return all_patterns


def filter_publisher_signals(signals: list, publisher_patterns: set) -> list:
    """Filter out publisher names from a list of signals."""
    if not publisher_patterns:
        return signals

    filtered = []
    for sig in signals:
        sig_upper = sig.upper()
        if sig_upper not in publisher_patterns:
            filtered.append(sig)

    return filtered


# =============================================================================
# TITLE CLEANING (removes publisher artifacts from title_display)
# =============================================================================

_cleaning_regex_cache = {}


def _build_cleaning_regex(patterns: set) -> list:
    """Build regex patterns for cleaning publisher names from titles."""
    # Use cache key based on pattern count (patterns rarely change)
    cache_key = len(patterns)
    if cache_key in _cleaning_regex_cache:
        return _cleaning_regex_cache[cache_key]

    # Escape special regex chars in patterns
    escaped = [re.escape(p) for p in patterns if p]
    if not escaped:
        return []

    # Join patterns with OR
    pattern_group = "|".join(escaped)

    regexes = [
        # Prefix patterns: "Pattern: Title" or "Pattern - Title" or "Pattern | Title"
        re.compile(r"^(?:" + pattern_group + r")\s*[:\-\|]\s*", re.IGNORECASE),
        # Suffix patterns: "Title | Pattern" or "Title - Pattern"
        re.compile(r"\s*[:\|\-]\s*(?:" + pattern_group + r")\s*$", re.IGNORECASE),
        # Bracket prefix: "[Pattern] Title"
        re.compile(r"^\[(?:" + pattern_group + r")\]\s*", re.IGNORECASE),
        # Exclusive variations: "Exclusive | Pattern:" or "Pattern Exclusive:"
        re.compile(
            r"^(?:Exclusive\s*[:\|\-]\s*)?(?:"
            + pattern_group
            + r")\s*(?:Exclusive\s*)?[:\-\|]\s*",
            re.IGNORECASE,
        ),
        # Parenthesis suffix: "Title (Pattern)"
        re.compile(r"\s*\((?:" + pattern_group + r")\)\s*$", re.IGNORECASE),
    ]

    _cleaning_regex_cache[cache_key] = regexes
    return regexes


def load_title_cleaning_patterns(conn) -> set:
    """Load patterns for title cleaning (includes multiple case variants)."""
    cur = conn.cursor()
    cur.execute("SELECT strip_patterns FROM feeds WHERE strip_patterns IS NOT NULL")
    rows = cur.fetchall()

    patterns = set()
    for (arr,) in rows:
        if arr:
            for p in arr:
                patterns.add(p.upper())
                patterns.add(p)  # Original case
                patterns.add(p.title())  # Title case

    return patterns


def clean_title_display(title: str, patterns: set) -> str:
    """
    Clean publisher artifacts from a title.

    Handles:
    - "Pattern: Title here" -> "Title here" (prefix with colon)
    - "Title here | Pattern" -> "Title here" (suffix with pipe)
    - "Title here - Pattern" -> "Title here" (suffix with dash)
    - "[Pattern] Title here" -> "Title here" (prefix in brackets)
    - "Pattern Exclusive: Title" -> "Title" (prefix variations)
    - "Title (Pattern)" -> "Title" (parenthesis suffix)

    Returns original title if cleaning would result in empty string.
    """
    if not title or not patterns:
        return title

    regexes = _build_cleaning_regex(patterns)
    if not regexes:
        return title

    original = title
    for regex in regexes:
        title = regex.sub("", title)

    # Clean up extra whitespace
    title = " ".join(title.split())

    # Don't return empty titles
    if not title.strip():
        return original

    return title


if __name__ == "__main__":
    # Test pattern derivation
    test_feeds = [
        ("Wall Street Journal", "wsj.com"),
        ("Hindustan Times", "hindustantimes.com"),
        ("CNN", "cnn.com"),
        ("BBC World", "bbc.com"),
        ("New York Times", "nytimes.com"),
        ("Al Jazeera", "aljazeera.com"),
        ("India Today", "indiatoday.in"),
        ("Channel NewsAsia", "channelnewsasia.com"),
    ]

    print("Pattern derivation test:")
    print("=" * 60)
    for name, domain in test_feeds:
        patterns = derive_publisher_patterns(name, domain)
        print("%s -> %s" % (name, sorted(patterns)))
