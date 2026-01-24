"""
Mechanical event clustering using labels + temporal patterns.

Clustering hierarchy:
1. BUCKET: domestic / bilateral-{country} (from target OR actor nationality)
2. LABEL: (actor, action_class) within bucket - one event per combination
3. TEMPORAL: spike detection marks high-activity events

Usage:
    python pipeline/phase_4/cluster_events_mechanical.py --centroid AMERICAS-USA --track geo_economy
    python pipeline/phase_4/cluster_events_mechanical.py --centroid AMERICAS-USA --track geo_economy --write
"""

import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2
from dotenv import load_dotenv

from core.ontology import GEO_ALIAS_TO_ISO

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "sni"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def load_titles_with_labels(conn, centroid_id: str, track: str) -> list[dict]:
    """Load titles with labels for a CTM, deduplicating identical titles."""
    cur = conn.cursor()
    # Use DISTINCT ON to keep only the first occurrence of each title_display
    # (earliest by pubdate_utc, then created_at)
    cur.execute(
        """
        SELECT
            t.id, t.title_display, t.matched_aliases, DATE(t.pubdate_utc) as pub_date,
            tl.actor, tl.action_class, tl.domain, tl.target, tl.actor_entity
        FROM (
            SELECT DISTINCT ON (title_display)
                id, title_display, matched_aliases, pubdate_utc
            FROM titles_v3
            WHERE id IN (
                SELECT ta.title_id
                FROM title_assignments ta
                JOIN ctm c ON c.id = ta.ctm_id
                WHERE c.centroid_id = %s AND c.track = %s
            )
            ORDER BY title_display, pubdate_utc ASC, created_at ASC
        ) t
        JOIN title_labels tl ON tl.title_id = t.id
        ORDER BY t.pubdate_utc DESC
    """,
        (centroid_id, track),
    )

    rows = cur.fetchall()
    return [
        {
            "id": str(r[0]),
            "title": r[1],
            "aliases": r[2] or [],
            "pub_date": str(r[3]),
            "actor": r[4],
            "action_class": r[5],
            "domain": r[6],
            "target": r[7],
            "actor_entity": r[8],
        }
        for r in rows
    ]


def get_geo_bucket_from_aliases(aliases: list, home_prefix: str) -> str:
    """
    Check if aliases suggest a geographic bucket.
    Uses GEO_ALIAS_TO_ISO from ontology.
    Returns bucket name or None.
    """
    for alias in aliases:
        alias_lower = str(alias).lower()
        if alias_lower in GEO_ALIAS_TO_ISO:
            iso = GEO_ALIAS_TO_ISO[alias_lower]
            if iso != home_prefix and iso != "US":  # Don't bucket to home country
                return "bilateral_%s" % iso
    return None


def extract_country_from_actor(actor: str) -> str:
    """Extract country code from actor like 'CN_EXECUTIVE' -> 'CN'."""
    if not actor or actor == "UNKNOWN":
        return None
    # Check for country prefix (XX_SOMETHING)
    if "_" in actor and len(actor.split("_")[0]) == 2:
        return actor.split("_")[0]
    # Regional blocs as actors
    if actor in ["EU", "NATO", "BRICS", "G7", "MERCOSUR", "IGO"]:
        return actor
    return None


def assign_bucket(title: dict, centroid_id: str) -> str:
    """Assign title to bucket based on target, actor nationality, OR aliases."""
    target = title["target"]
    actor = title["actor"]
    aliases = title.get("aliases", [])

    # Extract home country from centroid (AMERICAS-USA -> US)
    centroid_country = centroid_id.split("-")[-1]
    home_prefix = "US" if centroid_country == "USA" else centroid_country[:2]

    # 1. Check target first - explicit foreign target = bilateral
    if target and target != "-":
        # Home country institutions as target = domestic
        if target.startswith(home_prefix + "_") or target == home_prefix:
            pass  # Fall through to check actor/aliases
        # ISO codes or regional blocs = bilateral
        elif len(target) == 2 or target in ["NATO", "EU", "BRICS", "G7", "MERCOSUR"]:
            return "bilateral_%s" % target
        # Multi-target: use first
        elif "," in target:
            first = target.split(",")[0]
            return "bilateral_%s" % first

    # 2. Check actor nationality - foreign actor = bilateral by actor origin
    actor_country = extract_country_from_actor(actor)
    if actor_country and actor_country != home_prefix:
        return "bilateral_%s" % actor_country

    # 3. Check aliases for geographic signals (e.g., "greenland" -> bilateral_GL)
    alias_bucket = get_geo_bucket_from_aliases(aliases, home_prefix)
    if alias_bucket:
        return alias_bucket

    # 4. Default to domestic
    return "domestic"


