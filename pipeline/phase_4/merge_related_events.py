"""
Phase 4.3: Cross-Bucket Event Merging

Uses LLM to detect events within the same CTM that describe the same story
but ended up in different geographic buckets (domestic vs bilateral) or
fragmented due to weak signal overlap.

Only runs on CTMs containing at least one high-importance event.
Merges sub-stories into the main event and updates title + summary.

Usage:
    python pipeline/phase_4/merge_related_events.py --ctm-id <uuid>
    python pipeline/phase_4/merge_related_events.py --centroid MIDEAST-IRAN --track geo_politics
    python pipeline/phase_4/merge_related_events.py --ctm-id <uuid> --dry-run
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx
import psycopg2

from core.config import config
from core.llm_utils import extract_json

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

logger = logging.getLogger(__name__)

# Minimum importance score for a CTM to qualify for merge pass
CTM_IMPORTANCE_THRESHOLD = 0.5

# Minimum events in a CTM to bother with merge pass
MIN_EVENTS_FOR_MERGE = 4

# =============================================================================
# PROMPTS
# =============================================================================

MERGE_SYSTEM_PROMPT = """You identify news events that describe the SAME real-world story \
within a country's intelligence briefing.

Events may appear separate because they entered through different geographic angles \
(domestic vs bilateral) or because early clustering split them before the full picture emerged. \
Your job: find groups that are clearly the SAME story and should be merged.

MERGE when:
- Events describe the same core development from different angles (domestic vs international framing)
- One event is a direct sub-story of another (e.g., "Leader killed" and "Succession begins" = same story arc)
- Events cover the same specific action/decision but emphasize different actors involved

KEEP SEPARATE when:
- Events share a theme but cover genuinely different developments
- Events involve the same actors but different actions (e.g., "Trump tariffs" vs "Trump Greenland")
- Events involve the same country pair but different topics (e.g., "US threatens Spain over bases" vs "Amazon invests in Spain" are SEPARATE)
- Connection is only thematic (both about "economy" or "security" is NOT enough)
- One event is about government policy and the other about private sector activity, even if same countries

When in doubt, keep SEPARATE. A wrong merge destroys information. A missed merge is harmless.

For each merged group, also produce:
- An updated title (under 120 chars) that captures the full story
- An updated summary (2-4 sentences) written from the centroid's perspective -- \
prioritize how this story matters to and is framed by the centroid country"""

MERGE_USER_PROMPT = """CTM: {centroid_label} / {track} / {month}

Events (ID, bucket, sources, title, summary):
{events_text}

Which events describe the SAME real-world story and should be merged?

Return JSON:
{{
  "groups": [
    {{
      "event_ids": ["id1", "id2", ...],
      "updated_title": "Merged title capturing full story",
      "updated_summary": "2-4 sentence summary incorporating all perspectives."
    }}
  ]
}}

Rules:
- Only include groups of 2+ events that should merge. Omit singletons.
- If no merges are needed, return {{"groups": []}}
- event_ids must be valid IDs from the list above
- An event may appear in at most one group
- updated_title must be under 120 characters"""


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


def load_merge_candidates(conn, ctm_id):
    """Load all non-catchall, non-merged events with LLM-generated titles."""
    cur = conn.cursor()
    cur.execute(
        """SELECT e.id, e.event_type, e.bucket_key, e.source_batch_count,
                  e.title, e.summary, e.importance_score
           FROM events_v3 e
           WHERE e.ctm_id = %s
             AND e.is_catchall = FALSE
             AND e.merged_into IS NULL
             AND e.title IS NOT NULL
           ORDER BY e.source_batch_count DESC""",
        (ctm_id,),
    )
    events = []
    for r in cur.fetchall():
        events.append(
            {
                "id": str(r[0]),
                "event_type": r[1],
                "bucket_key": r[2] or "",
                "source_batch_count": r[3] or 0,
                "title": r[4],
                "summary": r[5] or "",
                "importance_score": r[6] or 0,
            }
        )
    return events


