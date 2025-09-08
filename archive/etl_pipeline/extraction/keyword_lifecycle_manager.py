#!/usr/bin/env python3
"""
Keyword Lifecycle Manager
Strategic Narrative Intelligence ETL Pipeline

Manages dynamic evolution of keyword database with aging and lifecycle tracking.
Handles daily ingestion, frequency updates, trend detection, and cleanup.
"""

import asyncio
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError

from ..core.database import get_db_session
from .dynamic_keyword_extractor import (ArticleKeywordResult,
                                        DynamicKeywordExtractor)

logger = structlog.get_logger(__name__)


@dataclass
class KeywordStats:
    """Statistics for a keyword"""

    keyword_id: str
    keyword_text: str
    total_frequency: int
    recent_frequency: int
    strategic_score: float
    trending_score: float
    lifecycle_stage: str


@dataclass
class TrendingKeyword:
    """Keyword showing trending behavior"""

    keyword: str
    spike_factor: float
    daily_frequency: int
    baseline_frequency: float
    trend_date: date


class KeywordLifecycleManager:
    """
    Manages the complete lifecycle of dynamically discovered keywords

    Daily Operations:
    1. Process new articles -> extract keywords -> update frequencies
    2. Calculate trending scores and detect spikes
    3. Update keyword lifecycle stages (active -> warm -> cold -> archived)
    4. Clean up old/irrelevant keywords
    5. Update co-occurrence patterns for clustering
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = structlog.get_logger(__name__)

        # Lifecycle thresholds
        self.active_days = self.config.get("active_days", 30)
        self.warm_days = self.config.get("warm_days", 365)
        self.purge_threshold = self.config.get(
            "purge_threshold", 5
        )  # Min mentions to keep
        self.purge_days = self.config.get(
            "purge_days", 180
        )  # Days before purge consideration

        # Trending detection
        self.trending_threshold = self.config.get("trending_threshold", 1.5)
        self.baseline_window = self.config.get(
            "baseline_window", 7
        )  # Days for baseline calc

        # Strategic scoring
        self.high_strategic_threshold = self.config.get("high_strategic_threshold", 0.7)

        # Initialize keyword extractor
        self.extractor = DynamicKeywordExtractor(config)

        self.logger.info(
            "Keyword lifecycle manager initialized",
            active_days=self.active_days,
            trending_threshold=self.trending_threshold,
        )

    async def process_new_articles(
        self, article_batch: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process batch of new articles through keyword extraction and lifecycle update

        Args:
            article_batch: List of dicts with keys: id, title, content, summary, published_at

        Returns:
            Processing statistics
        """
        start_time = datetime.utcnow()

        try:
            stats = {
                "articles_processed": 0,
                "keywords_extracted": 0,
                "new_keywords_created": 0,
                "keywords_updated": 0,
                "trending_keywords_detected": 0,
            }

            self.logger.info("Processing article batch", batch_size=len(article_batch))

            for article in article_batch:
                try:
                    # Extract keywords from article
                    result = self.extractor.extract_keywords(
                        article_id=str(article["id"]),
                        title=article["title"],
                        content=article.get("content", ""),
                        summary=article.get("summary"),
                    )

                    # Process extracted keywords
                    await self._process_article_keywords(article["id"], result)

                    stats["articles_processed"] += 1
                    stats["keywords_extracted"] += len(result.keywords)

                except Exception as e:
                    self.logger.error(
                        "Failed to process article",
                        article_id=article.get("id"),
                        error=str(e),
                    )
                    continue

            # Update daily trends and lifecycle stages
            trend_stats = await self._update_daily_trends()
            stats.update(trend_stats)

            # Clean up old keywords
            cleanup_stats = await self._cleanup_old_keywords()
            stats.update(cleanup_stats)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            self.logger.info(
                "Article batch processed", processing_time=processing_time, **stats
            )

            return {**stats, "processing_time": processing_time, "status": "success"}

        except Exception as e:
            self.logger.error("Batch processing failed", error=str(e))
            return {"status": "error", "error": str(e)}

    async def _process_article_keywords(
        self, article_id: uuid.UUID, result: ArticleKeywordResult
    ):
        """Process extracted keywords for a single article"""

        try:
            with get_db_session() as session:
                for rank, keyword in enumerate(result.keywords, 1):
                    # Get or create keyword record
                    keyword_id = await self._get_or_create_keyword(
                        session,
                        keyword.text,
                        keyword.keyword_type,
                        keyword.entity_label,
                    )

                    # Update keyword frequency and metadata
                    await self._update_keyword_frequency(session, keyword_id)

                    # Create article-keyword relationship
                    await self._create_article_keyword_link(
                        session, article_id, keyword_id, keyword, rank
                    )

                session.commit()

        except SQLAlchemyError as e:
            self.logger.error(
                "Failed to process article keywords",
                article_id=str(article_id),
                error=str(e),
            )
            raise

    async def _get_or_create_keyword(
        self, session, keyword_text: str, keyword_type: str, entity_label: Optional[str]
    ) -> str:
        """Get existing keyword or create new one"""

        # Try to find existing keyword
        result = session.execute(
            text("SELECT id FROM keywords WHERE keyword = :keyword"),
            {"keyword": keyword_text},
        )
        existing = result.fetchone()

        if existing:
            return existing[0]

        # Create new keyword
        keyword_id = str(uuid.uuid4())

        session.execute(
            text(
                """
            INSERT INTO keywords (
                id, keyword, keyword_type, entity_label,
                strategic_score, base_frequency, recent_frequency,
                first_seen, last_seen
            ) VALUES (
                :id, :keyword, :keyword_type, :entity_label,
                0.0, 0, 0, NOW(), NOW()
            )
        """
            ),
            {
                "id": keyword_id,
                "keyword": keyword_text,
                "keyword_type": keyword_type,
                "entity_label": entity_label,
            },
        )

        self.logger.debug("Created new keyword", keyword=keyword_text, id=keyword_id)

        return keyword_id

    async def _update_keyword_frequency(self, session, keyword_id: str):
        """Update keyword frequency counters"""

        # Update frequencies and last_seen
        session.execute(
            text(
                """
            UPDATE keywords 
            SET base_frequency = base_frequency + 1,
                recent_frequency = recent_frequency + 1,
                last_seen = NOW(),
                updated_at = NOW()
            WHERE id = :keyword_id
        """
            ),
            {"keyword_id": keyword_id},
        )

    async def _create_article_keyword_link(
        self, session, article_id: uuid.UUID, keyword_id: str, keyword, rank: int
    ):
        """Create article-keyword relationship"""

        # Note: This is a simplified version - you could add logic to detect
        # if keyword appears in title/summary based on article text analysis

        session.execute(
            text(
                """
            INSERT INTO article_keywords (
                article_id, keyword_id, extraction_method, extraction_score,
                strategic_score, keyword_rank, appears_in_title, appears_in_summary,
                position_importance
            ) VALUES (
                :article_id, :keyword_id, :method, :extraction_score,
                :strategic_score, :rank, :in_title, :in_summary, :position_importance
            ) ON CONFLICT (article_id, keyword_id) DO NOTHING
        """
            ),
            {
                "article_id": str(article_id),
                "keyword_id": keyword_id,
                "method": keyword.extraction_method,
                "extraction_score": float(keyword.extraction_score),
                "strategic_score": float(keyword.strategic_score),
                "rank": rank,
                "in_title": False,  # TODO: Implement title detection
                "in_summary": False,  # TODO: Implement summary detection
                "position_importance": 0.0,  # TODO: Implement position scoring
            },
        )

    async def _update_daily_trends(self) -> Dict[str, Any]:
        """Update daily trend tracking and detect spikes"""

        try:
            with get_db_session() as session:
                today = date.today()

                # Get today's keyword frequencies
                result = session.execute(
                    text(
                        """
                    SELECT 
                        ak.keyword_id,
                        k.keyword,
                        COUNT(*) as daily_count
                    FROM article_keywords ak
                    JOIN articles a ON ak.article_id = a.id  
                    JOIN keywords k ON ak.keyword_id = k.id
                    WHERE DATE(a.published_at) = :today
                    GROUP BY ak.keyword_id, k.keyword
                """
                    ),
                    {"today": today},
                )

                trending_count = 0

                for row in result.fetchall():
                    keyword_id, keyword_text, daily_count = row

                    # Calculate baseline (7-day average excluding today)
                    baseline = await self._calculate_baseline_frequency(
                        session, keyword_id, today
                    )

                    # Calculate spike factor
                    spike_factor = daily_count / baseline if baseline > 0 else 2.0

                    # Insert/update trend record
                    session.execute(
                        text(
                            """
                        INSERT INTO keyword_trends (
                            keyword_id, date, daily_frequency, spike_factor, baseline_frequency
                        ) VALUES (
                            :keyword_id, :date, :daily_count, :spike_factor, :baseline
                        ) ON CONFLICT (keyword_id, date) 
                        DO UPDATE SET 
                            daily_frequency = EXCLUDED.daily_frequency,
                            spike_factor = EXCLUDED.spike_factor,
                            baseline_frequency = EXCLUDED.baseline_frequency
                    """
                        ),
                        {
                            "keyword_id": keyword_id,
                            "date": today,
                            "daily_count": daily_count,
                            "spike_factor": spike_factor,
                            "baseline": baseline,
                        },
                    )

                    # Update keyword trending score if spiking
                    if spike_factor >= self.trending_threshold:
                        session.execute(
                            text(
                                """
                            UPDATE keywords 
                            SET trending_score = :spike_factor,
                                peak_frequency = GREATEST(peak_frequency, :daily_count),
                                peak_date = CASE 
                                    WHEN :daily_count > peak_frequency THEN :date 
                                    ELSE peak_date 
                                END
                            WHERE id = :keyword_id
                        """
                            ),
                            {
                                "keyword_id": keyword_id,
                                "spike_factor": spike_factor,
                                "daily_count": daily_count,
                                "date": today,
                            },
                        )

                        trending_count += 1

                        self.logger.info(
                            "Trending keyword detected",
                            keyword=keyword_text,
                            spike_factor=spike_factor,
                            daily_count=daily_count,
                        )

                session.commit()

                return {"trending_keywords_detected": trending_count}

        except SQLAlchemyError as e:
            self.logger.error("Failed to update daily trends", error=str(e))
            return {"trending_keywords_detected": 0}

    async def _calculate_baseline_frequency(
        self, session, keyword_id: str, current_date: date
    ) -> float:
        """Calculate baseline frequency for trend detection"""

        start_date = current_date - timedelta(days=self.baseline_window + 1)
        end_date = current_date - timedelta(days=1)  # Exclude current day

        result = session.execute(
            text(
                """
            SELECT AVG(daily_frequency)
            FROM keyword_trends 
            WHERE keyword_id = :keyword_id
              AND date BETWEEN :start_date AND :end_date
        """
            ),
            {"keyword_id": keyword_id, "start_date": start_date, "end_date": end_date},
        )

        baseline = result.fetchone()[0]
        return float(baseline) if baseline is not None else 0.0

    async def _cleanup_old_keywords(self) -> Dict[str, Any]:
        """Clean up old, low-frequency keywords"""

        try:
            with get_db_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=self.purge_days)

                # Find candidates for deletion
                result = session.execute(
                    text(
                        """
                    SELECT id, keyword FROM keywords
                    WHERE last_seen < :cutoff_date
                      AND base_frequency < :min_frequency
                      AND strategic_score < :min_strategic
                      AND lifecycle_stage IN ('cold', 'archived')
                """
                    ),
                    {
                        "cutoff_date": cutoff_date,
                        "min_frequency": self.purge_threshold,
                        "min_strategic": 0.3,  # Keep strategic keywords longer
                    },
                )

                candidates = result.fetchall()

                if candidates:
                    keyword_ids = [row[0] for row in candidates]

                    # Delete article_keywords first (foreign key constraint)
                    session.execute(
                        text(
                            """
                        DELETE FROM article_keywords 
                        WHERE keyword_id = ANY(:keyword_ids)
                    """
                        ),
                        {"keyword_ids": keyword_ids},
                    )

                    # Delete trend data
                    session.execute(
                        text(
                            """
                        DELETE FROM keyword_trends 
                        WHERE keyword_id = ANY(:keyword_ids)
                    """
                        ),
                        {"keyword_ids": keyword_ids},
                    )

                    # Delete keywords
                    session.execute(
                        text(
                            """
                        DELETE FROM keywords 
                        WHERE id = ANY(:keyword_ids)
                    """
                        ),
                        {"keyword_ids": keyword_ids},
                    )

                    session.commit()

                    self.logger.info(
                        "Cleaned up old keywords", deleted_count=len(candidates)
                    )

                    return {"keywords_purged": len(candidates)}

                return {"keywords_purged": 0}

        except SQLAlchemyError as e:
            self.logger.error("Failed to cleanup keywords", error=str(e))
            return {"keywords_purged": 0}

    async def get_trending_keywords(
        self, days: int = 7, limit: int = 50
    ) -> List[TrendingKeyword]:
        """Get currently trending keywords"""

        try:
            with get_db_session() as session:
                start_date = date.today() - timedelta(days=days)

                result = session.execute(
                    text(
                        """
                    SELECT 
                        k.keyword,
                        kt.spike_factor,
                        kt.daily_frequency,
                        kt.baseline_frequency,
                        kt.date
                    FROM keywords k
                    JOIN keyword_trends kt ON k.id = kt.keyword_id
                    WHERE kt.date >= :start_date
                      AND kt.spike_factor >= :threshold
                    ORDER BY kt.spike_factor DESC, kt.daily_frequency DESC
                    LIMIT :limit
                """
                    ),
                    {
                        "start_date": start_date,
                        "threshold": self.trending_threshold,
                        "limit": limit,
                    },
                )

                return [
                    TrendingKeyword(
                        keyword=row[0],
                        spike_factor=row[1],
                        daily_frequency=row[2],
                        baseline_frequency=row[3],
                        trend_date=row[4],
                    )
                    for row in result.fetchall()
                ]

        except SQLAlchemyError as e:
            self.logger.error("Failed to get trending keywords", error=str(e))
            return []

    async def get_strategic_keywords(
        self, min_score: float = 0.5, limit: int = 100
    ) -> List[KeywordStats]:
        """Get most strategic keywords"""

        try:
            with get_db_session() as session:
                result = session.execute(
                    text(
                        """
                    SELECT 
                        id, keyword, base_frequency, recent_frequency,
                        strategic_score, trending_score, lifecycle_stage
                    FROM keywords
                    WHERE strategic_score >= :min_score
                      AND lifecycle_stage IN ('active', 'warm')
                    ORDER BY strategic_score DESC, base_frequency DESC
                    LIMIT :limit
                """
                    ),
                    {"min_score": min_score, "limit": limit},
                )

                return [
                    KeywordStats(
                        keyword_id=row[0],
                        keyword_text=row[1],
                        total_frequency=row[2],
                        recent_frequency=row[3],
                        strategic_score=row[4],
                        trending_score=row[5],
                        lifecycle_stage=row[6],
                    )
                    for row in result.fetchall()
                ]

        except SQLAlchemyError as e:
            self.logger.error("Failed to get strategic keywords", error=str(e))
            return []


# Convenience functions
async def process_daily_articles(
    articles: List[Dict[str, Any]], config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process daily article batch through keyword lifecycle"""
    manager = KeywordLifecycleManager(config)
    return await manager.process_new_articles(articles)


if __name__ == "__main__":
    # Test the lifecycle manager
    async def test_lifecycle():
        # Mock article data
        test_articles = [
            {
                "id": uuid.uuid4(),
                "title": "Putin and Xi Jinping Discuss Trade at SCO Summit",
                "content": "Russian President Vladimir Putin met Chinese President Xi Jinping...",
                "summary": "Leaders discuss bilateral cooperation",
                "published_at": datetime.utcnow(),
            }
        ]

        result = await process_daily_articles(test_articles)
        print("Lifecycle test result:", result)

    # Run test
    asyncio.run(test_lifecycle())
