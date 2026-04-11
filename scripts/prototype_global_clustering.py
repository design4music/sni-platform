"""
Prototype: Global clustering (no bucket partitioning)

Clusters all titles in a CTM into one pool, then assigns bucket_key
to each cluster post-hoc based on the dominant foreign centroid.

This tests the hypothesis that removing bucket partitioning eliminates
cross-bucket duplicates while the existing safeguards (anchor locking,
discriminators, specificity gates) prevent mega-cluster drift.

Usage:
    python scripts/prototype_global_clustering.py AMERICAS-USA geo_politics --dry-run
    python scripts/prototype_global_clustering.py AMERICAS-USA geo_politics --write
    python scripts/prototype_global_clustering.py ASIA-CHINA geo_economy --write
"""

import argparse
import re
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import (
    HIGH_FREQ_ORGS,
    HIGH_FREQ_PERSONS,
    SIGNAL_TYPES,
    config,
    get_track_discriminators,
)
from core.publisher_filter import filter_publisher_signals, load_publisher_patterns

# --- Config ---

MONTH = "2026-03-01"
ANCHOR_LOCK_THRESHOLD = 5
EMERGENCE_THRESHOLD = 3
JOIN_THRESHOLD = 0.25

# GEO centroid prefixes (vs SYS- systemic centroids)
GEO_PREFIXES = (
    "AMERICAS-",
    "EUROPE-",
    "ASIA-",
    "AFRICA-",
    "MIDEAST-",
    "OCEANIA-",
)


def is_geo_centroid(c):
    return any(c.startswith(p) for p in GEO_PREFIXES)


# Structural label types -- scalar fields from title_labels
# These are the most consistent signals (99.99% coverage)
STRUCTURAL_LABELS = ["actor", "target", "action_class", "subject", "sector", "domain"]

# High-frequency structural values to skip (too generic to discriminate)
STRUCTURAL_SKIP = {
    "actor": {"NONE", "MEDIA_OUTLET", "MULTIPLE_STATES"},
    "target": {"NONE"},
    "subject": {"BILATERAL_RELATIONS"},
    "action_class": set(),
    "sector": set(),
    "domain": set(),
}

# Weights for all signal types (structural + entity + geo)
ALL_WEIGHTS = {
    # Structural labels (scalar, 99.99% coverage)
    "actor": 2.0,
    "target": 2.5,
    "action_class": 1.5,
    "subject": 1.5,
    "sector": 0.5,
    "domain": 0.3,
    # Entity signals (array, variable coverage)
    "persons": 2.5,
    "orgs": 1.5,
    "places": 2.0,
    "commodities": 2.0,
    "policies": 2.0,
    "systems": 1.5,
    "named_events": 3.0,
    # Geographic context
    "centroid": 1.0,
}


# --- IncrementalTopic (uses ALL labels, no MAX_TOPIC_SIZE) ---


