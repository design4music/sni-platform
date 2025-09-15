"""
Base classes and interfaces for data ingestion
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


@dataclass
class IngestionResult:
    """Result of an ingestion operation"""

    success: bool
    items_fetched: int
    items_processed: int
    items_failed: int
    errors: List[str]
    duration_seconds: float
    metadata: Dict[str, Any]


class RawArticle(BaseModel):
    """Raw article data before database storage"""

    title: str
    content: Optional[str] = None
    url: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    language: Optional[str] = None
    summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseIngestionSource(ABC):
    """Base class for all ingestion sources"""

    def __init__(self, source_config: Dict[str, Any]):
        self.config = source_config
        self.name = source_config.get("name", "unknown")
        self.url = source_config.get("url")
        self.language = source_config.get("language", "en")
        self.category = source_config.get("category", "general")
        self.priority = source_config.get("priority", 3)
        self.rate_limit = source_config.get("rate_limit", 60)  # per hour

    @abstractmethod
    async def fetch_articles(self) -> AsyncGenerator[RawArticle, None]:
        """Fetch articles from the source"""
        pass

    @abstractmethod
    async def validate_source(self) -> bool:
        """Validate that the source is accessible and properly configured"""
        pass

    def get_source_info(self) -> Dict[str, Any]:
        """Get source information for logging and monitoring"""
        return {
            "name": self.name,
            "url": self.url,
            "language": self.language,
            "category": self.category,
            "priority": self.priority,
            "rate_limit": self.rate_limit,
        }


class IngestionPipeline:
    """Main ingestion pipeline coordinator"""

    def __init__(self, sources: List[BaseIngestionSource]):
        self.sources = sources
        self.logger = structlog.get_logger(__name__)

    async def run_ingestion(self) -> IngestionResult:
        """Run the complete ingestion pipeline"""
        start_time = datetime.now(timezone.utc)

        total_fetched = 0
        total_processed = 0
        total_failed = 0
        all_errors = []

        self.logger.info("Starting ingestion pipeline", source_count=len(self.sources))

        # Process sources in parallel with rate limiting
        semaphore = asyncio.Semaphore(5)  # Limit concurrent sources

        async def process_source(source: BaseIngestionSource):
            async with semaphore:
                try:
                    return await self._process_single_source(source)
                except Exception as e:
                    self.logger.error(
                        "Failed to process source", source=source.name, error=str(e)
                    )
                    return IngestionResult(
                        success=False,
                        items_fetched=0,
                        items_processed=0,
                        items_failed=1,
                        errors=[f"Source {source.name}: {str(e)}"],
                        duration_seconds=0,
                        metadata={"source": source.name},
                    )

        # Execute all sources concurrently
        tasks = [process_source(source) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        for result in results:
            if isinstance(result, IngestionResult):
                total_fetched += result.items_fetched
                total_processed += result.items_processed
                total_failed += result.items_failed
                all_errors.extend(result.errors)

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        final_result = IngestionResult(
            success=total_failed < total_fetched * 0.5,  # Success if < 50% failures
            items_fetched=total_fetched,
            items_processed=total_processed,
            items_failed=total_failed,
            errors=all_errors,
            duration_seconds=duration,
            metadata={
                "sources_processed": len(self.sources),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
            },
        )

        self.logger.info("Ingestion pipeline completed", **final_result.__dict__)

        return final_result

    async def _process_single_source(
        self, source: BaseIngestionSource
    ) -> IngestionResult:
        """Process a single ingestion source"""
        start_time = datetime.now(timezone.utc)

        source_logger = self.logger.bind(source=source.name)
        source_logger.info("Starting source processing")

        fetched = 0
        processed = 0
        failed = 0
        errors = []

        try:
            # Validate source first
            if not await source.validate_source():
                raise Exception(f"Source validation failed for {source.name}")

            # Fetch and process articles
            async for article in source.fetch_articles():
                fetched += 1
                try:
                    # Process the article (deduplication, validation, etc.)
                    if await self._process_article(article, source):
                        processed += 1
                    else:
                        failed += 1
                        errors.append(
                            f"Failed to process article: {article.title[:50]}..."
                        )

                except Exception as e:
                    failed += 1
                    errors.append(f"Error processing article {article.url}: {str(e)}")
                    source_logger.error(
                        "Article processing error",
                        article_url=article.url,
                        error=str(e),
                    )

        except Exception as e:
            failed += 1
            errors.append(f"Source processing error: {str(e)}")
            source_logger.error("Source processing error", error=str(e))

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        result = IngestionResult(
            success=failed < fetched * 0.3,  # Success if < 30% failures
            items_fetched=fetched,
            items_processed=processed,
            items_failed=failed,
            errors=errors,
            duration_seconds=duration,
            metadata={"source": source.name},
        )

        source_logger.info("Source processing completed", **result.__dict__)

        return result

    async def _process_article(
        self, article: RawArticle, source: BaseIngestionSource
    ) -> bool:
        """Process a single article (validate, deduplicate, store)"""
        try:
            # Basic validation
            if not self._validate_article(article):
                return False

            # Check for duplicates
            if await self._is_duplicate(article):
                self.logger.debug("Duplicate article skipped", url=article.url)
                return False

            # Store in database
            return await self._store_article(article, source)

        except Exception as e:
            self.logger.error(
                "Article processing failed", article_url=article.url, error=str(e)
            )
            return False

    def _validate_article(self, article: RawArticle) -> bool:
        """Validate article data quality"""
        from config.settings import settings

        # Check required fields
        if not article.title or not article.url:
            return False

        # Check content length
        if article.content:
            content_length = len(article.content)
            if (
                content_length < settings.min_article_length
                or content_length > settings.max_article_length
            ):
                return False

        # Check URL format
        if not article.url.startswith(("http://", "https://")):
            return False

        return True

    async def _is_duplicate(self, article: RawArticle) -> bool:
        """Check if article is a duplicate"""
        # This would typically involve database lookup and similarity comparison
        # For now, just check URL
        from core.database import Article, SessionLocal

        with SessionLocal() as db:
            existing = db.query(Article).filter(Article.url == article.url).first()
            return existing is not None

    async def _store_article(
        self, article: RawArticle, source: BaseIngestionSource
    ) -> bool:
        """Store article in database"""
        from core.database import Article, NewsSource, SessionLocal

        try:
            with SessionLocal() as db:
                # Get or create source
                db_source = (
                    db.query(NewsSource).filter(NewsSource.name == source.name).first()
                )

                if not db_source:
                    db_source = NewsSource(
                        name=source.name,
                        url=source.url,
                        source_type="rss",  # Default, should be configurable
                        language=source.language,
                        category=source.category,
                        priority=source.priority,
                    )
                    db.add(db_source)
                    db.flush()

                # Create article
                db_article = Article(
                    source_id=db_source.id,
                    title=article.title,
                    content=article.content,
                    summary=article.summary,
                    url=article.url,
                    author=article.author,
                    language=article.language or source.language,
                    published_at=article.published_at,
                    metadata=article.metadata,
                )

                db.add(db_article)
                db.commit()

                return True

        except Exception as e:
            self.logger.error(
                "Database storage failed", article_url=article.url, error=str(e)
            )
            return False
