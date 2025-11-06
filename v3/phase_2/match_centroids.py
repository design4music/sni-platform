"""
Phase 2: 3-Pass Centroid Matcher

Mechanical matching without LLM gate_keep:
- Pass 1: Theater centroids (geo/person/org/model from taxonomy)
- Pass 2: Systemic centroids (anchor/domain/model for global topics)
- Pass 3: Macro centroids (superpower domestic catch-alls)

Uses proven v2 matching logic from taxonomy_extractor.py
"""

import re
import sys
import unicodedata
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config


def normalize_text(text: str) -> str:
    """
    Normalize text using v2 taxonomy_extractor logic.
    NFKC normalization, lowercase, remove periods, collapse whitespace.
    """
    if not text:
        return ""

    # NFKC Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # Remove periods (for matching "U.S." to "us", "U.K." to "uk", etc.)
    text = text.replace(".", "")

    # Lowercase and collapse whitespace
    text = re.sub(r"\s+", " ", text.lower()).strip()

    return text


def is_common_word_false_positive(alias_lower: str) -> bool:
    """Filter out common words that cause false positives across languages"""
    common_words = {
        # 2-letter words (English)
        "in",
        "is",
        "it",
        "as",
        "or",
        "no",
        "so",
        "to",
        "an",
        "at",
        "be",
        "by",
        "do",
        "go",
        "he",
        "if",
        "me",
        "my",
        "of",
        "on",
        "we",
        # 2-letter words (Romance languages - articles, prepositions)
        "il",  # Italian/French article "the"
        "la",  # Italian/French/Spanish article "the"
        "le",  # French article "the"
        "el",  # Spanish article "the"
        "un",  # Italian/French/Spanish article "a/an"
        "di",  # Italian preposition "of"
        "da",  # Italian preposition "from"
        "al",  # Italian/Spanish preposition "to the"
        "del",  # Italian/Spanish preposition "of the"
        # 3-letter words
        "who",
        "the",
        "and",
        "for",
        "are",
        "but",
        "not",
    }
    return alias_lower in common_words


def has_substring_script_chars(text: str) -> bool:
    """Check if text contains CJK scripts that need substring matching"""
    return any(
        "\u4e00" <= char <= "\u9fff"  # Chinese (Han ideographs)
        or "\u3040" <= char <= "\u309f"  # Japanese Hiragana
        or "\u30a0" <= char <= "\u30ff"  # Japanese Katakana
        or "\u0e00" <= char <= "\u0e7f"  # Thai
        for char in text
    )


