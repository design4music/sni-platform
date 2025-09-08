#!/usr/bin/env python3
"""
Execute the feed name updates and DW consolidation
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

    with get_db_session() as session:
        print('Executing feed updates:')
        print('=' * 80)
        
        # Feed name updates
        updates = [
            ('New York Times', 'The New York Times'),
            ('Washington Post', 'The Washington Post'), 
            ('ZeroHedge', 'zerohedge.com'),
            ('The Grayzone', 'thegrayzone.com'),
            ('Reuters Sitemap Sitemap', 'Reuters'),
            ('NPR World', 'NPR'),
            ('Associated Press (Google News)', 'AP News'),
            ('Agence France-Presse (AFP)', 'afp.com'),
            ('DW English', 'DW'),  # Rename the main DW feed
        ]
        
        for old_name, new_name in updates:
            result = session.execute(text('''
                UPDATE news_feeds 
                SET name = :new_name, updated_at = NOW()
                WHERE name = :old_name
            '''), {'old_name': old_name, 'new_name': new_name})
            
            if result.rowcount > 0:
                print(f'Updated "{old_name}" -> "{new_name}"')
            else:
                print(f'No feed found with name "{old_name}"')
        
        # Deactivate the other DW feeds
        dw_feeds_to_deactivate = ['DW Top', 'DW World']
        for feed_name in dw_feeds_to_deactivate:
            result = session.execute(text('''
                UPDATE news_feeds 
                SET is_active = false, updated_at = NOW()
                WHERE name = :feed_name
            '''), {'feed_name': feed_name})
            
            if result.rowcount > 0:
                print(f'Deactivated "{feed_name}"')
            else:
                print(f'No feed found with name "{feed_name}"')
        
        session.commit()
        
        print('\n' + '=' * 80)
        print('Updated feed list:')
        
        # Show updated feeds
        result = session.execute(text('''
            SELECT name, feed_type, is_active
            FROM news_feeds 
            WHERE name IN (
                'The New York Times', 'The Washington Post', 'zerohedge.com', 
                'thegrayzone.com', 'Reuters', 'NPR', 'AP News', 'afp.com', 'DW'
            ) OR name LIKE '%DW%'
            ORDER BY name
        '''))
        
        for name, feed_type, is_active in result.fetchall():
            status = 'ACTIVE' if is_active else 'INACTIVE'
            print(f'{name}: {feed_type} ({status})')

if __name__ == "__main__":
    main()