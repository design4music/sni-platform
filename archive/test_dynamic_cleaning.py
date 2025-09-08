#!/usr/bin/env python3
"""
Test the new dynamic source attribution cleaning system
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etl_pipeline.ingestion.rss_handler import clean_source_attribution, filter_cgtn_cookie_content

def test_dynamic_cleaning():
    """Test the dynamic source attribution cleaning function"""
    test_cases = [
        # (title, feed_name, expected_result)
        
        # DW with dash separator (RSS feed)
        ("German economy faces challenges - DW", "DW", "German economy faces challenges"),
        
        # NPR with colon separator (RSS feed)  
        ("Biden visits Japan: NPR", "NPR", "Biden visits Japan"),
        ("Climate report released : NPR", "NPR", "Climate report released"),
        
        # Google News feeds with various patterns
        ("Markets fall sharply zerohedge.com", "zerohedge.com", "Markets fall sharply"),
        ("Trump policy update The Washington Post", "The Washington Post", "Trump policy update"),
        ("Economic analysis - The New York Times", "The New York Times", "Economic analysis"),
        ("Breaking news (Reuters)", "Reuters", "Breaking news"),
        
        # Website domains should always be removed
        ("Tech story techcrunch.com", "Different Feed", "Tech story"),
        ("News update afp.com", "Some Other Feed", "News update"),
        
        # Should not modify when no match
        ("Clean title with no attribution", "DW", "Clean title with no attribution"),
        
        # Edge cases with punctuation
        ("Article title - DW,", "DW", "Article title"),
        ("Story: NPR .", "NPR", "Story"),
        
        # Handle "The" prefix variations
        ("News story The Washington Post", "The Washington Post", "News story"),
        ("Article - Washington Post", "The Washington Post", "Article"),
        
        # Multiple separator types
        ("Update | BBC", "BBC", "Update"),
        ("Report [Reuters]", "Reuters", "Report"),
        
        # Unicode dashes
        ("Story \u2013 DW", "DW", "Story"),
        ("Article \u2014 NPR", "NPR", "Article"),
    ]
    
    print("Testing dynamic source attribution cleaning:")
    print("=" * 90)
    
    all_passed = True
    for original, feed_name, expected in test_cases:
        result = clean_source_attribution(original, feed_name)
        status = "PASS" if result == expected else "FAIL"
        if status == "FAIL":
            all_passed = False
        
        print(f"{status:4} | Feed: {feed_name:20} | '{original}'")
        print(f"     | Result: {result}")
        if result != expected:
            print(f"     | Expected: {expected}")
        print("-" * 90)
    
    return all_passed

def test_cgtn_filtering():
    """Test CGTN cookie consent filtering (should work for all feeds)"""
    test_content = """
    By continuing to browse our site you agree to our use of cookies, revised Privacy Policy and Terms of Use. You can change your cookie settings through your browser.
    
    This is the actual article content that should remain. Important geopolitical developments continue to shape the region.
    
    Additional content that should be preserved.
    """
    
    expected = "This is the actual article content that should remain. Important geopolitical developments continue to shape the region. Additional content that should be preserved."
    
    result = filter_cgtn_cookie_content(test_content)
    
    print("\nTesting CGTN cookie filtering:")
    print("=" * 90)
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
    print("Testing Dynamic Source Attribution Cleaning System\n")
    
    attribution_test_passed = test_dynamic_cleaning()
    cgtn_test_passed = test_cgtn_filtering()
    
    print("\n" + "=" * 90)
    print("SUMMARY:")
    print(f"Source attribution cleaning: {'PASS' if attribution_test_passed else 'FAIL'}")
    print(f"CGTN cookie filtering: {'PASS' if cgtn_test_passed else 'FAIL'}")
    print(f"Overall result: {'ALL TESTS PASSED' if attribution_test_passed and cgtn_test_passed else 'SOME TESTS FAILED'}")
    
    if attribution_test_passed and cgtn_test_passed:
        print("\nThe dynamic cleaning system is ready for production!")
    else:
        print("\nSome tests failed - please review the cleaning logic.")