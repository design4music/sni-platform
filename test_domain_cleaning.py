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

    extracted = fetcher._extract_with_trafilatura(test_html, "https://example.com/article.html")
    
    success = False
    if extracted:
        # Check if extracted content contains main article text
        if "first paragraph of important news" in extracted and "second paragraph" in extracted:
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
    lines = filtered.split('\n\n')
    
    success = len(lines) < 6  # Should be fewer lines after filtering
    print(f"Structural filter: {'PASS' if success else 'FAIL'}")
    print(f"Original lines: 7, Filtered lines: {len(lines)}")
    print(f"Filtered content preview: {filtered[:200]}...")
    
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
    print("TRAFILATURA + DOMAIN-AGNOSTIC EXTRACTION TEST SUITE")
    print("=" * 60)

    test_results = []

    # Test 1: Trafilatura extraction
    result1 = await test_trafilatura_extraction()
    test_results.append(("Trafilatura Extraction", result1))

    # Test 2: Structural post-filter
    result2 = test_structural_post_filter()
    test_results.append(("Structural Post-Filter", result2))

    # Test 3: Paragraph cleaning (fallback)
    result3 = test_paragraph_cleaning()
    test_results.append(("Paragraph Cleaning", result3))

    # Test 4: AMP detection
    result4 = await test_amp_detection()
    test_results.append(("AMP Detection", result4))

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
        print("\nTRAFILATURA + DOMAIN-AGNOSTIC EXTRACTION READY!")
        return True
    else:
        print(f"\n{total-passed} test(s) need attention.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
