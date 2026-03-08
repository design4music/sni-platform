"""
Phase 4.1: Anchor-Candidate Topic Consolidation

Asymmetric dedup model: existing events are ANCHORS with fixed identity.
Smaller similar-looking events are CANDIDATES. The LLM confirms whether
each candidate is a true duplicate of an anchor (yes/no), never groups
events into invented themes.

Usage:
    python pipeline/phase_4/consolidate_topics.py --ctm-id <uuid>
    python pipeline/phase_4/consolidate_topics.py --centroid EUROPE-RUSSIA --track geo_politics
    python pipeline/phase_4/consolidate_topics.py --ctm-id <uuid> --dry-run
"""

import argparse
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path

import httpx
import psycopg2

# Fix Windows console encoding (prevents charmap errors on non-ASCII data)
if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from core.llm_utils import extract_json
from core.prompts import (
    CATCHALL_RESCUE_SYSTEM_PROMPT,
    CATCHALL_RESCUE_USER_PROMPT,
    DEDUP_CONFIRM_SYSTEM_PROMPT,
    DEDUP_CONFIRM_USER_PROMPT,
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


CATCHALL_MAX_AGE_DAYS = 3


def load_bucket_data(conn, ctm_id):
    """
    Load all events grouped by bucket.
    Non-catchall events carry their LLM-generated title (compact).
    Catchall titles are filtered to recent only (< CATCHALL_MAX_AGE_DAYS).
    Returns: {bucket_key: {"events": [...], "catchall": {"id":..., "titles":[...]}}}
    """
    cur = conn.cursor()

    # Get all events (include title for compact prompt representation)
    cur.execute(
        """SELECT e.id, e.bucket_key, e.source_batch_count, e.is_catchall,
                  e.topic_core, e.event_type, e.title, e.importance_score
           FROM events_v3 e
           WHERE e.ctm_id = %s
           ORDER BY e.source_batch_count DESC NULLS LAST""",
        (ctm_id,),
    )
    events_raw = cur.fetchall()

    if not events_raw:
        return {}

    # Load recent catchall titles only (older orphans are permanently unclustered)
    catchall_ids = [r[0] for r in events_raw if r[3]]  # is_catchall=True
    headlines_by_event = defaultdict(list)
    title_ids_by_event = defaultdict(list)

    if catchall_ids:
        cur.execute(
            """SELECT evt.event_id, t.title_display, evt.title_id
               FROM event_v3_titles evt
               JOIN titles_v3 t ON t.id = evt.title_id
               WHERE evt.event_id = ANY(%s::uuid[])
                 AND t.pubdate_utc >= NOW() - %s * INTERVAL '1 day'""",
            (catchall_ids, CATCHALL_MAX_AGE_DAYS),
        )
        for event_id, title_display, title_id in cur.fetchall():
            headlines_by_event[event_id].append(title_display)
            title_ids_by_event[event_id].append(title_id)

    # Group by bucket -- use event_type to distinguish domestic from other_international
    buckets = defaultdict(lambda: {"events": [], "catchall": None})
    for (
        eid,
        bucket_key,
        count,
        is_catchall,
        topic_core,
        event_type,
        title,
        imp_score,
    ) in events_raw:
        if bucket_key:
            bk = bucket_key
        elif event_type == "other_international":
            bk = "__other_international__"
        else:
            bk = "__domestic__"

        if is_catchall:
            tids = title_ids_by_event.get(eid, [])
            headlines = headlines_by_event.get(eid, [])
            buckets[bk]["catchall"] = {
                "id": eid,
                "titles": headlines,
                "title_ids": tids,
            }
        else:
            buckets[bk]["events"].append(
                {
                    "id": str(eid),
                    "count": count or 0,
                    "title": title,
                    "topic_core": topic_core,
                    "importance_score": imp_score or 0.0,
                }
            )

    return dict(buckets)


def call_llm(system_prompt, user_prompt):
    """Call DeepSeek LLM with retry and return parsed JSON response."""
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
        "temperature": config.llm_temperature,
        "max_tokens": 4000,
    }

    last_error = None
    for attempt in range(config.llm_retry_attempts):
        try:
            with httpx.Client(timeout=config.llm_timeout_seconds) as client:
                response = client.post(
                    "{}/chat/completions".format(config.deepseek_api_url),
                    headers=headers,
                    json=payload,
                )

                from core.llm_utils import check_rate_limit

                if check_rate_limit(response):
                    continue

                if response.status_code != 200:
                    raise RuntimeError(
                        "LLM API error: {} {}".format(
                            response.status_code, response.text[:200]
                        )
                    )

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

            return extract_json(content)
        except Exception as e:
            last_error = e
            if attempt < config.llm_retry_attempts - 1:
                wait = config.llm_retry_backoff**attempt
                print(
                    "  LLM retry %d/%d after %.1fs: %s"
                    % (attempt + 1, config.llm_retry_attempts, wait, e)
                )
                time.sleep(wait)
    raise last_error


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
                    len_diff = abs(len(vid) - len(eid))
                    if len_diff > 2:
                        continue
                    diffs = sum(1 for a, b in zip(vid, eid) if a != b) + len_diff
                    if diffs < best_diffs:
                        best = vid
                        best_diffs = diffs
                if best:
                    repaired.append(best)
                    already_used.add(best)
                else:
                    repaired.append(eid)  # keep as-is, validation will catch
        story["event_ids"] = repaired


