"""Layered clustering: mechanical signals first, then LLM intelligence.

Layer 1: Strong signal clusters (mechanical)
Layer 2: LLM clustering within bilateral/domestic pools
"""

import json
import re
import sys
import uuid
from collections import Counter, defaultdict

import httpx
import psycopg2

sys.path.insert(0, ".")
sys.stdout.reconfigure(errors="replace")

from core.config import config  # noqa: E402
from pipeline.phase_4.rebuild_centroid import tag_geo  # noqa: E402

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/sni_v2")
cur = conn.cursor()

CENTROID = sys.argv[1] if len(sys.argv) > 1 else "AMERICAS-USA"
TRACK = sys.argv[2] if len(sys.argv) > 2 else "geo_security"
WRITE = "--write" in sys.argv
MONTH = "2026-03-01"

# Sectors for this track
TRACK_SECTORS = {
    "geo_security": ("MILITARY", "SECURITY", "INTELLIGENCE"),
    "geo_politics": ("DIPLOMACY", "GOVERNANCE"),
    "geo_economy": ("ECONOMY", "ENERGY_RESOURCES", "TECHNOLOGY", "INFRASTRUCTURE"),
    "geo_society": ("HEALTH_ENVIRONMENT", "SOCIETY"),
}
sectors = TRACK_SECTORS.get(TRACK, ("MILITARY", "SECURITY"))

# Load titles
placeholders = ",".join(["%s"] * len(sectors))
cur.execute(
    """
    SELECT t.id, t.title_display, t.pubdate_utc, t.centroid_ids,
           t.detected_language,
           tl.sector, tl.subject, tl.target,
           tl.persons, tl.orgs, tl.places, tl.named_events
    FROM titles_v3 t
    JOIN title_labels tl ON tl.title_id = t.id
    WHERE %%s = ANY(t.centroid_ids)
    AND t.pubdate_utc >= %%s AND t.pubdate_utc < (%%s::date + interval '1 month')
    AND t.processing_status = 'assigned'
    AND tl.sector IN (%s)
    AND tl.sector != 'NON_STRATEGIC'
"""
    % placeholders,
    (CENTROID, MONTH, MONTH, *sectors),
)

titles = []
for r in cur.fetchall():
    targets = set()
    tgt = r[7] or ""
    if tgt and tgt != "NONE":
        for v in tgt.split(","):
            v = v.strip()
            if v and v != "NONE" and not v.startswith("US"):
                targets.add(v)
    signals = set()
    for p in r[8] or []:
        signals.add("PER:" + p)
    for o in r[9] or []:
        signals.add("ORG:" + o)
    for p in r[10] or []:
        signals.add("PLC:" + p.upper())
    for e in r[11] or []:
        signals.add("EVT:" + e)
    titles.append(
        {
            "id": str(r[0]),
            "title_display": r[1],
            "pubdate_utc": r[2],
            "centroid_ids": r[3] or [],
            "lang": r[4],
            "sector": r[5],
            "subject": r[6],
            "target_raw": r[7],
            "targets": targets,
            "signals": signals,
        }
    )

n = len(titles)
print("%s/%s: %d titles" % (CENTROID, TRACK, n))

# Global signal frequency + ubiquitous
sig_freq = Counter()
for t in titles:
    for s in t["signals"]:
        sig_freq[s] += 1
UBIQUITOUS = {s for s, c in sig_freq.items() if c > n * 0.10}
STRONG_MIN = 5
strong_signals = {
    s for s, c in sig_freq.items() if c >= STRONG_MIN and s not in UBIQUITOUS
}

print(
    "Ubiquitous (>10%%): %s"
    % ", ".join(sorted(s for s in UBIQUITOUS if not s.startswith("PER:TRUMP")))[:100]
)
print("Strong signals (5+, non-ub): %d" % len(strong_signals))


