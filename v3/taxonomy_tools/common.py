"""
Taxonomy Tools - Common Utilities

Shared normalization and matching functions extracted from Phase 2.
These functions must stay in sync with v3/phase_2/match_centroids.py
to ensure taxonomy compiler outputs match actual runtime behavior.
"""

import re
import sys
import unicodedata
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

# Supported languages
SUPPORTED_LANGUAGES = ["ar", "en", "de", "fr", "es", "ru", "zh", "ja", "hi"]


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

    This is the canonical normalization used for both titles and aliases.
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


# Aliases for spec compatibility
def normalize_title(text: str) -> str:
    """Normalize title text (alias for normalize_text)"""
    return normalize_text(text)


def normalize_alias(text: str) -> str:
    """Normalize alias text (alias for normalize_text)"""
    return normalize_text(text)


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
        if "-" in token:
            parts = token.split("-")
            for part in parts:
                if part:  # Skip empty parts
                    cleaned_tokens.add(part)

    return cleaned_tokens


def is_ascii_only(text: str) -> bool:
    """Check if text contains only ASCII letters, numbers, and spaces"""
    return all(c.isascii() and (c.isalnum() or c.isspace()) for c in text)


def has_substring_script_chars(text: str) -> bool:
    """Check if text contains CJK scripts that need substring matching"""
    return any(
        "\u4e00" <= char <= "\u9fff"  # Chinese (Han ideographs)
        or "\u3040" <= char <= "\u309f"  # Japanese Hiragana
        or "\u30a0" <= char <= "\u30ff"  # Japanese Katakana
        or "\u0e00" <= char <= "\u0e7f"  # Thai
        for char in text
    )


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


def title_matches_alias(norm_title: str, norm_alias: str) -> bool:
    """
    Check if a normalized title matches a normalized alias.

    Uses Phase 2 matching semantics:
    - Single-word aliases: token hash lookup
    - Multi-word ASCII: word boundary regex
    - Multi-word non-ASCII: substring match
    - CJK: substring match

    Args:
        norm_title: Normalized title text (output of normalize_title)
        norm_alias: Normalized alias text (output of normalize_alias)

    Returns:
        True if title matches alias, False otherwise
    """
    # CJK scripts need substring matching
    if has_substring_script_chars(norm_alias):
        return norm_alias in norm_title

    # Single-word aliases: check token presence
    if " " not in norm_alias:
        tokens = tokenize_text(norm_title)
        return norm_alias in tokens

    # Multi-word phrases
    if is_ascii_only(norm_alias):
        # ASCII phrase: use word boundary regex
        pattern = re.compile(r"\b" + re.escape(norm_alias) + r"\b", re.IGNORECASE)
        return pattern.search(norm_title) is not None
    else:
        # Non-ASCII phrase: substring match
        return norm_alias in norm_title


def get_db_connection():
    """
    Get database connection using core/config.py env vars.

    Returns:
        psycopg2 connection object
    """
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
