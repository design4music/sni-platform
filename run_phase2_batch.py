#!/usr/bin/env python3
"""
Run Phase 2 enrichment in small batches to avoid timeouts
Process titles in batches of 50 without LLM calls (static taxonomy only)
"""

import asyncio

from sqlalchemy import text

from apps.filter.taxonomy_extractor import \
    create_multi_vocab_taxonomy_extractor
from apps.filter.title_processor_helpers import update_title_entities
from core.database import get_db_session


async def process_batch_static_only(batch_size=50, total_batches=6):
    """
    Process titles using ONLY static taxonomy matching (no LLM).
    This is much faster and sufficient for testing the taxonomy system.
    """

    print("=" * 80)
    print("Phase 2 Enrichment - Static Taxonomy Only (No LLM)")
    print("=" * 80)

    # Load taxonomy extractor once
    print("\nLoading vocabularies...")
    extractor = create_multi_vocab_taxonomy_extractor()
    print("  [OK] Vocabularies loaded")

    total_processed = 0
    total_strategic = 0
    total_blocked = 0
    total_non_strategic = 0

    for batch_num in range(1, total_batches + 1):
        print(f"\n" + "=" * 80)
        print(f"Batch {batch_num}/{total_batches}")
        print("=" * 80)

        with get_db_session() as session:
            # Get next batch of titles
            query = text(
                """
                SELECT id, title_display
                FROM titles
                WHERE entities IS NULL
                AND created_at >= NOW() - INTERVAL '7 DAY'
                ORDER BY created_at DESC
                LIMIT :limit
            """
            )
            results = session.execute(query, {"limit": batch_size}).fetchall()

            if not results:
                print("No more pending titles")
                break

            print(f"Processing {len(results)} titles...")

            batch_strategic = 0
            batch_blocked = 0
            batch_non_strategic = 0

            for row in results:
                title_id = str(row.id)
                title_text = row.title_display

                # Use static taxonomy only (no LLM)
                strategic_hit = extractor.strategic_first_hit(title_text)

                if strategic_hit:
                    # Get all entities
                    entities = extractor.all_strategic_hits(title_text)
                    is_strategic = len(entities) > 0

                    if is_strategic:
                        batch_strategic += 1
                    else:
                        # Hit by STOP list - blocked
                        batch_blocked += 1
                        is_strategic = False
                        entities = []
                else:
                    # No static match - mark as non-strategic (skip LLM for speed)
                    is_strategic = False
                    entities = []
                    batch_non_strategic += 1

                # Update database
                update_title_entities(
                    session, title_id, {"actors": entities}, is_strategic
                )

            # Commit batch
            session.commit()

            print(f"\nBatch Results:")
            print(f"  Strategic: {batch_strategic}")
            print(f"  Blocked by STOP: {batch_blocked}")
            print(f"  Non-strategic: {batch_non_strategic}")

            total_processed += len(results)
            total_strategic += batch_strategic
            total_blocked += batch_blocked
            total_non_strategic += batch_non_strategic

    print("\n" + "=" * 80)
    print("Final Statistics:")
    print("=" * 80)
    print(f"  Total processed: {total_processed}")
    print(f"  Strategic: {total_strategic}")
    print(f"  Blocked by STOP: {total_blocked}")
    print(f"  Non-strategic (no match): {total_non_strategic}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(process_batch_static_only(batch_size=50, total_batches=6))
