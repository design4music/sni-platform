#!/usr/bin/env python3
"""
Examine current database schema for Phase 2 planning
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.database import get_db_session
from sqlalchemy import text

def examine_schema():
    """Examine current database schema"""
    with get_db_session() as session:
        print("=== EXAMINING DATABASE SCHEMA FOR PHASE 2 PLANNING ===\n")
        
        # Examine titles table
        print("=== TITLES TABLE SCHEMA ===")
        titles_schema = session.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'titles' 
            ORDER BY ordinal_position
        """)).fetchall()
        
        for col in titles_schema:
            print(f"{col.column_name}: {col.data_type} {'NULL' if col.is_nullable == 'YES' else 'NOT NULL'}")
        
        print(f"\nTitles table has {len(titles_schema)} columns")
        
        # Sample some titles data to see what we're working with
        print("\n=== SAMPLE TITLES DATA ===")
        sample_titles = session.execute(text("""
            SELECT id, title_display, publisher_name, pubdate_utc, gate_keep, entities
            FROM titles 
            WHERE gate_keep = true 
            ORDER BY pubdate_utc DESC 
            LIMIT 5
        """)).fetchall()
        
        for title in sample_titles:
            print(f"ID: {title.id}")
            print(f"Title: {title.title_display}")
            print(f"Publisher: {title.publisher_name}")
            print(f"Date: {title.pubdate_utc}")
            print(f"Strategic: {title.gate_keep}")
            print(f"Entities: {title.entities}")
            print("---")
        
        # Check bucket-related tables
        print("\n=== BUCKET TABLES SCHEMA ===")
        
        # Buckets table
        buckets_schema = session.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'buckets' 
            ORDER BY ordinal_position
        """)).fetchall()
        
        print("BUCKETS TABLE:")
        for col in buckets_schema:
            print(f"  {col.column_name}: {col.data_type} {'NULL' if col.is_nullable == 'YES' else 'NOT NULL'}")
        
        # Bucket members table
        members_schema = session.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'bucket_members' 
            ORDER BY ordinal_position
        """)).fetchall()
        
        print("BUCKET_MEMBERS TABLE:")
        for col in members_schema:
            print(f"  {col.column_name}: {col.data_type} {'NULL' if col.is_nullable == 'YES' else 'NOT NULL'}")
        
        # Count data in these tables
        print("\n=== DATA COUNTS ===")
        titles_count = session.execute(text("SELECT COUNT(*) FROM titles")).scalar()
        strategic_count = session.execute(text("SELECT COUNT(*) FROM titles WHERE gate_keep = true")).scalar()
        buckets_count = session.execute(text("SELECT COUNT(*) FROM buckets")).scalar()
        members_count = session.execute(text("SELECT COUNT(*) FROM bucket_members")).scalar()
        
        print(f"Total titles: {titles_count}")
        print(f"Strategic titles: {strategic_count}")
        print(f"Buckets: {buckets_count}")
        print(f"Bucket members: {members_count}")
        
        # Check event_families current state
        print("\n=== EVENT FAMILIES STATUS ===")
        ef_count = session.execute(text("SELECT COUNT(*) FROM event_families")).scalar()
        print(f"Current Event Families: {ef_count}")
        
        if ef_count > 0:
            latest_ef = session.execute(text("""
                SELECT title, key_actors, source_title_ids 
                FROM event_families 
                ORDER BY created_at DESC 
                LIMIT 1
            """)).fetchone()
            print(f"Latest EF: {latest_ef.title}")
            print(f"Actors: {latest_ef.key_actors}")
            print(f"Source titles: {len(latest_ef.source_title_ids) if latest_ef.source_title_ids else 0}")

if __name__ == "__main__":
    examine_schema()