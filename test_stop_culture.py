#!/usr/bin/env python3
"""
Test script to verify stop_culture filtering is working correctly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from apps.filter.taxonomy_extractor import \
    create_multi_vocab_taxonomy_extractor


def test_stop_culture_filtering():
    """Test that stop_culture patterns properly block non-strategic titles"""

    # Create taxonomy extractor
    extractor = create_multi_vocab_taxonomy_extractor()

    # Test titles that should be BLOCKED by stop_culture
    blocked_titles = [
        "Real Madrid defeats Barcelona in El Clasico football match",
        "Netflix releases new film series on streaming platform",
        "Fashion week in Paris showcases new designer collections",
        "Celebrity wedding ceremony attracts media attention",
        "Restaurant opens new location with vegan menu options",
        "Olympic games final results announced for tennis",
        "FIFA announces new tournament rules for next season",
        "Movie premiere night draws Hollywood stars",
        "Fashion campaign launched by luxury brand",
        "Wellness and fitness trends dominate lifestyle magazines",
    ]

    # Test titles that should be ALLOWED (strategic content)
    allowed_titles = [
        "Germany announces new defense spending amid NATO tensions",
        "Biden meets with Ukrainian president to discuss aid",
        "China trade negotiations continue with European Union",
        "Iran nuclear program faces new sanctions from US",
        "Russia military operations expand in Eastern Europe",
    ]

    print("=== TESTING STOP_CULTURE FILTERING ===")
    print()

    print("Testing titles that SHOULD BE BLOCKED:")
    blocked_count = 0
    for i, title in enumerate(blocked_titles, 1):
        strategic_hit = extractor.strategic_first_hit(title)
        is_strategic = strategic_hit is not None

        status = "ALLOWED [FAIL]" if is_strategic else "BLOCKED [OK]"
        print(f"{i:2d}. {status} | {title}")

        if not is_strategic:
            blocked_count += 1

    print(
        f"\nBlocked: {blocked_count}/{len(blocked_titles)} ({blocked_count/len(blocked_titles)*100:.1f}%)"
    )
    print()

    print("Testing titles that SHOULD BE ALLOWED:")
    allowed_count = 0
    for i, title in enumerate(allowed_titles, 1):
        strategic_hit = extractor.strategic_first_hit(title)
        is_strategic = strategic_hit is not None

        status = "ALLOWED [OK]" if is_strategic else "BLOCKED [FAIL]"
        print(f"{i:2d}. {status} | {title}")

        if is_strategic:
            allowed_count += 1

    print(
        f"\nAllowed: {allowed_count}/{len(allowed_titles)} ({allowed_count/len(allowed_titles)*100:.1f}%)"
    )
    print()

    # Summary
    print("=== SUMMARY ===")
    print(
        f"Stop culture blocking rate: {blocked_count}/{len(blocked_titles)} ({blocked_count/len(blocked_titles)*100:.1f}%)"
    )
    print(
        f"Strategic content pass rate: {allowed_count}/{len(allowed_titles)} ({allowed_count/len(allowed_titles)*100:.1f}%)"
    )

    # Check if filtering is working as expected
    if blocked_count == len(blocked_titles) and allowed_count == len(allowed_titles):
        print("[OK] STOP_CULTURE FILTERING WORKING CORRECTLY")
        return True
    else:
        print("[FAIL] STOP_CULTURE FILTERING HAS ISSUES")
        return False


if __name__ == "__main__":
    test_stop_culture_filtering()
