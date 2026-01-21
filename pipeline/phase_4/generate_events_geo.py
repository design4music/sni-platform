"""
Phase 4 Geo-Aware Event Generation

Processes geo CTMs using mechanical pre-clustering with alias-based sub-groups:
- Bilateral buckets: USA-China, USA-Iran, etc.
- Other International: titles outside top 15 bilateral
- Domestic: titles with no other geo centroids

Within each bucket:
- Systemic sub-groups (SYS-TRADE, SYS-TECH, etc.) become mechanical events
- Only untagged titles get LLM extraction

This reduces LLM calls by ~40% while guaranteeing 100% coverage.
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx
import psycopg2
from psycopg2.extras import Json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os

project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)

from core.config import config  # noqa: E402
from pipeline.phase_4.generate_events_digest import (  # noqa: E402
    mechanical_merge_overlapping_events, validate_and_fix_event_date)
from pipeline.phase_4.geo_precluster import BucketSubgroups  # noqa: E402
from pipeline.phase_4.geo_precluster import precluster_geo_ctm  # noqa: E402


def create_alias_events(
    subgroups: BucketSubgroups,
    title_data: dict[str, tuple],
    bucket_type: str,
    bucket_key: str = None,
    bucket_label: str = "",
) -> list:
    """
    Create mechanical events for alias-based sub-groups (no LLM needed).

    Each alias group becomes ONE event with all its titles.

    Args:
        subgroups: BucketSubgroups with by_alias and untagged
        title_data: {title_id: (title_text, pubdate)} for date extraction
        bucket_type: 'bilateral', 'other_international', or 'domestic'
        bucket_key: For bilateral, the counterparty ID
        bucket_label: Human-readable label for the bucket

    Returns:
        List of mechanical event dicts
    """
    events = []

    for alias, title_ids in subgroups.by_alias.items():
        if not title_ids:
            continue

        # Format alias for display (capitalize)
        alias_label = alias.title()

        # Get date range from titles
        dates = [title_data[tid][1] for tid in title_ids if tid in title_data]
        if dates:
            latest_date = max(dates).strftime("%Y-%m-%d")
        else:
            latest_date = "2026-01-01"

        # Build summary
        if bucket_type == "bilateral" and bucket_label:
            summary = f"[{alias_label}] {bucket_label} - {len(title_ids)} sources"
        elif bucket_type == "domestic":
            summary = f"[{alias_label}] Domestic - {len(title_ids)} sources"
        else:
            summary = f"[{alias_label}] International - {len(title_ids)} sources"

        events.append(
            {
                "date": latest_date,
                "summary": summary,
                "source_title_ids": list(title_ids),
                "date_confidence": "mechanical",
                "event_type": bucket_type,
                "bucket_key": bucket_key,
                "is_alias_group": True,
                "alias": alias,
            }
        )

    return events


async def extract_bucket_events(
    centroid_label: str,
    track: str,
    month: str,
    titles: list,
    bucket_type: str,
    bucket_key: str = None,
) -> list:
    """
    Extract events from a pre-clustered bucket with 100% coverage guarantee.

    All titles in the bucket are mechanically assigned. LLM groups some into
    events, and ungrouped titles go into a "Storyline" pseudo-event.

    Args:
        centroid_label: Main centroid label (e.g., "United States")
        track: Track category
        month: Month string (YYYY-MM)
        titles: List of (title_id, title_text, pubdate) tuples
        bucket_type: 'bilateral', 'multilateral', or 'domestic'
        bucket_key: For bilateral, the counterparty centroid ID

    Returns:
        List of event dicts with event_type and bucket_key added
    """
    if not titles:
        return []

    all_title_ids = {str(t[0]) for t in titles}

    # Build context string based on bucket type
    if bucket_type == "bilateral":
        context = f"Bilateral relations between {centroid_label} and {bucket_key}"
        bucket_label = (
            bucket_key.replace("-", " ").split()[-1] if bucket_key else "bilateral"
        )
    elif bucket_type == "multilateral":
        context = (
            f"Multilateral events involving {centroid_label} and multiple countries"
        )
        bucket_label = "multilateral"
    else:
        context = f"Domestic {track} events in {centroid_label}"
        bucket_label = "domestic"

    # For large buckets, batch the LLM calls
    batch_size = config.v3_p4_batch_size
    all_events = []

    if len(titles) <= batch_size:
        batches = [titles]
    else:
        batches = [
            titles[i : i + batch_size] for i in range(0, len(titles), batch_size)
        ]
        print(f"      Splitting {len(titles)} titles into {len(batches)} batches")

    for batch_idx, batch_titles in enumerate(batches):
        # Format titles for LLM
        titles_text = "\n".join(
            [
                f"[{i}] {pubdate.strftime('%Y-%m-%d')}: {text}"
                for i, (_, text, pubdate) in enumerate(batch_titles)
            ]
        )

        system_prompt = f"""You are extracting {bucket_type} events for: {context}

