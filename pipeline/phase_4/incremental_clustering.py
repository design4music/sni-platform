"""
Phase 4: Incremental Topic Clustering

Clusters titles as they arrive chronologically, simulating natural news flow.
Topics emerge from early titles and grow with co-occurring signals.

Key concepts:
- Anchor signals: Core identity from first N titles (locked after threshold)
- Co-occurring signals: Later additions that appear with anchors
- Topic emergence: Track when topic became significant (>threshold titles)

Usage:
    python pipeline/phase_4/incremental_clustering.py --ctm-id <ctm_id>
"""

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2

from core.config import (
    HIGH_FREQ_PERSONS,
    SIGNAL_TYPES,
    config,
    get_track_discriminators,
    get_track_weights,
)
from core.publisher_filter import filter_publisher_signals, load_publisher_patterns

# =============================================================================
# CONFIGURATION
# =============================================================================

# After this many titles, anchor signals are locked
ANCHOR_LOCK_THRESHOLD = 5

# Minimum titles for topic to be considered "emerged"
EMERGENCE_THRESHOLD = 3

# Similarity threshold for joining existing topic
JOIN_THRESHOLD = 0.2


def get_weights(track: str) -> dict:
    return get_track_weights(track)


def get_discriminators(track: str) -> list:
    # get_track_discriminators returns dict, but this clustering uses list of keys
    return list(get_track_discriminators(track).keys())


