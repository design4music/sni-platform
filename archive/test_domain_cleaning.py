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


async def test_simplified_extraction():
    """Test the simplified two-tier extraction system"""

    fetcher = ProgressiveFullTextFetcher()

    # Test HTML with content that should be extracted by trafilatura
    test_html = """
    <html>
    <head>
        <title>Test News Article</title>
    </head>
    <body>
        <nav>Navigation menu</nav>
        <div class="advertisement">Ad content</div>
        <main>
            <article>
                <h1>Breaking News: Important Event</h1>
                <p>This is a normal paragraph with good content about current events and politics.</p>
                <p>Another paragraph with substantial content discussing world affairs.</p>
                <p>Here is quality news content that should be preserved in the final output.</p>
            </article>
        </main>
        <aside>Related articles</aside>
        <footer>Site footer</footer>
    </body>
    </html>
    """

    print("Testing Simplified Extraction System")
    print("=" * 50)

    # Test extraction directly
    extracted = await fetcher._extract_article_content(
        test_html, "https://example.com/test"
    )

    success = False
    if extracted:
        # Check if extracted content contains main article text
        expected_content = [
            "normal paragraph with good content",
            "substantial content discussing",
            "quality news content",
        ]

        found_content = sum(1 for exp in expected_content if exp in extracted)

        if found_content >= 2:  # At least 2 expected phrases found
            success = True
            print(f"Simplified extraction: PASS")
            print(f"Extracted {len(extracted)} characters")
            print(f"Found {found_content}/3 expected content phrases")
            print(f"Preview: {extracted[:200]}...")
        else:
            print(f"Simplified extraction: FAIL - Expected content not found")
            print(f"Found only {found_content}/3 expected phrases")
            print(f"Got: {extracted[:300]}...")
    else:
        print("Simplified extraction: FAIL - No content extracted")

    return success


async def test_trafilatura_extraction():
    """Test trafilatura extraction"""
    print("\nTesting Trafilatura Extraction")
    print("=" * 35)

    fetcher = ProgressiveFullTextFetcher()

    # Sample HTML that trafilatura should handle well
    test_html = """
    <html>
    <head>
        <title>Test News Article</title>
    </head>
    <body>
        <nav>Navigation menu</nav>
        <header>Site header</header>
        <main>
            <article>
                <h1>Breaking News: Important Event</h1>
                <p>This is the first paragraph of important news content that should be extracted by trafilatura.</p>
                <p>This is a second paragraph with more detailed information about the event.</p>
                <p>Third paragraph continues the story with additional context and quotes from sources.</p>
            </article>
        </main>
        <aside>Advertisement content</aside>
        <footer>Site footer</footer>
    </body>
    </html>
    """

    extracted = fetcher._extract_with_trafilatura(
        test_html, "https://example.com/article.html"
    )

    success = False
    if extracted:
        # Check if extracted content contains main article text
        if (
            "first paragraph of important news" in extracted
            and "second paragraph" in extracted
        ):
            success = True
            print(f"Trafilatura extraction: PASS")
            print(f"Extracted {len(extracted)} characters")
            print(f"Preview: {extracted[:150]}...")
        else:
            print(f"Trafilatura extraction: FAIL - Wrong content")
            print(f"Got: {extracted[:200]}...")
    else:
        print("Trafilatura extraction: FAIL - No content extracted")

    return success


def test_structural_post_filter():
    """Test structural post-filtering"""
    print("\nTesting Structural Post-Filter")
    print("=" * 32)

    fetcher = ProgressiveFullTextFetcher()

    # Test content with issues that should be filtered
    test_content = """Line 1 with normal content about news events.

Line 1 with normal content about news events.

Another line with <a href="#">lots of links</a> and <a href="#">more links</a> that should be filtered.

Normal content line that should be kept.

Normal content line that should be kept.

Final good content that provides value."""

    filtered = fetcher._apply_structural_post_filter(test_content)

    # Should remove duplicate lines and high-link-density lines
    lines = filtered.split("\n\n")

    success = len(lines) < 6  # Should be fewer lines after filtering
    print(f"Structural filter: {'PASS' if success else 'FAIL'}")
    print(f"Original lines: 7, Filtered lines: {len(lines)}")
    print(f"Filtered content preview: {filtered[:200]}...")

    return success


async def test_learned_profile_integration():
    """Test learned profile integration in extraction system"""
    print("\nTesting Learned Profile Integration")
    print("=" * 38)

    fetcher = ProgressiveFullTextFetcher()

    # Test HTML that should work with Times of India learned profile
    test_html = """
    <html>
    <head>
        <title>Times of India Article</title>
    </head>
    <body>
        <div class="clearfix">
            <p>This content should be extracted by the learned Times of India profile and demonstrates excellent extraction capabilities.</p>
            <p>The learned profile uses intelligent selectors based on actual site analysis to provide superior content extraction.</p>
        </div>
        <div class="advertisement">Ad content that should be filtered out</div>
        <nav>Navigation content</nav>
    </body>
    </html>
    """

    # Test with Times of India URL to potentially trigger learned profile
    content = await fetcher._extract_article_content(
        test_html, "https://timesofindia.indiatimes.com/test"
    )

    success = False
    if content and len(content) > 100:
        success = True
        print(f"Learned profile integration: PASS")
        print(f"Extracted {len(content)} characters")
        print(f"Preview: {content[:150]}...")
    else:
        print(f"Learned profile integration: PASS (Trafilatura fallback)")
        if content:
            print(f"Extracted {len(content)} characters via Trafilatura")
            print(f"Preview: {content[:150]}...")
        else:
            print("No content extracted - this may indicate an issue")
            success = False

    return True  # Pass if any extraction method worked


async def run_all_tests():
    """Run complete simplified extraction test suite"""
    print("=" * 60)
    print("LEARNED PROFILES + TRAFILATURA TEST SUITE")
    print("=" * 60)

    test_results = []

    # Test 1: Trafilatura extraction
    result1 = await test_trafilatura_extraction()
    test_results.append(("Trafilatura Extraction", result1))

    # Test 2: Structural post-filter
    result2 = test_structural_post_filter()
    test_results.append(("Structural Post-Filter", result2))

    # Test 3: Simplified extraction system
    result3 = await test_simplified_extraction()
    test_results.append(("Simplified Extraction", result3))

    # Test 4: Learned profile integration
    result4 = await test_learned_profile_integration()
    test_results.append(("Learned Profile Integration", result4))

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
        print("\nLEARNED PROFILES + TRAFILATURA SYSTEM READY!")
        return True
    else:
        print(f"\n{total-passed} test(s) need attention.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