RULES:
1. ONE EVENT = ONE THEME - each event describes one development thread
2. MINIMUM 2 SOURCES - except for policy decisions, legal actions, diplomatic moves
3. Group related titles into events. Ungrouped titles will be shown separately.

Return ONLY a JSON array:
[{{
  "date": "YYYY-MM-DD",
  "summary": "1-2 sentence event description",
  "source_title_indices": [0, 1, 2]
}}]

Keep summaries concise and factual."""

        user_prompt = f"""Track: {track}
Month: {month}
Bucket: {bucket_type}

Titles ({len(batch_titles)} total):
{titles_text}

Extract events:"""

        headers = {
            "Authorization": f"Bearer {config.deepseek_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": config.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
        }

        try:
            async with httpx.AsyncClient(timeout=config.llm_timeout_seconds) as client:
                response = await client.post(
                    f"{config.deepseek_api_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    print(
                        f"      Batch {batch_idx + 1}: LLM error {response.status_code}"
                    )
                    continue

                data = response.json()
                events_json = data["choices"][0]["message"]["content"].strip()

                # Strip markdown code fences
                if events_json.startswith("```"):
                    events_json = events_json.split("```")[1]
                    if events_json.startswith("json"):
                        events_json = events_json[4:]
                    events_json = events_json.strip()

                events = json.loads(events_json)

                # Convert indices to UUIDs
                for event in events:
                    indices = (
                        event.get("source_title_indices")
                        or event.get("source_indices")
                        or event.get("title_indices")
                        or event.get("sources")
                        or []
                    )

                    title_ids = [
                        str(batch_titles[idx][0])
                        for idx in indices
                        if isinstance(idx, int) and idx < len(batch_titles)
                    ]

                    if not title_ids:
                        continue

                    fixed_date, confidence = validate_and_fix_event_date(
                        event["date"], month
                    )

                    all_events.append(
                        {
                            "date": fixed_date,
                            "summary": event["summary"],
                            "source_title_ids": title_ids,
                            "date_confidence": confidence,
                            "event_type": bucket_type,
                            "bucket_key": bucket_key,
                        }
                    )

                if len(batches) > 1:
                    print(
                        f"        Batch {batch_idx + 1}/{len(batches)}: {len(events)} events"
                    )

        except (json.JSONDecodeError, KeyError) as e:
            print(f"      Batch {batch_idx + 1}: Parse error {e}")
            continue

    # Mechanical merge for overlapping events
    if len(all_events) > 1:
        merged = mechanical_merge_overlapping_events(all_events)
        if len(merged) < len(all_events):
            print(f"      Merged {len(all_events)} -> {len(merged)} events")
        all_events = merged

    # Find ungrouped titles and create Storyline pseudo-event
    grouped_title_ids = set()
    for event in all_events:
        grouped_title_ids.update(event["source_title_ids"])

    ungrouped_title_ids = all_title_ids - grouped_title_ids

    if ungrouped_title_ids:
        # Get the latest date from ungrouped titles
        ungrouped_dates = [t[2] for t in titles if str(t[0]) in ungrouped_title_ids]
        latest_date = (
            max(ungrouped_dates).strftime("%Y-%m-%d")
            if ungrouped_dates
            else month + "-01"
        )

        all_events.append(
            {
                "date": latest_date,
                "summary": f"[Storyline] Other {bucket_label} coverage",
                "source_title_ids": list(ungrouped_title_ids),
                "date_confidence": "low",
                "event_type": bucket_type,
                "bucket_key": bucket_key,
                "is_storyline": True,
            }
        )
        print(f"      Storyline: {len(ungrouped_title_ids)} ungrouped titles")

    return all_events


async def consolidate_domestic_events(
    centroid_label: str,
    track: str,
    month: str,
    all_events: list,
) -> list:
    """Consolidate domestic events from multiple batches."""
    if len(all_events) <= 10:
        return all_events

    # Format events for consolidation
    events_text = "\n".join(
        [
            f"[{i}] {event['date']}: {event['summary'][:100]} ({len(event['source_title_ids'])} sources)"
            for i, event in enumerate(all_events)
        ]
    )

    system_prompt = """Consolidate events from multiple batches into a deduplicated timeline.

