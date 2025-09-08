#!/usr/bin/env python3
"""
Update news_feeds.name values to match actual source attribution patterns
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etl_pipeline.core.database import get_db_session, initialize_database
from etl_pipeline.core.config import get_config
from sqlalchemy import text

def main():
    config = get_config()
    initialize_database(config.database)

    # First check DW feed usage
    print('Checking DW feed usage:')
    print('=' * 80)

    with get_db_session() as session:
        # Check DW feed activity
        result = session.execute(text('''
            SELECT 
                nf.name as feed_name, 
                nf.url,
                COUNT(a.id) as total_articles,
                COUNT(CASE WHEN a.created_at > NOW() - INTERVAL '7 days' THEN 1 END) as recent_articles,
                MAX(a.created_at) as last_article
            FROM news_feeds nf
            LEFT JOIN articles a ON nf.id = a.feed_id
            WHERE nf.name LIKE '%DW%'
            GROUP BY nf.id, nf.name, nf.url
            ORDER BY recent_articles DESC, total_articles DESC
        '''))
        
        dw_feeds = []
        for feed_name, url, total, recent, last_article in result.fetchall():
            dw_feeds.append((feed_name, url, total, recent, last_article))
            print(f'{feed_name}:')
            print(f'  URL: {url}')
            print(f'  Total articles: {total}')
            print(f'  Recent (7 days): {recent}')
            print(f'  Last article: {last_article}')
            print()

        # Recommend which DW feed to keep
        if dw_feeds:
            best_feed = max(dw_feeds, key=lambda x: (x[3], x[2]))  # Most recent, then total
            print(f'RECOMMENDATION: Keep "{best_feed[0]}" as it has the most activity')
            print(f'  Recent articles: {best_feed[3]}, Total: {best_feed[2]}')
            
            # Show sample titles from the recommended feed
            result = session.execute(text('''
                SELECT a.title
                FROM articles a
                JOIN news_feeds nf ON a.feed_id = nf.id
                WHERE nf.name = :feed_name
                ORDER BY a.created_at DESC
                LIMIT 5
            '''), {'feed_name': best_feed[0]})
            
            print('\nSample titles from recommended DW feed:')
            for (title,) in result.fetchall():
                print(f'  {title}')

        # Now define the feed name updates
        feed_name_updates = [
            ('New York Times', 'The New York Times'),
            ('Washington Post', 'The Washington Post'), 
            ('ZeroHedge', 'zerohedge.com'),
            ('The Grayzone', 'thegrayzone.com'),
            ('Reuters Sitemap Sitemap', 'Reuters'),
            ('NPR World', 'NPR'),
            ('Associated Press (Google News)', 'AP News'),
            ('Agence France-Presse (AFP)', 'afp.com'),
        ]
        
        print('\n' + '=' * 80)
        print('Proposed feed name updates:')
        for old_name, new_name in feed_name_updates:
            print(f'"{old_name}" -> "{new_name}"')
            
        print('\nExecute these updates? (This will modify the database)')
        
if __name__ == "__main__":
    main()