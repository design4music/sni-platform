"""
API-based News Ingestion Implementation
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp
import structlog
from dateutil import parser as date_parser

from .base import BaseIngestionSource, RawArticle

logger = structlog.get_logger(__name__)


class NewsAPIIngestionSource(BaseIngestionSource):
    """NewsAPI.org ingestion source"""

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.api_key = source_config.get("api_key")
        self.endpoint = source_config.get(
            "endpoint", "https://newsapi.org/v2/top-headlines"
        )
        self.country = source_config.get("country")
        self.category = source_config.get("category", "general")
        self.page_size = min(
            source_config.get("page_size", 100), 100
        )  # NewsAPI max is 100
        self.max_pages = source_config.get("max_pages", 5)

        if not self.api_key:
            raise ValueError("NewsAPI requires api_key in configuration")

    async def validate_source(self) -> bool:
        """Validate NewsAPI accessibility and credentials"""
        try:
            test_params = {
                "apiKey": self.api_key,
                "pageSize": 1,
                "language": self.language,
            }

            if self.country:
                test_params["country"] = self.country

            url = f"{self.endpoint}?{urlencode(test_params)}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(
                            "NewsAPI validation failed",
                            source=self.name,
                            status=response.status,
                        )
                        return False

                    data = await response.json()

                    if data.get("status") != "ok":
                        logger.error(
                            "NewsAPI error response",
                            source=self.name,
                            error=data.get("message", "Unknown error"),
                        )
                        return False

                    return True

        except Exception as e:
            logger.error("NewsAPI validation error", source=self.name, error=str(e))
            return False

    async def fetch_articles(self) -> AsyncGenerator[RawArticle, None]:
        """Fetch articles from NewsAPI"""
        try:
            page = 1
            total_processed = 0

            async with aiohttp.ClientSession() as session:
                while page <= self.max_pages:
                    params = {
                        "apiKey": self.api_key,
                        "pageSize": self.page_size,
                        "page": page,
                        "language": self.language,
                        "sortBy": "publishedAt",
                    }

                    if self.country:
                        params["country"] = self.country

                    if self.category != "general":
                        params["category"] = self.category

                    url = f"{self.endpoint}?{urlencode(params)}"

                    async with session.get(url) as response:
                        if response.status != 200:
                            logger.error(
                                "NewsAPI request failed",
                                source=self.name,
                                page=page,
                                status=response.status,
                            )
                            break

                        data = await response.json()

                        if data.get("status") != "ok":
                            logger.error(
                                "NewsAPI error",
                                source=self.name,
                                error=data.get("message", "Unknown error"),
                            )
                            break

                        articles = data.get("articles", [])
                        if not articles:
                            logger.info(
                                "No more articles found", source=self.name, page=page
                            )
                            break

                        for article_data in articles:
                            try:
                                article = await self._parse_newsapi_article(
                                    article_data
                                )
                                if article:
                                    yield article
                                    total_processed += 1

                            except Exception as e:
                                logger.error(
                                    "Failed to parse NewsAPI article",
                                    source=self.name,
                                    error=str(e),
                                )
                                continue

                        page += 1

                        # Rate limiting
                        await asyncio.sleep(1)

            logger.info(
                "NewsAPI processing completed",
                source=self.name,
                total_processed=total_processed,
            )

        except Exception as e:
            logger.error("NewsAPI fetch error", source=self.name, error=str(e))

    async def _parse_newsapi_article(
        self, article_data: Dict[str, Any]
    ) -> Optional[RawArticle]:
        """Parse NewsAPI article data"""
        try:
            title = article_data.get("title", "").strip()
            if not title or title.lower() == "[removed]":
                return None

            url = article_data.get("url", "").strip()
            if not url:
                return None

            # Extract content and description
            content = article_data.get("content", "").strip()
            description = article_data.get("description", "").strip()

            # NewsAPI often truncates content, use description as fallback
            if not content or content.endswith("..."):
                content = description

            # Extract author
            author = article_data.get("author", "").strip()
            if author and author.lower() == "null":
                author = None

            # Extract published date
            published_at = None
            published_str = article_data.get("publishedAt")
            if published_str:
                try:
                    published_at = date_parser.parse(published_str)
                    if published_at.tzinfo is None:
                        published_at = published_at.replace(tzinfo=timezone.utc)
                except ValueError:
                    published_at = None

            # Extract source information
            source_info = article_data.get("source", {})
            source_name = source_info.get("name", "")

            # Create metadata
            metadata = {
                "source_type": "newsapi",
                "source_name": self.name,
                "original_source": source_name,
                "newsapi_source_id": source_info.get("id"),
                "url_to_image": article_data.get("urlToImage"),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

            return RawArticle(
                title=title,
                content=content,
                url=url,
                author=author,
                published_at=published_at,
                language=self.language,
                summary=description,
                metadata=metadata,
            )

        except Exception as e:
            logger.error("NewsAPI article parsing error", error=str(e))
            return None


class GuardianAPIIngestionSource(BaseIngestionSource):
    """The Guardian API ingestion source"""

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.api_key = source_config.get("api_key")
        self.endpoint = source_config.get(
            "endpoint", "https://content.guardianapis.com/search"
        )
        self.section = source_config.get("section")
        self.page_size = min(
            source_config.get("page_size", 50), 50
        )  # Guardian max is 50
        self.max_pages = source_config.get("max_pages", 10)

        if not self.api_key:
            raise ValueError("Guardian API requires api_key in configuration")

    async def validate_source(self) -> bool:
        """Validate Guardian API accessibility"""
        try:
            params = {
                "api-key": self.api_key,
                "page-size": 1,
                "show-fields": "headline",
            }

            url = f"{self.endpoint}?{urlencode(params)}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return False

                    data = await response.json()
                    return data.get("response", {}).get("status") == "ok"

        except Exception as e:
            logger.error(
                "Guardian API validation error", source=self.name, error=str(e)
            )
            return False

    async def fetch_articles(self) -> AsyncGenerator[RawArticle, None]:
        """Fetch articles from Guardian API"""
        try:
            page = 1
            total_processed = 0

            async with aiohttp.ClientSession() as session:
                while page <= self.max_pages:
                    params = {
                        "api-key": self.api_key,
                        "page-size": self.page_size,
                        "page": page,
                        "order-by": "newest",
                        "show-fields": "headline,byline,body,thumbnail,publication",
                        "show-tags": "contributor",
                        "from-date": (datetime.now() - timedelta(days=7)).strftime(
                            "%Y-%m-%d"
                        ),
                    }

                    if self.section:
                        params["section"] = self.section

                    url = f"{self.endpoint}?{urlencode(params)}"

                    async with session.get(url) as response:
                        if response.status != 200:
                            logger.error(
                                "Guardian API request failed",
                                source=self.name,
                                page=page,
                                status=response.status,
                            )
                            break

                        data = await response.json()
                        response_data = data.get("response", {})

                        if response_data.get("status") != "ok":
                            logger.error(
                                "Guardian API error",
                                source=self.name,
                                error="Invalid response status",
                            )
                            break

                        results = response_data.get("results", [])
                        if not results:
                            break

                        for article_data in results:
                            try:
                                article = await self._parse_guardian_article(
                                    article_data
                                )
                                if article:
                                    yield article
                                    total_processed += 1

                            except Exception as e:
                                logger.error(
                                    "Failed to parse Guardian article",
                                    source=self.name,
                                    error=str(e),
                                )
                                continue

                        page += 1
                        await asyncio.sleep(0.5)  # Rate limiting

            logger.info(
                "Guardian API processing completed",
                source=self.name,
                total_processed=total_processed,
            )

        except Exception as e:
            logger.error("Guardian API fetch error", source=self.name, error=str(e))

    async def _parse_guardian_article(
        self, article_data: Dict[str, Any]
    ) -> Optional[RawArticle]:
        """Parse Guardian API article data"""
        try:
            # Extract basic fields
            title = article_data.get("webTitle", "").strip()
            if not title:
                return None

            url = article_data.get("webUrl", "").strip()
            if not url:
                return None

            # Extract fields from fields object
            fields = article_data.get("fields", {})
            content = fields.get("body", "").strip()
            byline = fields.get("byline", "").strip()

            # Extract author from tags
            author = byline
            tags = article_data.get("tags", [])
            if not author and tags:
                contributor_tags = [
                    tag for tag in tags if tag.get("type") == "contributor"
                ]
                if contributor_tags:
                    author = contributor_tags[0].get("webTitle", "")

            # Extract published date
            published_at = None
            published_str = article_data.get("webPublicationDate")
            if published_str:
                try:
                    published_at = date_parser.parse(published_str)
                except ValueError:
                    published_at = None

            # Create metadata
            metadata = {
                "source_type": "guardian_api",
                "source_name": self.name,
                "guardian_id": article_data.get("id"),
                "section_name": article_data.get("sectionName"),
                "section_id": article_data.get("sectionId"),
                "pillar_name": article_data.get("pillarName"),
                "thumbnail": fields.get("thumbnail"),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

            return RawArticle(
                title=title,
                content=content,
                url=url,
                author=author,
                published_at=published_at,
                language="en",  # Guardian is English
                summary=None,  # Guardian doesn't provide summaries
                metadata=metadata,
            )

        except Exception as e:
            logger.error("Guardian article parsing error", error=str(e))
            return None


class GenericAPIIngestionSource(BaseIngestionSource):
    """Generic API ingestion source for custom endpoints"""

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.endpoint = source_config.get("endpoint")
        self.headers = source_config.get("headers", {})
        self.params = source_config.get("params", {})
        self.auth = source_config.get("auth")
        self.field_mapping = source_config.get("field_mapping", {})
        self.pagination_config = source_config.get("pagination", {})

        if not self.endpoint:
            raise ValueError("Generic API source requires endpoint in configuration")

    async def validate_source(self) -> bool:
        """Validate generic API endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(*self.auth) if self.auth else None

                async with session.get(
                    self.endpoint, headers=self.headers, params=self.params, auth=auth
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error("Generic API validation error", source=self.name, error=str(e))
            return False

    async def fetch_articles(self) -> AsyncGenerator[RawArticle, None]:
        """Fetch articles from generic API endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(*self.auth) if self.auth else None

                async with session.get(
                    self.endpoint, headers=self.headers, params=self.params, auth=auth
                ) as response:
                    if response.status != 200:
                        logger.error(
                            "Generic API request failed",
                            source=self.name,
                            status=response.status,
                        )
                        return

                    data = await response.json()
                    articles_data = self._extract_articles_from_response(data)

                    for article_data in articles_data:
                        try:
                            article = await self._parse_generic_article(article_data)
                            if article:
                                yield article

                        except Exception as e:
                            logger.error(
                                "Failed to parse generic API article",
                                source=self.name,
                                error=str(e),
                            )
                            continue

        except Exception as e:
            logger.error("Generic API fetch error", source=self.name, error=str(e))

    def _extract_articles_from_response(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract articles array from API response"""
        # Default behavior - look for common array keys
        for key in ["articles", "items", "data", "results", "posts"]:
            if key in data and isinstance(data[key], list):
                return data[key]

        # If data itself is a list
        if isinstance(data, list):
            return data

        return []

    async def _parse_generic_article(
        self, article_data: Dict[str, Any]
    ) -> Optional[RawArticle]:
        """Parse generic API article using field mapping"""
        try:
            # Default field mapping
            default_mapping = {
                "title": ["title", "headline", "subject"],
                "content": ["content", "body", "text", "description"],
                "url": ["url", "link", "permalink"],
                "author": ["author", "byline", "writer"],
                "published_at": ["published_at", "date", "pubDate", "created_at"],
                "summary": ["summary", "excerpt", "abstract"],
            }

            # Merge with custom mapping
            field_mapping = {**default_mapping, **self.field_mapping}

            # Extract fields
            extracted = {}
            for target_field, source_fields in field_mapping.items():
                for source_field in source_fields:
                    if source_field in article_data:
                        extracted[target_field] = article_data[source_field]
                        break

            # Validate required fields
            if not extracted.get("title") or not extracted.get("url"):
                return None

            # Parse published date
            published_at = None
            if extracted.get("published_at"):
                try:
                    published_at = date_parser.parse(str(extracted["published_at"]))
                    if published_at.tzinfo is None:
                        published_at = published_at.replace(tzinfo=timezone.utc)
                except ValueError:
                    published_at = None

            # Create metadata
            metadata = {
                "source_type": "generic_api",
                "source_name": self.name,
                "original_data": article_data,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

            return RawArticle(
                title=str(extracted["title"]).strip(),
                content=str(extracted.get("content", "")).strip() or None,
                url=str(extracted["url"]).strip(),
                author=str(extracted.get("author", "")).strip() or None,
                published_at=published_at,
                language=self.language,
                summary=str(extracted.get("summary", "")).strip() or None,
                metadata=metadata,
            )

        except Exception as e:
            logger.error("Generic API article parsing error", error=str(e))
            return None
