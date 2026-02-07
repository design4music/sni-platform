"""
Phase 4.2: Topic Aggregation

Intelligent merging and cleanup of topics within the same CTM/bucket.
- Step A: Identify merge candidates (signal overlap)
- Step B: LLM review for intelligent merge decisions
- Step C: Apply topic limits (dynamic based on bucket size)
- Step C.5: Generic signal cleanup (split mixed topics)
- Step D: Reassign "Other Coverage" titles to existing topics

Generic Signal Cleanup (Step C.5):
- Signals are "generic" if they appear in 5+ different topics (dynamic, per-CTM)
- Topics with ONLY generic signals + small title count are flagged as suspicious
- LLM reviews suspicious topics to detect mixed/unrelated stories
- Mixed titles are reassigned to specific sibling topics or "Other"

Usage:
    python pipeline/phase_4/aggregate_topics.py --ctm-id <uuid>
    python pipeline/phase_4/aggregate_topics.py --centroid AMERICAS-USA --track geo_economy
    python pipeline/phase_4/aggregate_topics.py --dry-run  # analyze only
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import httpx
import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config
from core.prompts import MIXED_TOPIC_REVIEW_PROMPT, TOPIC_MERGE_PROMPT

# =============================================================================
# GENERIC SIGNAL DETECTION CONFIG
# =============================================================================

# A signal is "generic" if it appears in this many+ different topics within a CTM
GENERIC_SIGNAL_TOPIC_THRESHOLD = 5

# Topics with only generic signals AND fewer than this many titles are flagged
SUSPICIOUS_TOPIC_MAX_TITLES = 12


# =============================================================================
# DATABASE
# =============================================================================


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def get_ctm_info(conn, ctm_id: str = None, centroid: str = None, track: str = None):
    """Get CTM info by ID or by centroid+track (most recent month)."""
    cur = conn.cursor()

    if ctm_id:
        cur.execute(
            """
            SELECT c.id, c.centroid_id, c.track, c.month, c.title_count
            FROM ctm c
            WHERE c.id = %s
            """,
            (ctm_id,),
        )
    else:
        cur.execute(
            """
            SELECT c.id, c.centroid_id, c.track, c.month, c.title_count
            FROM ctm c
            WHERE c.centroid_id = %s AND c.track = %s
            ORDER BY c.month DESC
            LIMIT 1
            """,
            (centroid, track),
        )

    row = cur.fetchone()
    if not row:
        return None

    return {
        "id": row[0],
        "centroid_id": row[1],
        "track": row[2],
        "month": row[3],
        "title_count": row[4],
    }


def get_topics_with_signals(conn, ctm_id: str) -> dict:
    """
    Get all topics for a CTM with aggregated signals and sample titles.
    Returns: {event_id: {bucket_key, count, is_catchall, signals, sample_titles}}
    """
    cur = conn.cursor()

    # Get events
    cur.execute(
        """
        SELECT e.id, e.title, e.summary, e.bucket_key,
               e.source_batch_count, e.is_catchall
        FROM events_v3 e
        WHERE e.ctm_id = %s
        ORDER BY e.source_batch_count DESC NULLS LAST
        """,
        (ctm_id,),
    )

    events = {}
    for row in cur.fetchall():
        event_id, title, summary, bucket_key, count, is_catchall = row
        events[event_id] = {
            "title": title or summary or "[Unnamed]",
            "bucket_key": bucket_key,
            "count": count or 0,
            "is_catchall": is_catchall or False,
            "persons": set(),
            "orgs": set(),
            "places": set(),
            "commodities": set(),
            "policies": set(),
            "action_classes": set(),
            "domains": set(),
            "sample_titles": [],
        }

    if not events:
        return {}

    # Aggregate signals
    cur.execute(
        """
        SELECT evt.event_id,
               tl.persons, tl.orgs, tl.places, tl.commodities, tl.policies,
               tl.action_class, tl.domain
        FROM event_v3_titles evt
        JOIN title_labels tl ON tl.title_id = evt.title_id
        WHERE evt.event_id = ANY(%s::uuid[])
        """,
        (list(events.keys()),),
    )

    for row in cur.fetchall():
        event_id, persons, orgs, places, commodities, policies, action_class, domain = (
            row
        )
        if event_id in events:
            if persons:
                events[event_id]["persons"].update(persons)
            if orgs:
                events[event_id]["orgs"].update(orgs)
            if places:
                events[event_id]["places"].update(places)
            if commodities:
                events[event_id]["commodities"].update(commodities)
            if policies:
                events[event_id]["policies"].update(policies)
            if action_class:
                events[event_id]["action_classes"].add(action_class)
            if domain:
                events[event_id]["domains"].add(domain)

    # Get sample titles (top 5)
    cur.execute(
        """
        SELECT evt.event_id, t.title_display
        FROM event_v3_titles evt
        JOIN titles_v3 t ON t.id = evt.title_id
        WHERE evt.event_id = ANY(%s::uuid[])
        """,
        (list(events.keys()),),
    )

    for row in cur.fetchall():
        event_id, title_display = row
        if event_id in events and len(events[event_id]["sample_titles"]) < 25:
            events[event_id]["sample_titles"].append(title_display)

    return events


# =============================================================================
# MERGE CANDIDATE DETECTION
# =============================================================================


def jaccard_similarity(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def get_all_signals(event: dict) -> set:
    """Get all signals combined for an event."""
    return (
        event["persons"]
        | event["orgs"]
        | event["places"]
        | event["commodities"]
        | event["policies"]
        | event.get("action_classes", set())
        | event.get("domains", set())
    )


def title_similarity(titles1: list, titles2: list) -> float:
    """
    Calculate similarity between two topic title sets using word overlap.
    This catches obvious duplicates that signal-based similarity might miss.
    """
    import re

    def tokenize(text):
        # Extract meaningful words (3+ chars, no stopwords)
        stopwords = {
            "the",
            "and",
            "for",
            "with",
            "that",
            "this",
            "from",
            "over",
            "into",
        }
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        return set(w for w in words if w not in stopwords)

    # Get all tokens from all titles
    tokens1 = set()
    tokens2 = set()

    for t in titles1[:5]:  # Use top 5 titles
        tokens1.update(tokenize(t))
    for t in titles2[:5]:
        tokens2.update(tokenize(t))

    if not tokens1 or not tokens2:
        return 0.0

    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)

    return intersection / union if union > 0 else 0.0


def find_merge_candidates(events: dict, similarity_threshold: float = 0.25) -> list:
    """
    Find groups of events within the same bucket that could be merged.
    Uses both signal similarity AND title text similarity.
    Returns: [{"bucket_key": ..., "events": [eid1, eid2, ...], "similarity": ...}]
    """
    # Group by bucket_key (exclude catchalls)
    by_bucket = defaultdict(list)
    for event_id, data in events.items():
        if not data["is_catchall"]:
            by_bucket[data["bucket_key"]].append(event_id)

    candidates = []

    for bucket_key, event_ids in by_bucket.items():
        if len(event_ids) < 2:
            continue

        # Build similarity matrix using BOTH signal and title similarity
        pairs = []
        for i, eid1 in enumerate(event_ids):
            for eid2 in event_ids[i + 1 :]:
                e1, e2 = events[eid1], events[eid2]

                # Signal similarity
                sig1 = get_all_signals(e1)
                sig2 = get_all_signals(e2)
                sig_sim = jaccard_similarity(sig1, sig2)

                # Event title similarity (high signal - these are LLM-generated summaries)
                event_title_sim = title_similarity(
                    [e1.get("title", "")], [e2.get("title", "")]
                )

                # Sample headline similarity (lower signal - varied source wording)
                headline_sim = title_similarity(
                    e1.get("sample_titles", [])[:3],
                    e2.get("sample_titles", [])[:3],
                )

                # Key entity boost: if topics share 2+ persons or orgs, add boost
                shared_persons = e1.get("persons", set()) & e2.get("persons", set())
                shared_orgs = e1.get("orgs", set()) & e2.get("orgs", set())
                key_entity_count = len(shared_persons) + len(shared_orgs)
                entity_boost = 0.15 if key_entity_count >= 2 else 0

                # Combined similarity: best of signal, event title, or headlines + boost
                combined_sim = (
                    max(sig_sim, event_title_sim, headline_sim) + entity_boost
                )

                if combined_sim >= similarity_threshold:
                    pairs.append((eid1, eid2, combined_sim, sig1 & sig2))

        # Group connected pairs into clusters
        if pairs:
            clusters = cluster_pairs(pairs, event_ids)
            for cluster in clusters:
                if len(cluster) >= 2:
                    # Calculate average similarity within cluster
                    cluster_sims = [
                        p[2] for p in pairs if p[0] in cluster and p[1] in cluster
                    ]
                    avg_sim = (
                        sum(cluster_sims) / len(cluster_sims) if cluster_sims else 0
                    )

                    candidates.append(
                        {
                            "bucket_key": bucket_key,
                            "events": list(cluster),
                            "avg_similarity": avg_sim,
                        }
                    )

    return candidates


def cluster_pairs(pairs: list, all_ids: list) -> list:
    """
    Group pairs into clusters where members are MUTUALLY similar.
    Prioritizes HIGHEST similarity pairs first to avoid suboptimal groupings.
    Can form clusters of 2, 3, 4, or more topics if all are mutually similar.
    """
    # Sort pairs by similarity DESCENDING - highest first
    sorted_pairs = sorted(pairs, key=lambda x: x[2], reverse=True)

    # Build adjacency with similarity scores
    similar = defaultdict(dict)
    for eid1, eid2, sim, shared in sorted_pairs:
        similar[eid1][eid2] = sim
        similar[eid2][eid1] = sim

    clusters = []
    used = set()

    # Process pairs in order of highest similarity first
    for eid1, eid2, sim, shared in sorted_pairs:
        if eid1 in used or eid2 in used:
            continue

        # Start with this pair and try to expand
        cluster = {eid1, eid2}

        # Find all candidates that are similar to ALL current cluster members
        while True:
            best_candidate = None
            best_avg_sim = 0.3  # Minimum threshold to join

            for candidate in similar[eid1].keys() | similar[eid2].keys():
                if candidate in used or candidate in cluster:
                    continue

                # Check if candidate is similar to ALL cluster members
                sims_to_cluster = []
                for member in cluster:
                    if candidate in similar[member]:
                        sims_to_cluster.append(similar[member][candidate])
                    else:
                        break  # Not connected to this member
                else:
                    # Connected to all members
                    avg_sim = sum(sims_to_cluster) / len(sims_to_cluster)
                    if avg_sim > best_avg_sim:
                        best_candidate = candidate
                        best_avg_sim = avg_sim

            if best_candidate:
                cluster.add(best_candidate)
            else:
                break  # No more candidates to add

        clusters.append(cluster)
        used.update(cluster)

    return clusters


# =============================================================================
# LLM MERGE REVIEW
# =============================================================================


def build_merge_review_prompt(events: dict, candidate: dict) -> str:
    """Build prompt for LLM to review merge candidates."""
    event_ids = candidate["events"]
    bucket = candidate["bucket_key"] or "Domestic"

    lines = [
        "Review these {} topics from the '{}' bucket.".format(len(event_ids), bucket),
        "",
        "TASK: Identify which topics (if any) cover the SAME story and should be merged.",
        "",
        "GUIDELINES:",
        "- MERGE topics that cover the same event/story from different sources",
        "- MERGE topics about the same entity doing the same thing",
        "- KEEP SEPARATE if topics have different contexts",
        "- For 3+ topics, you can specify PARTIAL merge (e.g., merge 1+3, keep 2 separate)",
        "",
    ]

    for i, eid in enumerate(event_ids, 1):
        e = events[eid]
        lines.append("TOPIC {}:".format(i))
        lines.append("  Count: {} titles".format(e["count"]))
        lines.append("  Signals: {}".format(", ".join(sorted(get_all_signals(e))[:10])))
        lines.append("  Sample headlines:")
        for t in e["sample_titles"][:3]:
            clean_t = t[:80].encode("ascii", errors="replace").decode("ascii")
            lines.append("    - {}".format(clean_t))
        lines.append("")

    lines.append("Return JSON with ONE of these formats:")
    lines.append('- All merge: {"decision": "MERGE", "reason": "..."}')
    lines.append('- All separate: {"decision": "SEPARATE", "reason": "..."}')
    lines.append(
        '- Partial: {"decision": "PARTIAL", "merge": [1,3], "separate": [2], "reason": "..."}'
    )

    return "\n".join(lines)


def review_merge_with_llm(events: dict, candidate: dict) -> dict:
    """Use LLM to review if merge candidate should be merged."""
    prompt = build_merge_review_prompt(events, candidate)
    event_ids = candidate["events"]

    headers = {
        "Authorization": "Bearer {}".format(config.deepseek_api_key),
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": TOPIC_MERGE_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 250,
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                "{}/chat/completions".format(config.deepseek_api_url),
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                return {"decision": "SEPARATE", "reason": "LLM error", "error": True}

            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()

            # Parse JSON response
            result = extract_json(content)
            decision = result.get("decision", "SEPARATE").upper()

            # Handle PARTIAL merge
            if decision == "PARTIAL":
                merge_indices = result.get("merge", [])
                # Convert 1-indexed to event IDs
                merge_event_ids = [
                    event_ids[i - 1] for i in merge_indices if 1 <= i <= len(event_ids)
                ]
                return {
                    "decision": "PARTIAL",
                    "merge_ids": merge_event_ids,
                    "reason": result.get("reason", ""),
                    "error": False,
                }

            return {
                "decision": decision,
                "reason": result.get("reason", ""),
                "error": False,
            }

    except Exception as e:
        return {"decision": "SEPARATE", "reason": str(e), "error": True}


def extract_json(text: str) -> dict:
    """Extract JSON from LLM response."""
    import re

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

    return {"decision": "SEPARATE", "reason": "Failed to parse LLM response"}


# =============================================================================
# MERGE EXECUTION
# =============================================================================


def merge_topics(conn, events: dict, event_ids: list) -> str:
    """
    Merge multiple topics into one.
    Keeps the largest topic, moves all titles to it.
    Returns: ID of merged topic
    """
    # Find largest topic
    sorted_ids = sorted(event_ids, key=lambda x: events[x]["count"], reverse=True)
    target_id = sorted_ids[0]
    source_ids = sorted_ids[1:]

    cur = conn.cursor()

    # Move all titles from source topics to target
    for source_id in source_ids:
        cur.execute(
            """
            UPDATE event_v3_titles
            SET event_id = %s
            WHERE event_id = %s
            """,
            (target_id, source_id),
        )

        # Delete source topic
        cur.execute(
            """
            DELETE FROM events_v3
            WHERE id = %s
            """,
            (source_id,),
        )

    # Update target topic count
    cur.execute(
        """
        UPDATE events_v3
        SET source_batch_count = (
            SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
        ),
        updated_at = NOW()
        WHERE id = %s
        """,
        (target_id, target_id),
    )

    conn.commit()
    return target_id


# =============================================================================
# TOPIC LIMITS (DYNAMIC)
# =============================================================================


def calculate_dynamic_limits(
    total_titles: int, bucket_titles: int, is_domestic: bool
) -> int:
    """
    Calculate dynamic topic limit based on title count.

    Philosophy:
    - Small buckets (< 50 titles): 3-5 topics max
    - Medium buckets (50-200 titles): 5-15 topics
    - Large buckets (200-1000 titles): 15-30 topics
    - Very large buckets (1000+ titles): 30-50 topics

    Also applies minimum title threshold per topic (3 titles).
    """
    if is_domestic:
        # Domestic gets more topics
        if bucket_titles < 50:
            return max(3, bucket_titles // 10)
        elif bucket_titles < 200:
            return max(5, min(15, bucket_titles // 15))
        elif bucket_titles < 1000:
            return max(15, min(30, bucket_titles // 30))
        else:
            return max(30, min(50, bucket_titles // 40))
    else:
        # Bilateral buckets - fewer topics
        if bucket_titles < 30:
            return max(2, bucket_titles // 10)
        elif bucket_titles < 100:
            return max(3, min(8, bucket_titles // 15))
        elif bucket_titles < 300:
            return max(5, min(12, bucket_titles // 25))
        else:
            return max(8, min(15, bucket_titles // 30))


def apply_topic_limits(
    conn,
    ctm_id: str,
    events: dict,
    ctm_title_count: int,
    dry_run: bool = False,
) -> dict:
    """
    Apply dynamic topic limits per bucket.
    Limits are calculated based on bucket size, not fixed values.
    """
    # Group by bucket
    by_bucket = defaultdict(list)
    catchall_id = None

    for event_id, data in events.items():
        if data["is_catchall"]:
            catchall_id = event_id
        else:
            by_bucket[data["bucket_key"]].append((event_id, data["count"]))

    # Sort each bucket by count
    for bucket in by_bucket:
        by_bucket[bucket].sort(key=lambda x: x[1], reverse=True)

    results = {
        "kept": 0,
        "merged_to_other": 0,
        "merged_titles": 0,
        "bucket_limits": {},
    }

    # Process domestic (None bucket)
    domestic = by_bucket.get(None, [])
    domestic_titles = sum(t[1] for t in domestic)
    domestic_limit = calculate_dynamic_limits(
        ctm_title_count, domestic_titles, is_domestic=True
    )
    results["bucket_limits"]["domestic"] = {
        "titles": domestic_titles,
        "limit": domestic_limit,
    }

    if len(domestic) > domestic_limit:
        keep = domestic[:domestic_limit]
        merge = domestic[domestic_limit:]

        results["kept"] += len(keep)
        results["merged_to_other"] += len(merge)
        results["merged_titles"] += sum(t[1] for t in merge)

        if not dry_run and catchall_id:
            for event_id, count in merge:
                move_titles_to_catchall(conn, event_id, catchall_id)
    else:
        results["kept"] += len(domestic)

    # Process bilateral buckets
    for bucket_key, topics in by_bucket.items():
        if bucket_key is None:
            continue

        bucket_titles = sum(t[1] for t in topics)
        bucket_limit = calculate_dynamic_limits(
            ctm_title_count, bucket_titles, is_domestic=False
        )
        results["bucket_limits"][bucket_key] = {
            "titles": bucket_titles,
            "limit": bucket_limit,
        }

        if len(topics) > bucket_limit:
            keep = topics[:bucket_limit]
            merge = topics[bucket_limit:]

            results["kept"] += len(keep)
            results["merged_to_other"] += len(merge)
            results["merged_titles"] += sum(t[1] for t in merge)

            if not dry_run and catchall_id:
                for event_id, count in merge:
                    move_titles_to_catchall(conn, event_id, catchall_id)
        else:
            results["kept"] += len(topics)

    return results


def move_titles_to_catchall(conn, source_id: str, catchall_id: str):
    """Move all titles from a topic to the catchall event."""
    cur = conn.cursor()

    # Move titles
    cur.execute(
        """
        UPDATE event_v3_titles
        SET event_id = %s
        WHERE event_id = %s
        """,
        (catchall_id, source_id),
    )

    # Delete source topic
    cur.execute(
        """
        DELETE FROM events_v3
        WHERE id = %s
        """,
        (source_id,),
    )

    # Update catchall count
    cur.execute(
        """
        UPDATE events_v3
        SET source_batch_count = (
            SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
        ),
        updated_at = NOW()
        WHERE id = %s
        """,
        (catchall_id, catchall_id),
    )

    conn.commit()


# =============================================================================
# OTHER COVERAGE REASSIGNMENT
# =============================================================================


def get_catchall_titles_with_signals(conn, catchall_id: str) -> list:
    """Get titles from catchall event with their signals."""
    cur = conn.cursor()

    cur.execute(
        """
        SELECT t.id, t.title_display,
               tl.persons, tl.orgs, tl.places, tl.commodities, tl.policies
        FROM event_v3_titles evt
        JOIN titles_v3 t ON t.id = evt.title_id
        LEFT JOIN title_labels tl ON tl.title_id = t.id
        WHERE evt.event_id = %s
        """,
        (catchall_id,),
    )

    titles = []
    for row in cur.fetchall():
        title_id, title_display, persons, orgs, places, commodities, policies = row
        signals = set()
        if persons:
            signals.update(persons)
        if orgs:
            signals.update(orgs)
        if places:
            signals.update(places)
        if commodities:
            signals.update(commodities)
        if policies:
            signals.update(policies)

        titles.append(
            {
                "id": title_id,
                "title_display": title_display,
                "signals": signals,
            }
        )

    return titles


def find_reassignment_candidates(
    catchall_titles: list,
    regular_events: dict,
    similarity_threshold: float = 0.3,
) -> list:
    """
    Find catchall titles that could be reassigned to existing topics.
    Uses both signal similarity AND title text similarity against event titles.
    Returns: [{title_id, target_event_id, similarity}]
    """
    candidates = []

    for title in catchall_titles:
        best_match = None
        best_similarity = 0

        for event_id, event in regular_events.items():
            if event["is_catchall"]:
                continue

            # Signal similarity
            event_signals = get_all_signals(event)
            sig_sim = 0
            if title["signals"] and event_signals:
                sig_sim = jaccard_similarity(title["signals"], event_signals)

            # Title text similarity: compare catchall headline vs event title
            # This catches cases where signals differ but the story is the same
            title_sim = title_similarity(
                [title["title_display"]], [event.get("title", "")]
            )

            # Best of signal or title similarity
            combined_sim = max(sig_sim, title_sim)

            if combined_sim > best_similarity:
                best_similarity = combined_sim
                best_match = event_id

        if best_match and best_similarity >= similarity_threshold:
            candidates.append(
                {
                    "title_id": title["id"],
                    "title_display": title["title_display"],
                    "target_event_id": best_match,
                    "target_title": regular_events[best_match]["title"],
                    "similarity": best_similarity,
                    "shared_signals": title["signals"]
                    & get_all_signals(regular_events[best_match]),
                }
            )

    # Sort by similarity descending
    candidates.sort(key=lambda x: x["similarity"], reverse=True)
    return candidates


def reassign_title_to_topic(
    conn, title_id: str, source_event_id: str, target_event_id: str
):
    """Move a single title from one event to another."""
    cur = conn.cursor()

    # Update event_v3_titles
    cur.execute(
        """
        UPDATE event_v3_titles
        SET event_id = %s
        WHERE title_id = %s AND event_id = %s
        """,
        (target_event_id, title_id, source_event_id),
    )

    # Update counts for both events
    cur.execute(
        """
        UPDATE events_v3
        SET source_batch_count = (
            SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
        ),
        updated_at = NOW()
        WHERE id = %s
        """,
        (source_event_id, source_event_id),
    )

    cur.execute(
        """
        UPDATE events_v3
        SET source_batch_count = (
            SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
        ),
        updated_at = NOW()
        WHERE id = %s
        """,
        (target_event_id, target_event_id),
    )

    conn.commit()


def process_catchall_reassignment(
    conn,
    ctm_id: str,
    events: dict,
    similarity_threshold: float = 0.25,
    max_reassignments: int = 100,
    dry_run: bool = False,
) -> dict:
    """
    Review catchall titles and reassign to existing topics where appropriate.
    """
    # Find catchall event
    catchall_id = None
    for event_id, event in events.items():
        if event["is_catchall"]:
            catchall_id = event_id
            break

    if not catchall_id:
        return {"reassigned": 0, "candidates": 0}

    # Get catchall titles with signals
    catchall_titles = get_catchall_titles_with_signals(conn, catchall_id)

    if not catchall_titles:
        return {"reassigned": 0, "candidates": 0}

    # Find reassignment candidates
    candidates = find_reassignment_candidates(
        catchall_titles, events, similarity_threshold
    )

    # Limit reassignments
    candidates = candidates[:max_reassignments]

    results = {
        "candidates": len(candidates),
        "reassigned": 0,
    }

    for c in candidates:
        if dry_run:
            results["reassigned"] += 1
        else:
            reassign_title_to_topic(
                conn, c["title_id"], catchall_id, c["target_event_id"]
            )
            results["reassigned"] += 1

    return results


# =============================================================================
# STEP C.5: GENERIC SIGNAL CLEANUP
# =============================================================================


def compute_signal_frequencies(events: dict) -> dict:
    """
    Count how many topics each signal appears in.
    Returns: {signal: topic_count}
    """
    signal_topics = defaultdict(set)

    for event_id, event in events.items():
        if event["is_catchall"]:
            continue

        all_signals = get_all_signals(event)
        for sig in all_signals:
            signal_topics[sig.lower()].add(event_id)

    return {sig: len(topics) for sig, topics in signal_topics.items()}


def find_suspicious_topics(
    events: dict,
    signal_frequencies: dict,
    generic_threshold: int = GENERIC_SIGNAL_TOPIC_THRESHOLD,
    max_titles: int = SUSPICIOUS_TOPIC_MAX_TITLES,
) -> list:
    """
    Find topics that may contain mixed/unrelated content.

    A topic is suspicious if:
    1. It has no specific ANCHOR signals (persons or orgs with < 5 topic appearances)
    2. AND it has fewer than 12 titles (not a legitimate broad topic)

    Note: places, commodities, policies are NOT considered anchors even if rare,
    because they can appear incidentally (e.g., "Europe" mentioned in passing).
    Only persons and orgs provide meaningful topic identity.

    Returns: [{event_id, signals, generic_signals, title_count, sample_titles}]
    """
    suspicious = []

    for event_id, event in events.items():
        if event["is_catchall"]:
            continue

        # Skip large topics - they're likely legitimate broad coverage
        if event["count"] >= max_titles:
            continue

        # Check for specific ANCHOR signals (persons or orgs only)
        # Places, commodities, policies can be incidental
        has_specific_anchor = False

        # Check persons
        for sig in event.get("persons", set()):
            sig_lower = sig.lower()
            freq = signal_frequencies.get(sig_lower, 1)
            if freq < generic_threshold:
                has_specific_anchor = True
                break

        # Check orgs
        if not has_specific_anchor:
            for sig in event.get("orgs", set()):
                sig_lower = sig.lower()
                freq = signal_frequencies.get(sig_lower, 1)
                if freq < generic_threshold:
                    has_specific_anchor = True
                    break

        # If no specific person/org anchor, this topic is suspicious
        if not has_specific_anchor:
            all_signals = get_all_signals(event)
            generic_signals = set()
            for sig in all_signals:
                sig_lower = sig.lower()
                freq = signal_frequencies.get(sig_lower, 1)
                if freq >= generic_threshold:
                    generic_signals.add(sig)

            if generic_signals:  # Must have at least some generic signals
                suspicious.append(
                    {
                        "event_id": event_id,
                        "title": event["title"],
                        "count": event["count"],
                        "bucket_key": event["bucket_key"],
                        "generic_signals": generic_signals,
                        "sample_titles": event["sample_titles"],
                    }
                )

    # Sort by title count ascending (smallest = most suspicious)
    suspicious.sort(key=lambda x: x["count"])
    return suspicious


def find_sibling_topics(
    events: dict,
    suspicious_topic: dict,
    signal_frequencies: dict,
    generic_threshold: int = GENERIC_SIGNAL_TOPIC_THRESHOLD,
) -> list:
    """
    Find topics that share the same generic signal but have specific anchors.
    These are potential homes for titles from the suspicious topic.

    E.g., for a "sanctions" topic, find "sanctions+Iran", "sanctions+Russia", etc.
    """
    generic_signals = suspicious_topic["generic_signals"]
    siblings = []

    for event_id, event in events.items():
        if event["is_catchall"]:
            continue
        if event_id == suspicious_topic["event_id"]:
            continue

        event_signals = get_all_signals(event)

        # Must share at least one generic signal
        shared_generic = generic_signals & event_signals
        if not shared_generic:
            continue

        # Must have at least one specific (non-generic) signal
        has_specific = False
        for sig in event_signals:
            sig_lower = sig.lower()
            freq = signal_frequencies.get(sig_lower, 1)
            if freq < generic_threshold:
                has_specific = True
                break

        if has_specific:
            siblings.append(
                {
                    "event_id": event_id,
                    "title": event["title"],
                    "count": event["count"],
                    "bucket_key": event["bucket_key"],
                    "shared_generic": shared_generic,
                    "all_signals": event_signals,
                }
            )

    # Sort by count descending (prefer larger, more established topics)
    siblings.sort(key=lambda x: -x["count"])
    return siblings


# MIXED_TOPIC_REVIEW_PROMPT imported from core.prompts


def review_suspicious_topic_with_llm(
    suspicious: dict,
    siblings: list,
    events: dict,
) -> dict:
    """
    Ask LLM to review a suspicious topic and determine if it's mixed.
    Returns: {"coherent": True} or {"coherent": False, "groups": [...]}
    """
    # Format titles
    titles_lines = []
    for i, title in enumerate(suspicious["sample_titles"], 1):
        safe_title = title[:100] if title else "[no title]"
        titles_lines.append("{}. {}".format(i, safe_title))
    titles_text = "\n".join(titles_lines)

    # Format siblings
    if siblings:
        sibling_lines = []
        for sib in siblings[:5]:  # Top 5 siblings
            sibling_lines.append(
                "- {} [{}]: {} (shared: {})".format(
                    sib["event_id"],
                    sib["count"],
                    sib["title"][:50],
                    ", ".join(list(sib["shared_generic"])[:3]),
                )
            )
        siblings_text = "\n".join(sibling_lines)
    else:
        siblings_text = "(no specific sibling topics found)"

    prompt = MIXED_TOPIC_REVIEW_PROMPT.format(
        topic_title=suspicious["title"][:60],
        count=suspicious["count"],
        bucket=suspicious["bucket_key"] or "Domestic",
        titles_text=titles_text,
        siblings_text=siblings_text,
    )

    headers = {
        "Authorization": "Bearer {}".format(config.deepseek_api_key),
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.llm_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 500,
    }

    try:
        response = httpx.post(
            "{}/chat/completions".format(config.deepseek_api_url),
            headers=headers,
            json=payload,
            timeout=30.0,
        )

        if response.status_code != 200:
            return {"coherent": True, "error": "API error"}

        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

        # Parse JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)
        return result

    except Exception as e:
        return {"coherent": True, "error": str(e)}


def get_title_ids_for_event(conn, event_id: str) -> list:
    """Get all title IDs for an event."""
    cur = conn.cursor()
    cur.execute(
        "SELECT title_id FROM event_v3_titles WHERE event_id = %s",
        (event_id,),
    )
    return [str(row[0]) for row in cur.fetchall()]


def process_generic_signal_cleanup(
    conn,
    ctm_id: str,
    events: dict,
    max_reviews: int = 25,
    dry_run: bool = False,
) -> dict:
    """
    Find and clean up topics with only generic signals.

    1. Compute which signals are "generic" (appear in 5+ topics)
    2. Find suspicious topics (only generic signals + small count)
    3. LLM review to determine if mixed
    4. Reassign titles to sibling topics or "Other"
    """
    results = {
        "signal_frequencies": {},
        "suspicious_found": 0,
        "reviewed": 0,
        "mixed_topics": 0,
        "titles_reassigned": 0,
    }

    # Step 1: Compute signal frequencies
    signal_freq = compute_signal_frequencies(events)
    results["signal_frequencies"] = {
        sig: freq for sig, freq in sorted(signal_freq.items(), key=lambda x: -x[1])[:10]
    }

    # Step 2: Find suspicious topics
    suspicious = find_suspicious_topics(events, signal_freq)
    results["suspicious_found"] = len(suspicious)

    if not suspicious:
        return results

    # Find catchall for reassignment fallback
    catchall_id = None
    for event_id, event in events.items():
        if event["is_catchall"]:
            catchall_id = event_id
            break

    # Step 3: Review each suspicious topic
    for topic in suspicious[:max_reviews]:
        results["reviewed"] += 1

        # Find sibling topics
        siblings = find_sibling_topics(events, topic, signal_freq)

        # LLM review
        review = review_suspicious_topic_with_llm(topic, siblings, events)

        if review.get("coherent", True):
            continue

        results["mixed_topics"] += 1
        groups = review.get("groups", [])

        if dry_run:
            print(
                "    Would split topic [{}]: {}".format(
                    topic["count"], topic["title"][:40]
                )
            )
            for g in groups:
                print(
                    "      -> titles {} to {}".format(
                        g["title_indices"],
                        (
                            g.get("best_sibling", "Other")[:20]
                            if g.get("best_sibling")
                            else "Other"
                        ),
                    )
                )
            continue

        # Get actual title IDs for this event
        title_ids = get_title_ids_for_event(conn, topic["event_id"])

        # Process each group
        for group in groups:
            indices = group.get("title_indices", [])
            target_id = group.get("best_sibling")

            # Validate target exists
            if target_id and target_id not in events:
                target_id = None

            # Default to catchall if no valid target
            if not target_id:
                target_id = catchall_id

            if not target_id:
                continue

            # Reassign titles (indices are 1-based, matching sample_titles order)
            for idx in indices:
                if 1 <= idx <= len(title_ids):
                    title_id = title_ids[idx - 1]
                    reassign_title_to_topic(
                        conn, title_id, topic["event_id"], target_id
                    )
                    results["titles_reassigned"] += 1

    return results


# =============================================================================
# MAIN
# =============================================================================


def process_ctm(
    ctm_id: str = None,
    centroid: str = None,
    track: str = None,
    dry_run: bool = False,
    similarity_threshold: float = 0.3,
):
    """
    Run topic aggregation on a CTM.
    """
    conn = get_connection()

    # Get CTM info
    ctm = get_ctm_info(conn, ctm_id, centroid, track)
    if not ctm:
        print("CTM not found")
        conn.close()
        return

    print("=" * 70)
    print("TOPIC AGGREGATION {}".format("(DRY RUN)" if dry_run else ""))
    print("=" * 70)
    print("CTM: {} / {} / {}".format(ctm["centroid_id"], ctm["track"], ctm["month"]))
    print("Titles: {}".format(ctm["title_count"]))
    print()

    # Load topics with signals
    events = get_topics_with_signals(conn, ctm["id"])
    print("Loaded {} topics".format(len(events)))

    # Step A: Find merge candidates
    print()
    print("-" * 70)
    print(
        "STEP A: MERGE CANDIDATES (similarity >= {:.0%})".format(similarity_threshold)
    )
    print("-" * 70)

    candidates = find_merge_candidates(events, similarity_threshold)
    print("Found {} candidate groups".format(len(candidates)))

    # Step B: LLM review (SKIP if no candidates - saves LLM calls)
    print()
    print("-" * 70)
    print("STEP B: LLM REVIEW")
    print("-" * 70)

    merge_decisions = []

    if not candidates:
        print("  No merge candidates - skipping LLM review")
    else:
        for i, candidate in enumerate(candidates[:20], 1):  # Limit to 20 reviews
            event_ids = candidate["events"]
            print(
                "Reviewing group {} ({} topics, bucket={})...".format(
                    i, len(event_ids), candidate["bucket_key"]
                )
            )

            # Show what's being reviewed
            for eid in event_ids[:3]:
                e = events[eid]
                print(
                    "  - [{}] {}".format(
                        e["count"], e["title"][:50] if e["title"] else "?"
                    )
                )

            review = review_merge_with_llm(events, candidate)
            print("  >> {} - {}".format(review["decision"], review["reason"][:60]))

            if review["decision"] == "MERGE":
                merge_decisions.append(
                    {
                        "events": candidate["events"],
                        "bucket_key": candidate["bucket_key"],
                    }
                )
            elif review["decision"] == "PARTIAL":
                merge_ids = review.get("merge_ids", [])
                if len(merge_ids) >= 2:
                    merge_decisions.append(
                        {"events": merge_ids, "bucket_key": candidate["bucket_key"]}
                    )

    # Execute merges
    print()
    print("-" * 70)
    print("STEP B RESULTS: {} groups to merge".format(len(merge_decisions)))
    print("-" * 70)

    merged_count = 0
    merged_titles = 0

    for candidate in merge_decisions:
        event_ids = candidate["events"]
        total_titles = sum(events[eid]["count"] for eid in event_ids)

        if dry_run:
            print(
                "  Would merge {} topics ({} titles) in bucket {}".format(
                    len(event_ids), total_titles, candidate["bucket_key"]
                )
            )
        else:
            target_id = merge_topics(conn, events, event_ids)
            print(
                "  Merged {} topics ({} titles) -> {}".format(
                    len(event_ids), total_titles, target_id[:8]
                )
            )

        merged_count += len(event_ids) - 1
        merged_titles += total_titles

    # Step C: Apply topic limits (dynamic based on bucket size)
    print()
    print("-" * 70)
    print("STEP C: TOPIC LIMITS (dynamic based on bucket size)")
    print("-" * 70)

    # Reload events after merges
    if not dry_run and merge_decisions:
        events = get_topics_with_signals(conn, ctm["id"])

    limits_result = apply_topic_limits(
        conn,
        ctm["id"],
        events,
        ctm_title_count=ctm["title_count"],
        dry_run=dry_run,
    )

    # Show dynamic limits for key buckets
    bucket_limits = limits_result.get("bucket_limits", {})
    if "domestic" in bucket_limits:
        bl = bucket_limits["domestic"]
        print(
            "  Domestic: {} titles -> {} topic limit".format(bl["titles"], bl["limit"])
        )

    # Show top 3 bilateral buckets
    bilateral = [(k, v) for k, v in bucket_limits.items() if k != "domestic"]
    bilateral.sort(key=lambda x: x[1]["titles"], reverse=True)
    for bucket_key, bl in bilateral[:3]:
        print(
            "  {}: {} titles -> {} topic limit".format(
                bucket_key, bl["titles"], bl["limit"]
            )
        )

    print()
    print("  Topics kept: {}".format(limits_result["kept"]))
    print("  Topics merged to Other: {}".format(limits_result["merged_to_other"]))
    print("  Titles moved to Other: {}".format(limits_result["merged_titles"]))

    # Step C.5: Generic signal cleanup
    print()
    print("-" * 70)
    print("STEP C.5: GENERIC SIGNAL CLEANUP")
    print("-" * 70)

    # Reload events after limits
    if not dry_run and limits_result["merged_to_other"] > 0:
        events = get_topics_with_signals(conn, ctm["id"])

    cleanup_result = process_generic_signal_cleanup(
        conn,
        ctm["id"],
        events,
        max_reviews=25,
        dry_run=dry_run,
    )

    if cleanup_result["suspicious_found"] == 0:
        print("  No suspicious topics - skipping LLM review")
    else:
        # Show top generic signals
        if cleanup_result["signal_frequencies"]:
            print("  Top generic signals (appear in 5+ topics):")
            for sig, freq in list(cleanup_result["signal_frequencies"].items())[:5]:
                if freq >= GENERIC_SIGNAL_TOPIC_THRESHOLD:
                    print("    {} -> {} topics".format(sig, freq))

        print()
        print(
            "  Suspicious topics found: {}".format(cleanup_result["suspicious_found"])
        )
        print("  Topics reviewed: {}".format(cleanup_result["reviewed"]))
        print("  Mixed topics detected: {}".format(cleanup_result["mixed_topics"]))
        print("  Titles reassigned: {}".format(cleanup_result["titles_reassigned"]))

    # Step D: Other Coverage reassignment
    print()
    print("-" * 70)
    print("STEP D: OTHER COVERAGE REASSIGNMENT (similarity >= 25%)")
    print("-" * 70)

    # Reload events after cleanup
    if not dry_run and cleanup_result["titles_reassigned"] > 0:
        events = get_topics_with_signals(conn, ctm["id"])

    reassign_result = process_catchall_reassignment(
        conn,
        ctm["id"],
        events,
        similarity_threshold=0.25,
        max_reassignments=100,
        dry_run=dry_run,
    )

    print("  Candidates found: {}".format(reassign_result["candidates"]))
    print("  Titles reassigned: {}".format(reassign_result["reassigned"]))

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("Merge candidates found: {}".format(len(candidates)))
    print("Merges approved by LLM: {}".format(len(merge_decisions)))
    print("Topics merged: {}".format(merged_count))
    print("Topics moved to Other: {}".format(limits_result["merged_to_other"]))
    print("Mixed topics cleaned up: {}".format(cleanup_result["mixed_topics"]))
    print("Titles reassigned (cleanup): {}".format(cleanup_result["titles_reassigned"]))
    print("Titles reassigned from Other: {}".format(reassign_result["reassigned"]))

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 4.2: Topic Aggregation")
    parser.add_argument("--ctm-id", type=str, help="CTM ID to process")
    parser.add_argument("--centroid", type=str, help="Centroid ID (e.g., AMERICAS-USA)")
    parser.add_argument("--track", type=str, help="Track (e.g., geo_economy)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Analyze only, don't modify"
    )
    parser.add_argument(
        "--similarity",
        type=float,
        default=0.3,
        help="Similarity threshold for merge candidates (default: 0.3)",
    )

    args = parser.parse_args()

    if not args.ctm_id and not (args.centroid and args.track):
        parser.error("Either --ctm-id or both --centroid and --track required")

    process_ctm(
        ctm_id=args.ctm_id,
        centroid=args.centroid,
        track=args.track,
        dry_run=args.dry_run,
        similarity_threshold=args.similarity,
    )
