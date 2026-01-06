"""
Taxonomy Tools - OOS Keyword Candidates

Detects general keywords/noun phrases that:
- Appear frequently in English titles
- Leak into out-of-scope titles (taxonomy gaps)
- Are NOT proper names (complementary to NameBombs)

Output: JSON reports only (no DB writes)

Usage:
    python oos_keyword_candidates.py --since-hours 24
    python oos_keyword_candidates.py --since-hours 48 --min-oos-support 3 --top 50
"""

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from common import get_db_connection, normalize_text

# English stopwords + news boilerplate
STOPWORDS_EN = {
    # Common stopwords
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "as",
    "is",
    "was",
    "are",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "should",
    "could",
    "may",
    "might",
    "must",
    "can",
    "that",
    "this",
    "these",
    "those",
    "it",
    "its",
    "he",
    "she",
    "him",
    "her",
    "his",
    "their",
    "them",
    "we",
    "us",
    "our",
    "you",
    "your",
    "they",
    "what",
    "which",
    "who",
    "when",
    "where",
    "why",
    "how",
    "all",
    "each",
    "every",
    "both",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "also",
    "after",
    "before",
    "because",
    "if",
    "then",
    "about",
    "into",
    "through",
    "during",
    "above",
    "below",
    "between",
    "under",
    "again",
    "further",
    "once",
    "here",
    "there",
    "out",
    "up",
    "down",
    "off",
    "over",
    # News boilerplate
    "says",
    "said",
    "told",
    "according",
    "report",
    "reports",
    "reported",
    "announced",
    "announce",
    "news",
    "update",
    "breaking",
    "latest",
    "live",
    "video",
    "photo",
    "watch",
    "read",
    "see",
    "via",
    # Temporal/ordinal (headline boilerplate)
    "first",
    "second",
    "third",
    "fourth",
    "next",
    "last",
    "new",
    "early",
    # Generic qualifiers (headline boilerplate)
    "major",
    "big",
    "top",
    "key",
    "fresh",
    "growing",
    "urgent",
    # Scope words (headline boilerplate)
    "global",
    "international",
    "world",
    "worldwide",
    # Content type (headline boilerplate)
    "opinion",
    "analysis",
    "editorial",
    "explainer",
    "feature",
    "interview",
    # Headline glue (headline boilerplate)
    "heres",
    "here's",
    "whys",
    "hows",
    "whats",
    "whos",
    "wheres",
    # Verbs with no taxonomy value (headline boilerplate)
    "take",
    "takes",
    "make",
    "makes",
    "made",
    "get",
    "gets",
    "got",
}

# Time/date words (treated as stopwords for bigram boundaries)
TIME_BOILERPLATE = {
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
    "today",
    "yesterday",
    "tomorrow",
    "tonight",
    "week",
    "month",
    "year",
    "morning",
    "afternoon",
    "evening",
    "night",
}

# Combined stopword set for filtering
ALL_STOPWORDS = STOPWORDS_EN | TIME_BOILERPLATE


def extract_titlecase_phrases(original_title):
    """
    Extract all TitleCase phrases from original title (for proper name filtering).

    Returns:
        set of normalized TitleCase phrases
    """
    # Pattern: 2+ consecutive TitleCase words
    titlecase_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b"

    proper_phrases = set()
    for match in re.finditer(titlecase_pattern, original_title):
        phrase = match.group(0)
        normalized = normalize_text(phrase)
        proper_phrases.add(normalized)

    return proper_phrases


def tokenize_title(normalized_title):
    """
    Tokenize normalized title into words.

    Relies on normalize_text() for punctuation handling.
    Additionally removes apostrophes to handle contractions/possessives.

    Returns:
        list of tokens
    """
    # Remove apostrophes to handle contractions and possessives
    # "here's" -> "heres", "president's" -> "presidents"
    cleaned = normalized_title.replace("'", "").replace("'", "")
    return cleaned.split()


def is_valid_token(token, min_length):
    """
    Check if token is valid for inclusion.

    Filters:
    - Length >= min_length
    - Not numeric-only
    - Not stopword
    """
    if len(token) < min_length:
        return False

    if token.isdigit():
        return False

    if token in ALL_STOPWORDS:
        return False

    return True


