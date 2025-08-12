#!/usr/bin/env python3
"""
Test English-only filtering across the pipeline
"""
import sys
import os
sys.path.append('.')

from etl_pipeline.extraction.dynamic_keyword_extractor import extract_dynamic_keywords

def test_english_only_filter():
    """Test that only English content is processed"""
    
    print("=== Testing English-Only Filter ===")
    
    # Test cases with different languages
    test_cases = [
        {
            'id': 'test_en',
            'title': 'Trump Meets Xi Jinping at Summit',
            'content': 'President Trump discussed trade with Chinese President Xi Jinping...',
            'language': 'en',
            'should_process': True
        },
        {
            'id': 'test_fr', 
            'title': 'Macron rencontre Poutine',
            'content': 'Le président français Emmanuel Macron a rencontré...',
            'language': 'fr',
            'should_process': False
        },
        {
            'id': 'test_de',
            'title': 'Merkel trifft Putin',
            'content': 'Die deutsche Bundeskanzlerin Angela Merkel...',
            'language': 'de', 
            'should_process': False
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting {test_case['language'].upper()} article:")
        print(f"Title: {test_case['title']}")
        
        result = extract_dynamic_keywords(
            test_case['id'],
            test_case['title'], 
            test_case['content'],
            language=test_case['language']
        )
        
        keyword_count = len(result.keywords)
        print(f"Keywords extracted: {keyword_count}")
        
        if test_case['should_process']:
            if keyword_count > 0:
                print("PASS: English content processed correctly")
                print(f"Top keywords: {[kw.text for kw in result.keywords[:3]]}")
            else:
                print("FAIL: English content should have keywords")
        else:
            if keyword_count == 0:
                print("PASS: Non-English content skipped correctly")
                print(f"Skipped stats: {result.filter_stats}")
            else:
                print("FAIL: Non-English content should be skipped")
                print(f"Unexpected keywords: {[kw.text for kw in result.keywords[:3]]}")

if __name__ == "__main__":
    test_english_only_filter()