def load_taxonomy():
    """
    Load all active taxonomy items and precompile patterns using v2 logic.
    Returns precompiled patterns for fast matching.
    """
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, item_raw, item_type, centroid_ids, aliases
            FROM taxonomy_v3
            WHERE is_active = true
        """
        )
        results = cur.fetchall()

    conn.close()

    taxonomy = {
        "pass1_patterns": [],  # [(centroid_ids, pattern, alias, use_substring)]
        "pass2_patterns": [],  # [(centroid_ids, pattern, alias, use_substring)]
        "pass3_patterns": [],  # [(centroid_ids, pattern, alias, use_substring)] for macro centroids
        "stop_patterns": [],  # [(pattern, alias, use_substring)] for stop words
    }

    for id, item_raw, item_type, centroid_ids, aliases in results:
        # Build searchable terms from item_raw + all aliases
        terms = {normalize_text(item_raw)}
        if aliases:
            if isinstance(aliases, dict):
                # Language-code format
                for lang_aliases in aliases.values():
                    terms.update(normalize_text(a) for a in lang_aliases)
            elif isinstance(aliases, list):
                # Flat array format (legacy)
                terms.update(normalize_text(a) for a in aliases)

        # Handle stop words
        if item_type == "stop":
            for term in terms:
                if is_common_word_false_positive(term):
                    continue
                if has_substring_script_chars(term):
                    taxonomy["stop_patterns"].append((None, term, True))
                else:
                    pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
                    taxonomy["stop_patterns"].append((pattern, None, False))
            continue

        # Determine which pass this item belongs to
        target_list = None
        if item_type in ("geo", "person", "org", "model"):
            target_list = taxonomy["pass1_patterns"]
        elif item_type in ("anchor", "domain"):
            target_list = taxonomy["pass2_patterns"]
        elif item_type == "macro":
            # Macro centroid keywords (for Pass 3 matching)
            target_list = taxonomy["pass3_patterns"]

        if target_list is not None and centroid_ids:
            # Precompile patterns for each term using v2 logic
            for term in terms:
                # Skip common word false positives
                if is_common_word_false_positive(term):
                    continue

                # Check if term needs substring matching (CJK scripts)
                if has_substring_script_chars(term):
                    # Substring matching for CJK
                    target_list.append((centroid_ids, None, term, True))
                else:
                    # Word boundary matching for Latin/Cyrillic
                    pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
                    target_list.append((centroid_ids, pattern, None, False))

    return taxonomy


def match_title(title_text, taxonomy):
    """
    Match title against taxonomy using v2 proven logic with stop word filtering.
    Returns: (matched_centroids, pass_number)
    pass_number: 1 for Pass 1 match, 2 for Pass 2 match, 3 for Pass 3 match, 0 for no match/blocked
    """
    normalized_title = normalize_text(title_text)
    matched_centroids = set()
    pass_number = 0

    # Check stop words FIRST (blocks everything if matched)
    for pattern, alias, use_substring in taxonomy["stop_patterns"]:
        if use_substring:
            if alias and alias in normalized_title:
                return set(), 0  # Blocked by stop word
        else:
            if pattern and pattern.search(normalized_title):
                return set(), 0  # Blocked by stop word

    # Pass 1: Theater centroids (geo/person/org/model)
    for centroid_ids, pattern, alias, use_substring in taxonomy["pass1_patterns"]:
        if use_substring:
            # Substring matching for CJK
            if alias and alias in normalized_title:
                matched_centroids.update(centroid_ids)
                pass_number = 1
        else:
            # Word boundary matching for Latin/Cyrillic
            if pattern and pattern.search(normalized_title):
                matched_centroids.update(centroid_ids)
                pass_number = 1

    # Pass 2: Systemic centroids (anchor/domain) - only if Pass 1 didn't match
    if not matched_centroids:
        for centroid_ids, pattern, alias, use_substring in taxonomy["pass2_patterns"]:
            if use_substring:
                # Substring matching for CJK
                if alias and alias in normalized_title:
                    matched_centroids.update(centroid_ids)
                    pass_number = 2
            else:
                # Word boundary matching for Latin/Cyrillic
                if pattern and pattern.search(normalized_title):
                    matched_centroids.update(centroid_ids)
                    pass_number = 2

    # Pass 3: Macro centroids with keyword matching (only if Pass 1 and 2 didn't match)
    if not matched_centroids:
        for centroid_ids, pattern, alias, use_substring in taxonomy["pass3_patterns"]:
            if use_substring:
                # Substring matching for CJK
                if alias and alias in normalized_title:
                    matched_centroids.update(centroid_ids)
                    pass_number = 3
            else:
                # Word boundary matching for Latin/Cyrillic
                if pattern and pattern.search(normalized_title):
                    matched_centroids.update(centroid_ids)
                    pass_number = 3

    return matched_centroids, pass_number


def process_batch(batch_size=100, max_titles=None):
    """Process a batch of unassigned titles"""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    print("Loading taxonomy...")
    taxonomy = load_taxonomy()
    print(f"  Pass 1 patterns: {len(taxonomy['pass1_patterns'])} patterns")
    print(f"  Pass 2 patterns: {len(taxonomy['pass2_patterns'])} patterns")
    print(
        f"  Pass 3 patterns: {len(taxonomy['pass3_patterns'])} patterns (macro keywords)"
    )
    print(f"  Stop patterns: {len(taxonomy['stop_patterns'])} patterns")

    with conn.cursor() as cur:
        # Get pending titles
        limit_clause = f"LIMIT {max_titles}" if max_titles else ""
        cur.execute(
            f"""
            SELECT id, title_display
            FROM titles_v3
            WHERE processing_status = 'pending'
            ORDER BY created_at DESC
            {limit_clause}
        """
        )
        titles = cur.fetchall()

    print(f"\nProcessing {len(titles)} titles...")

    assigned_count = 0
    out_of_scope_count = 0
    pass1_count = 0
    pass2_count = 0
    pass3_count = 0

    for title_id, title_text in titles:
        # Match against taxonomy
        matched_centroids, pass_num = match_title(title_text, taxonomy)

        if matched_centroids:
            # Found matches in Pass 1, 2, or 3
            if pass_num == 1:
                pass1_count += 1
            elif pass_num == 2:
                pass2_count += 1
            elif pass_num == 3:
                pass3_count += 1

            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE titles_v3
                    SET centroid_ids = %s,
                        processing_status = 'assigned',
                        updated_at = NOW()
                    WHERE id = %s
                """,
                    (list(matched_centroids), title_id),
                )
            assigned_count += 1
        else:
            # No matches or blocked by stop word - mark as out of scope
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE titles_v3
                    SET processing_status = 'out_of_scope',
                        updated_at = NOW()
                    WHERE id = %s
                """,
                    (title_id,),
                )
            out_of_scope_count += 1

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Total processed:     {len(titles)}")
    print(f"Assigned:            {assigned_count}")
    print(f"  - Pass 1 (theater):  {pass1_count}")
    print(f"  - Pass 2 (systemic): {pass2_count}")
    print(f"  - Pass 3 (macro):    {pass3_count}")
    print(f"Out of scope:        {out_of_scope_count}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 2: Match titles to centroids")
    parser.add_argument(
        "--max-titles", type=int, help="Maximum number of titles to process"
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Batch size for processing"
    )

    args = parser.parse_args()

    process_batch(batch_size=args.batch_size, max_titles=args.max_titles)