# Actor types that should be clustered by entity (not by action)
# These need LLM to extract the specific entity name
ENTITY_ACTORS = {"CORPORATION", "ARMED_GROUP", "NGO", "MEDIA_OUTLET", "UNKNOWN"}

# Actor suffixes where the actor itself IS the entity (consolidate all actions)
# e.g., US_CENTRAL_BANK is always "the Fed" - all their actions are one event
CONSOLIDATED_ACTOR_SUFFIXES = {"_CENTRAL_BANK"}

# Known corporate entities for target-based grouping
# When action is LEGAL_CONTESTATION and target matches, group with corporation
KNOWN_CORPORATE_TARGETS = {
    "META",
    "OPENAI",
    "NVIDIA",
    "APPLE",
    "GOOGLE",
    "AMAZON",
    "MICROSOFT",
    "TESLA",
    "BOEING",
    "JPMORGAN",
    "GOLDMAN SACHS",
    "BLACKROCK",
    "SPACEX",
    "NETFLIX",
    "DISNEY",
    "EXXON",
    "CHEVRON",
    "WALMART",
    "INTEL",
    "AMD",
}

# Institutional entities - cluster ALL titles about this entity together
# Whether as actor OR as target, they become one event
INSTITUTIONAL_ENTITIES = {
    "US_CENTRAL_BANK",
    "US_JUDICIARY",
    "US_LEGISLATURE",
    "EU_CENTRAL_BANK",
    "CN_CENTRAL_BANK",
    "UK_CENTRAL_BANK",
    "JP_CENTRAL_BANK",
}


def should_consolidate_actor(actor: str) -> bool:
    """Check if actor should have all actions consolidated into one event."""
    for suffix in CONSOLIDATED_ACTOR_SUFFIXES:
        if actor.endswith(suffix):
            return True
    return False


def get_institutional_entity(actor: str, target: str) -> str:
    """Check if actor or target is an institutional entity."""
    # Check if actor IS an institution
    if actor in INSTITUTIONAL_ENTITIES:
        return actor
    # Check consolidated actor suffixes (e.g., XX_CENTRAL_BANK)
    for suffix in CONSOLIDATED_ACTOR_SUFFIXES:
        if actor and actor.endswith(suffix):
            return actor
    # Check if target is an institution
    if target and target in INSTITUTIONAL_ENTITIES:
        return target
    return None


def get_corporate_entity(actor: str, entity: str, target: str, action: str) -> str:
    """Check if this title is about a specific corporation."""
    # Actor is CORPORATION with entity
    if actor in ENTITY_ACTORS and entity:
        return entity.upper()
    # Target is a known corporation (e.g., LEGAL_CONTESTATION -> META)
    if target:
        target_upper = target.upper()
        if target_upper in KNOWN_CORPORATE_TARGETS:
            return target_upper
    return None


def cluster_by_labels(titles: list[dict], min_cluster_size: int = 3) -> dict:
    """Cluster titles by entity (for institutions/corporations) or by action.

    Entity-centric clustering (takes priority):
    1. INSTITUTIONAL entity (as actor OR target) -> one event per institution
    2. CORPORATE entity (actor_entity OR target) -> one event per corporation

    Action-based clustering (fallback):
    3. All other actors -> group by action_class
    """
    clusters = defaultdict(list)
    for t in titles:
        actor = t["actor"]
        action = t["action_class"]
        entity = t.get("actor_entity")
        target = t.get("target")

        # Rule 1: Institutional entity (actor or target) -> cluster by institution
        inst_entity = get_institutional_entity(actor, target)
        if inst_entity:
            key = ("INSTITUTION", inst_entity)
        # Rule 2: Corporate entity -> cluster by corporation
        else:
            corp_entity = get_corporate_entity(actor, entity, target, action)
            if corp_entity:
                key = ("CORPORATION", corp_entity)
            # Rule 3: Standard grouping by action
            else:
                key = ("ACTION", actor, action)

        clusters[key].append(t)

    # Filter by min size
    return {k: v for k, v in clusters.items() if len(v) >= min_cluster_size}


