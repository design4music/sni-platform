"""
Ingestion module for Strategic Narrative Intelligence ETL Pipeline

This module provides feed ingestion capabilities from multiple sources
including RSS feeds, REST APIs, and web scrapers.
"""

from .feed_ingestor import ArticleData, FeedIngestor, IngestionResult

__all__ = ["FeedIngestor", "IngestionResult", "ArticleData"]
