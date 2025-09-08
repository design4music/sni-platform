#!/usr/bin/env python3
"""
Reality Check: What Actually Works
Test the actual state of the system to separate fact from fiction
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_database_connection():
    """Test actual database connectivity"""
    print("=== DATABASE CONNECTION TEST ===")
    try:
        from etl_pipeline.core.config import get_config
        from etl_pipeline.core.database import (get_db_session,
                                                initialize_database)

        config = get_config()
        print(f"Database: {config.database.database}")
        print(f"Host: {config.database.host}:{config.database.port}")
        print(f"User: {config.database.username}")

        # Try to initialize and connect
        initialize_database(config.database)
        with get_db_session() as db:
            from sqlalchemy import text

            result = db.execute(text("SELECT COUNT(*) as count FROM articles")).first()
            article_count = result.count if result else 0
            print(f"[OK] Database connection successful")
            print(f"[OK] Articles in database: {article_count}")

            # Check for narratives table
            try:
                result = db.execute(
                    text("SELECT COUNT(*) as count FROM narratives")
                ).first()
                narrative_count = result.count if result else 0
                print(f"[OK] Narratives in database: {narrative_count}")
            except Exception as e:
                print(f"[ERROR] Narratives table issue: {e}")

        return True
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False


def test_working_scripts():
    """Check which scripts are executable"""
    print("\n=== SCRIPT AVAILABILITY TEST ===")

    scripts_to_test = [
        "rss_ingestion.py",
        "production_clust1.py",
        "clust3_consolidate_narratives.py",
    ]

    working_scripts = []

    for script in scripts_to_test:
        if os.path.exists(script):
            print(f"[OK] {script} exists")
            working_scripts.append(script)
        else:
            print(f"[MISSING] {script}")

    return working_scripts


def check_recent_activity():
    """Check log files for recent activity"""
    print("\n=== RECENT ACTIVITY CHECK ===")

    log_files = [
        "rss_ingestion.log",
        "clust1_production.log",
        "clust3_consolidation.log",
    ]

    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                stat = os.stat(log_file)
                mtime = datetime.fromtimestamp(stat.st_mtime)
                print(f"[OK] {log_file} last modified: {mtime}")
            except:
                print(f"[ERROR] {log_file} cannot read")
        else:
            print(f"[MISSING] {log_file}")


def main():
    print("STRATEGIC NARRATIVE INTELLIGENCE - REALITY CHECK")
    print("=" * 50)
    print(f"Timestamp: {datetime.now()}")
    print()

    # Test database
    db_works = test_database_connection()

    # Test scripts
    working_scripts = test_working_scripts()

    # Check recent activity
    check_recent_activity()

    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Database Connection: {'WORKING' if db_works else 'BROKEN'}")
    print(f"Available Scripts: {len(working_scripts)}/3")
    print("=" * 50)


if __name__ == "__main__":
    main()
