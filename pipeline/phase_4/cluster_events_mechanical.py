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
ENTITY_ACTORS = {"CORPORATION", "ARMED_GROUP", "NGO", "MEDIA_OUTLET"}

# Invalid entity values that should be ignored (not specific companies)
INVALID_ENTITIES = {
    # Trump-related (should be US_EXECUTIVE, not CORPORATION)
    "TRUMP", "TRUMP ADMINISTRATION", "TRUMP MEDIA GROUP",
    "TRUMP ORGANIZATION", "TRUMP STORE",
    # Collective/generic terms (not specific companies)
    "WALL STREET", "TECH FIRMS", "STARTUP", "SILICON VALLEY",
    "PRIVATE EQUITY", "HEDGE FUND", "HEDGE FUNDS",
    "RARE-EARTH MAGNET MAKER", "TECH GIANT", "TECH GIANTS",
    "BIG TECH", "BANKS", "AUTOMAKER", "AUTOMAKERS",
    # Institutions that are not corporations
    "FED", "FEDERAL RESERVE", "ECB", "CENTRAL BANK",
}


def normalize_entity(entity: str) -> str:
    """Normalize entity names for consistency."""
    if not entity:
        return None

    entity = entity.upper().strip()

    # Skip invalid entities
    if entity in INVALID_ENTITIES:
        return None

    # Normalize common variations
    normalizations = {
        "GOLDMAN": "GOLDMAN SACHS",
        "JPMORGAN CHASE": "JPMORGAN",
        "JP MORGAN": "JPMORGAN",
        "ALPHABET": "GOOGLE",  # Parent company -> common name
        "ALPHABET INC": "GOOGLE",
    }

    return normalizations.get(entity, entity)


def cluster_by_labels(titles: list[dict], min_cluster_size: int = 3) -> dict:
    """Cluster titles by (actor, action) or (actor, entity) for entity actors.

    For ENTITY_ACTORS (CORPORATION, etc.), groups ALL actions for one entity together.
    This creates ONE event per company summarizing all their news.
    For state actors, groups by action_class as before.
    """
    clusters = defaultdict(list)
    for t in titles:
        actor = t["actor"]
        action = t["action_class"]
        raw_entity = t.get("actor_entity")
        entity = normalize_entity(raw_entity) if raw_entity else None

        # For entity-based actors with valid entity: group by entity only
        # This creates ONE event per company (e.g., "Nvidia news summary")
        if actor in ENTITY_ACTORS and entity:
            key = (actor, entity, None)  # None for action = all actions combined
        else:
            key = (actor, None, action)  # None for entity = standard grouping

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

        for (actor, entity, action), label_titles in label_clusters.items():
            # Step 3: For large UNKNOWN clusters, split by spike
            if actor == "UNKNOWN" and len(label_titles) >= unknown_split_threshold:
                spike_days = detect_spike_days(label_titles)
                if spike_days:
                    groups = split_by_spike(label_titles, spike_days, min_label_cluster)
                    for i, group in enumerate(groups):
                        is_spike = any(t["pub_date"] in spike_days for t in group)
                        events.append(
                            create_event(
                                bucket_name, actor, entity, action, group, is_spike
                            )
                        )
                else:
                    events.append(
                        create_event(bucket_name, actor, entity, action, label_titles)
                    )
            else:
                events.append(
                    create_event(
                        bucket_name, actor, entity, action, label_titles, False
                    )
                )

    # Sort by title count descending
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

            # For entity-grouped events (action=None), show "news summary" instead
            if e.get("action_class"):
                label = "%s -> %s" % (actor_display, e["action_class"])
            else:
                label = "%s (news summary)" % actor_display

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


def write_events_to_db(conn, events: list[dict], ctm_id: str) -> int:
    """Write clustered events to events_v3 and event_v3_titles."""
    cur = conn.cursor()

    # Delete existing events for this CTM
    cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))
    deleted = cur.rowcount
    print("Deleted %d existing events for CTM" % deleted)

    written = 0
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

        # Use most recent date from titles
        event_date = e["date_range"][1]

        # Generate placeholder summary
        spike_tag = " [SPIKE]" if e["spike_days"] else ""
        actor_display = e["actor"]
        if e.get("actor_entity"):
            actor_display = "%s:%s" % (e["actor"], e["actor_entity"])

        # For entity-grouped events (action=None), use "news summary" format
        if e.get("action_class"):
            summary = "%s -> %s (%d titles)%s" % (
                actor_display,
                e["action_class"],
                e["title_count"],
                spike_tag,
            )
        else:
            summary = "%s news (%d titles)%s" % (
                actor_display,
                e["title_count"],
                spike_tag,
            )

        # Insert event
        cur.execute(
            """
            INSERT INTO events_v3 (ctm_id, date, summary, event_type, bucket_key, source_batch_count)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (ctm_id, event_date, summary, event_type, bucket_key, e["title_count"]),
        )
        event_id = cur.fetchone()[0]

        # Insert title links
        for t in e["titles"]:
            cur.execute(
                "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s)",
                (event_id, t["id"]),
            )

        written += 1

    conn.commit()
    return written


def main():
    parser = argparse.ArgumentParser(description="Mechanical event clustering")
    parser.add_argument("--centroid", required=True, help="Centroid ID")
    parser.add_argument("--track", required=True, help="Track name")
    parser.add_argument(
        "--min-label", type=int, default=3, help="Min titles per label cluster"
    )
    parser.add_argument("--write", action="store_true", help="Write events to database")
    args = parser.parse_args()

    conn = get_connection()

    print("Loading titles for %s / %s..." % (args.centroid, args.track))
    titles = load_titles_with_labels(conn, args.centroid, args.track)
    print("Loaded %d titles with labels" % len(titles))

    events = cluster_titles(
        titles,
        args.centroid,
        min_label_cluster=args.min_label,
    )

    print_cluster_report(events)

    if args.write:
        ctm_id = get_ctm_id(conn, args.centroid, args.track)
        written = write_events_to_db(conn, events, ctm_id)
        print()
        print("Wrote %d events to events_v3" % written)

    conn.close()


if __name__ == "__main__":
    main()
