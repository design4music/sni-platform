"""
Database models for Strategic Narrative Intelligence ETL Pipeline

This module defines SQLAlchemy models for storing news articles, feeds,
processing metadata, and vector embeddings using pgvector.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional

import structlog
from pgvector.sqlalchemy import Vector
from sqlalchemy import (JSON, Boolean, CheckConstraint, Column, DateTime,
                        Float, ForeignKey, Index, Integer, String, Text,
                        UniqueConstraint)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

logger = structlog.get_logger(__name__)

Base = declarative_base()


class ProcessingStatus(PyEnum):
    """Processing status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    FILTERED_OUT = "filtered_out"
    DUPLICATE = "duplicate"


class FeedType(PyEnum):
    """Feed type enumeration"""

    RSS = "rss"
    GOOGLE_RSS = "google_rss"
    XML_SITEMAP = "xml_sitemap"
    API = "api"
    SCRAPER = "scraper"


class ContentCategory(PyEnum):
    """Content category enumeration"""

    GEOPOLITICS = "geopolitics"
    MILITARY = "military"
    ENERGY = "energy"
    AI_TECHNOLOGY = "ai_technology"
    ECONOMICS = "economics"
    DIPLOMACY = "diplomacy"
    SECURITY = "security"
    OTHER = "other"


class LanguageCode(PyEnum):
    """Supported language codes"""

    EN = "en"
    RU = "ru"
    DE = "de"
    FR = "fr"


# Create ENUMs for PostgreSQL
processing_status_enum = ENUM(ProcessingStatus, name="processing_status")
feed_type_enum = ENUM(FeedType, name="feed_type")
content_category_enum = ENUM(ContentCategory, name="content_category")
language_code_enum = ENUM(LanguageCode, name="language_code")


class NewsFeed(Base):
    """
    News feed configuration and metadata
    """

    __tablename__ = "news_feeds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    feed_type = Column(feed_type_enum, nullable=False)
    language = Column(language_code_enum, nullable=False)
    country_code = Column(String(2))  # ISO country code

    # Configuration
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=1)  # 1=high, 5=low
    fetch_interval_minutes = Column(Integer, default=60)

    # API-specific configuration
    api_key_required = Column(Boolean, default=False)
    api_headers = Column(JSON)
    api_params = Column(JSON)

    # Processing configuration
    content_xpath = Column(String(500))  # For scraper feeds
    title_xpath = Column(String(500))
    date_xpath = Column(String(500))

    # Quality metrics
    reliability_score = Column(Float, default=0.5)  # 0.0 to 1.0
    avg_articles_per_day = Column(Float)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_fetched_at = Column(DateTime)
    last_successful_fetch_at = Column(DateTime)

    # Relationships
    articles = relationship(
        "Article", back_populates="feed", cascade="all, delete-orphan"
    )
    feed_metrics = relationship(
        "FeedMetrics", back_populates="feed", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_news_feeds_active_priority", "is_active", "priority"),
        Index("idx_news_feeds_language", "language"),
        Index("idx_news_feeds_last_fetched", "last_fetched_at"),
    )