RULES:
1. AGGRESSIVE MERGING - same action/actors/timeframe = same event
2. ONE EVENT = ONE THEME
3. PRESERVE "Other events" bucket - merge all into ONE
4. 100% COVERAGE - every index must appear exactly once

Return JSON array:
[{
  "date": "YYYY-MM-DD",
  "summary": "Consolidated description",
  "source_event_indices": [0, 1, 2]
}]"""

    user_prompt = f"""Centroid: {centroid_label}
Track: {track}
Month: {month}

Events to consolidate ({len(all_events)} total):
{events_text}

Consolidate:"""

    headers = {
        "Authorization": f"Bearer {config.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 3000,
    }

    async with httpx.AsyncClient(timeout=config.llm_timeout_seconds) as client:
        response = await client.post(
            f"{config.deepseek_api_url}/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            print(f"  Consolidation failed: {response.status_code}")
            return all_events

        data = response.json()
        cons_json = data["choices"][0]["message"]["content"].strip()

        if cons_json.startswith("```"):
            cons_json = cons_json.split("```")[1]
            if cons_json.startswith("json"):
                cons_json = cons_json[4:]
            cons_json = cons_json.strip()

        try:
            consolidated = json.loads(cons_json)

            final_events = []
            for event in consolidated:
                combined_titles = []
                for idx in event["source_event_indices"]:
                    if idx < len(all_events):
                        combined_titles.extend(all_events[idx]["source_title_ids"])

                fixed_date, confidence = validate_and_fix_event_date(
                    event["date"], month
                )

                final_events.append(
                    {
                        "date": fixed_date,
                        "summary": event["summary"],
                        "source_title_ids": list(set(combined_titles)),
                        "date_confidence": confidence,
                        "event_type": "domestic",
                        "bucket_key": None,
                    }
                )

            return final_events

        except json.JSONDecodeError:
            return all_events


async def extract_domestic_events(
    centroid_label: str,
    track: str,
    month: str,
    titles: list,
) -> list:
    """
    Extract events from domestic bucket with 100% coverage guarantee.

    Domestic titles get special handling:
    - More lenient singleton rules
    - Consolidation pass for high-volume buckets
    - Storyline pseudo-event for ungrouped titles
    """
    if not titles:
        return []

    all_title_ids = {str(t[0]) for t in titles}
    batch_size = config.v3_p4_batch_size

    # Single batch
    if len(titles) <= batch_size:
        events = await extract_domestic_single_batch(
            centroid_label, track, month, titles
        )
        for event in events:
            event["event_type"] = "domestic"
            event["bucket_key"] = None
    else:
        # Multi-batch with consolidation
        all_events = []
        num_batches = (len(titles) + batch_size - 1) // batch_size

        print(
            f"      Domestic: splitting {len(titles)} titles into {num_batches} batches"
        )

        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(titles))
            batch_titles = titles[start_idx:end_idx]

            batch_events = await extract_domestic_single_batch(
                centroid_label, track, month, batch_titles
            )
            all_events.extend(batch_events)
            print(
                f"        Batch {batch_num + 1}/{num_batches}: {len(batch_events)} events"
            )

        print(f"      Total from batches: {len(all_events)} events")

        # Mechanical merge first
        merged = mechanical_merge_overlapping_events(all_events)
        if len(merged) < len(all_events):
            print(f"      After mechanical merge: {len(merged)} events")

        # LLM consolidation if still too many
        if len(merged) > 30:
            print("      Running consolidation pass...")
            events = await consolidate_domestic_events(
                centroid_label, track, month, merged
            )
            print(f"      After consolidation: {len(events)} events")
        else:
            events = merged

        # Add event_type metadata
        for event in events:
            event["event_type"] = "domestic"
            event["bucket_key"] = None

    # Find ungrouped titles and create Storyline pseudo-event
    grouped_title_ids = set()
    for event in events:
        grouped_title_ids.update(event.get("source_title_ids", []))

    ungrouped_title_ids = all_title_ids - grouped_title_ids

    if ungrouped_title_ids:
        # Get the latest date from ungrouped titles
        ungrouped_dates = [t[2] for t in titles if str(t[0]) in ungrouped_title_ids]
        latest_date = (
            max(ungrouped_dates).strftime("%Y-%m-%d")
            if ungrouped_dates
            else month + "-01"
        )

        events.append(
            {
                "date": latest_date,
                "summary": "[Storyline] Other domestic coverage",
                "source_title_ids": list(ungrouped_title_ids),
                "date_confidence": "low",
                "event_type": "domestic",
                "bucket_key": None,
                "is_storyline": True,
            }
        )
        print(f"      Storyline: {len(ungrouped_title_ids)} ungrouped titles")

    return events


async def extract_domestic_single_batch(
    centroid_label: str,
    track: str,
    month: str,
    titles: list,
) -> list:
    """Extract domestic events with Other bucket."""

    titles_text = "\n".join(
        [
            f"[{i}] {pubdate.strftime('%Y-%m-%d')}: {text}"
            for i, (_, text, pubdate) in enumerate(titles)
        ]
    )

    system_prompt = f"""You are extracting domestic {track} events for {centroid_label}.

