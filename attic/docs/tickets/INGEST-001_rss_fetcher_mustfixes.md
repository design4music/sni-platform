# Plan for Claude Code (next steps)

* Scope: implement must-fixes A–F (below).
* Out of scope: clustering/LLM; any non-ingest tables.
* Acceptance criteria (see section 6).

---

## 1) Minimal DB migrations (two tiny changes)

Create two SQL files under `db/migrations/`:

**1.1 feeds table (for watermark + HTTP caching)**

```
-- 2509051201_add_feeds_table.sql
-- up
CREATE TABLE IF NOT EXISTS feeds (
  feed_url           text PRIMARY KEY,
  etag               text,
  last_modified      text,
  last_pubdate_utc   timestamptz,
  last_run_at        timestamptz
);
-- down
DROP TABLE IF EXISTS feeds;
```

**1.2 add title\_norm + unique constraint on items (or titles)**

```
-- 2509051202_add_title_norm_and_unique.sql
-- up
ALTER TABLE titles ADD COLUMN IF NOT EXISTS title_norm text;
ALTER TABLE titles ADD CONSTRAINT uq_titles_hash_feed UNIQUE (content_hash, feed_id);
-- down
ALTER TABLE titles DROP CONSTRAINT IF EXISTS uq_titles_hash_feed;
ALTER TABLE titles DROP COLUMN IF EXISTS title_norm;
```

> If your table is named `items` not `titles`, adjust the table name—*no other schema changes*.

---

## 2) Config knobs (single source of truth)

In `sni/config.py` (or `core/config.py`), add:

* `MAX_ITEMS_PER_FEED: Optional[int] = None`  *(default: no limit)*
* `LOOKBACK_DAYS: int = 3`  *(watermark grace window for out-of-order items)*
* `HTTP_RETRIES: int = 3`
* `HTTP_TIMEOUT_SEC: int = 30`

Update `.env.example` accordingly.

---

## 3) Small helper: FeedsRepo (ops only)

Add `apps/ingest/feeds_repo.py`:

* `get_feed_meta(feed_url) -> {etag,last_modified,last_pubdate_utc}`
* `upsert_feed_meta(feed_url, etag?, last_modified?, last_pubdate_utc?, last_run_at=now)`

This keeps `rss_fetcher.py` clean.

---

## 4) Changes required in `rss_fetcher.py` (no full rewrite yet)

Claude will implement these **exact** deltas:

A) **Unicode & suffix normalization**

* Apply **NFKC** to titles.
* Strip trailing publisher with **any dash** variant (`–`, `—`, `-`) when it *exactly* matches `entry.source.title`.

B) **Publisher extraction (Google News)**

* Prefer `entry.source.title` and `entry.source.href` (domain from `href`).
* Fallback to `feed.feed.title` only if `entry.source.*` missing.

C) **Idempotent UPSERT**

* Use the unique constraint `(content_hash, feed_id)` and `ON CONFLICT DO NOTHING`.
* **Persist `title_norm`** column.

D) **Remove hard slice `[:50]`**

* Iterate **all entries** returned.
* Keep only entries with `pubdate_utc > (watermark − LOOKBACK_DAYS)`.
* Update watermark to **max(pubdate)** seen.

E) **Conditional GET + retries**

* Read `etag` / `last_modified` from `feeds`.
* Send `If-None-Match` / `If-Modified-Since`.
* If **304**, short-circuit with empty result.
* Wrap GET in up to `HTTP_RETRIES` attempts (exponential backoff with small jitter).

F) **Provenance**

* Log per-feed counts (fetched/inserted/skipped/errors) and duration.
* (Optional) write a `runs` row if your ingest already does this.

---

## 5) What to keep exactly as is

* Record shape for titles/items (no new “business” columns).
* Google News URLs only; do **not** unwrap publisher links.
* Language detection behavior (graceful; may be `null`).
* Logging style and module boundaries.

---

## 6) Acceptance criteria (copy into the ticket)

**Functional**

* Re-running the same feed within minutes inserts **0** new rows (idempotent).
* Titles are normalized with **NFKC**; `title_norm` persisted.
* Publisher name/domain reflects the **actual source** (not `news.google.com`) when provided by Google News.
* No `[:50]` truncation; initial backfill ingests **all** entries returned by the feed.
* Subsequent run ingests **only** entries newer than `(last_pubdate_utc − LOOKBACK_DAYS)`.

**HTTP discipline**

* When the server returns **304**, the fetch is skipped and reported as such.
* On transient HTTP errors, up to **3 retries** occur with backoff.

**DB**

* Unique constraint `(content_hash, feed_id)` exists.
* `ON CONFLICT DO NOTHING` used for insert.
* `feeds` table updated with latest `etag`, `last_modified`, `last_pubdate_utc`, `last_run_at`.

**Telemetry**

* INFO logs include: feed URL, feed title, entry count, inserted/dupe/skip counts, duration.
* WARN/ERROR logs include the feed URL and exception message.

**Tests (smoke)**

* A small sample feed run twice → asserts idempotency.
* A run with `MAX_ITEMS_PER_FEED=None` and with a test override (e.g., `=25`) confirms the knob works (optional).
* Mocked HTTP 304 case returns 0 new items and updates `last_run_at`.

---

## 7) How to hand this to Claude Code

1. **Commit the migrations + config changes + empty FeedsRepo stub** to a branch, e.g. `feat/ingest-mustfixes`.
2. Add the **ticket doc** with this checklist.
3. Paste the **“Changes required in rss\_fetcher.py”** section into the ticket (so Claude has a bounded task).
4. Ask Claude to:

   * run the migrations,
   * implement A–F,
   * add a 2-minute **smoke test** script under `tests/ingest/` (pytest or simple script),
   * and open a PR titled: **“INGEST-001: RSS must-fixes (NFKC, real publisher, UPSERT, watermark, ETag)”**.

**PR template (drop in your repo):**

* Summary: what changed (bullet A–F)
* Migrations: 2 files (ids)
* Config: new keys + defaults
* Testing: commands and results (counts on a real feed)
* Risks: none beyond ingest; no business schema touched
* Rollback: revert PR; migrations have down scripts

---
