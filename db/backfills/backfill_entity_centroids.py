"""
Backfill centroid_ids based on entity_countries.

Updates titles_v3.centroid_ids by looking up ISO codes extracted
from entity_countries in title_labels and mapping them to centroids.

Example: {"JAISHANKAR": "IN"} -> adds ASIA-INDIA to centroid_ids
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import execute_batch

from core.config import config


def build_iso_to_centroid_map(conn) -> dict:
    """
    Build a mapping from ISO code to most specific centroid_id.

    When an ISO code appears in multiple centroids (e.g., ET in both
    AFRICA-ETHIOPIA and AFRICA-EAST), prefer the country-specific one.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, iso_codes
        FROM centroids_v3
        WHERE iso_codes IS NOT NULL AND array_length(iso_codes, 1) > 0
    """
    )

    # Build reverse mapping: ISO -> list of centroids
    iso_to_centroids = {}
    for centroid_id, iso_codes in cur.fetchall():
        for iso in iso_codes:
            if iso not in iso_to_centroids:
                iso_to_centroids[iso] = []
            iso_to_centroids[iso].append((centroid_id, len(iso_codes)))

    # For each ISO, pick the centroid with fewest iso_codes (most specific)
    iso_to_centroid = {}
    for iso, centroids in iso_to_centroids.items():
        # Sort by iso_codes count ascending (most specific first)
        centroids.sort(key=lambda x: x[1])
        iso_to_centroid[iso] = centroids[0][0]

    return iso_to_centroid


def backfill_entity_centroids(batch_size=500, limit=None, dry_run=False):
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    print("Building ISO -> centroid map...")
    iso_to_centroid = build_iso_to_centroid_map(conn)
    print("  Loaded {} ISO code mappings".format(len(iso_to_centroid)))

    # Show sample mappings
    samples = list(iso_to_centroid.items())[:10]
    for iso, centroid in samples:
        print("    {} -> {}".format(iso, centroid))

    # Count titles with entity_countries
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM title_labels tl
            JOIN titles_v3 t ON t.id = tl.title_id
            WHERE tl.entity_countries IS NOT NULL
              AND tl.entity_countries != '{}'::jsonb
        """
        )
        total = cur.fetchone()[0]
        print("\nTitles with entity_countries: {}".format(total))

    if total == 0:
        print("No titles to process. Run extract_labels.py first.")
        conn.close()
        return

    if limit:
        total = min(total, limit)
        print("  (limited to {})".format(limit))

    processed = 0
    updated = 0
    skipped_no_match = 0

    while processed < total:
        # Fetch batch of titles with entity_countries
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tl.title_id, tl.entity_countries, t.centroid_ids
                FROM title_labels tl
                JOIN titles_v3 t ON t.id = tl.title_id
                WHERE tl.entity_countries IS NOT NULL
                  AND tl.entity_countries != '{}'::jsonb
                ORDER BY tl.title_id
                OFFSET %s LIMIT %s
            """,
                (processed, batch_size),
            )
            rows = cur.fetchall()

        if not rows:
            break

        # Process batch
        updates = []
        for title_id, entity_countries, current_centroid_ids in rows:
            if not entity_countries:
                continue

            # Extract unique codes from entity_countries values
            # Handle both 2-letter ISO codes AND special codes (NATO, ISIS, EU, etc.)
            codes = set()
            for entity, code in entity_countries.items():
                if code and isinstance(code, str):
                    code = code.upper().strip()
                    # Accept any valid code (2-letter ISO or special codes in our mapping)
                    if len(code) >= 2 and code.isalpha():
                        codes.add(code)

            if not codes:
                skipped_no_match += 1
                continue

            # Map codes to centroid_ids
            new_centroids = set()
            for code in codes:
                if code in iso_to_centroid:
                    new_centroids.add(iso_to_centroid[code])

            if not new_centroids:
                skipped_no_match += 1
                continue

            # Merge with existing centroid_ids
            current_set = set(current_centroid_ids) if current_centroid_ids else set()
            combined = current_set | new_centroids

            # Only update if there are new centroids
            if combined != current_set:
                updates.append((list(combined), title_id))

        # Update batch
        if updates and not dry_run:
            with conn.cursor() as cur:
                execute_batch(
                    cur,
                    """
                    UPDATE titles_v3
                    SET centroid_ids = %s
                    WHERE id = %s
                """,
                    updates,
                    page_size=batch_size,
                )
            conn.commit()
            updated += len(updates)
        elif updates and dry_run:
            updated += len(updates)
            # Show sample updates
            if updated <= 10:
                for new_ids, tid in updates[:3]:
                    print("    Would update {}: {}".format(tid, new_ids))

        processed += len(rows)
        pct = (processed / total) * 100
        mode = "DRY RUN - " if dry_run else ""
        print(
            "  {}Processed: {}/{} ({:.1f}%) - Updated: {} - No match: {}".format(
                mode, processed, total, pct, updated, skipped_no_match
            )
        )

    print("\nDone. Updated {} titles with new centroid_ids.".format(updated))
    print(
        "Skipped {} titles (no valid ISO codes or no matching centroids).".format(
            skipped_no_match
        )
    )
    conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Backfill centroid_ids from entity_countries"
    )
    parser.add_argument("--limit", type=int, help="Limit titles to process")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be updated"
    )
    args = parser.parse_args()

    backfill_entity_centroids(
        batch_size=args.batch_size, limit=args.limit, dry_run=args.dry_run
    )
