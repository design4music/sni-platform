"""
Geo Pre-Clustering for Phase 4 Event Extraction

Mechanically routes titles into coherent buckets based on centroid overlap:
- Bilateral: titles mentioning exactly 1 other geo centroid
- Multilateral: titles mentioning 2+ other geo centroids
- Domestic: titles mentioning only the main centroid (no other geo)

This gives LLM coherent slices to work with instead of random batches.
"""

import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import config  # noqa: E402


@dataclass
class BucketSubgroups:
    """Alias-based sub-groups within a bucket."""

    by_alias: dict[str, list[str]]  # {alias: [title_ids]} - top 15 aliases
    untagged: list[str]  # Titles not in top 15 alias groups


@dataclass
class PreclusterResult:
    """Result of pre-clustering titles for a geo CTM."""

    ctm_id: str
    main_centroid: str
    bilaterals: dict[str, list[str]]  # {counterparty: [title_ids]} - top 15 only
    bilateral_subgroups: dict[str, BucketSubgroups]  # {counterparty: subgroups}
    other_international: list[str]  # [title_ids] - titles outside top 15
    other_intl_subgroups: BucketSubgroups  # Alias sub-groups for other_intl
    domestic: list[str]  # [title_ids]
    domestic_subgroups: BucketSubgroups  # Alias sub-groups for domestic
    top_bilaterals: list[str]  # Top 15 counterparties by title count

    def summary(self) -> str:
        """Return a summary string."""
        lines = [
            f"Pre-cluster for {self.main_centroid}:",
            f"  Bilateral buckets (top 15): {len(self.bilaterals)}",
        ]
        for cp in self.top_bilaterals:
            subgroups = self.bilateral_subgroups.get(cp)
            alias_count = len(subgroups.by_alias) if subgroups else 0
            untagged = len(subgroups.untagged) if subgroups else 0
            lines.append(
                f"    - {cp}: {len(self.bilaterals[cp])} titles ({alias_count} alias groups, {untagged} untagged)"
            )

        lines.append(f"  Other International: {len(self.other_international)} titles")
        if self.other_intl_subgroups:
            lines.append(
                f"    ({len(self.other_intl_subgroups.by_alias)} alias groups, {len(self.other_intl_subgroups.untagged)} untagged)"
            )

        lines.append(f"  Domestic: {len(self.domestic)} titles")
        if self.domestic_subgroups:
            lines.append(
                f"    ({len(self.domestic_subgroups.by_alias)} alias groups, {len(self.domestic_subgroups.untagged)} untagged)"
            )

        return "\n".join(lines)


def _compute_alias_subgroups(
    title_ids: list[str],
    title_aliases: dict[str, list[str]],
    max_alias_groups: int = 15,
) -> BucketSubgroups:
    """
    Compute alias-based sub-groups for a list of titles.

    Groups titles by their matched aliases, keeping top N by count.
    Titles with multiple aliases go to the largest matching group.
    """
    # Count titles per alias
    alias_counts: dict[str, int] = Counter()
    for tid in title_ids:
        aliases = title_aliases.get(tid, [])
        for alias in aliases:
            alias_counts[alias] += 1

    # Get top N aliases
    top_aliases = [alias for alias, _ in alias_counts.most_common(max_alias_groups)]
    top_alias_set = set(top_aliases)

    # Group titles by their best alias (largest group they belong to)
    by_alias: dict[str, list[str]] = {alias: [] for alias in top_aliases}
    untagged: list[str] = []

    for tid in title_ids:
        aliases = title_aliases.get(tid, [])
        # Find the best alias (one in top N with highest count)
        best_alias = None
        best_count = 0
        for alias in aliases:
            if alias in top_alias_set and alias_counts[alias] > best_count:
                best_alias = alias
                best_count = alias_counts[alias]

        if best_alias:
            by_alias[best_alias].append(tid)
        else:
            untagged.append(tid)

    # Remove empty alias groups
    by_alias = {k: v for k, v in by_alias.items() if v}

    return BucketSubgroups(by_alias=by_alias, untagged=untagged)


