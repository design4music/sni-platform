"""
Phase 4: Topic Clustering

Clusters titles into Topics using typed signals and co-occurrence matrix.

Topics are merge-biased storylines (1-2000 titles) that persist beyond CTM boundaries.
Co-occurrence is computed in-memory using weighted signal pairs.

Usage:
    python pipeline/phase_4/cluster_topics.py --ctm-id <ctm_id>
    python pipeline/phase_4/cluster_topics.py --centroid AMERICAS-USA --track geo_economy
"""

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2
from loguru import logger

from core.config import (
    SIGNAL_TYPES,
    config,
    get_track_discriminators,
    get_track_weights,
)
from core.ontology import GEO_ALIAS_TO_ISO
from core.publisher_filter import filter_publisher_signals, load_publisher_patterns

# =============================================================================
# DATABASE OPERATIONS
# =============================================================================


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def load_titles_with_signals(conn, ctm_id: str) -> list:
    """Load titles with their signals for clustering."""
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            t.id,
            t.title_display,
            t.pubdate_utc,
            tl.actor,
            tl.action_class,
            tl.domain,
            tl.target,
            tl.persons,
            tl.orgs,
            tl.places,
            tl.commodities,
            tl.policies,
            tl.systems,
            tl.named_events
        FROM titles_v3 t
        JOIN title_assignments ta ON t.id = ta.title_id
        JOIN title_labels tl ON t.id = tl.title_id
        WHERE ta.ctm_id = %s
          AND (tl.persons IS NOT NULL OR tl.orgs IS NOT NULL OR tl.places IS NOT NULL
               OR tl.commodities IS NOT NULL OR tl.policies IS NOT NULL
               OR tl.systems IS NOT NULL OR tl.named_events IS NOT NULL)
        ORDER BY t.pubdate_utc DESC
        """,
        (ctm_id,),
    )

    rows = cur.fetchall()
    titles = []

    for r in rows:
        titles.append(
            {
                "id": str(r[0]),
                "title_display": r[1],
                "pubdate_utc": r[2],
                "actor": r[3],
                "action_class": r[4],
                "domain": r[5],
                "target": r[6],
                "persons": r[7] or [],
                "orgs": r[8] or [],
                "places": r[9] or [],
                "commodities": r[10] or [],
                "policies": r[11] or [],
                "systems": r[12] or [],
                "named_events": r[13] or [],
            }
        )

    return titles


def filter_titles_publisher_signals(titles: list, publisher_patterns: set) -> int:
    """Filter publisher names from orgs in all titles. Modifies in place.

    Returns: count of filtered signals
    """
    filtered_count = 0
    for title in titles:
        orgs = title.get("orgs", [])
        if orgs:
            filtered = filter_publisher_signals(orgs, publisher_patterns)
            filtered_count += len(orgs) - len(filtered)
            title["orgs"] = filtered
    return filtered_count


def get_ctm_info(conn, ctm_id: str) -> dict:
    """Get CTM metadata."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT c.id, c.centroid_id, c.track, c.month
        FROM ctm c
        WHERE c.id = %s
        """,
        (ctm_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "id": str(row[0]),
        "centroid_id": row[1],
        "track": row[2],
        "month": row[3],
    }


# =============================================================================
# BUCKET ASSIGNMENT (Domestic / Bilateral)
# =============================================================================


def load_centroid_iso_codes(conn, centroid_id: str) -> set:
    """Load iso_codes for a centroid from centroids_v3."""
    cur = conn.cursor()
    cur.execute("SELECT iso_codes FROM centroids_v3 WHERE id = %s", (centroid_id,))
    row = cur.fetchone()
    if row and row[0]:
        return set(row[0])
    return set()


def get_geo_bucket_from_aliases(aliases: list, home_iso_codes: set) -> str:
    """Check if aliases suggest a geographic bucket using GEO_ALIAS_TO_ISO."""
    for alias in aliases:
        alias_lower = str(alias).lower()
        if alias_lower in GEO_ALIAS_TO_ISO:
            iso = GEO_ALIAS_TO_ISO[alias_lower]
            if iso not in home_iso_codes:
                return iso
    return None


def extract_country_from_actor(actor: str) -> str:
    """Extract country code from actor like 'CN_EXECUTIVE' -> 'CN'."""
    if not actor or actor == "UNKNOWN":
        return None
    if "_" in actor and len(actor.split("_")[0]) == 2:
        return actor.split("_")[0]
    if actor in ["EU", "NATO", "BRICS", "G7", "MERCOSUR", "IGO"]:
        return actor
    return None


def assign_title_bucket(title: dict, home_iso_codes: set) -> tuple:
    """Assign a title to bucket based on target, actor, aliases.

    Returns: (event_type, bucket_key)
        - ("domestic", None)
        - ("bilateral", "US") or ("bilateral", "EU") etc.
    """
    target = title.get("target")
    actor = title.get("actor")
    # Use places from signals as pseudo-aliases for bucket detection
    places = title.get("places", [])

    # 1. Check target first
    if target and target != "-":
        if len(target) == 2:
            if target not in home_iso_codes:
                return ("bilateral", target)
        elif "_" in target:
            target_country = target.split("_")[0]
            if len(target_country) == 2 and target_country not in home_iso_codes:
                return ("bilateral", target_country)
        elif target in ["NATO", "EU", "BRICS", "G7", "MERCOSUR"]:
            return ("bilateral", target)
        elif "," in target:
            for t in target.split(","):
                t = t.strip()
                if len(t) == 2 and t not in home_iso_codes:
                    return ("bilateral", t)

    # 2. Check actor nationality
    actor_country = extract_country_from_actor(actor)
    if actor_country:
        if actor_country not in home_iso_codes:
            if len(actor_country) == 2:
                return ("bilateral", actor_country)
            elif actor_country in ["NATO", "EU", "BRICS", "G7", "MERCOSUR"]:
                return ("bilateral", actor_country)

    # 3. Check places (from typed signals) for geographic bucket
    for place in places:
        bucket_iso = get_geo_bucket_from_aliases([place], home_iso_codes)
        if bucket_iso:
            return ("bilateral", bucket_iso)

    return ("domestic", None)


def determine_topic_bucket(cluster, home_iso_codes: set) -> tuple:
    """Determine bucket for a topic cluster based on majority of titles.

    Returns: (event_type, bucket_key)
    """
    bucket_counts = Counter()

    for title in cluster.titles:
        event_type, bucket_key = assign_title_bucket(title, home_iso_codes)
        if event_type == "bilateral" and bucket_key:
            bucket_counts[bucket_key] += 1
        else:
            bucket_counts["_domestic"] += 1

    if not bucket_counts:
        return ("domestic", None)

    # Get most common bucket
    most_common = bucket_counts.most_common(1)[0]
    if most_common[0] == "_domestic":
        return ("domestic", None)
    else:
        return ("bilateral", most_common[0])


# =============================================================================
# CO-OCCURRENCE MATRIX
# =============================================================================


def extract_signal_tokens(title: dict, weights: dict) -> list:
    """Extract weighted signal tokens from a title.

    Uses ONLY typed signals for clustering, not ELO labels (actor/target).
    ELO labels are for event classification, typed signals are for topic clustering.
    """
    tokens = []

    for sig_type in SIGNAL_TYPES:
        weight = weights.get(sig_type, 1.0)
        values = title.get(sig_type, [])

        for val in values:
            # Create typed token: "persons:TRUMP", "commodities:oil"
            token = "{}:{}".format(
                sig_type, val.upper() if sig_type == "persons" else val
            )
            tokens.append((token, weight))

    return tokens


def build_cooccurrence_matrix(titles: list, weights: dict) -> dict:
    """
    Build weighted co-occurrence matrix.

    Returns: {token: {other_token: weighted_count}}
    """
    matrix = defaultdict(Counter)

    for title in titles:
        tokens = extract_signal_tokens(title, weights)

        # Count co-occurrences within same title
        for i, (t1, w1) in enumerate(tokens):
            for t2, w2 in tokens[i + 1 :]:
                # Weighted co-occurrence
                combined_weight = (w1 + w2) / 2
                matrix[t1][t2] += combined_weight
                matrix[t2][t1] += combined_weight

    return dict(matrix)


def compute_token_frequencies(titles: list, weights: dict) -> Counter:
    """Count token frequencies across all titles."""
    freq = Counter()
    for title in titles:
        tokens = extract_signal_tokens(title, weights)
        for token, weight in tokens:
            freq[token] += 1
    return freq


def compute_idf_weights(token_freq: Counter, total_docs: int) -> dict:
    """
    Compute IDF-like dampening for high-frequency tokens.

    Tokens appearing in >30% of docs get reduced weight.
    """
    idf = {}
    for token, count in token_freq.items():
        doc_freq = count / total_docs
        if doc_freq > 0.3:
            # Strong dampening for very common tokens
            idf[token] = max(0.1, 1.0 - (doc_freq - 0.3) * 2)
        elif doc_freq > 0.1:
            # Mild dampening
            idf[token] = 1.0 - (doc_freq - 0.1)
        else:
            # No dampening for rare tokens
            idf[token] = 1.0
    return idf


# =============================================================================
# CLUSTERING
# =============================================================================


class TopicCluster:
    """A cluster of titles forming a Topic."""

    def __init__(self, seed_title: dict):
        self.titles = [seed_title]
        self.token_counts = Counter()
        self._update_tokens(seed_title)

    def _update_tokens(self, title: dict):
        """Update token counts from title using only typed signals."""
        for sig_type in SIGNAL_TYPES:
            for val in title.get(sig_type, []):
                token = "{}:{}".format(
                    sig_type, val.upper() if sig_type == "persons" else val
                )
                self.token_counts[token] += 1

    def add_title(self, title: dict):
        """Add a title to this cluster."""
        self.titles.append(title)
        self._update_tokens(title)

    def similarity(
        self, title: dict, weights: dict, idf: dict = None, discriminators: dict = None
    ) -> float:
        """Compute similarity between title and cluster with IDF dampening.

        Uses only typed signals, not ELO labels.
        Applies discriminator penalties for conflicting signals (e.g., different orgs).
        """
        if not self.token_counts:
            return 0.0

        # Build title tokens grouped by signal type
        title_tokens = set()
        title_by_type = defaultdict(set)
        for sig_type in SIGNAL_TYPES:
            for val in title.get(sig_type, []):
                token = "{}:{}".format(
                    sig_type, val.upper() if sig_type == "persons" else val
                )
                title_tokens.add(token)
                title_by_type[sig_type].add(token)

        if not title_tokens:
            return 0.0

        # Build cluster tokens grouped by signal type
        cluster_tokens = set(self.token_counts.keys())
        cluster_by_type = defaultdict(set)
        for token in cluster_tokens:
            sig_type = token.split(":")[0]
            cluster_by_type[sig_type].add(token)

        # Weighted Jaccard-like similarity
        intersection = title_tokens & cluster_tokens
        union = title_tokens | cluster_tokens

        if not union:
            return 0.0

        # Weight the intersection by token importance with IDF dampening
        weighted_match = 0.0
        for token in intersection:
            sig_type = token.split(":")[0]
            base_weight = weights.get(sig_type, 1.0)

            # Apply IDF dampening for common tokens
            idf_factor = idf.get(token, 1.0) if idf else 1.0

            # Mild boost by cluster count (capped)
            count_boost = min(self.token_counts[token] / 5, 1.5)

            weighted_match += base_weight * idf_factor * count_boost

        base_similarity = weighted_match / len(union)

        # Apply discriminator penalties for conflicting signals
        # e.g., if cluster's PRIMARY org is FED and title has JPMORGAN (not FED), reject
        if discriminators:
            for sig_type, penalty_weight in discriminators.items():
                cluster_sigs = cluster_by_type.get(sig_type, set())
                title_sigs = title_by_type.get(sig_type, set())

                if cluster_sigs and title_sigs:
                    # Get cluster's PRIMARY signal of this type (most common)
                    cluster_primary = None
                    max_count = 0
                    for token in cluster_sigs:
                        count = self.token_counts.get(token, 0)
                        if count > max_count:
                            max_count = count
                            cluster_primary = token

                    # Check for conflict: title has DIFFERENT orgs than cluster's primary
                    if cluster_primary and cluster_primary not in title_sigs:
                        # Cluster has 5+ titles and primary is in 25%+ of them
                        dominance = max_count / max(len(self.titles), 1)
                        if len(self.titles) >= 5 and dominance > 0.25:
                            return 0.0  # Reject - title lacks cluster's primary org

        return max(0.0, base_similarity)

    def get_top_tokens(self, n: int = 5) -> list:
        """Get top N tokens by count."""
        return self.token_counts.most_common(n)

    def generate_summary_key(self) -> str:
        """Generate a key for this topic based on top tokens."""
        top = self.get_top_tokens(3)
        if not top:
            return "misc"
        return "_".join(t[0].split(":")[1] for t in top)


def cluster_titles(
    titles: list,
    weights: dict,
    min_similarity: float = 0.15,
    idf: dict = None,
    discriminators: dict = None,
) -> list:
    """
    Cluster titles into Topics using greedy assignment with IDF dampening.

    Args:
        titles: List of title dicts with signals
        weights: Signal type weights
        min_similarity: Minimum similarity threshold to join cluster
        idf: IDF weights for token dampening
        discriminators: Penalty weights for conflicting signal types

    Returns: list of TopicCluster objects
    """
    if not titles:
        return []

    # Compute IDF if not provided
    if idf is None:
        token_freq = compute_token_frequencies(titles, weights)
        idf = compute_idf_weights(token_freq, len(titles))

    # Sort by date (newest first) to seed with recent stories
    sorted_titles = sorted(titles, key=lambda t: t["pubdate_utc"], reverse=True)

    clusters = []

    for title in sorted_titles:
        # Find best matching cluster
        best_cluster = None
        best_sim = min_similarity

        for cluster in clusters:
            sim = cluster.similarity(title, weights, idf, discriminators)
            if sim > best_sim:
                best_sim = sim
                best_cluster = cluster

        if best_cluster:
            best_cluster.add_title(title)
        else:
            # Create new cluster
            clusters.append(TopicCluster(title))

    return clusters


# =============================================================================
# ANALYSIS
# =============================================================================


def analyze_clustering(clusters: list, titles: list):
    """Print clustering analysis."""
    print("\n" + "=" * 70)
    print("CLUSTERING ANALYSIS")
    print("=" * 70)

    print("\nTotal titles: {}".format(len(titles)))
    print("Total topics: {}".format(len(clusters)))

    # Size distribution
    sizes = [len(c.titles) for c in clusters]
    sizes.sort(reverse=True)

    print("\nTopic size distribution:")
    print("  Largest: {}".format(sizes[0] if sizes else 0))
    print("  Top 5: {}".format(sizes[:5]))
    print("  Topics with 1 title: {}".format(sum(1 for s in sizes if s == 1)))
    print("  Topics with 2-5 titles: {}".format(sum(1 for s in sizes if 2 <= s <= 5)))
    print("  Topics with 6-20 titles: {}".format(sum(1 for s in sizes if 6 <= s <= 20)))
    print("  Topics with >20 titles: {}".format(sum(1 for s in sizes if s > 20)))

    # Show top topics
    print("\n" + "-" * 70)
    print("TOP 15 TOPICS (by size)")
    print("-" * 70)

    for i, cluster in enumerate(
        sorted(clusters, key=lambda c: len(c.titles), reverse=True)[:15]
    ):
        top_tokens = cluster.get_top_tokens(4)
        token_str = ", ".join(
            "{}({})".format(t[0].split(":")[1], t[1]) for t in top_tokens
        )

        print("\n{}. {} titles - {}".format(i + 1, len(cluster.titles), token_str))

        # Show sample titles (ASCII safe for Windows console)
        for title in cluster.titles[:3]:
            display = title["title_display"][:80]
            safe_display = display.encode("ascii", "replace").decode()
            print("   - {}".format(safe_display))
        if len(cluster.titles) > 3:
            print("   ... and {} more".format(len(cluster.titles) - 3))


def write_topics_to_db(
    conn, clusters: list, ctm_id: str, home_iso_codes: set, min_titles: int = 2
) -> int:
    """
    Write topic clusters to events_v3 table.

    Only writes clusters with >= min_titles.
    """
    import uuid

    cur = conn.cursor()
    written = 0
    domestic_count = 0
    bilateral_count = 0

    # Clear old events for this CTM
    cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))
    deleted = cur.rowcount
    if deleted > 0:
        logger.info("Cleared {} old events for CTM".format(deleted))

    # Filter clusters by minimum size
    valid_clusters = [c for c in clusters if len(c.titles) >= min_titles]

    for cluster in valid_clusters:
        # Get date range
        dates = [t["pubdate_utc"] for t in cluster.titles]
        first_date = min(dates).date() if dates else None
        last_date = max(dates).date() if dates else None

        # Generate topic summary from top tokens
        top_tokens = cluster.get_top_tokens(4)
        summary_parts = []
        for token, count in top_tokens:
            sig_type, value = token.split(":", 1)
            summary_parts.append(value)

        # Show all keywords (no truncation)
        summary = "Topic: {}".format(", ".join(summary_parts))

        # Create event_id
        event_id = str(uuid.uuid4())

        # Determine if catchall (large cluster with common signals)
        is_catchall = len(cluster.titles) > 50

        # Determine bucket (domestic vs bilateral)
        event_type, bucket_key = determine_topic_bucket(cluster, home_iso_codes)
        if event_type == "bilateral":
            bilateral_count += 1
        else:
            domestic_count += 1

        try:
            # Insert event
            cur.execute(
                """
                INSERT INTO events_v3 (
                    id, ctm_id, date, first_seen, summary, event_type, bucket_key,
                    source_batch_count, is_catchall, last_active
                ) VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
                """,
                (
                    event_id,
                    ctm_id,
                    first_date,
                    summary,
                    event_type,
                    bucket_key,
                    len(cluster.titles),
                    is_catchall,
                    last_date,
                ),
            )

            # Insert title links
            for title in cluster.titles:
                cur.execute(
                    """
                    INSERT INTO event_v3_titles (event_id, title_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (event_id, title["id"]),
                )

            written += 1

        except Exception as e:
            logger.warning("Failed to write topic: {}".format(e))
            continue

    conn.commit()
    print("  Domestic: {}, Bilateral: {}".format(domestic_count, bilateral_count))
    return written


