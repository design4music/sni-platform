"""
Sitemap Parsing Utilities
Strategic Narrative Intelligence ETL Pipeline

Robust XML sitemap parsing with support for:
- Sitemap index files
- Gzipped sitemaps
- News sitemap namespace
- Mixed namespaces
- Timezone-aware processing
"""

import gzip
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Generator, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
import structlog

logger = structlog.get_logger(__name__)

# Query parameters to drop for URL normalization
DROP_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "_ga",
    "_gl",
    "ref",
    "source",
}


def _now_utc() -> datetime:
    """Get current time in UTC with timezone info"""
    return datetime.now(timezone.utc)


def _parse_dt(s: str) -> datetime:
    """
    Parse ISO8601 datetime string to timezone-aware UTC datetime

    Handles formats:
    - 2025-08-28T17:12:52.031Z
    - 2025-08-28T17:12:52+00:00
    - 2025-08-28
    """
    if not s:
        return _now_utc()

    s = s.strip()

    try:
        # Handle Z suffix (Zulu time)
        if s.endswith("Z"):
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        elif "T" in s:
            # Full timestamp with timezone
            dt = datetime.fromisoformat(s)
        else:
            # Date only - assume UTC
            dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)

        # Convert to UTC if not already
        return dt.astimezone(timezone.utc)

    except ValueError as e:
        logger.debug(f"Failed to parse datetime '{s}': {e}")
        return _now_utc()


def _http_get_text(url: str, timeout: int = 30) -> str:
    """
    Fetch URL content with gzip support and proper encoding handling
    """
    headers = {
        "User-Agent": "SNI Unified Ingestion Bot/1.0",
        "Accept": "application/xml, text/xml, */*",
        "Accept-Encoding": "gzip, deflate",
    }

    response = requests.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()

    # Handle gzipped content
    content_encoding = response.headers.get("Content-Encoding", "").lower()
    if url.endswith(".gz") or "gzip" in content_encoding:
        try:
            return gzip.decompress(response.content).decode("utf-8", errors="replace")
        except Exception as e:
            logger.warning(f"Failed to decompress gzipped content from {url}: {e}")
            # Fall back to raw content
            return response.text

    return response.text


def _iter_url_elems(root: ET.Element) -> Generator[Tuple[str, str], None, None]:
    """
    Namespace-agnostic iteration over URL elements in sitemap

    Yields: (url, lastmod_text)
    """
    # Find all url elements regardless of namespace
    for url_elem in root.findall(".//{*}url"):
        # Find loc element (required)
        loc_elem = url_elem.find("{*}loc")
        if loc_elem is None or not loc_elem.text:
            continue

        url = loc_elem.text.strip()

        # Find lastmod (optional)
        lastmod_elem = url_elem.find("{*}lastmod")
        lastmod_text = ""

        if lastmod_elem is not None and lastmod_elem.text:
            lastmod_text = lastmod_elem.text.strip()
        else:
            # Fallback to news:publication_date for news sitemaps
            news_date_elem = url_elem.find("{*}publication_date")
            if news_date_elem is not None and news_date_elem.text:
                lastmod_text = news_date_elem.text.strip()

        yield url, lastmod_text


def _iter_sitemap_entries(root: ET.Element) -> Generator[Tuple[str, str], None, None]:
    """
    Namespace-agnostic iteration over sitemap entries in sitemap index

    Yields: (sitemap_url, lastmod_text)
    """
    for sm_elem in root.findall(".//{*}sitemap"):
        loc_elem = sm_elem.find("{*}loc")
        if loc_elem is None or not loc_elem.text:
            continue

        sitemap_url = loc_elem.text.strip()

        # Find lastmod (optional)
        lastmod_elem = sm_elem.find("{*}lastmod")
        lastmod_text = (
            lastmod_elem.text.strip()
            if (lastmod_elem is not None and lastmod_elem.text)
            else ""
        )

        yield sitemap_url, lastmod_text


