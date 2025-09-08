#!/usr/bin/env python3
"""
Check fulltext enrichment status
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

    print('Fulltext enrichment status:')
    print('=' * 50)

    with get_db_session() as session:
        result = session.execute(text('''
            SELECT 
                processing_status,
                COUNT(*) as count,
                ROUND(AVG(LENGTH(content))) as avg_content_length
            FROM articles 
            WHERE created_at > NOW() - INTERVAL '24 hours'
            GROUP BY processing_status
            ORDER BY processing_status
        '''))
        
        total = 0
        for status, count, avg_length in result.fetchall():
            print(f'{status:12}: {count:4} articles (avg content: {avg_length or 0:.0f} chars)')
            total += count
        
        print(f'{"TOTAL":12}: {total:4} articles')
        
        # Check recent successes
        result = session.execute(text('''
            SELECT COUNT(*) as successful_fetches
            FROM articles 
            WHERE processing_status = 'COMPLETED'
            AND created_at > NOW() - INTERVAL '24 hours'
            AND LENGTH(content) > 300
        '''))
        
        successful = result.fetchone()[0]
        print(f'\nSuccessful full-text articles (>300 chars): {successful}')
        
        # Check what still needs processing
        result = session.execute(text('''
            SELECT COUNT(*) as pending
            FROM articles 
            WHERE processing_status = 'PENDING'
            AND created_at > NOW() - INTERVAL '24 hours'
        '''))
        
        pending = result.fetchone()[0]
        print(f'Still pending full-text fetch: {pending}')

if __name__ == "__main__":
    main()