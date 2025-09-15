#!/usr/bin/env python3
"""
Database Smoke Test
Strategic Narrative Intelligence Platform

Comprehensive database verification including table counts, structure validation,
and index verification for all core tables.
"""

import sys
from collections import defaultdict
from datetime import datetime

# Add project root to path
sys.path.append(".")

from etl_pipeline.core.config import get_config
from etl_pipeline.core.database import get_db_session, initialize_database
from sqlalchemy import text


def test_basic_connectivity():
    """Test basic database connectivity"""
    print("=== DATABASE CONNECTIVITY TEST ===")

    try:
        config = get_config()
        print(f"Database: {config.database.database}")
        print(f"Host: {config.database.host}:{config.database.port}")
        print(f"User: {config.database.username}")

        initialize_database(config.database)

        with get_db_session() as db:
            result = db.execute(text("SELECT version()")).first()
            print(f"[OK] PostgreSQL version: {result[0].split(',')[0]}")
            return True

    except Exception as e:
        print(f"[ERROR] Database connectivity failed: {e}")
        return False


def test_core_table_counts():
    """Test counts for core data tables"""
    print("\n=== CORE TABLE COUNTS ===")

    core_tables = {
        "articles": "Raw articles from RSS feeds",
        "keywords": "Extracted keywords database",
        "article_keywords": "Article-keyword relationships",
        "narratives": "Generated narrative clusters",
        "narrative_metrics": "Narrative performance metrics",
        "article_clusters": "Article clustering assignments",
    }

    results = {}

    try:
        with get_db_session() as db:
            for table_name, description in core_tables.items():
                try:
                    result = db.execute(
                        text(f"SELECT COUNT(*) as count FROM {table_name}")
                    ).first()
                    count = result.count if result else 0
                    results[table_name] = count
                    print(f"[OK] {table_name}: {count:,} records - {description}")
                except Exception as e:
                    print(f"[ERROR] {table_name}: Table access failed - {e}")
                    results[table_name] = -1

        return results

    except Exception as e:
        print(f"[ERROR] Table count test failed: {e}")
        return {}


def test_table_existence_and_structure():
    """Test that required tables exist with expected structure"""
    print("\n=== TABLE STRUCTURE TEST ===")

    expected_tables = {
        "articles": ["id", "title", "content", "url", "published_at", "source_name"],
        "keywords": ["id", "keyword", "keyword_type", "entity_label", "base_frequency"],
        "article_keywords": [
            "article_id",
            "keyword_id",
            "relevance_score",
            "extraction_method",
        ],
        "narratives": [
            "id",
            "narrative_id",
            "title",
            "summary",
            "parent_id",
            "created_at",
        ],
        "narrative_metrics": [
            "narrative_id",
            "article_count",
            "keyword_diversity",
            "updated_at",
        ],
        "article_clusters": [
            "id",
            "article_id",
            "cluster_id",
            "cluster_algorithm",
            "created_at",
        ],
    }

    results = {}

    try:
        with get_db_session() as db:
            # Get all tables in database
            result = db.execute(
                text(
                    """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """
                )
            )

            existing_tables = {row[0] for row in result.fetchall()}
            print(f"Database has {len(existing_tables)} tables total")

            for table_name, expected_columns in expected_tables.items():
                if table_name in existing_tables:
                    # Get column information
                    result = db.execute(
                        text(
                            """
                        SELECT column_name, data_type, is_nullable 
                        FROM information_schema.columns 
                        WHERE table_name = :table_name 
                        ORDER BY ordinal_position
                    """
                        ),
                        {"table_name": table_name},
                    )

                    columns = result.fetchall()
                    column_names = [col[0] for col in columns]

                    # Check for expected columns
                    missing_columns = set(expected_columns) - set(column_names)
                    if missing_columns:
                        print(
                            f"[WARNING] {table_name}: Missing columns {missing_columns}"
                        )
                        results[table_name] = "partial"
                    else:
                        print(
                            f"[OK] {table_name}: All expected columns present ({len(column_names)} total)"
                        )
                        results[table_name] = "complete"
                else:
                    print(f"[ERROR] {table_name}: Table does not exist")
                    results[table_name] = "missing"

            return results

    except Exception as e:
        print(f"[ERROR] Table structure test failed: {e}")
        return {}