def _title_words(text):
    """Extract lowercase content words from a headline."""
    if not text:
        return set()
    stop = {
        "the",
        "a",
        "an",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "and",
        "or",
        "with",
        "as",
        "by",
        "is",
        "are",
        "its",
        "after",
        "from",
        "new",
        "says",
        "has",
        "have",
        "will",
        "been",
        "over",
        "amid",
        "not",
        "but",
    }
    words = set()
    for w in text.lower().split():
        w = w.strip(".,;:!?\"'()[]")
        if w and w not in stop and len(w) > 2:
            words.add(w)
    return words


# ---------------------------------------------------------------------------
# New: Anchor-Candidate helpers
# ---------------------------------------------------------------------------


def _repair_single_id(broken_id, valid_ids):
    """Find the closest valid ID to a potentially corrupted UUID."""
    best = None
    best_diffs = 5
    for vid in valid_ids:
        len_diff = abs(len(vid) - len(broken_id))
        if len_diff > 2:
            continue
        diffs = sum(1 for a, b in zip(vid, broken_id) if a != b) + len_diff
        if diffs < best_diffs:
            best = vid
            best_diffs = diffs
    return best


def _find_merge_candidates(events, dice_threshold=0.35):
    """Pre-LLM filter: find anchor-candidate pairs by title word Dice.

    For each pair above threshold, the larger event is the anchor and the
    smaller is the candidate.  Returns (anchors, candidates) as flat lists.
    Events with no similar partner are excluded entirely.
    """
    n = len(events)
    if n < 2:
        return [], []

    word_sets = []
    for ev in events:
        text = ev.get("title") or ev.get("topic_core") or ""
        word_sets.append(_title_words(text))

    is_candidate = set()
    is_anchor = set()

    for i in range(n):
        for j in range(i + 1, n):
            a, b = word_sets[i], word_sets[j]
            if not a or not b:
                continue
            dice = 2 * len(a & b) / (len(a) + len(b))
            if dice >= dice_threshold:
                ci = events[i]["count"] or 0
                cj = events[j]["count"] or 0
                imp_i = events[i].get("importance_score", 0) or 0
                imp_j = events[j].get("importance_score", 0) or 0
                # High-importance events strongly prefer anchor role
                if imp_i - imp_j > 0.3:
                    is_anchor.add(i)
                    is_candidate.add(j)
                elif imp_j - imp_i > 0.3:
                    is_anchor.add(j)
                    is_candidate.add(i)
                elif ci >= cj:
                    is_anchor.add(i)
                    is_candidate.add(j)
                else:
                    is_anchor.add(j)
                    is_candidate.add(i)

    # An event that is similar to something larger is always a candidate,
    # even if it was also an anchor for something smaller.
    is_anchor -= is_candidate

    if not is_candidate:
        return [], []

    anchors = [events[i] for i in sorted(is_anchor)]
    candidates = [events[i] for i in sorted(is_candidate)]
    return anchors, candidates