class Article(Base):
    """
    News article with full content and metadata
    """

    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feed_id = Column(UUID(as_uuid=True), ForeignKey("news_feeds.id"), nullable=False)

    # Content
    title = Column(Text, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    url = Column(Text, nullable=False)
    author = Column(String(255))

    # Metadata
    published_at = Column(DateTime, nullable=False)
    language = Column(language_code_enum, nullable=False)
    source_name = Column(String(255))

    # Content hashing for deduplication
    content_hash = Column(String(64), nullable=False)  # SHA-256 hash
    title_hash = Column(String(64), nullable=False)

    # Processing status
    processing_status = Column(processing_status_enum, default=ProcessingStatus.PENDING)
    ingestion_status = Column(processing_status_enum, default=ProcessingStatus.PENDING)
    filtering_status = Column(processing_status_enum, default=ProcessingStatus.PENDING)
    ner_status = Column(processing_status_enum, default=ProcessingStatus.PENDING)
    ml_status = Column(processing_status_enum, default=ProcessingStatus.PENDING)

    # Quality metrics
    relevance_score = Column(Float)  # 0.0 to 1.0
    quality_score = Column(Float)  # 0.0 to 1.0
    sentiment_score = Column(Float)  # -1.0 to 1.0

    # Content analysis
    word_count = Column(Integer)
    reading_time_minutes = Column(Float)

    # Categorization
    primary_category = Column(content_category_enum)
    categories = Column(JSON)  # List of categories with confidence scores

    # Geographic information
    countries_mentioned = Column(JSON)  # List of country codes
    regions_mentioned = Column(JSON)  # List of geographic regions

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)

    # Relationships
    feed = relationship("NewsFeed", back_populates="articles")
    entities = relationship(
        "EntityMention", back_populates="article", cascade="all, delete-orphan"
    )
    embeddings = relationship(
        "ArticleEmbedding", back_populates="article", cascade="all, delete-orphan"
    )
    clusters = relationship("ArticleCluster", back_populates="article")

    __table_args__ = (
        UniqueConstraint("feed_id", "content_hash", name="uq_article_content_hash"),
        Index("idx_articles_published_at", "published_at"),
        Index("idx_articles_processing_status", "processing_status"),
        Index("idx_articles_language", "language"),
        Index("idx_articles_category", "primary_category"),
        Index("idx_articles_relevance", "relevance_score"),
        Index("idx_articles_url_hash", "content_hash"),
        CheckConstraint("relevance_score >= 0 AND relevance_score <= 1"),
        CheckConstraint("quality_score >= 0 AND quality_score <= 1"),
        CheckConstraint("sentiment_score >= -1 AND sentiment_score <= 1"),
    )


class EntityMention(Base):
    """
    Named Entity Recognition results for articles
    """

    __tablename__ = "entity_mentions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False)

    # Entity details
    entity_text = Column(String(500), nullable=False)
    entity_type = Column(String(50), nullable=False)  # PERSON, ORG, GPE, etc.
    entity_label = Column(String(200))  # Normalized entity name

    # Position in text
    start_char = Column(Integer, nullable=False)
    end_char = Column(Integer, nullable=False)

    # Confidence and context
    confidence_score = Column(Float, nullable=False)
    context_snippet = Column(Text)

    # Normalization and linking
    knowledge_base_id = Column(String(100))  # Link to external KB
    wikipedia_id = Column(String(100))
    coordinates = Column(JSON)  # For geographic entities

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    article = relationship("Article", back_populates="entities")

    __table_args__ = (
        Index("idx_entity_mentions_article", "article_id"),
        Index("idx_entity_mentions_type", "entity_type"),
        Index("idx_entity_mentions_label", "entity_label"),
        Index("idx_entity_mentions_confidence", "confidence_score"),
    )


class ArticleEmbedding(Base):
    """
    Vector embeddings for articles using pgvector
    """

    __tablename__ = "article_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False)

    # Embedding details
    embedding_model = Column(
        String(100), nullable=False
    )  # e.g., 'sentence-transformers/all-MiniLM-L6-v2'
    embedding_version = Column(String(20), nullable=False)

    # Vector embeddings (pgvector)
    title_embedding = Column(Vector(384))  # Adjust dimension based on model
    content_embedding = Column(Vector(384))
    summary_embedding = Column(Vector(384))

    # Metadata
    embedding_created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    article = relationship("Article", back_populates="embeddings")

    __table_args__ = (
        UniqueConstraint(
            "article_id",
            "embedding_model",
            "embedding_version",
            name="uq_article_embedding",
        ),
        Index("idx_article_embeddings_model", "embedding_model"),
    )


class ArticleCluster(Base):
    """
    ML clustering results for articles
    """

    __tablename__ = "article_clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False)

    # Cluster information
    cluster_id = Column(String(100), nullable=False)
    cluster_algorithm = Column(String(50), nullable=False)  # e.g., 'CLUST-1', 'CLUST-2'
    cluster_version = Column(String(20), nullable=False)

    # Clustering metadata
    similarity_score = Column(Float)  # Similarity to cluster centroid
    cluster_size = Column(Integer)  # Number of articles in cluster
    cluster_label = Column(String(255))  # Human-readable cluster label
    cluster_keywords = Column(JSON)  # Key terms/topics for cluster

    # Timestamps
    clustered_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    article = relationship("Article", back_populates="clusters")

    __table_args__ = (
        Index("idx_article_clusters_cluster_id", "cluster_id"),
        Index("idx_article_clusters_algorithm", "cluster_algorithm"),
        Index("idx_article_clusters_similarity", "similarity_score"),
    )


