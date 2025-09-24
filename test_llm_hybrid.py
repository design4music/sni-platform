#!/usr/bin/env python3
"""
Test script to verify LLM hybrid filtering is working correctly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from apps.filter.entity_enrichment import get_entity_enrichment_service

def test_llm_hybrid_filtering():
    """Test that LLM hybrid filtering works for ambiguous titles"""

    service = get_entity_enrichment_service()

    # Test titles that should trigger LLM (no static taxonomy match)
    ambiguous_titles = [
        "Biden meets with Ukrainian president to discuss aid",  # Should be strategic via LLM
        "New cybersecurity regulations announced by government",  # Should be strategic via LLM
        "Environmental protests disrupt economic summit",  # Should be strategic via LLM
        "Celebrity wedding ceremony in Paris",  # Should be non-strategic
        "Local restaurant wins cooking competition",  # Should be non-strategic
    ]

    # Test titles that should use static taxonomy (no LLM needed)
    static_titles = [
        "Germany announces new defense spending amid NATO tensions",  # Strategic via static
        "Real Madrid defeats Barcelona in El Clasico",  # Non-strategic via static (if stop words worked)
    ]

    print("=== TESTING LLM HYBRID FILTERING ===")
    print()

    print("Testing AMBIGUOUS titles (should trigger LLM):")
    for i, title in enumerate(ambiguous_titles, 1):
        title_data = {"title_display": title}
        entities = service.extract_entities_for_title(title_data)

        used_llm = "llm_strategic" in entities.get("actors", [])
        is_strategic = entities["is_strategic"]

        status = "STRATEGIC" if is_strategic else "NON-STRATEGIC"
        llm_flag = "(LLM)" if used_llm else "(STATIC)"

        print(f"{i:2d}. {status} {llm_flag} | {title}")

    print()
    print("Testing STATIC taxonomy titles (should NOT trigger LLM):")
    for i, title in enumerate(static_titles, 1):
        title_data = {"title_display": title}
        entities = service.extract_entities_for_title(title_data)

        used_llm = "llm_strategic" in entities.get("actors", [])
        is_strategic = entities["is_strategic"]

        status = "STRATEGIC" if is_strategic else "NON-STRATEGIC"
        llm_flag = "(LLM)" if used_llm else "(STATIC)"

        print(f"{i:2d}. {status} {llm_flag} | {title}")

    print()
    print("=== TEST COMPLETE ===")
    print("Expected: Ambiguous titles use LLM, static titles use taxonomy")

if __name__ == "__main__":
    test_llm_hybrid_filtering()