def _find_catchall_matches(events, catchall_titles, min_overlap=2):
    """Pre-filter catchall titles to those with word overlap to any event.

    Returns list of catchall indices with >= min_overlap shared content words
    with at least one existing event.
    """
    if not events or not catchall_titles:
        return []

    event_words = []
    for ev in events:
        text = ev.get("title") or ev.get("topic_core") or ""
        event_words.append(_title_words(text))

    matched_indices = []
    for ci, title in enumerate(catchall_titles):
        tw = _title_words(title)
        if not tw:
            continue
        for ew in event_words:
            if len(tw & ew) >= min_overlap:
                matched_indices.append(ci)
                break

    return matched_indices


def build_dedup_prompt(anchors, candidates, ctm_info, bucket_label):
    """Format the dedup confirmation prompt for one bucket."""
    month_str = str(ctm_info["month"])[:7] if ctm_info["month"] else "unknown"

    anchors_lines = []
    for i, ev in enumerate(anchors, 1):
        title = ev.get("title") or ev.get("topic_core") or "(untitled)"
        anchors_lines.append(
            "A{} [{} sources] id={} -- {}".format(i, ev["count"], ev["id"], title)
        )

    candidates_lines = []
    for i, ev in enumerate(candidates, 1):
        title = ev.get("title") or ev.get("topic_core") or "(untitled)"
        candidates_lines.append(
            "C{} [{} sources] id={} -- {}".format(i, ev["count"], ev["id"], title)
        )

    return DEDUP_CONFIRM_USER_PROMPT.format(
        centroid_label=ctm_info["centroid_label"],
        track=ctm_info["track"],
        month=month_str,
        anchors_text="\n".join(anchors_lines),
        candidates_text="\n".join(candidates_lines),
    )


def build_rescue_prompt(
    events, catchall_titles, catchall_indices, ctm_info, bucket_label
):
    """Format the catchall rescue prompt for one bucket."""
    month_str = str(ctm_info["month"])[:7] if ctm_info["month"] else "unknown"

    events_lines = []
    for i, ev in enumerate(events, 1):
        title = ev.get("title") or ev.get("topic_core") or "(untitled)"
        events_lines.append(
            "E{} [{} sources] id={} -- {}".format(i, ev["count"], ev["id"], title)
        )

    headlines_lines = []
    for seq, ci in enumerate(catchall_indices):
        safe_t = catchall_titles[ci][:100] if catchall_titles[ci] else "[no title]"
        headlines_lines.append("H{}: {}".format(seq, safe_t))

    return CATCHALL_RESCUE_USER_PROMPT.format(
        centroid_label=ctm_info["centroid_label"],
        track=ctm_info["track"],
        month=month_str,
        events_text="\n".join(events_lines),
        headlines_text="\n".join(headlines_lines),
    )


def validate_dedup_response(response, candidate_ids, anchor_ids):
    """Validate LLM dedup response structure.

    Returns (is_valid, error_message).
    """
    matches = response.get("matches", [])
    if not matches:
        return False, "No matches in response"

    valid_anchors = set(anchor_ids) | {"none"}
    seen = set()

    for m in matches:
        cid = m.get("candidate_id")
        aid = m.get("anchor_id")
        conf = m.get("confidence", 0)

        if cid not in set(candidate_ids):
            return False, "Unknown candidate_id: {}".format(cid)
        if aid not in valid_anchors:
            return False, "Invalid anchor_id: {}".format(aid)
        if not isinstance(conf, (int, float)) or conf < 0 or conf > 1:
            return False, "Confidence out of range: {}".format(conf)
        if cid in seen:
            return False, "Duplicate candidate_id: {}".format(cid)
        seen.add(cid)

    # Auto-fix: add missing candidates as "none"
    missing = set(candidate_ids) - seen
    if missing:
        for cid in missing:
            response["matches"].append(
                {"candidate_id": cid, "anchor_id": "none", "confidence": 0}
            )

    return True, ""


