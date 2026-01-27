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
            t.id, t.title_display, t.pubdate_utc, t.centroid_ids,
            tl.persons, tl.orgs, tl.places, tl.commodities,
            tl.policies, tl.systems, tl.named_events
        FROM titles_v3 t
        JOIN title_assignments ta ON t.id = ta.title_id
        LEFT JOIN title_labels tl ON t.id = tl.title_id
        WHERE ta.ctm_id = %s
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
                "centroid_ids": r[3] or [],
                "persons": r[4] or [],
                "orgs": r[5] or [],
                "places": r[6] or [],
                "commodities": r[7] or [],
                "policies": r[8] or [],
                "systems": r[9] or [],
                "named_events": r[10] or [],
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


# =============================================================================
# GEOGRAPHIC BUCKETING (using centroid_ids)
# =============================================================================

MIN_BILATERAL_TITLES = 5


def is_geo_centroid(centroid_id: str) -> bool:
    """Check if centroid is geographic (not systemic)."""
    # GEO centroids have format like AMERICAS-USA, EUROPE-DE
    # SYS centroids have format like SYS-TECH, SYS-ENERGY
    return not centroid_id.startswith("SYS-")


def bucket_titles_by_centroid(titles: list, home_centroid_id: str) -> dict:
    """
    Bucket titles by geography using centroid_ids.

    - Domestic: centroid_ids has ONLY the home centroid (or home + SYS)
    - Bilateral: centroid_ids has exactly one foreign GEO centroid
    - Other International: multiple foreign GEO centroids or small bilateral buckets

    GEO centroids take priority over SYS centroids for bucketing.
    """
    domestic = []
    bilateral_raw = defaultdict(list)
    multilateral = []

    for title in titles:
        centroid_ids = title.get("centroid_ids", [])
        foreign_all = [c for c in centroid_ids if c != home_centroid_id]
        foreign_geo = [c for c in foreign_all if is_geo_centroid(c)]

        if not foreign_geo:
            # No foreign GEO centroid -> domestic (even if has SYS centroids)
            domestic.append(title)
        elif len(foreign_geo) == 1:
            # Single foreign GEO centroid -> bilateral
            bilateral_raw[foreign_geo[0]].append(title)
        else:
            # Multiple foreign GEO centroids -> defer to pass 2
            multilateral.append(title)

    # Pass 2: Assign multilateral to biggest foreign GEO bucket
    bucket_sizes = {k: len(v) for k, v in bilateral_raw.items()}
    for title in multilateral:
        centroid_ids = title.get("centroid_ids", [])
        foreign_geo = [
            c for c in centroid_ids if c != home_centroid_id and is_geo_centroid(c)
        ]
        if foreign_geo:
            # Assign to biggest bucket among this title's foreign GEOs
            best = max(foreign_geo, key=lambda c: bucket_sizes.get(c, 0))
            bilateral_raw[best].append(title)
            bucket_sizes[best] = bucket_sizes.get(best, 0) + 1

    # Pass 3: Move small bilateral buckets to other_international
    bilateral = {}
    other_international = []
    for centroid_id, ctitles in bilateral_raw.items():
        if len(ctitles) >= MIN_BILATERAL_TITLES:
            bilateral[centroid_id] = ctitles
        else:
            other_international.extend(ctitles)

    return {
        "domestic": domestic,
        "bilateral": bilateral,
        "other_international": other_international,
    }


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

    def __init__(self, seed_title: dict, topic_id: int):
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
    join_threshold: float = JOIN_THRESHOLD,
) -> list:
    """
    Cluster titles incrementally in chronological order.

    Titles should already be filtered to a single bucket before calling this.

    Returns: list of IncrementalTopic objects
    """
    if not titles:
        return []

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
            new_topic = IncrementalTopic(title, topic_counter)
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