RULES:
1. ONE EVENT = ONE THEME
2. MINIMUM 2 SOURCES (except policy/legal/diplomatic)
3. MANDATORY "OTHER" BUCKET - create exactly ONE event with summary "OTHER" for:
   - Celebrity/entertainment
   - Pure opinion without news
   - Isolated local items
   - Anything not fitting a strategic theme
4. 100% COVERAGE

Return JSON array:
[{{
  "date": "YYYY-MM-DD",
  "summary": "Description OR 'OTHER'",
  "source_title_indices": [0, 1, 2]
}}]"""

    user_prompt = f"""Track: {track}
Month: {month}

Titles ({len(titles)}):
{titles_text}

Extract events:"""

    headers = {
        "Authorization": f"Bearer {config.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    async with httpx.AsyncClient(timeout=config.llm_timeout_seconds) as client:
        response = await client.post(
            f"{config.deepseek_api_url}/chat/completions",
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            raise Exception(f"LLM API error: {response.status_code}")

        data = response.json()
        events_json = data["choices"][0]["message"]["content"].strip()

        if events_json.startswith("```"):
            events_json = events_json.split("```")[1]
            if events_json.startswith("json"):
                events_json = events_json[4:]
            events_json = events_json.strip()

        try:
            events = json.loads(events_json)

            enriched = []
            for event in events:
                # Handle common key variations
                indices = (
                    event.get("source_title_indices")
                    or event.get("source_indices")
                    or event.get("title_indices")
                    or event.get("sources")
                    or []
                )

                title_ids = [
                    str(titles[idx][0])
                    for idx in indices
                    if isinstance(idx, int) and idx < len(titles)
                ]

                fixed_date, confidence = validate_and_fix_event_date(
                    event["date"], month
                )

                summary = event["summary"]
                if summary.upper() == "OTHER":
                    summary = f"{centroid_label} / {track} - Other events"

                enriched.append(
                    {
                        "date": fixed_date,
                        "summary": summary,
                        "source_title_ids": title_ids,
                        "date_confidence": confidence,
                        "event_type": "domestic",
                        "bucket_key": None,
                    }
                )

            return enriched

        except (json.JSONDecodeError, KeyError) as e:
            print(f"    Parse error: {e}")
            return []


def write_events_to_v3_with_buckets(
    conn, ctm_id: str, events: list, batch_count: int = 1
) -> int:
    """
    Write events to v3 tables with bucket metadata.

    Similar to write_events_to_v3_tables but includes event_type and bucket_key.
    """
    if not events:
        return 0

    events_written = 0

    with conn.cursor() as cur:
        # Delete existing events for this CTM
        cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))

        for event in events:
            cur.execute(
                """
                INSERT INTO events_v3 (
                    ctm_id, date, summary, date_confidence,
                    source_batch_count, event_type, bucket_key
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    ctm_id,
                    event["date"],
                    event["summary"],
                    event.get("date_confidence", "high"),
                    batch_count,
                    event.get("event_type"),
                    event.get("bucket_key"),
                ),
            )

            event_id = cur.fetchone()[0]
            events_written += 1

            # Write title associations
            for title_id in event["source_title_ids"]:
                cur.execute(
                    """
                    INSERT INTO event_v3_titles (event_id, title_id, added_from_batch)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (event_id, title_id) DO NOTHING
                    """,
                    (event_id, title_id, batch_count),
                )

    return events_written