# === LAYER 1: Strong signal clusters ===
def week_of(dt):
    if not dt:
        return "W0"
    d = dt.day
    if d <= 7:
        return "W1"
    if d <= 14:
        return "W2"
    if d <= 21:
        return "W3"
    return "W4"


layer1_clusters = defaultdict(list)  # signal -> [indices]
layer1_assigned = set()

# Assign each title to its MOST SPECIFIC strong signal (lowest frequency)
for i, t in enumerate(titles):
    candidates = t["signals"] & strong_signals
    if candidates:
        # Pick most specific (least frequent)
        best = min(candidates, key=lambda s: sig_freq[s])
        layer1_clusters[best].append(i)
        layer1_assigned.add(i)

# Temporal split within each signal cluster (1-day gaps)
TIME_GAP_DAYS = 1
all_events = []


def temporal_split(indices):
    if len(indices) <= 1:
        return [indices]
    sorted_idx = sorted(indices, key=lambda i: titles[i]["pubdate_utc"] or "")
    events = [[sorted_idx[0]]]
    for k in range(1, len(sorted_idx)):
        d1 = titles[sorted_idx[k - 1]].get("pubdate_utc")
        d2 = titles[sorted_idx[k]].get("pubdate_utc")
        if d1 and d2 and (d2 - d1).days >= TIME_GAP_DAYS:
            events.append([])
        events[-1].append(sorted_idx[k])
    return events


for signal, indices in layer1_clusters.items():
    for chunk in temporal_split(indices):
        if len(chunk) >= 2:
            all_events.append({"anchor": signal, "indices": chunk, "source": "layer1"})

l1_events = len(all_events)
l1_titles = sum(len(e["indices"]) for e in all_events)
print(
    "\nLayer 1: %d clusters, %d titles (%.0f%%)"
    % (l1_events, l1_titles, 100 * l1_titles / n)
)

# === LAYER 2: LLM clustering of remainder ===
remainder = [i for i in range(n) if i not in layer1_assigned]
print("Remainder for LLM: %d titles" % len(remainder))

# Build pools: bilateral (by target) and domestic (by subject)
bilateral_pools = defaultdict(list)  # target -> [indices]
domestic_pools = defaultdict(list)  # subject -> [indices]

for i in remainder:
    t = titles[i]
    if t["targets"] and len(t["targets"]) == 1:
        tgt = list(t["targets"])[0]
        bilateral_pools[tgt].append(i)
    elif not t["targets"]:
        domestic_pools[t["subject"]].append(i)
    else:
        # Multilateral: assign to primary target (first alphabetically)
        tgt = sorted(t["targets"])[0]
        bilateral_pools[tgt].append(i)

# For pools under 100: one LLM call, expect 1-5 stories
# For pools over 100: split by subject+week, then LLM
LLM_POOL_MAX = 80  # max titles to send in one LLM call


def select_representative(indices, max_n):
    """Pick most representative English titles by centrality."""
    if len(indices) <= max_n:
        return indices
    # Simple: prefer English, sort by word overlap
    word_freq = Counter()
    words_map = {}
    for i in indices:
        t = titles[i]
        words = set(w.lower() for w in re.findall(r"[A-Za-z]{4,}", t["title_display"]))
        words_map[i] = words
        for w in words:
            word_freq[w] += 1
    scored = []
    for i in indices:
        ws = words_map.get(i, set())
        score = sum(word_freq[w] for w in ws) / max(len(ws), 1)
        is_en = titles[i].get("lang") in ("en", None)
        scored.append((i, score * (1.5 if is_en else 1.0)))
    scored.sort(key=lambda x: -x[1])
    return [s[0] for s in scored[:max_n]]


