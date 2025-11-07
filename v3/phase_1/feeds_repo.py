"""
Feeds Repository for v3 Pipeline

Manages feed metadata (ETag, Last-Modified, watermarks) using psycopg2.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config


class FeedsRepo:
    """Repository for managing RSS feed metadata"""

    def __init__(self):
        self.config = config

    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.config.db_host,
            port=self.config.db_port,
            database=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password,
        )

    def get(self, feed_url: str) -> Dict:
        """
        Get feed metadata for conditional HTTP requests.

        Returns:
            Dict with feed_url, etag, last_modified, last_pubdate_utc, last_run_at
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT url, etag, last_modified, last_pubdate_utc, last_run_at
                    FROM feeds
                    WHERE url = %s
                """,
                    (feed_url,),
                )
                row = cur.fetchone()

                if row:
                    return {
                        "feed_url": row[0],
                        "etag": row[1],
                        "last_modified": row[2],
                        "last_pubdate_utc": row[3],
                        "last_run_at": row[4],
                    }
                else:
                    return {
                        "feed_url": feed_url,
                        "etag": None,
                        "last_modified": None,
                        "last_pubdate_utc": None,
                        "last_run_at": None,
                    }
        finally:
            conn.close()

    def upsert(
        self,
        feed_url: str,
        *,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        last_pubdate_utc: Optional[datetime] = None,
    ) -> None:
        """
        Update feed metadata after fetching.

        Args:
            feed_url: Feed URL
            etag: ETag from response headers
            last_modified: Last-Modified from response headers
            last_pubdate_utc: Latest article publication date seen
        """
        now = datetime.now(timezone.utc)
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE feeds
                    SET etag = COALESCE(%s, etag),
                        last_modified = COALESCE(%s, last_modified),
                        last_pubdate_utc = GREATEST(COALESCE(%s, last_pubdate_utc), last_pubdate_utc),
                        last_run_at = %s,
                        updated_at = %s
                    WHERE url = %s
                """,
                    (etag, last_modified, last_pubdate_utc, now, now, feed_url),
                )
            conn.commit()
        finally:
            conn.close()