# =============================================================================
# MAIN
# =============================================================================


def process_ctm(
    ctm_id: str, min_similarity: float = 0.15, min_titles: int = 2, dry_run: bool = True
):
    """Process a CTM for topic clustering."""
    conn = get_connection()

    # Get CTM info
    ctm_info = get_ctm_info(conn, ctm_id)
    if not ctm_info:
        print("CTM not found: {}".format(ctm_id))
        conn.close()
        return

    print("Processing CTM: {} / {}".format(ctm_info["centroid_id"], ctm_info["track"]))
    print("Month: {}".format(ctm_info["month"]))

    # Load centroid's home ISO codes for bucket assignment
    home_iso_codes = load_centroid_iso_codes(conn, ctm_info["centroid_id"])
    print("Home ISO codes: {}".format(sorted(home_iso_codes)))

    # Get weights and discriminators for this track
    weights = get_track_weights(ctm_info["track"])
    discriminators = get_track_discriminators(ctm_info["track"])
    print("\nTrack weights: {}".format(ctm_info["track"]))
    for sig_type, weight in weights.items():
        print("  {}: {:.1f}".format(sig_type, weight))
    if discriminators:
        print("\nDiscriminators (penalty for conflicting signals):")
        for sig_type, penalty in discriminators.items():
            print("  {}: {:.1f}".format(sig_type, penalty))

    # Load titles
    print("\nLoading titles with signals...")
    titles = load_titles_with_signals(conn, ctm_id)

    if not titles:
        print("No titles with signals found.")
        conn.close()
        return

    print("Found {} titles with signals".format(len(titles)))

    # Filter publisher names from orgs
    publisher_patterns = load_publisher_patterns(conn)
    filtered_count = filter_titles_publisher_signals(titles, publisher_patterns)
    if filtered_count > 0:
        print("Filtered {} publisher signals from orgs".format(filtered_count))

    # Build co-occurrence matrix (for analysis)
    print("\nBuilding co-occurrence matrix...")
    matrix = build_cooccurrence_matrix(titles, weights)
    print("Matrix has {} unique tokens".format(len(matrix)))

    # Compute token frequencies and IDF
    token_freq = compute_token_frequencies(titles, weights)
    idf = compute_idf_weights(token_freq, len(titles))

    # Show dampened tokens
    dampened = [(t, f, idf[t]) for t, f in token_freq.most_common(20) if idf[t] < 1.0]
    if dampened:
        print("\nDampened high-frequency tokens:")
        for token, freq, idf_val in dampened[:10]:
            print("  {} (freq={}, idf={:.2f})".format(token, freq, idf_val))

    # Show top co-occurring pairs
    print("\nTop co-occurring signal pairs:")
    pairs = []
    for t1, others in matrix.items():
        for t2, count in others.items():
            if t1 < t2:  # Avoid duplicates
                pairs.append((t1, t2, count))
    pairs.sort(key=lambda x: x[2], reverse=True)
    for t1, t2, count in pairs[:10]:
        print("  {:.1f}: {} + {}".format(count, t1, t2))

    # Cluster with IDF
    print(
        "\nClustering with min_similarity={:.2f} and IDF dampening...".format(
            min_similarity
        )
    )
    clusters = cluster_titles(titles, weights, min_similarity, idf, discriminators)

    # Analyze
    analyze_clustering(clusters, titles)

    if dry_run:
        print("\n(DRY RUN - no database writes)")
    else:
        print("\nWriting topics to database...")
        written = write_topics_to_db(
            conn, clusters, ctm_id, home_iso_codes, min_titles=min_titles
        )
        print("Wrote {} topics (clusters with {}+ titles)".format(written, min_titles))

        # Count small clusters not written
        small_clusters = sum(1 for c in clusters if len(c.titles) < min_titles)
        if small_clusters > 0:
            print(
                "Skipped {} small clusters (<{} titles)".format(
                    small_clusters, min_titles
                )
            )

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cluster titles into Topics")
    parser.add_argument("--ctm-id", required=True, help="CTM ID to process")
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.15,
        help="Minimum similarity threshold",
    )
    parser.add_argument(
        "--min-titles", type=int, default=2, help="Minimum titles per topic"
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=True, help="Don't write to database"
    )
    parser.add_argument(
        "--write", action="store_true", help="Actually write to database"
    )

    args = parser.parse_args()

    process_ctm(
        ctm_id=args.ctm_id,
        min_similarity=args.min_similarity,
        min_titles=args.min_titles,
        dry_run=not args.write,
    )