def llm_cluster(indices, context_label):
    """Send titles to LLM for story grouping. Returns list of (title, [indices])."""
    rep = select_representative(indices, LLM_POOL_MAX)

    lines = []
    idx_map = {}  # LLM number -> title index
    for num, i in enumerate(rep, 1):
        t = titles[i]
        date = t["pubdate_utc"].strftime("%m/%d") if t["pubdate_utc"] else "?"
        lines.append("%d. [%s] %s" % (num, date, t["title_display"][:100]))
        idx_map[num] = i

    system = (
        "You receive numbered headlines about %s. "
        "Group them into distinct news stories. Each story = one developing situation. "
        "Different days of same story = SAME group. Reactions/follow-ups = SAME group. "
        'Return JSON: {"stories": [{"title": "5-10 word title", "ids": [1,3,7]}, ...]}'
    ) % context_label

    try:
        resp = httpx.post(
            config.deepseek_api_url + "/chat/completions",
            headers={"Authorization": "Bearer " + config.deepseek_api_key},
            json={
                "model": config.llm_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": "\n".join(lines)},
                ],
                "temperature": 0.1,
                "max_tokens": 4000,
            },
            timeout=90,
        )
        text = resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("    LLM error: %s" % str(e)[:60])
        return [("Unclustered", indices)]

    result = None
    try:
        result = json.loads(text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                result = json.loads(m.group(0))
            except Exception:
                pass

    if not result or "stories" not in result:
        return [("Unclustered", indices)]

    stories = []
    used = set()
    for s in result["stories"]:
        ids = [idx_map[num] for num in s.get("ids", []) if num in idx_map]
        if ids:
            stories.append((s.get("title", "Untitled"), ids))
            used.update(ids)

    # Assign non-representative titles to nearest story
    non_rep = [i for i in indices if i not in set(rep)]
    if non_rep and stories:
        # Build word signature per story
        story_words = []
        for title, ids in stories:
            words = set()
            for i in ids:
                words.update(
                    w.lower()
                    for w in re.findall(r"[A-Za-z]{4,}", titles[i]["title_display"])
                )
            story_words.append(words)

        for i in non_rep:
            tw = set(
                w.lower()
                for w in re.findall(r"[A-Za-z]{4,}", titles[i]["title_display"])
            )
            best_idx = 0
            best_overlap = 0
            for si, sw in enumerate(story_words):
                overlap = len(tw & sw)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_idx = si
            stories[best_idx] = (stories[best_idx][0], stories[best_idx][1] + [i])

    # Also add rep titles not claimed by any story
    unclaimed = [i for i in rep if i not in used]
    if unclaimed and stories:
        stories[0] = (stories[0][0], stories[0][1] + unclaimed)

    return stories


DRY_RUN_LLM = "--dry-llm" in sys.argv
llm_calls = 0
llm_events_created = 0

# Process bilateral pools
print("\nLayer 2 bilateral pools:")
for tgt in sorted(bilateral_pools.keys(), key=lambda t: -len(bilateral_pools[t])):
    indices = bilateral_pools[tgt]
    if len(indices) < 2:
        continue

    if len(indices) <= 100:
        # Small pool: one LLM call
        if DRY_RUN_LLM:
            print("  [DRY] TGT:%s: %d titles -> 1 LLM call" % (tgt, len(indices)))
            llm_calls += 1
            all_events.append(
                {"anchor": "TGT:" + tgt, "indices": indices, "source": "layer2"}
            )
        else:
            context = "%s bilateral relations with %s" % (CENTROID.split("-")[-1], tgt)
            stories = llm_cluster(indices, context)
            llm_calls += 1
            for title, ids in stories:
                if ids:
                    all_events.append(
                        {
                            "anchor": "TGT:" + tgt,
                            "indices": ids,
                            "source": "layer2",
                            "llm_title": title,
                        }
                    )
                    llm_events_created += 1
            print(
                "  TGT:%s: %d titles -> %d stories" % (tgt, len(indices), len(stories))
            )
    else:
        # Large pool: split by subject+week, then LLM each
        sub_pools = defaultdict(list)
        for i in indices:
            key = (titles[i]["subject"], week_of(titles[i]["pubdate_utc"]))
            sub_pools[key].append(i)

        for (subj, week), sub_indices in sorted(
            sub_pools.items(), key=lambda x: -len(x[1])
        ):
            if len(sub_indices) < 2:
                continue
            if DRY_RUN_LLM:
                print(
                    "  [DRY] TGT:%s/%s/%s: %d titles -> 1 LLM call"
                    % (tgt, subj, week, len(sub_indices))
                )
                llm_calls += 1
                all_events.append(
                    {
                        "anchor": "TGT:%s/%s/%s" % (tgt, subj, week),
                        "indices": sub_indices,
                        "source": "layer2",
                    }
                )
            else:
                context = "%s %s operations regarding %s (week %s)" % (
                    CENTROID.split("-")[-1],
                    subj.lower().replace("_", " "),
                    tgt,
                    week,
                )
                stories = llm_cluster(sub_indices, context)
                llm_calls += 1
                for title, ids in stories:
                    if ids:
                        all_events.append(
                            {
                                "anchor": "TGT:%s/%s" % (tgt, subj),
                                "indices": ids,
                                "source": "layer2",
                                "llm_title": title,
                            }
                        )
                        llm_events_created += 1
                print(
                    "  TGT:%s/%s/%s: %d titles -> %d stories"
                    % (tgt, subj, week, len(sub_indices), len(stories))
                )

# Process domestic pools
print("\nLayer 2 domestic pools:")
for subj in sorted(domestic_pools.keys(), key=lambda s: -len(domestic_pools[s])):
    indices = domestic_pools[subj]
    if len(indices) < 2:
        continue
    if DRY_RUN_LLM:
        calls = (
            1
            if len(indices) <= 100
            else len(set(week_of(titles[i]["pubdate_utc"]) for i in indices))
        )
        print(
            "  [DRY] DOM/%s: %d titles -> %d LLM call(s)" % (subj, len(indices), calls)
        )
        llm_calls += calls
        all_events.append(
            {"anchor": "DOM/" + subj, "indices": indices, "source": "layer2"}
        )
    else:
        if len(indices) <= 100:
            context = "%s domestic %s" % (
                CENTROID.split("-")[-1],
                subj.lower().replace("_", " "),
            )
            stories = llm_cluster(indices, context)
            llm_calls += 1
            for title, ids in stories:
                if ids:
                    all_events.append(
                        {
                            "anchor": "DOM/" + subj,
                            "indices": ids,
                            "source": "layer2",
                            "llm_title": title,
                        }
                    )
                    llm_events_created += 1
            print(
                "  DOM/%s: %d titles -> %d stories" % (subj, len(indices), len(stories))
            )
        else:
            sub_pools = defaultdict(list)
            for i in indices:
                sub_pools[week_of(titles[i]["pubdate_utc"])].append(i)
            for week, sub_indices in sorted(sub_pools.items()):
                if len(sub_indices) < 2:
                    continue
                context = "%s domestic %s (week %s)" % (
                    CENTROID.split("-")[-1],
                    subj.lower().replace("_", " "),
                    week,
                )
                stories = llm_cluster(sub_indices, context)
                llm_calls += 1
                for title, ids in stories:
                    if ids:
                        all_events.append(
                            {
                                "anchor": "DOM/" + subj,
                                "indices": ids,
                                "source": "layer2",
                                "llm_title": title,
                            }
                        )
                        llm_events_created += 1
                print(
                    "  DOM/%s/%s: %d titles -> %d stories"
                    % (subj, week, len(sub_indices), len(stories))
                )

# Collect unassigned as catchall
assigned = set()
for e in all_events:
    assigned.update(e["indices"])
catchall = [i for i in range(n) if i not in assigned]

all_events.sort(key=lambda e: -len(e["indices"]))

print("\n=== RESULTS ===")
print("Layer 1 clusters: %d" % l1_events)
print(
    "Layer 2 LLM stories: %d" % llm_events_created
    if not DRY_RUN_LLM
    else "Layer 2 LLM calls (dry): %d" % llm_calls
)
print("Total events: %d" % len(all_events))
print("Titles in events: %d" % len(assigned))
print("Catchall: %d (%.0f%%)" % (len(catchall), 100 * len(catchall) / n if n else 0))
print("LLM calls: %d" % llm_calls)

print("\nTop 20 events:")
for e in all_events[:20]:
    src = len(e["indices"])
    anchor = e["anchor"][:25]
    llm_title = e.get("llm_title", "")
    sample = llm_title if llm_title else titles[e["indices"][0]]["title_display"][:60]
    print("  [%3d] %-25s %s" % (src, anchor, sample[:65]))

if not WRITE:
    print("\nDRY RUN. Use --write to save to DB.")
    conn.close()
    sys.exit(0)

# === WRITE TO DB ===
cur.execute(
    "SELECT id FROM ctm WHERE centroid_id = %s AND track = %s AND month = %s",
    (CENTROID, TRACK, MONTH),
)
CTM_ID = cur.fetchone()[0]

# Clean
cur.execute(
    "DELETE FROM event_strategic_narratives WHERE event_id IN "
    "(SELECT id FROM events_v3 WHERE ctm_id = %s)",
    (CTM_ID,),
)
cur.execute(
    "DELETE FROM event_v3_titles WHERE event_id IN "
    "(SELECT id FROM events_v3 WHERE ctm_id = %s)",
    (CTM_ID,),
)
cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (CTM_ID,))
conn.commit()