def precluster_geo_ctm(
    ctm_id: str,
    max_bilaterals: int = 15,
    conn=None,
) -> PreclusterResult:
    """
    Pre-cluster titles for a geo CTM based on FIRST other geo centroid mentioned.

    Routing logic:
    1. For each title, find the FIRST other geo centroid in centroid_ids
    2. Count titles per first-mentioned counterparty
    3. Top 15 by count become bilateral buckets (no minimum threshold)
    4. Titles whose first counterparty is NOT in top 15 -> "Other International"
    5. Titles with no other geo centroids -> "Domestic"
    6. Within each bucket, sub-group by FIRST systemic centroid

    Args:
        ctm_id: CTM UUID
        max_bilaterals: Maximum number of bilateral buckets (top N)
        conn: Optional DB connection (creates one if not provided)

    Returns:
        PreclusterResult with routing and alias-based sub-grouping
    """
    close_conn = False
    if conn is None:
        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
        )
        close_conn = True

    try:
        with conn.cursor() as cur:
            # Get main centroid for this CTM
            cur.execute(
                """
                SELECT centroid_id FROM ctm WHERE id = %s
                """,
                (ctm_id,),
            )
            main_centroid = cur.fetchone()[0]

            # Get all geo centroids
            cur.execute(
                """
                SELECT id FROM centroids_v3
                WHERE class = 'geo' AND is_active = true
                """
            )
            geo_centroids = {row[0] for row in cur.fetchall()}

            # Get all titles for this CTM with their centroid_ids and matched_aliases
            cur.execute(
                """
                SELECT ta.title_id, t.centroid_ids, t.matched_aliases
                FROM title_assignments ta
                JOIN titles_v3 t ON ta.title_id = t.id
                WHERE ta.ctm_id = %s
                """,
                (ctm_id,),
            )

            # Store all title aliases for sub-grouping later
            title_aliases: dict[str, list[str]] = {}

            # First pass: count titles per FIRST other geo centroid
            first_counterparty_counts: dict[str, int] = Counter()
            title_first_counterparty: dict[str, str | None] = {}
            domestic: list[str] = []

            for title_id, centroid_ids, matched_aliases in cur.fetchall():
                title_id_str = str(title_id)
                title_aliases[title_id_str] = matched_aliases or []

                if centroid_ids is None:
                    domestic.append(title_id_str)
                    title_first_counterparty[title_id_str] = None
                    continue

                # Find FIRST other geo centroid (order preserved from centroid_ids)
                first_other_geo = None
                for c in centroid_ids:
                    if c in geo_centroids and c != main_centroid:
                        first_other_geo = c
                        break

                if first_other_geo is None:
                    # Domestic: no other geo centroids
                    domestic.append(title_id_str)
                    title_first_counterparty[title_id_str] = None
                else:
                    # International: has at least one other geo centroid
                    first_counterparty_counts[first_other_geo] += 1
                    title_first_counterparty[title_id_str] = first_other_geo

            # Determine top 15 counterparties by count (no minimum threshold)
            sorted_counterparties = sorted(
                first_counterparty_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )
            top_bilaterals = [cp for cp, _ in sorted_counterparties[:max_bilaterals]]
            top_bilateral_set = set(top_bilaterals)

            # Second pass: route titles to bilateral or other_international
            bilaterals: dict[str, list[str]] = {cp: [] for cp in top_bilaterals}
            other_international: list[str] = []

            for title_id_str, first_cp in title_first_counterparty.items():
                if first_cp is None:
                    continue  # Already in domestic
                elif first_cp in top_bilateral_set:
                    bilaterals[first_cp].append(title_id_str)
                else:
                    other_international.append(title_id_str)

            # Compute alias-based sub-groups for each bucket
            bilateral_subgroups = {
                cp: _compute_alias_subgroups(titles, title_aliases)
                for cp, titles in bilaterals.items()
            }

            other_intl_subgroups = _compute_alias_subgroups(
                other_international, title_aliases
            )

            domestic_subgroups = _compute_alias_subgroups(domestic, title_aliases)

            return PreclusterResult(
                ctm_id=ctm_id,
                main_centroid=main_centroid,
                bilaterals=bilaterals,
                bilateral_subgroups=bilateral_subgroups,
                other_international=other_international,
                other_intl_subgroups=other_intl_subgroups,
                domestic=domestic,
                domestic_subgroups=domestic_subgroups,
                top_bilaterals=top_bilaterals,
            )

    finally:
        if close_conn:
            conn.close()


def get_bucket_titles(
    ctm_id: str,
    bucket_type: str,
    bucket_key: str = None,
    conn=None,
) -> list[tuple]:
    """
    Get full title data for a specific bucket.

    Args:
        ctm_id: CTM UUID
        bucket_type: 'bilateral', 'other_international', or 'domestic'
        bucket_key: For bilateral, the counterparty centroid ID
        conn: Optional DB connection

    Returns:
        List of (title_id, title_display, pubdate_utc) tuples
    """
    close_conn = False
    if conn is None:
        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
        )
        close_conn = True

    try:
        # First get the pre-cluster result
        result = precluster_geo_ctm(ctm_id, conn=conn)

        # Get the title IDs for this bucket
        if bucket_type == "bilateral":
            if bucket_key not in result.bilaterals:
                return []
            title_ids = result.bilaterals[bucket_key]
        elif bucket_type == "other_international":
            title_ids = result.other_international
        elif bucket_type == "domestic":
            title_ids = result.domestic
        else:
            raise ValueError(f"Unknown bucket type: {bucket_type}")

        if not title_ids:
            return []

        # Fetch full title data
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title_display, pubdate_utc
                FROM titles_v3
                WHERE id = ANY(%s)
                ORDER BY pubdate_utc ASC
                """,
                (title_ids,),
            )
            return cur.fetchall()

    finally:
        if close_conn:
            conn.close()


if __name__ == "__main__":
    # Test with USA geo_economy
    import argparse

    parser = argparse.ArgumentParser(description="Test geo pre-clustering")
    parser.add_argument("--ctm-id", help="CTM UUID to test")
    parser.add_argument("--centroid", default="AMERICAS-USA", help="Centroid ID")
    parser.add_argument("--track", default="geo_economy", help="Track")

    args = parser.parse_args()

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        if args.ctm_id:
            ctm_id = args.ctm_id
        else:
            # Find CTM by centroid and track
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id FROM ctm
                    WHERE centroid_id = %s AND track = %s
                    ORDER BY month DESC LIMIT 1
                    """,
                    (args.centroid, args.track),
                )
                row = cur.fetchone()
                if not row:
                    print(f"No CTM found for {args.centroid}/{args.track}")
                    sys.exit(1)
                ctm_id = row[0]

        result = precluster_geo_ctm(ctm_id, conn=conn)
        print(result.summary())

        # Total coverage check
        total = (
            sum(len(t) for t in result.bilaterals.values())
            + len(result.multilateral)
            + len(result.domestic)
        )
        print(f"\nTotal titles routed: {total}")

    finally:
        conn.close()