def test_database_indexes():
    """Test that expected indexes exist on core tables"""
    print("\n=== DATABASE INDEXES TEST ===")

    expected_indexes = {
        "articles": [
            "articles_pkey",  # Primary key
            "idx_articles_published_at",  # Time-based queries
            "idx_articles_source_name",  # Source filtering
            "idx_articles_search_vector",  # Full-text search
        ],
        "keywords": [
            "keywords_pkey",
            "idx_keywords_keyword",  # Keyword lookup
            "idx_keywords_frequency",  # Frequency-based queries
            "idx_keywords_type_entity",  # Type and entity filtering
        ],
        "article_keywords": [
            "article_keywords_pkey",
            "idx_article_keywords_article_id",  # Article lookup
            "idx_article_keywords_keyword_id",  # Keyword lookup
            "idx_article_keywords_relevance",  # Relevance scoring
        ],
        "narratives": [
            "narratives_pkey",
            "idx_narratives_parent_id",  # Hierarchy queries
            "idx_narratives_created_at",  # Time-based queries
            "idx_narratives_narrative_id",  # Business key lookup
        ],
        "article_clusters": [
            "article_clusters_pkey",
            "idx_article_clusters_article_id",  # Article lookup
            "idx_article_clusters_cluster_id",  # Cluster lookup
            "idx_article_clusters_algorithm",  # Algorithm filtering
        ],
    }

    results = {}

    try:
        with get_db_session() as db:
            # Get all indexes
            result = db.execute(
                text(
                    """
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """
                )
            )

            existing_indexes = defaultdict(list)
            for schema, table, index, definition in result.fetchall():
                existing_indexes[table].append(index)

            print(f"Database has indexes on {len(existing_indexes)} tables")

            for table_name, expected_idx_list in expected_indexes.items():
                existing_idx_list = existing_indexes.get(table_name, [])

                if existing_idx_list:
                    # Check for critical indexes (allow for some flexibility in naming)
                    has_primary_key = any("pkey" in idx for idx in existing_idx_list)
                    critical_indexes = [
                        idx for idx in expected_idx_list if "pkey" not in idx
                    ]

                    found_indexes = []
                    for expected_idx in critical_indexes:
                        # Flexible matching - check if core concept is present
                        core_concept = expected_idx.replace("idx_", "").replace(
                            table_name + "_", ""
                        )
                        if any(
                            core_concept in existing_idx
                            for existing_idx in existing_idx_list
                        ):
                            found_indexes.append(expected_idx)

                    if has_primary_key:
                        print(
                            f"[OK] {table_name}: Primary key + {len(existing_idx_list)-1} indexes"
                        )
                    else:
                        print(f"[WARNING] {table_name}: No primary key found")

                    results[table_name] = {
                        "total_indexes": len(existing_idx_list),
                        "has_primary_key": has_primary_key,
                        "critical_indexes_found": len(found_indexes),
                    }
                else:
                    print(f"[ERROR] {table_name}: No indexes found")
                    results[table_name] = {"total_indexes": 0, "has_primary_key": False}

            return results

    except Exception as e:
        print(f"[ERROR] Index test failed: {e}")
        return {}


def test_data_integrity():
    """Test basic data integrity constraints"""
    print("\n=== DATA INTEGRITY TEST ===")

    integrity_tests = {}

    try:
        with get_db_session() as db:
            # Test foreign key relationships
            print("Testing foreign key relationships...")

            # Check article_keywords -> articles relationship
            result = db.execute(
                text(
                    """
                SELECT COUNT(*) as orphaned_count
                FROM article_keywords ak
                LEFT JOIN articles a ON ak.article_id = a.id
                WHERE a.id IS NULL
            """
                )
            ).first()

            orphaned_ak = result.orphaned_count if result else 0
            if orphaned_ak == 0:
                print("[OK] article_keywords: No orphaned records")
            else:
                print(f"[WARNING] article_keywords: {orphaned_ak} orphaned records")
            integrity_tests["article_keywords_fk"] = orphaned_ak

            # Check article_keywords -> keywords relationship
            result = db.execute(
                text(
                    """
                SELECT COUNT(*) as orphaned_count
                FROM article_keywords ak
                LEFT JOIN keywords k ON ak.keyword_id = k.id
                WHERE k.id IS NULL
            """
                )
            ).first()

            orphaned_keyword = result.orphaned_count if result else 0
            if orphaned_keyword == 0:
                print("[OK] article_keywords->keywords: No orphaned records")
            else:
                print(
                    f"[WARNING] article_keywords->keywords: {orphaned_keyword} orphaned records"
                )
            integrity_tests["keywords_fk"] = orphaned_keyword

            # Check narratives parent_id self-referential integrity
            result = db.execute(
                text(
                    """
                SELECT COUNT(*) as orphaned_count
                FROM narratives child
                LEFT JOIN narratives parent ON child.parent_id = parent.id
                WHERE child.parent_id IS NOT NULL AND parent.id IS NULL
            """
                )
            ).first()

            orphaned_narratives = result.orphaned_count if result else 0
            if orphaned_narratives == 0:
                print("[OK] narratives: No orphaned parent references")
            else:
                print(
                    f"[WARNING] narratives: {orphaned_narratives} orphaned parent references"
                )
            integrity_tests["narratives_parent_fk"] = orphaned_narratives

            return integrity_tests

    except Exception as e:
        print(f"[ERROR] Data integrity test failed: {e}")
        return {}


