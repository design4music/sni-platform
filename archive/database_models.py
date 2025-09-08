"""
Database models for Strategic Narrative Intelligence platform using SQLAlchemy
Includes all tables, relationships, and database configuration
"""

import enum
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, JSON, Boolean, CheckConstraint, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (Float, ForeignKey, Index, Integer, LargeBinary, String,
                        Table, Text, UniqueConstraint)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.dialects.postgresql import VECTOR
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

# ============================================================================
# ENUMS
# ============================================================================


class AlignmentType(enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class NarrativeStatus(enum.Enum):
    ACTIVE = "active"
    EMERGING = "emerging"
    DECLINING = "declining"
    DORMANT = "dormant"


class SourceType(enum.Enum):
    NEWS = "news"
    SOCIAL = "social"
    BLOG = "blog"
    ACADEMIC = "academic"
    GOVERNMENT = "government"


class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(enum.Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"


# ============================================================================
# ASSOCIATION TABLES (Many-to-Many relationships)
# ============================================================================

# Narratives to Articles association
narrative_articles = Table(
    "narrative_articles",
    Base.metadata,
    Column(
        "narrative_id",
        PGUUID(as_uuid=True),
        ForeignKey("narratives.id"),
        primary_key=True,
    ),
    Column(
        "article_id", PGUUID(as_uuid=True), ForeignKey("articles.id"), primary_key=True
    ),
    Column("relevance_score", Float, nullable=False, default=0.0),
    Column("created_at", DateTime(timezone=True), default=func.now()),
    Index("idx_narrative_articles_relevance", "relevance_score"),
    Index("idx_narrative_articles_created", "created_at"),
)

# Narratives to Clusters association
narrative_clusters = Table(
    "narrative_clusters",
    Base.metadata,
    Column(
        "narrative_id",
        PGUUID(as_uuid=True),
        ForeignKey("narratives.id"),
        primary_key=True,
    ),
    Column(
        "cluster_id", PGUUID(as_uuid=True), ForeignKey("clusters.id"), primary_key=True
    ),
    Column("membership_score", Float, nullable=False, default=0.0),
    Column("created_at", DateTime(timezone=True), default=func.now()),
)

# User favorites/bookmarks
user_narrative_bookmarks = Table(
    "user_narrative_bookmarks",
    Base.metadata,
    Column("user_id", PGUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column(
        "narrative_id",
        PGUUID(as_uuid=True),
        ForeignKey("narratives.id"),
        primary_key=True,
    ),
    Column("created_at", DateTime(timezone=True), default=func.now()),
)

# ============================================================================
# CORE MODELS
# ============================================================================


class User(Base):
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    created_narratives = relationship("Narrative", back_populates="creator")
    created_articles = relationship("Article", back_populates="creator")
    bookmarked_narratives = relationship(
        "Narrative",
        secondary=user_narrative_bookmarks,
        back_populates="bookmarked_by_users",
    )
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("length(username) >= 3", name="username_min_length"),
        CheckConstraint("length(password_hash) >= 60", name="password_hash_min_length"),
        Index("idx_users_role_active", "role", "is_active"),
    )


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))

    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=100)
    requests_today = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="api_keys")


class Source(Base):
    __tablename__ = "sources"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False, unique=True)
    type = Column(SQLEnum(SourceType), nullable=False)
    base_url = Column(String(500), nullable=False)
    credibility_score = Column(Float, nullable=False, default=0.5)
    bias_score = Column(Float, nullable=False, default=0.0)  # -1 (left) to 1 (right)
    is_active = Column(Boolean, default=True, nullable=False)

    # RSS/API configuration
    feed_url = Column(String(500))
    api_key = Column(String(255))
    update_frequency_minutes = Column(Integer, default=60)
    last_crawled = Column(DateTime(timezone=True))

    # Quality metrics
    articles_count = Column(Integer, default=0)
    avg_quality_score = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    articles = relationship("Article", back_populates="source")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "credibility_score >= 0.0 AND credibility_score <= 1.0",
            name="credibility_score_range",
        ),
        CheckConstraint(
            "bias_score >= -1.0 AND bias_score <= 1.0", name="bias_score_range"
        ),
        Index("idx_sources_type_active", "type", "is_active"),
    )