def detect_spike_days(titles: list[dict], threshold: float = 2.0) -> set:
    """Detect days with activity spike (>threshold x average)."""
    daily_counts = defaultdict(int)
    for t in titles:
        daily_counts[t["pub_date"]] += 1

    if not daily_counts:
        return set()

    avg = sum(daily_counts.values()) / len(daily_counts)
    return {day for day, cnt in daily_counts.items() if cnt > threshold * avg}


def split_by_spike(
    titles: list[dict], spike_days: set, min_size: int = 3
) -> list[list[dict]]:
    """
    Split titles into spike vs non-spike groups.
    Returns list of title groups, each large enough to be an event.
    """
    spike_titles = [t for t in titles if t["pub_date"] in spike_days]
    non_spike_titles = [t for t in titles if t["pub_date"] not in spike_days]

    groups = []
    if len(spike_titles) >= min_size:
        groups.append(spike_titles)
    if len(non_spike_titles) >= min_size:
        groups.append(non_spike_titles)

    # If splitting didn't work, return original
    if not groups:
        return [titles]

    return groups


def create_event(
    bucket_name: str,
    actor: str,
    actor_entity: str,
    action: str,
    titles: list[dict],
    is_spike_group: bool = False,
) -> dict:
    """Create event dict from titles."""
    spike_days = detect_spike_days(titles)

    # Collect top aliases
    alias_counts = defaultdict(int)
    for t in titles:
        for alias in t.get("aliases", []):
            if str(alias).isascii():
                alias_counts[str(alias)] += 1
    top_aliases = sorted(alias_counts.keys(), key=lambda a: -alias_counts[a])[:5]

    return {
        "bucket": bucket_name,
        "actor": actor,
        "actor_entity": actor_entity,
        "action_class": action,
        "aliases": top_aliases,
        "title_count": len(titles),
        "titles": titles,
        "spike_days": list(spike_days),
        "is_spike_group": is_spike_group,
        "date_range": (
            min(t["pub_date"] for t in titles),
            max(t["pub_date"] for t in titles),
        ),
    }


def cluster_titles(
    titles: list[dict],
    centroid_id: str,
    min_label_cluster: int = 3,
    unknown_split_threshold: int = 50,
) -> list[dict]:
    """
    Clustering pipeline:
    1. Assign buckets (by target, actor nationality, OR geographic aliases)
    2. Within bucket: cluster by (actor, action_class)
    3. For large UNKNOWN clusters: split by spike days
    """
    events = []

    # Step 1: Bucket assignment (now uses aliases via GEO_ALIAS_TO_ISO)
    buckets = defaultdict(list)
    for t in titles:
        bucket = assign_bucket(t, centroid_id)
        buckets[bucket].append(t)

    # Process each bucket
    for bucket_name, bucket_titles in buckets.items():
        # Step 2: Label clustering within bucket
        label_clusters = cluster_by_labels(bucket_titles, min_label_cluster)

        for key, label_titles in label_clusters.items():
            # Unpack key based on cluster type
            cluster_type = key[0]

            if cluster_type == "INSTITUTION":
                # Entity-centric: ("INSTITUTION", entity_name)
                actor = key[1]  # The institution name
                entity = None
                action = None
            elif cluster_type == "CORPORATION":
                # Entity-centric: ("CORPORATION", entity_name)
                actor = "CORPORATION"
                entity = key[1]  # The corporation name
                action = None
            else:
                # Action-based: ("ACTION", actor, action)
                actor = key[1]
                entity = None
                action = key[2]

            # Step 3: For large UNKNOWN clusters, split by spike
            if actor == "UNKNOWN" and len(label_titles) >= unknown_split_threshold:
                spike_days = detect_spike_days(label_titles)
                if spike_days:
                    groups = split_by_spike(label_titles, spike_days, min_label_cluster)
                    for i, group in enumerate(groups):
                        is_spike = any(t["pub_date"] in spike_days for t in group)
                        event = create_event(
                            bucket_name, actor, entity, action, group, is_spike
                        )
                        events.append(event)
                else:
                    event = create_event(
                        bucket_name, actor, entity, action, label_titles
                    )
                    events.append(event)
            else:
                event = create_event(
                    bucket_name, actor, entity, action, label_titles, False
                )
                events.append(event)

    # Mark catch-all events and sort by title count
    for e in events:
        # UNKNOWN without entity = catch-all
        e["is_catchall"] = e["actor"] == "UNKNOWN" and not e.get("actor_entity")

    events.sort(key=lambda e: -e["title_count"])
    return events


