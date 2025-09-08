#!/usr/bin/env python3
"""
Clean Google News specific code from core pipeline files
"""
import os
import re

def clean_fetch_fulltext():
    """Remove Google News resolution methods from fetch_fulltext.py"""
    print("Cleaning fetch_fulltext.py...")
    
    filepath = "etl_pipeline/ingestion/fetch_fulltext.py"
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Remove the Google News URL resolution methods
    patterns_to_remove = [
        # Remove _resolve_google_news_batchexecute method
        r'    async def _resolve_google_news_batchexecute\(self[^}]*?\n        except Exception as e:\n            logger\.warning\(f"Error in batchexecute resolution for \{url\}: \{e\}"\)\n            return url\n\n',
        
        # Remove the batchexecute call from _resolve_google_news_url
        r'            # First, try the batchexecute method \(most reliable\)\n            resolved_url = await self\._resolve_google_news_batchexecute\(url\)\n            if resolved_url != url:\n                logger\.debug\(f"Batchexecute successfully resolved URL"\)\n                return resolved_url\n\n            logger\.debug\(f"Batchexecute failed, falling back to traditional redirect resolution"\)\n\n',
    ]
    
    original_content = content
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Simplify the _resolve_google_news_url method to just return the original URL
    # since we're not doing Google News resolution anymore
    simplified_method = '''    async def _resolve_google_news_url(self, url: str) -> str:
        """Google News URLs are no longer supported - return original URL"""
        logger.debug(f"Google News URLs no longer supported, returning original: {url}")
        return url
'''
    
    # Replace the entire _resolve_google_news_url method
    method_pattern = r'    async def _resolve_google_news_url\(self, url: str\) -> str:.*?(?=\n    async def|\n    def|\nclass|\Z)'
    content = re.sub(method_pattern, simplified_method.rstrip(), content, flags=re.DOTALL)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  -> Cleaned Google News code from {filepath}")
    else:
        print(f"  - No changes needed in {filepath}")

def clean_models():
    """Remove GOOGLE_RSS from models.py"""
    print("Cleaning models.py...")
    
    filepath = "etl_pipeline/core/database/models.py"
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove GOOGLE_RSS from FeedType enum
    content = re.sub(r'    GOOGLE_RSS = "google_rss"\n', '', content)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  -> Removed GOOGLE_RSS from {filepath}")
    else:
        print(f"  - No changes needed in {filepath}")

def clean_rss_ingestion():
    """Remove Google News specific code from rss_ingestion.py"""
    print("Cleaning rss_ingestion.py...")
    
    filepath = "etl_pipeline/ingestion/rss_ingestion.py"
    if not os.path.exists(filepath):
        print(f"  - File {filepath} not found")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove any Google News specific handling
    google_patterns = [
        r'.*google_rss.*\n',
        r'.*news\.google\.com.*\n',
        r'.*GOOGLE_RSS.*\n',
    ]
    
    for pattern in google_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  -> Cleaned Google News references from {filepath}")
    else:
        print(f"  - No changes needed in {filepath}")

def clean_rss_handler():
    """Remove Google News specific code from rss_handler.py"""
    print("Cleaning rss_handler.py...")
    
    filepath = "etl_pipeline/ingestion/rss_handler.py"
    if not os.path.exists(filepath):
        print(f"  - File {filepath} not found")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove Google News specific handling
    google_patterns = [
        r'.*google_rss.*\n',
        r'.*news\.google\.com.*\n',
        r'.*GOOGLE_RSS.*\n',
        r'.*Google News.*\n',
    ]
    
    for pattern in google_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  -> Cleaned Google News references from {filepath}")
    else:
        print(f"  - No changes needed in {filepath}")

def clean_ingestion_tasks():
    """Remove Google News specific code from ingestion_tasks.py"""
    print("Cleaning ingestion_tasks.py...")
    
    filepath = "etl_pipeline/core/tasks/ingestion_tasks.py"
    if not os.path.exists(filepath):
        print(f"  - File {filepath} not found")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove Google News specific handling
    google_patterns = [
        r'.*google_rss.*\n',
        r'.*news\.google\.com.*\n', 
        r'.*GOOGLE_RSS.*\n',
        r'.*Google News.*\n',
    ]
    
    for pattern in google_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  -> Cleaned Google News references from {filepath}")
    else:
        print(f"  - No changes needed in {filepath}")

def clean_unified_ingestion():
    """Remove Google News specific code from unified_ingestion.py"""
    print("Cleaning unified_ingestion.py...")
    
    filepath = "unified_ingestion.py"
    if not os.path.exists(filepath):
        print(f"  - File {filepath} not found")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove Google News specific handling
    google_patterns = [
        r'.*google_rss.*\n',
        r'.*news\.google\.com.*\n',
        r'.*GOOGLE_RSS.*\n',
        r'.*Google News.*\n',
    ]
    
    for pattern in google_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  -> Cleaned Google News references from {filepath}")
    else:
        print(f"  - No changes needed in {filepath}")

def clean_rss_ingestion_root():
    """Remove Google News specific code from rss_ingestion.py in root"""
    print("Cleaning rss_ingestion.py (root)...")
    
    filepath = "rss_ingestion.py"
    if not os.path.exists(filepath):
        print(f"  - File {filepath} not found")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove Google News specific handling
    google_patterns = [
        r'.*google_rss.*\n',
        r'.*news\.google\.com.*\n',
        r'.*GOOGLE_RSS.*\n',
        r'.*Google News.*\n',
    ]
    
    for pattern in google_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  -> Cleaned Google News references from {filepath}")
    else:
        print(f"  - No changes needed in {filepath}")

def main():
    print("CLEANING GOOGLE NEWS CODE FROM CORE FILES")
    print("=" * 50)
    
    try:
        clean_models()
        clean_fetch_fulltext()
        clean_rss_ingestion()
        clean_rss_handler()
        clean_ingestion_tasks()
        clean_unified_ingestion()
        clean_rss_ingestion_root()
        
        print("\n" + "=" * 50)
        print("CODE CLEANUP COMPLETED")
        print("=" * 50)
        print("\nCleaned files:")
        print("-> Removed GOOGLE_RSS from models.py")
        print("-> Simplified Google News URL resolution in fetch_fulltext.py")
        print("-> Cleaned Google News references from ingestion scripts")
        
        print("\nRecommendations:")
        print("1. Review the cleaned files to ensure no functionality is broken")
        print("2. Test the RSS ingestion pipeline without Google News")
        print("3. Consider adding direct publisher RSS feeds")
        
    except Exception as e:
        print(f"ERROR during code cleanup: {e}")

if __name__ == "__main__":
    main()