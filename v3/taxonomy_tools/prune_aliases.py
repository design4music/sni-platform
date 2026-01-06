"""
Taxonomy Tools - Prune Redundant Aliases (Static Subsumption)

Deterministic pruning based on STATIC alias subsumption analysis.
An alias is redundant if another alias will ALWAYS match everything it matches.

Key principle: Taxonomy exists as "high probability catchers" for future ingestion.
Never prune based on zero current matches - only prune logical redundancy.

Subsumption rule:
- Alias A subsumes alias B if tokens(A) ⊆ tokens(B) and A != B
- Example: "AI" subsumes "AI infrastructure" (ai ⊂ {ai, infrastructure})
- Example: "ceasefire" subsumes "temporary ceasefire"

Pruning scope:
- Within (centroid_id, language) groups only
- Never prune across different centroids
- Each centroid maintains independent alias sets

Safety rules:
- Dry-run by default
- Abort if removal count exceeds safety threshold
- Keep at least N aliases per group (default: 1)

Usage:
    python prune_aliases.py --centroid-id SYS-MEDIA --mode dry-run
    python prune_aliases.py --language ar --mode apply
    python prune_aliases.py --mode apply  # All centroids, all languages
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from common import (SUPPORTED_LANGUAGES, get_db_connection, normalize_alias,
                    tokenize_text)


def load_aliases_grouped(centroid_filter=None, language_filter=None):
    """
    Load aliases grouped by (centroid_id, language).

    Returns:
        dict: {(centroid_id, language): [(alias, normalized, tokens, taxonomy_id), ...]}
    """
    conn = get_db_connection()

    with conn.cursor() as cur:
        if centroid_filter:
            cur.execute(
                """
                SELECT id, centroid_ids, aliases
                FROM taxonomy_v3
                WHERE is_active = true
                  AND is_stop_word = false
                  AND %s = ANY(centroid_ids)
                """,
                (centroid_filter,),
            )
        else:
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

    # Group by (centroid_id, language)
    grouped = defaultdict(list)

    for taxonomy_id, centroid_ids, aliases in taxonomy_items:
        if not aliases or not isinstance(aliases, dict):
            continue

        # Expand to all centroids this item belongs to
        for centroid_id in centroid_ids or []:
            for lang, lang_aliases in aliases.items():
                # Filter by language
                if language_filter and lang not in language_filter:
                    continue

                if lang not in SUPPORTED_LANGUAGES:
                    continue

                # Add each alias with its normalized form and tokens
                for alias in lang_aliases:
                    normalized = normalize_alias(alias)
                    tokens = tokenize_text(normalized)
                    grouped[(centroid_id, lang)].append(
                        (alias, normalized, tokens, taxonomy_id)
                    )

    return dict(grouped)


def is_subsumed_by(alias_a_tokens, alias_b_tokens):
    """
    Check if alias A subsumes alias B.

    Returns True if:
    - All tokens of A are in B
    - A has fewer tokens than B (proper subset)

    This means A will ALWAYS match everything B matches.

    Examples:
    - is_subsumed_by({ai}, {ai, infrastructure}) → True
    - is_subsumed_by({ceasefire}, {temporary, ceasefire}) → True
    - is_subsumed_by({human, rights}, {human, rights, violations}) → True
    - is_subsumed_by({ai}, {ai}) → False (same, not proper subset)
    """
    return alias_a_tokens < alias_b_tokens  # Proper subset check


def find_subsumed_aliases(aliases, min_keep=1):
    """
    Find aliases that are subsumed by other aliases in the same group.

    Algorithm:
    1. Sort aliases by token count ascending (check shorter ones first)
    2. For each alias B, check if any shorter alias A subsumes it
    3. Mark B as redundant if subsumed

    Returns:
        (kept_aliases, subsumed_aliases)
    """
    # Sort by token count ascending, then by alias length
    sorted_aliases = sorted(aliases, key=lambda x: (len(x[2]), len(x[0])))

    kept = []
    subsumed = []

    for alias, normalized, tokens, taxonomy_id in sorted_aliases:
        # Check if this alias is subsumed by any kept alias
        is_redundant = False
        subsumed_by = None

        for kept_alias, kept_normalized, kept_tokens, kept_taxonomy_id in kept:
            if is_subsumed_by(kept_tokens, tokens):
                is_redundant = True
                subsumed_by = kept_alias
                break

        if is_redundant:
            subsumed.append((alias, normalized, tokens, taxonomy_id, subsumed_by))
        else:
            kept.append((alias, normalized, tokens, taxonomy_id))

    # Enforce min_keep constraint
    if len(kept) < min_keep and subsumed:
        # Move subsumed back to kept until min_keep satisfied
        while len(kept) < min_keep and subsumed:
            alias, normalized, tokens, taxonomy_id, _ = subsumed.pop(0)
            kept.append((alias, normalized, tokens, taxonomy_id))

    return kept, subsumed


def apply_pruning(removals, dry_run=True):
    """
    Apply pruning by removing alias strings from taxonomy_v3.aliases[lang].

    Args:
        removals: list of (language, alias, taxonomy_id)
        dry_run: if True, only simulate changes
    """
    if dry_run:
        print("\n  DRY-RUN MODE: No database changes will be made.")
        return

    conn = get_db_connection()

    # Group removals by taxonomy_id
    removals_by_id = defaultdict(list)
    for language, alias, taxonomy_id in removals:
        removals_by_id[taxonomy_id].append((language, alias))

    updated_count = 0
    deactivated_count = 0

    with conn.cursor() as cur:
        for taxonomy_id, removals_list in removals_by_id.items():
            # Load current aliases
            cur.execute("SELECT aliases FROM taxonomy_v3 WHERE id = %s", (taxonomy_id,))
            result = cur.fetchone()
            if not result:
                continue

            current_aliases = result[0] or {}

            # Remove specified aliases per language
            for language, alias in removals_list:
                if language in current_aliases:
                    if alias in current_aliases[language]:
                        current_aliases[language].remove(alias)
                    # Remove language key if empty
                    if not current_aliases[language]:
                        del current_aliases[language]

            # Check if item is now alias-less
            if not current_aliases:
                # Set is_active=false
                cur.execute(
                    """
                    UPDATE taxonomy_v3
                    SET aliases = %s,
                        is_active = false,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (json.dumps(current_aliases), taxonomy_id),
                )
                deactivated_count += 1
            else:
                # Update aliases only
                cur.execute(
                    """
                    UPDATE taxonomy_v3
                    SET aliases = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (json.dumps(current_aliases), taxonomy_id),
                )
                updated_count += 1

    conn.commit()
    conn.close()

    print(
        f"\n  APPLIED: Updated {updated_count} items, deactivated {deactivated_count} items."
    )


def prune_group(centroid_id, language, aliases, min_keep, safety_max_remove):
    """
    Prune aliases for a specific (centroid_id, language) group.

    Returns:
        (report_dict, removals_list) or None if aborted
    """
    print(f"\nAnalyzing: {centroid_id} / {language}")
    print(f"  Aliases: {len(aliases)}")

    if not aliases:
        print("  No aliases to analyze")
        return None

    # Find subsumed aliases
    kept, subsumed = find_subsumed_aliases(aliases, min_keep)

    print(f"  Kept: {len(kept)}")
    print(f"  Subsumed (redundant): {len(subsumed)}")

    # Safety check: max removal limit
    if len(subsumed) > safety_max_remove:
        print(
            f"\n  ERROR: Would remove {len(subsumed)} aliases (exceeds safety limit {safety_max_remove})."
        )
        print("  Aborting pruning for this group.")
        return None

    # Show examples of subsumed aliases (ASCII-safe output)
    if subsumed:
        print("\n  Examples of redundant aliases:")
        for alias, normalized, tokens, taxonomy_id, subsumed_by in subsumed[:5]:
            # Use normalized forms (ASCII-safe) for console output
            print(
                f"    {len(tokens)} tokens subsumed by {len(tokenize_text(normalize_alias(subsumed_by)))} tokens"
            )
        if len(subsumed) > 5:
            print(f"    ... and {len(subsumed) - 5} more")

    # Build report
    report = {
        "centroid_id": centroid_id,
        "language": language,
        "aliases_before_count": len(aliases),
        "aliases_after_count": len(kept),
        "removed_count": len(subsumed),
        "kept_aliases": [
            {
                "alias": alias,
                "normalized": normalized,
                "tokens": list(tokens),
                "taxonomy_id": str(taxonomy_id),
            }
            for alias, normalized, tokens, taxonomy_id in kept
        ],
        "subsumed_aliases": [
            {
                "alias": alias,
                "normalized": normalized,
                "tokens": list(tokens),
                "taxonomy_id": str(taxonomy_id),
                "subsumed_by": subsumed_by,
                "reason": "tokens_subset",
            }
            for alias, normalized, tokens, taxonomy_id, subsumed_by in subsumed
        ],
        "timestamp": datetime.now().isoformat(),
    }

    return report, subsumed


def main():
    parser = argparse.ArgumentParser(
        description="Prune redundant aliases using static subsumption analysis"
    )
    parser.add_argument(
        "--centroid-id",
        help="Specific centroid ID (e.g., SYS-MEDIA). Omit for all centroids.",
    )
    parser.add_argument(
        "--language",
        help="Specific language code (e.g., ar, en). Omit for all languages.",
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "apply"],
        default="dry-run",
        help="Execution mode (default: dry-run)",
    )
    parser.add_argument(
        "--min-keep",
        type=int,
        default=1,
        help="Minimum aliases to keep per centroid+language (default: 1)",
    )
    parser.add_argument(
        "--safety-max-remove",
        type=int,
        default=2000,
        help="Abort if more than N aliases would be removed from one group (default: 2000)",
    )

    args = parser.parse_args()

    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(__file__).parent.parent.parent / "out" / "taxonomy_prune" / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("TAXONOMY ALIAS PRUNING TOOL (Static Subsumption)")
    print("=" * 60)
    print(f"Centroid: {args.centroid_id or 'ALL'}")
    print(f"Language: {args.language or 'ALL'}")
    print(f"Mode: {args.mode}")
    print(f"Min keep: {args.min_keep}")
    print(f"Safety max remove: {args.safety_max_remove}")
    print(f"Output: {out_dir}")

    # Load aliases grouped by (centroid_id, language)
    print("\nLoading aliases...")
    language_filter = [args.language] if args.language else SUPPORTED_LANGUAGES
    grouped_aliases = load_aliases_grouped(args.centroid_id, language_filter)

    total_aliases = sum(len(aliases) for aliases in grouped_aliases.values())
    print(f"  Loaded {total_aliases} aliases across {len(grouped_aliases)} groups")

    if not grouped_aliases:
        print("ERROR: No aliases found.")
        return

    # Analyze each group
    all_reports = []
    all_removals = []  # (language, alias, taxonomy_id)

    for (centroid_id, language), aliases in sorted(grouped_aliases.items()):
        result = prune_group(
            centroid_id, language, aliases, args.min_keep, args.safety_max_remove
        )

        if result:
            report, subsumed = result
            all_reports.append(report)

            # Track removals for database update
            for alias, normalized, tokens, taxonomy_id, subsumed_by in subsumed:
                all_removals.append((language, alias, taxonomy_id))

    # Write consolidated report
    prune_report_file = out_dir / "prune_report.json"
    with open(prune_report_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "method": "static_subsumption",
                "centroid_filter": args.centroid_id,
                "language_filter": args.language,
                "mode": args.mode,
                "timestamp": datetime.now().isoformat(),
                "total_groups": len(all_reports),
                "total_removed": sum(r["removed_count"] for r in all_reports),
                "total_kept": sum(r["aliases_after_count"] for r in all_reports),
                "group_reports": all_reports,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\n  Wrote: {prune_report_file.name}")

    # Summary stats
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Groups analyzed: {len(all_reports)}")
    print(
        f"Total aliases before: {sum(r['aliases_before_count'] for r in all_reports)}"
    )
    print(f"Total aliases after: {sum(r['aliases_after_count'] for r in all_reports)}")
    print(f"Total removed: {len(all_removals)}")

    # Apply pruning if mode=apply
    if args.mode == "apply" and all_removals:
        print(f"\nApplying pruning ({len(all_removals)} total removals)...")
        apply_pruning(all_removals, dry_run=False)

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