def extract_ngrams(tokens, max_n=2):
    """
    Generate unigrams and bigrams from token list.

    Returns:
        set of n-gram strings (space-separated for bigrams)
    """
    ngrams = set()

    # Unigrams
    for token in tokens:
        ngrams.add(token)

    # Bigrams
    if max_n >= 2:
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]} {tokens[i+1]}"
            ngrams.add(bigram)

    return ngrams


def is_valid_bigram(bigram):
    """
    Check if bigram is valid (doesn't start/end with stopword or time word).
    """
    tokens = bigram.split()
    if len(tokens) != 2:
        return True  # Not a bigram, skip this check

    # Check first and last token against ALL_STOPWORDS (includes time boilerplate)
    if tokens[0] in ALL_STOPWORDS or tokens[-1] in ALL_STOPWORDS:
        return False

    return True


def load_taxonomy_aliases_en():
    """
    Load normalized English aliases from taxonomy_v3.

    Returns:
        set of normalized aliases
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

    # Extract English aliases
    aliases_en = set()

    for (aliases,) in taxonomy_items:
        if not aliases or not isinstance(aliases, dict):
            continue

        en_aliases = aliases.get("en", [])
        for alias in en_aliases:
            normalized = normalize_text(alias)
            aliases_en.add(normalized)

    return aliases_en


def load_titles_en(since_hours):
    """
    Load English titles from the last N hours.

    Returns:
        list of (title_id, title_display, is_oos)
    """
    conn = get_db_connection()

    cutoff_time = datetime.utcnow() - timedelta(hours=since_hours)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, title_display, processing_status
            FROM titles_v3
            WHERE created_at >= %s
              AND detected_language = 'en'
            ORDER BY created_at DESC
            """,
            (cutoff_time,),
        )
        titles = cur.fetchall()

    conn.close()

    # Format with OOS flag
    formatted_titles = []
    for title_id, title_display, processing_status in titles:
        is_oos = processing_status == "out_of_scope"
        formatted_titles.append((title_id, title_display, is_oos))

    return formatted_titles


def analyze_titles(
    titles,
    taxonomy_aliases,
    min_total_support,
    min_oos_support,
    ngram_max,
    min_length,
    top_n,
):
    """
    Analyze titles and extract keyword candidates.

    Returns:
        list of candidate dicts
    """
    # Count support for each candidate
    candidate_support_all = defaultdict(int)
    candidate_support_oos = defaultdict(int)
    candidate_examples_all = defaultdict(list)
    candidate_examples_oos = defaultdict(list)

    # Process all titles in single pass
    for title_id, title_display, is_oos in titles:
        # Extract TitleCase phrases once per title (for proper name filtering)
        titlecase_phrases = extract_titlecase_phrases(title_display)

        # Normalize and tokenize
        normalized = normalize_text(title_display)
        tokens = tokenize_title(normalized)

        # Filter tokens
        valid_tokens = [t for t in tokens if is_valid_token(t, min_length)]

        # Generate n-grams
        ngrams = extract_ngrams(valid_tokens, max_n=ngram_max)

        # Process each candidate
        for candidate in ngrams:
            # Filter: already in taxonomy
            if candidate in taxonomy_aliases:
                continue

            # Filter: proper name (per-title check)
            if candidate in titlecase_phrases:
                continue

            # Filter: bigram starts/ends with stopword
            if " " in candidate and not is_valid_bigram(candidate):
                continue

            # Count support (all titles)
            candidate_support_all[candidate] += 1
            if len(candidate_examples_all[candidate]) < 5:
                candidate_examples_all[candidate].append(title_display)

            # Count support (OOS titles)
            if is_oos:
                candidate_support_oos[candidate] += 1
                if len(candidate_examples_oos[candidate]) < 3:
                    candidate_examples_oos[candidate].append(title_display)

    # Apply inclusion rule
    qualified_candidates = []

    for candidate, support_all in candidate_support_all.items():
        support_oos = candidate_support_oos.get(candidate, 0)

        # Basic inclusion rule
        if support_all < min_total_support or support_oos < min_oos_support:
            continue

        is_bigram = " " in candidate

        # Prefer bigrams: only include unigrams if they have strong OOS leakage
        if not is_bigram and support_oos < 5:
            continue

        qualified_candidates.append(
            {
                "token": candidate,
                "support_all": support_all,
                "support_oos": support_oos,
                "is_bigram": is_bigram,
                "examples_oos": candidate_examples_oos.get(candidate, []),
                "examples_all": candidate_examples_all[candidate][:3],
            }
        )

    # Rank candidates
    qualified_candidates.sort(
        key=lambda x: (
            -x["support_oos"],  # OOS leakage first
            -x["support_all"],  # Then total support
            -int(x["is_bigram"]),  # Bigrams before unigrams
            x["token"],  # Alphabetical
        )
    )

    # Limit to top N
    qualified_candidates = qualified_candidates[:top_n]

    # Remove is_bigram from output (was just for sorting)
    for candidate in qualified_candidates:
        del candidate["is_bigram"]

    return qualified_candidates