def normalize_url(url: str) -> str:
    """
    Normalize URL for deduplication

    - Removes tracking parameters
    - Normalizes case for domain
    - Removes fragment
    - Preserves path case and important query parameters
    """
    try:
        parsed = urlparse(url.strip())

        # Normalize domain to lowercase
        netloc = parsed.netloc.lower()

        # Filter out tracking query parameters
        query_params = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_params = [
            (k, v) for k, v in query_params if k.lower() not in DROP_QUERY_KEYS
        ]
        query = urlencode(filtered_params, doseq=True)

        # Remove fragment, keep path as-is
        return urlunparse(
            (
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.params,
                query,
                "",  # Remove fragment
            )
        )

    except Exception as e:
        logger.debug(f"URL normalization failed for '{url}': {e}")
        return url.strip()


def fetch_sitemap_urls(
    sitemap_url: str, hours_lookback: int, max_urls: int = 100
) -> List[Tuple[str, datetime]]:
    """
    Fetch and parse XML sitemap with robust support for:
    - Sitemap index files
    - Gzipped content
    - Multiple namespaces
    - Timezone handling

    Args:
        sitemap_url: URL to XML sitemap or sitemap index
        hours_lookback: Only return URLs modified within this time window
        max_urls: Maximum URLs to return

    Returns:
        List of (normalized_url, publication_date) tuples, newest first
    """
    try:
        logger.debug(f"Fetching sitemap: {sitemap_url}")
        xml_text = _http_get_text(sitemap_url)
        root = ET.fromstring(xml_text)

        cutoff_time = _now_utc() - timedelta(hours=hours_lookback)
        urls_with_dates = []

        # Determine if this is a sitemap index or regular sitemap
        root_tag = root.tag.lower()

        if root_tag.endswith("sitemapindex"):
            logger.debug("Processing sitemap index")

            # Collect child sitemaps, filter by lastmod when available
            child_sitemaps = []
            for sitemap_url_child, lastmod_text in _iter_sitemap_entries(root):
                try:
                    lastmod_dt = _parse_dt(lastmod_text) if lastmod_text else None
                except Exception:
                    lastmod_dt = None

                # Include child sitemap if no lastmod or within time window
                if lastmod_dt is None or lastmod_dt >= cutoff_time:
                    child_sitemaps.append(
                        (sitemap_url_child, lastmod_dt or cutoff_time)
                    )

            # Sort by most recent first, limit to reasonable number
            child_sitemaps.sort(key=lambda x: x[1], reverse=True)
            child_sitemaps = child_sitemaps[:20]  # Max 20 child sitemaps

            logger.debug(f"Processing {len(child_sitemaps)} child sitemaps")

            # Process each child sitemap
            for child_url, _ in child_sitemaps:
                try:
                    child_xml = _http_get_text(child_url)
                    child_root = ET.fromstring(child_xml)

                    for url, lastmod_text in _iter_url_elems(child_root):
                        try:
                            lastmod_dt = (
                                _parse_dt(lastmod_text) if lastmod_text else cutoff_time
                            )

                            if lastmod_dt >= cutoff_time:
                                normalized_url = normalize_url(url)
                                urls_with_dates.append((normalized_url, lastmod_dt))

                        except Exception as e:
                            logger.debug(
                                f"Error processing URL from child sitemap: {e}"
                            )
                            continue

                except Exception as e:
                    logger.warning(f"Failed to process child sitemap {child_url}: {e}")
                    continue

        else:
            # Regular sitemap (urlset)
            logger.debug("Processing regular sitemap")

            for url, lastmod_text in _iter_url_elems(root):
                try:
                    lastmod_dt = (
                        _parse_dt(lastmod_text) if lastmod_text else cutoff_time
                    )

                    if lastmod_dt >= cutoff_time:
                        normalized_url = normalize_url(url)
                        urls_with_dates.append((normalized_url, lastmod_dt))

                except Exception as e:
                    logger.debug(f"Error processing URL: {e}")
                    continue

        # Sort by most recent first and limit
        urls_with_dates.sort(key=lambda x: x[1], reverse=True)
        urls_with_dates = urls_with_dates[:max_urls]

        logger.info(f"Fetched {len(urls_with_dates)} recent URLs from sitemap")
        return urls_with_dates

    except Exception as e:
        logger.error(f"Failed to fetch sitemap {sitemap_url}: {e}")
        return []
