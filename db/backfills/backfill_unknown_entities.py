"""
Smart backfill: Extract entity_countries ONLY for titles with unknown entities.

This script:
1. Loads known aliases from taxonomy_v3
2. Finds titles with entities NOT in taxonomy_v3
3. Only runs LLM extraction for those titles
4. Then runs centroid mapping

This reduces LLM calls by ~71% compared to processing all titles.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2

from core.config import config


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def load_known_aliases(conn) -> set:
    """Load all known aliases from taxonomy_v3 (all languages)."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT UPPER(alias) FROM (
            SELECT jsonb_array_elements_text(aliases->'en') as alias
            FROM taxonomy_v3 WHERE aliases->'en' IS NOT NULL
            UNION
            SELECT jsonb_array_elements_text(aliases->'de') as alias
            FROM taxonomy_v3 WHERE aliases->'de' IS NOT NULL
            UNION
            SELECT jsonb_array_elements_text(aliases->'es') as alias
            FROM taxonomy_v3 WHERE aliases->'es' IS NOT NULL
            UNION
            SELECT jsonb_array_elements_text(aliases->'fr') as alias
            FROM taxonomy_v3 WHERE aliases->'fr' IS NOT NULL
        ) x
    """
    )
    return set(r[0] for r in cur.fetchall())


def find_titles_with_unknown_entities(conn, known_aliases: set, limit: int = None):
    """Find title_ids that have entities NOT in taxonomy_v3."""
    cur = conn.cursor()

    # Get titles with their entities (that don't have entity_countries yet)
    cur.execute(
        """
        SELECT tl.title_id, tl.persons, tl.orgs, tl.places, tl.systems
        FROM title_labels tl
        WHERE tl.entity_countries IS NULL
           OR tl.entity_countries = '{}'::jsonb
    """
    )

    titles_needing_extraction = []

    for row in cur.fetchall():
        title_id, persons, orgs, places, systems = row

        # Combine all entities
        all_entities = set()
        for arr in [persons, orgs, places, systems]:
            if arr:
                all_entities.update(e.upper() for e in arr)

        # Check if any are unknown
        unknown_entities = all_entities - known_aliases

        if unknown_entities:
            titles_needing_extraction.append(title_id)

            if limit and len(titles_needing_extraction) >= limit:
                break

    return titles_needing_extraction


def main(max_titles: int = None, batch_size: int = 25, concurrency: int = 3):
    conn = get_connection()

    print("Loading known aliases from taxonomy_v3...")
    known_aliases = load_known_aliases(conn)
    print("  Found {:,} known aliases".format(len(known_aliases)))

    print("\nFinding titles with unknown entities...")
    title_ids = find_titles_with_unknown_entities(conn, known_aliases, limit=max_titles)
    print(
        "  Found {:,} titles needing entity_countries extraction".format(len(title_ids))
    )

    if not title_ids:
        print("\nNo titles need processing!")
        conn.close()
        return

    conn.close()

    # Now run the extraction only for these titles
    print("\nRunning LLM extraction for {} titles...".format(len(title_ids)))

    # Import here to avoid circular imports
    from pipeline.phase_3_1.extract_labels import process_titles

    # Process in batches
    result = process_titles(
        max_titles=len(title_ids),
        batch_size=batch_size,
        concurrency=concurrency,
        backfill_entity_countries=True,
        title_ids_filter=title_ids,  # Only process these titles
    )

    print("\nExtraction complete: {} written".format(result.get("written", 0)))

    # Run centroid backfill
    print("\nRunning centroid mapping...")
    from pipeline.phase_3_2.backfill_entity_centroids import backfill_entity_centroids

    backfill_entity_centroids(batch_size=500)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Smart backfill: only process titles with unknown entities"
    )
    parser.add_argument("--max-titles", type=int, help="Limit titles to process")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--concurrency", type=int, default=3)
    args = parser.parse_args()

    main(
        max_titles=args.max_titles,
        batch_size=args.batch_size,
        concurrency=args.concurrency,
    )
