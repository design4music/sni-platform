#!/usr/bin/env python3
"""
Clean up existing article titles using the new dynamic source attribution cleaning system
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etl_pipeline.core.database import get_db_session, initialize_database
from etl_pipeline.core.config import get_config
from etl_pipeline.ingestion.rss_handler import clean_source_attribution, filter_cgtn_cookie_content
from sqlalchemy import text

def main():
    config = get_config()
    initialize_database(config.database)

    print('Analyzing existing article titles for cleanup opportunities:')
    print('=' * 80)

    with get_db_session() as session:
        # Get articles with titles that need cleanup
        result = session.execute(text('''
            SELECT 
                nf.name as feed_name,
                a.id as article_id,
                a.title as original_title
            FROM articles a
            JOIN news_feeds nf ON a.feed_id = nf.id
            WHERE a.title IS NOT NULL
            AND LENGTH(a.title) > 0
            ORDER BY a.created_at DESC
        '''))
        
        all_articles = list(result.fetchall())
        
        # Find titles that need cleanup
        cleanup_candidates = []
        for feed_name, article_id, title in all_articles:
            if title:
                cleaned_title = clean_source_attribution(title, feed_name)
                if cleaned_title != title:
                    cleanup_candidates.append((feed_name, article_id, title, cleaned_title))
        
        print(f'Analyzed {len(all_articles)} total articles')
        print(f'Found {len(cleanup_candidates)} article titles that need cleanup')
        print()
        
        # Show examples of what will be cleaned
        print('Examples of cleanup to be performed:')
        print('-' * 80)
        for feed_name, article_id, original_title, cleaned_title in cleanup_candidates[:15]:
            print(f'Feed: {feed_name}')
            print(f'  Original: "{original_title}"')
            print(f'  Cleaned:  "{cleaned_title}"')
            print()
        
        if cleanup_candidates:
            print(f'Proceeding with cleanup of {len(cleanup_candidates)} article titles...')
            
            # Execute the cleanup
            updated_count = 0
            for feed_name, article_id, original_title, cleaned_title in cleanup_candidates:
                try:
                    session.execute(text('''
                        UPDATE articles 
                        SET title = :cleaned_title, updated_at = NOW()
                        WHERE id = :article_id
                    '''), {'cleaned_title': cleaned_title, 'article_id': article_id})
                    updated_count += 1
                    
                    if updated_count % 100 == 0:
                        print(f'Updated {updated_count} articles...')
                        
                except Exception as e:
                    print(f'Error updating article {article_id}: {e}')
            
            session.commit()
            print(f'Successfully updated {updated_count} article titles!')
            
        else:
            print('No article titles found that need cleanup.')

if __name__ == "__main__":
    main()