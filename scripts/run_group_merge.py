"""Within-group LLM merge for all CTMs. Writes merge results to DB."""

import json
import re
import sys
from collections import Counter, defaultdict

import httpx
import psycopg2

sys.path.insert(0, ".")
sys.stdout.reconfigure(errors="replace")

from core.config import config  # noqa: E402

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/sni_v2")
cur = conn.cursor()

DRY_RUN = "--dry-run" in sys.argv
MIN_GROUP_SIZE = 3  # only LLM-merge groups with 3+ events
MIN_CTM_EVENTS = 10  # skip CTMs with fewer emerged events (not worth LLM cost)

MERGE_SYSTEM = (
    "You receive numbered news topics (each with sample headlines). "
    "These topics already share a common signal (person, place, or organization). "
    "Your job: identify which topics belong to the SAME ongoing story thread. "
    "Merge aggressively: different days of the same developing story = SAME thread. "
    "Reactions, consequences, and follow-ups to an event = SAME thread. "
    "Only keep topics standalone if they are genuinely UNRELATED stories that happen "
    "to mention the same entity. Example: a corruption scandal and a military operation "
    "both mentioning the same leader = different threads. "
    'Return JSON: {"merge": [[1,3,7], [2,5]], "standalone": [4,6,8]} '
    "where each inner array is a group of same-story topics. "
    "Topics not in any merge group go to standalone. "
    "When in doubt, MERGE."
)


def llm_call(system, user, max_tokens=2000):
    try:
        resp = httpx.post(
            config.deepseek_api_url + "/chat/completions",
            headers={"Authorization": "Bearer " + config.deepseek_api_key},
            json={
                "model": config.llm_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.1,
                "max_tokens": max_tokens,
            },
            timeout=60,
        )
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def extract_json(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return None


def db_merge_events(anchor_eid, absorbed_eids):
    """Merge absorbed events into anchor event in DB."""
    if not absorbed_eids:
        return
    # Move titles from absorbed to anchor
    for eid in absorbed_eids:
        cur.execute(
            "INSERT INTO event_v3_titles (event_id, title_id) "
            "SELECT %s, title_id FROM event_v3_titles WHERE event_id = %s "
            "ON CONFLICT DO NOTHING",
            (anchor_eid, eid),
        )
        # Soft-delete absorbed event
        cur.execute(
            "UPDATE events_v3 SET merged_into = %s WHERE id = %s",
            (anchor_eid, eid),
        )
    # Update anchor source count
    cur.execute(
        "UPDATE events_v3 SET source_batch_count = "
        "(SELECT count(*) FROM event_v3_titles WHERE event_id = %s), "
        "updated_at = NOW() WHERE id = %s",
        (anchor_eid, anchor_eid),
    )


# --- Load all CTMs with enough events ---
cur.execute(
    """
    SELECT ctm.id, ctm.centroid_id, ctm.track,
           count(*) FILTER (WHERE NOT e.is_catchall AND e.merged_into IS NULL) as emerged
    FROM ctm
    JOIN events_v3 e ON e.ctm_id = ctm.id
    WHERE ctm.month = '2026-03-01'
    GROUP BY ctm.id, ctm.centroid_id, ctm.track
    HAVING count(*) FILTER (WHERE NOT e.is_catchall AND e.merged_into IS NULL) >= %s
    ORDER BY count(*) FILTER (WHERE NOT e.is_catchall AND e.merged_into IS NULL) DESC
""",
    (MIN_CTM_EVENTS,),
)
ctms = cur.fetchall()
print("CTMs to process: %d (>= %d emerged events)" % (len(ctms), MIN_CTM_EVENTS))

total_llm_calls = 0
total_merges = 0

for ctm_idx, (ctm_id, centroid, track, emerged) in enumerate(ctms):
    # Load events with their titles and signals
    cur.execute(
        """
        SELECT e.id, e.topic_core, e.source_batch_count,
               (array_agg(t.title_display ORDER BY t.pubdate_utc DESC))[1:3] as titles
        FROM events_v3 e
        JOIN event_v3_titles et ON et.event_id = e.id
        JOIN titles_v3 t ON t.id = et.title_id
        WHERE e.ctm_id = %s AND NOT e.is_catchall AND e.merged_into IS NULL
        GROUP BY e.id, e.topic_core, e.source_batch_count
    """,
        (ctm_id,),
    )

    events = {}
    for r in cur.fetchall():
        events[str(r[0])] = {
            "id": str(r[0]),
            "anchor": r[1],
            "src": r[2],
            "titles": r[3] or [],
        }

    # Build groups from topic_core (same logic as prototype)
    group_anchors = Counter()
    for ev in events.values():
        a = ev["anchor"]
        if a and not a.startswith("TXT:"):
            clean = re.sub(r" \(general\)$", "", a)
            group_anchors[clean] += 1

    valid_groups = {a for a, c in group_anchors.items() if c >= MIN_GROUP_SIZE}

    groups = defaultdict(list)
    for eid, ev in events.items():
        a = ev["anchor"]
        if a and not a.startswith("TXT:"):
            clean = re.sub(r" \(general\)$", "", a)
            if clean in valid_groups:
                groups[clean].append(eid)

    if not groups:
        continue

    ctm_merges = 0
    ctm_calls = 0

    for anchor, eids in groups.items():
        if len(eids) < MIN_GROUP_SIZE:
            continue

        # Build prompt
        lines = []
        eid_map = {}
        for idx, eid in enumerate(sorted(eids, key=lambda e: -events[e]["src"]), 1):
            ev = events[eid]
            eid_map[idx] = eid
            sample = "\n".join("  - " + t[:80] for t in ev["titles"][:3])
            lines.append("Topic %d (%d sources):\n%s" % (idx, ev["src"], sample))

        user_msg = "\n\n".join(lines)

        if DRY_RUN:
            ctm_calls += 1
            continue

        response = llm_call(MERGE_SYSTEM, user_msg)
        ctm_calls += 1
        result = extract_json(response)

        if not result or "merge" not in result:
            continue

        for merge_group in result.get("merge", []):
            group_eids = [eid_map[n] for n in merge_group if n in eid_map]
            if len(group_eids) < 2:
                continue
            # Anchor = event with most sources
            sorted_eids = sorted(group_eids, key=lambda e: -events[e]["src"])
            anchor_eid = sorted_eids[0]
            absorbed = sorted_eids[1:]
            db_merge_events(anchor_eid, absorbed)
            ctm_merges += len(absorbed)

    if ctm_calls > 0:
        conn.commit()
        total_llm_calls += ctm_calls
        total_merges += ctm_merges
        status = "DRY" if DRY_RUN else "%d merges" % ctm_merges
        print(
            "  [%d/%d] %-25s %-15s %4d events, %2d groups, %2d calls -> %s"
            % (
                ctm_idx + 1,
                len(ctms),
                centroid,
                track,
                emerged,
                len(groups),
                ctm_calls,
                status,
            )
        )

print("\nDone. %d LLM calls, %d total merges." % (total_llm_calls, total_merges))
if DRY_RUN:
    print("(DRY RUN - no changes written)")
conn.close()
