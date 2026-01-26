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

from core.config import config

# =============================================================================
# TRACK-SPECIFIC WEIGHTING
# =============================================================================

# Signal weights by track - higher weight = more discriminating for that track
TRACK_WEIGHTS = {
    "geo_economy": {
        "persons": 1.0,  # Moderate - economic actors matter
        "orgs": 2.0,  # High - companies, central banks key
        "places": 1.0,  # Moderate
        "commodities": 3.0,  # Very high - oil, gold, wheat distinguish stories
        "policies": 2.0,  # High - tariffs, sanctions key
        "systems": 2.0,  # High - SWIFT, trade systems
        "named_events": 1.5,  # Moderate - Davos, G20
    },
    "geo_security": {
        "persons": 1.5,  # Moderate - military leaders
        "orgs": 2.0,  # High - NATO, militaries
        "places": 3.0,  # Very high - Crimea, Gaza distinguish conflicts
        "commodities": 0.5,  # Low
        "policies": 1.5,  # Moderate - defense agreements
        "systems": 2.5,  # High - S-400, weapons systems
        "named_events": 1.0,  # Moderate
    },
    "geo_politics": {
        "persons": 2.5,  # Very high - political actors key
        "orgs": 1.5,  # Moderate - parties, institutions
        "places": 1.5,  # Moderate
        "commodities": 0.5,  # Low
        "policies": 2.0,  # High - elections, legislation
        "systems": 0.5,  # Low
        "named_events": 2.0,  # High - elections, summits
    },
    "default": {
        "persons": 1.5,
        "orgs": 1.5,
        "places": 1.5,
        "commodities": 1.5,
        "policies": 1.5,
        "systems": 1.5,
        "named_events": 1.5,
    },
}

SIGNAL_TYPES = [
    "persons",
    "orgs",
    "places",
    "commodities",
    "policies",
    "systems",
    "named_events",
]


def get_weights(track: str) -> dict:
    """Get signal weights for a track."""
    return TRACK_WEIGHTS.get(track, TRACK_WEIGHTS["default"])


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
          AND tl.persons IS NOT NULL
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

    def similarity(self, title: dict, weights: dict, idf: dict = None) -> float:
        """Compute similarity between title and cluster with IDF dampening.

        Uses only typed signals, not ELO labels.
        """
        if not self.token_counts:
            return 0.0

        title_tokens = set()
        for sig_type in SIGNAL_TYPES:
            for val in title.get(sig_type, []):
                token = "{}:{}".format(
                    sig_type, val.upper() if sig_type == "persons" else val
                )
                title_tokens.add(token)

        if not title_tokens:
            return 0.0

        # Weighted Jaccard-like similarity
        cluster_tokens = set(self.token_counts.keys())
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

        # Normalize by union size
        return weighted_match / len(union)

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
    titles: list, weights: dict, min_similarity: float = 0.15, idf: dict = None
) -> list:
    """
    Cluster titles into Topics using greedy assignment with IDF dampening.

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
            sim = cluster.similarity(title, weights, idf)
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


def write_topics_to_db(conn, clusters: list, ctm_id: str, min_titles: int = 2) -> int:
    """
    Write topic clusters to events_v3 table.

    Only writes clusters with >= min_titles.
    """
    import uuid

    cur = conn.cursor()
    written = 0

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

        summary = "Topic: {}".format(", ".join(summary_parts[:3]))
        if len(summary_parts) > 3:
            summary += " (+{})".format(len(summary_parts) - 3)

        # Create event_id
        event_id = str(uuid.uuid4())

        # Determine if catchall (large cluster with common signals)
        is_catchall = len(cluster.titles) > 50

        try:
            # Insert event
            cur.execute(
                """
                INSERT INTO events_v3 (
                    id, ctm_id, date, first_seen, summary, event_type,
                    source_batch_count, is_catchall, last_active
                ) VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s, %s)
                """,
                (
                    event_id,
                    ctm_id,
                    first_date,
                    summary,
                    "domestic",  # Default - would need bucket logic for bilateral
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

    # Get weights for this track
    weights = get_weights(ctm_info["track"])
    print("\nTrack weights: {}".format(ctm_info["track"]))
    for sig_type, weight in weights.items():
        print("  {}: {:.1f}".format(sig_type, weight))

    # Load titles
    print("\nLoading titles with signals...")
    titles = load_titles_with_signals(conn, ctm_id)

    if not titles:
        print("No titles with signals found.")
        conn.close()
        return

    print("Found {} titles with signals".format(len(titles)))

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
    clusters = cluster_titles(titles, weights, min_similarity, idf)

    # Analyze
    analyze_clustering(clusters, titles)

    if dry_run:
        print("\n(DRY RUN - no database writes)")
    else:
        print("\nWriting topics to database...")
        written = write_topics_to_db(conn, clusters, ctm_id, min_titles=min_titles)
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