class Article(Base):
    __tablename__ = "articles"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(1000), nullable=False, unique=True, index=True)
    author = Column(String(200))
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    language = Column(String(5), default="en", nullable=False)

    # Foreign keys
    source_id = Column(PGUUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    creator_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    # ML/Analysis fields
    embedding_vector = Column(VECTOR(384))  # Assuming 384-dim embeddings
    sentiment_score = Column(Float, default=0.0)  # -1 to 1
    relevance_score = Column(Float, default=0.0)  # 0 to 1
    quality_score = Column(Float, default=0.0)  # 0 to 1

    # Metadata
    tags = Column(ARRAY(String), default=list)
    word_count = Column(Integer, default=0)
    reading_time_minutes = Column(Integer, default=0)

    # Processing status
    is_processed = Column(Boolean, default=False, nullable=False)
    processing_error = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    source = relationship("Source", back_populates="articles")
    creator = relationship("User", back_populates="created_articles")
    narratives = relationship(
        "Narrative", secondary=narrative_articles, back_populates="articles"
    )
    excerpts = relationship(
        "SourceExcerpt", back_populates="article", cascade="all, delete-orphan"
    )
    turning_point_articles = relationship(
        "TurningPointArticle", back_populates="article"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "sentiment_score >= -1.0 AND sentiment_score <= 1.0",
            name="sentiment_score_range",
        ),
        CheckConstraint(
            "relevance_score >= 0.0 AND relevance_score <= 1.0",
            name="relevance_score_range",
        ),
        CheckConstraint(
            "quality_score >= 0.0 AND quality_score <= 1.0", name="quality_score_range"
        ),
        CheckConstraint("word_count >= 0", name="word_count_positive"),
        Index("idx_articles_published_relevance", "published_at", "relevance_score"),
        Index("idx_articles_source_processed", "source_id", "is_processed"),
        Index("idx_articles_embedding_vector", "embedding_vector"),
    )


class Narrative(Base):
    __tablename__ = "narratives"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(200), nullable=False)
    description = Column(String(2000), nullable=False)
    topic = Column(String(100), nullable=False, index=True)
    alignment = Column(SQLEnum(AlignmentType), nullable=False, index=True)
    status = Column(
        SQLEnum(NarrativeStatus), nullable=False, default=NarrativeStatus.EMERGING
    )

    # Foreign keys
    creator_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    # CANONICAL PARENT-CHILD HIERARCHY FIELD
    parent_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("narratives.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Scoring and metrics
    confidence_score = Column(Float, nullable=False, default=0.0)
    impact_score = Column(Float, nullable=False, default=0.0)
    trend_momentum = Column(Float, default=0.0)  # -1 to 1

    # ML fields
    embedding_vector = Column(VECTOR(384))

    # Metadata
    tags = Column(ARRAY(String), default=list)
    keywords = Column(ARRAY(String), default=list)

    # Derived metrics (updated by background processes)
    article_count = Column(Integer, default=0)
    last_activity = Column(DateTime(timezone=True), default=func.now())

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    creator = relationship("User", back_populates="created_narratives")
    articles = relationship(
        "Article", secondary=narrative_articles, back_populates="narratives"
    )
    timeline = relationship(
        "TurningPoint", back_populates="narrative", cascade="all, delete-orphan"
    )
    source_excerpts = relationship(
        "SourceExcerpt", back_populates="narrative", cascade="all, delete-orphan"
    )
    tensions_as_primary = relationship(
        "NarrativeTension",
        foreign_keys="NarrativeTension.primary_narrative_id",
        back_populates="primary_narrative",
        cascade="all, delete-orphan",
    )
    tensions_as_opposing = relationship(
        "NarrativeTension",
        foreign_keys="NarrativeTension.opposing_narrative_id",
        back_populates="opposing_narrative",
    )
    clusters = relationship(
        "Cluster", secondary=narrative_clusters, back_populates="narratives"
    )
    bookmarked_by_users = relationship(
        "User",
        secondary=user_narrative_bookmarks,
        back_populates="bookmarked_narratives",
    )
    analytics = relationship(
        "NarrativeAnalytics", back_populates="narrative", cascade="all, delete-orphan"
    )
    rai_analyses = relationship(
        "RAIAnalysis", back_populates="narrative", cascade="all, delete-orphan"
    )

    # CANONICAL PARENT-CHILD HIERARCHY RELATIONSHIPS
    # Self-referential relationship for parent/child hierarchy
    children = relationship(
        "Narrative",
        backref="parent",
        remote_side=[id],
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Hierarchy helper methods
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

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="confidence_score_range",
        ),
        CheckConstraint(
            "impact_score >= 0.0 AND impact_score <= 1.0", name="impact_score_range"
        ),
        CheckConstraint(
            "trend_momentum >= -1.0 AND trend_momentum <= 1.0",
            name="trend_momentum_range",
        ),
        # CANONICAL PARENT-CHILD HIERARCHY CONSTRAINTS
        CheckConstraint("id != parent_id", name="chk_narratives_no_self_reference"),
        # Performance indexes
        Index("idx_narratives_topic_status", "topic", "status"),
        Index("idx_narratives_scores", "confidence_score", "impact_score"),
        Index("idx_narratives_activity", "last_activity"),
        # CANONICAL: Parent-child hierarchy indexes
        Index("idx_narratives_parent_id", "parent_id"),
        Index(
            "idx_narratives_parent_children",
            "parent_id",
            postgresql_where="parent_id IS NOT NULL",
        ),
        Index(
            "idx_narratives_parents_only",
            "parent_id",
            postgresql_where="parent_id IS NULL",
        ),
        Index("idx_narratives_hierarchy_created", "parent_id", "created_at"),
    )

    @hybrid_property
    def all_tensions(self):
        """Get all tensions (both as primary and opposing narrative)."""
        return self.tensions_as_primary + self.tensions_as_opposing


