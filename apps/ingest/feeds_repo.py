from typing import Optional, Dict
from datetime import datetime, timezone
from sqlalchemy import text
from core.database import get_db_session

class FeedsRepo:
    def get(self, feed_url: str) -> Dict:
        with get_db_session() as s:
            row = s.execute(text("""
                SELECT url as feed_url, etag, last_modified, last_pubdate_utc, last_run_at
                FROM feeds WHERE url = :u
            """), {"u": feed_url}).mappings().first()
            return dict(row) if row else {"feed_url": feed_url, "etag": None, "last_modified": None, "last_pubdate_utc": None, "last_run_at": None}

    def upsert(self, feed_url: str, *, etag: Optional[str]=None, last_modified: Optional[str]=None,
               last_pubdate_utc: Optional[datetime]=None) -> None:
        now = datetime.now(timezone.utc)
        with get_db_session() as s:
            s.execute(text("""
                INSERT INTO feeds (url, etag, last_modified, last_pubdate_utc, last_run_at, updated_at)
                VALUES (:u, :e, :m, :p, :now, :now)
                ON CONFLICT (url) DO UPDATE SET
                  etag = COALESCE(EXCLUDED.etag, feeds.etag),
                  last_modified = COALESCE(EXCLUDED.last_modified, feeds.last_modified),
                  last_pubdate_utc = GREATEST(COALESCE(EXCLUDED.last_pubdate_utc, feeds.last_pubdate_utc), feeds.last_pubdate_utc),
                  last_run_at = :now,
                  updated_at = :now
            """), {"u": feed_url, "e": etag, "m": last_modified, "p": last_pubdate_utc, "now": now})