# =============================================================================
# DATABASE
# =============================================================================


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def load_titles_chronological(conn, ctm_id: str) -> list:
    """Load titles in chronological order (oldest first)."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            t.id, t.title_display, t.pubdate_utc,
            tl.persons, tl.orgs, tl.places, tl.commodities,
            tl.policies, tl.systems, tl.named_events,
            tl.target, tl.actor
        FROM titles_v3 t
        JOIN title_assignments ta ON t.id = ta.title_id
        JOIN title_labels tl ON t.id = tl.title_id
        WHERE ta.ctm_id = %s
          AND (tl.persons IS NOT NULL OR tl.orgs IS NOT NULL OR tl.places IS NOT NULL
               OR tl.commodities IS NOT NULL OR tl.policies IS NOT NULL
               OR tl.systems IS NOT NULL OR tl.named_events IS NOT NULL)
        ORDER BY t.pubdate_utc ASC
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
                "persons": r[3] or [],
                "orgs": r[4] or [],
                "places": r[5] or [],
                "commodities": r[6] or [],
                "policies": r[7] or [],
                "systems": r[8] or [],
                "named_events": r[9] or [],
                "target": r[10],
                "actor": r[11],
            }
        )
    return titles


def load_centroid_iso_codes(conn, centroid_id: str) -> set:
    """Load iso_codes for a centroid."""
    cur = conn.cursor()
    cur.execute("SELECT iso_codes FROM centroids_v3 WHERE id = %s", (centroid_id,))
    row = cur.fetchone()
    if row and row[0]:
        return set(row[0])
    return set()


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
    """Assign a title to bucket based on target/actor.

    Returns: (event_type, bucket_key)
    """
    target = title.get("target")
    actor = title.get("actor")

    # Check target first
    if target and target != "-":
        if len(target) == 2 and target not in home_iso_codes:
            return ("bilateral", target)
        elif target in ["NATO", "EU", "BRICS", "G7", "MERCOSUR"]:
            return ("bilateral", target)

    # Check actor nationality
    actor_country = extract_country_from_actor(actor)
    if actor_country and actor_country not in home_iso_codes:
        if len(actor_country) == 2:
            return ("bilateral", actor_country)
        elif actor_country in ["NATO", "EU", "BRICS", "G7", "MERCOSUR"]:
            return ("bilateral", actor_country)

    return ("domestic", None)


def get_ctm_info(conn, ctm_id: str) -> dict:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, centroid_id, track, month FROM ctm WHERE id = %s",
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
# INCREMENTAL TOPIC
# =============================================================================


# HIGH_FREQ_PERSONS imported from core.config


class IncrementalTopic:
    """A topic that grows incrementally as titles arrive."""

    def __init__(self, seed_title: dict, topic_id: int, home_iso_codes: set = None):
        self.id = topic_id
        self.titles = [seed_title]
        self.created_date = (
            seed_title["pubdate_utc"].date() if seed_title["pubdate_utc"] else None
        )
        self.emerged_date = None  # Set when titles >= EMERGENCE_THRESHOLD

        # Anchor signals - locked after ANCHOR_LOCK_THRESHOLD titles
        self.anchor_signals = set()  # e.g., {"orgs:FED", "persons:POWELL"}
        self.anchors_locked = False

        # All signals with counts
        self.signal_counts = Counter()

        # Daily title counts for growth tracking
        self.daily_counts = Counter()  # {date: count}

        # Bucket tracking
        self.home_iso_codes = home_iso_codes or set()
        self.bucket_counts = Counter()  # {"domestic": N, "IR": M, ...}

        # Initialize from seed
        self._add_signals(seed_title)

    def _extract_tokens(self, title: dict, for_matching: bool = False) -> set:
        """Extract signal tokens from title.

        If for_matching=True, excludes high-freq persons for similarity calc.
        """
        tokens = set()
        for sig_type in SIGNAL_TYPES:
            for val in title.get(sig_type, []):
                normalized = val.upper() if sig_type == "persons" else val
                token = "{}:{}".format(sig_type, normalized)

                # Skip high-freq persons for matching (they don't discriminate)
                if (
                    for_matching
                    and sig_type == "persons"
                    and normalized in HIGH_FREQ_PERSONS
                ):
                    continue

                tokens.add(token)
        return tokens

    def _add_signals(self, title: dict):
        """Update signal counts from title."""
        tokens = self._extract_tokens(title, for_matching=False)
        for token in tokens:
            self.signal_counts[token] += 1

        # Track daily count
        if title["pubdate_utc"]:
            day = title["pubdate_utc"].date()
            self.daily_counts[day] += 1

        # Track bucket
        event_type, bucket_key = assign_title_bucket(title, self.home_iso_codes)
        if event_type == "bilateral" and bucket_key:
            self.bucket_counts[bucket_key] += 1
        else:
            self.bucket_counts["_domestic"] += 1

        # Update anchors if not locked (exclude high-freq persons from anchors)
        if not self.anchors_locked:
            threshold = max(1, len(self.titles) // 2)
            self.anchor_signals = set()
            for token, count in self.signal_counts.items():
                if count >= threshold:
                    # Exclude high-freq persons from anchors
                    sig_type, val = token.split(":", 1)
                    if sig_type == "persons" and val in HIGH_FREQ_PERSONS:
                        continue
                    self.anchor_signals.add(token)

            # Lock anchors after threshold
            if len(self.titles) >= ANCHOR_LOCK_THRESHOLD:
                self.anchors_locked = True

        # Check emergence
        if self.emerged_date is None and len(self.titles) >= EMERGENCE_THRESHOLD:
            self.emerged_date = (
                title["pubdate_utc"].date() if title["pubdate_utc"] else None
            )

    def get_bucket(self) -> tuple:
        """Get dominant bucket for this topic."""
        if not self.bucket_counts:
            return ("domestic", None)
        most_common = self.bucket_counts.most_common(1)[0]
        if most_common[0] == "_domestic":
            return ("domestic", None)
        return ("bilateral", most_common[0])

    def add_title(self, title: dict):
        """Add a title to this topic."""
        self.titles.append(title)
        self._add_signals(title)

    def match_score(self, title: dict, weights: dict, discriminators: list) -> float:
        """
        Calculate match score for a title against this topic.

        Returns 0.0 if discriminator conflict, otherwise weighted overlap score.
        High-frequency persons (TRUMP etc) are excluded from matching.
        """
        title_tokens = self._extract_tokens(title, for_matching=True)
        if not title_tokens:
            return 0.0

        # Check discriminator conflicts
        if self.anchors_locked and discriminators:
            for sig_type in discriminators:
                # Get anchor signals of this type
                anchor_sigs = {
                    t for t in self.anchor_signals if t.startswith(sig_type + ":")
                }
                title_sigs = {t for t in title_tokens if t.startswith(sig_type + ":")}

                # If topic has anchor of this type and title has different value, reject
                if anchor_sigs and title_sigs and not (anchor_sigs & title_sigs):
                    return 0.0  # Hard reject - different org/commodity

        # Calculate weighted overlap with anchors (if locked) or all signals
        compare_set = (
            self.anchor_signals
            if self.anchors_locked
            else set(self.signal_counts.keys())
        )

        if not compare_set:
            return 0.0

        overlap = title_tokens & compare_set

        if not overlap:
            return 0.0

        # Weighted score
        score = 0.0
        for token in overlap:
            sig_type = token.split(":")[0]
            weight = weights.get(sig_type, 1.0)
            # Boost if signal is in anchors
            anchor_boost = 1.5 if token in self.anchor_signals else 1.0
            score += weight * anchor_boost

        # Normalize by topic anchor count
        max_score = sum(weights.get(t.split(":")[0], 1.0) * 1.5 for t in compare_set)
        return score / max_score if max_score > 0 else 0.0

    def get_anchor_summary(self) -> str:
        """Get summary from anchor signals."""
        # Sort by count, take top 4
        anchor_list = [(t, self.signal_counts[t]) for t in self.anchor_signals]
        anchor_list.sort(key=lambda x: -x[1])
        parts = [t.split(":")[1] for t, _ in anchor_list[:4]]
        return ", ".join(parts) if parts else "misc"

    def get_cooccurring_signals(self) -> list:
        """Get signals that co-occur with anchors but aren't anchors themselves."""
        cooccur = []
        for token, count in self.signal_counts.most_common(20):
            if token not in self.anchor_signals:
                cooccur.append((token, count))
        return cooccur[:10]


