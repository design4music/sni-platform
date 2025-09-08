#!/usr/bin/env python3
"""
Check DW article titles and update feed names
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

    print('Checking DW article titles:')
    print('=' * 80)

    with get_db_session() as session:
        # Check DW articles specifically
        result = session.execute(text('''
            SELECT nf.name as feed_name, a.title, LEFT(a.summary, 100) as summary_preview,
                   COUNT(*) OVER (PARTITION BY nf.name) as article_count
            FROM articles a
            JOIN news_feeds nf ON a.feed_id = nf.id
            WHERE nf.name LIKE '%DW%'
            AND a.created_at > NOW() - INTERVAL '7 days'
            ORDER BY a.created_at DESC
            LIMIT 15
        '''))
        
        dw_feeds_usage = {}
        for feed_name, title, summary, count in result.fetchall():
            if feed_name not in dw_feeds_usage:
                dw_feeds_usage[feed_name] = count
            print(f'Feed: {feed_name}')
            print(f'Title: {title}')
            if summary:
                print(f'Summary: {summary}...')
            print('-' * 40)
        
        print('\nDW Feed Usage Summary:')
        for feed_name, count in dw_feeds_usage.items():
            print(f'{feed_name}: {count} articles in last 7 days')
        
        # Also check some Google RSS articles to see current attribution
        print('\n' + '=' * 80)
        print('Sample Google RSS articles (current state):')
        
        result = session.execute(text('''
            SELECT nf.name as feed_name, a.title
            FROM articles a
            JOIN news_feeds nf ON a.feed_id = nf.id
            WHERE nf.feed_type = 'google_rss'
            AND a.created_at > NOW() - INTERVAL '2 days'
            ORDER BY a.created_at DESC
            LIMIT 10
        '''))
        
        for feed_name, title in result.fetchall():
            print(f'{feed_name}: {title}')

if __name__ == "__main__":
    main()