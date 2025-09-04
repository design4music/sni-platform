#!/usr/bin/env python3
"""
SNI-v2 Database Setup Script
Creates the SNI database and sets up initial tables
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import subprocess
from loguru import logger
from sqlalchemy import create_engine, text
from core.config import get_config
from core.database import init_database, create_tables, check_database_connection


def create_database():
    """Create the SNI database if it doesn't exist"""
    config = get_config()
    
    # Connect to postgres database to create SNI database
    postgres_url = config.database_url.replace(f"/{config.db_name}", "/postgres")
    
    try:
        engine = create_engine(postgres_url)
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(
                "SELECT 1 FROM pg_database WHERE datname = :db_name"
            ), {"db_name": config.db_name})
            
            if not result.fetchone():
                # Create database
                conn.execute(text("COMMIT"))  # Close any transaction
                conn.execute(text(f'CREATE DATABASE "{config.db_name}"'))
                logger.info(f"Created database: {config.db_name}")
            else:
                logger.info(f"Database already exists: {config.db_name}")
                
    except Exception as e:
        logger.error(f"Failed to create database: {e}")
        return False
    
    return True


def setup_pgvector():
    """Set up pgvector extension for embeddings"""
    try:
        with get_db_session() as session:
            # Check if pgvector is available
            result = session.execute(text(
                "SELECT 1 FROM pg_available_extensions WHERE name = 'vector'"
            ))
            
            if result.fetchone():
                # Create extension if not exists
                session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                logger.info("pgvector extension enabled")
                return True
            else:
                logger.warning("pgvector extension not available - embeddings will use JSON storage")
                return False
                
    except Exception as e:
        logger.error(f"Failed to setup pgvector: {e}")
        return False


def run_sql_script(script_path: Path):
    """Run a SQL script file"""
    if not script_path.exists():
        logger.error(f"SQL script not found: {script_path}")
        return False
        
    config = get_config()
    
    try:
        # Use psql command if available
        env = os.environ.copy()
        env['PGPASSWORD'] = config.db_password
        
        cmd = [
            'psql',
            '-h', config.db_host,
            '-p', str(config.db_port),
            '-U', config.db_user,
            '-d', config.db_name,
            '-f', str(script_path)
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Successfully executed SQL script: {script_path.name}")
            return True
        else:
            logger.error(f"SQL script failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        logger.warning("psql command not found, using SQLAlchemy instead")
        return run_sql_via_sqlalchemy(script_path)


def run_sql_via_sqlalchemy(script_path: Path):
    """Run SQL script via SQLAlchemy (fallback)"""
    try:
        with get_db_session() as session:
            sql_content = script_path.read_text()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                session.execute(text(statement))
                
            logger.info(f"Successfully executed SQL script via SQLAlchemy: {script_path.name}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to execute SQL script: {e}")
        return False


def main():
    """Main setup function"""
    logger.info("Starting SNI-v2 database setup...")
    
    # Step 1: Create database
    if not create_database():
        logger.error("Database creation failed")
        sys.exit(1)
    
    # Step 2: Initialize database connection
    init_database()
    
    # Step 3: Check connection
    if not check_database_connection():
        logger.error("Database connection failed")
        sys.exit(1)
    
    # Step 4: Setup pgvector (optional)
    setup_pgvector()
    
    # Step 5: Create tables via schema script
    schema_script = project_root / "db" / "schema.sql"
    if schema_script.exists():
        if not run_sql_script(schema_script):
            logger.error("Schema creation failed")
            sys.exit(1)
    else:
        # Fallback to SQLAlchemy table creation
        logger.info("Creating tables via SQLAlchemy...")
        create_tables()
    
    # Step 6: Run any migration scripts
    migrations_dir = project_root / "db" / "migrations"
    if migrations_dir.exists():
        for migration_file in sorted(migrations_dir.glob("*.sql")):
            run_sql_script(migration_file)
    
    logger.success("SNI-v2 database setup completed!")
    
    # Show database stats
    from core.database import get_database_stats
    stats = get_database_stats()
    logger.info("Database statistics:")
    for table, count in stats.items():
        logger.info(f"  {table}: {count}")


if __name__ == "__main__":
    # Import here to avoid circular imports
    from core.database import get_db_session
    main()