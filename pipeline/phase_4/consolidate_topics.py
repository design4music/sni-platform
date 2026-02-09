"""
Phase 4.1: LLM-Driven Topic Consolidation

Replaces the old multi-step aggregate_topics with ONE intelligent LLM call
per bucket that sees all topics + catchall and groups them into real stories.

Each story gets a topic_core -- a semantic essence that captures the story.

Usage:
    python pipeline/phase_4/consolidate_topics.py --ctm-id <uuid>
    python pipeline/phase_4/consolidate_topics.py --centroid EUROPE-RUSSIA --track geo_politics
    python pipeline/phase_4/consolidate_topics.py --ctm-id <uuid> --dry-run
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import httpx
import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from core.prompts import (
    TOPIC_CONSOLIDATION_SYSTEM_PROMPT,
    TOPIC_CONSOLIDATION_USER_PROMPT,
)


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def get_ctm_info(conn, ctm_id=None, centroid=None, track=None):
    """Get CTM info by ID or by centroid+track (most recent month)."""
    cur = conn.cursor()
    if ctm_id:
        cur.execute(
            """SELECT c.id, c.centroid_id, c.track, c.month, c.title_count
               FROM ctm c WHERE c.id = %s""",
            (ctm_id,),
        )
    else:
        cur.execute(
            """SELECT c.id, c.centroid_id, c.track, c.month, c.title_count
               FROM ctm c WHERE c.centroid_id = %s AND c.track = %s
               ORDER BY c.month DESC LIMIT 1""",
            (centroid, track),
        )
    row = cur.fetchone()
    if not row:
        return None
    # Get centroid label
    cur.execute("SELECT label FROM centroids_v3 WHERE id = %s", (row[1],))
    label_row = cur.fetchone()
    return {
        "id": row[0],
        "centroid_id": row[1],
        "track": row[2],
        "month": row[3],
        "title_count": row[4],
        "centroid_label": label_row[0] if label_row else row[1],
    }


def load_bucket_data(conn, ctm_id):
    """
    Load all events grouped by bucket with sample headlines.
    Uses (event_type, bucket_key) as grouping key to prevent domestic
    and other_international events (both bucket_key=NULL) from mixing.
    Returns: {bucket_key: {"events": [...], "catchall": {"id":..., "titles":[...]}}}
    """
    cur = conn.cursor()

    # Get all events (include event_type for proper grouping)
    cur.execute(
        """SELECT e.id, e.bucket_key, e.source_batch_count, e.is_catchall,
                  e.topic_core, e.event_type
           FROM events_v3 e
           WHERE e.ctm_id = %s
           ORDER BY e.source_batch_count DESC NULLS LAST""",
        (ctm_id,),
    )
    events_raw = cur.fetchall()

    if not events_raw:
        return {}

    # Collect event IDs for headline lookup
    event_ids = [r[0] for r in events_raw]

    # Get sample headlines per event (up to 5 for regular, up to 50 for catchall)
    cur.execute(
        """SELECT evt.event_id, t.title_display
           FROM event_v3_titles evt
           JOIN titles_v3 t ON t.id = evt.title_id
           WHERE evt.event_id = ANY(%s::uuid[])""",
        (event_ids,),
    )
    headlines_by_event = defaultdict(list)
    for event_id, title_display in cur.fetchall():
        headlines_by_event[event_id].append(title_display)

    # Group by bucket -- use event_type to distinguish domestic from other_international
    buckets = defaultdict(lambda: {"events": [], "catchall": None})
    for event_id, bucket_key, count, is_catchall, topic_core, event_type in events_raw:
        if bucket_key:
            bk = bucket_key  # bilateral: use the foreign centroid
        elif event_type == "other_international":
            bk = "__other_international__"
        else:
            bk = "__domestic__"

        headlines = headlines_by_event.get(event_id, [])

        if is_catchall:
            buckets[bk]["catchall"] = {
                "id": event_id,
                "titles": headlines[:50],
            }
        else:
            buckets[bk]["events"].append(
                {
                    "id": str(event_id),
                    "count": count or 0,
                    "headlines": headlines[:5],
                    "topic_core": topic_core,
                }
            )

    return dict(buckets)


def compute_target_guidance(is_domestic, total_titles):
    """
    Compute dynamic topic target range based on bucket type and size.
    Monthly maximums: domestic up to 10-15, bilateral up to 6-7.
    Early in month (fewer titles), targets scale down proportionally.
    """
    if is_domestic:
        # Domestic: scale from 2-4 (small) to 10-15 (large/end of month)
        if total_titles < 30:
            return "Target 2-4 stories"
        elif total_titles < 80:
            return "Target 4-7 stories"
        elif total_titles < 200:
            return "Target 6-10 stories"
        else:
            return "Target 8-15 stories"
    else:
        # Bilateral: scale from 2-3 (small) to 5-7 (large/end of month)
        if total_titles < 20:
            return "Target 2-3 stories"
        elif total_titles < 60:
            return "Target 3-5 stories"
        elif total_titles < 150:
            return "Target 4-6 stories"
        else:
            return "Target 5-7 stories"


def build_prompt(bucket_label, events, catchall_titles, ctm_info):
    """Build the user prompt for one bucket."""
    # Build topics text
    topics_lines = []
    total_titles = 0
    for i, ev in enumerate(events, 1):
        total_titles += ev["count"]
        topics_lines.append("T{} [{} titles] id={}".format(i, ev["count"], ev["id"]))
        max_headlines = 3 if len(events) > 20 else 5
        for h in ev["headlines"][:max_headlines]:
            safe_h = h[:100] if h else "[no title]"
            topics_lines.append("  - {}".format(safe_h))
        topics_lines.append("")

    topics_text = "\n".join(topics_lines)

    # Build catchall section
    if catchall_titles:
        total_titles += len(catchall_titles)
        catchall_lines = [
            "CATCHALL ({} unclustered titles):".format(len(catchall_titles))
        ]
        for i, t in enumerate(catchall_titles):
            safe_t = t[:100] if t else "[no title]"
            catchall_lines.append("C{}: {}".format(i, safe_t))
        catchall_section = "\n".join(catchall_lines)
    else:
        catchall_section = "CATCHALL: (none)"

    month_str = str(ctm_info["month"])[:7] if ctm_info["month"] else "unknown"
    is_domestic = bucket_label == "Domestic"
    guidance = compute_target_guidance(is_domestic, total_titles)

    return TOPIC_CONSOLIDATION_USER_PROMPT.format(
        centroid_label=ctm_info["centroid_label"],
        track=ctm_info["track"],
        month=month_str,
        bucket_label=bucket_label,
        total_titles=total_titles,
        topics_text=topics_text,
        catchall_section=catchall_section,
        target_guidance=guidance,
    )


def call_llm(system_prompt, user_prompt):
    """Call DeepSeek LLM and return parsed JSON response."""
    headers = {
        "Authorization": "Bearer {}".format(config.deepseek_api_key),
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 1000,
    }

    with httpx.Client(timeout=60) as client:
        response = client.post(
            "{}/chat/completions".format(config.deepseek_api_url),
            headers=headers,
            json=payload,
        )
        if response.status_code != 200:
            raise RuntimeError(
                "LLM API error: {} {}".format(response.status_code, response.text[:200])
            )

        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

    return extract_json(content)


def extract_json(text):
    """Extract JSON from LLM response."""
    # Try direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try markdown code block
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError("Failed to parse LLM response as JSON")


def repair_event_ids(response, valid_ids):
    """
    Fix LLM-corrupted UUIDs by fuzzy-matching against valid IDs.
    LLMs sometimes flip a character in long UUIDs.
    """
    valid_set = set(valid_ids)
    # Collect all IDs already correctly used so we don't double-map
    already_used = set()
    for story in response.get("stories", []):
        for eid in story.get("event_ids", []):
            if eid in valid_set:
                already_used.add(eid)

    for story in response.get("stories", []):
        repaired = []
        for eid in story.get("event_ids", []):
            if eid in valid_set:
                repaired.append(eid)
            else:
                # Find closest unused valid ID (minimum char diff, max 4)
                best = None
                best_diffs = 5
                for vid in valid_ids:
                    if vid in already_used:
                        continue
                    if len(vid) == len(eid):
                        diffs = sum(1 for a, b in zip(vid, eid) if a != b)
                        if diffs < best_diffs:
                            best = vid
                            best_diffs = diffs
                if best:
                    repaired.append(best)
                    already_used.add(best)
                else:
                    repaired.append(eid)  # keep as-is, validation will catch
        story["event_ids"] = repaired


def validate_response(response, event_ids, catchall_count):
    """
    Validate LLM response: every event_id must appear exactly once.
    Returns (is_valid, error_message).
    """
    stories = response.get("stories", [])
    if not stories:
        return False, "No stories in response"

    seen_ids = set()
    for story in stories:
        for eid in story.get("event_ids", []):
            if eid in seen_ids:
                return False, "Duplicate event_id: {}".format(eid)
            seen_ids.add(eid)

        # Validate catchall indices
        for ci in story.get("catchall_ids", []):
            if not isinstance(ci, int) or ci < 0 or ci >= catchall_count:
                return False, "Invalid catchall index: {}".format(ci)

    # Validate unmatched_catchall indices
    for ci in response.get("unmatched_catchall", []):
        if not isinstance(ci, int) or ci < 0 or ci >= catchall_count:
            return False, "Invalid unmatched_catchall index: {}".format(ci)

    expected = set(event_ids)
    if seen_ids != expected:
        missing = expected - seen_ids
        extra = seen_ids - expected
        if extra:
            return False, "Extra event IDs: {}".format(extra)
        if missing:
            # Auto-fix: put each missing ID into its own singleton story
            for mid in missing:
                response["stories"].append(
                    {
                        "topic_core": "",
                        "event_ids": [mid],
                        "catchall_ids": [],
                    }
                )
            return True, ""  # fixed

    return True, ""


def apply_consolidation(
    conn, stories, catchall_event_id, catchall_titles, ctm_id, bucket_key
):
    """
    Execute merges and set topic_core for one bucket.
    Returns stats dict.
    """
    cur = conn.cursor()
    stats = {"merged": 0, "rescued": 0, "rescue_skipped": 0, "deleted": 0, "created": 0}

    # For bilateral buckets, derive the DB bucket_key for centroid validation
    db_bucket = (
        None
        if bucket_key in ("__domestic__", "__other_international__")
        else bucket_key
    )

    for story in stories:
        event_ids = story.get("event_ids", [])
        topic_core = story.get("topic_core", "")
        catchall_ids = story.get("catchall_ids", [])

        if not event_ids and not catchall_ids:
            continue

        target_id = None

        if event_ids:
            # Find the largest event as merge target
            counts = []
            for eid in event_ids:
                cur.execute(
                    "SELECT source_batch_count FROM events_v3 WHERE id = %s",
                    (eid,),
                )
                row = cur.fetchone()
                counts.append((eid, row[0] if row else 0))
            counts.sort(key=lambda x: x[1], reverse=True)
            target_id = counts[0][0]
            source_ids = [c[0] for c in counts[1:]]

            # Merge sources into target
            for source_id in source_ids:
                cur.execute(
                    "UPDATE event_v3_titles SET event_id = %s WHERE event_id = %s",
                    (target_id, source_id),
                )
                cur.execute(
                    "DELETE FROM events_v3 WHERE id = %s",
                    (source_id,),
                )
                stats["merged"] += 1
                stats["deleted"] += 1

        elif catchall_ids and catchall_event_id:
            # No existing events -- create a new event from catchall titles
            db_bucket = (
                None
                if bucket_key in ("__domestic__", "__other_international__")
                else bucket_key
            )
            if bucket_key == "__domestic__":
                db_event_type = "domestic"
            elif bucket_key == "__other_international__":
                db_event_type = "other_international"
            else:
                db_event_type = "bilateral"
            cur.execute(
                """INSERT INTO events_v3
                   (ctm_id, date, summary, event_type, bucket_key,
                    is_catchall, topic_core, source_batch_count)
                   VALUES (%s, CURRENT_DATE, %s, %s, %s,
                           false, %s, 0)
                   RETURNING id""",
                (
                    ctm_id,
                    topic_core or "New topic",
                    db_event_type,
                    db_bucket,
                    topic_core,
                ),
            )
            target_id = cur.fetchone()[0]
            stats["created"] += 1

        # Rescue catchall titles into target
        if catchall_ids and catchall_event_id and catchall_titles and target_id:
            # Get actual title_ids from catchall event
            cur.execute(
                """SELECT evt.title_id, t.title_display
                   FROM event_v3_titles evt
                   JOIN titles_v3 t ON t.id = evt.title_id
                   WHERE evt.event_id = %s""",
                (catchall_event_id,),
            )
            catchall_rows = cur.fetchall()
            # Build index -> title_id mapping by matching title text
            # (catchall_titles list order = prompt order)
            catchall_title_to_id = {}
            for tid, tdisplay in catchall_rows:
                catchall_title_to_id[tdisplay] = tid

            for ci in catchall_ids:
                if 0 <= ci < len(catchall_titles):
                    title_text = catchall_titles[ci]
                    title_id = catchall_title_to_id.get(title_text)
                    if title_id:
                        # For bilateral events, verify title has the bucket centroid
                        if db_bucket:
                            cur.execute(
                                "SELECT %s = ANY(centroid_ids) FROM titles_v3 WHERE id = %s",
                                (db_bucket, title_id),
                            )
                            row = cur.fetchone()
                            if not row or not row[0]:
                                stats["rescue_skipped"] += 1
                                continue
                        cur.execute(
                            """UPDATE event_v3_titles
                               SET event_id = %s
                               WHERE title_id = %s AND event_id = %s""",
                            (target_id, title_id, catchall_event_id),
                        )
                        stats["rescued"] += 1

        # Update target count and set topic_core
        cur.execute(
            """UPDATE events_v3
               SET source_batch_count = (
                   SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
               ),
               topic_core = %s,
               updated_at = NOW()
               WHERE id = %s""",
            (target_id, topic_core, target_id),
        )

    # Update catchall count if any rescues happened
    if stats["rescued"] > 0 and catchall_event_id:
        cur.execute(
            """UPDATE events_v3
               SET source_batch_count = (
                   SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
               ),
               updated_at = NOW()
               WHERE id = %s""",
            (catchall_event_id, catchall_event_id),
        )

    return stats


def process_bucket(conn, ctm_info, bucket_key, bucket_data, dry_run=False):
    """Process one bucket: call LLM, validate, apply."""
    events = bucket_data["events"]
    catchall = bucket_data.get("catchall")

    # Skip conditions
    if len(events) <= 1 and (not catchall or len(catchall.get("titles", [])) < 5):
        return {"skipped": True, "reason": "too few events"}

    # Skip if all events already have topic_core
    if all(ev.get("topic_core") for ev in events):
        return {"skipped": True, "reason": "already consolidated"}

    if bucket_key == "__domestic__":
        bucket_label = "Domestic"
    elif bucket_key == "__other_international__":
        bucket_label = "Other International"
    else:
        bucket_label = bucket_key
    catchall_titles = catchall["titles"] if catchall else []

    # Build and send prompt
    user_prompt = build_prompt(bucket_label, events, catchall_titles, ctm_info)
    event_ids = [ev["id"] for ev in events]

    if dry_run:
        print(
            "  Bucket '{}': {} events, {} catchall titles".format(
                bucket_label, len(events), len(catchall_titles)
            )
        )
        print("  Prompt length: {} chars".format(len(user_prompt)))

    try:
        response = call_llm(TOPIC_CONSOLIDATION_SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        print("  LLM error for bucket '{}': {}".format(bucket_label, e))
        return {"skipped": True, "reason": "llm_error"}

    # Repair any corrupted UUIDs before validation
    repair_event_ids(response, event_ids)

    # Validate
    is_valid, error = validate_response(response, event_ids, len(catchall_titles))
    if not is_valid:
        print("  Validation error for bucket '{}': {}".format(bucket_label, error))
        return {"skipped": True, "reason": "validation_error: {}".format(error)}

    stories = response.get("stories", [])

    # Over-merge guard: if LLM returns 1 group for 10+ input topics, skip
    if len(stories) == 1 and len(events) >= 10:
        print("  Over-merge guard: 1 story for {} topics, skipping".format(len(events)))
        return {"skipped": True, "reason": "over_merge_guard"}

    if dry_run:
        print("  LLM returned {} stories:".format(len(stories)))
        for s in stories:
            print(
                "    [{}] {} (events: {}, catchall: {})".format(
                    s.get("topic_core", "?"),
                    len(s.get("event_ids", [])),
                    ", ".join(s.get("event_ids", [])[:3]),
                    len(s.get("catchall_ids", [])),
                )
            )
        unmatched = response.get("unmatched_catchall", [])
        print("  Unmatched catchall: {}".format(len(unmatched)))
        return {
            "skipped": False,
            "stories": len(stories),
            "input_events": len(events),
        }

    # Apply in transaction
    catchall_id = catchall["id"] if catchall else None
    stats = apply_consolidation(
        conn,
        stories,
        catchall_id,
        catchall_titles,
        ctm_id=ctm_info["id"],
        bucket_key=bucket_key,
    )
    conn.commit()

    print(
        "  Bucket '{}': {} stories, merged {}, rescued {}, deleted {}, created {}".format(
            bucket_label,
            len(stories),
            stats["merged"],
            stats["rescued"],
            stats["deleted"],
            stats["created"],
        )
    )

    return {
        "skipped": False,
        "stories": len(stories),
        "merged": stats["merged"],
        "rescued": stats["rescued"],
        "deleted": stats["deleted"],
        "created": stats["created"],
    }


def cross_bucket_dedup(conn, ctm_id, home_centroid_id, dry_run=False):
    """
    Post-consolidation pass: merge orphaned other_international events
    into bilateral buckets when their titles have clear geo signals.

    For each non-catchall event with event_type='other_international',
    look at its titles' centroid_ids to find the dominant foreign GEO centroid.
    If a bilateral event exists for that centroid with a similar topic, merge.
    Otherwise reassign the event to that bilateral bucket.
    """
    cur = conn.cursor()

    # Find other_international non-catchall events
    cur.execute(
        """SELECT e.id, e.topic_core, e.source_batch_count
           FROM events_v3 e
           WHERE e.ctm_id = %s AND e.event_type = 'other_international'
             AND e.is_catchall = false
           ORDER BY e.source_batch_count DESC""",
        (ctm_id,),
    )
    orphans = cur.fetchall()
    if not orphans:
        return 0

    # Load bilateral events for matching
    cur.execute(
        """SELECT e.id, e.bucket_key, e.topic_core, e.source_batch_count
           FROM events_v3 e
           WHERE e.ctm_id = %s AND e.event_type = 'bilateral'
             AND e.bucket_key IS NOT NULL AND e.is_catchall = false""",
        (ctm_id,),
    )
    bilateral_events = cur.fetchall()
    bilateral_by_bucket = defaultdict(list)
    for eid, bk, tc, cnt in bilateral_events:
        bilateral_by_bucket[bk].append({"id": eid, "topic_core": tc, "count": cnt})

    merged = 0
    for orphan_id, orphan_core, orphan_count in orphans:
        # Get centroid_ids from this event's titles
        cur.execute(
            """SELECT DISTINCT UNNEST(t.centroid_ids)
               FROM event_v3_titles evt
               JOIN titles_v3 t ON t.id = evt.title_id
               WHERE evt.event_id = %s""",
            (orphan_id,),
        )
        centroids = [r[0] for r in cur.fetchall()]
        # Find foreign GEO centroids (not home, not SYS-)
        foreign_geo = [
            c
            for c in centroids
            if c != home_centroid_id
            and not c.startswith("SYS-")
            and not c.startswith("NON-STATE-")
        ]
        if not foreign_geo:
            continue

        # Pick the most common foreign centroid among titles
        cur.execute(
            """SELECT cid, COUNT(*) AS cnt FROM (
                 SELECT UNNEST(t.centroid_ids) AS cid
                 FROM event_v3_titles evt
                 JOIN titles_v3 t ON t.id = evt.title_id
                 WHERE evt.event_id = %s
               ) sub
               WHERE cid = ANY(%s::text[])
               GROUP BY cid ORDER BY cnt DESC LIMIT 1""",
            (orphan_id, foreign_geo),
        )
        row = cur.fetchone()
        if not row:
            continue
        target_bucket = row[0]

        if dry_run:
            print(
                "  Cross-bucket: '{}' -> bucket {}".format(
                    (orphan_core or "?")[:50], target_bucket
                )
            )
            merged += 1
            continue

        # Only move titles that actually have the target centroid
        cur.execute(
            """SELECT evt.title_id
               FROM event_v3_titles evt
               JOIN titles_v3 t ON t.id = evt.title_id
               WHERE evt.event_id = %s
                 AND %s = ANY(t.centroid_ids)""",
            (orphan_id, target_bucket),
        )
        matching_title_ids = [r[0] for r in cur.fetchall()]
        if not matching_title_ids:
            continue

        # Find best bilateral event to merge into (largest in that bucket)
        candidates = bilateral_by_bucket.get(target_bucket, [])
        if candidates:
            best = max(candidates, key=lambda e: e["count"])
            # Move ONLY matching titles from orphan to target
            for tid in matching_title_ids:
                cur.execute(
                    """UPDATE event_v3_titles SET event_id = %s
                       WHERE title_id = %s AND event_id = %s""",
                    (best["id"], tid, orphan_id),
                )
            # Update target count
            cur.execute(
                """UPDATE events_v3 SET source_batch_count = (
                     SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
                   ), updated_at = NOW() WHERE id = %s""",
                (best["id"], best["id"]),
            )
            best["count"] += len(matching_title_ids)
            print(
                "  Cross-bucket merge: %d/%d titles -> '%s' in %s"
                % (
                    len(matching_title_ids),
                    orphan_count,
                    (best["topic_core"] or "?")[:40],
                    target_bucket,
                )
            )
        else:
            # No bilateral event exists -- move matching titles to a new event
            import uuid

            new_event_id = str(uuid.uuid4())
            cur.execute(
                """INSERT INTO events_v3 (id, ctm_id, date, event_type, bucket_key,
                       source_batch_count, is_catchall, topic_core)
                   VALUES (%s, %s, CURRENT_DATE, 'bilateral', %s, %s, false, %s)""",
                (
                    new_event_id,
                    ctm_id,
                    target_bucket,
                    len(matching_title_ids),
                    orphan_core,
                ),
            )
            for tid in matching_title_ids:
                cur.execute(
                    """UPDATE event_v3_titles SET event_id = %s
                       WHERE title_id = %s AND event_id = %s""",
                    (new_event_id, tid, orphan_id),
                )
            bilateral_by_bucket[target_bucket].append(
                {
                    "id": new_event_id,
                    "topic_core": orphan_core,
                    "count": len(matching_title_ids),
                }
            )
            print(
                "  Cross-bucket new: %d/%d titles -> new event in %s"
                % (len(matching_title_ids), orphan_count, target_bucket)
            )

        # Update orphan count (titles remaining) or delete if empty
        cur.execute(
            "SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s",
            (orphan_id,),
        )
        remaining = cur.fetchone()[0]
        if remaining == 0:
            cur.execute("DELETE FROM events_v3 WHERE id = %s", (orphan_id,))
        else:
            cur.execute(
                """UPDATE events_v3 SET source_batch_count = %s, updated_at = NOW()
                   WHERE id = %s""",
                (remaining, orphan_id),
            )

        merged += 1

    if merged > 0 and not dry_run:
        conn.commit()

    return merged


def redistribute_oi_catchall(conn, ctm_id, home_centroid_id, dry_run=False):
    """Move other_international catchall titles to bilateral catchalls by centroid_ids.

    For each title in an OI catchall, check its foreign GEO centroids.
    If it has exactly one, move it to that bilateral catchall.
    If multiple, move to the biggest bilateral bucket's catchall.
    """
    import uuid

    cur = conn.cursor()

    # Find OI catchall events
    cur.execute(
        """SELECT e.id FROM events_v3 e
           WHERE e.ctm_id = %s AND e.event_type = 'other_international'
             AND e.is_catchall = true""",
        (ctm_id,),
    )
    oi_catchalls = [r[0] for r in cur.fetchall()]
    if not oi_catchalls:
        return 0

    # Load bilateral catchalls (find or create later)
    cur.execute(
        """SELECT e.bucket_key, e.id
           FROM events_v3 e
           WHERE e.ctm_id = %s AND e.event_type = 'bilateral' AND e.is_catchall = true""",
        (ctm_id,),
    )
    bilateral_catchalls = dict(cur.fetchall())

    # Load bilateral event counts for picking biggest bucket
    cur.execute(
        """SELECT e.bucket_key, SUM(e.source_batch_count) as total
           FROM events_v3 e
           WHERE e.ctm_id = %s AND e.event_type = 'bilateral'
           GROUP BY e.bucket_key""",
        (ctm_id,),
    )
    bilateral_sizes = dict(cur.fetchall())

    moved = 0

    for oi_id in oi_catchalls:
        # Get all titles with their centroid_ids
        cur.execute(
            """SELECT evt.title_id, t.centroid_ids
               FROM event_v3_titles evt
               JOIN titles_v3 t ON t.id = evt.title_id
               WHERE evt.event_id = %s""",
            (oi_id,),
        )
        titles = cur.fetchall()

        for title_id, centroid_ids in titles:
            foreign_geo = [
                c
                for c in (centroid_ids or [])
                if c != home_centroid_id
                and not c.startswith("SYS-")
                and not c.startswith("NON-STATE-")
            ]
            if not foreign_geo:
                continue  # no foreign GEO, stays in OI catchall

            # Pick target bucket
            if len(foreign_geo) == 1:
                target = foreign_geo[0]
            else:
                # Multiple foreign GEOs: pick biggest bilateral bucket
                target = max(foreign_geo, key=lambda c: bilateral_sizes.get(c, 0))

            if dry_run:
                moved += 1
                continue

            # Find or create bilateral catchall for target
            if target not in bilateral_catchalls:
                ca_id = str(uuid.uuid4())
                cur.execute(
                    """INSERT INTO events_v3 (id, ctm_id, date, summary,
                           event_type, bucket_key, source_batch_count, is_catchall)
                       VALUES (%s, %s, CURRENT_DATE, 'Other coverage',
                           'bilateral', %s, 0, true)""",
                    (ca_id, ctm_id, target),
                )
                bilateral_catchalls[target] = ca_id

            # Move title
            cur.execute(
                """UPDATE event_v3_titles SET event_id = %s
                   WHERE title_id = %s AND event_id = %s""",
                (bilateral_catchalls[target], title_id, oi_id),
            )
            moved += 1

    if not dry_run and moved > 0:
        # Update all affected catchall counts
        for ca_id in list(bilateral_catchalls.values()) + oi_catchalls:
            cur.execute(
                """UPDATE events_v3 SET source_batch_count = (
                       SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
                   ), updated_at = NOW() WHERE id = %s""",
                (ca_id, ca_id),
            )
        # Delete empty OI catchalls
        for oi_id in oi_catchalls:
            cur.execute(
                "SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s",
                (oi_id,),
            )
            if cur.fetchone()[0] == 0:
                cur.execute("DELETE FROM events_v3 WHERE id = %s", (oi_id,))
        conn.commit()

    if moved > 0:
        print(
            "  OI catchall redistribution: %d titles moved to bilateral catchalls"
            % moved
        )
    return moved


def process_ctm(ctm_id=None, centroid=None, track=None, dry_run=False):
    """
    Run topic consolidation on a CTM.
    Same signature as aggregate_topics.process_ctm for daemon compatibility.
    """
    conn = get_connection()

    ctm = get_ctm_info(conn, ctm_id, centroid, track)
    if not ctm:
        print("CTM not found")
        conn.close()
        return

    print("=" * 70)
    print("TOPIC CONSOLIDATION {}".format("(DRY RUN)" if dry_run else ""))
    print("=" * 70)
    print("{} / {} / {}".format(ctm["centroid_id"], ctm["track"], ctm["month"]))
    print("Titles: {}".format(ctm["title_count"]))
    print()

    # Load all bucket data
    buckets = load_bucket_data(conn, ctm["id"])
    if not buckets:
        print("No events found")
        conn.close()
        return

    total_events = sum(len(b["events"]) for b in buckets.values())
    print(
        "Loaded {} buckets, {} non-catchall events".format(len(buckets), total_events)
    )
    print()

    total_stories = 0
    total_merged = 0
    total_rescued = 0
    total_deleted = 0
    buckets_processed = 0

    for bucket_key, bucket_data in buckets.items():
        result = process_bucket(conn, ctm, bucket_key, bucket_data, dry_run)
        if not result.get("skipped"):
            buckets_processed += 1
            total_stories += result.get("stories", 0)
            total_merged += result.get("merged", 0)
            total_rescued += result.get("rescued", 0)
            total_deleted += result.get("deleted", 0)

    # Cross-bucket dedup: merge orphaned other_international into bilateral
    cross_merged = cross_bucket_dedup(conn, ctm["id"], ctm["centroid_id"], dry_run)

    # Redistribute OI catchall titles to bilateral catchalls
    oi_redistributed = redistribute_oi_catchall(
        conn, ctm["id"], ctm["centroid_id"], dry_run
    )

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("Buckets processed: {}".format(buckets_processed))
    print("Stories created: {}".format(total_stories))
    print("Events merged: {}".format(total_merged))
    print("Catchall titles rescued: {}".format(total_rescued))
    print("Events deleted: {}".format(total_deleted))
    if cross_merged:
        print("Cross-bucket dedup: {}".format(cross_merged))
    if oi_redistributed:
        print("OI catchall redistributed: {}".format(oi_redistributed))

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 4.1: Topic Consolidation")
    parser.add_argument("--ctm-id", type=str, help="CTM ID to process")
    parser.add_argument("--centroid", type=str, help="Centroid ID")
    parser.add_argument("--track", type=str, help="Track name")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only")

    args = parser.parse_args()

    if not args.ctm_id and not (args.centroid and args.track):
        parser.error("Either --ctm-id or both --centroid and --track required")

    process_ctm(
        ctm_id=args.ctm_id,
        centroid=args.centroid,
        track=args.track,
        dry_run=args.dry_run,
    )