# =============================================================================
# INCREMENTAL CLUSTERING
# =============================================================================


def cluster_incrementally(
    titles: list,
    weights: dict,
    discriminators: list,
    home_iso_codes: set = None,
    join_threshold: float = JOIN_THRESHOLD,
) -> list:
    """
    Cluster titles incrementally in chronological order.

    Returns: list of IncrementalTopic objects
    """
    if not titles:
        return []

    home_iso_codes = home_iso_codes or set()
    topics = []
    topic_counter = 0

    for i, title in enumerate(titles):
        # Find best matching topic
        best_topic = None
        best_score = join_threshold

        for topic in topics:
            score = topic.match_score(title, weights, discriminators)
            if score > best_score:
                best_score = score
                best_topic = topic

        if best_topic:
            best_topic.add_title(title)
        else:
            # Create new topic
            topic_counter += 1
            new_topic = IncrementalTopic(title, topic_counter, home_iso_codes)
            topics.append(new_topic)

        # Progress logging
        if (i + 1) % 500 == 0:
            emerged = sum(1 for t in topics if t.emerged_date is not None)
            print(
                "Processed {}/{} titles, {} topics ({} emerged)".format(
                    i + 1, len(titles), len(topics), emerged
                )
            )

    return topics


# =============================================================================
# ANALYSIS
# =============================================================================


def analyze_topics(topics: list):
    """Print analysis of incremental clustering results."""
    print("\n" + "=" * 70)
    print("INCREMENTAL CLUSTERING RESULTS")
    print("=" * 70)

    emerged = [t for t in topics if t.emerged_date is not None]
    sizes = sorted([len(t.titles) for t in topics], reverse=True)

    print("\nTotal topics: {}".format(len(topics)))
    print("Emerged topics ({}+ titles): {}".format(EMERGENCE_THRESHOLD, len(emerged)))
    print("\nSize distribution:")
    print("  Largest: {}".format(sizes[0] if sizes else 0))
    print("  Top 5: {}".format(sizes[:5]))
    print("  Single-title topics: {}".format(sum(1 for s in sizes if s == 1)))

    print("\n" + "-" * 70)
    print("TOP 15 EMERGED TOPICS")
    print("-" * 70)

    emerged_sorted = sorted(emerged, key=lambda t: -len(t.titles))

    for i, topic in enumerate(emerged_sorted[:15]):
        anchor_str = topic.get_anchor_summary()
        cooccur = topic.get_cooccurring_signals()
        cooccur_str = ", ".join("+{}".format(t.split(":")[1]) for t, c in cooccur[:3])

        locked_str = "[LOCKED]" if topic.anchors_locked else "[forming]"

        print(
            "\n{}. {} titles - {} {}".format(
                i + 1, len(topic.titles), anchor_str, locked_str
            )
        )
        if cooccur_str:
            print("   Co-occurring: {}".format(cooccur_str))
        print(
            "   Created: {}, Emerged: {}".format(topic.created_date, topic.emerged_date)
        )

        # Sample titles (ASCII safe)
        for title in topic.titles[:2]:
            display = title["title_display"][:70]
            safe_display = display.encode("ascii", "replace").decode()
            print("   - {}".format(safe_display))
        if len(topic.titles) > 2:
            print("   ... and {} more".format(len(topic.titles) - 2))


def show_topic_timeline(topics: list):
    """Show when topics emerged day by day."""
    print("\n" + "-" * 70)
    print("TOPIC EMERGENCE TIMELINE")
    print("-" * 70)

    emerged = [t for t in topics if t.emerged_date is not None]
    by_date = defaultdict(list)
    for topic in emerged:
        by_date[topic.emerged_date].append(topic)

    for day in sorted(by_date.keys()):
        day_topics = sorted(by_date[day], key=lambda t: -len(t.titles))
        print("\n{}:".format(day))
        for topic in day_topics[:5]:
            print(
                "  - {} ({} titles)".format(
                    topic.get_anchor_summary(), len(topic.titles)
                )
            )


