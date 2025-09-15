#!/usr/bin/env python3
"""
RSS Ingestion Driver for SNI-v2
Runs RSS ingestion across all active strategic feeds
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.config import get_config
from apps.ingest.rss_fetcher import RSSFetcher


class IngestionRunner:
    """RSS ingestion runner for all active feeds"""
    
    def __init__(self):
        self.config = get_config()
        self.engine = create_engine(self.config.database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.fetcher = RSSFetcher()
        
        # Overall statistics
        self.stats = {
            'feeds_processed': 0,
            'feeds_success': 0,
            'feeds_errors': 0,
            'total_fetched': 0,
            'total_inserted': 0,
            'total_skipped': 0,
            'total_errors': 0,
            'start_time': datetime.now()
        }
    
    def get_active_feeds(self) -> List[Dict[str, Any]]:
        """Get all active feeds for ingestion"""
        with self.Session() as session:
            result = session.execute(text("""
                SELECT id, url, name, source_domain, language_code
                FROM feeds 
                WHERE is_active = true
                ORDER BY priority DESC, name
            """))
            
            return [
                {
                    'id': row.id,
                    'url': row.url,
                    'name': row.name,
                    'source_domain': row.source_domain,
                    'language_code': row.language_code
                }
                for row in result.fetchall()
            ]
    
    def run_ingestion(self, max_feeds: int = None) -> Dict[str, Any]:
        """
        Run RSS ingestion across all active feeds
        
        Args:
            max_feeds: Maximum number of feeds to process (None for all)
            
        Returns:
            Overall statistics
        """
        logger.info("Starting RSS ingestion across all strategic feeds...")
        
        feeds = self.get_active_feeds()
        if max_feeds:
            feeds = feeds[:max_feeds]
        
        logger.info(f"Found {len(feeds)} active feeds to process")
        
        for i, feed in enumerate(feeds, 1):
            logger.info(f"Processing feed {i}/{len(feeds)}: {feed['name']} ({feed['source_domain']})")
            
            try:
                # Run RSS fetch for this feed
                articles, feed_stats = self.fetcher.fetch_feed(feed['id'], feed['url'])
                
                # Update overall stats
                self.stats['feeds_processed'] += 1
                self.stats['feeds_success'] += 1
                self.stats['total_fetched'] += feed_stats.get('fetched', 0)
                self.stats['total_inserted'] += feed_stats.get('inserted', 0)
                self.stats['total_skipped'] += feed_stats.get('skipped', 0)
                self.stats['total_errors'] += feed_stats.get('errors', 0)
                
                logger.info(f"Feed complete: {feed['name']} - "
                          f"fetched: {feed_stats.get('fetched', 0)}, "
                          f"inserted: {feed_stats.get('inserted', 0)}, "
                          f"skipped: {feed_stats.get('skipped', 0)}")
                
            except Exception as e:
                logger.error(f"Feed processing failed: {feed['name']} - {e}")
                self.stats['feeds_processed'] += 1
                self.stats['feeds_errors'] += 1
                continue
        
        # Calculate final stats
        self.stats['end_time'] = datetime.now()
        self.stats['total_duration'] = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        self._log_summary()
        return self.stats
    
    def _log_summary(self):
        """Log ingestion summary statistics"""
        stats = self.stats
        logger.info("=== RSS INGESTION SUMMARY ===")
        logger.info(f"Feeds processed: {stats['feeds_processed']}")
        logger.info(f"Feeds success: {stats['feeds_success']}")
        logger.info(f"Feeds errors: {stats['feeds_errors']}")
        logger.info(f"Total articles fetched: {stats['total_fetched']}")
        logger.info(f"Total articles inserted: {stats['total_inserted']}")
        logger.info(f"Total articles skipped: {stats['total_skipped']}")
        logger.info(f"Total processing errors: {stats['total_errors']}")
        logger.info(f"Total duration: {stats['total_duration']:.1f}s")
        
        if stats['feeds_processed'] > 0:
            success_rate = (stats['feeds_success'] / stats['feeds_processed']) * 100
            logger.info(f"Feed success rate: {success_rate:.1f}%")
        
        if stats['total_fetched'] > 0:
            insert_rate = (stats['total_inserted'] / stats['total_fetched']) * 100
            logger.info(f"Article insert rate: {insert_rate:.1f}%")


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RSS Ingestion Runner")
    parser.add_argument('--max-feeds', type=int, default=None,
                       help='Maximum feeds to process (default: all)')
    parser.add_argument('--summary', action='store_true',
                       help='Show current database summary and exit')
    
    args = parser.parse_args()
    
    runner = IngestionRunner()
    
    if args.summary:
        with runner.Session() as session:
            # Feed counts
            feed_result = session.execute(text("""
                SELECT 
                    COUNT(*) as total_feeds,
                    COUNT(*) FILTER (WHERE is_active = true) as active_feeds
                FROM feeds
            """))
            feed_row = feed_result.fetchone()
            
            # Title counts
            title_result = session.execute(text("""
                SELECT 
                    COUNT(*) as total_titles,
                    COUNT(*) FILTER (WHERE processing_status = 'pending') as pending_titles,
                    COUNT(*) FILTER (WHERE processing_status = 'gated') as gated_titles
                FROM titles
            """))
            title_row = title_result.fetchone()
            
            print("Database Summary:")
            print(f"  Feeds: {feed_row.active_feeds}/{feed_row.total_feeds} active")
            print(f"  Titles: {title_row.total_titles} total, {title_row.pending_titles} pending, {title_row.gated_titles} gated")
        return
    
    # Run ingestion
    try:
        stats = runner.run_ingestion(max_feeds=args.max_feeds)
        
        # Print automation-friendly summary
        print(f"INGESTION_RESULT: {stats['feeds_success']}/{stats['feeds_processed']} feeds success, "
              f"{stats['total_inserted']} articles inserted, {stats['total_skipped']} skipped")
        
        # Exit with appropriate code
        sys.exit(0 if stats['feeds_errors'] == 0 else 1)
        
    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()