written = 0
for cl in all_events:
    geo_type, geo_key = tag_geo(cl["indices"], titles, CENTROID)
    eid = str(uuid.uuid4())
    tids = [titles[i]["id"] for i in cl["indices"]]
    dates = [
        titles[i]["pubdate_utc"] for i in cl["indices"] if titles[i]["pubdate_utc"]
    ]
    d = max(dates) if dates else MONTH
    fs = min(dates) if dates else None
    anchor = cl.get("anchor", "")
    llm_title = cl.get("llm_title")

    cur.execute(
        "INSERT INTO events_v3 (id,ctm_id,source_batch_count,date,first_seen,"
        "last_active,event_type,bucket_key,is_catchall,topic_core,title,created_at,updated_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())",
        (eid, CTM_ID, len(tids), d, fs, d, geo_type, geo_key, False, anchor, llm_title),
    )
    for tid in tids:
        cur.execute(
            "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s::uuid) "
            "ON CONFLICT DO NOTHING",
            (eid, tid),
        )
    written += 1

# Catchall
for i in catchall:
    eid = str(uuid.uuid4())
    t = titles[i]
    d = t["pubdate_utc"] or MONTH
    geo_type, geo_key = tag_geo([i], titles, CENTROID)
    cur.execute(
        "INSERT INTO events_v3 (id,ctm_id,source_batch_count,date,first_seen,"
        "last_active,event_type,bucket_key,is_catchall,title,created_at,updated_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())",
        (eid, CTM_ID, 1, d, d, d, geo_type, geo_key, True, t["title_display"][:200]),
    )
    cur.execute(
        "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s::uuid) "
        "ON CONFLICT DO NOTHING",
        (eid, t["id"]),
    )
    written += 1

conn.commit()

# Assign best titles for events without LLM title
cur.execute(
    """
    UPDATE events_v3 e SET title = (
        SELECT t.title_display FROM event_v3_titles et
        JOIN titles_v3 t ON t.id = et.title_id
        WHERE et.event_id = e.id
        AND (t.detected_language = 'en' OR t.detected_language IS NULL)
        ORDER BY t.pubdate_utc DESC LIMIT 1
    ) WHERE e.ctm_id = %s AND e.title IS NULL
""",
    (CTM_ID,),
)
conn.commit()

print("Written %d events." % written)
conn.close()
