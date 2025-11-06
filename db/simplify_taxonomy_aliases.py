"""
Simplify taxonomy aliases by removing redundancies.

Rules:
1. Remove identical transliterations across languages (keep in 'en' only)
2. Remove redundant formal names unless commonly used
3. Flag partial name duplicates for review
4. Always keep non-Latin scripts (Chinese, Arabic, Cyrillic, etc.)
5. Only keep language-specific variants when actually different

Example transformations:
- "Putin" in en/es/de/it/fr → keep only in 'en'
- "China" + "People's Republic of China" → keep only "China"
- Keep "中国" (Chinese) and "Путин" (Cyrillic)
"""

import re
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def has_non_latin_script(text: str) -> bool:
    """Check if text contains non-Latin scripts (CJK, Cyrillic, Arabic, etc.)"""
    return any(
        "\u0400" <= char <= "\u04ff"  # Cyrillic
        or "\u4e00" <= char <= "\u9fff"  # Chinese (Han)
        or "\u3040" <= char <= "\u309f"  # Japanese Hiragana
        or "\u30a0" <= char <= "\u30ff"  # Japanese Katakana
        or "\u0600" <= char <= "\u06ff"  # Arabic
        or "\u0750" <= char <= "\u077f"  # Arabic Supplement
        or "\u0e00" <= char <= "\u0e7f"  # Thai
        or "\u0590" <= char <= "\u05ff"  # Hebrew
        for char in text
    )


def normalize_for_comparison(text: str) -> str:
    """Normalize text for duplicate detection (case-insensitive, no punctuation)"""
    # Remove punctuation and whitespace, lowercase
    return re.sub(r"[^\w]", "", text.lower())


def is_formal_name_redundant(formal: str, short: str) -> bool:
    """
    Check if formal name is redundant with short form.
    E.g., "People's Republic of China" is redundant with "China"
    """
    # If formal name just adds descriptor words, it's likely redundant
    formal_words = set(formal.lower().split())
    short_words = set(short.lower().split())

    # If short form is contained in formal name
    if short_words.issubset(formal_words):
        # And formal adds common descriptor words
        descriptors = {
            "republic",
            "democratic",
            "peoples",
            "people's",
            "federal",
            "kingdom",
            "united",
            "islamic",
        }
        added_words = formal_words - short_words
        if added_words.issubset(descriptors):
            return True

    return False


def simplify_aliases(item_raw: str, aliases: dict) -> tuple[dict, list]:
    """
    Simplify aliases by removing redundancies.

    Returns:
        (cleaned_aliases, warnings)
    """
    if not aliases:
        return {}, []

    warnings = []
    cleaned = {}

    # Step 1: Group identical normalized aliases across languages
    normalized_to_langs = {}  # normalized_text -> {lang: [original_texts]}

    for lang, alias_list in aliases.items():
        for alias in alias_list:
            normalized = normalize_for_comparison(alias)
            if normalized not in normalized_to_langs:
                normalized_to_langs[normalized] = {}
            if lang not in normalized_to_langs[normalized]:
                normalized_to_langs[normalized][lang] = []
            normalized_to_langs[normalized][lang].append(alias)

    # Step 2: For each group, decide which languages to keep
    for normalized, lang_map in normalized_to_langs.items():
        # Check if any version has non-Latin script
        has_non_latin = any(
            has_non_latin_script(alias)
            for aliases_in_lang in lang_map.values()
            for alias in aliases_in_lang
        )

        if has_non_latin:
            # Keep all non-Latin versions, plus one Latin version
            for lang, alias_list in lang_map.items():
                for alias in alias_list:
                    if has_non_latin_script(alias):
                        if lang not in cleaned:
                            cleaned[lang] = []
                        cleaned[lang].append(alias)

            # Keep one Latin version (prefer English)
            if "en" in lang_map:
                latin_versions = [
                    a for a in lang_map["en"] if not has_non_latin_script(a)
                ]
                if latin_versions and "en" not in cleaned:
                    cleaned["en"] = []
                cleaned["en"].extend(latin_versions)

        else:
            # All Latin script - keep only in English (or first language found)
            if "en" in lang_map:
                if "en" not in cleaned:
                    cleaned["en"] = []
                cleaned["en"].extend(lang_map["en"])
            else:
                # No English version, keep in first language found
                first_lang = sorted(lang_map.keys())[0]
                if first_lang not in cleaned:
                    cleaned[first_lang] = []
                cleaned[first_lang].extend(lang_map[first_lang])

    # Step 3: Remove redundant formal names
    if "en" in cleaned:
        non_redundant = []
        item_raw_normalized = normalize_for_comparison(item_raw)

        for alias in cleaned["en"]:
            alias_normalized = normalize_for_comparison(alias)

            # Skip if identical to item_raw
            if alias_normalized == item_raw_normalized:
                warnings.append(f"Removed duplicate of item_raw: '{alias}'")
                continue

            # Check if it's a redundant formal name
            if is_formal_name_redundant(alias, item_raw):
                warnings.append(f"Removed redundant formal name: '{alias}'")
                continue

            non_redundant.append(alias)

        if non_redundant:
            cleaned["en"] = non_redundant
        else:
            # All English aliases were redundant
            del cleaned["en"]

    # Step 4: Remove empty language entries
    cleaned = {lang: aliases for lang, aliases in cleaned.items() if aliases}

    return cleaned, warnings


def simplify_taxonomy():
    """Simplify all taxonomy aliases"""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            # Get all items with aliases
            cur.execute(
                """
                SELECT id, item_raw, item_type, aliases
                FROM taxonomy_v3
                WHERE aliases IS NOT NULL
                  AND aliases != '{}'::jsonb
                ORDER BY item_raw
            """
            )
            items = cur.fetchall()

        print(f"Processing {len(items)} taxonomy items...\n")

        updated_count = 0
        total_aliases_before = 0
        total_aliases_after = 0
        all_warnings = []

        for id, item_raw, item_type, aliases in items:
            # Count before
            before_count = sum(len(v) for v in aliases.values())
            total_aliases_before += before_count

            # Simplify
            cleaned, warnings = simplify_aliases(item_raw, aliases)

            # Count after
            after_count = sum(len(v) for v in cleaned.values())
            total_aliases_after += after_count

            if cleaned != aliases:
                # Update database
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE taxonomy_v3
                        SET aliases = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """,
                        (Json(cleaned), id),
                    )

                updated_count += 1

                # Print changes
                if warnings:
                    try:
                        print(f"\n{item_raw} ({item_type}):")
                        print(f"  Before: {before_count} aliases")
                        print(f"  After: {after_count} aliases")
                        for warning in warnings:
                            print(f"  • {warning}")
                        all_warnings.extend(warnings)
                    except UnicodeEncodeError:
                        # Skip printing if Unicode issues
                        pass

        conn.commit()

        # Summary
        print(f"\n{'='*70}")
        print("SIMPLIFICATION COMPLETE")
        print(f"{'='*70}")
        print(f"Items processed:      {len(items)}")
        print(f"Items updated:        {updated_count}")
        print(f"Total aliases before: {total_aliases_before}")
        print(f"Total aliases after:  {total_aliases_after}")
        print(
            f"Aliases removed:      {total_aliases_before - total_aliases_after} ({100 * (total_aliases_before - total_aliases_after) / total_aliases_before:.1f}%)"
        )
        print(f"Total changes:        {len(all_warnings)}")

    except Exception as e:
        print(f"Simplification failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    simplify_taxonomy()
