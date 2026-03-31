"""Test: within-group LLM merge + prose generation for one CTM."""

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

CENTROID = sys.argv[1] if len(sys.argv) > 1 else "AMERICAS-USA"
TRACK = sys.argv[2] if len(sys.argv) > 2 else "geo_politics"
WRITE = "--write" in sys.argv
DRY_RUN = not WRITE

# --- Load CTM ---
cur.execute(
    "SELECT id FROM ctm WHERE centroid_id = %s AND track = %s AND month = '2026-03-01'",
    (CENTROID, TRACK),
)
row = cur.fetchone()
if not row:
    print("CTM not found")
    sys.exit(1)
CTM_ID = row[0]

# --- Load all emerged events with titles ---
cur.execute(
    """
    SELECT e.id, e.topic_core, e.source_batch_count,
           array_agg(t.title_display ORDER BY t.pubdate_utc DESC) as titles,
           array_agg(DISTINCT p) FILTER (WHERE p IS NOT NULL) as persons,
           array_agg(DISTINCT pl) FILTER (WHERE pl IS NOT NULL) as places,
           array_agg(DISTINCT o) FILTER (WHERE o IS NOT NULL) as orgs,
           array_agg(DISTINCT tl.target) FILTER (WHERE tl.target IS NOT NULL AND tl.target != 'NONE') as targets
    FROM events_v3 e
    JOIN event_v3_titles et ON et.event_id = e.id
    JOIN titles_v3 t ON t.id = et.title_id
    JOIN title_labels tl ON tl.title_id = t.id
    LEFT JOIN LATERAL unnest(tl.persons) p ON true
    LEFT JOIN LATERAL unnest(tl.places) pl ON true
    LEFT JOIN LATERAL unnest(tl.orgs) o ON true
    WHERE e.ctm_id = %s AND NOT e.is_catchall AND e.merged_into IS NULL
    GROUP BY e.id, e.topic_core, e.source_batch_count
    ORDER BY e.source_batch_count DESC
""",
    (CTM_ID,),
)

events = {}
for r in cur.fetchall():
    events[str(r[0])] = {
        "id": str(r[0]),
        "anchor": r[1],
        "src": r[2],
        "titles": r[3] or [],
        "persons": set(r[4] or []),
        "places": set(r[5] or []),
        "orgs": set(r[6] or []),
        "targets": set(r[7] or []),
    }

print("%s/%s: %d emerged events" % (CENTROID, TRACK, len(events)))

# --- STEP 1: Build groups + rescue ungrouped ---
group_anchors = Counter()
for ev in events.values():
    a = ev["anchor"]
    if a and not a.startswith("TXT:"):
        clean = re.sub(r" \(general\)$", "", a)
        group_anchors[clean] += 1

valid_groups = {a for a, c in group_anchors.items() if c >= 2}

groups = defaultdict(list)  # anchor -> [event_ids]
ungrouped = []

for eid, ev in events.items():
    a = ev["anchor"]
    if a and not a.startswith("TXT:"):
        clean = re.sub(r" \(general\)$", "", a)
        if clean in valid_groups:
            groups[clean].append(eid)
            continue

    # Try rescue: does this event's signals match a group anchor?
    sigs = set()
    for p in ev["persons"]:
        sigs.add("PER:" + p)
    for p in ev["places"]:
        sigs.add("PLC:" + p.upper())
    for o in ev["orgs"]:
        sigs.add("ORG:" + o)
    for t in ev["targets"]:
        for v in t.split(","):
            v = v.strip()
            if v and v != "NONE":
                sigs.add("TGT:" + v)

    matches = sigs & valid_groups
    if matches:
        best = max(matches, key=lambda a: group_anchors[a])
        groups[best].append(eid)
    else:
        ungrouped.append(eid)

rescued = sum(len(eids) for eids in groups.values()) - sum(
    1
    for ev in events.values()
    if ev["anchor"]
    and not ev["anchor"].startswith("TXT:")
    and re.sub(r" \(general\)$", "", ev["anchor"]) in valid_groups
)

print(
    "Step 1: %d groups, %d grouped events (+%d rescued), %d ungrouped"
    % (len(groups), sum(len(v) for v in groups.values()), rescued, len(ungrouped))
)

# --- STEP 2: Within-group LLM merge ---
MIN_SOURCES_FOR_PROSE = 10  # USA threshold

