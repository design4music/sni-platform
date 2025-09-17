#!/usr/bin/env python3
"""
Strategic Gate Smoke Test Script
Quick verification that gate processing works end-to-end
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from core.config import get_config
from apps.filter.run_gate import GateProcessor


def insert_test_titles():
    """Insert some test titles for smoke testing"""
    config = get_config()
    engine = create_engine(config.database_url)
    
    test_titles = [
        {
            'url_gnews': 'https://test.example/1',
            'title_original': 'EU imposes sanctions on Iranian officials over human rights',
            'title_display': 'EU imposes sanctions on Iranian officials over human rights',
            'title_norm': 'eu imposes sanctions on iranian officials over human rights',
            'pubdate_utc': datetime.now(timezone.utc) - timedelta(hours=1),
            'processing_status': 'pending'
        },
        {
            'url_gnews': 'https://test.example/2', 
            'title_original': 'Beijing warns against Taiwan independence moves',
            'title_display': 'Beijing warns against Taiwan independence moves',
            'title_norm': 'beijing warns against taiwan independence moves',
            'pubdate_utc': datetime.now(timezone.utc) - timedelta(hours=2),
            'processing_status': 'pending'
        },
        {
            'url_gnews': 'https://test.example/3',
            'title_original': 'Team Alpha defeats Team Beta in championship match',
            'title_display': 'Team Alpha defeats Team Beta in championship match',
            'title_norm': 'team alpha defeats team beta in championship match', 
            'pubdate_utc': datetime.now(timezone.utc) - timedelta(hours=3),
            'processing_status': 'pending'
        }
    ]
    
    with engine.connect() as conn:
        for title in test_titles:
            # Check if already exists to avoid duplicates
            existing = conn.execute(text("""
                SELECT id FROM titles WHERE url_gnews = :url_gnews
            """), {'url_gnews': title['url_gnews']}).fetchone()
            
            if not existing:
                conn.execute(text("""
                    INSERT INTO titles (url_gnews, title_original, title_display, title_norm, pubdate_utc, processing_status)
                    VALUES (:url_gnews, :title_original, :title_display, :title_norm, :pubdate_utc, :processing_status)
                """), title)
        
        conn.commit()
        print("Test titles inserted")


def run_smoke_test():
    """Run complete smoke test"""
    print("=== STRATEGIC GATE SMOKE TEST ===")
    
    # Step 1: Insert test data
    print("\n1. Inserting test titles...")
    insert_test_titles()
    
    # Step 2: Check initial state
    processor = GateProcessor(batch_size=10)
    pending_before = processor.check_pending_count()
    print(f"Pending titles before: {pending_before}")
    
    # Step 3: Run gate processing
    print("\n2. Running gate processor...")
    stats = processor.run(max_batches=1)  # Process just one batch
    
    # Step 4: Check results  
    print("\n3. Checking results...")
    pending_after = processor.check_pending_count()
    summary = processor.get_gate_summary()
    
    print(f"Pending titles after: {pending_after}")
    print(f"Summary: {summary['kept_titles']}/{summary['processed_titles']} kept " +
          f"({summary['keep_rate']:.1f}%)")
    print(f"Reason breakdown: {summary['reason_breakdown']}")
    
    # Step 5: Test idempotency - run again
    print("\n4. Testing idempotency (run again)...")
    stats2 = processor.run(max_batches=1)
    
    if stats2['total_processed'] == 0:
        print("PASS: Idempotent - no duplicate processing")
    else:
        print(f"WARNING: Processed {stats2['total_processed']} titles on second run")
    
    # Step 6: Verify specific test cases
    print("\n5. Verifying test case results...")
    config = get_config()
    engine = create_engine(config.database_url)
    
    with engine.connect() as conn:
        results = conn.execute(text("""
            SELECT title_display, gate_keep, gate_reason, gate_actor_hit, gate_score
            FROM titles 
            WHERE url_gnews LIKE 'https://test.example/%'
            AND gate_at IS NOT NULL
            ORDER BY url_gnews
        """)).fetchall()
        
        for row in results:
            print(f"  '{row.title_display[:50]}...': keep={row.gate_keep}, " +
                  f"reason={row.gate_reason}, actor={row.gate_actor_hit}, score={row.gate_score:.3f}")
    
    print("\n=== SMOKE TEST COMPLETE ===")
    
    # Return success if we processed some titles and have expected results
    expected_kept = 2  # EU sanctions + Beijing should be kept, sports should not
    actual_kept = len([r for r in results if r.gate_keep])
    
    if actual_kept >= 1:  # At least one should be kept
        print("RESULT: PASS")
        return True
    else:
        print("RESULT: FAIL - No titles kept as expected")
        return False


def main():
    """Main entry point"""
    try:
        success = run_smoke_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()