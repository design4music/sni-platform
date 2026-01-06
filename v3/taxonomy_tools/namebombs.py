"""
Taxonomy Tools - NameBombs Detector

Detects emerging proper names (people/orgs/places) that:
- Appear frequently in recent titles
- Leak into out-of-scope titles (not caught by taxonomy)
- Are not already in taxonomy aliases

Output: JSON reports only (no DB writes)

Usage:
    python namebombs.py --since-hours 24
    python namebombs.py --since-hours 48 --languages en,ru --top 100
"""

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from common import get_db_connection, normalize_text

# Supported languages for v1
SUPPORTED_LANGUAGES = ["en", "fr", "es", "ru"]

# Default minimum support thresholds per language
DEFAULT_MIN_TOTAL_SUPPORT = {
    "en": 5,
    "fr": 3,
    "es": 3,
    "ru": 3,
}

# Boilerplate patterns to filter out (month/day names)
BOILERPLATE_PATTERNS = {
    "en": [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    ],
    "fr": [
        "lundi",
        "mardi",
        "mercredi",
        "jeudi",
        "vendredi",
        "samedi",
        "dimanche",
        "janvier",
        "fevrier",
        "mars",
        "avril",
        "mai",
        "juin",
        "juillet",
        "aout",
        "septembre",
        "octobre",
        "novembre",
        "decembre",
    ],
    "es": [
        "lunes",
        "martes",
        "miercoles",
        "jueves",
        "viernes",
        "sabado",
        "domingo",
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ],
    "ru": [
        "понедельник",
        "вторник",
        "среда",
        "четверг",
        "пятница",
        "суббота",
        "воскресенье",
        "январь",
        "февраль",
        "март",
        "апрель",
        "май",
        "июнь",
        "июль",
        "август",
        "сентябрь",
        "октябрь",
        "ноябрь",
        "декабрь",
    ],
}


def extract_candidates(title_text, language):
    """
    Extract proper name candidates from title text.

    Returns:
        set of candidate strings (raw form, not normalized)
    """
    candidates = set()

    # Pattern 1: Multi-word TitleCase phrases (2-4 words)
    if language in ["en", "fr", "es"]:
        # Latin scripts
        titlecase_pattern = r"([A-Z][a-z]+)(\s+[A-Z][a-z]+){1,3}"
        # re.findall with groups returns tuples, reconstruct full match
        for match in re.finditer(titlecase_pattern, title_text):
            candidates.add(match.group(0))

    elif language == "ru":
        # Cyrillic scripts
        titlecase_pattern = r"([А-ЯЁ][а-яё]+)(\s+[А-ЯЁ][а-яё]+){1,3}"
        for match in re.finditer(titlecase_pattern, title_text):
            candidates.add(match.group(0))

    # Pattern 2: Acronyms (2-6 uppercase letters)
    if language in ["en", "fr", "es"]:
        acronym_pattern = r"\b[A-Z]{2,6}\b"
        candidates.update(re.findall(acronym_pattern, title_text))

    elif language == "ru":
        # Cyrillic acronyms
        acronym_pattern = r"\b[А-ЯЁ]{2,6}\b"
        candidates.update(re.findall(acronym_pattern, title_text))
        # Also allow Latin acronyms in Russian titles
        latin_acronym_pattern = r"\b[A-Z]{2,6}\b"
        candidates.update(re.findall(latin_acronym_pattern, title_text))

    return candidates


def is_valid_candidate(candidate, language, taxonomy_aliases_normalized):
    """
    Apply filters to determine if candidate is valid.

    Returns:
        True if candidate passes all filters
    """
    # Normalize using Phase 2 logic
    normalized = normalize_text(candidate)

    # Filter: length < 3 after normalization
    if len(normalized) < 3:
        return False

    # Filter: purely numeric or punctuation
    if not any(c.isalpha() for c in normalized):
        return False

    # Filter: single-word TitleCase (too noisy)
    if " " not in candidate:
        return False

    # Filter: contains month/day boilerplate
    boilerplate = BOILERPLATE_PATTERNS.get(language, [])
    normalized_lower = normalized.lower()
    for term in boilerplate:
        if term in normalized_lower:
            return False

    # Filter: already in taxonomy aliases (exact normalized match)
    if normalized in taxonomy_aliases_normalized:
        return False

    return True


