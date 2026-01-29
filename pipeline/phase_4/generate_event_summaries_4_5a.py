"""
Phase 4.5a: Event Summary Generation

Generates conversational summaries for event clusters:
- title: Plain-language headline (5-12 words)
- summary: Conversational explanation scaled to topic size
- tags: Derived from clustering backbone signals (persons, orgs, etc.)

Input: Clustered titles + backbone signals from title_labels
Output: {title, summary, tags} stored in events_v3
"""

import argparse
import asyncio
import json
import re
import sys
from collections import Counter
from pathlib import Path

import httpx
import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from core.prompts import EVENT_SUMMARY_SYSTEM_PROMPT, EVENT_SUMMARY_USER_PROMPT


def get_backbone_signals(conn, event_id: str) -> dict:
    """Compute backbone signals (what grouped these headlines) from title_labels.

    Returns signals with their frequency counts, sorted by importance.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tl.persons, tl.orgs, tl.commodities, tl.policies, tl.places
            FROM event_v3_titles evt
            JOIN title_labels tl ON tl.title_id = evt.title_id
            WHERE evt.event_id = %s
            """,
            (event_id,),
        )

        persons = Counter()
        orgs = Counter()
        commodities = Counter()
        policies = Counter()
        places = Counter()

        for row in cur.fetchall():
            if row[0]:
                for p in row[0]:
                    persons[p] += 1
            if row[1]:
                for o in row[1]:
                    orgs[o] += 1
            if row[2]:
                for c in row[2]:
                    commodities[c] += 1
            if row[3]:
                for p in row[3]:
                    policies[p] += 1
            if row[4]:
                for p in row[4]:
                    places[p] += 1

        return {
            "persons": persons.most_common(5),
            "orgs": orgs.most_common(5),
            "commodities": commodities.most_common(3),
            "policies": policies.most_common(3),
            "places": places.most_common(3),
        }


def get_title_signals(conn, event_id: str) -> dict:
    """Get signals for each title in an event.

    Returns: {title_id: set of all signals for that title}
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT evt.title_id, t.title_display,
                   tl.persons, tl.orgs, tl.commodities, tl.policies, tl.places
            FROM event_v3_titles evt
            JOIN titles_v3 t ON t.id = evt.title_id
            LEFT JOIN title_labels tl ON tl.title_id = evt.title_id
            WHERE evt.event_id = %s
            """,
            (event_id,),
        )

        result = {}
        for row in cur.fetchall():
            title_id, title_display, persons, orgs, commodities, policies, places = row
            signals = set()
            if persons:
                signals.update(persons)
            if orgs:
                signals.update(orgs)
            if commodities:
                signals.update(commodities)
            if policies:
                signals.update(policies)
            if places:
                signals.update(places)
            result[title_id] = {
                "title": title_display,
                "signals": signals,
            }
        return result


def is_combo_headline(title: str) -> bool:
    """Detect 'news roundup' headlines that list multiple unrelated stories.

    Examples:
    - "Minnesota Prosecutors Quit, Trump in Detroit, Inflation Report"
    - "Gold rises, stocks fall, Fed meets tomorrow"
    """
    # Count comma-separated segments that look like distinct stories
    # (capitalized words after commas suggest new topics)
    import re

    segments = [s.strip() for s in title.split(",")]
    if len(segments) >= 3:
        # 3+ comma segments is likely a roundup
        return True

    # Check for patterns like "X, Y, Z" where each is a distinct topic
    # Look for multiple capitalized phrases separated by commas
    caps_after_comma = len(re.findall(r",\s*[A-Z][a-z]+", title))
    if caps_after_comma >= 2:
        return True

    return False


def filter_outlier_titles(
    titles: list,
    title_signals: dict,
    backbone_signals: dict,
    min_core_freq: int = 3,
) -> tuple:
    """Filter out titles that don't share enough core signals with the topic.

    Args:
        titles: List of title strings
        title_signals: Dict from get_title_signals
        backbone_signals: Dict from get_backbone_signals
        min_core_freq: Minimum frequency for a signal to be "core"

    Returns:
        (core_titles, outlier_titles) - both lists of strings
    """
    # Build set of core signals (appear frequently in topic)
    core_signals = set()
    for signal_list in [
        backbone_signals["persons"],
        backbone_signals["orgs"],
        backbone_signals["commodities"],
        backbone_signals["policies"],
        backbone_signals["places"],
    ]:
        for signal, count in signal_list:
            if count >= min_core_freq:
                core_signals.add(signal)

    # If no core signals, return all titles as core
    if not core_signals:
        return titles, []

    # Build title -> signals lookup by title text
    title_to_signals = {}
    for tid, data in title_signals.items():
        title_to_signals[data["title"]] = data["signals"]

    core_titles = []
    outlier_titles = []

    for title in titles:
        title_sigs = title_to_signals.get(title, set())
        overlap = title_sigs & core_signals

        # Combo headlines (news roundups) need stricter filtering
        if is_combo_headline(title):
            # Require 2+ core signals for combo headlines
            if len(overlap) >= 2:
                core_titles.append(title)
            else:
                outlier_titles.append(title)
        else:
            # Regular headlines: 1+ core signal is enough
            if overlap:
                core_titles.append(title)
            else:
                outlier_titles.append(title)

    return core_titles, outlier_titles


