"""
Database module for Strategic Narrative Intelligence ETL Pipeline

This module provides database connectivity, session management, and
configuration for PostgreSQL with pgvector support.
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional

import structlog
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from ..config import DatabaseConfig
from .models import Base, create_all_tables

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """
    Database connection and session management
    """

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
        self._setup_session_factory()

    def _setup_engine(self):
        """Setup SQLAlchemy engine with optimal configuration"""
        connection_string = (
            f"postgresql://{self.config.username}:{self.config.password}"
            f"@{self.config.host}:{self.config.port}/{self.config.database}"
        )

        # Engine configuration for production workloads
        engine_config = {
            "poolclass": QueuePool,
            "pool_size": self.config.pool_size,
            "max_overflow": self.config.max_overflow,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # Recycle connections every hour
            "echo": self.config.echo_sql,
            "echo_pool": False,
            "future": True,
        }

        # Add SSL configuration if specified
        if self.config.ssl_mode:
            engine_config["connect_args"] = {
                "sslmode": self.config.ssl_mode,
                "options": "-c timezone=UTC",
            }

        self.engine = create_engine(connection_string, **engine_config)

        # Setup event listeners
        self._setup_event_listeners()

        logger.info(
            "Database engine configured",
            host=self.config.host,
            database=self.config.database,
            pool_size=self.config.pool_size,
        )

    def _setup_session_factory(self):
        """Setup session factory with optimal configuration"""
        self.SessionLocal = sessionmaker(
            bind=self.engine, autocommit=False, autoflush=False, expire_on_commit=False
        )

    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring and optimization"""

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set PostgreSQL-specific connection settings"""
            if "postgresql" in str(dbapi_connection):
                with dbapi_connection.cursor() as cursor:
                    # Enable pgvector extension
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    # Set optimal settings for our workload
                    cursor.execute("SET statement_timeout = '300s'")  # 5 minute timeout
                    cursor.execute("SET lock_timeout = '30s'")
                    cursor.execute("SET idle_in_transaction_session_timeout = '60s'")

        @event.listens_for(self.engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Log slow queries for performance monitoring"""
            context._query_start_time = logger.info(
                "Query started", query=statement[:100]
            )

        @event.listens_for(self.engine, "after_cursor_execute")
        def receive_after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Log query execution time"""
            if hasattr(context, "_query_start_time"):
                logger.info(
                    "Query completed", execution_time="<calculated>"
                )
                # In real implementation, calculate actual time

    def create_tables(self):
        """Create all database tables"""
        try:
            create_all_tables(self.engine)
            logger.info("Database tables created successfully")
        except Exception as exc:
            logger.error("Failed to create database tables", error=str(exc))
            raise

    def health_check(self) -> bool:
        """Perform database health check"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
                return True
        except Exception as exc:
            logger.error("Database health check failed", error=str(exc))
            return False

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.error("Database session error", error=str(exc))
            raise
        finally:
            session.close()

    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def initialize_database(config: DatabaseConfig) -> DatabaseManager:
    """Initialize global database manager"""
    global _db_manager
    _db_manager = DatabaseManager(config)
    return _db_manager


