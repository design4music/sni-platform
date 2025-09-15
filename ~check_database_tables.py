#!/usr/bin/env python3
"""
Database table inspection script for SNI database
Checks what tables exist and gets their schema structure
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path so we can import core modules
sys.path.insert(0, str(Path(__file__).parent))

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters from .env
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'sni_v2')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

def connect_to_database():
    """Connect to the PostgreSQL database"""
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return connection
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def get_all_tables(connection):
    """Get list of all tables in the database"""
    try:
        with connection.cursor() as cursor:
            # Query to get all tables in the public schema
            cursor.execute("""
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            tables = cursor.fetchall()
            return tables
    except psycopg2.Error as e:
        print(f"Error querying tables: {e}")
        return []

def get_table_schema(connection, table_name):
    """Get the schema structure of a specific table"""
    try:
        with connection.cursor() as cursor:
            # Query to get column information
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            
            columns = cursor.fetchall()
            return columns
    except psycopg2.Error as e:
        print(f"Error querying schema for table {table_name}: {e}")
        return []

def get_table_row_count(connection, table_name):
    """Get the number of rows in a table"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            return count
    except psycopg2.Error as e:
        print(f"Error counting rows in {table_name}: {e}")
        return "Error"

def main():
    print("=== SNI Database Table Inspection ===")
    print(f"Database: {DB_NAME} on {DB_HOST}:{DB_PORT}")
    print(f"User: {DB_USER}")
    print()
    
    # Connect to database
    connection = connect_to_database()
    if not connection:
        print("Failed to connect to database!")
        sys.exit(1)
    
    print("Connected to database successfully!")
    print()
    
    # Get all tables
    tables = get_all_tables(connection)
    
    if not tables:
        print("No tables found in the database!")
        connection.close()
        return
    
    print(f"Found {len(tables)} tables:")
    print("-" * 80)
    
    for table_name, table_type in tables:
        print(f"\nTable: {table_name} ({table_type})")
        
        # Get row count
        row_count = get_table_row_count(connection, table_name)
        print(f"Rows: {row_count}")
        
        # Get schema
        columns = get_table_schema(connection, table_name)
        if columns:
            print("Columns:")
            for col_name, data_type, is_nullable, default, max_length in columns:
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                length_info = f"({max_length})" if max_length else ""
                default_info = f" DEFAULT {default}" if default else ""
                print(f"  - {col_name}: {data_type}{length_info} {nullable}{default_info}")
        
        print("-" * 80)
    
    # Check specifically for events and narratives tables
    print("\n=== Specific Tables Check ===")
    
    table_names = [table[0] for table in tables]
    
    # Look for events-related tables
    events_tables = [t for t in table_names if 'event' in t.lower()]
    if events_tables:
        print(f"Events-related tables found: {events_tables}")
    else:
        print("No 'events' tables found")
    
    # Look for narratives-related tables  
    narrative_tables = [t for t in table_names if 'narrative' in t.lower()]
    if narrative_tables:
        print(f"Narratives-related tables found: {narrative_tables}")
    else:
        print("No 'narratives' tables found")
    
    # Look for other important tables
    important_tables = ['feeds', 'titles', 'clusters', 'articles']
    for table in important_tables:
        if table in table_names:
            count = get_table_row_count(connection, table)
            print(f"Table '{table}' exists with {count} rows")
        else:
            print(f"Table '{table}' not found")
    
    connection.close()
    print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()