class IncrementalTopic:
    def __init__(self, seed_title, topic_id):
        self.id = topic_id
        self.titles = [seed_title]
        self.anchor_signals = set()
        self.anchors_locked = False
        self.signal_counts = Counter()
        self._add_signals(seed_title)

    def _extract_tokens(self, title, for_matching=False):
        tokens = set()

        # 1. Entity signals (array fields): persons, orgs, places, etc.
        for sig_type in SIGNAL_TYPES:
            for val in title.get(sig_type, []):
                normalized = val.upper() if sig_type == "persons" else val
                if for_matching:
                    if sig_type == "persons" and normalized in HIGH_FREQ_PERSONS:
                        continue
                    if sig_type == "orgs" and normalized in HIGH_FREQ_ORGS:
                        continue
                tokens.add("%s:%s" % (sig_type, normalized))

        # 2. Structural labels (scalar fields): actor, target, subject, etc.
        for label_type in STRUCTURAL_LABELS:
            val = title.get(label_type)
            if not val:
                continue
            # Target/actor can be compound ("US,IL") -- split
            if "," in val:
                parts = [p.strip() for p in val.split(",")]
                for part in parts:
                    if for_matching and part in STRUCTURAL_SKIP.get(label_type, set()):
                        continue
                    tokens.add("%s:%s" % (label_type, part))
            else:
                if for_matching and val in STRUCTURAL_SKIP.get(label_type, set()):
                    continue
                tokens.add("%s:%s" % (label_type, val))

        # 3. Centroid context (which countries is this title about)
        home = title.get("_home_centroid", "")
        for cid in title.get("centroid_ids", []):
            if cid != home:
                tokens.add("centroid:%s" % cid)

        return tokens

    def _add_signals(self, title):
        tokens = self._extract_tokens(title, for_matching=False)
        for token in tokens:
            self.signal_counts[token] += 1

        if not self.anchors_locked:
            threshold = max(1, len(self.titles) // 2)
            self.anchor_signals = set()
            for token, count in self.signal_counts.items():
                if count >= threshold:
                    sig_type, val = token.split(":", 1)
                    if sig_type == "persons" and val in HIGH_FREQ_PERSONS:
                        continue
                    if sig_type == "orgs" and val in HIGH_FREQ_ORGS:
                        continue
                    self.anchor_signals.add(token)
            if len(self.titles) >= ANCHOR_LOCK_THRESHOLD:
                self.anchors_locked = True

    def add_title(self, title):
        self.titles.append(title)
        self._add_signals(title)

    def match_score(self, title, weights, discriminators):
        title_tokens = self._extract_tokens(title, for_matching=True)
        if not title_tokens:
            return 0.0

        # Discriminator conflicts: hard reject if anchor and title disagree
        # on key signal types (prevents unrelated story merging)
        if self.anchors_locked:
            # Always discriminate on target (most important for story identity)
            for sig_type in ["target", "subject"] + discriminators:
                anchor_sigs = {
                    t for t in self.anchor_signals if t.startswith(sig_type + ":")
                }
                title_sigs = {t for t in title_tokens if t.startswith(sig_type + ":")}
                if anchor_sigs and title_sigs and not (anchor_sigs & title_sigs):
                    return 0.0

        # Large-topic specificity gate: require a specific signal overlap
        if self.anchors_locked and len(self.titles) >= 30:
            specific_types = {
                "places",
                "named_events",
                "commodities",
                "policies",
                "actor",
                "action_class",
            }
            has_specific = any(
                token in self.anchor_signals
                for token in title_tokens
                if token.split(":")[0] in specific_types
            )
            if not has_specific:
                frequent = {
                    t
                    for t, c in self.signal_counts.items()
                    if c >= len(self.titles) // 4 and t.split(":")[0] in specific_types
                }
                if frequent and not (title_tokens & frequent):
                    return 0.0

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

        # Weighted score using ALL_WEIGHTS
        score = 0.0
        for token in overlap:
            sig_type = token.split(":")[0]
            weight = ALL_WEIGHTS.get(sig_type, 1.0)
            anchor_boost = 1.5 if token in self.anchor_signals else 1.0
            score += weight * anchor_boost

        max_score = sum(
            ALL_WEIGHTS.get(t.split(":")[0], 1.0) * 1.5 for t in compare_set
        )
        return score / max_score if max_score > 0 else 0.0

    def get_anchor_summary(self):
        anchor_list = [(t, self.signal_counts[t]) for t in self.anchor_signals]
        anchor_list.sort(key=lambda x: -x[1])
        parts = [t.split(":")[1] for t, _ in anchor_list[:4]]
        return ", ".join(parts) if parts else "misc"


# --- Global clustering ---


def cluster_globally(titles, discriminators):
    """Cluster ALL titles in one pool. No bucket partitioning."""
    topics = []
    topic_counter = 0

    for i, title in enumerate(titles):
        best_topic = None
        best_score = JOIN_THRESHOLD

        for topic in topics:
            score = topic.match_score(title, ALL_WEIGHTS, discriminators)
            if score > best_score:
                best_score = score
                best_topic = topic

        if best_topic:
            best_topic.add_title(title)
        else:
            topic_counter += 1
            topics.append(IncrementalTopic(title, topic_counter))

        if (i + 1) % 1000 == 0:
            emerged = sum(1 for t in topics if len(t.titles) >= EMERGENCE_THRESHOLD)
            print(
                "  %d/%d titles, %d topics (%d emerged)"
                % (
                    i + 1,
                    len(titles),
                    len(topics),
                    emerged,
                )
            )

    return topics


# --- Post-hoc bucket assignment ---


def assign_bucket(topic, home_centroid):
    """Assign event_type and bucket_key to a cluster based on its titles' centroids."""
    foreign_counts = Counter()
    domestic_count = 0

    for title in topic.titles:
        centroid_ids = title.get("centroid_ids", [])
        foreign_geo = [
            c for c in centroid_ids if c != home_centroid and is_geo_centroid(c)
        ]

        if not foreign_geo:
            domestic_count += 1
        else:
            for c in foreign_geo:
                foreign_counts[c] += 1

    if not foreign_counts or domestic_count > sum(foreign_counts.values()):
        return "domestic", None

    # Dominant foreign centroid
    top_foreign, _ = foreign_counts.most_common(1)[0]
    return "bilateral", top_foreign


# --- Central title selection ---


def pick_central_title(topic):
    """Pick the most representative English title as cluster title."""
    STOP = frozenset(
        "the a an in of on for to and is are was were with from at by as its it be "
        "has had have that this or but not no new over after into about up out more "
        "says said will could would may amid us set than been also".split()
    )

    def tokenize(text):
        words = set(re.findall(r"[a-z][a-z0-9]+", (text or "").lower()))
        return words - STOP

    # Build corpus word frequencies
    all_words = Counter()
    title_data = []
    for t in topic.titles:
        words = tokenize(t["title_display"])
        title_data.append((t, words))
        all_words.update(words)

    if not title_data:
        return topic.titles[0]["title_display"]

    # Score each title: sum of word frequencies (more common words = more central)
    best_score = -1
    best_title = topic.titles[0]["title_display"]

    for t, words in title_data:
        if not words:
            continue
        # Prefer English titles
        lang = t.get("detected_language", "en")
        lang_boost = 1.0 if lang == "en" else 0.5
        score = sum(all_words[w] for w in words) / len(words) * lang_boost
        if score > best_score:
            best_score = score
            best_title = t["title_display"]

    return best_title


# --- DB operations ---


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def load_titles(conn, ctm_id, home_centroid):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT t.id, t.title_display, t.pubdate_utc, t.centroid_ids,
               t.detected_language,
               tl.actor, tl.target, tl.action_class, tl.subject,
               tl.sector, tl.domain,
               tl.persons, tl.orgs, tl.places, tl.commodities,
               tl.policies, tl.systems, tl.named_events,
               tl.importance_score
        FROM titles_v3 t
        JOIN title_assignments ta ON t.id = ta.title_id
        LEFT JOIN title_labels tl ON t.id = tl.title_id
        WHERE ta.ctm_id = %s
        ORDER BY t.pubdate_utc ASC
    """,
        (ctm_id,),
    )
    rows = cur.fetchall()
    cur.close()
    titles = []
    for r in rows:
        titles.append(
            {
                "id": str(r[0]),
                "title_display": r[1],
                "pubdate_utc": r[2],
                "centroid_ids": r[3] or [],
                "detected_language": r[4] or "en",
                # Structural labels
                "actor": r[5] or "",
                "target": r[6] or "",
                "action_class": r[7] or "",
                "subject": r[8] or "",
                "sector": r[9] or "",
                "domain": r[10] or "",
                # Entity signals
                "persons": r[11] or [],
                "orgs": r[12] or [],
                "places": r[13] or [],
                "commodities": r[14] or [],
                "policies": r[15] or [],
                "systems": r[16] or [],
                "named_events": r[17] or [],
                # Importance
                "importance_score": r[18] or 0.0,
                # Context for centroid token extraction
                "_home_centroid": home_centroid,
            }
        )
    return titles


def wipe_ctm_events(conn, ctm_id):
    """Delete all events, families, and links for a CTM."""
    cur = conn.cursor()
    # Clear merged_into refs
    cur.execute(
        "UPDATE events_v3 SET merged_into = NULL "
        "WHERE merged_into IN (SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (ctm_id,),
    )
    # Clear family links
    cur.execute(
        "UPDATE events_v3 SET family_id = NULL WHERE ctm_id = %s",
        (ctm_id,),
    )
    # Delete families
    cur.execute("DELETE FROM event_families WHERE ctm_id = %s", (ctm_id,))
    # Delete title links
    cur.execute(
        "DELETE FROM event_v3_titles WHERE event_id IN "
        "(SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (ctm_id,),
    )
    # Delete events
    cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))
    conn.commit()
    cur.close()


def write_topics(conn, ctm_id, topics, home_centroid):
    """Write clustered topics to events_v3."""
    cur = conn.cursor()
    written = 0
    catchall_titles = []

    for topic in topics:
        if len(topic.titles) < 2:
            catchall_titles.extend(topic.titles)
            continue

        event_type, bucket_key = assign_bucket(topic, home_centroid)
        event_id = str(uuid.uuid4())
        dates = [t["pubdate_utc"] for t in topic.titles if t["pubdate_utc"]]
        first_date = min(dates).date() if dates else None
        last_date = max(dates).date() if dates else None
        title = pick_central_title(topic)

        # Truncate title safely
        if len(title) > 500:
            title = title[:497] + "..."

        cur.execute(
            """INSERT INTO events_v3
               (id, ctm_id, date, first_seen, title, event_type, bucket_key,
                source_batch_count, is_catchall, last_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, false, %s)""",
            (
                event_id,
                ctm_id,
                first_date,
                first_date,
                title,
                event_type,
                bucket_key,
                len(topic.titles),
                last_date,
            ),
        )

        for t in topic.titles:
            cur.execute(
                "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s) "
                "ON CONFLICT DO NOTHING",
                (event_id, t["id"]),
            )

        written += 1

    # Catchall per bucket
    if catchall_titles:
        # Group catchall by bucket
        domestic_ca = []
        bilateral_ca = defaultdict(list)
        for t in catchall_titles:
            foreign_geo = [
                c
                for c in t.get("centroid_ids", [])
                if c != home_centroid and is_geo_centroid(c)
            ]
            if not foreign_geo:
                domestic_ca.append(t)
            else:
                bilateral_ca[foreign_geo[0]].append(t)

        for ca_titles, ev_type, bk in [(domestic_ca, "domestic", None)] + [
            (v, "bilateral", k) for k, v in bilateral_ca.items()
        ]:
            if not ca_titles:
                continue
            ca_id = str(uuid.uuid4())
            dates = [t["pubdate_utc"] for t in ca_titles if t["pubdate_utc"]]
            first_date = min(dates).date() if dates else None
            cur.execute(
                """INSERT INTO events_v3
                   (id, ctm_id, date, first_seen, title, event_type, bucket_key,
                    source_batch_count, is_catchall)
                VALUES (%s, %s, %s, %s, 'Other coverage', %s, %s, %s, true)""",
                (ca_id, ctm_id, first_date, first_date, ev_type, bk, len(ca_titles)),
            )
            for t in ca_titles:
                cur.execute(
                    "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s) "
                    "ON CONFLICT DO NOTHING",
                    (ca_id, t["id"]),
                )

    conn.commit()
    cur.close()
    return written


# --- Main ---


def main():
    parser = argparse.ArgumentParser(
        description="Prototype: global clustering (no buckets)"
    )
    parser.add_argument("centroid", help="Centroid ID (e.g., AMERICAS-USA)")
    parser.add_argument("track", help="Track (e.g., geo_politics)")
    parser.add_argument("--dry-run", action="store_true", help="Report only")
    parser.add_argument(
        "--write", action="store_true", help="Write to DB (destructive)"
    )
    parser.add_argument("--month", default=MONTH, help="Month (YYYY-MM-DD)")
    args = parser.parse_args()

    if not args.dry_run and not args.write:
        print("Specify --dry-run or --write")
        sys.exit(1)

    conn = get_connection()
    cur = conn.cursor()

    # Get CTM
    cur.execute(
        "SELECT id, title_count FROM ctm WHERE centroid_id = %s AND track = %s AND month = %s",
        (args.centroid, args.track, args.month),
    )
    row = cur.fetchone()
    if not row:
        print("CTM not found: %s %s %s" % (args.centroid, args.track, args.month))
        return
    ctm_id, title_count = str(row[0]), row[1]
    cur.close()

    print("=== GLOBAL CLUSTERING PROTOTYPE ===")
    print(
        "  %s / %s / %s (%d titles)"
        % (args.centroid, args.track, args.month, title_count)
    )

    # Load titles with ALL labels
    titles = load_titles(conn, ctm_id, args.centroid)
    print("  Loaded %d titles" % len(titles))

    # Filter publisher signals
    publisher_patterns = load_publisher_patterns(conn)
    for t in titles:
        t["orgs"] = filter_publisher_signals(t.get("orgs", []), publisher_patterns)

    discriminators = list(get_track_discriminators(args.track).keys())
    print("  Discriminators: %s" % discriminators)

    # Signal coverage check
    has_actor = sum(1 for t in titles if t["actor"] and t["actor"] != "NONE")
    has_target = sum(1 for t in titles if t["target"] and t["target"] != "NONE")
    has_entity = sum(1 for t in titles if t["persons"] or t["orgs"] or t["places"])
    print(
        "  Signal coverage: actor=%d target=%d entity=%d (of %d)"
        % (
            has_actor,
            has_target,
            has_entity,
            len(titles),
        )
    )

    # CLUSTER GLOBALLY with ALL signals
    print("\nClustering %d titles globally (all labels, no buckets)..." % len(titles))
    topics = cluster_globally(titles, discriminators)

    emerged = [t for t in topics if len(t.titles) >= 2]
    single = [t for t in topics if len(t.titles) == 1]
    total_in_topics = sum(len(t.titles) for t in emerged)

    print("\n=== RESULTS ===")
    print(
        "  %d topics (%d emerged, %d single-title)"
        % (len(topics), len(emerged), len(single))
    )
    print("  %d titles in topics, %d catchall" % (total_in_topics, len(single)))
    print(
        "  Catchall rate: %.1f%%" % (100 * len(single) / len(titles) if titles else 0)
    )

    # Size distribution
    sizes = sorted([len(t.titles) for t in emerged], reverse=True)
    print("\n  Size distribution:")
    print("    Largest: %d" % (sizes[0] if sizes else 0))
    print("    Top 10: %s" % sizes[:10])
    print("    >100 titles: %d topics" % sum(1 for s in sizes if s > 100))
    print("    >50 titles: %d topics" % sum(1 for s in sizes if s > 50))
    print("    >20 titles: %d topics" % sum(1 for s in sizes if s > 20))

    # Bucket distribution of emerged topics
    bucket_dist = Counter()
    multi_bucket = 0
    for topic in emerged:
        event_type, bucket_key = assign_bucket(topic, args.centroid)
        label = event_type if not bucket_key else "bilateral:%s" % bucket_key
        bucket_dist[label] += 1
        # Check if topic has titles from multiple buckets
        foreign_buckets = set()
        for t in topic.titles:
            foreign_geo = [
                c
                for c in t.get("centroid_ids", [])
                if c != args.centroid and is_geo_centroid(c)
            ]
            if foreign_geo:
                foreign_buckets.add(foreign_geo[0])
        if len(foreign_buckets) > 1:
            multi_bucket += 1

    print("\n  Bucket assignment (post-hoc):")
    for label, cnt in bucket_dist.most_common(15):
        print("    %-30s %d topics" % (label, cnt))
    if len(bucket_dist) > 15:
        print("    ... +%d more" % (len(bucket_dist) - 15))
    print("  Multi-bucket topics (cross-bucket merge achieved): %d" % multi_bucket)

    # Top topics
    emerged.sort(key=lambda t: -len(t.titles))
    print("\n  Top 20 topics:")
    for i, topic in enumerate(emerged[:20]):
        event_type, bucket_key = assign_bucket(topic, args.centroid)
        bk_label = bucket_key or "domestic"
        # Count unique buckets
        foreign_buckets = set()
        for t in topic.titles:
            foreign_geo = [
                c
                for c in t.get("centroid_ids", [])
                if c != args.centroid and is_geo_centroid(c)
            ]
            if foreign_geo:
                for fg in foreign_geo:
                    foreign_buckets.add(fg)
        bk_count = len(foreign_buckets)
        multi_str = " [%d buckets]" % bk_count if bk_count > 1 else ""
        central = pick_central_title(topic)
        # Truncate for display
        if len(central) > 80:
            central = central[:77] + "..."
        print(
            "    %3d. %4d titles  %-20s %s%s"
            % (
                i + 1,
                len(topic.titles),
                bk_label,
                central,
                multi_str,
            )
        )

    if args.dry_run:
        print("\nDRY RUN -- no DB changes. Use --write to apply.")
        conn.close()
        return

    # WRITE
    print("\nWiping existing events for CTM %s..." % ctm_id[:8])
    wipe_ctm_events(conn, ctm_id)
    print("Writing %d topics..." % len(emerged))
    written = write_topics(conn, ctm_id, topics, args.centroid)
    print("Wrote %d events + catchalls" % written)

    # Run family assembly
    print("\nRunning family assembly...")
    from pipeline.phase_4.assemble_families import process_ctm

    process_ctm(ctm_id=ctm_id, force=True)

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