def format_backbone_signals(signals: dict) -> str:
    """Format backbone signals for the prompt."""
    parts = []
    if signals["persons"]:
        items = ["%s (%d)" % (p, c) for p, c in signals["persons"]]
        parts.append("People: %s" % ", ".join(items))
    if signals["orgs"]:
        items = ["%s (%d)" % (o, c) for o, c in signals["orgs"]]
        parts.append("Organizations: %s" % ", ".join(items))
    if signals["commodities"]:
        items = ["%s (%d)" % (c, cnt) for c, cnt in signals["commodities"]]
        parts.append("Commodities: %s" % ", ".join(items))
    if signals["policies"]:
        items = ["%s (%d)" % (p, c) for p, c in signals["policies"]]
        parts.append("Policies: %s" % ", ".join(items))
    if signals["places"]:
        items = ["%s (%d)" % (p, c) for p, c in signals["places"]]
        parts.append("Places: %s" % ", ".join(items))
    return "\n".join(parts) if parts else "(no strong signals)"


def normalize_tag(tag_type: str, value: str) -> str:
    """Normalize a tag value for consistency."""
    # Lowercase and strip
    value = value.lower().strip()
    # Replace underscores with spaces
    value = value.replace("_", " ")
    # Remove extra whitespace
    value = " ".join(value.split())
    return "%s:%s" % (tag_type, value)


def signals_to_tags(signals: dict, min_freq: int = 2) -> list:
    """Convert backbone signals to typed tags.

    Only includes signals that appear in at least min_freq titles.
    Deduplicates and normalizes tags.
    """
    seen = set()
    tags = []

    def add_tag(tag_type: str, value: str, count: int):
        if count < min_freq:
            return
        tag = normalize_tag(tag_type, value)
        # Dedupe by normalized form
        if tag not in seen:
            seen.add(tag)
            tags.append(tag)

    # Add high-frequency signals as tags (priority order)
    for person, count in signals["persons"]:
        add_tag("person", person, count)
    for org, count in signals["orgs"]:
        add_tag("org", org, count)
    for commodity, count in signals["commodities"]:
        add_tag("topic", commodity, count)
    for policy, count in signals["policies"]:
        add_tag("topic", policy, count)
    for place, count in signals["places"]:
        add_tag("place", place, count)

    return tags[:8]  # Limit to 8 tags


def get_events_needing_summaries(
    conn,
    max_events: int = None,
    ctm_id: str = None,
    centroid_id: str = None,
    track: str = None,
    domestic_only: bool = False,
    bilateral_only: bool = False,
    force_regenerate: bool = False,
) -> list:
    """Fetch events that need title/summary generation.

    Args:
        conn: Database connection
        max_events: Maximum events to return
        ctm_id: Filter by specific CTM
        centroid_id: Filter by centroid (e.g., AMERICAS-USA)
        track: Filter by track (e.g., geo_economy)
        domestic_only: Only include events with bucket_key IS NULL
        bilateral_only: Only include events with bucket_key IS NOT NULL
        force_regenerate: Regenerate even if summary exists
    """
    with conn.cursor() as cur:
        conditions = []
        params = []

        if not force_regenerate:
            # Events without title OR with mechanical labels
            conditions.append(
                "(e.title IS NULL OR e.summary LIKE '%%->%%' OR e.summary LIKE '%%titles)%%' OR e.summary LIKE '%%SPIKE]%%')"
            )

        if ctm_id:
            conditions.append("e.ctm_id = %s")
            params.append(ctm_id)

        if centroid_id and track:
            conditions.append(
                "e.ctm_id IN (SELECT id FROM ctm WHERE centroid_id = %s AND track = %s)"
            )
            params.append(centroid_id)
            params.append(track)
        elif centroid_id:
            conditions.append("e.ctm_id IN (SELECT id FROM ctm WHERE centroid_id = %s)")
            params.append(centroid_id)

        if domestic_only:
            conditions.append("e.bucket_key IS NULL")
            conditions.append("e.is_catchall = false")
        elif bilateral_only:
            conditions.append("e.bucket_key IS NOT NULL")
            conditions.append("e.is_catchall = false")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        limit_clause = "LIMIT %s" if max_events else ""
        if max_events:
            params.append(max_events)

        query = """
            SELECT e.id, e.ctm_id, e.summary as label, e.bucket_key, e.source_batch_count,
                   e.date, e.first_seen
            FROM events_v3 e
            JOIN ctm c ON c.id = e.ctm_id
            WHERE %s
            ORDER BY c.title_count DESC, e.ctm_id, e.source_batch_count DESC NULLS LAST
            %s
        """ % (
            where_clause,
            limit_clause,
        )

        cur.execute(query, tuple(params) if params else None)

        events = []
        for row in cur.fetchall():
            event_id, ctm_id_val, label, bucket_key, count, date, first_seen = row

            # Fetch ALL titles for this event with dates
            cur.execute(
                """
                SELECT t.title_display, DATE(t.pubdate_utc)
                FROM event_v3_titles evt
                JOIN titles_v3 t ON evt.title_id = t.id
                WHERE evt.event_id = %s
                ORDER BY t.pubdate_utc DESC
                """,
                (event_id,),
            )
            rows = cur.fetchall()
            titles = [r[0] for r in rows]
            dates = [r[1] for r in rows if r[1]]

            # Get backbone signals
            backbone = get_backbone_signals(conn, event_id)

            # Get per-title signals for outlier detection
            title_signals = get_title_signals(conn, event_id)

            events.append(
                {
                    "id": event_id,
                    "ctm_id": ctm_id_val,
                    "label": label,
                    "bucket_key": bucket_key,
                    "count": count or len(titles),
                    "titles": titles,
                    "date": date,
                    "first_seen": first_seen,
                    "title_dates": dates,
                    "backbone_signals": backbone,
                    "title_signals": title_signals,
                }
            )

        return events


