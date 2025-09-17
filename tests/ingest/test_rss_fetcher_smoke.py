import unicodedata
from datetime import datetime, timezone

import pytest

# If your fetcher path differs, adjust this import
from apps.ingest.rss_fetcher import RSSFetcher

# ---- Minimal XML fixture (2 items) ----
# Includes <source> so we can verify real publisher extraction.
RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Google News - Example</title>
    <item>
      <title>US-Taiwan partnership remains a "cornerstone of stability" - Reuters</title>
      <link>https://news.google.com/articles/AAA</link>
      <pubDate>Mon, 01 Sep 2025 10:00:00 GMT</pubDate>
      <source url="https://www.reuters.com">Reuters</source>
    </item>
    <item>
      <title>Beijing warns of "dangerous provocation" - Global Times</title>
      <link>https://news.google.com/articles/BBB</link>
      <pubDate>Mon, 01 Sep 2025 11:00:00 GMT</pubDate>
      <source url="https://www.globaltimes.cn">Global Times</source>
    </item>
  </channel>
</rss>
""".encode(
    "utf-8"
)


class DummyResp:
    def __init__(self, status_code=200, content=b"", headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")


@pytest.fixture
def fetcher(monkeypatch):
    # Stub FeedsRepo.get/upsert to avoid DB in smoke test
    class DummyFeedsRepo:
        def __init__(self):
            self.meta = {}

        def get(self, feed_url: str):
            return {
                "feed_url": feed_url,
                "etag": None,
                "last_modified": None,
                "last_pubdate_utc": None,
                "last_run_at": None,
            }

        def upsert(
            self, feed_url, *, etag=None, last_modified=None, last_pubdate_utc=None
        ):
            self.meta["etag"] = etag
            self.meta["last_modified"] = last_modified
            self.meta["last_pubdate_utc"] = last_pubdate_utc

    # Patch FeedsRepo class BEFORE creating RSSFetcher
    monkeypatch.setattr("apps.1_ingest.rss_fetcher.FeedsRepo", DummyFeedsRepo)

    f = RSSFetcher()

    # Stub HTTP GET to return our XML
    def fake_get(url, headers=None, timeout=30):
        return DummyResp(
            status_code=200,
            content=RSS_XML,
            headers={"ETag": "W/xyz", "Last-Modified": "Wed, 03 Sep 2025 12:00:00 GMT"},
        )

    f.session.get = fake_get

    # Stub insert_articles to avoid DB in smoke test
    def fake_insert_articles(articles, feed_url):
        return {"inserted": len(articles), "skipped": 0}

    f.insert_articles = fake_insert_articles

    return f


def test_fetch_feed_parses_publishers_and_nfkc(fetcher, monkeypatch):
    # No 304: first fetch
    articles, stats = fetcher.fetch_feed(
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    )

    # We expect 2 parsed items
    assert len(articles) == 2

    a0 = articles[0]
    a1 = articles[1]

    # Title normalization: NFKC + whitespace collapse + dash-suffix strip
    # Ensure we actually performed Unicode normalization (en/em dashes handled)
    assert unicodedata.normalize("NFKC", a0["title_display"]) == a0["title_display"]
    assert (
        "Reuters" not in a0["title_display"].rstrip()
    )  # stripped trailing " – Reuters"
    assert (
        "Global Times" not in a1["title_display"].rstrip()
    )  # stripped trailing " — Global Times"

    # Persisted normalized form exists
    assert a0["title_norm"]
    # title_norm removes quotes and non-informative symbols per normalize_title()
    assert (
        a0["title_norm"] == "us-taiwan partnership remains a cornerstone of stability"
    )

    # Real publisher comes from <source> (not news.google.com)
    assert a0["publisher_name"] == "Reuters"
    assert (
        a0["publisher_domain"] == "www.reuters.com"
        or a0["publisher_domain"] == "reuters.com"
    )
    assert a1["publisher_name"] == "Global Times"
    assert "globaltimes" in (a1["publisher_domain"] or "")

    # Google News URL present and pubdate parsed
    assert a0["url_gnews"].startswith("https://news.google.com/")
    assert isinstance(a0["pubdate_utc"], datetime)
    assert a0["pubdate_utc"].tzinfo == timezone.utc


def test_conditional_304_short_circuits(fetcher, monkeypatch):
    # First call returns 304 (simulate cached)
    def fake_get_304(url, headers=None, timeout=30):
        return DummyResp(status_code=304, content=b"")

    fetcher.session.get = fake_get_304

    articles, stats = fetcher.fetch_feed(
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    )
    assert articles == []  # no parsing when 304
