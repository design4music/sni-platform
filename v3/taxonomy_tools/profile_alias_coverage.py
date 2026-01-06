"""
Taxonomy Tools - Profile Alias Coverage

Measures alias effectiveness per centroid/language:
- How many titles each alias matches
- Total coverage per centroid/language
- High-overlap aliases (cross-centroid contamination)

Usage:
    python profile_alias_coverage.py --centroid-id SYS-TECH
    python profile_alias_coverage.py --language ar
    python profile_alias_coverage.py --centroid-id SYS-MEDIA --language en
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from common import (SUPPORTED_LANGUAGES, get_db_connection, normalize_alias,
                    normalize_title, title_matches_alias)


def load_titles_for_centroid(centroid_id, title_status, limit_titles):
    """
    Load titles assigned to the specified centroid.

    Returns:
        list of (title_id, title_display, normalized_title, detected_language)
    """
    conn = get_db_connection()

    with conn.cursor() as cur:
        if centroid_id:
            # Filter by specific centroid
            cur.execute(
                """
                SELECT id, title_display, detected_language
                FROM titles_v3
                WHERE processing_status = %s
                  AND %s = ANY(centroid_ids)
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (title_status, centroid_id, limit_titles),
            )
        else:
            # All assigned titles
            cur.execute(
                """
                SELECT id, title_display, detected_language
                FROM titles_v3
                WHERE processing_status = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (title_status, limit_titles),
            )

        titles = cur.fetchall()

    conn.close()

    # Normalize titles once
    normalized_titles = []
    for title_id, title_display, detected_language in titles:
        normalized_titles.append(
            (title_id, title_display, normalize_title(title_display), detected_language)
        )

    return normalized_titles


def load_aliases_for_centroid(centroid_id, language_filter):
    """
    Load active aliases for the specified centroid.

    Returns:
        dict: {language: [(alias, normalized_alias, taxonomy_id, centroid_ids), ...]}
    """
    conn = get_db_connection()

    with conn.cursor() as cur:
        if centroid_id:
            # Filter by specific centroid
            cur.execute(
                """
                SELECT id, centroid_ids, aliases
                FROM taxonomy_v3
                WHERE is_active = true
                  AND is_stop_word = false
                  AND %s = ANY(centroid_ids)
                """,
                (centroid_id,),
            )
        else:
            # All active taxonomy items
            cur.execute(
                """
                SELECT id, centroid_ids, aliases
                FROM taxonomy_v3
                WHERE is_active = true
                  AND is_stop_word = false
                """
            )

        taxonomy_items = cur.fetchall()

    conn.close()

    # Organize by language
    aliases_by_lang = defaultdict(list)

    for taxonomy_id, centroid_ids, aliases in taxonomy_items:
        if not aliases or not isinstance(aliases, dict):
            continue

        for lang, lang_aliases in aliases.items():
            # Skip languages not in filter
            if language_filter and lang not in language_filter:
                continue

            # Skip unsupported languages
            if lang not in SUPPORTED_LANGUAGES:
                continue

            for alias in lang_aliases:
                normalized = normalize_alias(alias)
                aliases_by_lang[lang].append(
                    (alias, normalized, taxonomy_id, centroid_ids)
                )

    return dict(aliases_by_lang)


def profile_centroid_language(centroid_id, language, titles, aliases, out_dir):
    """
    Profile alias coverage for a specific centroid + language combination.

    Writes:
    - centroid_<id>__lang_<lang>__alias_stats.json
    - centroid_<id>__lang_<lang>__summary.json
    """
    centroid_safe = centroid_id if centroid_id else "ALL"
    print(f"\nProfiling: {centroid_safe} / {language}")

    # Filter titles by language
    lang_titles = [
        (tid, tdisplay, tnorm)
        for tid, tdisplay, tnorm, tlang in titles
        if tlang == language
    ]

    if not lang_titles:
        print(f"  No titles found for language {language}")
        return

    print(f"  Titles: {len(lang_titles)}")
    print(f"  Aliases: {len(aliases)}")

    # Profile each alias
    alias_stats = {}
    matched_title_ids = set()  # Track overall coverage

    for alias, norm_alias, taxonomy_id, centroid_ids in aliases:
        matches = []

        # Match against all titles
        for title_id, title_display, norm_title in lang_titles:
            if title_matches_alias(norm_title, norm_alias):
                matches.append((title_id, title_display))

        if matches:
            matched_title_ids.update(tid for tid, _ in matches)

            # Store stats (limit sample to 10 titles)
            alias_stats[alias] = {
                "match_count": len(matches),
                "normalized_alias": norm_alias,
                "matched_title_ids_sample": [str(tid) for tid, _ in matches[:10]],
                "matched_titles_sample": [tdisplay for _, tdisplay in matches[:10]],
                "taxonomy_id": str(taxonomy_id),
                "centroid_ids": centroid_ids,
            }

    # Sort by match count descending
    alias_stats = dict(
        sorted(alias_stats.items(), key=lambda x: x[1]["match_count"], reverse=True)
    )

    # Summary stats
    summary = {
        "centroid_id": centroid_id,
        "language": language,
        "total_titles": len(lang_titles),
        "total_matched_titles": len(matched_title_ids),
        "coverage_ratio": (
            round(len(matched_title_ids) / len(lang_titles), 3) if lang_titles else 0
        ),
        "total_aliases": len(aliases),
        "aliases_with_matches": len(alias_stats),
        "timestamp": datetime.utcnow().isoformat(),
    }

    print(
        f"  Coverage: {summary['total_matched_titles']}/{summary['total_titles']} ({summary['coverage_ratio']:.1%})"
    )
    print(
        f"  Active aliases: {summary['aliases_with_matches']}/{summary['total_aliases']}"
    )

    # Write outputs
    alias_stats_file = (
        out_dir / f"centroid_{centroid_safe}__lang_{language}__alias_stats.json"
    )
    summary_file = out_dir / f"centroid_{centroid_safe}__lang_{language}__summary.json"

    with open(alias_stats_file, "w", encoding="utf-8") as f:
        json.dump(alias_stats, f, indent=2, ensure_ascii=False)

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"  Wrote: {alias_stats_file.name}")
    print(f"  Wrote: {summary_file.name}")


def compute_global_overlap(aliases_by_lang, titles_by_centroid, out_dir, min_matches=5):
    """
    Compute cross-centroid alias overlap (contamination detection).

    Writes:
    - global_alias_overlap.json
    """
    print("\nComputing global alias overlap...")

    # For each alias, track which centroids it matches
    alias_overlap = defaultdict(set)  # (alias, lang) -> set of centroid_ids

    for lang, aliases in aliases_by_lang.items():
        for alias, norm_alias, taxonomy_id, centroid_ids in aliases:
            # Check matches across all centroids
            for centroid_id, titles in titles_by_centroid.items():
                # Filter titles by language
                lang_titles = [
                    (tid, tdisplay, tnorm)
                    for tid, tdisplay, tnorm, tlang in titles
                    if tlang == lang
                ]

                # Count matches
                match_count = sum(
                    1
                    for tid, tdisplay, tnorm in lang_titles
                    if title_matches_alias(tnorm, norm_alias)
                )

                if match_count >= min_matches:
                    alias_overlap[(alias, lang, norm_alias)].add(centroid_id)

    # Filter to aliases matching multiple centroids
    multi_centroid_aliases = {
        (alias, lang, norm_alias): list(centroids)
        for (alias, lang, norm_alias), centroids in alias_overlap.items()
        if len(centroids) > 1
    }

    # Format output
    overlap_report = []
    for (alias, lang, norm_alias), centroids in sorted(
        multi_centroid_aliases.items(), key=lambda x: len(x[1]), reverse=True
    ):
        overlap_report.append(
            {
                "alias": alias,
                "language": lang,
                "normalized_alias": norm_alias,
                "centroid_count": len(centroids),
                "centroids": sorted(centroids),
            }
        )

    overlap_file = out_dir / "global_alias_overlap.json"
    with open(overlap_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "min_matches_threshold": min_matches,
                "total_aliases": len(overlap_report),
                "timestamp": datetime.utcnow().isoformat(),
                "aliases": overlap_report,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"  Found {len(overlap_report)} aliases matching multiple centroids")
    print(f"  Wrote: {overlap_file.name}")


def main():
    parser = argparse.ArgumentParser(
        description="Profile alias coverage per centroid/language"
    )
    parser.add_argument(
        "--centroid-id",
        help="Specific centroid ID (e.g., SYS-TECH). Omit for all centroids.",
    )
    parser.add_argument(
        "--language",
        help="Specific language code (e.g., ar, en). Omit for all languages.",
    )
    parser.add_argument(
        "--title-status",
        default="assigned",
        help="Title processing status to consider (default: assigned)",
    )
    parser.add_argument(
        "--limit-titles",
        type=int,
        default=50000,
        help="Maximum titles to load (safety limit)",
    )
    parser.add_argument(
        "--compute-overlap",
        action="store_true",
        help="Compute global alias overlap (slow for large datasets)",
    )

    args = parser.parse_args()

    # Create output directory
    out_dir = Path(__file__).parent.parent.parent / "out" / "taxonomy_profile"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("TAXONOMY ALIAS COVERAGE PROFILER")
    print("=" * 60)
    print(f"Centroid: {args.centroid_id or 'ALL'}")
    print(f"Language: {args.language or 'ALL'}")
    print(f"Title status: {args.title_status}")
    print(f"Title limit: {args.limit_titles}")
    print(f"Output: {out_dir}")

    # Load data
    print("\nLoading titles...")
    titles = load_titles_for_centroid(
        args.centroid_id, args.title_status, args.limit_titles
    )
    print(f"  Loaded {len(titles)} titles")

    if not titles:
        print("ERROR: No titles found. Check --centroid-id and --title-status.")
        return

    print("\nLoading aliases...")
    language_filter = [args.language] if args.language else SUPPORTED_LANGUAGES
    aliases_by_lang = load_aliases_for_centroid(args.centroid_id, language_filter)
    total_aliases = sum(len(aliases) for aliases in aliases_by_lang.values())
    print(f"  Loaded {total_aliases} aliases across {len(aliases_by_lang)} languages")

    if not aliases_by_lang:
        print("ERROR: No aliases found. Check --centroid-id and --language.")
        return

    # Profile each language
    for language, aliases in aliases_by_lang.items():
        profile_centroid_language(args.centroid_id, language, titles, aliases, out_dir)

    # Optional: compute global overlap
    if args.compute_overlap:
        # Need to load titles grouped by centroid
        print("\nLoading all centroids for overlap analysis...")
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT id FROM centroids_v3 WHERE is_active = true")
            centroid_ids = [row[0] for row in cur.fetchall()]
        conn.close()

        titles_by_centroid = {}
        for cid in centroid_ids:
            titles_by_centroid[cid] = load_titles_for_centroid(
                cid, args.title_status, args.limit_titles
            )

        compute_global_overlap(aliases_by_lang, titles_by_centroid, out_dir)

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
