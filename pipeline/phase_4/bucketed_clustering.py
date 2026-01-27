"""
Phase 4: Bucketed Topic Clustering

Two-stage approach:
1. FIRST: Bucket titles by geography (from Phase 2 centroid matching)
   - Domestic: titles about home country
   - Bilateral: titles about specific foreign country (US-EU, US-CN, etc.)
   - Other International: low-coverage bilateral and multilateral

2. THEN: Within each bucket, apply incremental topic clustering
   - Anchor signals from early titles
   - Co-occurrence matrix
   - Day-by-day growth tracking

Usage:
    python pipeline/phase_4/bucketed_clustering.py --ctm-id <ctm_id>
    python pipeline/phase_4/bucketed_clustering.py --ctm-id <ctm_id> --write
"""

import argparse
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2

from core.config import config
from core.publisher_filter import filter_publisher_signals, load_publisher_patterns

# =============================================================================
# CONFIGURATION
# =============================================================================

ANCHOR_LOCK_THRESHOLD = 5
EMERGENCE_THRESHOLD = 3
JOIN_THRESHOLD = 0.25
MIN_BILATERAL_TITLES = 5

HIGH_FREQ_PERSONS = {"TRUMP", "BIDEN", "PUTIN", "ZELENSKY", "XI"}

SIGNAL_TYPES = [
    "persons",
    "orgs",
    "places",
    "commodities",
    "policies",
    "systems",
    "named_events",
]