def validate_rescue_response(response, catchall_indices, anchor_ids):
    """Validate LLM rescue response structure.

    Returns (is_valid, error_message).
    """
    assignments = response.get("assignments", [])
    if not assignments:
        return False, "No assignments in response"

    valid_anchors = set(anchor_ids) | {"none"}
    valid_indices = set(catchall_indices)
    seen = set()

    for a in assignments:
        idx = a.get("index")
        aid = a.get("anchor_id")

        if idx not in valid_indices:
            return False, "Unknown index: {}".format(idx)
        if aid not in valid_anchors:
            return False, "Invalid anchor_id: {}".format(aid)
        if idx in seen:
            return False, "Duplicate index: {}".format(idx)
        seen.add(idx)

    # Auto-fix: add missing indices as "none"
    missing = valid_indices - seen
    if missing:
        for idx in missing:
            response["assignments"].append({"index": idx, "anchor_id": "none"})

    return True, ""


def apply_merges(conn, matches, min_confidence=0.7):
    """Apply confirmed dedup merges.

    Moves titles from candidate to anchor. Never touches anchor's
    title/topic_core/summary -- only source_batch_count updates.
    Returns stats dict.
    """
    cur = conn.cursor()
    stats = {"merged": 0, "deleted": 0}

    for m in matches:
        if m.get("anchor_id") == "none":
            continue
        if m.get("confidence", 0) < min_confidence:
            continue

        candidate_id = m["candidate_id"]
        anchor_id = m["anchor_id"]

        # Move all titles from candidate to anchor
        cur.execute(
            "UPDATE event_v3_titles SET event_id = %s WHERE event_id = %s",
            (anchor_id, candidate_id),
        )
        # Delete the candidate event
        cur.execute("DELETE FROM events_v3 WHERE id = %s", (candidate_id,))
        # Update anchor's source_batch_count
        cur.execute(
            """UPDATE events_v3
               SET source_batch_count = (
                   SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
               ), updated_at = NOW()
               WHERE id = %s""",
            (anchor_id, anchor_id),
        )
        stats["merged"] += 1
        stats["deleted"] += 1

    return stats


def apply_rescues(conn, assignments, catchall_event_id, catchall_title_ids, bucket_key):
    """Move assigned catchall titles from catchall to anchor events.

    Includes bilateral centroid validation (same as original).
    Returns stats dict.
    """
    cur = conn.cursor()
    stats = {"rescued": 0, "rescue_skipped": 0}

    db_bucket = (
        None
        if bucket_key in ("__domestic__", "__other_international__")
        else bucket_key
    )

    updated_anchors = set()

    for a in assignments:
        if a.get("anchor_id") == "none":
            continue

        idx = a["index"]
        anchor_id = a["anchor_id"]

        if idx < 0 or idx >= len(catchall_title_ids):
            continue

        title_id = catchall_title_ids[idx]
        if not title_id:
            continue

        # Bilateral centroid validation
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
            (anchor_id, title_id, catchall_event_id),
        )
        stats["rescued"] += 1
        updated_anchors.add(anchor_id)

    # Update source_batch_count for all affected anchors
    for aid in updated_anchors:
        cur.execute(
            """UPDATE events_v3
               SET source_batch_count = (
                   SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
               ), updated_at = NOW()
               WHERE id = %s""",
            (aid, aid),
        )

    # Update catchall count
    if stats["rescued"] > 0 and catchall_event_id:
        cur.execute(
            """UPDATE events_v3
               SET source_batch_count = (
                   SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
               ), updated_at = NOW()
               WHERE id = %s""",
            (catchall_event_id, catchall_event_id),
        )

    return stats