class TrendingTopic(Base):
    """
    Real-time trending topics and narratives
    """

    __tablename__ = "trending_topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Topic details
    topic_name = Column(String(255), nullable=False)
    topic_keywords = Column(JSON, nullable=False)  # List of keywords
    topic_description = Column(Text)

    # Trending metrics
    mention_count = Column(Integer, default=0)
    trending_score = Column(Float, nullable=False)  # Calculated trending intensity
    velocity = Column(Float)  # Rate of change in mentions

    # Time window
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)

    # Geographic distribution
    countries_trending = Column(JSON)  # List of country codes where trending
    languages = Column(JSON)  # Languages where topic is trending

    # Related articles
    article_count = Column(Integer, default=0)
    sample_article_ids = Column(JSON)  # Sample of related article IDs

    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_trending_topics_score", "trending_score"),
        Index("idx_trending_topics_detected", "detected_at"),
        Index("idx_trending_topics_window", "window_start", "window_end"),
    )


class PipelineRun(Base):
    """
    ETL pipeline execution tracking
    """

    __tablename__ = "pipeline_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_id = Column(String(100), nullable=False)

    # Execution details
    status = Column(processing_status_enum, nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)

    # Metrics
    feeds_processed = Column(Integer, default=0)
    articles_ingested = Column(Integer, default=0)
    articles_filtered = Column(Integer, default=0)
    articles_processed = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)

    # Performance metrics
    processing_time_seconds = Column(Float)
    throughput_articles_per_second = Column(Float)

    # Configuration snapshot
    config_snapshot = Column(JSON)

    # Error details
    error_message = Column(Text)
    error_details = Column(JSON)

    __table_args__ = (
        Index("idx_pipeline_runs_pipeline_id", "pipeline_id"),
        Index("idx_pipeline_runs_status", "status"),
        Index("idx_pipeline_runs_started", "started_at"),
    )


class FeedMetrics(Base):
    """
    Feed performance and quality metrics
    """

    __tablename__ = "feed_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feed_id = Column(UUID(as_uuid=True), ForeignKey("news_feeds.id"), nullable=False)

    # Time window
    date = Column(DateTime, nullable=False)  # Daily metrics

    # Fetch metrics
    fetch_attempts = Column(Integer, default=0)
    fetch_successes = Column(Integer, default=0)
    fetch_failures = Column(Integer, default=0)

    # Content metrics
    articles_fetched = Column(Integer, default=0)
    articles_new = Column(Integer, default=0)
    articles_duplicate = Column(Integer, default=0)
    articles_filtered_out = Column(Integer, default=0)

    # Quality metrics
    avg_relevance_score = Column(Float)
    avg_quality_score = Column(Float)
    avg_processing_time_seconds = Column(Float)

    # Error tracking
    error_count = Column(Integer, default=0)
    last_error_message = Column(Text)

    # Relationships
    feed = relationship("NewsFeed", back_populates="feed_metrics")

    __table_args__ = (
        UniqueConstraint("feed_id", "date", name="uq_feed_metrics_daily"),
        Index("idx_feed_metrics_date", "date"),
        Index(
            "idx_feed_metrics_fetch_success_rate", "fetch_successes", "fetch_attempts"
        ),
    )


class DataQualityReport(Base):
    """
    Data quality assessment reports
    """

    __tablename__ = "data_quality_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Report details
    report_type = Column(String(50), nullable=False)  # 'daily', 'weekly', 'monthly'
    report_date = Column(DateTime, nullable=False)

    # Quality metrics
    total_articles = Column(Integer, default=0)
    duplicate_articles = Column(Integer, default=0)
    low_quality_articles = Column(Integer, default=0)
    irrelevant_articles = Column(Integer, default=0)

    # Language distribution
    language_distribution = Column(JSON)

    # Category distribution
    category_distribution = Column(JSON)

    # Feed performance summary
    active_feeds = Column(Integer, default=0)
    failing_feeds = Column(Integer, default=0)
    avg_feed_reliability = Column(Float)

    # Processing performance
    avg_processing_time = Column(Float)
    processing_error_rate = Column(Float)

    # Data freshness
    avg_article_age_hours = Column(Float)
    stale_articles_count = Column(Integer, default=0)

    # Detailed analysis
    quality_issues = Column(JSON)  # Detailed quality issue breakdown
    recommendations = Column(JSON)  # System recommendations

    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_data_quality_reports_date", "report_date"),
        Index("idx_data_quality_reports_type", "report_type"),
    )


