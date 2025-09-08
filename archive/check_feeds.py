#!/usr/bin/env python3
"""
Check current news feeds and sample article titles
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etl_pipeline.core.database import get_db_session, initialize_database
from etl_pipeline.core.config import get_config
from sqlalchemy import text

def main():
    # Initialize database
    config = get_config()
    initialize_database(config.database)

    print('Current news feeds:')
    print('=' * 80)

    with get_db_session() as session:
        result = session.execute(text('''
            SELECT id, name, feed_type, is_active, url
            FROM news_feeds 
            ORDER BY feed_type, name
        '''))
        
        dw_feeds = {}
        all_feeds = []
        for feed_id, name, feed_type, is_active, url in result.fetchall():
            status = 'ACTIVE' if is_active else 'INACTIVE'
            print(f'{feed_type:12} | {status:8} | {name}')
            all_feeds.append((feed_id, name, feed_type))
            if 'DW' in name:
                dw_feeds[name] = (feed_id, url)
        
        print('\nDW Feeds found:')
        for name, (feed_id, url) in dw_feeds.items():
            print(f'{name}: {url}')
            
        # Check recent articles to see actual source attribution patterns
        print('\nSample article titles to check source attribution patterns:')
        print('=' * 80)
        
        result = session.execute(text('''
            SELECT nf.name as feed_name, a.title, LEFT(a.summary, 100) as summary_preview
            FROM articles a
            JOIN news_feeds nf ON a.feed_id = nf.id
            WHERE a.created_at > NOW() - INTERVAL '24 hours'
            ORDER BY a.created_at DESC
            LIMIT 20
        '''))
        
        for feed_name, title, summary in result.fetchall():
            print(f'Feed: {feed_name}')
            print(f'Title: {title}')
            if summary:
                print(f'Summary: {summary}...')
            print()

if __name__ == "__main__":
    main()