def extract_json_from_response(text: str) -> dict:
    """Extract JSON object from LLM response."""
    # Try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try markdown code block
    patterns = [
        r"```json\s*(.*?)\s*```",
        r"```\s*(.*?)\s*```",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue

    # Try to find JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError("No valid JSON found in response")


async def generate_event_data(
    titles: list,
    backbone_signals: dict,
    title_signals: dict,
    num_titles: int,
    max_titles: int = 200,
) -> dict:
    """Generate title and summary for an event cluster.

    Args:
        titles: List of headline strings
        backbone_signals: Dict with persons, orgs, etc. from clustering
        title_signals: Dict mapping title_id to signals for outlier detection
        num_titles: Total number of titles (for context)
        max_titles: Maximum titles to send to LLM (default 200)
    """
    # Filter out outlier titles that don't share core signals
    core_titles, outlier_titles = filter_outlier_titles(
        titles, title_signals, backbone_signals, min_core_freq=3
    )

    # Use core titles for summary, but note if outliers exist
    titles_to_use = core_titles if core_titles else titles
    titles_sample = titles_to_use[:max_titles]
    titles_text = "\n".join("- %s" % t for t in titles_sample)

    if len(titles_to_use) > max_titles:
        titles_text += "\n... and %d more headlines" % (len(titles_to_use) - max_titles)

    # Note outliers filtered
    outlier_note = ""
    if outlier_titles and len(outlier_titles) <= 5:
        outlier_note = "\n\n(Note: %d off-topic headlines were filtered out)" % len(
            outlier_titles
        )
    elif outlier_titles:
        outlier_note = "\n\n(Note: %d off-topic headlines were filtered out)" % len(
            outlier_titles
        )

    # Format backbone signals for prompt
    backbone_text = format_backbone_signals(backbone_signals)

    user_prompt = EVENT_SUMMARY_USER_PROMPT.format(
        num_titles=len(titles_to_use),  # Use filtered count
        titles_text=titles_text + outlier_note,
        backbone_signals=backbone_text,
    )

    headers = {
        "Authorization": "Bearer %s" % config.deepseek_api_key,
        "Content-Type": "application/json",
    }

    # Scale max_tokens based on topic size
    if num_titles < 20:
        max_tokens = 300
    elif num_titles < 100:
        max_tokens = 500
    else:
        max_tokens = 800

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": EVENT_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.4,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            "%s/chat/completions" % config.deepseek_api_url,
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(
                "LLM API error: %d - %s" % (response.status_code, response.text)
            )

        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

        result = extract_json_from_response(content)

        # Validate
        title = result.get("title", "").strip()
        summary = result.get("summary", "").strip()

        return {
            "title": title,
            "summary": summary,
        }


async def process_event(
    semaphore: asyncio.Semaphore,
    conn,
    event: dict,
) -> bool:
    """Process a single event with semaphore for concurrency control."""
    async with semaphore:
        try:
            if not event["titles"]:
                print("  Skipping %s: no titles" % event["id"][:8])
                return False

            backbone = event.get("backbone_signals", {})
            title_signals = event.get("title_signals", {})

            result = await generate_event_data(
                event["titles"],
                backbone,
                title_signals,
                event["count"],
            )

            title = result["title"]
            summary = result["summary"]

            # Derive tags from backbone signals (the actual clustering anchors)
            tags = signals_to_tags(backbone, min_freq=2)

            # Calculate date range from titles
            title_dates = event.get("title_dates", [])
            if title_dates:
                first_seen = min(title_dates)
                last_seen = max(title_dates)
            else:
                first_seen = event.get("first_seen") or event.get("date")
                last_seen = event.get("date")

            # Update event with all fields
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE events_v3
                    SET title = %s,
                        summary = %s,
                        tags = %s,
                        first_seen = %s,
                        date = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (title, summary, tags, first_seen, last_seen, event["id"]),
                )
            conn.commit()

            # Print summary preview (first 100 chars)
            summary_preview = summary.replace("\n", " ")[:100]
            print("  [%3d] %s" % (event["count"], title[:60]))
            print("        %s..." % summary_preview)
            print("        tags: %s" % tags[:5])

            return True

        except Exception as e:
            print("  X Error for %s: %s" % (event["id"][:8], e))
            conn.rollback()
            return False


