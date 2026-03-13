"""
Social Posting Module -- Daemon Slot 5

Automatically posts trending events, CTM spotlights, and a daily
"Narrative of the Day" to Telegram and X/Twitter.

Usage:
    python -m pipeline.social.social_posting --dry-run --type trending
    python -m pipeline.social.social_posting --platform telegram --type trending
    python -m pipeline.social.social_posting --dry-run --type narrative_of_day
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from psycopg2.extras import RealDictCursor

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import config  # noqa: E402

# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


def _title_words(title):
    """Lowercase word set for overlap comparison."""
    return set(title.lower().split())


def _is_duplicate_title(title, posted_titles, threshold=0.6):
    """Check if title overlaps > threshold with any already-posted title."""
    words = _title_words(title)
    if not words:
        return False
    for posted in posted_titles:
        posted_words = _title_words(posted)
        if not posted_words:
            continue
        overlap = len(words & posted_words) / min(len(words), len(posted_words))
        if overlap > threshold:
            return True
    return False


def _get_posted_titles(conn, post_type, days=3):
    """Fetch titles of recently posted events for dedup."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(e.title, '') FROM social_posts sp
            JOIN events_v3 e ON e.id = sp.entity_id
            WHERE sp.post_type = %s AND sp.error IS NULL
              AND sp.posted_at > NOW() - make_interval(days => %s)
            """,
            (post_type, days),
        )
        return [row[0] for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Content Selection (SQL)
# ---------------------------------------------------------------------------


def _enrich_event_stats(conn, event):
    """Add publisher_count and language_count to event dict."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(DISTINCT t.publisher_name) as pubs,
                   COUNT(DISTINCT t.detected_language) as langs
            FROM event_v3_titles evt
            JOIN titles_v3 t ON t.id = evt.title_id
            WHERE evt.event_id = %s
            """,
            (str(event["id"]),),
        )
        row = cur.fetchone()
        event["publisher_count"] = row[0]
        event["language_count"] = row[1]
    return event


def select_trending_event(conn):
    """Top trending event not yet posted, with dedup against recent posts."""
    posted_titles = _get_posted_titles(conn, "trending")

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT e.id, e.title, e.summary, e.source_batch_count,
                   c.centroid_id, cv.label as centroid_label, c.track,
                   (ln(e.source_batch_count + 1)
                    * pow(0.5, EXTRACT(EPOCH FROM (NOW() - COALESCE(e.last_active, e.date)::timestamp)) / (3 * 86400))
                    * CASE WHEN EXTRACT(EPOCH FROM (NOW() - e.date::timestamp)) < 86400
                           THEN 1 + LEAST(e.source_batch_count / GREATEST(EXTRACT(EPOCH FROM (NOW() - e.date::timestamp)) / 3600, 1), 3)
                           ELSE 1 END
                   )::numeric(10,2) as trending_score
            FROM events_v3 e
            JOIN ctm c ON c.id = e.ctm_id
            JOIN centroids_v3 cv ON cv.id = c.centroid_id
            WHERE e.source_batch_count >= 10
              AND e.is_catchall = false
              AND e.title IS NOT NULL
              AND e.summary IS NOT NULL
              AND LENGTH(TRIM(e.summary)) > 20
              AND COALESCE(e.last_active, e.date) >= CURRENT_DATE - INTERVAL '3 days'
              AND NOT EXISTS (
                  SELECT 1 FROM social_posts sp
                  WHERE sp.entity_id = e.id AND sp.post_type = 'trending'
                    AND sp.error IS NULL
              )
            ORDER BY trending_score DESC
            LIMIT 20
            """
        )
        candidates = cur.fetchall()

    for event in candidates:
        if not _is_duplicate_title(event["title"], posted_titles):
            return _enrich_event_stats(conn, event)
        print("  Dedup skip: %s" % event["title"][:60])

    return None


