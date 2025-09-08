#!/usr/bin/env python3
"""
Test LLM-powered extraction profiles system
"""

import asyncio
import json
import sys
from unittest.mock import Mock, patch

sys.path.append('.')

from tools.learn_feed_extractors import FeedExtractorLearner


def test_profile_schema():
    """Test the extraction profile JSON schema"""
    learner = FeedExtractorLearner()
    schema = learner.get_profile_schema()
    
    # Verify all required fields are present
    required_fields = [
        "version", "scope", "main_selector", "title_selector", "date_selector", 
        "author_selector", "remove_selectors", "allow_tags", "junk_phrases",
        "pre_clean_regex", "post_clean_regex", "min_length", "density_threshold",
        "last_validated_at", "source", "notes"
    ]
    
    for field in required_fields:
        assert field in schema, f"Required field '{field}' missing from schema"
    
    # Verify correct defaults
    assert schema["version"] == 1
    assert schema["scope"] in ["feed", "domain"]
    assert schema["source"] == "llm"
    assert schema["min_length"] >= 100
    assert schema["density_threshold"] > 0
    
    print("Profile schema validation: PASS")
    return True


def test_html_structure_analysis():
    """Test HTML structure analysis for LLM"""
    learner = FeedExtractorLearner()
    
    # Test HTML with typical news article structure
    test_html = """
    <html>
    <head><title>Test News Article</title></head>
    <body>
        <nav class="navigation">Menu</nav>
        <header class="site-header">Header</header>
        <main class="main-content">
            <article class="article-body">
                <h1 class="article-title">Breaking News: Important Event</h1>
                <div class="byline">By Reporter Name</div>
                <div class="article-content">
                    <p>This is the main article content with substantial text that should be extracted.</p>
                    <p>Another paragraph with more detailed information about the news event.</p>
                </div>
            </article>
            <aside class="sidebar">Related articles</aside>
        </main>
        <footer class="site-footer">Footer</footer>
    </body>
    </html>
    """
    
    analysis = learner.analyze_html_structure(test_html, "https://example.com/article")
    
    # Verify analysis structure
    assert "url" in analysis
    assert "top_tags" in analysis
    assert "top_classes" in analysis
    assert "content_candidates" in analysis
    assert "title_candidates" in analysis
    
    # Check content candidates
    candidates = analysis["content_candidates"]
    assert len(candidates) > 0
    
    # Should find the article content
    found_main_content = any("main article content" in c["text_preview"] for c in candidates)
    assert found_main_content, "Main article content not found in candidates"
    
    # Check title candidates
    title_candidates = analysis["title_candidates"]
    assert len(title_candidates) > 0
    
    # Should find the h1 title
    found_title = any("Breaking News" in t["text"] for t in title_candidates)
    assert found_title, "Article title not found in candidates"
    
    print("HTML structure analysis: PASS")
    return True


def test_profile_validation():
    """Test profile validation against HTML samples"""
    learner = FeedExtractorLearner()
    
    # Create test profile
    profile = {
        "version": 1,
        "scope": "feed",
        "main_selector": ".article-content",
        "remove_selectors": [".sidebar", ".advertisement"],
        "allow_tags": ["p", "h2", "h3", "ul", "li"],
        "junk_phrases": ["Subscribe now", "Related articles"],
        "pre_clean_regex": [],
        "post_clean_regex": [],
        "min_length": 100,
        "density_threshold": 0.10
    }
    
    # Test HTML samples
    html_samples = [
        ("https://example.com/1", """
        <html><body>
            <div class="article-content">
                <p>This is a good article with sufficient content for validation testing.</p>
                <p>Another paragraph with more substantial content that meets length requirements.</p>
                <p>Third paragraph to ensure we have enough text for validation.</p>
            </div>
            <div class="sidebar">Sidebar content</div>
        </body></html>
        """),
        ("https://example.com/2", """
        <html><body>
            <div class="article-content">
                <p>Second article with good content length and quality.</p>
                <p>More content here to test profile validation functionality.</p>
                <p>Subscribe now to get more content.</p>
            </div>
        </body></html>
        """),
    ]
    
    passes, results = learner.validate_profile(profile, html_samples)
    
    assert isinstance(passes, bool)
    assert "success_rate" in results
    assert "results" in results
    assert len(results["results"]) == 2
    
    # Should pass validation with good content
    assert results["success_rate"] > 0.5, f"Low success rate: {results['success_rate']}"
    
    print("Profile validation: PASS")
    return True


def test_learned_profile_extraction():
    """Test learned profile extraction in fetch_fulltext"""
    from etl_pipeline.ingestion.fetch_fulltext import ProgressiveFullTextFetcher
    
    fetcher = ProgressiveFullTextFetcher()
    
    # Test learned profile extraction
    profile = {
        "version": 1,
        "main_selector": ".content",
        "remove_selectors": [".ads", ".social"],
        "allow_tags": ["p", "h2", "h3"],
        "junk_phrases": ["Advertisement"],
        "pre_clean_regex": [],
        "post_clean_regex": [],
        "min_length": 50,
        "density_threshold": 0.05
    }
    
    html = """
    <html>
    <body>
        <div class="content">
            <h2>Article Title</h2>
            <p>This is the main article content that should be extracted by the learned profile.</p>
            <p>Another paragraph with substantial content.</p>
        </div>
        <div class="ads">Advertisement content</div>
        <div class="social">Share buttons</div>
    </body>
    </html>
    """
    
    extracted = fetcher._extract_with_learned_profile(html, profile)
    
    assert extracted is not None, "Learned profile extraction failed"
    assert "main article content" in extracted, "Expected content not found"
    assert "Advertisement" not in extracted, "Junk phrase not removed"
    assert len(extracted) >= 50, f"Extracted content too short: {len(extracted)}"
    
    print("Learned profile extraction: PASS")
    return True


def run_all_tests():
    """Run all LLM profiles tests"""
    print("=" * 60)
    print("LLM EXTRACTION PROFILES TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Profile Schema", test_profile_schema),
        ("HTML Structure Analysis", test_html_structure_analysis),
        ("Profile Validation", test_profile_validation),
        ("Learned Profile Extraction", test_learned_profile_extraction),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"{test_name}: FAIL - {e}")
            results.append((test_name, False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n{'='*60}")
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\nLLM EXTRACTION PROFILES SYSTEM READY!")
        return True
    else:
        print(f"\n{total-passed} test(s) need attention.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)