def print_cluster_report(events: list[dict], max_events: int = 30):
    """Print clustering report."""
    print()
    print("=" * 80)
    print("EVENT CLUSTERS (mechanical)")
    print("=" * 80)
    print()

    total_titles = sum(e["title_count"] for e in events)
    print("Total events: %d" % len(events))
    print("Total titles clustered: %d" % total_titles)
    print()

    # Group by bucket for reporting
    by_bucket = defaultdict(list)
    for e in events:
        by_bucket[e["bucket"]].append(e)

    for bucket in sorted(by_bucket.keys()):
        bucket_events = by_bucket[bucket]
        bucket_total = sum(e["title_count"] for e in bucket_events)
        print("-" * 80)
        print(
            "BUCKET: %s (%d titles in %d events)"
            % (bucket, bucket_total, len(bucket_events))
        )
        print("-" * 80)

        for e in bucket_events[:10]:  # Top 10 per bucket
            spike_marker = " [SPIKE]" if e["spike_days"] else ""
            # Show entity for CORPORATION etc.
            actor_display = e["actor"]
            if e.get("actor_entity"):
                actor_display = "%s:%s" % (e["actor"], e["actor_entity"])

            # For entity-grouped events (action=None), show "news" instead
            if e.get("action_class"):
                label = "%s -> %s" % (actor_display, e["action_class"])
            else:
                label = "%s news" % actor_display

            print("%3d | %s%s" % (e["title_count"], label, spike_marker))
            if e["aliases"]:
                print("     aliases: %s" % e["aliases"][:5])
            print("     dates: %s to %s" % e["date_range"])

            # Sample title
            sample = e["titles"][0]["title"][:65]
            try:
                sample = sample.encode("ascii", "replace").decode()
            except Exception:
                pass
            print("     example: %s..." % sample)
            print()


def get_ctm_id(conn, centroid_id: str, track: str) -> str:
    """Get CTM ID for centroid/track combination."""
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM ctm WHERE centroid_id = %s AND track = %s",
        (centroid_id, track),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError("CTM not found for %s / %s" % (centroid_id, track))
    return str(row[0])