def main():
    parser = argparse.ArgumentParser(
        description="Detect general keyword candidates leaking into out-of-scope"
    )
    parser.add_argument(
        "--since-hours",
        type=int,
        default=24,
        help="Analyze titles from the last N hours (default: 24)",
    )
    parser.add_argument(
        "--min-total-support",
        type=int,
        default=5,
        help="Minimum total occurrences required (default: 5)",
    )
    parser.add_argument(
        "--min-oos-support",
        type=int,
        default=2,
        help="Minimum OOS occurrences required (default: 2)",
    )
    parser.add_argument(
        "--ngram-max",
        type=int,
        default=2,
        help="Maximum n-gram size (1=unigrams only, 2=unigrams+bigrams) (default: 2)",
    )
    parser.add_argument(
        "--min-length", type=int, default=4, help="Minimum token length (default: 4)"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=100,
        help="Maximum candidates to report (default: 100)",
    )
    parser.add_argument(
        "--output-dir",
        default="out/oos_reports",
        help="Output directory for reports (default: out/oos_reports)",
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("OOS KEYWORD CANDIDATES DETECTOR")
    print("=" * 60)
    print(f"Since hours: {args.since_hours}")
    print(f"Min total support: {args.min_total_support}")
    print(f"Min OOS support: {args.min_oos_support}")
    print(f"N-gram max: {args.ngram_max}")
    print(f"Min token length: {args.min_length}")
    print(f"Top N: {args.top}")
    print(f"Output: {output_dir}")

    # Load taxonomy aliases
    print("\nLoading taxonomy aliases (EN)...")
    taxonomy_aliases = load_taxonomy_aliases_en()
    print(f"  Loaded {len(taxonomy_aliases)} English aliases")

    # Load titles
    print(f"\nLoading English titles from last {args.since_hours} hours...")
    titles = load_titles_en(args.since_hours)
    titles_all_count = len(titles)
    titles_oos_count = sum(1 for _, _, is_oos in titles if is_oos)
    print(f"  All titles: {titles_all_count}")
    print(f"  OOS titles: {titles_oos_count}")

    if not titles:
        print("\nNo English titles found in time window. Exiting.")
        return

    # Analyze
    print("\nAnalyzing keyword candidates...")
    candidates = analyze_titles(
        titles,
        taxonomy_aliases,
        args.min_total_support,
        args.min_oos_support,
        args.ngram_max,
        args.min_length,
        args.top,
    )

    print(f"  Found {len(candidates)} qualified candidates")

    # Build report
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")

    report = {
        "run": {
            "since_hours": args.since_hours,
            "language": "en",
            "min_total_support": args.min_total_support,
            "min_oos_support": args.min_oos_support,
            "ngram_max": args.ngram_max,
            "min_length": args.min_length,
            "timestamp": datetime.utcnow().isoformat(),
        },
        "totals": {
            "titles_all": titles_all_count,
            "titles_oos": titles_oos_count,
        },
        "candidates": candidates,
    }

    # Write report
    output_file = output_dir / f"oos_candidates_en_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nWrote: {output_file.name}")

    # Show top 10
    if candidates:
        print("\nTop candidates (by OOS leakage):")
        for candidate in candidates[:10]:
            token = candidate["token"]
            all_count = candidate["support_all"]
            oos_count = candidate["support_oos"]
            print(f"  {token:30s} (all:{all_count:3d}, oos:{oos_count:2d})")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