def get_ctm_info(conn, ctm_id):
    """Get centroid label, track, month for a CTM."""
    cur = conn.cursor()
    cur.execute(
        """SELECT c.label, ct.track, ct.month
           FROM ctm ct
           JOIN centroids_v3 c ON c.id = ct.centroid_id
           WHERE ct.id = %s""",
        (ctm_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {"label": row[0], "track": row[1], "month": row[2]}


def find_ctms_needing_merge(conn, include_frozen=False):
    """Find CTMs with at least one high-importance event and enough events to merge."""
    cur = conn.cursor()
    frozen_clause = "" if include_frozen else "AND ct.is_frozen = FALSE"
    cur.execute(
        """SELECT ct.id, ct.centroid_id, ct.track,
                  COUNT(e.id) as event_count,
                  MAX(e.importance_score) as max_importance
           FROM ctm ct
           JOIN events_v3 e ON e.ctm_id = ct.id
           WHERE e.is_catchall = FALSE
             AND e.merged_into IS NULL
             AND e.title IS NOT NULL
             {}
           GROUP BY ct.id, ct.centroid_id, ct.track
           HAVING MAX(e.importance_score) >= %s
              AND COUNT(e.id) >= %s
           ORDER BY MAX(e.importance_score) DESC""".format(
            frozen_clause
        ),
        (CTM_IMPORTANCE_THRESHOLD, MIN_EVENTS_FOR_MERGE),
    )
    return [
        {
            "ctm_id": str(r[0]),
            "centroid_id": r[1],
            "track": r[2],
            "event_count": r[3],
            "max_importance": r[4],
        }
        for r in cur.fetchall()
    ]


# =============================================================================
# LLM
# =============================================================================


def call_llm(system_prompt, user_prompt):
    """Call DeepSeek and return parsed JSON."""
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
        "temperature": 0.1,
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
                        "LLM error: {} {}".format(
                            response.status_code, response.text[:200]
                        )
                    )
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
            return extract_json(content)
        except Exception as e:
            last_error = e
            if attempt < config.llm_retry_attempts - 1:
                import time

                wait = config.llm_retry_backoff**attempt
                time.sleep(wait)

    raise RuntimeError("LLM failed after retries: {}".format(last_error))


def build_merge_prompt(events, ctm_info):
    """Format events for the merge prompt."""
    month_str = str(ctm_info["month"])[:7] if ctm_info["month"] else "unknown"

    lines = []
    for ev in events:
        bucket_label = ev["event_type"]
        if ev["bucket_key"]:
            bucket_label = "bilateral/{}".format(ev["bucket_key"])

        summary_snippet = ev["summary"][:200] if ev["summary"] else "(no summary)"
        lines.append(
            '[{id}] ({bucket}, {src} sources) "{title}"\n    {summary}'.format(
                id=ev["id"][:8],
                bucket=bucket_label,
                src=ev["source_batch_count"],
                title=ev["title"],
                summary=summary_snippet,
            )
        )

    return MERGE_USER_PROMPT.format(
        centroid_label=ctm_info["label"],
        track=ctm_info["track"],
        month=month_str,
        events_text="\n\n".join(lines),
    )


# =============================================================================
# MERGE EXECUTION
# =============================================================================


def pick_anchor(events_in_group):
    """Pick the surviving event: domestic preferred, but source count wins ties.

    Domestic priority only applies when the domestic event has at least
    half the sources of the largest event. Otherwise, the biggest event wins
    regardless of bucket (a 2-source domestic shouldn't anchor a 125-source group).
    """
    biggest = max(events_in_group, key=lambda e: e["source_batch_count"])
    domestic = [e for e in events_in_group if e["event_type"] == "domestic"]
    if domestic:
        best_domestic = max(domestic, key=lambda e: e["source_batch_count"])
        if best_domestic["source_batch_count"] >= biggest["source_batch_count"] * 0.5:
            return best_domestic
    return biggest


def execute_merges(conn, events, merge_groups, dry_run=False):
    """Execute merge groups: re-link titles, update anchor, mark absorbed."""
    events_by_id = {}
    for ev in events:
        events_by_id[ev["id"]] = ev
        events_by_id[ev["id"][:8]] = ev  # short ID lookup

    cur = conn.cursor()
    total_merged = 0

    for group in merge_groups:
        eids = group.get("event_ids", [])
        if len(eids) < 2:
            continue

        # Resolve short IDs to full IDs
        group_events = []
        for eid in eids:
            ev = events_by_id.get(eid)
            if ev:
                group_events.append(ev)

        if len(group_events) < 2:
            continue

        anchor = pick_anchor(group_events)
        absorbed = [e for e in group_events if e["id"] != anchor["id"]]

        updated_title = group.get("updated_title", anchor["title"])
        updated_summary = group.get("updated_summary", anchor["summary"])

        # Truncate title to 120 chars
        if len(updated_title) > 120:
            updated_title = updated_title[:117] + "..."

        absorbed_ids = [e["id"] for e in absorbed]
        absorbed_sources = sum(e["source_batch_count"] for e in absorbed)

        print(
            "  MERGE: {} ({} src) absorbs {} events (+{} src)".format(
                anchor["title"][:60],
                anchor["source_batch_count"],
                len(absorbed),
                absorbed_sources,
            )
        )
        for a in absorbed:
            print("    <- {} ({} src)".format(a["title"][:65], a["source_batch_count"]))

        if dry_run:
            total_merged += len(absorbed)
            continue

        # 1. Re-link titles from absorbed events to anchor
        for aid in absorbed_ids:
            cur.execute(
                """UPDATE event_v3_titles SET event_id = %s
                   WHERE event_id = %s
                   AND title_id NOT IN (
                       SELECT title_id FROM event_v3_titles WHERE event_id = %s
                   )""",
                (anchor["id"], aid, anchor["id"]),
            )
            # Remove remaining duplicates (titles already in anchor)
            cur.execute(
                "DELETE FROM event_v3_titles WHERE event_id = %s",
                (aid,),
            )

        # 2. Mark absorbed events
        cur.execute(
            """UPDATE events_v3 SET merged_into = %s, updated_at = NOW()
               WHERE id = ANY(%s::uuid[])""",
            (anchor["id"], absorbed_ids),
        )

        # 3. Update anchor: title, summary, source count
        cur.execute(
            """UPDATE events_v3
               SET title = %s,
                   summary = %s,
                   source_batch_count = (
                       SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
                   ),
                   updated_at = NOW()
               WHERE id = %s""",
            (updated_title, updated_summary, anchor["id"], anchor["id"]),
        )

        total_merged += len(absorbed)

    if not dry_run:
        conn.commit()

    return total_merged


# =============================================================================
# MAIN ENTRY POINTS
# =============================================================================


def process_ctm_merge(conn, ctm_id, dry_run=False):
    """Run cross-bucket merge for a single CTM. Returns count of merged events."""
    ctm_info = get_ctm_info(conn, ctm_id)
    if not ctm_info:
        return 0

    events = load_merge_candidates(conn, ctm_id)
    if len(events) < MIN_EVENTS_FOR_MERGE:
        return 0

    max_imp = max(e["importance_score"] for e in events)
    if max_imp < CTM_IMPORTANCE_THRESHOLD:
        return 0

    print(
        "Phase 4.3: {} / {} -- {} events (max importance {:.2f})".format(
            ctm_info["label"], ctm_info["track"], len(events), max_imp
        )
    )

    prompt = build_merge_prompt(events, ctm_info)
    result = call_llm(MERGE_SYSTEM_PROMPT, prompt)

    groups = result.get("groups", [])
    if not groups:
        print("  No merges needed.")
        return 0

    print("  LLM proposed {} merge group(s)".format(len(groups)))
    merged = execute_merges(conn, events, groups, dry_run=dry_run)
    print("  Merged {} events".format(merged))
    return merged


def run_all(dry_run=False, limit=None, include_frozen=False):
    """Find all CTMs needing merge and process them."""
    conn = get_connection()
    ctms = find_ctms_needing_merge(conn, include_frozen=include_frozen)
    print("Found {} CTMs qualifying for merge pass".format(len(ctms)))

    if limit:
        ctms = ctms[:limit]

    total = 0
    for ctm in ctms:
        try:
            merged = process_ctm_merge(conn, ctm["ctm_id"], dry_run=dry_run)
            total += merged
        except Exception as e:
            print("  ERROR on {} / {}: {}".format(ctm["centroid_id"], ctm["track"], e))

    conn.close()
    print("\nTotal events merged: {}".format(total))
    return total


def main():
    parser = argparse.ArgumentParser(
        description="Phase 4.3: Cross-Bucket Event Merging"
    )
    parser.add_argument("--ctm-id", help="Process a specific CTM")
    parser.add_argument("--centroid", help="Filter by centroid ID")
    parser.add_argument("--track", help="Filter by track")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show merges without executing"
    )
    parser.add_argument("--limit", type=int, help="Max CTMs to process")
    parser.add_argument(
        "--include-frozen",
        action="store_true",
        help="Also process frozen (past-month) CTMs",
    )
    args = parser.parse_args()

    if args.ctm_id:
        conn = get_connection()
        process_ctm_merge(conn, args.ctm_id, dry_run=args.dry_run)
        conn.close()
    elif args.centroid and args.track:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """SELECT id FROM ctm
               WHERE centroid_id = %s AND track = %s AND is_frozen = FALSE
               ORDER BY month DESC LIMIT 1""",
            (args.centroid, args.track),
        )
        row = cur.fetchone()
        if row:
            process_ctm_merge(conn, str(row[0]), dry_run=args.dry_run)
        else:
            print("CTM not found")
        conn.close()
    else:
        run_all(
            dry_run=args.dry_run,
            limit=args.limit,
            include_frozen=args.include_frozen,
        )


if __name__ == "__main__":
    main()