def load_taxonomy_aliases(languages):
    """
    Load normalized aliases from taxonomy_v3 for specified languages.

    Returns:
        dict: {language: set of normalized aliases}
    """
    conn = get_db_connection()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT aliases
            FROM taxonomy_v3
            WHERE is_active = true
            """
        )
        taxonomy_items = cur.fetchall()

    conn.close()

    # Extract and normalize aliases per language
    aliases_by_lang = defaultdict(set)

    for (aliases,) in taxonomy_items:
        if not aliases or not isinstance(aliases, dict):
            continue

        for lang, lang_aliases in aliases.items():
            if lang not in languages:
                continue

            for alias in lang_aliases:
                normalized = normalize_text(alias)
                aliases_by_lang[lang].add(normalized)

    return dict(aliases_by_lang)


def load_titles(since_hours, languages):
    """
    Load titles from the last N hours, filtered by language.

    Returns:
        dict: {language: [(title_id, title_display, is_oos), ...]}
    """
    conn = get_db_connection()

    cutoff_time = datetime.utcnow() - timedelta(hours=since_hours)

    titles_by_lang = defaultdict(list)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, title_display, detected_language, processing_status
            FROM titles_v3
            WHERE created_at >= %s
            ORDER BY created_at DESC
            """,
            (cutoff_time,),
        )
        titles = cur.fetchall()

    conn.close()

    for title_id, title_display, detected_language, processing_status in titles:
        if detected_language not in languages:
            continue

        is_oos = processing_status == "out_of_scope"
        titles_by_lang[detected_language].append((title_id, title_display, is_oos))

    return dict(titles_by_lang)