# =============================================================================
# DATABASE WRITE
# =============================================================================


def write_topics_to_db(conn, topics: list, ctm_id: str, min_titles: int = 2) -> tuple:
    """Write incremental topics to events_v3 table.

    Returns: (written_count, domestic_count, bilateral_count)
    """
    import uuid

    cur = conn.cursor()

    # Clear old events for this CTM
    cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))
    deleted = cur.rowcount
    if deleted > 0:
        print("Cleared {} old events".format(deleted))

    # Filter to emerged topics with minimum titles
    valid_topics = [t for t in topics if len(t.titles) >= min_titles]

    written = 0
    domestic_count = 0
    bilateral_count = 0

    for topic in valid_topics:
        event_id = str(uuid.uuid4())

        # Get dates
        dates = [t["pubdate_utc"] for t in topic.titles if t["pubdate_utc"]]
        first_date = min(dates).date() if dates else None
        last_date = max(dates).date() if dates else None

        # Build summary from anchors
        anchor_list = sorted(
            topic.anchor_signals, key=lambda x: -topic.signal_counts.get(x, 0)
        )
        anchor_values = [a.split(":")[1] for a in anchor_list[:4]]
        summary = (
            "Topic: {}".format(", ".join(anchor_values)) if anchor_values else "misc"
        )

        # Get anchor and co-occurring signals as arrays
        anchor_arr = list(topic.anchor_signals)[:10]
        cooccur = topic.get_cooccurring_signals()
        cooccur_arr = [t for t, c in cooccur[:10]]

        # Get bucket
        event_type, bucket_key = topic.get_bucket()
        if event_type == "bilateral":
            bilateral_count += 1
        else:
            domestic_count += 1

        try:
            cur.execute(
                """
                INSERT INTO events_v3 (
                    id, ctm_id, date, first_seen, summary,
                    source_batch_count, last_active,
                    anchor_signals, cooccurring_signals, emerged_date,
                    event_type, bucket_key
                ) VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event_id,
                    ctm_id,
                    first_date,
                    summary,
                    len(topic.titles),
                    last_date,
                    anchor_arr,
                    cooccur_arr,
                    topic.emerged_date,
                    event_type,
                    bucket_key,
                ),
            )

            # Link titles
            for title in topic.titles:
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
            print("Failed to write topic: {}".format(e))
            continue

    conn.commit()
    print("  Domestic: {}, Bilateral: {}".format(domestic_count, bilateral_count))
    return written


# =============================================================================
# MAIN
# =============================================================================


def process_ctm(ctm_id: str, dry_run: bool = True):
    """Process CTM with incremental clustering."""
    conn = get_connection()

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

    weights = get_weights(ctm_info["track"])
    discriminators = get_discriminators(ctm_info["track"])

    print("\nTrack config:")
    print(
        "  Weights: {}".format(
            ", ".join("{}={:.1f}".format(k, v) for k, v in weights.items())
        )
    )
    print("  Discriminators: {}".format(discriminators))
    print("  Join threshold: {}".format(JOIN_THRESHOLD))
    print("  Anchor lock after: {} titles".format(ANCHOR_LOCK_THRESHOLD))
    print("  High-freq persons (dampened): {}".format(sorted(HIGH_FREQ_PERSONS)))

    # Load titles chronologically
    print("\nLoading titles (oldest first)...")
    titles = load_titles_chronological(conn, ctm_id)

    if not titles:
        print("No titles with signals found.")
        conn.close()
        return

    print("Found {} titles".format(len(titles)))
    print(
        "Date range: {} to {}".format(
            titles[0]["pubdate_utc"].date() if titles else "N/A",
            titles[-1]["pubdate_utc"].date() if titles else "N/A",
        )
    )

    # Filter publisher signals
    publisher_patterns = load_publisher_patterns(conn)
    for title in titles:
        title["orgs"] = filter_publisher_signals(
            title.get("orgs", []), publisher_patterns
        )

    # Cluster incrementally
    print("\nClustering incrementally...")
    topics = cluster_incrementally(titles, weights, discriminators, home_iso_codes)

    # Analyze
    analyze_topics(topics)
    show_topic_timeline(topics)

    if not dry_run:
        print("\nWriting to database...")
        written = write_topics_to_db(conn, topics, ctm_id, min_titles=2)
        print("Wrote {} topics (with 2+ titles)".format(written))
    else:
        print("\n(DRY RUN - use --write to save)")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Incremental topic clustering")
    parser.add_argument("--ctm-id", required=True, help="CTM ID to process")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--write", action="store_true", help="Save to database")

    args = parser.parse_args()
    process_ctm(args.ctm_id, dry_run=not args.write)