class TurningPoint(Base):
    __tablename__ = "turning_points"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    narrative_id = Column(
        PGUUID(as_uuid=True), ForeignKey("narratives.id"), nullable=False
    )
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    event_description = Column(String(1000), nullable=False)
    impact_score = Column(Float, nullable=False, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    narrative = relationship("Narrative", back_populates="timeline")
    supporting_articles = relationship(
        "TurningPointArticle",
        back_populates="turning_point",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "impact_score >= 0.0 AND impact_score <= 1.0", name="impact_score_range"
        ),
        Index("idx_turning_points_narrative_time", "narrative_id", "timestamp"),
    )


class TurningPointArticle(Base):
    __tablename__ = "turning_point_articles"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    turning_point_id = Column(
        PGUUID(as_uuid=True), ForeignKey("turning_points.id"), nullable=False
    )
    article_id = Column(PGUUID(as_uuid=True), ForeignKey("articles.id"), nullable=False)
    relevance_score = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relationships
    turning_point = relationship("TurningPoint", back_populates="supporting_articles")
    article = relationship("Article", back_populates="turning_point_articles")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "turning_point_id", "article_id", name="unique_turning_point_article"
        ),
    )


class NarrativeTension(Base):
    __tablename__ = "narrative_tensions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    primary_narrative_id = Column(
        PGUUID(as_uuid=True), ForeignKey("narratives.id"), nullable=False
    )
    opposing_narrative_id = Column(
        PGUUID(as_uuid=True), ForeignKey("narratives.id"), nullable=False
    )
    tension_score = Column(Float, nullable=False, default=0.0)
    key_differences = Column(ARRAY(String), default=list)
    timeline_overlap = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    primary_narrative = relationship(
        "Narrative",
        foreign_keys=[primary_narrative_id],
        back_populates="tensions_as_primary",
    )
    opposing_narrative = relationship(
        "Narrative",
        foreign_keys=[opposing_narrative_id],
        back_populates="tensions_as_opposing",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "tension_score >= 0.0 AND tension_score <= 1.0", name="tension_score_range"
        ),
        CheckConstraint(
            "primary_narrative_id != opposing_narrative_id", name="different_narratives"
        ),
        UniqueConstraint(
            "primary_narrative_id",
            "opposing_narrative_id",
            name="unique_narrative_tension",
        ),
        Index("idx_tensions_score", "tension_score"),
    )