# ---------------------------------------------------------------------------
# Main bucket processor (rewritten for anchor-candidate model)
# ---------------------------------------------------------------------------


def process_bucket(conn, ctm_info, bucket_key, bucket_data, dry_run=False):
    """Process one bucket: anchor-candidate dedup + catchall rescue."""
    all_events = bucket_data["events"]
    catchall = bucket_data.get("catchall")

    # Only titled events participate
    events = [ev for ev in all_events if ev.get("title")]
    catchall_titles = catchall["titles"] if catchall else []
    catchall_tids = catchall.get("title_ids", []) if catchall else []

    # Skip if too little data
    if len(events) < 2 and len(catchall_titles) < 5:
        return {"skipped": True, "reason": "too few titled events"}

    if bucket_key == "__domestic__":
        bucket_label = "Domestic"
    elif bucket_key == "__other_international__":
        bucket_label = "Other International"
    else:
        bucket_label = bucket_key

    stats = {"merged": 0, "rescued": 0, "rescue_skipped": 0, "deleted": 0}

    # --- Phase A: Anchor-candidate dedup ---
    merged_candidate_ids = set()
    if len(events) >= 2:
        anchors, candidates = _find_merge_candidates(events)
        if anchors and candidates:
            user_prompt = build_dedup_prompt(
                anchors, candidates, ctm_info, bucket_label
            )
            anchor_ids = [a["id"] for a in anchors]
            candidate_ids = [c["id"] for c in candidates]

            if dry_run:
                print(
                    "  [%s] Dedup: %d anchors, %d candidates, prompt %d chars"
                    % (bucket_label, len(anchors), len(candidates), len(user_prompt))
                )

            try:
                response = call_llm(DEDUP_CONFIRM_SYSTEM_PROMPT, user_prompt)
            except Exception as e:
                print("  [%s] Dedup LLM error: %s" % (bucket_label, e))
                response = None

            if response:
                # Repair corrupted UUIDs
                for m in response.get("matches", []):
                    if m.get("candidate_id") not in set(candidate_ids):
                        fixed = _repair_single_id(m["candidate_id"], candidate_ids)
                        if fixed:
                            m["candidate_id"] = fixed
                    aid = m.get("anchor_id")
                    if aid and aid != "none" and aid not in set(anchor_ids):
                        fixed = _repair_single_id(aid, anchor_ids)
                        if fixed:
                            m["anchor_id"] = fixed

                ok, err = validate_dedup_response(response, candidate_ids, anchor_ids)
                if ok:
                    if dry_run:
                        confirmed = [
                            m
                            for m in response["matches"]
                            if m.get("anchor_id") != "none"
                            and m.get("confidence", 0) >= 0.7
                        ]
                        print("    -> %d confirmed merges" % len(confirmed))
                        for m in confirmed:
                            print(
                                "      %s -> %s (conf=%.2f)"
                                % (
                                    m["candidate_id"][:12],
                                    m["anchor_id"][:12],
                                    m["confidence"],
                                )
                            )
                    else:
                        merge_stats = apply_merges(conn, response["matches"])
                        stats["merged"] += merge_stats["merged"]
                        stats["deleted"] += merge_stats["deleted"]
                        conn.commit()
                        # Track which candidates were merged for Phase B
                        for m in response["matches"]:
                            if (
                                m.get("anchor_id") != "none"
                                and m.get("confidence", 0) >= 0.7
                            ):
                                merged_candidate_ids.add(m["candidate_id"])
                else:
                    print("  [%s] Dedup validation error: %s" % (bucket_label, err))
        elif dry_run:
            print(
                "  [%s] No similar pairs (Dice < 0.35), skipping dedup" % bucket_label
            )

    # Remove merged candidates from event list before rescue phase
    if merged_candidate_ids:
        events = [ev for ev in events if ev["id"] not in merged_candidate_ids]

    # --- Phase B: Catchall rescue ---
    if catchall_titles and events:
        matched_indices = _find_catchall_matches(events, catchall_titles)
        if matched_indices:
            user_prompt = build_rescue_prompt(
                events, catchall_titles, matched_indices, ctm_info, bucket_label
            )
            event_ids = [ev["id"] for ev in events]

            if dry_run:
                print(
                    "  [%s] Rescue: %d catchall -> %d pre-filtered, prompt %d chars"
                    % (
                        bucket_label,
                        len(catchall_titles),
                        len(matched_indices),
                        len(user_prompt),
                    )
                )

            try:
                response = call_llm(CATCHALL_RESCUE_SYSTEM_PROMPT, user_prompt)
            except Exception as e:
                print("  [%s] Rescue LLM error: %s" % (bucket_label, e))
                response = None

            if response:
                # Repair corrupted anchor IDs
                for a in response.get("assignments", []):
                    aid = a.get("anchor_id")
                    if aid and aid != "none" and aid not in set(event_ids):
                        fixed = _repair_single_id(aid, event_ids)
                        if fixed:
                            a["anchor_id"] = fixed

                # Validate against sequential indices (prompt uses H0, H1, ...)
                seq_indices = list(range(len(matched_indices)))
                ok, err = validate_rescue_response(response, seq_indices, event_ids)
                # Remap sequential -> original catchall indices
                if ok:
                    for a in response.get("assignments", []):
                        seq = a.get("index", -1)
                        if 0 <= seq < len(matched_indices):
                            a["index"] = matched_indices[seq]
                if ok:
                    if dry_run:
                        assigned = [
                            a
                            for a in response["assignments"]
                            if a.get("anchor_id") != "none"
                        ]
                        print("    -> %d titles assigned to events" % len(assigned))
                    else:
                        rescue_stats = apply_rescues(
                            conn,
                            response["assignments"],
                            catchall["id"],
                            catchall_tids,
                            bucket_key,
                        )
                        stats["rescued"] += rescue_stats["rescued"]
                        stats["rescue_skipped"] += rescue_stats["rescue_skipped"]
                        conn.commit()
                else:
                    print("  [%s] Rescue validation error: %s" % (bucket_label, err))
        elif dry_run:
            print("  [%s] No catchall word-overlap matches" % bucket_label)

    if not dry_run and (stats["merged"] or stats["rescued"]):
        print(
            "  Bucket '%s': merged %d, rescued %d (skipped %d), deleted %d"
            % (
                bucket_label,
                stats["merged"],
                stats["rescued"],
                stats["rescue_skipped"],
                stats["deleted"],
            )
        )

    return {"skipped": False, **stats}


