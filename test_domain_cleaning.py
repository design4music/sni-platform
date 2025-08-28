#!/usr/bin/env python3
"""
Test for domain-agnostic content extraction improvements
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our improved fetcher class
from etl_pipeline.ingestion.fetch_fulltext import ProgressiveFullTextFetcher


def test_paragraph_cleaning():
    """Test the generic paragraph-level cleaning logic"""

    fetcher = ProgressiveFullTextFetcher()

    # Test cases for generic paragraph filtering
    test_paragraphs = [
        "https://p.dw.com/p/4zXc3",  # Should be removed (first line URL)
        "Updated- August 27, 2025 10:27 am IST - Breaking news",  # Should be removed (timestamp)
        "Our Privacy Statement & Cookie Policy By continuing to browse our site you agree to our use of cookies.",  # Should be removed (privacy)
        "The TOI Business Desk is a vigilant and dedicated team of journalists committed to delivering the latest news.",  # Should be removed (promo)
        "WORLDWEST ASIAASIA-PACIFICAFRICAUSEUROPEUKAMERICASSOCIETYARTSSPORTSCONVERSATIONS IRANPOLITICSECONOMYENERGYNUCLEAR",  # Should be removed (menu)
        "This is a normal paragraph with good content about current events and politics.",  # Should be kept
        "Another paragraph with substantial content discussing world affairs.",  # Should be kept
        "Short text",  # Should be removed (too short)
        "READ MORE: Click here for more articles",  # Should be removed (also read)
        "Here is quality news content that should be preserved in the final output.",  # Should be kept
    ]

    print("Testing Generic Paragraph Cleaning")
    print("=" * 50)

    # Test cleaning
    cleaned = fetcher._clean_paragraphs(test_paragraphs, "Test Article Title")

    print(f"Original paragraphs: {len(test_paragraphs)}")
    print(f"Cleaned paragraphs: {len(cleaned)}")
    print("\nKept paragraphs:")
    for i, para in enumerate(cleaned, 1):
        print(f"{i}. {para[:80]}{'...' if len(para) > 80 else ''}")

    # Test scoring and selection
    selected = fetcher._select_best_content_run(cleaned, "Test Article Title")
    print(f"\nSelected best run: {len(selected)} paragraphs")

    # Expect to keep ~3 good paragraphs
    expected_kept = [
        "This is a normal paragraph",
        "Another paragraph with substantial",
        "Here is quality news content",
    ]
    actual_kept = [
        para for para in cleaned if any(exp in para for exp in expected_kept)
    ]

    success = len(actual_kept) >= 2  # At least 2 good paragraphs kept
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")
    print(f"Expected good content preserved: {success}")

    return success


async def test_amp_detection():
    """Test AMP URL detection"""
    print("\nTesting AMP Detection")
    print("=" * 30)

    fetcher = ProgressiveFullTextFetcher()

    # Sample HTML with AMP link
    test_html = """
    <html>
    <head>
        <title>Test Article</title>
        <link rel="amphtml" href="https://example.com/amp/article.html">
    </head>
    <body>
        <article>
            <p>This is test content.</p>
        </article>
    </body>
    </html>
    """

    amp_url = await fetcher._find_amp_url(test_html, "https://example.com/article.html")

    expected_amp = "https://example.com/amp/article.html"
    success = amp_url == expected_amp

    print(f"AMP detection: {'PASS' if success else 'FAIL'}")
    print(f"Expected: {expected_amp}")
    print(f"Found: {amp_url}")

    return success


async def run_all_tests():
    """Run complete domain-agnostic extraction test suite"""
    print("=" * 60)
    print("DOMAIN-AGNOSTIC EXTRACTION TEST SUITE")
    print("=" * 60)

    test_results = []

    # Test 1: Paragraph cleaning
    result1 = test_paragraph_cleaning()
    test_results.append(("Paragraph Cleaning", result1))

    # Test 2: AMP detection
    result2 = await test_amp_detection()
    test_results.append(("AMP Detection", result2))

    # Summary
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    print(f"\n{'='*60}")
    print("TEST SUITE SUMMARY")
    print("=" * 60)

    for test_name, result in test_results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")

    print(f"\nTests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("\nDOMAIN-AGNOSTIC EXTRACTION READY!")
        return True
    else:
        print(f"\n{total-passed} test(s) need attention.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