def jaccard_similarity(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def tokenize_for_matching(text: str) -> set:
    """Tokenize text into words for Jaccard matching."""
    if not text:
        return set()
    # Lowercase, split on non-alphanumeric, filter short words
    import re

    words = re.split(r"[^a-z0-9]+", text.lower())
    # Filter stopwords and short words
    stopwords = {
        "the",
        "a",
        "an",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "and",
        "or",
        "is",
        "are",
        "was",
        "were",
        "has",
        "have",
        "had",
        "be",
        "been",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "with",
        "by",
        "from",
        "as",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "he",
        "she",
        "they",
        "we",
        "you",
        "his",
        "her",
        "their",
        "our",
        "your",
    }
    return {w for w in words if len(w) > 2 and w not in stopwords}


def find_matching_event(
    cur,
    ctm_id: str,
    bucket_key: str,
    event_type: str,
    new_titles: list[dict],
    title_threshold: float = 0.4,
    tag_threshold: float = 0.5,
) -> dict:
    """Find an existing event that matches the new cluster.

    Returns event dict if match found, None otherwise.
    """
    # Get existing events in same bucket
    cur.execute(
        """
        SELECT e.id, e.title, e.tags, e.date, e.first_seen
        FROM events_v3 e
        WHERE e.ctm_id = %s
          AND e.event_type = %s
          AND (e.bucket_key = %s OR (e.bucket_key IS NULL AND %s IS NULL))
          AND e.title IS NOT NULL
        """,
        (ctm_id, event_type, bucket_key, bucket_key),
    )
    existing_events = cur.fetchall()

    if not existing_events:
        return None

    # Build word set from new titles
    new_title_words = set()
    for t in new_titles:
        new_title_words |= tokenize_for_matching(t.get("title", ""))

    for event_id, title, tags, date, first_seen in existing_events:
        # Check title similarity
        existing_title_words = tokenize_for_matching(title)
        title_sim = jaccard_similarity(new_title_words, existing_title_words)

        # Tags will be regenerated after merge, so we only match on title words

        if title_sim >= title_threshold:
            return {
                "id": event_id,
                "title": title,
                "tags": tags,
                "date": date,
                "first_seen": first_seen,
                "similarity": title_sim,
            }

    return None


def write_events_to_db(conn, events: list[dict], ctm_id: str) -> int:
    """Write clustered events to events_v3 with merge support.

    For each new cluster:
    1. Check if matching event exists (same bucket, similar titles)
    2. If match: add new titles to existing event, update date range
    3. If no match: create new event
    """
    cur = conn.cursor()

    # Get existing title IDs for this CTM to avoid duplicates
    cur.execute(
        """
        SELECT evt.title_id
        FROM event_v3_titles evt
        JOIN events_v3 e ON evt.event_id = e.id
        WHERE e.ctm_id = %s
        """,
        (ctm_id,),
    )
    existing_title_ids = {str(r[0]) for r in cur.fetchall()}

    created = 0
    merged = 0
    titles_added = 0

    for e in events:
        # Determine event_type and bucket_key from bucket name
        bucket = e["bucket"]
        if bucket == "domestic":
            event_type = "domestic"
            bucket_key = None
        elif bucket.startswith("bilateral_"):
            event_type = "bilateral"
            bucket_key = bucket.replace("bilateral_", "")
        else:
            event_type = "other_international"
            bucket_key = bucket

        # Filter out titles already in existing events
        new_titles = [t for t in e["titles"] if t["id"] not in existing_title_ids]

        if not new_titles:
            # All titles already assigned to events
            continue

        # Check for matching existing event
        match = find_matching_event(cur, ctm_id, bucket_key, event_type, new_titles)

        if match:
            # Merge: add new titles to existing event
            event_id = match["id"]

            for t in new_titles:
                try:
                    cur.execute(
                        "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s)",
                        (event_id, t["id"]),
                    )
                    existing_title_ids.add(t["id"])
                    titles_added += 1
                except Exception:
                    pass  # Ignore duplicate key errors

            # Update date range and source count
            new_dates = [t["pub_date"] for t in new_titles if t.get("pub_date")]
            if new_dates:
                min_new = min(new_dates)
                max_new = max(new_dates)

                cur.execute(
                    """
                    UPDATE events_v3
                    SET first_seen = LEAST(first_seen, %s::date),
                        date = GREATEST(date, %s::date),
                        source_batch_count = source_batch_count + %s,
                        title = NULL,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (min_new, max_new, len(new_titles), event_id),
                )

            merged += 1
            print(
                "  MERGED %d titles into existing event (sim=%.2f)"
                % (len(new_titles), match["similarity"])
            )

        else:
            # Create new event
            event_date = e["date_range"][1]
            first_seen = e["date_range"][0]

            # Generate placeholder summary (will be replaced by LLM in Phase 4.5a)
            spike_tag = " [SPIKE]" if e["spike_days"] else ""
            actor_display = e["actor"]
            if e.get("actor_entity"):
                actor_display = "%s:%s" % (e["actor"], e["actor_entity"])

            if e.get("action_class"):
                summary = "%s -> %s (%d titles)%s" % (
                    actor_display,
                    e["action_class"],
                    len(new_titles),
                    spike_tag,
                )
            else:
                summary = "%s news (%d titles)%s" % (
                    actor_display,
                    len(new_titles),
                    spike_tag,
                )

            cur.execute(
                """
                INSERT INTO events_v3 (ctm_id, date, first_seen, summary, event_type, bucket_key, source_batch_count, is_catchall)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    ctm_id,
                    event_date,
                    first_seen,
                    summary,
                    event_type,
                    bucket_key,
                    len(new_titles),
                    e.get("is_catchall", False),
                ),
            )
            event_id = cur.fetchone()[0]

            for t in new_titles:
                cur.execute(
                    "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s)",
                    (event_id, t["id"]),
                )
                existing_title_ids.add(t["id"])

            created += 1

    conn.commit()

    print("")
    print("Events created: %d" % created)
    print("Events merged:  %d" % merged)
    print("Titles added:   %d" % titles_added)

    return created + merged