# ---------------------------------------------------------------------------
# Cross-bucket passes (unchanged)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def process_ctm(ctm_id=None, centroid=None, track=None, dry_run=False):
    """
    Run topic consolidation on a CTM.
    Same signature as aggregate_topics.process_ctm for daemon compatibility.
    """
    conn = get_connection()
    try:
        ctm = get_ctm_info(conn, ctm_id, centroid, track)
        if not ctm:
            print("CTM not found")
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
            return

        total_events = sum(len(b["events"]) for b in buckets.values())
        print(
            "Loaded {} buckets, {} non-catchall events".format(
                len(buckets), total_events
            )
        )
        print()

        total_merged = 0
        total_rescued = 0
        total_deleted = 0
        buckets_processed = 0

        for bucket_key, bucket_data in buckets.items():
            result = process_bucket(conn, ctm, bucket_key, bucket_data, dry_run)
            if not result.get("skipped"):
                buckets_processed += 1
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
        print("Events merged (dedup): {}".format(total_merged))
        print("Catchall titles rescued: {}".format(total_rescued))
        print("Events deleted: {}".format(total_deleted))
        if cross_merged:
            print("Cross-bucket dedup: {}".format(cross_merged))
        if oi_redistributed:
            print("OI catchall redistributed: {}".format(oi_redistributed))
    finally:
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