class SourceExcerpt(Base):
    __tablename__ = "source_excerpts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    narrative_id = Column(
        PGUUID(as_uuid=True), ForeignKey("narratives.id"), nullable=False
    )
    article_id = Column(PGUUID(as_uuid=True), ForeignKey("articles.id"), nullable=False)
    excerpt = Column(String(1000), nullable=False)
    relevance_score = Column(Float, nullable=False, default=0.0)
    start_position = Column(Integer, nullable=False, default=0)
    end_position = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relationships
    narrative = relationship("Narrative", back_populates="source_excerpts")
    article = relationship("Article", back_populates="excerpts")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "relevance_score >= 0.0 AND relevance_score <= 1.0",
            name="relevance_score_range",
        ),
        CheckConstraint("start_position >= 0", name="start_position_positive"),
        CheckConstraint("end_position >= start_position", name="end_after_start"),
        Index("idx_excerpts_narrative_relevance", "narrative_id", "relevance_score"),
    )


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=False)
    algorithm = Column(String(50), nullable=False)  # kmeans, dbscan, etc.

    # Cluster metrics
    centroid_vector = Column(VECTOR(384))
    coherence_score = Column(Float, nullable=False, default=0.0)
    size = Column(Integer, nullable=False, default=0)

    # Derived data
    topic_keywords = Column(ARRAY(String), default=list)
    representative_articles = Column(ARRAY(PGUUID), default=list)
    temporal_distribution = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    narratives = relationship(
        "Narrative", secondary=narrative_clusters, back_populates="clusters"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "coherence_score >= 0.0 AND coherence_score <= 1.0",
            name="coherence_score_range",
        ),
        CheckConstraint("size >= 0", name="size_positive"),
        Index("idx_clusters_algorithm_coherence", "algorithm", "coherence_score"),
    )


class NarrativeAnalytics(Base):
    __tablename__ = "narrative_analytics"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    narrative_id = Column(
        PGUUID(as_uuid=True), ForeignKey("narratives.id"), nullable=False
    )

    # Time series data
    time_window = Column(String(10), nullable=False)  # 1h, 6h, 24h, 7d, 30d
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Metrics
    article_count = Column(Integer, default=0)
    sentiment_avg = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    velocity = Column(Float, default=0.0)
    acceleration = Column(Float, default=0.0)
    volume = Column(Integer, default=0)

    # Trend analysis
    trend_direction = Column(String(10))  # up, down, stable
    growth_rate = Column(Float, default=0.0)
    anomaly_score = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relationships
    narrative = relationship("Narrative", back_populates="analytics")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "engagement_score >= 0.0 AND engagement_score <= 1.0",
            name="engagement_score_range",
        ),
        CheckConstraint("anomaly_score >= 0.0", name="anomaly_score_positive"),
        UniqueConstraint(
            "narrative_id", "time_window", "timestamp", name="unique_analytics_record"
        ),
        Index("idx_analytics_narrative_time", "narrative_id", "timestamp"),
        Index("idx_analytics_window_trend", "time_window", "trend_direction"),
    )


class RAIAnalysis(Base):
    __tablename__ = "rai_analyses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    narrative_id = Column(
        PGUUID(as_uuid=True), ForeignKey("narratives.id"), nullable=False
    )

    # RAI Metrics
    bias_score = Column(Float, default=0.0)  # 0 to 1
    fairness_metrics = Column(JSONB, default=dict)
    transparency_score = Column(Float, default=0.0)  # 0 to 1
    accountability_score = Column(Float, default=0.0)  # 0 to 1

    # Analysis results
    recommendations = Column(ARRAY(String), default=list)
    risk_factors = Column(ARRAY(String), default=list)
    mitigation_strategies = Column(ARRAY(String), default=list)

    # Source diversity analysis
    source_diversity_score = Column(Float, default=0.0)
    geographic_diversity = Column(JSONB, default=dict)
    temporal_bias_detected = Column(Boolean, default=False)

    # Quality assessment
    fact_check_score = Column(Float, default=0.0)
    citation_quality = Column(Float, default=0.0)
    methodology_transparency = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    narrative = relationship("Narrative", back_populates="rai_analyses")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "bias_score >= 0.0 AND bias_score <= 1.0", name="bias_score_range"
        ),
        CheckConstraint(
            "transparency_score >= 0.0 AND transparency_score <= 1.0",
            name="transparency_score_range",
        ),
        CheckConstraint(
            "accountability_score >= 0.0 AND accountability_score <= 1.0",
            name="accountability_score_range",
        ),
        CheckConstraint(
            "source_diversity_score >= 0.0 AND source_diversity_score <= 1.0",
            name="source_diversity_score_range",
        ),
        Index("idx_rai_narrative_created", "narrative_id", "created_at"),
    )