TRACK_WEIGHTS = {
    "geo_economy": {
        "persons": 1.0,
        "orgs": 3.0,
        "places": 1.0,
        "commodities": 3.0,
        "policies": 2.0,
        "systems": 2.0,
        "named_events": 1.5,
    },
    "geo_security": {
        "persons": 1.5,
        "orgs": 2.0,
        "places": 3.0,
        "commodities": 0.5,
        "policies": 1.5,
        "systems": 2.5,
        "named_events": 1.0,
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

TRACK_DISCRIMINATORS = {
    "geo_economy": ["orgs", "commodities"],
    "geo_security": ["places", "systems"],
    "default": [],
}


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


def get_ctm_info(conn, ctm_id: str) -> dict:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, centroid_id, track, month FROM ctm WHERE id = %s", (ctm_id,)
    )
    row = cur.fetchone()
    if not row:
        return None
    return {"id": str(row[0]), "centroid_id": row[1], "track": row[2], "month": row[3]}


def load_titles_with_bucket_info(conn, ctm_id: str) -> list:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT t.id, t.title_display, t.pubdate_utc, t.centroid_ids,
               tl.persons, tl.orgs, tl.places, tl.commodities,
               tl.policies, tl.systems, tl.named_events
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
    return [
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
        for r in cur.fetchall()
    ]


# =============================================================================
# STAGE 1: GEOGRAPHIC BUCKETING (based on titles_v3.centroid_ids)
# =============================================================================


def bucket_titles(titles: list, home_centroid_id: str) -> dict:
    """
    Bucket titles by geography using centroid_ids:
    - Domestic: centroid_ids has ONLY the home centroid
    - International: centroid_ids has multiple centroids

    For titles with 3+ centroids (multilateral), assign to biggest non-local
    bucket within this CTM.
    """
    domestic = []
    bilateral_raw = defaultdict(list)  # centroid_id -> titles (for 2-centroid titles)
    multilateral = []  # titles with 3+ centroids (assigned later)

    # Pass 1: Separate domestic, bilateral (2 centroids), multilateral (3+)
    for title in titles:
        centroid_ids = title.get("centroid_ids", [])

        if len(centroid_ids) <= 1:
            # Only home centroid (or none) -> domestic
            domestic.append(title)
        elif len(centroid_ids) == 2:
            # Bilateral: find the foreign centroid
            foreign = [c for c in centroid_ids if c != home_centroid_id]
            if foreign:
                bilateral_raw[foreign[0]].append(title)
            else:
                domestic.append(title)
        else:
            # 3+ centroids -> multilateral, defer assignment
            multilateral.append(title)

    # Pass 2: Assign multilateral titles to biggest non-local bucket
    for title in multilateral:
        centroid_ids = title.get("centroid_ids", [])
        foreign = [c for c in centroid_ids if c != home_centroid_id]

        if not foreign:
            domestic.append(title)
            continue

        # Find which foreign centroid has the biggest bucket so far
        best_centroid = None
        best_count = -1
        for fc in foreign:
            count = len(bilateral_raw.get(fc, []))
            if count > best_count:
                best_count = count
                best_centroid = fc

        if best_centroid:
            bilateral_raw[best_centroid].append(title)
        else:
            # No existing bucket, use first foreign centroid
            bilateral_raw[foreign[0]].append(title)

    # Pass 3: Filter small buckets to "other international"
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


# =============================================================================
# STAGE 2: TOPIC CLUSTERING
# =============================================================================


class Topic:
    def __init__(self, seed_title: dict, topic_id: int):
        self.id = topic_id
        self.titles = [seed_title]
        self.created_date = (
            seed_title["pubdate_utc"].date() if seed_title["pubdate_utc"] else None
        )
        self.emerged_date = None
        self.anchor_signals = set()
        self.anchors_locked = False
        self.signal_counts = Counter()
        self.daily_counts = Counter()
        self._add_signals(seed_title)

    def _extract_tokens(self, title: dict, for_matching: bool = False) -> set:
        tokens = set()
        for sig_type in SIGNAL_TYPES:
            for val in title.get(sig_type, []):
                normalized = val.upper() if sig_type == "persons" else val
                if (
                    for_matching
                    and sig_type == "persons"
                    and normalized in HIGH_FREQ_PERSONS
                ):
                    continue
                tokens.add("{}:{}".format(sig_type, normalized))
        return tokens

    def _add_signals(self, title: dict):
        for token in self._extract_tokens(title):
            self.signal_counts[token] += 1

        if title["pubdate_utc"]:
            self.daily_counts[title["pubdate_utc"].date()] += 1

        if not self.anchors_locked:
            threshold = max(1, len(self.titles) // 2)
            self.anchor_signals = set()
            for token, count in self.signal_counts.items():
                if count >= threshold:
                    sig_type, val = token.split(":", 1)
                    if sig_type == "persons" and val in HIGH_FREQ_PERSONS:
                        continue
                    self.anchor_signals.add(token)
            if len(self.titles) >= ANCHOR_LOCK_THRESHOLD:
                self.anchors_locked = True

        if self.emerged_date is None and len(self.titles) >= EMERGENCE_THRESHOLD:
            self.emerged_date = (
                title["pubdate_utc"].date() if title["pubdate_utc"] else None
            )

    def add_title(self, title: dict):
        self.titles.append(title)
        self._add_signals(title)

    def match_score(self, title: dict, weights: dict, discriminators: list) -> float:
        title_tokens = self._extract_tokens(title, for_matching=True)
        if not title_tokens:
            return 0.0

        title_by_type = defaultdict(set)
        for t in title_tokens:
            title_by_type[t.split(":")[0]].add(t)

        compare_set = (
            self.anchor_signals
            if self.anchors_locked
            else set(self.signal_counts.keys())
        )
        compare_set = {
            t
            for t in compare_set
            if not (t.startswith("persons:") and t.split(":")[1] in HIGH_FREQ_PERSONS)
        }

        if not compare_set:
            return 0.0

        if self.anchors_locked and discriminators:
            for sig_type in discriminators:
                anchor_sigs = {
                    t for t in self.anchor_signals if t.startswith(sig_type + ":")
                }
                title_sigs = title_by_type.get(sig_type, set())
                if anchor_sigs and title_sigs and not (anchor_sigs & title_sigs):
                    return 0.0

        overlap = title_tokens & compare_set
        if not overlap:
            return 0.0

        score = sum(weights.get(t.split(":")[0], 1.0) for t in overlap)
        max_score = sum(weights.get(t.split(":")[0], 1.0) for t in compare_set)
        return score / max_score if max_score > 0 else 0.0

    def get_anchor_summary(self) -> str:
        anchor_list = sorted(
            self.anchor_signals, key=lambda x: -self.signal_counts.get(x, 0)
        )
        return ", ".join(a.split(":")[1] for a in anchor_list[:4])

    def get_cooccurring(self) -> list:
        return [
            (t, c)
            for t, c in self.signal_counts.most_common(15)
            if t not in self.anchor_signals
        ][:8]

    def merge_from(self, other: "Topic"):
        """Absorb another topic into this one."""
        for title in other.titles:
            self.titles.append(title)
            for token in self._extract_tokens(title):
                self.signal_counts[token] += 1
            if title["pubdate_utc"]:
                self.daily_counts[title["pubdate_utc"].date()] += 1

        # Recalculate anchors from merged signals
        threshold = max(1, len(self.titles) // 2)
        self.anchor_signals = set()
        for token, count in self.signal_counts.items():
            if count >= threshold:
                sig_type, val = token.split(":", 1)
                if sig_type == "persons" and val in HIGH_FREQ_PERSONS:
                    continue
                self.anchor_signals.add(token)

        # Update dates
        if other.created_date and (
            not self.created_date or other.created_date < self.created_date
        ):
            self.created_date = other.created_date
        if other.emerged_date and (
            not self.emerged_date or other.emerged_date < self.emerged_date
        ):
            self.emerged_date = other.emerged_date
        if self.emerged_date is None and len(self.titles) >= EMERGENCE_THRESHOLD:
            dates = [t["pubdate_utc"] for t in self.titles if t["pubdate_utc"]]
            if dates:
                self.emerged_date = min(dates).date()


def merge_topics_pass(topics: list) -> list:
    """
    Post-clustering merge: combine topics that share anchor signals.
    Topics sharing 1+ anchor are merged (larger absorbs smaller).
    """
    if len(topics) <= 1:
        return topics

    merged = []
    absorbed = set()

    # Sort by size descending (larger topics absorb smaller)
    sorted_topics = sorted(topics, key=lambda t: -len(t.titles))

    for i, topic_a in enumerate(sorted_topics):
        if i in absorbed:
            continue

        for j, topic_b in enumerate(sorted_topics[i + 1 :], start=i + 1):
            if j in absorbed:
                continue

            # Check for shared anchors
            shared = topic_a.anchor_signals & topic_b.anchor_signals
            if shared:
                topic_a.merge_from(topic_b)
                absorbed.add(j)

        merged.append(topic_a)

    return merged


def cluster_bucket(titles: list, weights: dict, discriminators: list) -> list:
    if not titles:
        return []
    topics = []
    topic_id = 0
    for title in titles:
        best_topic = None
        best_score = JOIN_THRESHOLD
        for topic in topics:
            score = topic.match_score(title, weights, discriminators)
            if score > best_score:
                best_score = score
                best_topic = topic
        if best_topic:
            best_topic.add_title(title)
        else:
            topic_id += 1
            topics.append(Topic(title, topic_id))
    return topics


# =============================================================================
# ANALYSIS
# =============================================================================


def analyze_bucket(bucket_name: str, topics: list, bucket_key: str = None):
    if not topics:
        return
    emerged = [t for t in topics if t.emerged_date]
    sizes = sorted([len(t.titles) for t in topics], reverse=True)

    header = bucket_name + (" [{}]".format(bucket_key) if bucket_key else "")
    print("\n" + "=" * 60)
    print(header)
    print("=" * 60)
    print(
        "Topics: {} ({} emerged), Titles: {}".format(
            len(topics), len(emerged), sum(sizes)
        )
    )

    for i, topic in enumerate(sorted(emerged, key=lambda t: -len(t.titles))[:8]):
        anchor_str = topic.get_anchor_summary() or "misc"
        cooccur = ", ".join(
            "+{}".format(t.split(":")[1]) for t, c in topic.get_cooccurring()[:3]
        )
        print("\n  {}. {} titles - {}".format(i + 1, len(topic.titles), anchor_str))
        if cooccur:
            print("     +{}".format(cooccur))


# =============================================================================
# DATABASE WRITE
# =============================================================================


def write_all_topics(conn, all_results: dict, ctm_id: str, min_titles: int = 2) -> int:
    cur = conn.cursor()
    cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))
    if cur.rowcount > 0:
        print("Cleared {} old events".format(cur.rowcount))

    written = domestic_count = bilateral_count = 0

    def write_topic(topic, event_type, bucket_key=None):
        nonlocal written, domestic_count, bilateral_count
        if len(topic.titles) < min_titles:
            return

        event_id = str(uuid.uuid4())
        dates = [t["pubdate_utc"] for t in topic.titles if t["pubdate_utc"]]
        first_date = min(dates).date() if dates else None
        last_date = max(dates).date() if dates else None

        anchor_list = sorted(
            topic.anchor_signals, key=lambda x: -topic.signal_counts.get(x, 0)
        )
        summary = (
            "Topic: {}".format(", ".join(a.split(":")[1] for a in anchor_list[:4]))
            or "misc"
        )

        cur.execute(
            """
            INSERT INTO events_v3 (id, ctm_id, date, first_seen, summary, source_batch_count,
                last_active, anchor_signals, cooccurring_signals, emerged_date, event_type, bucket_key)
            VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s)
        """,
            (
                event_id,
                ctm_id,
                first_date,
                summary,
                len(topic.titles),
                last_date,
                list(topic.anchor_signals)[:10],
                [t for t, c in topic.get_cooccurring()[:10]],
                topic.emerged_date,
                event_type,
                bucket_key,
            ),
        )

        for title in topic.titles:
            cur.execute(
                "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (event_id, title["id"]),
            )
        written += 1
        if event_type == "domestic":
            domestic_count += 1
        else:
            bilateral_count += 1

    for topic in all_results.get("domestic", []):
        write_topic(topic, "domestic")
    for country, topics in all_results.get("bilateral", {}).items():
        for topic in topics:
            write_topic(topic, "bilateral", country)
    for topic in all_results.get("other_international", []):
        write_topic(topic, "other_international")

    conn.commit()
    print("  Domestic: {}, Bilateral: {}".format(domestic_count, bilateral_count))
    return written


# =============================================================================
# MAIN
# =============================================================================


def process_ctm(ctm_id: str, dry_run: bool = True):
    conn = get_connection()
    ctm_info = get_ctm_info(conn, ctm_id)
    if not ctm_info:
        print("CTM not found")
        conn.close()
        return

    home_centroid_id = ctm_info["centroid_id"]
    print("CTM: {} / {}".format(home_centroid_id, ctm_info["track"]))

    weights = TRACK_WEIGHTS.get(ctm_info["track"], TRACK_WEIGHTS["default"])
    discriminators = TRACK_DISCRIMINATORS.get(ctm_info["track"], [])

    titles = load_titles_with_bucket_info(conn, ctm_id)
    if not titles:
        print("No titles")
        conn.close()
        return

    publisher_patterns = load_publisher_patterns(conn)
    for title in titles:
        title["orgs"] = filter_publisher_signals(
            title.get("orgs", []), publisher_patterns
        )

    print(
        "Titles: {} ({} to {})".format(
            len(titles),
            titles[0]["pubdate_utc"].date(),
            titles[-1]["pubdate_utc"].date(),
        )
    )

    # STAGE 1: Bucket by centroid_ids
    print("\n--- STAGE 1: Geographic Bucketing ---")
    buckets = bucket_titles(titles, home_centroid_id)
    print("Domestic: {}".format(len(buckets["domestic"])))
    for c in sorted(buckets["bilateral"], key=lambda x: -len(buckets["bilateral"][x])):
        print("  {}: {}".format(c, len(buckets["bilateral"][c])))
    print("Other Intl: {}".format(len(buckets["other_international"])))

    # STAGE 2: Cluster + Merge
    print("\n--- STAGE 2: Topic Clustering + Merge ---")
    all_results = {"domestic": [], "bilateral": {}, "other_international": []}

    domestic_topics = cluster_bucket(buckets["domestic"], weights, discriminators)
    all_results["domestic"] = merge_topics_pass(domestic_topics)
    analyze_bucket("DOMESTIC", all_results["domestic"])

    for country in sorted(
        buckets["bilateral"], key=lambda x: -len(buckets["bilateral"][x])
    ):
        bilateral_topics = cluster_bucket(
            buckets["bilateral"][country], weights, discriminators
        )
        all_results["bilateral"][country] = merge_topics_pass(bilateral_topics)
        analyze_bucket("BILATERAL", all_results["bilateral"][country], country)

    if buckets["other_international"]:
        other_topics = cluster_bucket(
            buckets["other_international"], weights, discriminators
        )
        all_results["other_international"] = merge_topics_pass(other_topics)
        analyze_bucket("OTHER INTL", all_results["other_international"])

    if not dry_run:
        print("\n--- Writing to DB ---")
        write_all_topics(conn, all_results, ctm_id)
    else:
        print("\n(DRY RUN)")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ctm-id", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    process_ctm(args.ctm_id, dry_run=not args.write)