async def process_geo_ctm(
    ctm_id: str,
    centroid_id: str,
    centroid_label: str,
    track: str,
    month: str,
    conn=None,
) -> tuple[list, int]:
    """
    Process a geo CTM using pre-clustering with alias-based sub-groups.

    Strategy:
    - Systemic-tagged titles -> mechanical events (no LLM)
    - Untagged titles -> LLM extraction

    Returns:
        (events, bucket_count) tuple
    """
    close_conn = False
    if conn is None:
        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
        )
        close_conn = True

    try:
        # Pre-cluster titles with alias-based sub-groups
        precluster = precluster_geo_ctm(ctm_id, conn=conn)
        print(
            f"  Pre-cluster: {len(precluster.top_bilaterals)} bilateral, "
            f"{len(precluster.other_international)} other intl, "
            f"{len(precluster.domestic)} domestic"
        )

        all_events = []
        bucket_count = 0

        # Fetch ALL title data upfront for mechanical events
        with conn.cursor() as cur:
            # Get all title IDs from all buckets
            all_title_ids = []
            for title_ids in precluster.bilaterals.values():
                all_title_ids.extend(title_ids)
            all_title_ids.extend(precluster.other_international)
            all_title_ids.extend(precluster.domestic)

            if not all_title_ids:
                return [], 0

            cur.execute(
                """
                SELECT id, title_display, pubdate_utc
                FROM titles_v3
                WHERE id = ANY(%s::uuid[])
                """,
                (all_title_ids,),
            )
            rows = cur.fetchall()
            # Build lookup: {title_id_str: (title_text, pubdate)}
            title_data = {str(r[0]): (r[1], r[2]) for r in rows}

            # Process bilateral buckets
            for counterparty in precluster.top_bilaterals:
                title_ids = precluster.bilaterals[counterparty]
                subgroups = precluster.bilateral_subgroups.get(counterparty)

                # Extract country name for label
                bucket_label = (
                    counterparty.split("-")[-1] if counterparty else "bilateral"
                )

                # Count alias vs untagged
                alias_count = (
                    sum(len(t) for t in subgroups.by_alias.values()) if subgroups else 0
                )
                untagged_count = (
                    len(subgroups.untagged) if subgroups else len(title_ids)
                )

                print(
                    f"    Bilateral {counterparty}: {len(title_ids)} titles "
                    f"({alias_count} alias, {untagged_count} untagged)"
                )

                bucket_events = []

                # Create mechanical events for alias sub-groups
                if subgroups and subgroups.by_alias:
                    sys_events = create_alias_events(
                        subgroups,
                        title_data,
                        bucket_type="bilateral",
                        bucket_key=counterparty,
                        bucket_label=bucket_label,
                    )
                    bucket_events.extend(sys_events)
                    if sys_events:
                        print(f"      Mechanical: {len(sys_events)} alias events")

                # LLM extraction for untagged titles only
                if subgroups and subgroups.untagged:
                    untagged_ids = subgroups.untagged
                    # Build titles list for LLM
                    titles = [
                        (tid, title_data[tid][0], title_data[tid][1])
                        for tid in untagged_ids
                        if tid in title_data
                    ]
                    if titles:
                        llm_events = await extract_bucket_events(
                            centroid_label,
                            track,
                            month,
                            titles,
                            bucket_type="bilateral",
                            bucket_key=counterparty,
                        )
                        bucket_events.extend(llm_events)
                        print(
                            f"      LLM: {len(llm_events)} events from {len(titles)} untagged"
                        )

                all_events.extend(bucket_events)
                bucket_count += 1
                print(f"      -> {len(bucket_events)} total events")

            # Process other_international bucket
            if precluster.other_international:
                subgroups = precluster.other_intl_subgroups
                alias_count = (
                    sum(len(t) for t in subgroups.by_alias.values()) if subgroups else 0
                )
                untagged_count = (
                    len(subgroups.untagged)
                    if subgroups
                    else len(precluster.other_international)
                )

                print(
                    f"    Other International: {len(precluster.other_international)} titles "
                    f"({alias_count} alias, {untagged_count} untagged)"
                )

                bucket_events = []

                # Mechanical events for alias sub-groups
                if subgroups and subgroups.by_alias:
                    sys_events = create_alias_events(
                        subgroups,
                        title_data,
                        bucket_type="other_international",
                        bucket_key=None,
                        bucket_label="International",
                    )
                    bucket_events.extend(sys_events)
                    if sys_events:
                        print(f"      Mechanical: {len(sys_events)} alias events")

                # LLM for untagged
                if subgroups and subgroups.untagged:
                    titles = [
                        (tid, title_data[tid][0], title_data[tid][1])
                        for tid in subgroups.untagged
                        if tid in title_data
                    ]
                    if titles:
                        llm_events = await extract_bucket_events(
                            centroid_label,
                            track,
                            month,
                            titles,
                            bucket_type="other_international",
                            bucket_key=None,
                        )
                        bucket_events.extend(llm_events)
                        print(
                            f"      LLM: {len(llm_events)} events from {len(titles)} untagged"
                        )

                all_events.extend(bucket_events)
                bucket_count += 1
                print(f"      -> {len(bucket_events)} total events")

            # Process domestic bucket
            if precluster.domestic:
                subgroups = precluster.domestic_subgroups
                alias_count = (
                    sum(len(t) for t in subgroups.by_alias.values()) if subgroups else 0
                )
                untagged_count = (
                    len(subgroups.untagged) if subgroups else len(precluster.domestic)
                )

                print(
                    f"    Domestic: {len(precluster.domestic)} titles "
                    f"({alias_count} alias, {untagged_count} untagged)"
                )

                bucket_events = []

                # Mechanical events for alias sub-groups
                if subgroups and subgroups.by_alias:
                    sys_events = create_alias_events(
                        subgroups,
                        title_data,
                        bucket_type="domestic",
                        bucket_key=None,
                        bucket_label="Domestic",
                    )
                    bucket_events.extend(sys_events)
                    if sys_events:
                        print(f"      Mechanical: {len(sys_events)} alias events")

                # LLM for untagged domestic titles
                if subgroups and subgroups.untagged:
                    titles = [
                        (tid, title_data[tid][0], title_data[tid][1])
                        for tid in subgroups.untagged
                        if tid in title_data
                    ]
                    if titles:
                        llm_events = await extract_domestic_events(
                            centroid_label,
                            track,
                            month,
                            titles,
                        )
                        bucket_events.extend(llm_events)
                        print(
                            f"      LLM: {len(llm_events)} events from {len(titles)} untagged"
                        )

                all_events.extend(bucket_events)
                bucket_count += 1
                print(f"      -> {len(bucket_events)} total events")

        return all_events, bucket_count

    finally:
        if close_conn:
            conn.close()


