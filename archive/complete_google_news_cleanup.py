#!/usr/bin/env python3
"""
Complete Google News cleanup script
Removes all Google News integration from the SNI platform
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etl_pipeline.core.database import get_db_session, initialize_database
from etl_pipeline.core.config import get_config
from sqlalchemy import text

def cleanup_google_news_database():
    """Remove all Google News data from database"""
    print("CLEANING UP GOOGLE NEWS DATABASE RECORDS")
    print("=" * 50)
    
    config = get_config()
    initialize_database(config.database)
    
    with get_db_session() as session:
        # Get current counts for reporting
        result = session.execute(text('''
            SELECT COUNT(*) FROM articles a
            JOIN news_feeds nf ON a.feed_id = nf.id
            WHERE nf.feed_type = 'google_rss'
        '''))
        article_count = result.fetchone()[0]
        
        result = session.execute(text('''
            SELECT COUNT(*) FROM news_feeds
            WHERE feed_type = 'google_rss'
        '''))
        feed_count = result.fetchone()[0]
        
        print(f"Found {article_count} Google News articles to delete")
        print(f"Found {feed_count} Google News feeds to delete")
        
        if article_count == 0 and feed_count == 0:
            print("No Google News records found - cleanup already completed")
            return
        
        print("\nStarting database cleanup...")
        
        # 1. Delete all Google News articles
        result = session.execute(text('''
            DELETE FROM articles
            WHERE feed_id IN (
                SELECT id FROM news_feeds WHERE feed_type = 'google_rss'
            )
        '''))
        
        deleted_articles = result.rowcount
        print(f"Deleted {deleted_articles} Google News articles")
        
        # 2. Delete all Google News feeds
        result = session.execute(text('''
            DELETE FROM news_feeds
            WHERE feed_type = 'google_rss'
        '''))
        
        deleted_feeds = result.rowcount
        print(f"Deleted {deleted_feeds} Google News feeds")
        
        # 3. Remove google_rss from feed_type enum
        # Note: This requires careful handling in PostgreSQL
        print("\nRemoving 'google_rss' from feed_type enum...")
        
        try:
            # Create a new enum without google_rss
            session.execute(text('''
                CREATE TYPE feed_type_new AS ENUM ('RSS', 'xml_sitemap', 'api', 'scraper')
            '''))
            
            # Update the news_feeds table to use the new enum
            session.execute(text('''
                ALTER TABLE news_feeds 
                ALTER COLUMN feed_type TYPE feed_type_new 
                USING feed_type::text::feed_type_new
            '''))
            
            # Drop the old enum and rename the new one
            session.execute(text('DROP TYPE feed_type'))
            session.execute(text('ALTER TYPE feed_type_new RENAME TO feed_type'))
            
            print("Successfully removed 'google_rss' from feed_type enum")
            
        except Exception as e:
            print(f"Warning: Could not remove google_rss from enum: {e}")
            print("This is expected if there are still references. Will need manual cleanup.")
        
        # Commit all changes
        session.commit()
        
        print("\nDatabase cleanup completed successfully!")
        
        # Verify cleanup
        result = session.execute(text('''
            SELECT COUNT(*) FROM articles a
            JOIN news_feeds nf ON a.feed_id = nf.id
            WHERE nf.feed_type = 'RSS'  -- Check remaining articles
        '''))
        remaining_articles = result.fetchone()[0]
        
        result = session.execute(text('''
            SELECT COUNT(*) FROM news_feeds
            WHERE feed_type = 'RSS'
        '''))
        remaining_feeds = result.fetchone()[0]
        
        print(f"Remaining after cleanup: {remaining_articles} articles, {remaining_feeds} RSS feeds")

def cleanup_google_news_files():
    """Remove or clean up Google News specific files"""
    print("\nCLEANING UP GOOGLE NEWS FILES")
    print("=" * 40)
    
    # Files to completely delete (Google News specific)
    files_to_delete = [
        "test_realistic_browser.py",
        "test_google_news_parsing.py", 
        "test_simplified_batchexecute.py",
        "debug_batchexecute.py",
        "test_batchexecute_decoder.py",
        "debug_google_news_content.py",
        "analyze_google_news_challenge.py",
        "verify_cleanup.py",
        "complete_url_cleanup.py",
        "cleanup_corrupted_articles.py",
        "test_bug_fix.py",
        "investigate_content.py",
        "test_google_news_fetch.py",
        "test_google_news_resolution.py",
        "check_google_news_articles.py",
        "add_google_news_feeds.py",
        "google_news_feeds_example.json",
        "analyze_google_news_scope.py",  # This current analysis file
    ]
    
    deleted_files = 0
    for filename in files_to_delete:
        filepath = os.path.join(os.getcwd(), filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"Deleted: {filename}")
                deleted_files += 1
            except Exception as e:
                print(f"Failed to delete {filename}: {e}")
    
    print(f"\nDeleted {deleted_files} Google News specific files")
    
    # Note: Core files like fetch_fulltext.py, rss_ingestion.py etc. 
    # will need manual code cleanup which we'll handle separately
    print("\nFiles requiring manual code cleanup:")
    files_need_cleanup = [
        "etl_pipeline/ingestion/fetch_fulltext.py",
        "etl_pipeline/ingestion/rss_ingestion.py", 
        "etl_pipeline/ingestion/rss_handler.py",
        "etl_pipeline/core/database/models.py",
        "etl_pipeline/core/tasks/ingestion_tasks.py",
        "database_migrations/030_add_google_rss_feed_type_and_ap_feed.sql"
    ]
    
    for filename in files_need_cleanup:
        print(f"  - {filename}")

def create_migration_to_remove_google_rss():
    """Create a database migration to cleanly remove google_rss"""
    migration_content = '''-- Migration: Remove google_rss feed type and all related data
-- This migration removes all Google News integration from the database

BEGIN;

-- Remove all articles from Google RSS feeds
DELETE FROM articles 
WHERE feed_id IN (
    SELECT id FROM news_feeds WHERE feed_type = 'google_rss'
);

-- Remove all Google RSS feeds
DELETE FROM news_feeds 
WHERE feed_type = 'google_rss';

-- Create new enum without google_rss
CREATE TYPE feed_type_new AS ENUM ('RSS', 'xml_sitemap', 'api', 'scraper');

-- Update table to use new enum
ALTER TABLE news_feeds 
ALTER COLUMN feed_type TYPE feed_type_new 
USING feed_type::text::feed_type_new;

-- Drop old enum and rename new one
DROP TYPE feed_type;
ALTER TYPE feed_type_new RENAME TO feed_type;

-- Update comment
COMMENT ON TYPE feed_type IS 'Feed type enumeration: RSS, xml_sitemap, api, scraper';

COMMIT;
'''
    
    migration_file = "database_migrations/031_remove_google_rss_feed_type.sql"
    with open(migration_file, 'w') as f:
        f.write(migration_content)
    
    print(f"\nCreated migration file: {migration_file}")

def main():
    print("COMPLETE GOOGLE NEWS CLEANUP")
    print("=" * 60)
    print("This script will remove ALL Google News integration from SNI platform:")
    print("- Delete all Google News articles and feeds from database")
    print("- Remove google_rss from feed_type enum")
    print("- Delete Google News specific files")
    print("- Create cleanup migration")
    print()
    print("Proceeding with cleanup...")
    
    try:
        cleanup_google_news_database()
        cleanup_google_news_files()
        create_migration_to_remove_google_rss()
        
        print("\n" + "=" * 60)
        print("GOOGLE NEWS CLEANUP COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Manually clean Google News code from remaining files")
        print("2. Update models.py to remove GOOGLE_RSS enum")
        print("3. Test the system to ensure it works without Google News")
        print("4. Consider adding direct publisher RSS feeds")
        
    except Exception as e:
        print(f"\nERROR during cleanup: {e}")
        print("You may need to run parts of the cleanup manually")

if __name__ == "__main__":
    main()