def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""
    if _db_manager is None:
        raise RuntimeError(
            "Database not initialized. Call initialize_database() first."
        )
    return _db_manager


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session from global manager"""
    db_manager = get_database_manager()
    with db_manager.get_session() as session:
        yield session


# Database initialization and migration utilities
def init_database_with_extensions(config: DatabaseConfig):
    """Initialize database with required extensions"""
    # Connect as superuser to create extensions
    admin_config = DatabaseConfig(
        host=config.host,
        port=config.port,
        database="postgres",  # Connect to default database
        username=config.admin_username or config.username,
        password=config.admin_password or config.password,
        ssl_mode=config.ssl_mode,
    )

    admin_manager = DatabaseManager(admin_config)

    try:
        with admin_manager.get_session() as session:
            # Create database if it doesn't exist
            session.execute(f"CREATE DATABASE {config.database}")
            logger.info("Database created", database=config.database)
    except Exception:
        # Database might already exist
        pass

    # Now connect to our database and create extensions
    db_manager = DatabaseManager(config)

    with db_manager.get_session() as session:
        # Create required extensions
        session.execute("CREATE EXTENSION IF NOT EXISTS vector")
        session.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")  # For text search
        session.execute("CREATE EXTENSION IF NOT EXISTS btree_gin")  # For JSON indexing
        session.execute(
            "CREATE EXTENSION IF NOT EXISTS uuid-ossp"
        )  # For UUID generation

        logger.info("Database extensions created successfully")

    # Create all tables
    db_manager.create_tables()

    return db_manager


# Query utilities and helpers
class QueryBuilder:
    """Helper class for building complex queries"""

    @staticmethod
    def articles_by_date_range(session: Session, start_date, end_date, language=None):
        """Get articles within date range"""
        from .models import Article

        query = session.query(Article).filter(
            Article.published_at >= start_date, Article.published_at <= end_date
        )

        if language:
            query = query.filter(Article.language == language)

        return query

    @staticmethod
    def articles_by_relevance(session: Session, min_relevance=0.7, limit=100):
        """Get highly relevant articles"""
        from .models import Article

        return (
            session.query(Article)
            .filter(Article.relevance_score >= min_relevance)
            .order_by(Article.relevance_score.desc())
            .limit(limit)
        )

    @staticmethod
    def trending_topics_current(session: Session, hours_back=24):
        """Get current trending topics"""
        from datetime import datetime, timedelta

        from .models import TrendingTopic

        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

        return (
            session.query(TrendingTopic)
            .filter(TrendingTopic.detected_at >= cutoff_time)
            .order_by(TrendingTopic.trending_score.desc())
        )

    @staticmethod
    def similar_articles_by_embedding(
        session: Session, article_id, similarity_threshold=0.8, limit=10
    ):
        """Find similar articles using vector similarity"""
        from .models import Article, ArticleEmbedding

        # This would use pgvector similarity search
        # Example implementation would require raw SQL for vector operations
        query = """
        SELECT a.*, 
               1 - (ae1.content_embedding <=> ae2.content_embedding) as similarity
        FROM articles a
        JOIN article_embeddings ae1 ON a.id = ae1.article_id
        JOIN article_embeddings ae2 ON ae2.article_id = :target_article_id
        WHERE a.id != :target_article_id
          AND ae1.embedding_model = ae2.embedding_model
          AND 1 - (ae1.content_embedding <=> ae2.content_embedding) >= :threshold
        ORDER BY similarity DESC
        LIMIT :limit
        """

        return session.execute(
            query,
            {
                "target_article_id": article_id,
                "threshold": similarity_threshold,
                "limit": limit,
            },
        )


# Migration and maintenance utilities
def perform_database_maintenance(session: Session):
    """Perform routine database maintenance"""

    # Analyze tables for query optimization
    maintenance_queries = [
        "ANALYZE articles",
        "ANALYZE article_embeddings",
        "ANALYZE entity_mentions",
        "ANALYZE trending_topics",
        # Update statistics
        "SELECT pg_stat_reset()",
        # Cleanup old data (older than 1 year)
        """DELETE FROM trending_topics 
           WHERE detected_at < NOW() - INTERVAL '1 year'""",
        """DELETE FROM feed_metrics 
           WHERE date < NOW() - INTERVAL '1 year'""",
        """DELETE FROM pipeline_runs 
           WHERE started_at < NOW() - INTERVAL '6 months'""",
    ]

    for query in maintenance_queries:
        try:
            session.execute(query)
            logger.info("Maintenance query executed", query=query[:50])
        except Exception as exc:
            logger.warning("Maintenance query failed", query=query[:50], error=str(exc))

    session.commit()
    logger.info("Database maintenance completed")


def create_indexes_for_performance(session: Session):
    """Create additional performance indexes"""

    performance_indexes = [
        # Vector similarity indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_article_embeddings_content_cosine "
        "ON article_embeddings USING ivfflat (content_embedding vector_cosine_ops) "
        "WITH (lists = 100)",
        # Text search indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_title_search "
        "ON articles USING gin(to_tsvector('english', title))",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_content_search "
        "ON articles USING gin(to_tsvector('english', content))",
        # JSON indexes for categories and metadata
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_categories_gin "
        "ON articles USING gin(categories)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trending_topics_keywords_gin "
        "ON trending_topics USING gin(topic_keywords)",
        # Composite indexes for common queries
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_status_date "
        "ON articles(processing_status, published_at DESC)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_feed_metrics_composite "
        "ON feed_metrics(feed_id, date DESC, fetch_successes, fetch_attempts)",
    ]

    for index_sql in performance_indexes:
        try:
            session.execute(index_sql)
            logger.info("Performance index created", index=index_sql[:80])
        except Exception as exc:
            logger.warning(
                "Failed to create index", index=index_sql[:80], error=str(exc)
            )

    session.commit()
    logger.info("Performance indexes creation completed")
