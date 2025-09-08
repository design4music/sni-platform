#!/usr/bin/env python3
"""
Add new RSS feeds directly via Python
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etl_pipeline.core.database import get_db_session, initialize_database
from etl_pipeline.core.config import get_config
from sqlalchemy import text

def add_new_feeds():
    print("ADDING NEW RSS FEEDS")
    print("=" * 30)
    
    config = get_config()
    initialize_database(config.database)
    
    feeds = [
        ('Financial Times World', 'https://www.ft.com/world?format=rss', 'GB', 1, 0.9),
        ('Financial Times Technology', 'https://www.ft.com/technology?format=rss', 'GB', 1, 0.9),
        ('Financial Times Markets', 'https://www.ft.com/markets?format=rss', 'GB', 1, 0.9),
        ('Financial Times Climate', 'https://www.ft.com/climate-capital?format=rss', 'GB', 1, 0.9),
        ('Fox News Politics', 'https://moxie.foxnews.com/google-publisher/politics.xml', 'US', 2, 0.8),
        ('Fox News World', 'https://moxie.foxnews.com/google-publisher/world.xml', 'US', 2, 0.8),
        ('Fox News Technology', 'https://moxie.foxnews.com/google-publisher/tech.xml', 'US', 2, 0.8),
        ('ZeroHedge', 'https://cms.zerohedge.com/fullrss2.xml', 'US', 2, 0.7),
        ('Reason.com', 'https://reason.com/feed/', 'US', 2, 0.8),
        ('Der Spiegel International', 'https://www.spiegel.de/international/index.rss', 'DE', 2, 0.8),
        ('Daily Mail News', 'https://www.dailymail.co.uk/news/index.rss', 'GB', 3, 0.6),
    ]
    
    with get_db_session() as session:
        added_count = 0
        
        for name, url, country, priority, reliability in feeds:
            try:
                result = session.execute(text('''
                    INSERT INTO news_feeds (
                        id, name, url, feed_type, language, country_code, 
                        is_active, priority, fetch_interval_minutes, reliability_score,
                        created_at, updated_at
                    ) VALUES (
                        gen_random_uuid(), :name, :url, 'RSS', 'EN', :country,
                        true, :priority, 60, :reliability,
                        NOW(), NOW()
                    )
                '''), {
                    'name': name,
                    'url': url, 
                    'country': country,
                    'priority': priority,
                    'reliability': reliability
                })
                
                print(f"+ Added: {name}")
                added_count += 1
                
            except Exception as e:
                print(f"- Failed to add {name}: {e}")
        
        session.commit()
        
        print(f"\nSuccessfully added {added_count}/{len(feeds)} feeds")
        
        # Verify
        result = session.execute(text('''
            SELECT name, country_code, priority, reliability_score
            FROM news_feeds 
            WHERE created_at > NOW() - INTERVAL '1 minute'
            ORDER BY name
        '''))
        
        print("\nNewly added feeds:")
        for row in result.fetchall():
            name, country, priority, reliability = row
            print(f"  {name} ({country}) - Priority {priority}, Score {reliability}")

if __name__ == "__main__":
    add_new_feeds()