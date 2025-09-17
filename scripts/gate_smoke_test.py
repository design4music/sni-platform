#!/usr/bin/env python3
"""
Strategic Gate Smoke Test Script
Quick verification that gate processing works end-to-end
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text

from apps.filter.run_enhanced_gate import run_enhanced_gate_processing
from core.config import get_config


def insert_test_titles():
    """Insert some test titles for smoke testing"""
    config = get_config()
    engine = create_engine(config.database_url)

    test_titles = [
        {
            "url_gnews": "https://test.example/1",
            "title_original": "EU imposes sanctions on Iranian officials over human rights",
            "title_display": "EU imposes sanctions on Iranian officials over human rights",
            "title_norm": "eu imposes sanctions on iranian officials over human rights",
            "pubdate_utc": datetime.now(timezone.utc) - timedelta(hours=1),
            "processing_status": "pending",
        },
        {
            "url_gnews": "https://test.example/2",
            "title_original": "Beijing warns against Taiwan independence moves",
            "title_display": "Beijing warns against Taiwan independence moves",
            "title_norm": "beijing warns against taiwan independence moves",
            "pubdate_utc": datetime.now(timezone.utc) - timedelta(hours=2),
            "processing_status": "pending",
        },
        {
            "url_gnews": "https://test.example/3",
            "title_original": "Team Alpha defeats Team Beta in championship match",
            "title_display": "Team Alpha defeats Team Beta in championship match",
            "title_norm": "team alpha defeats team beta in championship match",
            "pubdate_utc": datetime.now(timezone.utc) - timedelta(hours=3),
            "processing_status": "pending",
        },
    ]

    with engine.connect() as conn:
        for title in test_titles:
            # Check if already exists to avoid duplicates
            existing = conn.execute(
                text(
                    """
                SELECT id FROM titles WHERE url_gnews = :url_gnews
            """
                ),
                {"url_gnews": title["url_gnews"]},
            ).fetchone()

            if not existing:
                conn.execute(
                    text(
                        """
                    INSERT INTO titles (url_gnews, title_original, title_display, title_norm, pubdate_utc, processing_status)
                    VALUES (:url_gnews, :title_original, :title_display, :title_norm, :pubdate_utc, :processing_status)
                """
                    ),
                    title,
                )

        conn.commit()
        print("Test titles inserted")


async def run_smoke_test():
    """Run complete smoke test"""
    print("=== STRATEGIC GATE SMOKE TEST ===")

    # Step 1: Insert test data
    print("\n1. Inserting test titles...")
    insert_test_titles()

    # Step 2: Run enhanced gate processing
    print("\n2. Running enhanced gate processing...")
    stats = await run_enhanced_gate_processing(hours=1, max_titles=10, dry_run=False)

    # Step 3: Check results
    print("\n3. Checking results...")
    print(f"Titles processed: {stats['titles_processed']}")
    print(f"Strategic titles: {stats['strategic_titles']}")
    print(f"Non-strategic titles: {stats['non_strategic_titles']}")
    print(f"Entities extracted: {stats['entities_extracted']}")
    if stats["errors"] > 0:
        print(f"Errors: {stats['errors']}")

    # Step 4: Verify specific test cases
    print("\n4. Verifying test case results...")
    config = get_config()
    engine = create_engine(config.database_url)

    with engine.connect() as conn:
        results = conn.execute(
            text(
                """
            SELECT title_display, gate_keep, gate_reason, gate_actor_hit, gate_score
            FROM titles 
            WHERE url_gnews LIKE 'https://test.example/%'
            AND gate_at IS NOT NULL
            ORDER BY url_gnews
        """
            )
        ).fetchall()

        for row in results:
            score_str = (
                f"{row.gate_score:.3f}" if row.gate_score is not None else "None"
            )
            print(
                f"  '{row.title_display[:50]}...': keep={row.gate_keep}, "
                + f"reason={row.gate_reason}, actor={row.gate_actor_hit}, score={score_str}"
            )

    print("\n=== SMOKE TEST COMPLETE ===")

    # Return success if we processed some titles and have expected results
    actual_kept = len([r for r in results if r.gate_keep])

    if actual_kept >= 1:  # At least one should be kept
        print("RESULT: PASS")
        return True
    else:
        print("RESULT: FAIL - No titles kept as expected")
        return False


async def main():
    """Main entry point"""
    try:
        success = await run_smoke_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
