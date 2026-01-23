"""
Phase 2: Accumulative Centroid Matcher

Mechanical matching without LLM gate_keep:
- Match ALL centroids (geo + systemic) accumulative
- One title can match multiple centroids
- Enables bilateral relationship tracking and comprehensive event aggregation

Performance optimizations:
- Pre-tokenization + hash-based matching (O(n) instead of O(n*m))
- Precompiled regex patterns (compile once, not per title)
- Script-aware matching (word boundaries for ASCII, substring for others)
- Stop word fast-fail
- Batched database updates

Uses proven v2 matching logic from taxonomy_extractor.py
"""

import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

# =============================================================================
# CANONICAL ALIAS MAPPING
# =============================================================================
# Maps language variants to canonical (English) form for clustering.
# Add new mappings here as needed. Format: "variant": "canonical"
# =============================================================================
CANONICAL_ALIASES = {
    # Greenland variants
    "groenlandia": "greenland",  # Spanish/Italian
    "groenland": "greenland",  # French/Dutch
    "gronland": "greenland",  # German (without umlaut)
    "grönland": "greenland",  # German (with umlaut)
    "grønland": "greenland",  # Danish/Norwegian
    "гренландия": "greenland",  # Russian
    "格陵兰": "greenland",  # Chinese
    "جرينلاند": "greenland",  # Arabic
    # Tariffs variants
    "dazi": "tariffs",  # Italian
    "aranceles": "tariffs",  # Spanish
    "droits de douane": "tariffs",  # French
    "zolle": "tariffs",  # German (Zölle)
    "zoll": "tariffs",  # German singular
    "tarifas": "tariffs",  # Portuguese
    "тарифы": "tariffs",  # Russian
    "关税": "tariffs",  # Chinese
    # Federal Reserve variants
    "reserva federal": "federal reserve",  # Spanish
    "fed": "fed",  # Keep as-is (already canonical)
    # Add more as discovered...
}


def canonicalize_alias(alias: str) -> str:
    """Map alias to canonical form, or return as-is if no mapping exists."""
    return CANONICAL_ALIASES.get(alias, alias)


def strip_diacritics(text: str) -> str:
    """
    Remove Unicode diacritics (accent marks) from text.
    Example: "Côte d'Ivoire" -> "Cote d'Ivoire"
    """
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def normalize_text(text: str) -> str:
    """
    Normalize text using v2 taxonomy_extractor logic.
    Steps: lowercase, strip diacritics, remove periods, normalize dashes, collapse whitespace.
    """
    if not text:
        return ""

    # Lowercase first
    text = text.lower()

    # Strip diacritics (Côte d'Ivoire -> Cote d'Ivoire)
    text = strip_diacritics(text)

    # NFKC Unicode normalization (after diacritic stripping)
    text = unicodedata.normalize("NFKC", text)

    # Remove periods (for matching "U.S." to "us", "U.K." to "uk", etc.)
    text = text.replace(".", "")

    # Normalize all dash types to standard hyphen (-, –, —, ―)
    text = text.replace("–", "-")  # en-dash
    text = text.replace("—", "-")  # em-dash
    text = text.replace("―", "-")  # horizontal bar

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def tokenize_text(text: str) -> set:
    """
    Extract word tokens from normalized text for hash-based matching.
    Handles hyphenated terms and compound words:
    - Preserves full hyphenated terms: "Tu-214", "F-35"
    - Also splits compounds: "China-made" -> {"china-made", "china", "made"}
    - Strips possessive suffixes: "Netanyahu's" -> "netanyahu"
    Returns set of individual words and their components.
    """
    # Extract tokens: word characters with optional internal hyphens
    # Matches: "word", "Tu-214", "F-35", but not "-word" or "word-"
    tokens = re.findall(r"\b[\w][\w-]*[\w]\b|\b\w\b", text.lower())

    # Strip possessive suffixes and split hyphenated compounds
    cleaned_tokens = set()
    for token in tokens:
        # Remove common possessive patterns
        if token.endswith("'s") or token.endswith("'s"):
            token = token[:-2]
        elif token.endswith("'"):
            token = token[:-1]

        # Add the full token
        cleaned_tokens.add(token)

        # If token contains hyphen, also add individual parts
        # This allows "china-made" to match "china" and "us-russian" to match "us" + "russian"
        if "-" in token:
            parts = token.split("-")
            for part in parts:
                if part:  # Skip empty parts
                    cleaned_tokens.add(part)

    return cleaned_tokens