async def test_geo_ctm(
    centroid_id: str = "AMERICAS-USA",
    track: str = "geo_economy",
    save: bool = False,
):
    """Test geo CTM processing with pre-clustering."""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        with conn.cursor() as cur:
            # Find latest CTM for centroid/track
            cur.execute(
                """
                SELECT c.id, c.month, c.title_count, cent.label
                FROM ctm c
                JOIN centroids_v3 cent ON c.centroid_id = cent.id
                WHERE c.centroid_id = %s AND c.track = %s
                ORDER BY c.month DESC LIMIT 1
                """,
                (centroid_id, track),
            )
            row = cur.fetchone()

            if not row:
                print(f"No CTM found for {centroid_id}/{track}")
                return

            ctm_id, month, title_count, centroid_label = row
            month_str = month.strftime("%Y-%m")

            print("=" * 60)
            print("Testing geo pre-cluster extraction")
            print("=" * 60)
            print(f"Centroid: {centroid_label} ({centroid_id})")
            print(f"Track: {track}")
            print(f"Month: {month_str}")
            print(f"Titles: {title_count}")
            print("=" * 60)
            print()

            # Process with pre-clustering
            events, bucket_count = await process_geo_ctm(
                ctm_id, centroid_id, centroid_label, track, month_str, conn=conn
            )

            print()
            print("=" * 60)
            print("RESULTS")
            print("=" * 60)
            print(f"Buckets processed: {bucket_count}")
            print(f"Total events: {len(events)}")
            print()

            # Count by type
            by_type = {}
            for event in events:
                t = event.get("event_type", "unknown")
                by_type[t] = by_type.get(t, 0) + 1

            print("Events by type:")
            for t, count in sorted(by_type.items()):
                print(f"  {t}: {count}")
            print()

            # Show sample events (first 20)
            print("Sample events (first 20):")
            for i, event in enumerate(events[:20]):
                bucket_info = event.get("bucket_key") or event.get("event_type")
                summary_safe = (
                    event["summary"][:80].encode("ascii", "replace").decode("ascii")
                )
                print(f"  [{i+1}] {event['date']} ({bucket_info})")
                print(f"      {summary_safe}...")
                print(f"      Sources: {len(event['source_title_ids'])}")
            if len(events) > 20:
                print(f"  ... and {len(events) - 20} more events")
            print()

            # Count total titles covered
            all_title_ids = set()
            for event in events:
                all_title_ids.update(event["source_title_ids"])
            print(f"Total titles covered: {len(all_title_ids)}")

            # Save if requested
            if save:
                # Write to v3 tables
                written = write_events_to_v3_with_buckets(
                    conn, ctm_id, events, bucket_count
                )

                # Also update JSONB with full metadata for frontend
                jsonb_events = [
                    {
                        "date": e["date"],
                        "summary": e["summary"],
                        "source_title_ids": e["source_title_ids"],
                        "event_type": e.get("event_type"),
                        "bucket_key": e.get("bucket_key"),
                        "alias": e.get("alias"),
                        "is_alias_group": e.get("is_alias_group", False),
                    }
                    for e in events
                ]

                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE ctm
                        SET events_digest = %s, updated_at = NOW()
                        WHERE id = %s
                        """,
                        (Json(jsonb_events), ctm_id),
                    )

                conn.commit()
                print(f"Saved {written} events to v3 tables")

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test geo pre-cluster extraction")
    parser.add_argument("--centroid", default="AMERICAS-USA", help="Centroid ID")
    parser.add_argument("--track", default="geo_economy", help="Track")
    parser.add_argument("--save", action="store_true", help="Save results to database")

    args = parser.parse_args()

    asyncio.run(
        test_geo_ctm(centroid_id=args.centroid, track=args.track, save=args.save)
    )