def select_ctm_spotlight(conn):
    """CTM with substantial summary, not posted in last 7 days."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT c.id, c.centroid_id, c.track, c.title_count,
                   c.summary_text, cv.label as centroid_label,
                   (SELECT COUNT(*) FROM events_v3 e WHERE e.ctm_id = c.id) as event_count
            FROM ctm c
            JOIN centroids_v3 cv ON cv.id = c.centroid_id
            WHERE c.summary_text IS NOT NULL
              AND LENGTH(c.summary_text) >= 200
              AND c.title_count >= 100
              AND c.is_frozen = false
              AND NOT EXISTS (
                  SELECT 1 FROM social_posts sp
                  WHERE sp.entity_id = c.id AND sp.post_type = 'ctm_spotlight'
                    AND sp.error IS NULL
                    AND sp.posted_at > NOW() - INTERVAL '7 days'
              )
            ORDER BY c.title_count DESC
            LIMIT 1
            """
        )
        return cur.fetchone()


def select_narrative_candidate(conn):
    """Top event for Narrative of the Day. Higher bar, with dedup."""
    posted_titles = _get_posted_titles(conn, "narrative_of_day") + _get_posted_titles(
        conn, "trending"
    )

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT e.id, e.title, e.summary, e.source_batch_count,
                   c.centroid_id, cv.label as centroid_label, c.track
            FROM events_v3 e
            JOIN ctm c ON c.id = e.ctm_id
            JOIN centroids_v3 cv ON cv.id = c.centroid_id
            WHERE e.source_batch_count >= 20
              AND e.is_catchall = false
              AND e.title IS NOT NULL
              AND e.summary IS NOT NULL
              AND LENGTH(TRIM(e.summary)) > 20
              AND COALESCE(e.last_active, e.date) >= CURRENT_DATE - INTERVAL '2 days'
              AND NOT EXISTS (
                  SELECT 1 FROM social_posts sp
                  WHERE sp.entity_id = e.id AND sp.post_type = 'narrative_of_day'
                    AND sp.error IS NULL
              )
            ORDER BY e.source_batch_count DESC
            LIMIT 10
            """
        )
        candidates = cur.fetchall()

    for event in candidates:
        if not _is_duplicate_title(event["title"], posted_titles):
            return _enrich_event_stats(conn, event)
        print("  Dedup skip (narrative): %s" % event["title"][:60])

    return None


# ---------------------------------------------------------------------------
# Narrative Extraction (reuse existing pipeline)
# ---------------------------------------------------------------------------


def ensure_narratives_extracted(conn, event_id):
    """Return existing narrative frames, or extract new ones."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, label, description, moral_frame
            FROM narratives
            WHERE entity_type = 'event' AND entity_id = %s
            """,
            (str(event_id),),
        )
        existing = cur.fetchall()

    if existing:
        return existing

    # Import extraction functions (deferred to avoid circular imports)
    from pipeline.phase_4.extract_ctm_narratives import sample_titles
    from pipeline.phase_4.extract_event_narratives import (
        extract_narratives_llm,
        fetch_event_by_id,
        fetch_event_titles,
        save_narratives,
    )

    event = fetch_event_by_id(conn, event_id)
    if not event:
        print("  Event %s not found" % str(event_id)[:8])
        return []

    titles = fetch_event_titles(conn, event_id)
    if len(titles) < 10:
        print("  Only %d titles, skipping extraction" % len(titles))
        return []

    sampled = sample_titles(titles, time_stratify=True)
    print("  Extracting narratives from %d sampled titles..." % len(sampled))

    try:
        frames, tok_in, tok_out = extract_narratives_llm(event, sampled)
    except Exception as e:
        print("  LLM extraction failed: %s" % e)
        return []

    if not frames or not isinstance(frames, list):
        print("  No frames extracted")
        return []

    saved = save_narratives(
        conn, event_id, frames, sampled, event["source_batch_count"]
    )
    print("  Extracted %d narrative frames (tokens: %d/%d)" % (saved, tok_in, tok_out))

    # Compute signal stats
    try:
        from core.signal_stats import compute_event_stats

        stats = compute_event_stats(conn, event_id)
        if stats:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE narratives SET signal_stats = signal_stats || %s
                    WHERE entity_type = 'event' AND entity_id = %s
                    """,
                    (json.dumps(stats), str(event_id)),
                )
            conn.commit()
    except Exception as e:
        print("  Signal stats failed: %s" % e)

    # Re-fetch saved narratives
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, label, description, moral_frame
            FROM narratives
            WHERE entity_type = 'event' AND entity_id = %s
            """,
            (str(event_id),),
        )
        return cur.fetchall()


# ---------------------------------------------------------------------------
# RAI Analysis (call frontend API)
# ---------------------------------------------------------------------------


def ensure_rai_analysis(narrative_id, base_url, internal_key):
    """POST to frontend RAI API. Returns (sections, scores) or (None, None)."""
    url = "%s/api/rai-analyse" % base_url.rstrip("/")
    headers = {
        "Authorization": "Bearer %s" % internal_key,
        "Content-Type": "application/json",
    }

    try:
        resp = httpx.post(
            url,
            headers=headers,
            json={"narrative_id": str(narrative_id)},
            timeout=120,
        )
        if resp.status_code != 200:
            print("  RAI API error: %d - %s" % (resp.status_code, resp.text[:200]))
            return None, None

        data = resp.json()
        return data.get("sections"), data.get("scores")
    except Exception as e:
        print("  RAI API call failed: %s" % e)
        return None, None


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def _clean_summary(text):
    """Strip markdown headers and extra whitespace from LLM summaries."""
    if not text:
        return ""
    import re

    # Remove ### headers
    text = re.sub(r"^#{1,4}\s+\w+\s*\n?", "", text, flags=re.MULTILINE)
    # Collapse multiple newlines
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def _truncate(text, max_len):
    """Truncate text to max_len, adding ... if needed."""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rsplit(" ", 1)[0] + "..."


def _stats_line(event):
    """Build stats string like '179 articles, 75 outlets, 12 languages'."""
    parts = ["%d articles" % event["source_batch_count"]]
    pubs = event.get("publisher_count") or 0
    langs = event.get("language_count") or 0
    if pubs:
        parts.append("%d outlets" % pubs)
    if langs > 1:
        parts.append("%d languages" % langs)
    return ", ".join(parts)


_TRACK_DISPLAY = {
    "geo_security": "Security",
    "geo_politics": "Politics",
    "geo_economy": "Economy",
    "geo_information": "Information",
    "geo_energy": "Energy",
    "energy_conflict": "Energy Conflict",
}


def _topic_path(event):
    """Build 'Label > Track' string with human-readable track name."""
    label = event.get("centroid_label") or ""
    track = event.get("track") or ""
    display_track = _TRACK_DISPLAY.get(track, track)
    if label and display_track:
        return "%s > %s" % (label, display_track)
    return label or display_track


def _escape_html(text):
    """Escape HTML special chars for Telegram HTML mode."""
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


_TRENDING_FOOTER = (
    "<i>Trending story tracked by WorldBrief -- "
    "AI-powered, fully automated media intelligence with worldwide reach.\n"
    "worldbrief.info</i>"
)

_CTM_FOOTER = (
    "<i>Topic spotlight from WorldBrief -- "
    "AI-powered, fully automated media intelligence with worldwide reach.\n"
    "worldbrief.info</i>"
)

_NARRATIVE_FOOTER = (
    "<i>Narrative of the Day from WorldBrief -- "
    "AI-powered, fully automated media intelligence with worldwide reach.\n"
    "worldbrief.info</i>"
)


def format_telegram_trending(event, base_url):
    """Trending event post for Telegram (HTML mode)."""
    url = "%s/events/%s" % (base_url.rstrip("/"), event["id"])
    summary = _escape_html(_truncate(_clean_summary(event["summary"]), 300))
    stats = _stats_line(event)
    topic = _escape_html(_topic_path(event))

    return (
        "<b>%s</b>\n\n"
        "%s\n\n"
        "%s: %s\n"
        '<a href="%s">Read the full story, view sources and explore media narratives</a>\n\n'
        "%s"
    ) % (
        _escape_html(event["title"]),
        summary,
        topic,
        stats,
        url,
        _TRENDING_FOOTER,
    )


def _ctm_stats_line(ctm):
    """Build CTM stats like 'Tracking 425 headlines across 12 events'."""
    parts = ["Tracking %d headlines" % ctm["title_count"]]
    events = ctm.get("event_count") or 0
    if events:
        parts.append("across %d events" % events)
    return " ".join(parts)


def format_telegram_ctm(ctm, base_url):
    """CTM spotlight post for Telegram (HTML mode)."""
    url = "%s/c/%s/t/%s" % (
        base_url.rstrip("/"),
        ctm["centroid_id"],
        ctm["track"],
    )
    summary = _escape_html(_truncate(_clean_summary(ctm["summary_text"]), 400))
    return (
        "<b>%s</b> -- %s\n\n"
        "%s\n\n"
        "%s\n"
        '<a href="%s">Explore the topic, view event timeline and related coverage</a>\n\n'
        "%s"
    ) % (
        _escape_html(ctm["centroid_label"]),
        _escape_html(_TRACK_DISPLAY.get(ctm["track"], ctm["track"])),
        summary,
        _ctm_stats_line(ctm),
        url,
        _CTM_FOOTER,
    )


def format_telegram_narrative(event, frames, analysis, base_url):
    """Flagship Narrative of the Day for Telegram (HTML mode)."""
    sections, scores = analysis
    narrative_id = frames[0]["id"] if frames else ""
    analysis_url = "%s/analysis/%s" % (base_url.rstrip("/"), narrative_id)
    event_url = "%s/events/%s" % (base_url.rstrip("/"), event["id"])

    lines = ["<b>Narrative of the Day</b>\n"]
    lines.append("<b>%s</b>\n" % _escape_html(event["title"]))

    for f in frames[:3]:
        lines.append(
            "- <b>%s</b>: %s"
            % (
                _escape_html(f["label"]),
                _escape_html(_truncate(f.get("description") or "", 120)),
            )
        )

    if scores:
        adequacy = scores.get("adequacy")
        if adequacy is not None:
            lines.append("\nCoverage adequacy: %s/10" % adequacy)

        blind_spots = scores.get("blind_spots")
        if blind_spots and isinstance(blind_spots, list):
            lines.append("Blind spots: %s" % _escape_html(", ".join(blind_spots[:3])))

        synthesis = scores.get("synthesis")
        if synthesis:
            lines.append("\n<i>%s</i>" % _escape_html(_truncate(synthesis, 200)))

    lines.append(
        '\n<a href="%s">Read full AI analysis</a> | <a href="%s">View event and sources</a>'
        % (analysis_url, event_url)
    )
    lines.append("\n%s" % _NARRATIVE_FOOTER)
    return "\n".join(lines)


def format_x_trending(event, base_url):
    """Single tweet for trending event, max 280 chars."""
    url = "%s/events/%s" % (base_url.rstrip("/"), event["id"])
    # URL counts as ~23 chars on X
    budget = 280 - 25 - 3  # url + space + buffer
    title = _truncate(event["title"], 120)
    summary = _truncate(event["summary"], budget - len(title) - 2)
    return "%s\n\n%s\n%s" % (title, summary, url)


def format_x_narrative_thread(event, frames, analysis, base_url):
    """Thread for Narrative of the Day on X."""
    sections, scores = analysis
    narrative_id = frames[0]["id"] if frames else ""
    analysis_url = "%s/analysis/%s" % (base_url.rstrip("/"), narrative_id)

    tweets = []

    # Tweet 1: hook
    tweets.append(
        "Narrative of the Day: %s\n\n%d sources, multiple competing frames. Thread:"
        % (_truncate(event["title"], 180), event["source_batch_count"])
    )

    # Tweet 2-3: frame highlights
    frame_lines = []
    for f in frames[:3]:
        frame_lines.append(
            "- %s: %s" % (f["label"], _truncate(f.get("description") or "", 80))
        )
    tweets.append("\n".join(frame_lines))

    # RAI findings
    if scores:
        rai_parts = []
        adequacy = scores.get("adequacy")
        if adequacy is not None:
            rai_parts.append("Coverage: %s/10" % adequacy)
        blind_spots = scores.get("blind_spots")
        if blind_spots and isinstance(blind_spots, list):
            rai_parts.append("Blind spots: %s" % ", ".join(blind_spots[:2]))
        if rai_parts:
            tweets.append("\n".join(rai_parts))

    # Last tweet: link
    tweets.append("Full analysis: %s" % analysis_url)

    # Enforce 280 char limit per tweet
    return [_truncate(t, 280) for t in tweets]


# ---------------------------------------------------------------------------
# Platform Clients
# ---------------------------------------------------------------------------


def post_telegram(text, bot_token, channel_id):
    """Send message via Telegram Bot API. Returns message_id or None."""
    url = "https://api.telegram.org/bot%s/sendMessage" % bot_token
    payload = {
        "chat_id": channel_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = httpx.post(url, json=payload, timeout=30)
        data = resp.json()
        if data.get("ok"):
            return str(data["result"]["message_id"])
        print("  Telegram error: %s" % data.get("description", "unknown"))
        return None
    except Exception as e:
        print("  Telegram send failed: %s" % e)
        return None


def post_x_tweet(client, text, reply_to=None):
    """Post a tweet via tweepy. Returns tweet_id or None."""
    try:
        kwargs = {"text": text}
        if reply_to:
            kwargs["in_reply_to_tweet_id"] = reply_to
        resp = client.create_tweet(**kwargs)
        return str(resp.data["id"])
    except Exception as e:
        print("  X post failed: %s" % e)
        return None


def post_x_thread(client, tweets):
    """Post a thread of tweets. Returns first tweet_id or None."""
    first_id = None
    reply_to = None
    for text in tweets:
        tid = post_x_tweet(client, text, reply_to=reply_to)
        if tid is None:
            return first_id
        if first_id is None:
            first_id = tid
        reply_to = tid
        time.sleep(1)  # rate limit courtesy
    return first_id


def _get_x_client():
    """Create tweepy Client from config."""
    try:
        import tweepy
    except ImportError:
        print("  tweepy not installed, skipping X posting")
        return None

    if not all(
        [
            config.x_api_key,
            config.x_api_secret,
            config.x_access_token,
            config.x_access_secret,
        ]
    ):
        print("  X credentials not configured")
        return None

    return tweepy.Client(
        consumer_key=config.x_api_key,
        consumer_secret=config.x_api_secret,
        access_token=config.x_access_token,
        access_token_secret=config.x_access_secret,
    )


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------


def record_post(
    conn,
    platform,
    post_type,
    entity_type,
    entity_id,
    narrative_id,
    external_id,
    text,
    error=None,
):
    """Insert into social_posts table."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO social_posts
                (platform, post_type, entity_type, entity_id, narrative_id,
                 external_id, post_text, error)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (platform, post_type, entity_id) DO UPDATE SET
                external_id = EXCLUDED.external_id,
                post_text = EXCLUDED.post_text,
                error = EXCLUDED.error,
                posted_at = NOW()
            """,
            (
                platform,
                post_type,
                entity_type,
                str(entity_id),
                str(narrative_id) if narrative_id else None,
                external_id,
                text[:2000],
                error,
            ),
        )
    conn.commit()


# ---------------------------------------------------------------------------
# Posting Logic
# ---------------------------------------------------------------------------


def _post_to_platforms(
    conn,
    post_type,
    entity_type,
    entity_id,
    narrative_id,
    telegram_text,
    x_text_or_thread,
    platform_filter=None,
    dry_run=False,
):
    """Post content to configured platforms, record results."""
    results = []

    # Telegram
    if platform_filter in (None, "telegram"):
        if dry_run:
            print("\n--- TELEGRAM [%s] ---" % post_type)
            print(telegram_text)
            results.append(("telegram", "DRY_RUN"))
        elif config.telegram_bot_token and config.telegram_channel_id:
            msg_id = post_telegram(
                telegram_text, config.telegram_bot_token, config.telegram_channel_id
            )
            error = None if msg_id else "send_failed"
            record_post(
                conn,
                "telegram",
                post_type,
                entity_type,
                entity_id,
                narrative_id,
                msg_id,
                telegram_text,
                error,
            )
            results.append(("telegram", msg_id or "FAILED"))
        else:
            print("  Telegram not configured, skipping")

    # X/Twitter
    if platform_filter in (None, "x"):
        if dry_run:
            print("\n--- X [%s] ---" % post_type)
            if isinstance(x_text_or_thread, list):
                for i, t in enumerate(x_text_or_thread, 1):
                    print("[Tweet %d] %s" % (i, t))
            else:
                print(x_text_or_thread)
            results.append(("x", "DRY_RUN"))
        else:
            client = _get_x_client()
            if client:
                if isinstance(x_text_or_thread, list):
                    tweet_id = post_x_thread(client, x_text_or_thread)
                    text_for_record = x_text_or_thread[0] if x_text_or_thread else ""
                else:
                    tweet_id = post_x_tweet(client, x_text_or_thread)
                    text_for_record = x_text_or_thread
                error = None if tweet_id else "send_failed"
                record_post(
                    conn,
                    "x",
                    post_type,
                    entity_type,
                    entity_id,
                    narrative_id,
                    tweet_id,
                    text_for_record,
                    error,
                )
                results.append(("x", tweet_id or "FAILED"))

    return results


def _count_today_posts(conn, post_type):
    """Count posts of this type today (UTC)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM social_posts
            WHERE post_type = %s
              AND posted_at >= CURRENT_DATE
              AND error IS NULL
            """,
            (post_type,),
        )
        return cur.fetchone()[0]


def try_trending(conn, base_url, platform=None, dry_run=False):
    """Select and post a trending event."""
    event = select_trending_event(conn)
    if not event:
        print("  No trending event available")
        return None

    print(
        "  Trending: %s (%d sources)"
        % (event["title"][:60], event["source_batch_count"])
    )
    tg = format_telegram_trending(event, base_url)
    x = format_x_trending(event, base_url)
    return _post_to_platforms(
        conn, "trending", "event", event["id"], None, tg, x, platform, dry_run
    )


def try_ctm_spotlight(conn, base_url, platform=None, dry_run=False):
    """Select and post a CTM spotlight."""
    ctm = select_ctm_spotlight(conn)
    if not ctm:
        print("  No CTM spotlight available")
        return None

    print(
        "  CTM: %s / %s (%d titles)"
        % (ctm["centroid_label"], ctm["track"], ctm["title_count"])
    )
    tg = format_telegram_ctm(ctm, base_url)
    # X tweet: simplified version
    url = "%s/c/%s/t/%s" % (base_url.rstrip("/"), ctm["centroid_id"], ctm["track"])
    x = "%s - %s\n\n%s\n%s" % (
        ctm["centroid_label"],
        ctm["track"],
        _truncate(ctm["summary_text"], 180),
        url,
    )
    return _post_to_platforms(
        conn, "ctm_spotlight", "ctm", ctm["id"], None, tg, x, platform, dry_run
    )


def try_narrative_of_day(conn, base_url, internal_key, platform=None, dry_run=False):
    """Select top event, extract narratives, get RAI analysis, post."""
    event = select_narrative_candidate(conn)
    if not event:
        print("  No narrative candidate available")
        return None

    print(
        "  Narrative candidate: %s (%d sources)"
        % (event["title"][:60], event["source_batch_count"])
    )

    # Extract narratives
    frames = ensure_narratives_extracted(conn, event["id"])
    if not frames:
        print("  No narrative frames, skipping")
        return None

    # RAI analysis
    sections, scores = None, None
    if internal_key and not dry_run:
        sections, scores = ensure_rai_analysis(frames[0]["id"], base_url, internal_key)
    elif dry_run:
        scores = {
            "adequacy": "N/A",
            "blind_spots": ["(dry run)"],
            "synthesis": "(dry run)",
        }
        sections = []

    analysis = (sections or [], scores or {})

    tg = format_telegram_narrative(event, frames, analysis, base_url)
    x_thread = format_x_narrative_thread(event, frames, analysis, base_url)
    return _post_to_platforms(
        conn,
        "narrative_of_day",
        "event",
        event["id"],
        frames[0]["id"] if frames else None,
        tg,
        x_thread,
        platform,
        dry_run,
    )


# ---------------------------------------------------------------------------
# Main Entry Points
# ---------------------------------------------------------------------------


def run_social_posting(conn, cfg):
    """Daemon entry point. Called from Slot 5 every 3h."""
    base_url = cfg.social_base_url
    internal_key = cfg.rai_internal_key

    now_utc = datetime.now(timezone.utc)
    hour_utc = now_utc.hour
    print("Social posting at %s UTC" % now_utc.strftime("%H:%M"))

    narrative_count = _count_today_posts(conn, "narrative_of_day")
    ctm_count = _count_today_posts(conn, "ctm_spotlight")
    trending_count = _count_today_posts(conn, "trending")
    print(
        "  Today: %d narrative, %d CTM, %d trending"
        % (narrative_count, ctm_count, trending_count)
    )

    results = {"narrative_of_day": 0, "ctm_spotlight": 0, "trending": 0}

    # Narrative of the Day: up to 2/day, after 6 UTC
    if narrative_count < 2 and hour_utc >= 6:
        r = try_narrative_of_day(conn, base_url, internal_key)
        if r:
            results["narrative_of_day"] = 1

    # CTM spotlight: up to 3/day
    if ctm_count < 3:
        r = try_ctm_spotlight(conn, base_url)
        if r:
            results["ctm_spotlight"] = 1

    # Trending: up to 8/day
    if trending_count < 8:
        r = try_trending(conn, base_url)
        if r:
            results["trending"] = 1

    print("Posted: %s" % results)
    return results


def main():
    parser = argparse.ArgumentParser(description="Social posting for WorldBrief")
    parser.add_argument(
        "--dry-run", action="store_true", help="Format and print, don't post"
    )
    parser.add_argument(
        "--type",
        choices=["trending", "ctm_spotlight", "narrative_of_day"],
        help="Force specific post type",
    )
    parser.add_argument(
        "--platform",
        choices=["telegram", "x"],
        help="Post to one platform only",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of posts to send (default 1)",
    )
    args = parser.parse_args()

    import psycopg2

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    base_url = config.social_base_url
    internal_key = config.rai_internal_key

    print("Social Posting CLI")
    print("=" * 50)
    print("Base URL: %s" % base_url)
    print("Dry run: %s" % args.dry_run)
    print("Type: %s" % (args.type or "auto"))
    print("Platform: %s" % (args.platform or "all"))
    print()

    if args.type == "trending":
        for i in range(args.count):
            if args.count > 1:
                print("[%d/%d]" % (i + 1, args.count))
            try_trending(conn, base_url, args.platform, args.dry_run)
    elif args.type == "ctm_spotlight":
        for i in range(args.count):
            if args.count > 1:
                print("[%d/%d]" % (i + 1, args.count))
            try_ctm_spotlight(conn, base_url, args.platform, args.dry_run)
    elif args.type == "narrative_of_day":
        for i in range(args.count):
            if args.count > 1:
                print("[%d/%d]" % (i + 1, args.count))
            try_narrative_of_day(
                conn, base_url, internal_key, args.platform, args.dry_run
            )
    else:
        run_social_posting(conn, config)

    conn.close()


if __name__ == "__main__":
    main()
