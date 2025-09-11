#!/usr/bin/env python3
"""
GEN-1 Schema Setup
Creates database tables for Event Families and Framed Narratives
"""

import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import text

from core.database import get_db_session, check_database_connection


def setup_gen1_schema() -> bool:
    """
    Create GEN-1 database schema (Event Families and Framed Narratives tables)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Setting up GEN-1 database schema...")
        
        # Check database connection first
        if not check_database_connection():
            logger.error("Database connection failed")
            return False
        
        # Read schema file
        schema_file = Path(__file__).parent / "schema.sql"
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        schema_sql = schema_file.read_text()
        
        # Execute schema creation
        with get_db_session() as session:
            # Split schema into individual statements for better error handling
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements, 1):
                try:
                    if statement.strip():
                        session.execute(text(statement))
                        logger.debug(f"Executed statement {i}/{len(statements)}")
                except Exception as e:
                    # Some statements might fail if objects already exist - that's OK
                    if "already exists" in str(e).lower():
                        logger.debug(f"Statement {i} - object already exists: {e}")
                    else:
                        logger.warning(f"Statement {i} failed: {e}")
            
            session.commit()
        
        logger.info("GEN-1 schema setup completed successfully")
        
        # Verify tables were created
        return verify_schema()
        
    except Exception as e:
        logger.error(f"Schema setup failed: {e}")
        return False


def verify_schema() -> bool:
    """
    Verify that GEN-1 tables were created correctly
    
    Returns:
        True if all tables exist, False otherwise
    """
    try:
        logger.info("Verifying GEN-1 schema...")
        
        with get_db_session() as session:
            # Check for event_families table
            result = session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'event_families'
                );
            """)).scalar()
            
            if not result:
                logger.error("event_families table not found")
                return False
            
            # Check for framed_narratives table
            result = session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'framed_narratives'
                );
            """)).scalar()
            
            if not result:
                logger.error("framed_narratives table not found")
                return False
            
            # Check table structures
            ef_columns = session.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'event_families' 
                ORDER BY ordinal_position;
            """)).fetchall()
            
            fn_columns = session.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'framed_narratives' 
                ORDER BY ordinal_position;
            """)).fetchall()
            
            logger.info(f"event_families table has {len(ef_columns)} columns")
            logger.info(f"framed_narratives table has {len(fn_columns)} columns")
            
            # Check for key indexes
            indexes = session.execute(text("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename IN ('event_families', 'framed_narratives')
                ORDER BY tablename, indexname;
            """)).fetchall()
            
            logger.info(f"Created {len(indexes)} indexes")
            
        logger.info("Schema verification passed")
        return True
        
    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return False


def drop_gen1_schema() -> bool:
    """
    Drop GEN-1 database schema (WARNING: This will delete all data!)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.warning("Dropping GEN-1 database schema (THIS WILL DELETE ALL DATA!)")
        
        with get_db_session() as session:
            # Drop tables in reverse order due to foreign key constraints
            session.execute(text("DROP TABLE IF EXISTS framed_narratives CASCADE;"))
            session.execute(text("DROP TABLE IF EXISTS event_families CASCADE;"))
            
            # Drop the trigger function
            session.execute(text("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;"))
            
            session.commit()
        
        logger.info("GEN-1 schema dropped successfully")
        return True
        
    except Exception as e:
        logger.error(f"Schema drop failed: {e}")
        return False


def main():
    """Main CLI entry point for schema management"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="GEN-1 Database Schema Management",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    parser.add_argument(
        "action",
        choices=["create", "verify", "drop"],
        help="Action to perform",
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force operation without confirmation (for drop)",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>GEN-1-SCHEMA</cyan> | {message}",
        level="INFO",
        colorize=True,
    )
    
    logger.info("GEN-1 Database Schema Management")
    logger.info("=" * 40)
    
    try:
        if args.action == "create":
            success = setup_gen1_schema()
        elif args.action == "verify":
            success = verify_schema()
        elif args.action == "drop":
            if not args.force:
                print("WARNING: This will delete all GEN-1 data!")
                confirm = input("Type 'DELETE' to confirm: ")
                if confirm != "DELETE":
                    logger.info("Operation cancelled")
                    sys.exit(0)
            success = drop_gen1_schema()
        else:
            logger.error(f"Unknown action: {args.action}")
            success = False
        
        if success:
            logger.info(f"Schema {args.action} completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Schema {args.action} failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()