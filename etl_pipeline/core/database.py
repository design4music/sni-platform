"""
Database models and connection management for the ETL pipeline
"""

import uuid
from datetime import datetime
from enum import Enum

from config.settings import settings
from pgvector.sqlalchemy import Vector
from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Index, Integer, String, Text, UniqueConstraint,
                        create_engine)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

# Database setup
engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_pool_max_overflow,
    echo=settings.debug,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class PipelineStage(str, Enum):
    INGESTION = "ingestion"
    CLUST_1 = "clust_1_thematic"
    CLUST_2 = "clust_2_interpretive"
    CLUST_3 = "clust_3_temporal_anomaly"
    CLUST_4 = "clust_4_consolidation"
    GEN_1 = "gen_1_narrative_builder"
    GEN_2 = "gen_2_updates"
    GEN_3 = "gen_3_contradiction_detection"


# Models
class NewsSource(Base):
    """News source configuration"""

    __tablename__ = "news_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    url = Column(Text, nullable=False)
    source_type = Column(String(20), nullable=False)  # rss, api
    language = Column(String(5), nullable=False)
    category = Column(String(50))
    priority = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer)  # requests per hour
    last_fetch = Column(DateTime(timezone=True))
    success_rate = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    articles = relationship("Article", back_populates="source")


class Article(Base):
    """Raw article data"""

    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("news_sources.id"))

    # Article metadata
    title = Column(Text, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    url = Column(Text, nullable=False)
    author = Column(String(200))
    language = Column(String(5))

    # Timestamps
    published_at = Column(DateTime(timezone=True))
    fetched_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Processing status
    processing_status = Column(String(20), default=ProcessingStatus.PENDING)
    current_stage = Column(String(30), default=PipelineStage.INGESTION)

    # Embeddings and features
    title_embedding = Column(Vector(settings.embedding_dimension))
    content_embedding = Column(Vector(settings.embedding_dimension))

    # Extracted features
    entities = Column(JSON)  # Named entities
    sentiment = Column(JSON)  # Sentiment analysis results
    topics = Column(ARRAY(String))
    keywords = Column(ARRAY(String))

    # Quality metrics
    quality_score = Column(Float)
    readability_score = Column(Float)
    credibility_score = Column(Float)

    # Metadata
    metadata = Column(JSON)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    source = relationship("NewsSource", back_populates="articles")
    cluster_assignments = relationship("ClusterAssignment", back_populates="article")

    # Indexes
    __table_args__ = (
        Index("idx_articles_published_at", "published_at"),
        Index("idx_articles_processing_status", "processing_status"),
        Index("idx_articles_current_stage", "current_stage"),
        Index("idx_articles_url_hash", "url"),
        Index(
            "idx_articles_title_embedding",
            "title_embedding",
            postgresql_using="ivfflat",
        ),
        Index(
            "idx_articles_content_embedding",
            "content_embedding",
            postgresql_using="ivfflat",
        ),
    )


class Cluster(Base):
    """Clustering results for each stage"""

    __tablename__ = "clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage = Column(String(30), nullable=False)  # clust_1, clust_2, etc.
    cluster_label = Column(String(100))

    # Cluster characteristics
    centroid = Column(Vector(settings.embedding_dimension))
    size = Column(Integer, default=0)
    coherence_score = Column(Float)
    temporal_span_hours = Column(Float)

    # Cluster metadata
    dominant_topics = Column(ARRAY(String))
    key_entities = Column(JSON)
    sentiment_distribution = Column(JSON)
    language_distribution = Column(JSON)
    source_distribution = Column(JSON)

    # Narrative elements
    main_narrative = Column(Text)
    sub_narratives = Column(JSON)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    assignments = relationship("ClusterAssignment", back_populates="cluster")
    narratives = relationship("GeneratedNarrative", back_populates="cluster")

    # Indexes
    __table_args__ = (
        Index("idx_clusters_stage", "stage"),
        Index("idx_clusters_created_at", "created_at"),
        Index("idx_clusters_centroid", "centroid", postgresql_using="ivfflat"),
    )


class ClusterAssignment(Base):
    """Many-to-many relationship between articles and clusters"""

    __tablename__ = "cluster_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"))
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id"))

    # Assignment metadata
    confidence_score = Column(Float)
    distance_to_centroid = Column(Float)
    assignment_reason = Column(Text)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    article = relationship("Article", back_populates="cluster_assignments")
    cluster = relationship("Cluster", back_populates="assignments")

    # Constraints
    __table_args__ = (
        UniqueConstraint("article_id", "cluster_id", name="uq_article_cluster"),
        Index("idx_cluster_assignments_article", "article_id"),
        Index("idx_cluster_assignments_cluster", "cluster_id"),
    )


class GeneratedNarrative(Base):
    """Generated narratives from the generation pipeline"""

    __tablename__ = "generated_narratives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id"))
    stage = Column(String(30), nullable=False)  # gen_1, gen_2, gen_3

    # Generated content
    title = Column(Text)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    key_points = Column(JSON)

    # Generation metadata
    model_used = Column(String(50))
    generation_params = Column(JSON)
    confidence_score = Column(Float)

    # Narrative characteristics
    narrative_type = Column(String(50))  # main, update, contradiction
    contradictions_detected = Column(JSON)
    update_reason = Column(Text)

    # Versioning
    version = Column(Integer, default=1)
    parent_narrative_id = Column(UUID(as_uuid=True))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    cluster = relationship("Cluster", back_populates="narratives")

    # Indexes
    __table_args__ = (
        Index("idx_narratives_cluster", "cluster_id"),
        Index("idx_narratives_stage", "stage"),
        Index("idx_narratives_created_at", "created_at"),
    )


class PipelineExecution(Base):
    """Track pipeline execution runs"""

    __tablename__ = "pipeline_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_date = Column(DateTime(timezone=True), nullable=False)
    stage = Column(String(30), nullable=False)

    # Execution details
    status = Column(String(20), default=ProcessingStatus.PENDING)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Float)

    # Metrics
    items_processed = Column(Integer, default=0)
    items_successful = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSON)
    retry_count = Column(Integer, default=0)

    # Configuration used
    config_snapshot = Column(JSON)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_pipeline_executions_date_stage", "execution_date", "stage"),
        Index("idx_pipeline_executions_status", "status"),
    )


class QualityMetric(Base):
    """Data quality metrics and validation results"""

    __tablename__ = "quality_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_executions.id"))
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float)
    threshold = Column(Float)
    passed = Column(Boolean)

    # Additional context
    details = Column(JSON)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# Database utility functions
def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)


# Database connection test
def test_connection() -> bool:
    """Test database connection"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False
