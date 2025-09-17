#!/usr/bin/env python3
"""
Investigate why 97.8% of strategic titles are unprocessed
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


from sqlalchemy import text

from core.database import get_db_session


def investigate_processing_gaps():
    """Deep dive into why titles aren't being processed"""

    with get_db_session() as session:
        print("=== PROCESSING GAP ANALYSIS ===\n")

        # Get detailed breakdown of unprocessed titles
        print("1. UNPROCESSED TITLES ANALYSIS")
        print("-" * 50)

        unprocessed_sample = session.execute(
            text(
                """
            SELECT 
                id,
                title_display,
                publisher_name,
                pubdate_utc,
                gate_actor_hit,
                entities,
                detected_language
            FROM titles 
            WHERE gate_keep = true 
            AND event_family_id IS NULL
            ORDER BY pubdate_utc DESC
            LIMIT 20
        """
            )
        ).fetchall()

        print("Sample unprocessed strategic titles:")
        for i, title in enumerate(unprocessed_sample):
            print(f"{i+1}. {title.title_display[:80]}...")
            print(f"   Publisher: {title.publisher_name}")
            print(f"   Date: {title.pubdate_utc}")
            print(f"   Actors: {title.gate_actor_hit}")
            print(f"   Language: {title.detected_language}")
            print()

        # Check batch processing status
        print("\n2. BATCH PROCESSING ANALYSIS")
        print("-" * 50)

        batch_analysis = session.execute(
            text(
                """
            SELECT 
                processing_notes,
                COUNT(*) as title_count
            FROM titles 
            WHERE gate_keep = true 
            AND event_family_id IS NOT NULL
            AND processing_notes IS NOT NULL
            GROUP BY processing_notes
            ORDER BY title_count DESC
        """
            )
        ).fetchall()

        print("Processed titles by batch:")
        for batch in batch_analysis:
            print(f"  {batch.processing_notes}: {batch.title_count} titles")

        # Language distribution
        print("\n3. LANGUAGE DISTRIBUTION")
        print("-" * 50)

        lang_analysis = session.execute(
            text(
                """
            SELECT 
                detected_language,
                COUNT(*) as total_count,
                COUNT(CASE WHEN event_family_id IS NOT NULL THEN 1 END) as processed_count,
                ROUND(
                    COUNT(CASE WHEN event_family_id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 
                    2
                ) as processing_rate
            FROM titles 
            WHERE gate_keep = true
            GROUP BY detected_language
            ORDER BY total_count DESC
        """
            )
        ).fetchall()

        print("Processing rate by language:")
        for lang in lang_analysis:
            print(
                f"  {lang.detected_language}: {lang.processed_count}/{lang.total_count} ({lang.processing_rate}%)"
            )

        # Date distribution
        print("\n4. TEMPORAL DISTRIBUTION")
        print("-" * 50)

        date_analysis = session.execute(
            text(
                """
            SELECT 
                DATE(pubdate_utc) as pub_date,
                COUNT(*) as total_count,
                COUNT(CASE WHEN event_family_id IS NOT NULL THEN 1 END) as processed_count
            FROM titles 
            WHERE gate_keep = true
            AND pubdate_utc >= '2025-09-01'
            GROUP BY DATE(pubdate_utc)
            ORDER BY pub_date DESC
            LIMIT 10
        """
            )
        ).fetchall()

        print("Recent dates processing rates:")
        for date_row in date_analysis:
            rate = (
                (date_row.processed_count / date_row.total_count * 100)
                if date_row.total_count > 0
                else 0
            )
            print(
                f"  {date_row.pub_date}: {date_row.processed_count}/{date_row.total_count} ({rate:.1f}%)"
            )

        # Check for fragmentation in similar EFs
        print("\n5. EVENT FAMILY FRAGMENTATION ANALYSIS")
        print("-" * 50)

        fragmentation_check = session.execute(
            text(
                """
            SELECT 
                primary_theater,
                event_type,
                COUNT(*) as ef_count,
                STRING_AGG(title, ' | ') as titles
            FROM event_families 
            WHERE status = 'active'
            GROUP BY primary_theater, event_type
            HAVING COUNT(*) > 1
            ORDER BY ef_count DESC, primary_theater, event_type
        """
            )
        ).fetchall()

        print("Potential fragmentation (multiple EFs with same theater+type):")
        for frag in fragmentation_check:
            print(f"\n{frag.primary_theater} + {frag.event_type}: {frag.ef_count} EFs")
            titles = frag.titles.split(" | ")
            for i, title in enumerate(titles):
                print(f"  {i+1}. {title[:70]}...")

        # Identify specific fragmentation issues
        print("\n6. TRUMP ADMINISTRATION FRAGMENTATION")
        print("-" * 50)

        trump_efs = session.execute(
            text(
                """
            SELECT 
                id,
                title,
                key_actors,
                ef_key,
                source_title_ids,
                created_at
            FROM event_families 
            WHERE status = 'active'
            AND (
                title ILIKE '%trump%' 
                OR 'Donald Trump' = ANY(key_actors)
            )
            ORDER BY created_at
        """
            )
        ).fetchall()

        print("Trump-related Event Families (potential duplicates):")
        for ef in trump_efs:
            print(f"EF: {ef.title}")
            print(f"  Key: {ef.ef_key}")
            print(f"  Actors: {ef.key_actors}")
            print(f"  Titles: {len(ef.source_title_ids)}")
            print(f"  Created: {ef.created_at}")
            print()


if __name__ == "__main__":
    investigate_processing_gaps()