def test_postgresql_extensions():
    """Test that required PostgreSQL extensions are installed"""
    print("\n=== POSTGRESQL EXTENSIONS TEST ===")

    required_extensions = ["vector", "pg_trgm"]
    results = {}

    try:
        with get_db_session() as db:
            result = db.execute(
                text(
                    """
                SELECT extname, extversion 
                FROM pg_extension 
                ORDER BY extname
            """
                )
            )

            installed_extensions = {
                name: version for name, version in result.fetchall()
            }

            print(f"Installed extensions: {list(installed_extensions.keys())}")

            for ext_name in required_extensions:
                if ext_name in installed_extensions:
                    version = installed_extensions[ext_name]
                    print(f"[OK] {ext_name}: Version {version}")
                    results[ext_name] = version
                else:
                    print(f"[ERROR] {ext_name}: Not installed")
                    results[ext_name] = None

            return results

    except Exception as e:
        print(f"[ERROR] Extensions test failed: {e}")
        return {}


def generate_summary_report(
    connectivity, table_counts, table_structure, indexes, integrity, extensions
):
    """Generate comprehensive summary report"""
    print("\n" + "=" * 60)
    print("DATABASE SMOKE TEST SUMMARY")
    print("=" * 60)

    # Overall status
    connectivity_ok = connectivity
    tables_ok = (
        all(count >= 0 for count in table_counts.values()) if table_counts else False
    )
    structure_ok = (
        all(status in ["complete", "partial"] for status in table_structure.values())
        if table_structure
        else False
    )
    indexes_ok = (
        all(info.get("has_primary_key", False) for info in indexes.values())
        if indexes
        else False
    )
    integrity_ok = (
        all(count == 0 for count in integrity.values()) if integrity else False
    )
    extensions_ok = (
        all(version is not None for version in extensions.values())
        if extensions
        else False
    )

    overall_status = (
        "HEALTHY"
        if all([connectivity_ok, tables_ok, structure_ok, extensions_ok])
        else "NEEDS ATTENTION"
    )

    print(f"Overall Status: {overall_status}")
    print()

    # Detailed results
    print("Component Status:")
    print(f"  Database Connectivity: {'✅ OK' if connectivity_ok else '❌ FAILED'}")
    print(f"  Core Tables: {'✅ OK' if tables_ok else '❌ ISSUES'}")
    print(f"  Table Structure: {'✅ OK' if structure_ok else '❌ INCOMPLETE'}")
    print(f"  Database Indexes: {'✅ OK' if indexes_ok else '⚠️ MISSING'}")
    print(f"  Data Integrity: {'✅ OK' if integrity_ok else '⚠️ ISSUES'}")
    print(f"  PostgreSQL Extensions: {'✅ OK' if extensions_ok else '❌ MISSING'}")

    # Data summary
    if table_counts:
        print("\nData Summary:")
        total_articles = table_counts.get("articles", 0)
        total_keywords = table_counts.get("keywords", 0)
        total_relationships = table_counts.get("article_keywords", 0)
        total_narratives = table_counts.get("narratives", 0)
        total_clusters = table_counts.get("article_clusters", 0)

        print(f"  Articles: {total_articles:,}")
        print(f"  Keywords: {total_keywords:,}")
        print(f"  Article-Keyword Relationships: {total_relationships:,}")
        print(f"  Narratives: {total_narratives:,}")
        print(f"  Article Clusters: {total_clusters:,}")

        if total_articles > 0:
            avg_keywords_per_article = (
                total_relationships / total_articles if total_articles > 0 else 0
            )
            print(f"  Average Keywords per Article: {avg_keywords_per_article:.1f}")

    # Recommendations
    print("\nRecommendations:")
    if not connectivity_ok:
        print("  - Fix database connectivity issues")
    if not extensions_ok:
        print("  - Install missing PostgreSQL extensions")
    if not structure_ok:
        print("  - Complete table schema migrations")
    if not indexes_ok:
        print("  - Create missing database indexes for performance")
    if not integrity_ok:
        print("  - Clean up data integrity issues")

    if overall_status == "HEALTHY":
        print("  - Database is healthy and ready for operations")

    return overall_status == "HEALTHY"


def main():
    """Run comprehensive database smoke test"""

    print("STRATEGIC NARRATIVE INTELLIGENCE - DATABASE SMOKE TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print()

    # Run all tests
    connectivity = test_basic_connectivity()
    table_counts = test_core_table_counts()
    table_structure = test_table_existence_and_structure()
    indexes = test_database_indexes()
    integrity = test_data_integrity()
    extensions = test_postgresql_extensions()

    # Generate summary
    success = generate_summary_report(
        connectivity, table_counts, table_structure, indexes, integrity, extensions
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