def analyze_language(
    language, titles, taxonomy_aliases, min_total_support, min_oos_support, top_n
):
    """
    Analyze titles for one language and detect NameBombs.

    Returns:
        dict: report structure for this language
    """
    # Count support for each candidate
    candidate_support_all = defaultdict(int)
    candidate_support_oos = defaultdict(int)
    candidate_examples_all = defaultdict(list)
    candidate_examples_oos = defaultdict(list)

    # Extract candidates from all titles
    for title_id, title_display, is_oos in titles:
        candidates = extract_candidates(title_display, language)

        for candidate in candidates:
            # Apply filters
            if not is_valid_candidate(
                candidate, language, taxonomy_aliases.get(language, set())
            ):
                continue

            # Normalize for counting (count normalized form)
            normalized = normalize_text(candidate)

            # Count support
            candidate_support_all[normalized] += 1
            if len(candidate_examples_all[normalized]) < 5:
                candidate_examples_all[normalized].append(title_display)

            if is_oos:
                candidate_support_oos[normalized] += 1
                if len(candidate_examples_oos[normalized]) < 3:
                    candidate_examples_oos[normalized].append(title_display)

    # Apply inclusion rule
    qualified_candidates = []

    for normalized in candidate_support_all.keys():
        support_all = candidate_support_all[normalized]
        support_oos = candidate_support_oos.get(normalized, 0)

        # Inclusion rule
        if support_all >= min_total_support and support_oos >= min_oos_support:
            qualified_candidates.append(
                {
                    "name": normalized,
                    "support_all": support_all,
                    "support_oos": support_oos,
                    "examples_oos": candidate_examples_oos.get(normalized, []),
                    "examples_all": candidate_examples_all[normalized][:3],
                }
            )

    # Rank candidates
    qualified_candidates.sort(
        key=lambda x: (
            -x["support_all"],
            -x["support_oos"],
            -len(x["name"]),
            x["name"],
        )
    )

    # Limit to top N
    qualified_candidates = qualified_candidates[:top_n]

    # Build report
    titles_all = len(titles)
    titles_oos = sum(1 for _, _, is_oos in titles if is_oos)

    report = {
        "language": language,
        "totals": {
            "titles_all": titles_all,
            "titles_oos": titles_oos,
        },
        "candidates": qualified_candidates,
    }

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Detect emerging proper names leaking into out-of-scope titles"
    )
    parser.add_argument(
        "--since-hours",
        type=int,
        default=24,
        help="Analyze titles from the last N hours (default: 24)",
    )
    parser.add_argument(
        "--languages",
        default="en,fr,es,ru",
        help="Comma-separated language codes (default: en,fr,es,ru)",
    )
    parser.add_argument(
        "--min-oos-support",
        type=int,
        default=1,
        help="Minimum OOS occurrences required (default: 1)",
    )
    parser.add_argument(
        "--min-total-support-map",
        help="JSON map of language -> min total support (default: en:5, others:3)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=50,
        help="Maximum candidates to report per language (default: 50)",
    )
    parser.add_argument(
        "--output-dir",
        default="out/oos_reports",
        help="Output directory for reports (default: out/oos_reports)",
    )

    args = parser.parse_args()

    # Parse languages
    languages = [lang.strip() for lang in args.languages.split(",")]
    languages = [lang for lang in languages if lang in SUPPORTED_LANGUAGES]

    if not languages:
        print(f"ERROR: No valid languages specified. Supported: {SUPPORTED_LANGUAGES}")
        return

    # Parse min total support map
    if args.min_total_support_map:
        min_total_support_map = json.loads(args.min_total_support_map)
    else:
        min_total_support_map = DEFAULT_MIN_TOTAL_SUPPORT

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("NAMEBOMBS DETECTOR")
    print("=" * 60)
    print(f"Since hours: {args.since_hours}")
    print(f"Languages: {', '.join(languages)}")
    print(f"Min OOS support: {args.min_oos_support}")
    print(f"Min total support: {min_total_support_map}")
    print(f"Top N per language: {args.top}")
    print(f"Output: {output_dir}")

    # Load taxonomy aliases
    print("\nLoading taxonomy aliases...")
    taxonomy_aliases = load_taxonomy_aliases(languages)
    for lang in languages:
        alias_count = len(taxonomy_aliases.get(lang, set()))
        print(f"  {lang}: {alias_count} aliases")

    # Load titles
    print(f"\nLoading titles from last {args.since_hours} hours...")
    titles_by_lang = load_titles(args.since_hours, languages)
    for lang in languages:
        title_count = len(titles_by_lang.get(lang, []))
        print(f"  {lang}: {title_count} titles")

    if not titles_by_lang:
        print("\nNo titles found in time window. Exiting.")
        return

    # Analyze each language
    print("\nAnalyzing candidates...")
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")

    for language in languages:
        titles = titles_by_lang.get(language, [])
        if not titles:
            print(f"\n{language.upper()}: No titles, skipping")
            continue

        min_total_support = min_total_support_map.get(language, 3)

        report = analyze_language(
            language,
            titles,
            taxonomy_aliases,
            min_total_support,
            args.min_oos_support,
            args.top,
        )

        # Add run metadata
        full_report = {
            "run": {
                "since_hours": args.since_hours,
                "languages": languages,
                "min_oos_support": args.min_oos_support,
                "min_total_support_map": min_total_support_map,
                "timestamp": datetime.utcnow().isoformat(),
            },
            **report,
        }

        # Write report
        output_file = output_dir / f"namebombs_{language}_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)

        print(f"\n{language.upper()}: {len(report['candidates'])} candidates")
        print(f"  Wrote: {output_file.name}")

        # Show top 5
        if report["candidates"]:
            print("  Top candidates:")
            for candidate in report["candidates"][:5]:
                print(
                    f"    {candidate['name']} (all:{candidate['support_all']}, oos:{candidate['support_oos']})"
                )

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
