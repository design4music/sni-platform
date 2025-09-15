#!/usr/bin/env python3
"""
Run entity enrichment on ALL strategic titles for entity-based batching
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


from apps.clust1.entity_enrichment import get_entity_enrichment_service


def main():
    """Run comprehensive entity enrichment"""
    print("Running FULL entity enrichment on all strategic titles...")
    
    service = get_entity_enrichment_service()
    
    # Check current status
    print("\n=== CURRENT STATUS ===")
    status = service.get_enrichment_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Run enrichment on ALL titles (no time limit, high batch limit)
    print("\n=== RUNNING FULL ENRICHMENT ===")
    print("This will process ALL strategic titles that need entities...")
    
    # Process in large batches
    stats = service.enrich_titles_batch(since_hours=24*365, limit=10000)  # 1 year back, 10K limit
    
    print("\n=== ENRICHMENT COMPLETE ===")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Check final status
    print("\n=== FINAL STATUS ===")
    final_status = service.get_enrichment_status()
    for key, value in final_status.items():
        print(f"  {key}: {value}")
    
    print(f"\nSuccess! {stats['strategic']} strategic titles now have entities.")


if __name__ == "__main__":
    main()