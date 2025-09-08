#!/usr/bin/env python3
"""
Show ingestion KPIs by feed - articles ingested in the last run
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etl_pipeline.core.database import get_db_session, initialize_database
from etl_pipeline.core.config import get_config
from sqlalchemy import text

def show_ingestion_kpis():
    print("INGESTION KPIs BY FEED")
    print("=" * 60)
    
    config = get_config()
    initialize_database(config.database)
    
    with get_db_session() as session:
        # Show articles ingested in the last hour (recent ingestion)
        result = session.execute(text('''
            SELECT 
                nf.name,
                nf.country_code,
                nf.priority,
                COUNT(a.id) as articles_ingested,
                MIN(a.created_at) as first_article,
                MAX(a.created_at) as last_article,
                AVG(LENGTH(COALESCE(a.content, a.summary, ''))) as avg_content_length,
                COUNT(CASE WHEN a.word_count >= 300 THEN 1 END) as articles_long,
                COUNT(CASE WHEN a.word_count < 50 THEN 1 END) as articles_short
            FROM articles a
            JOIN news_feeds nf ON a.feed_id = nf.id
            WHERE a.created_at > NOW() - INTERVAL '2 hours'
            GROUP BY nf.id, nf.name, nf.country_code, nf.priority
            ORDER BY articles_ingested DESC, nf.priority ASC
        '''))
        
        recent_articles = list(result.fetchall())
        
        if not recent_articles:
            print("No recent articles found (last 2 hours)")
            return
        
        print(f"Articles ingested in the last 2 hours: {sum(row[3] for row in recent_articles)}")
        print()
        print("Feed Performance Report:")
        print("-" * 100)
        print(f"{'Feed Name':<35} {'Country':<8} {'Priority':<8} {'Articles':<8} {'Avg Len':<8} {'Long':<6} {'Short':<6}")
        print("-" * 100)
        
        for row in recent_articles:
            name, country, priority, count, first, last, avg_len, long_articles, short_articles = row
            name = name or "Unknown"
            country = country or "??"
            priority = priority or 0
            avg_len = int(avg_len) if avg_len else 0
            print(f"{name[:34]:<35} {country:<8} {priority:<8} {count:<8} {avg_len:<8} {long_articles:<6} {short_articles:<6}")
        
        print("-" * 100)
        
        # Show top sources by volume
        print("\nTop 10 Most Active Feeds:")
        top_feeds = sorted(recent_articles, key=lambda x: x[3], reverse=True)[:10]
        for i, row in enumerate(top_feeds, 1):
            name, country, priority, count, first, last, avg_len, long_articles, short_articles = row
            print(f"{i:2}. {name} ({country}): {count} articles")
        
        # Show total stats
        total_articles = sum(row[3] for row in recent_articles)
        total_long = sum(row[7] for row in recent_articles) 
        total_short = sum(row[8] for row in recent_articles)
        active_feeds = len(recent_articles)
        
        print(f"\nSummary:")
        print(f"Active feeds: {active_feeds}")
        print(f"Total articles: {total_articles}")
        print(f"Long articles (>=300 words): {total_long} ({100*total_long/total_articles if total_articles else 0:.1f}%)")
        print(f"Short articles (<50 words): {total_short} ({100*total_short/total_articles if total_articles else 0:.1f}%)")
        
        # Show new feeds performance
        new_feeds = [row for row in recent_articles if row[0] in [
            'Financial Times World', 'Financial Times Technology', 'Financial Times Markets', 'Financial Times Climate',
            'Fox News Politics', 'Fox News World', 'Fox News Technology', 
            'ZeroHedge', 'Reason.com', 'Der Spiegel International', 'Daily Mail News'
        ]]
        
        if new_feeds:
            print(f"\nNew Feeds Performance ({len(new_feeds)} active):")
            new_total = sum(row[3] for row in new_feeds)
            print(f"Articles from new feeds: {new_total} ({100*new_total/total_articles if total_articles else 0:.1f}% of total)")
            
            for row in sorted(new_feeds, key=lambda x: x[3], reverse=True):
                name, country, priority, count, first, last, avg_len, long_articles, short_articles = row
                print(f"  {name}: {count} articles")

if __name__ == "__main__":
    show_ingestion_kpis()