def is_ascii_only(text: str) -> bool:
    """Check if text contains only ASCII letters, numbers, and spaces"""
    return all(c.isascii() and (c.isalnum() or c.isspace()) for c in text)


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
        "il",
        "la",
        "le",
        "el",
        "un",
        "di",
        "da",
        "al",
        "del",
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
    Load all active taxonomy items and build hash-based lookup structures.

    Returns:
        taxonomy dict with:
        - stop_words_set: set of stop word tokens (hash lookup)
        - stop_phrase_patterns: list of (pattern_type, pattern/substring) for stop phrases
        - single_word_aliases: dict mapping word -> set of centroid_ids (multiple aliases per centroid)
        - phrase_patterns: list of (compiled_pattern, centroid_id) for multi-word phrases (ASCII)
        - phrase_substrings: list of (substring, centroid_id) for multi-word phrases (non-ASCII)
        - substring_patterns: list of (substring, centroid_id) for CJK matching
    """
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    with conn.cursor() as cur:
        # Load all taxonomy items (label is display-only, not used for matching)
        cur.execute(
            """
            SELECT id, is_stop_word, centroid_id, aliases
            FROM taxonomy_v3
            WHERE is_active = true
        """
        )
        taxonomy_results = cur.fetchall()

    conn.close()

    # Hash-based structures for O(1) lookup
    stop_words_set = set()  # Single-word stop terms
    stop_phrase_patterns = []  # Precompiled patterns/substrings for stop phrases
    single_word_aliases = defaultdict(
        set
    )  # Word -> set of centroid_ids (multiple aliases can map to same centroid)
    phrase_patterns = []  # (compiled_pattern, centroid_id) for ASCII multi-word
    phrase_substrings = []  # (substring, centroid_id) for non-ASCII multi-word
    substring_patterns = []  # (substring, centroid_id) for CJK

    for id, is_stop_word, centroid_id, aliases in taxonomy_results:
        # Build searchable terms from aliases only (item_raw/label is display-only)
        terms = set()
        if aliases:
            if isinstance(aliases, dict):
                # Language-code format
                for lang_aliases in aliases.values():
                    terms.update(normalize_text(a) for a in lang_aliases)
            elif isinstance(aliases, list):
                # Flat array format (legacy)
                terms.update(normalize_text(a) for a in aliases)

        # Handle stop words
        if is_stop_word:
            for term in terms:
                if is_common_word_false_positive(term):
                    continue

                # Single-word stop terms go into hash set
                if " " not in term and not has_substring_script_chars(term):
                    stop_words_set.add(term)
                # Multi-word or CJK stop terms need phrase/substring matching
                else:
                    if has_substring_script_chars(term):
                        stop_phrase_patterns.append(("substring", term))
                    elif is_ascii_only(term):
                        # ASCII phrase - use word boundary regex
                        pattern = re.compile(
                            r"\b" + re.escape(term) + r"\b", re.IGNORECASE
                        )
                        stop_phrase_patterns.append(("regex", pattern))
                    else:
                        # Non-ASCII (Arabic, Devanagari, etc.) - use substring
                        stop_phrase_patterns.append(("substring", term))
            continue

        # Add matching patterns for non-stop-word items
        if not centroid_id:
            continue

        for term in terms:
            # Skip common word false positives
            if is_common_word_false_positive(term):
                continue

            # CJK scripts need substring matching (can't tokenize)
            if has_substring_script_chars(term):
                substring_patterns.append((term, centroid_id))
            # Single-word aliases go into hash map
            elif " " not in term:
                single_word_aliases[term].add(centroid_id)
            # Multi-word phrases: precompile patterns based on script
            else:
                if is_ascii_only(term):
                    # ASCII phrase - use word boundary regex (precompile)
                    pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
                    phrase_patterns.append(
                        (pattern, centroid_id, term)
                    )  # Include alias
                else:
                    # Non-ASCII phrase - use substring matching
                    phrase_substrings.append((term, centroid_id))

    return {
        "stop_words_set": stop_words_set,
        "stop_phrase_patterns": stop_phrase_patterns,
        "single_word_aliases": dict(single_word_aliases),
        "phrase_patterns": phrase_patterns,
        "phrase_substrings": phrase_substrings,
        "substring_patterns": substring_patterns,
    }


def match_title(title_text, taxonomy):
    """
    Match title against taxonomy using hash-based lookup.

    Returns: (matched_centroids, matched_aliases, match_status)
    - matched_centroids: set of centroid IDs
    - matched_aliases: set of normalized alias strings that triggered matches
    - match_status: "blocked_stopword", "no_match", "matched"
    """
    normalized_title = normalize_text(title_text)

    # Step 1: Fast-fail on stop words (hash lookup O(n) where n = words in title)
    tokens = tokenize_text(normalized_title)

    # Check single-word stop terms (O(1) hash lookup per token)
    if tokens & taxonomy["stop_words_set"]:
        return set(), set(), "blocked_stopword"

    # Check multi-word/CJK stop phrases (precompiled patterns)
    for phrase_type, pattern_or_substring in taxonomy["stop_phrase_patterns"]:
        if phrase_type == "substring":
            if pattern_or_substring in normalized_title:
                return set(), set(), "blocked_stopword"
        else:  # regex (precompiled)
            if pattern_or_substring.search(normalized_title):
                return set(), set(), "blocked_stopword"

    # Step 2: Match against all patterns (hash lookup O(n))
    matched_centroids = set()
    matched_aliases = set()

    # Check single-word aliases (O(1) hash lookup per token)
    for token in tokens:
        if token in taxonomy["single_word_aliases"]:
            matched_centroids.update(taxonomy["single_word_aliases"][token])
            matched_aliases.add(token)

    # Check ASCII multi-word phrases (precompiled regex patterns)
    for pattern, centroid_id, alias_norm in taxonomy["phrase_patterns"]:
        if pattern.search(normalized_title):
            matched_centroids.add(centroid_id)
            matched_aliases.add(alias_norm)

    # Check non-ASCII multi-word phrases (substring matching)
    for substring, centroid_id in taxonomy["phrase_substrings"]:
        if substring in normalized_title:
            matched_centroids.add(centroid_id)
            matched_aliases.add(substring)

    # Check CJK substring patterns
    for substring, centroid_id in taxonomy["substring_patterns"]:
        if substring in normalized_title:
            matched_centroids.add(centroid_id)
            matched_aliases.add(substring)

    # Step 3: Canonicalize aliases and return
    if matched_centroids:
        canonical_aliases = {canonicalize_alias(a) for a in matched_aliases}
        return matched_centroids, canonical_aliases, "matched"
    else:
        return set(), set(), "no_match"


def process_batch(batch_size=100, max_titles=None):
    """Process titles with batched database updates"""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    print("Loading taxonomy...")
    taxonomy = load_taxonomy()
    print(f"  Stop words (hash): {len(taxonomy['stop_words_set'])} words")
    print(f"  Stop phrases: {len(taxonomy['stop_phrase_patterns'])} patterns")
    print(
        f"  Single-word aliases (hash): {len(taxonomy['single_word_aliases'])} entries"
    )
    print(
        f"  ASCII phrase patterns (precompiled): {len(taxonomy['phrase_patterns'])} patterns"
    )
    print(
        f"  Non-ASCII phrase substrings: {len(taxonomy['phrase_substrings'])} patterns"
    )
    print(f"  CJK substring patterns: {len(taxonomy['substring_patterns'])} patterns")

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

    # Batch updates
    matched_updates = []  # (centroid_ids, matched_aliases_json, title_id)
    out_of_scope_ids = []
    blocked_stopword_ids = []
    multi_centroid_count = 0

    for title_id, title_text in titles:
        # Match against taxonomy
        matched_centroids, matched_aliases, match_status = match_title(
            title_text, taxonomy
        )

        if match_status == "matched":
            if len(matched_centroids) > 1:
                multi_centroid_count += 1
            # Store aliases as JSON array
            aliases_json = Json(sorted(matched_aliases)) if matched_aliases else None
            matched_updates.append((list(matched_centroids), aliases_json, title_id))
        elif match_status == "blocked_stopword":
            blocked_stopword_ids.append(title_id)
        else:  # no_match
            out_of_scope_ids.append(title_id)

    # Execute batched updates
    print("\nExecuting batched database updates...")

    with conn.cursor() as cur:
        # Batch update matched titles
        if matched_updates:
            from psycopg2.extras import execute_batch

            execute_batch(
                cur,
                """
                UPDATE titles_v3
                SET centroid_ids = %s,
                    matched_aliases = %s,
                    processing_status = 'assigned',
                    updated_at = NOW()
                WHERE id = %s
                """,
                matched_updates,
                page_size=batch_size,
            )

        # Batch update out_of_scope titles
        if out_of_scope_ids:
            cur.execute(
                """
                UPDATE titles_v3
                SET processing_status = 'out_of_scope',
                    updated_at = NOW()
                WHERE id = ANY(%s::uuid[])
                """,
                (out_of_scope_ids,),
            )

        # Batch update blocked_stopword titles
        if blocked_stopword_ids:
            cur.execute(
                """
                UPDATE titles_v3
                SET processing_status = 'blocked_stopword',
                    updated_at = NOW()
                WHERE id = ANY(%s::uuid[])
                """,
                (blocked_stopword_ids,),
            )

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Total processed:        {len(titles)}")
    print(f"Matched:                {len(matched_updates)}")
    print(
        f"  - Multi-centroid:     {multi_centroid_count} ({100*multi_centroid_count//len(matched_updates) if matched_updates else 0}%)"
    )
    print(f"Blocked (stop words):   {len(blocked_stopword_ids)}")
    print(f"No match (out of scope):{len(out_of_scope_ids)}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 2: Match titles to centroids")
    parser.add_argument(
        "--max-titles", type=int, help="Maximum number of titles to process"
    )
    parser.add_argument(
        "--batch-size", type=int, default=100, help="Batch size for database updates"
    )

    args = parser.parse_args()

    process_batch(batch_size=args.batch_size, max_titles=args.max_titles)