def process_ctm(
    conn, centroid_id: str, track: str, min_label: int = 3, write: bool = False
):
    """Process a single CTM for clustering."""
    titles = load_titles_with_labels(conn, centroid_id, track)

    if len(titles) < min_label:
        return 0, 0

    events = cluster_titles(titles, centroid_id, min_label_cluster=min_label)

    if not events:
        return 0, 0

    if write:
        # Get CTM ID
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM ctm WHERE centroid_id = %s AND track = %s",
            (centroid_id, track),
        )
        row = cur.fetchone()
        if row:
            ctm_id = str(row[0])
            result = write_events_to_db(conn, events, ctm_id)
            return len(events), result

    return len(events), 0


def main():
    parser = argparse.ArgumentParser(description="Mechanical event clustering")
    parser.add_argument("--centroid", help="Centroid ID (omit for all)")
    parser.add_argument("--track", help="Track name (omit for all tracks)")
    parser.add_argument(
        "--min-label", type=int, default=3, help="Min titles per label cluster"
    )
    parser.add_argument("--write", action="store_true", help="Write events to database")
    args = parser.parse_args()

    conn = get_connection()

    # Determine which CTMs to process
    cur = conn.cursor()

    if args.centroid and args.track:
        # Single CTM mode
        print("Loading titles for %s / %s..." % (args.centroid, args.track))
        titles = load_titles_with_labels(conn, args.centroid, args.track)
        print("Loaded %d titles with labels" % len(titles))

        events = cluster_titles(titles, args.centroid, min_label_cluster=args.min_label)
        print_cluster_report(events)

        if args.write and events:
            ctm_id = get_ctm_id(conn, args.centroid, args.track)
            written = write_events_to_db(conn, events, ctm_id)
            print("Wrote %d events" % written)

        conn.close()
        return

    # Build query for CTM selection
    conditions = ["c.title_count >= 3", "c.is_frozen = false"]
    params = []

    if args.centroid:
        conditions.append("c.centroid_id = %s")
        params.append(args.centroid)

    if args.track:
        conditions.append("c.track = %s")
        params.append(args.track)

    query = """
        SELECT c.centroid_id, c.track, c.title_count
        FROM ctm c
        WHERE %s
        ORDER BY c.title_count DESC
    """ % " AND ".join(
        conditions
    )

    cur.execute(query, tuple(params) if params else None)
    ctms = cur.fetchall()

    print("Processing %d CTMs..." % len(ctms))
    print("")

    total_events = 0
    total_written = 0

    for centroid_id, track, title_count in ctms:
        print("%s / %s (%d titles)" % (centroid_id, track, title_count), end=" ")

        titles = load_titles_with_labels(conn, centroid_id, track)

        if len(titles) < args.min_label:
            print("-> skip (no labels)")
            continue

        events = cluster_titles(titles, centroid_id, min_label_cluster=args.min_label)

        if not events:
            print("-> 0 events")
            continue

        if args.write:
            ctm_id = get_ctm_id(conn, centroid_id, track)
            written = write_events_to_db(conn, events, ctm_id)
            total_written += written
            print("-> %d events" % len(events))
        else:
            print("-> %d events (dry run)" % len(events))

        total_events += len(events)

    print("")
    print("=" * 60)
    print("TOTAL")
    print("=" * 60)
    print("CTMs processed: %d" % len(ctms))
    print("Events found:   %d" % total_events)
    if args.write:
        print("Events written: %d" % total_written)

    conn.close()


if __name__ == "__main__":
    main()
