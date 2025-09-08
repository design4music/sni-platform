#!/usr/bin/env python3
"""
Test script for Google News title cleaning functions
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etl_pipeline.ingestion.rss_handler import clean_google_news_content, filter_cgtn_cookie_content

def test_title_cleaning():
    """Test the dynamic title cleaning function"""
    test_cases = [
        # (title, feed_name, expected_result)
        ("Greenland's Energy Stakes Trigger Denmark-U.S. Diplomatic Clash zerohedge.com", 
         "ZeroHedge", "Greenland's Energy Stakes Trigger Denmark-U.S. Diplomatic Clash"),
        
        ("How Trump's tax law will affect your state returns, in 4 charts The Washington Post",
         "Washington Post", "How Trump's tax law will affect your state returns, in 4 charts"),
        
        ("Breaking News Story - CNN", "CNN", "Breaking News Story"),
        
        ("Economic Analysis (Reuters)", "Reuters", "Economic Analysis"),
        
        ("Latest Tech News techcrunch.com", "TechCrunch", "Latest Tech News"),
        
        # Should not modify clean titles when feed name doesn't match
        ("Clean Article Title", "Some Other Feed", "Clean Article Title"),
        
        ("Market Update Financial Times", "Financial Times", "Market Update"),
        
        ("Economic Analysis ZeroHedge", "ZeroHedge", "Economic Analysis"),
        
        # Test with "The" prefix
        ("News Story The Grayzone", "The Grayzone", "News Story"),
        
        # Domain cleaning should work regardless of feed name
        ("Article Title somesite.com", "Different Feed", "Article Title"),
    ]
    
    print("Testing dynamic title cleaning function:")
    print("=" * 80)
    
    all_passed = True
    for original, feed_name, expected in test_cases:
        result = clean_google_news_content(original, feed_name)
        status = "PASS" if result == expected else "FAIL"
        if status == "FAIL":
            all_passed = False
        
        print(f"{status}: '{original}' (feed: {feed_name})")
        print(f"   -> '{result}'")
        if result != expected:
            print(f"   Expected: '{expected}'")
        print()
    
    return all_passed

def test_cgtn_filtering():
    """Test CGTN cookie consent filtering"""
    test_content = """
    By continuing to browse our site you agree to our use of cookies, revised Privacy Policy and Terms of Use. You can change your cookie settings through your browser.
    
    This is the actual article content that should remain. It talks about important news and events.
    
    More content here that should not be filtered out.
    """
    
    expected = "This is the actual article content that should remain. It talks about important news and events. More content here that should not be filtered out."
    
    result = filter_cgtn_cookie_content(test_content)
    
    print("Testing CGTN cookie filtering:")
    print("=" * 80)
    print("Original content:")
    print(repr(test_content))
    print("\nFiltered content:")
    print(repr(result))
    print("\nExpected:")
    print(repr(expected))
    
    passed = expected.strip() == result.strip()
    print(f"\nResult: {'PASS' if passed else 'FAIL'}")
    
    return passed

if __name__ == "__main__":
    print("Testing Google News cleaning functions\n")
    
    title_test_passed = test_title_cleaning()
    print()
    cgtn_test_passed = test_cgtn_filtering()
    
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print(f"Title cleaning: {'PASS' if title_test_passed else 'FAIL'}")
    print(f"CGTN filtering: {'PASS' if cgtn_test_passed else 'FAIL'}")
    print(f"Overall: {'ALL TESTS PASSED' if title_test_passed and cgtn_test_passed else 'SOME TESTS FAILED'}")