MERGE_SYSTEM = (
    "You receive numbered news topics (each with sample headlines). "
    "Identify which topics describe the SAME specific news story or event. "
    "Different aspects/reactions to the same event count as same story. "
    "Different events involving the same person/place are NOT the same story. "
    'Return JSON: {"merge": [[1,3,7], [2,5]], "standalone": [4,6,8]} '
    "where each inner array is a group of same-story topics. "
    "Topics not in any merge group go to standalone."
)


def llm_call(system, user, max_tokens=2000):
    """Single LLM call."""
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
    except Exception as e:
        print("  LLM error: %s" % e)
        return None


def extract_json(text):
    """Extract JSON from LLM response."""
    if not text:
        return None
    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # Try extracting from markdown code block
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # Try finding JSON object
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return None


print("\nStep 2: Within-group LLM merge")
total_merges = 0
merge_results = (
    {}
)  # group_anchor -> {merged_groups: [[eid,...]], standalone: [eid,...]}

# Only process groups with enough events to be worth merging
for anchor in sorted(groups.keys(), key=lambda a: -len(groups[a])):
    eids = groups[anchor]
    if len(eids) < 3:
        merge_results[anchor] = {"merged_groups": [], "standalone": eids}
        continue

    # Build prompt with top 3 headlines per event
    lines = []
    eid_map = {}  # number -> eid
    for idx, eid in enumerate(sorted(eids, key=lambda e: -events[e]["src"]), 1):
        ev = events[eid]
        eid_map[idx] = eid
        sample = "\n".join("  - " + t[:80] for t in ev["titles"][:3])
        lines.append("Topic %d (%d sources):\n%s" % (idx, ev["src"], sample))

    user_msg = "\n\n".join(lines)

    if DRY_RUN:
        # Just show what we'd send
        if len(eids) >= 5:  # only show larger groups
            print(
                "  [DRY] %s: %d events, would send %d tokens"
                % (anchor, len(eids), len(user_msg) // 4)
            )
        merge_results[anchor] = {"merged_groups": [], "standalone": eids}
        continue

    response = llm_call(MERGE_SYSTEM, user_msg)
    result = extract_json(response)

    if not result or "merge" not in result:
        print("  %s: LLM parse failed, keeping all standalone" % anchor)
        merge_results[anchor] = {"merged_groups": [], "standalone": eids}
        continue

    merged_groups = []
    used = set()
    for merge_group in result.get("merge", []):
        group_eids = [eid_map[n] for n in merge_group if n in eid_map]
        if len(group_eids) >= 2:
            merged_groups.append(group_eids)
            used.update(group_eids)
            total_merges += len(group_eids) - 1

    standalone = [eid for eid in eids if eid not in used]
    # Add explicitly standalone from LLM
    for n in result.get("standalone", []):
        if n in eid_map and eid_map[n] not in used:
            pass  # already in standalone

    merge_results[anchor] = {"merged_groups": merged_groups, "standalone": standalone}
    merged_desc = ", ".join(
        "[%s]" % "+".join(str(events[e]["src"]) for e in mg) for mg in merged_groups
    )
    if merged_groups:
        print(
            "  %s: %d events -> %s merged, %d standalone"
            % (anchor, len(eids), merged_desc, len(standalone))
        )

if DRY_RUN:
    print("\n  DRY RUN. Use --write to execute LLM calls and save.")
    print("  Groups >= 5 events shown above. Smaller groups skipped.")
    # Show summary
    large = sum(1 for a, eids in groups.items() if len(eids) >= 3)
    print("  Groups to process: %d (3+ events)" % large)
    print("  Estimated LLM calls: %d (merge) + prose generation" % large)
else:
    print("Step 2 complete: %d total merges across all groups" % total_merges)

# --- STEP 3: Generate prose (titles for events, descriptions for groups) ---
# TODO: implement after merge step is validated

print("\n--- Summary ---")
print("Groups: %d" % len(groups))
print("Ungrouped: %d" % len(ungrouped))
print(
    "Events above prose threshold (%d+ src): %d"
    % (
        MIN_SOURCES_FOR_PROSE,
        sum(1 for ev in events.values() if ev["src"] >= MIN_SOURCES_FOR_PROSE),
    )
)

conn.close()