def write_bucketed_topics_to_db(
    conn, bucketed_topics: dict, ctm_id: str, min_titles: int = 2
) -> int:
    """Write bucketed topics to events_v3 table.

    Args:
        bucketed_topics: {
            "domestic": [topics],
            "bilateral": {"CENTROID-ID": [topics], ...},
            "other_international": [topics]
        }
        ctm_id: CTM ID
        min_titles: Minimum titles for a topic to be written

    Returns: total written count
    """
    import uuid

    cur = conn.cursor()

    # Clear old events for this CTM
    cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))
    deleted = cur.rowcount
    if deleted > 0:
        print("Cleared {} old events".format(deleted))

    written = 0
    domestic_count = 0
    bilateral_count = 0
    catchall_count = 0

    # Track ungrouped titles per bucket for catchall events
    ungrouped = {
        "domestic": [],
        "bilateral": {},  # centroid_key -> [titles]
        "other_international": [],
    }

    def write_topic(topic, event_type, bucket_key=None):
        """Write a topic if it meets min_titles, otherwise collect for catchall."""
        nonlocal written, domestic_count, bilateral_count

        if len(topic.titles) < min_titles:
            # Collect for catchall
            if event_type == "domestic":
                ungrouped["domestic"].extend(topic.titles)
            elif event_type == "bilateral":
                if bucket_key not in ungrouped["bilateral"]:
                    ungrouped["bilateral"][bucket_key] = []
                ungrouped["bilateral"][bucket_key].extend(topic.titles)
            else:
                ungrouped["other_international"].extend(topic.titles)
            return

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

        try:
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
                    len(topic.titles),
                    False,
                    last_date,
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
            if event_type == "domestic":
                domestic_count += 1
            else:
                bilateral_count += 1

        except Exception as e:
            print("Failed to write topic: {}".format(e))

    def write_catchall(titles, event_type, bucket_key=None):
        """Write a catchall 'Other coverage' event for ungrouped titles."""
        nonlocal written, catchall_count

        if not titles:
            return

        event_id = str(uuid.uuid4())

        dates = [t["pubdate_utc"] for t in titles if t.get("pubdate_utc")]
        first_date = min(dates).date() if dates else None
        last_date = max(dates).date() if dates else None

        try:
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
                    "Other coverage",
                    event_type,
                    bucket_key,
                    len(titles),
                    True,
                    last_date,
                ),
            )

            for title in titles:
                cur.execute(
                    """
                    INSERT INTO event_v3_titles (event_id, title_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (event_id, title["id"]),
                )

            written += 1
            catchall_count += 1

        except Exception as e:
            print("Failed to write catchall: {}".format(e))

    # Write domestic topics
    for topic in bucketed_topics.get("domestic", []):
        write_topic(topic, "domestic", None)

    # Write bilateral topics
    for centroid_key, topics in bucketed_topics.get("bilateral", {}).items():
        for topic in topics:
            write_topic(topic, "bilateral", centroid_key)

    # Write other international topics
    for topic in bucketed_topics.get("other_international", []):
        write_topic(topic, "other_international", None)

    # Write catchall events for ungrouped titles
    write_catchall(ungrouped["domestic"], "domestic", None)
    for centroid_key, titles in ungrouped["bilateral"].items():
        write_catchall(titles, "bilateral", centroid_key)
    write_catchall(ungrouped["other_international"], "other_international", None)

    conn.commit()
    print(
        "  Domestic: {}, Bilateral: {}, Catchalls: {}".format(
            domestic_count, bilateral_count, catchall_count
        )
    )
    return written


# =============================================================================
# DAEMON INTERFACE
# =============================================================================


def process_ctm_for_daemon(conn, ctm_id: str, centroid_id: str, track: str) -> int:
    """
    Process a CTM for the pipeline daemon.

    This is the main entry point for daemon integration.
    Uses an existing connection (daemon manages connections).

    Returns: number of topics written to database
    """
    # Get track config
    weights = get_weights(track)
    discriminators = get_discriminators(track)

    # Load titles chronologically (oldest first for proper anchor formation)
    titles = load_titles_chronological(conn, ctm_id)

    if not titles:
        return 0

    # Filter publisher signals from orgs
    publisher_patterns = load_publisher_patterns(conn)
    for title in titles:
        title["orgs"] = filter_publisher_signals(
            title.get("orgs", []), publisher_patterns
        )

    # STAGE 1: Bucket by centroid_ids (geo-bucketing first)
    buckets = bucket_titles_by_centroid(titles, centroid_id)

    # STAGE 2: Cluster incrementally within each bucket
    bucketed_topics = {"domestic": [], "bilateral": {}, "other_international": []}

    # Domestic
    if buckets["domestic"]:
        domestic_sorted = sorted(buckets["domestic"], key=lambda t: t["pubdate_utc"])
        bucketed_topics["domestic"] = cluster_incrementally(
            domestic_sorted, weights, discriminators
        )

    # Bilateral (per country)
    for foreign_centroid, btitles in buckets["bilateral"].items():
        bilateral_sorted = sorted(btitles, key=lambda t: t["pubdate_utc"])
        bucketed_topics["bilateral"][foreign_centroid] = cluster_incrementally(
            bilateral_sorted, weights, discriminators
        )

    # Other international
    if buckets["other_international"]:
        other_sorted = sorted(
            buckets["other_international"], key=lambda t: t["pubdate_utc"]
        )
        bucketed_topics["other_international"] = cluster_incrementally(
            other_sorted, weights, discriminators
        )

    # Write to database
    written = write_bucketed_topics_to_db(conn, bucketed_topics, ctm_id, min_titles=2)

    return written


# =============================================================================
# MAIN (CLI)
# =============================================================================


def process_ctm(ctm_id: str, dry_run: bool = True):
    """Process CTM with incremental clustering (geo-bucketed first)."""
    conn = get_connection()

    ctm_info = get_ctm_info(conn, ctm_id)
    if not ctm_info:
        print("CTM not found: {}".format(ctm_id))
        conn.close()
        return

    centroid_id = ctm_info["centroid_id"]
    print("Processing CTM: {} / {}".format(centroid_id, ctm_info["track"]))
    print("Month: {}".format(ctm_info["month"]))

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
    print(
        "  High-freq persons (excluded from anchors): {}".format(
            sorted(HIGH_FREQ_PERSONS)
        )
    )

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

    # STAGE 1: Bucket by centroid_ids (geo-bucketing first)
    print("\n--- STAGE 1: Geographic Bucketing ---")
    buckets = bucket_titles_by_centroid(titles, centroid_id)
    print("Domestic: {} titles".format(len(buckets["domestic"])))
    for c in sorted(buckets["bilateral"], key=lambda x: -len(buckets["bilateral"][x])):
        print("  Bilateral {}: {} titles".format(c, len(buckets["bilateral"][c])))
    print("Other International: {} titles".format(len(buckets["other_international"])))

    # STAGE 2: Cluster incrementally within each bucket
    print("\n--- STAGE 2: Incremental Clustering per Bucket ---")
    bucketed_topics = {"domestic": [], "bilateral": {}, "other_international": []}

    # Domestic
    if buckets["domestic"]:
        domestic_sorted = sorted(buckets["domestic"], key=lambda t: t["pubdate_utc"])
        print("\nClustering DOMESTIC ({} titles)...".format(len(domestic_sorted)))
        bucketed_topics["domestic"] = cluster_incrementally(
            domestic_sorted, weights, discriminators
        )
        emerged = sum(1 for t in bucketed_topics["domestic"] if t.emerged_date)
        print(
            "  -> {} topics ({} emerged)".format(
                len(bucketed_topics["domestic"]), emerged
            )
        )

    # Bilateral (per country)
    for foreign_centroid in sorted(
        buckets["bilateral"], key=lambda x: -len(buckets["bilateral"][x])
    ):
        btitles = buckets["bilateral"][foreign_centroid]
        bilateral_sorted = sorted(btitles, key=lambda t: t["pubdate_utc"])
        print(
            "\nClustering BILATERAL {} ({} titles)...".format(
                foreign_centroid, len(bilateral_sorted)
            )
        )
        bucketed_topics["bilateral"][foreign_centroid] = cluster_incrementally(
            bilateral_sorted, weights, discriminators
        )
        emerged = sum(
            1 for t in bucketed_topics["bilateral"][foreign_centroid] if t.emerged_date
        )
        print(
            "  -> {} topics ({} emerged)".format(
                len(bucketed_topics["bilateral"][foreign_centroid]), emerged
            )
        )

    # Other international
    if buckets["other_international"]:
        other_sorted = sorted(
            buckets["other_international"], key=lambda t: t["pubdate_utc"]
        )
        print(
            "\nClustering OTHER INTERNATIONAL ({} titles)...".format(len(other_sorted))
        )
        bucketed_topics["other_international"] = cluster_incrementally(
            other_sorted, weights, discriminators
        )
        emerged = sum(
            1 for t in bucketed_topics["other_international"] if t.emerged_date
        )
        print(
            "  -> {} topics ({} emerged)".format(
                len(bucketed_topics["other_international"]), emerged
            )
        )

    # Summary
    print("\n--- RESULTS ---")
    total_topics = (
        len(bucketed_topics["domestic"])
        + sum(len(t) for t in bucketed_topics["bilateral"].values())
        + len(bucketed_topics["other_international"])
    )
    print("Total topics: {}".format(total_topics))

    if not dry_run:
        print("\nWriting to database...")
        written = write_bucketed_topics_to_db(
            conn, bucketed_topics, ctm_id, min_titles=2
        )
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