# ============================================================================
# NSF-1 NARRATIVE INTELLIGENCE MODELS
# ============================================================================


class NarrativeNSF1(Base):
    """
    NSF-1 Narrative Model - Exact match to finalized specification
    Uses UUID primary key internally with narrative_id for display/API
    This is the main Narrative model for content storage.
    """

    __tablename__ = "narratives"

    # PRIMARY KEY - UUID for internal use
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # DISPLAY ID - Used by API and frontend (e.g., "EN-002-A")
    narrative_id = Column(String(50), nullable=False, unique=True)

    # CORE NSF-1 FIELDS (scalar columns)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    origin_language = Column(String(2), nullable=False)

    # QUALITY AND CONFIDENCE (scalar columns)
    confidence_rating = Column(String(20))  # low, medium, high, very_high

    # FRINGE AND QUALITY METADATA - structured JSONB fields
    fringe_notes = Column(
        JSONB, nullable=False, default=list
    )  # Array of fringe/outlier annotations
    data_quality_notes = Column(
        JSONB, nullable=False, default=list
    )  # Array of data quality issues

    # HIERARCHY FIELD - canonical parent/child relationship
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("narratives.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # ARRAY FIELDS - stored as JSONB
    dominant_source_languages = Column(JSONB, nullable=False, default=list)
    alignment = Column(JSONB, nullable=False, default=list)
    actor_origin = Column(JSONB, nullable=False, default=list)
    conflict_alignment = Column(JSONB, nullable=False, default=list)
    frame_logic = Column(JSONB, nullable=False, default=list)
    nested_within = Column(JSONB, default=list)  # DEPRECATED: Use parent_id instead
    conflicts_with = Column(JSONB, default=list)
    logical_strain = Column(JSONB, default=list)

    # STRUCTURED OBJECT FIELDS - stored as JSONB
    narrative_tension = Column(JSONB, default=list)  # Array of {type, description}
    activity_timeline = Column(JSONB, default=dict)  # Object with date keys
    turning_points = Column(JSONB, default=list)  # Array of {date, description}
    media_spike_history = Column(JSONB, default=dict)  # Object with date keys
    source_stats = Column(JSONB, default=dict)  # Object with total_articles, sources
    top_excerpts = Column(JSONB, default=list)  # Array of excerpt objects
    update_status = Column(
        JSONB, default=dict
    )  # Object with last_updated, update_trigger
    version_history = Column(JSONB, default=list)  # Array of version objects
    rai_analysis = Column(JSONB, default=dict)  # RAI analysis object

    # SEARCH AND PERFORMANCE FIELDS
    narrative_embedding = Column(Vector(1536))  # For semantic similarity
    # Note: search_vector will be added as generated column in SQL

    # METADATA
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # Self-referential relationship for parent/child hierarchy
    children = relationship(
        "NarrativeNSF1",
        backref="parent",
        remote_side=[id],
        cascade="all, delete",
        passive_deletes=True,
    )

    article_associations = relationship(
        "NarrativeArticleAssociation",
        back_populates="narrative",
        cascade="all, delete-orphan",
    )
    metrics = relationship(
        "NarrativeMetrics",
        back_populates="narrative",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Narrative(id={self.id}, narrative_id='{self.narrative_id}', title='{self.title[:50]}...')>"

    def is_parent(self) -> bool:
        """Check if this narrative is a parent (has no parent_id)."""
        return self.parent_id is None

    def is_child(self) -> bool:
        """Check if this narrative is a child (has parent_id)."""
        return self.parent_id is not None

    def get_root(self):
        """Get the root parent narrative in the hierarchy."""
        if self.parent_id is None:
            return self
        return self.parent.get_root() if self.parent else self

    def get_hierarchy_level(self) -> int:
        """Get the level in hierarchy (0 = parent, 1 = child)."""
        return 0 if self.parent_id is None else 1

    # ========================================================================
    # FRINGE AND QUALITY NOTES HELPER METHODS
    # ========================================================================

    def add_fringe_note(
        self,
        summary: str,
        source_count: Optional[int] = None,
        tone: Optional[str] = None,
        example_articles: Optional[List[str]] = None,
    ) -> None:
        """Add a fringe note to track narrative outliers and low-diversity content.

        Args:
            summary: Brief 1-2 sentence description of the fringe content
            source_count: Number of sources supporting this fringe perspective
            tone: Tone classification (propagandistic, neutral, etc.)
            example_articles: List of article URLs as evidence
        """
        from datetime import datetime

        fringe_note = {
            "note_type": "fringe",
            "summary": summary,
            "source_count": source_count,
            "tone": tone,
            "example_articles": example_articles or [],
            "detected_at": datetime.utcnow().isoformat(),
        }

        # Initialize fringe_notes if None
        if self.fringe_notes is None:
            self.fringe_notes = []

        # Add note and update timestamp
        self.fringe_notes = self.fringe_notes + [fringe_note]
        self.updated_at = datetime.utcnow()

    def add_data_quality_note(
        self,
        summary: str,
        source_count: Optional[int] = None,
        example_articles: Optional[List[str]] = None,
    ) -> None:
        """Add a data quality note to track pipeline and processing issues.

        Args:
            summary: Brief description of the data quality issue
            source_count: Number of sources affected by this issue
            example_articles: List of article URLs demonstrating the issue
        """
        from datetime import datetime

        quality_note = {
            "note_type": "quality",
            "summary": summary,
            "source_count": source_count,
            "example_articles": example_articles or [],
            "detected_at": datetime.utcnow().isoformat(),
        }

        # Initialize data_quality_notes if None
        if self.data_quality_notes is None:
            self.data_quality_notes = []

        # Add note and update timestamp
        self.data_quality_notes = self.data_quality_notes + [quality_note]
        self.updated_at = datetime.utcnow()

    def get_fringe_notes_by_tone(self, tone: str) -> List[Dict[str, Any]]:
        """Get all fringe notes with a specific tone.

        Args:
            tone: Target tone to filter by (e.g., 'propagandistic', 'neutral')

        Returns:
            List of fringe notes matching the tone
        """
        if not self.fringe_notes:
            return []

        return [
            note
            for note in self.fringe_notes
            if note.get("tone") == tone and note.get("note_type") == "fringe"
        ]

    def get_latest_quality_issues(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get the most recent data quality issues.

        Args:
            limit: Maximum number of issues to return

        Returns:
            List of most recent quality notes
        """
        if not self.data_quality_notes:
            return []

        # Sort by detected_at timestamp descending
        quality_notes = [
            note
            for note in self.data_quality_notes
            if note.get("note_type") == "quality"
        ]

        sorted_notes = sorted(
            quality_notes, key=lambda x: x.get("detected_at", ""), reverse=True
        )

        return sorted_notes[:limit]

    def has_fringe_content(self) -> bool:
        """Check if this narrative has any fringe notes."""
        return bool(self.fringe_notes and len(self.fringe_notes) > 0)

    def has_quality_issues(self) -> bool:
        """Check if this narrative has any data quality issues."""
        return bool(self.data_quality_notes and len(self.data_quality_notes) > 0)

    def get_fringe_summary(self) -> Dict[str, Any]:
        """Get summary statistics about fringe content in this narrative.

        Returns:
            Dictionary with fringe analysis metrics
        """
        if not self.fringe_notes:
            return {
                "has_fringe": False,
                "total_notes": 0,
                "tones": [],
                "avg_source_count": None,
            }

        fringe_only = [n for n in self.fringe_notes if n.get("note_type") == "fringe"]

        tones = list(set(note.get("tone") for note in fringe_only if note.get("tone")))

        source_counts = [
            note.get("source_count")
            for note in fringe_only
            if note.get("source_count") is not None
        ]

        return {
            "has_fringe": len(fringe_only) > 0,
            "total_notes": len(fringe_only),
            "tones": tones,
            "avg_source_count": (
                sum(source_counts) / len(source_counts) if source_counts else None
            ),
        }

    __table_args__ = (
        # Indexes for performance
        Index("idx_narratives_narrative_id", "narrative_id"),
        Index("idx_narratives_origin_language", "origin_language"),
        Index("idx_narratives_confidence", "confidence_rating"),
        Index("idx_narratives_created", "created_at"),
        Index("idx_narratives_updated", "updated_at"),
        # Hierarchy indexes (parent_id based)
        Index("idx_narratives_parent_id", "parent_id"),
        Index(
            "idx_narratives_parent_children",
            "parent_id",
            postgresql_where="parent_id IS NOT NULL",
        ),
        Index(
            "idx_narratives_parents", "parent_id", postgresql_where="parent_id IS NULL"
        ),
        Index("idx_narratives_hierarchy_created", "parent_id", "created_at"),
        # JSONB GIN indexes for array/object queries
        Index("idx_narratives_alignment_gin", "alignment", postgresql_using="gin"),
        Index(
            "idx_narratives_actor_origin_gin", "actor_origin", postgresql_using="gin"
        ),
        Index("idx_narratives_frame_logic_gin", "frame_logic", postgresql_using="gin"),
        Index(
            "idx_narratives_nested_within_gin", "nested_within", postgresql_using="gin"
        ),  # DEPRECATED
        Index(
            "idx_narratives_conflicts_with_gin",
            "conflicts_with",
            postgresql_using="gin",
        ),
        Index(
            "idx_narratives_dominant_source_languages_gin",
            "dominant_source_languages",
            postgresql_using="gin",
        ),
        Index(
            "idx_narratives_conflict_alignment_gin",
            "conflict_alignment",
            postgresql_using="gin",
        ),
        # FRINGE AND QUALITY NOTES indexes
        Index(
            "idx_narratives_fringe_notes_gin", "fringe_notes", postgresql_using="gin"
        ),
        Index(
            "idx_narratives_data_quality_notes_gin",
            "data_quality_notes",
            postgresql_using="gin",
        ),
        # Vector similarity index
        Index(
            "idx_narratives_embedding",
            "narrative_embedding",
            postgresql_using="ivfflat",
            postgresql_ops={"narrative_embedding": "vector_cosine_ops"},
        ),
        # Constraints
        CheckConstraint(
            "confidence_rating IN ('low', 'medium', 'high', 'very_high') OR confidence_rating IS NULL",
            name="chk_narratives_confidence_rating",
        ),
        CheckConstraint(
            "length(origin_language) = 2", name="chk_narratives_origin_language_length"
        ),
        CheckConstraint(
            "length(narrative_id) >= 3", name="chk_narratives_narrative_id_length"
        ),
        CheckConstraint("id != parent_id", name="chk_narratives_no_self_reference"),
    )


class NarrativeMetrics(Base):
    """
    Analytics and metrics for narratives - separate from NSF-1 content
    This table stores all analytics, scoring, and operational data
    while keeping NSF-1 narratives table purely for content.
    One-to-one relationship with NarrativeNSF1.
    """

    __tablename__ = "narrative_metrics"

    # Foreign key to narratives table (UUID primary key)
    narrative_uuid = Column(
        UUID(as_uuid=True), ForeignKey("narratives.id"), primary_key=True
    )

    # TEMPORAL FIELDS
    narrative_start_date = Column(DateTime)
    narrative_end_date = Column(DateTime)
    last_spike = Column(DateTime)

    # SCORING FIELDS
    trending_score = Column(Float, default=0.0)
    credibility_score = Column(Float)
    engagement_score = Column(Float)
    sentiment_score = Column(Float)

    # PRIORITY AND STATUS
    narrative_priority = Column(Integer, default=5)
    narrative_status = Column(String(20), default="active")

    # METADATA
    geographic_scope = Column(String(100))  # e.g., 'global', 'europe', 'us-domestic'
    update_frequency = Column(String(50), default="15 minutes")
    version_number = Column(Integer, default=1)

    # KEYWORDS FOR QUICK FILTERING
    keywords = Column(JSON)  # Array of core tags for filtering and search

    # TIMESTAMPS
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    narrative = relationship("NarrativeNSF1", back_populates="metrics", uselist=False)

    __table_args__ = (
        # Indexes for dashboard and trending queries
        Index("idx_narrative_metrics_trending_score", "trending_score"),
        Index("idx_narrative_metrics_status", "narrative_status"),
        Index("idx_narrative_metrics_priority", "narrative_priority"),
        Index("idx_narrative_metrics_credibility", "credibility_score"),
        Index("idx_narrative_metrics_engagement", "engagement_score"),
        Index("idx_narrative_metrics_start_date", "narrative_start_date"),
        Index("idx_narrative_metrics_geographic_scope", "geographic_scope"),
        # Composite indexes for common dashboard queries
        Index(
            "idx_narrative_metrics_status_trending",
            "narrative_status",
            "trending_score",
        ),
        Index(
            "idx_narrative_metrics_active_priority",
            "narrative_status",
            "narrative_priority",
        ),
        # Constraints
        CheckConstraint(
            "trending_score >= 0", name="chk_narrative_metrics_trending_score"
        ),
        CheckConstraint(
            "credibility_score >= 0 AND credibility_score <= 10 OR credibility_score IS NULL",
            name="chk_narrative_metrics_credibility_score",
        ),
        CheckConstraint(
            "engagement_score >= 0 AND engagement_score <= 1 OR engagement_score IS NULL",
            name="chk_narrative_metrics_engagement_score",
        ),
        CheckConstraint(
            "sentiment_score >= -1 AND sentiment_score <= 1 OR sentiment_score IS NULL",
            name="chk_narrative_metrics_sentiment_score",
        ),
        CheckConstraint(
            "narrative_priority >= 1 AND narrative_priority <= 10",
            name="chk_narrative_metrics_priority",
        ),
        CheckConstraint(
            "narrative_status IN ('active', 'emerging', 'declining', 'dormant', 'archived')",
            name="chk_narrative_metrics_status",
        ),
        CheckConstraint(
            "narrative_start_date IS NULL OR narrative_end_date IS NULL OR narrative_start_date <= narrative_end_date",
            name="chk_narrative_metrics_dates",
        ),
    )

    def __repr__(self):
        return f"<NarrativeMetrics(narrative_uuid={self.narrative_uuid}, status='{self.narrative_status}', trending_score={self.trending_score})>"


class NarrativeArticleAssociation(Base):
    """
    Many-to-many relationship between narratives and articles
    Links NSF-1 narratives to source articles with relevance scoring
    """

    __tablename__ = "narrative_articles"

    # Foreign keys
    narrative_id = Column(
        UUID(as_uuid=True), ForeignKey("narratives.id"), primary_key=True
    )
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), primary_key=True)

    # Association metadata
    relevance_score = Column(Float, nullable=False, default=0.5)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = Column(String(50), default="auto")  # 'auto' or 'manual'

    # Relationships
    narrative = relationship("NarrativeNSF1", back_populates="article_associations")
    article = relationship("Article")  # Assuming Article model exists

    __table_args__ = (
        Index("idx_narrative_articles_narrative_id", "narrative_id"),
        Index("idx_narrative_articles_article_id", "article_id"),
        Index("idx_narrative_articles_relevance", "narrative_id", "relevance_score"),
        CheckConstraint(
            "relevance_score >= 0 AND relevance_score <= 1",
            name="chk_narrative_articles_relevance_score",
        ),
    )

    def __repr__(self):
        return f"<NarrativeArticleAssociation(narrative_id={self.narrative_id}, article_id={self.article_id}, relevance={self.relevance_score})>"


# ============================================================================
# MODEL ALIASES FOR CLEANER IMPORTS
# ============================================================================

# Provide cleaner aliases for the main models
Narrative = NarrativeNSF1  # Main narrative model
# NarrativeMetrics already has a clean name


# ============================================================================
# Database utility functions
def create_all_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(engine)
    logger.info("All database tables created successfully")


def drop_all_tables(engine):
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(engine)
    logger.warning("All database tables dropped")


def get_table_info():
    """Get information about all defined tables"""
    tables_info = {}
    for table_name, table in Base.metadata.tables.items():
        tables_info[table_name] = {
            "columns": [col.name for col in table.columns],
            "indexes": [idx.name for idx in table.indexes],
            "constraints": [const.name for const in table.constraints if const.name],
        }
    return tables_info