class PipelineTask(Base):
    __tablename__ = "pipeline_tasks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(String(50), nullable=False, index=True)
    status = Column(
        SQLEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING, index=True
    )
    priority = Column(Integer, default=5)  # 1-10, lower = higher priority

    # Task parameters and results
    parameters = Column(JSONB, default=dict)
    result = Column(JSONB)
    error_message = Column(Text)

    # Progress tracking
    progress = Column(Float, default=0.0)  # 0-100
    estimated_duration_seconds = Column(Integer)

    # Execution tracking
    started_at = Column(DateTime(timezone=True), index=True)
    completed_at = Column(DateTime(timezone=True))
    worker_id = Column(String(100))

    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("progress >= 0.0 AND progress <= 100.0", name="progress_range"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="priority_range"),
        CheckConstraint("retry_count >= 0", name="retry_count_positive"),
        Index("idx_tasks_status_priority", "status", "priority"),
        Index("idx_tasks_type_created", "type", "created_at"),
    )


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    query_text = Column(String(500))
    filters = Column(JSONB, default=dict)

    # Results and performance
    result_count = Column(Integer, default=0)
    query_time_ms = Column(Float, default=0.0)

    # User tracking (optional, can be null for anonymous searches)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(100))
    ip_address = Column(String(45))  # Support IPv6

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        Index("idx_search_queries_user_created", "user_id", "created_at"),
        Index("idx_search_queries_session", "session_id"),
    )


# ============================================================================
# DATABASE UTILITY FUNCTIONS
# ============================================================================


@listens_for(Article, "before_insert")
def calculate_article_metrics(mapper, connection, target):
    """Calculate derived metrics before inserting article."""
    if target.content:
        words = target.content.split()
        target.word_count = len(words)
        target.reading_time_minutes = max(1, target.word_count // 200)  # ~200 WPM


@listens_for(Narrative, "before_update")
def update_narrative_activity(mapper, connection, target):
    """Update last_activity when narrative is modified."""
    target.last_activity = datetime.now(timezone.utc)


def create_database_indexes(engine):
    """Create additional database indexes for performance."""
    from sqlalchemy import text

    with engine.connect() as conn:
        # Vector similarity indexes (requires pgvector extension)
        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_articles_embedding_cosine 
            ON articles USING ivfflat (embedding_vector vector_cosine_ops) 
            WITH (lists = 100);
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_narratives_embedding_cosine 
            ON narratives USING ivfflat (embedding_vector vector_cosine_ops) 
            WITH (lists = 100);
        """
            )
        )

        # Full-text search indexes
        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_articles_fulltext 
            ON articles USING gin(to_tsvector('english', title || ' ' || content));
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_narratives_fulltext 
            ON narratives USING gin(to_tsvector('english', title || ' ' || description));
        """
            )
        )

        # Composite performance indexes
        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_articles_performance 
            ON articles (source_id, published_at DESC, relevance_score DESC) 
            WHERE is_processed = true;
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_narratives_performance 
            ON narratives (topic, status, last_activity DESC, impact_score DESC);
        """
            )
        )

        conn.commit()


def get_database_stats(session: Session) -> Dict[str, Any]:
    """Get database statistics for monitoring."""
    stats = {}

    # Table counts
    stats["users"] = session.query(User).count()
    stats["articles"] = session.query(Article).count()
    stats["narratives"] = session.query(Narrative).count()
    stats["clusters"] = session.query(Cluster).count()
    stats["pipeline_tasks"] = session.query(PipelineTask).count()

    # Recent activity
    stats["articles_last_24h"] = (
        session.query(Article)
        .filter(Article.created_at >= datetime.now(timezone.utc) - timedelta(days=1))
        .count()
    )

    stats["narratives_active"] = (
        session.query(Narrative)
        .filter(Narrative.status == NarrativeStatus.ACTIVE)
        .count()
    )

    # Processing status
    stats["articles_processed"] = (
        session.query(Article).filter(Article.is_processed == True).count()
    )

    stats["tasks_pending"] = (
        session.query(PipelineTask)
        .filter(PipelineTask.status == TaskStatus.PENDING)
        .count()
    )

    return stats
