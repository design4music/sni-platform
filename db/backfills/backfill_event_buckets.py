"""
Backfill event_type and bucket_key for existing events.

Finds events with missing event_type/bucket_key and assigns them based on:
1. Title labels (target, actor nationality)
2. Matched aliases (geographic signals)

Usage:
    python db/backfill_event_buckets.py                    # Dry run
    python db/backfill_event_buckets.py --write            # Actually update
    python db/backfill_event_buckets.py --centroid EUROPE-ALPINE --write
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from core.config import config
from core.ontology import GEO_ALIAS_TO_ISO


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def load_centroid_iso_codes(cur, centroid_id: str) -> set:
    """Load iso_codes for a centroid."""
    cur.execute(
        "SELECT iso_codes FROM centroids_v3 WHERE id = %s",
        (centroid_id,),
    )
    row = cur.fetchone()
    if row and row[0]:
        return set(row[0])
    return set()


def get_geo_bucket_from_aliases(aliases: list, home_iso_codes: set) -> str:
    """Check aliases for geographic bucket signal."""
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


def determine_bucket(titles_data: list, home_iso_codes: set) -> tuple:
    """
    Determine event_type and bucket_key from title data.

    Returns: (event_type, bucket_key)
    """
    foreign_countries = Counter()

    for title in titles_data:
        target = title.get("target")
        actor = title.get("actor")
        aliases = title.get("aliases") or []

        # Check target
        if target and target != "-":
            if len(target) == 2 and target not in home_iso_codes:
                foreign_countries[target] += 1
            elif "_" in target:
                target_country = target.split("_")[0]
                if len(target_country) == 2 and target_country not in home_iso_codes:
                    foreign_countries[target_country] += 1
            elif target in ["NATO", "EU", "BRICS", "G7", "MERCOSUR"]:
                foreign_countries[target] += 1

        # Check actor nationality
        actor_country = extract_country_from_actor(actor)
        if actor_country and actor_country not in home_iso_codes:
            foreign_countries[actor_country] += 1

        # Check aliases
        alias_iso = get_geo_bucket_from_aliases(aliases, home_iso_codes)
        if alias_iso:
            foreign_countries[alias_iso] += 1

    if foreign_countries:
        # Use most common foreign country
        most_common = foreign_countries.most_common(1)[0][0]
        return ("bilateral", most_common)

    return ("domestic", None)


def backfill_events(centroid_id: str = None, write: bool = False):
    """Backfill event_type and bucket_key for events missing them."""
    conn = get_connection()
    cur = conn.cursor()

    # Find events with missing event_type
    query = """
        SELECT e.id, e.ctm_id, e.summary, c.centroid_id
        FROM events_v3 e
        JOIN ctm c ON e.ctm_id = c.id
        WHERE e.event_type IS NULL
    """
    params = []

    if centroid_id:
        query += " AND c.centroid_id = %s"
        params.append(centroid_id)

    cur.execute(query, params if params else None)
    events = cur.fetchall()

    print("Found %d events with missing event_type" % len(events))

    if not events:
        conn.close()
        return

    # Cache centroid iso_codes
    iso_codes_cache = {}

    updates = []

    for event_id, ctm_id, summary, cent_id in events:
        # Get centroid iso_codes
        if cent_id not in iso_codes_cache:
            iso_codes_cache[cent_id] = load_centroid_iso_codes(cur, cent_id)
        home_iso_codes = iso_codes_cache[cent_id]

        # Get title data for this event
        cur.execute(
            """
            SELECT t.matched_aliases, tl.actor, tl.target
            FROM event_v3_titles evt
            JOIN titles_v3 t ON evt.title_id = t.id
            LEFT JOIN title_labels tl ON tl.title_id = t.id
            WHERE evt.event_id = %s
        """,
            (event_id,),
        )

        titles_data = []
        for aliases, actor, target in cur.fetchall():
            titles_data.append(
                {
                    "aliases": aliases,
                    "actor": actor,
                    "target": target,
                }
            )

        if not titles_data:
            continue

        event_type, bucket_key = determine_bucket(titles_data, home_iso_codes)
        updates.append((event_type, bucket_key, event_id, summary[:50]))

    # Report
    domestic_count = sum(1 for u in updates if u[0] == "domestic")
    bilateral_count = sum(1 for u in updates if u[0] == "bilateral")

    print("\nResults:")
    print("  Domestic:  %d" % domestic_count)
    print("  Bilateral: %d" % bilateral_count)

    if bilateral_count > 0:
        print("\nBilateral events (sample):")
        bilateral_shown = 0
        for event_type, bucket_key, event_id, summary in updates:
            if event_type == "bilateral" and bilateral_shown < 20:
                # Safely encode for console output
                safe_summary = summary.encode("ascii", "replace").decode()
                print("  %s -> %s: %s..." % (bucket_key, event_id[:8], safe_summary))
                bilateral_shown += 1
        if bilateral_count > 20:
            print("  ... and %d more bilateral events" % (bilateral_count - 20))

    if write:
        print("\nWriting updates...")
        for event_type, bucket_key, event_id, _ in updates:
            cur.execute(
                """
                UPDATE events_v3
                SET event_type = %s, bucket_key = %s, updated_at = NOW()
                WHERE id = %s
            """,
                (event_type, bucket_key, event_id),
            )
        conn.commit()
        print("Updated %d events" % len(updates))
    else:
        print("\nDry run - use --write to apply changes")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill event_type/bucket_key")
    parser.add_argument("--centroid", help="Limit to specific centroid")
    parser.add_argument("--write", action="store_true", help="Actually update database")

    args = parser.parse_args()
    backfill_events(centroid_id=args.centroid, write=args.write)