async def process_events(
    max_events: int = None,
    ctm_id: str = None,
    centroid_id: str = None,
    track: str = None,
    concurrency: int = 5,
    domestic_only: bool = False,
    bilateral_only: bool = False,
    force_regenerate: bool = False,
):
    """Process events to generate title, summary, and tags."""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        events = get_events_needing_summaries(
            conn,
            max_events,
            ctm_id,
            centroid_id,
            track=track,
            domestic_only=domestic_only,
            bilateral_only=bilateral_only,
            force_regenerate=force_regenerate,
        )

        if not events:
            print("No events need processing.")
            return

        filter_desc = []
        if domestic_only:
            filter_desc.append("domestic")
        if bilateral_only:
            filter_desc.append("bilateral")
        if force_regenerate:
            filter_desc.append("force")
        filter_str = " (%s)" % ", ".join(filter_desc) if filter_desc else ""

        # Group events by CTM for ordered processing
        ctm_groups = {}
        for event in events:
            cid = event["ctm_id"]
            if cid not in ctm_groups:
                ctm_groups[cid] = []
            ctm_groups[cid].append(event)

        ctm_count = len(ctm_groups)
        print(
            "Processing %d events across %d CTMs%s (concurrency: %d)...\n"
            % (len(events), ctm_count, filter_str, concurrency)
        )

        semaphore = asyncio.Semaphore(concurrency)

        # Process CTM-by-CTM: complete one CTM before starting the next
        results = []
        for ctm_idx, (ctm_id_key, ctm_events) in enumerate(ctm_groups.items(), 1):
            # Look up centroid/track for logging
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT centroid_id, track FROM ctm WHERE id = %s",
                    (ctm_id_key,),
                )
                row = cur.fetchone()
            ctm_label = "%s / %s" % (row[0], row[1]) if row else ctm_id_key[:8]

            print(
                "[CTM %d/%d] %s (%d events)"
                % (ctm_idx, ctm_count, ctm_label, len(ctm_events))
            )

            tasks = [process_event(semaphore, conn, event) for event in ctm_events]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)

        success = sum(1 for r in results if r is True)
        errors = len(results) - success

        print("")
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        print("Total events:  %d" % len(events))
        print("Processed:     %d" % success)
        print("Errors:        %d" % errors)

    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 4.5a: Generate title, summary, and tags for events"
    )
    parser.add_argument(
        "--max-events", type=int, help="Maximum number of events to process"
    )
    parser.add_argument(
        "--ctm-id", type=str, help="Process events for specific CTM only"
    )
    parser.add_argument(
        "--centroid",
        type=str,
        help="Process events for specific centroid (e.g., AMERICAS-USA)",
    )
    parser.add_argument(
        "--track",
        type=str,
        help="Process events for specific track (e.g., geo_economy)",
    )
    parser.add_argument(
        "--concurrency", type=int, default=5, help="Number of concurrent LLM calls"
    )
    parser.add_argument(
        "--domestic-only",
        action="store_true",
        help="Only process domestic topics (bucket_key IS NULL)",
    )
    parser.add_argument(
        "--bilateral-only",
        action="store_true",
        help="Only process bilateral topics (bucket_key IS NOT NULL)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regenerate even if summary exists",
    )

    args = parser.parse_args()

    asyncio.run(
        process_events(
            max_events=args.max_events,
            ctm_id=args.ctm_id,
            centroid_id=args.centroid,
            track=args.track,
            concurrency=args.concurrency,
            domestic_only=args.domestic_only,
            bilateral_only=args.bilateral_only,
            force_regenerate=args.force,
        )
    )
