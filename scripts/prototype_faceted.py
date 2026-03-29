"""Prototype: faceted mechanical clustering (no Louvain)."""

import re
import sys
import uuid
from collections import Counter, defaultdict

import psycopg2

sys.path.insert(0, ".")
sys.stdout.reconfigure(errors="replace")

from pipeline.phase_4.rebuild_centroid import (  # noqa: E402
    SECTOR_TO_TRACK,
    tag_geo,
)

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/sni_v2")
cur = conn.cursor()

CENTROID = sys.argv[1] if len(sys.argv) > 1 else "EUROPE-FRANCE"
WRITE = "--write" in sys.argv

cur.execute(
    """
    SELECT t.id, t.title_display, t.pubdate_utc,
           tl.sector, tl.subject, tl.actor, tl.action_class, tl.target,
           tl.persons, tl.orgs, tl.places, tl.named_events,
           t.centroid_ids
    FROM titles_v3 t
    JOIN title_labels tl ON tl.title_id = t.id
    WHERE %s = ANY(t.centroid_ids)
    AND t.pubdate_utc >= '2026-03-01' AND t.pubdate_utc < '2026-04-01'
    AND t.processing_status = 'assigned'
    AND tl.sector IS NOT NULL AND tl.sector != 'NON_STRATEGIC'
""",
    (CENTROID,),
)
titles = []
for r in cur.fetchall():
    titles.append(
        {
            "id": str(r[0]),
            "title_display": r[1],
            "pubdate_utc": r[2],
            "sector": r[3],
            "subject": r[4],
            "actor": r[5],
            "action_class": r[6],
            "target": r[7],
            "persons": r[8] or [],
            "orgs": r[9] or [],
            "places": r[10] or [],
            "named_events": r[11] or [],
            "centroid_ids": r[12] or [],
        }
    )

n = len(titles)
print("%s strategic titles: %d" % (CENTROID, n))

# --- Signal frequency ---
signal_freq = Counter()
for t in titles:
    signals = set()
    for p in t["persons"]:
        signals.add("PER:" + p.upper())
    for o in t["orgs"]:
        signals.add("ORG:" + o.upper())
    for p in t["places"]:
        signals.add("PLC:" + p.upper())
    for e in t["named_events"]:
        signals.add("EVT:" + e)
    tgt = t.get("target") or ""
    if tgt and tgt != "NONE":
        for v in tgt.split(","):
            v = v.strip()
            if v and v != "NONE":
                signals.add("TGT:" + v)
    for s in signals:
        signal_freq[s] += 1

ubiquitous = {s for s, c in signal_freq.items() if c > n * 0.10}
print("Ubiquitous (>10%%): %s" % ", ".join(sorted(ubiquitous)))

# --- Title text: compute word frequency, filter ubiquitous dynamically ---
UBIQUITOUS_RATIO = 0.05  # stricter for text words (noisier than LLM signals)

all_word_freq = Counter()
for t in titles:
    words = re.findall(r"[A-Za-z\u00C0-\u024F]{2,}", t["title_display"])
    for w in {w.lower() for w in words}:
        all_word_freq[w] += 1

ubiquitous_words = {w for w, c in all_word_freq.items() if c > n * UBIQUITOUS_RATIO}
print(
    "Ubiquitous words (>5%%, %d filtered): %s"
    % (
        len(ubiquitous_words),
        ", ".join(sorted(w for w in ubiquitous_words if len(w) >= 4)),
    )
)


def title_content_words(title):
    words = re.findall(r"[A-Za-z\u00C0-\u024F]{2,}", title)
    return {w.lower() for w in words if w.lower() not in ubiquitous_words}


def get_anchors(idx):
    t = titles[idx]
    anchors = set()
    for p in t["persons"]:
        lbl = "PER:" + p.upper()
        if lbl not in ubiquitous:
            anchors.add(lbl)
    for o in t["orgs"]:
        lbl = "ORG:" + o.upper()
        if lbl not in ubiquitous:
            anchors.add(lbl)
    for p in t["places"]:
        lbl = "PLC:" + p.upper()
        if lbl not in ubiquitous:
            anchors.add(lbl)
    for e in t["named_events"]:
        lbl = "EVT:" + e
        if lbl not in ubiquitous:
            anchors.add(lbl)
    tgt = t.get("target") or ""
    if tgt and tgt != "NONE":
        for v in tgt.split(","):
            v = v.strip()
            if v and v != "NONE":
                lbl = "TGT:" + v
                if lbl not in ubiquitous:
                    anchors.add(lbl)
    return anchors


# --- L1: sector+subject groups ---
l1_groups = defaultdict(list)
for i, t in enumerate(titles):
    l1_groups[(t["sector"], t["subject"])].append(i)

print("L1 groups: %d" % len(l1_groups))

# --- L2: anchor signal split + L3: temporal split ---
ANCHOR_MIN = 3
TIME_GAP_DAYS = 1
MAX_GROUP = 50  # groups larger than this get recursive sub-splitting


def temporal_split(group_indices):
    if len(group_indices) <= 1:
        return [group_indices]
    sorted_idx = sorted(group_indices, key=lambda i: titles[i]["pubdate_utc"] or "")
    events = [[sorted_idx[0]]]
    for k in range(1, len(sorted_idx)):
        d1 = titles[sorted_idx[k - 1]].get("pubdate_utc")
        d2 = titles[sorted_idx[k]].get("pubdate_utc")
        if d1 and d2 and (d2 - d1).days >= TIME_GAP_DAYS:
            events.append([])
        events[-1].append(sorted_idx[k])
    return events


def find_anchor_groups(indices, exclude_anchors=None):
    """Split indices by best anchor signal. Returns (anchor_groups, remainder).

    exclude_anchors: signals already used as anchors at higher levels (don't reuse).
    """
    exclude = exclude_anchors or set()

    group_freq = Counter()
    title_anchor_map = {}
    for i in indices:
        a = get_anchors(i) - exclude
        title_anchor_map[i] = a
        for s in a:
            group_freq[s] += 1

    group_size = len(indices)
    valid_anchors = {
        s for s, c in group_freq.items() if c >= ANCHOR_MIN and c < group_size * 0.50
    }

    anchor_groups = defaultdict(list)
    remainder = []
    for i in indices:
        ta = title_anchor_map[i] & valid_anchors
        if ta:
            best = max(ta, key=lambda a: group_freq[a])
            anchor_groups[best].append(i)
        else:
            remainder.append(i)

    return dict(anchor_groups), remainder


def find_text_groups(indices):
    """Fallback: split by title text content words."""
    word_freq = Counter()
    title_words_map = {}
    for i in indices:
        words = title_content_words(titles[i]["title_display"])
        title_words_map[i] = words
        for w in words:
            word_freq[w] += 1

    group_size = len(indices)
    # Filter: ubiquitous within THIS group (>20%) + too short (<4 chars)
    local_ubiquitous = {w for w, c in word_freq.items() if c > group_size * 0.20}
    text_anchors = {
        w
        for w, c in word_freq.items()
        if c >= ANCHOR_MIN
        and c < group_size * 0.50
        and w not in local_ubiquitous
        and len(w) >= 4
    }
    text_groups = defaultdict(list)
    remainder = []
    for i in indices:
        tw = title_words_map[i] & text_anchors
        if tw:
            best = max(tw, key=lambda w: word_freq[w])
            text_groups[best].append(i)
        else:
            remainder.append(i)

    return {("TXT:" + k): v for k, v in text_groups.items()}, remainder


def cluster_group(indices, sector, subject, exclude_anchors=None, depth=0):
    """Recursively cluster a group of indices. Returns (events, remainder)."""
    events = []
    all_remainder = []

    # L2: anchor signal split
    anchor_groups, remainder = find_anchor_groups(indices, exclude_anchors)

    for anchor, members in anchor_groups.items():
        # L3: temporal split
        for chunk in temporal_split(members):
            if len(chunk) < 2:
                remainder.extend(chunk)
            elif len(chunk) > MAX_GROUP and depth < 2:
                # Recursive split: too large, try again with secondary signals
                sub_events, sub_remainder = cluster_group(
                    chunk,
                    sector,
                    subject,
                    exclude_anchors=(exclude_anchors or set()) | {anchor},
                    depth=depth + 1,
                )
                events.extend(sub_events)
                # Sub-remainder becomes a single event (the "general" bucket)
                if len(sub_remainder) >= 2:
                    events.append(
                        {
                            "sector": sector,
                            "subject": subject,
                            "anchor": anchor + " (general)",
                            "indices": sub_remainder,
                        }
                    )
                else:
                    all_remainder.extend(sub_remainder)
            else:
                events.append(
                    {
                        "sector": sector,
                        "subject": subject,
                        "anchor": anchor,
                        "indices": chunk,
                    }
                )

    # Fallback: title text anchors for remainder
    if remainder:
        text_groups, final_remainder = find_text_groups(remainder)
        for anchor, members in text_groups.items():
            for chunk in temporal_split(members):
                if len(chunk) >= 2:
                    events.append(
                        {
                            "sector": sector,
                            "subject": subject,
                            "anchor": anchor,
                            "indices": chunk,
                        }
                    )
                else:
                    final_remainder.extend(chunk)
        all_remainder.extend(final_remainder)
    else:
        all_remainder.extend(remainder)

    return events, all_remainder


all_events = []
total_assigned = 0
total_remainder = 0

for (sector, subject), indices in l1_groups.items():
    events, remainder = cluster_group(indices, sector, subject)
    for ev in events:
        total_assigned += len(ev["indices"])
    all_events.extend(events)
    total_remainder += len(remainder)

# === MECHANICAL MERGE ===
# Merge events that share: same subject + specific non-ubiquitous signal + date overlap


def build_event_profile(ev):
    """Build signal profile for merge matching."""
    persons = Counter()
    orgs = Counter()
    places = Counter()
    named_events = Counter()
    targets = Counter()
    dates = []
    for i in ev["indices"]:
        t = titles[i]
        for p in t.get("persons", []):
            persons[p.upper()] += 1
        for o in t.get("orgs", []):
            orgs[o.upper()] += 1
        for p in t.get("places", []):
            places[p.upper()] += 1
        for e in t.get("named_events", []):
            named_events[e] += 1
        tgt = t.get("target") or ""
        if tgt and tgt != "NONE":
            for v in tgt.split(","):
                v = v.strip()
                if v and v != "NONE":
                    targets[v] += 1
        if t.get("pubdate_utc"):
            dates.append(t["pubdate_utc"])
    return {
        "persons": set(persons),
        "orgs": set(orgs),
        "places": set(places),
        "named_events": set(named_events),
        "targets": set(targets),
        "min_date": min(dates) if dates else None,
        "max_date": max(dates) if dates else None,
    }


def merge_events(events):
    """Merge events sharing same subject + specific signals + date overlap."""

    # Compute ubiquitous signals within emerged events only
    sig_freq = Counter()
    total_events = len(events)
    profiles = []
    for ev in events:
        p = build_event_profile(ev)
        profiles.append(p)
        for s in p["persons"]:
            sig_freq["PER:" + s] += 1
        for s in p["places"]:
            sig_freq["PLC:" + s] += 1
        for s in p["named_events"]:
            sig_freq["EVT:" + s] += 1
        for s in p["targets"]:
            sig_freq["TGT:" + s] += 1

    # Ubiquitous: appears in >10% of emerged events
    merge_ubiquitous = {s for s, c in sig_freq.items() if c > total_events * 0.10}
    if merge_ubiquitous:
        ub_display = [s for s in sorted(merge_ubiquitous) if not s.startswith("TGT:")]
        if ub_display:
            print("Merge ubiquitous (>10%%): %s" % ", ".join(ub_display[:10]))

    # Find merge candidates
    merged_into = {}  # event index -> merged target index
    merge_count = 0

    for i in range(len(events)):
        if i in merged_into:
            continue
        for j in range(i + 1, len(events)):
            if j in merged_into:
                continue

            # Same subject required
            if events[i]["subject"] != events[j]["subject"]:
                continue

            pi, pj = profiles[i], profiles[j]

            # Date overlap: within 1 day
            if pi["min_date"] and pj["min_date"] and pi["max_date"] and pj["max_date"]:
                gap = max(
                    (pj["min_date"] - pi["max_date"]).days,
                    (pi["min_date"] - pj["max_date"]).days,
                )
                if gap > 1:
                    continue
            else:
                continue  # skip if no dates

            # Shared SPECIFIC signals (exclude ubiquitous)
            shared_specific = set()
            for p in pi["places"] & pj["places"]:
                if ("PLC:" + p) not in merge_ubiquitous:
                    shared_specific.add("PLC:" + p)
            for p in pi["persons"] & pj["persons"]:
                if ("PER:" + p) not in merge_ubiquitous:
                    shared_specific.add("PER:" + p)
            for e in pi["named_events"] & pj["named_events"]:
                if ("EVT:" + e) not in merge_ubiquitous:
                    shared_specific.add("EVT:" + e)

            if len(shared_specific) < 2:
                continue

            # Merge j into i (no profile rebuild — prevents cascading)
            events[i]["indices"].extend(events[j]["indices"])
            events[j]["indices"] = []  # mark as empty
            merged_into[j] = i
            merge_count += 1

    # Remove empty events
    events = [ev for ev in events if ev["indices"]]
    return events, merge_count


print("\n--- Mechanical merge ---")
before_count = len(all_events)
all_events, merge_count = merge_events(all_events)
print(
    "Merged: %d pairs (%d events -> %d events)"
    % (merge_count, before_count, len(all_events))
)

# === LLM MERGE PASS ===
# Find candidates with 1 shared specific signal (mechanical requires 2+)
# Send to LLM for yes/no confirmation

LLM_MERGE = "--llm-merge" in sys.argv


def find_llm_candidates(events):
    """Find event pairs with 1 shared specific signal — LLM candidates.

    Filters:
    - Same subject required
    - Date overlap within 1 day
    - Shared PLC or PER (not EVT alone) — places and persons are stronger identity
    - Min source count: 8 for high-volume tracks (>500 emerged), 5 otherwise
    """
    profiles = [build_event_profile(ev) for ev in events]

    # Dynamic min sources: high-volume tracks need stricter filter
    emerged_count = sum(1 for ev in events if len(ev["indices"]) >= 2)
    min_sources = 8 if emerged_count > 500 else 5
    print(
        "  LLM candidate filter: min_sources=%d (emerged=%d)"
        % (min_sources, emerged_count)
    )

    # Ubiquitous within emerged events
    sig_freq = Counter()
    for p in profiles:
        for s in p["persons"]:
            sig_freq["PER:" + s] += 1
        for s in p["places"]:
            sig_freq["PLC:" + s] += 1
    ub = {s for s, c in sig_freq.items() if c > len(events) * 0.10}

    candidates = []
    for i in range(len(events)):
        if len(events[i]["indices"]) < min_sources:
            continue
        for j in range(i + 1, len(events)):
            if len(events[j]["indices"]) < min_sources:
                continue
            if events[i]["subject"] != events[j]["subject"]:
                continue

            pi, pj = profiles[i], profiles[j]
            if not (
                pi["min_date"] and pj["min_date"] and pi["max_date"] and pj["max_date"]
            ):
                continue
            gap = max(
                (pj["min_date"] - pi["max_date"]).days,
                (pi["min_date"] - pj["max_date"]).days,
            )
            if gap > 1:
                continue

            # Require shared PLC or PER (stronger identity than EVT)
            shared = set()
            for p in pi["places"] & pj["places"]:
                if ("PLC:" + p) not in ub:
                    shared.add("PLC:" + p)
            for p in pi["persons"] & pj["persons"]:
                if ("PER:" + p) not in ub:
                    shared.add("PER:" + p)

            if len(shared) == 1:
                candidates.append((i, j, shared))

    return candidates


def llm_merge_review(events, candidates):
    """Send candidates to LLM for yes/no merge decision."""
    import httpx

    from core.config import config

    SYSTEM = (
        "You compare two groups of news headlines. "
        "Decide if they describe the SAME specific news event or story. "
        "Different aspects of the same situation (e.g. reactions to the same event) count as the same story. "
        "Different events involving the same person/place do NOT count as the same story. "
        "Reply with ONLY: YES or NO"
    )

    merged = 0
    merge_log = []
    merged_set = set()

    for idx, (i, j, shared) in enumerate(candidates):
        if i in merged_set or j in merged_set:
            continue

        a_titles = [titles[k]["title_display"][:100] for k in events[i]["indices"][:5]]
        b_titles = [titles[k]["title_display"][:100] for k in events[j]["indices"][:5]]

        user_msg = "Group A (%d sources):\n%s\n\nGroup B (%d sources):\n%s" % (
            len(events[i]["indices"]),
            "\n".join("- " + t for t in a_titles),
            len(events[j]["indices"]),
            "\n".join("- " + t for t in b_titles),
        )

        try:
            resp = httpx.post(
                config.deepseek_api_url + "/chat/completions",
                headers={"Authorization": "Bearer " + config.deepseek_api_key},
                json={
                    "model": config.llm_model,
                    "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": user_msg},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 10,
                },
                timeout=30,
            )
            answer = resp.json()["choices"][0]["message"]["content"].strip().upper()
        except Exception as e:
            print("  LLM error: %s" % e)
            answer = "ERROR"

        decision = "YES" if answer.startswith("YES") else "NO"
        a_sample = a_titles[0][:60]
        b_sample = b_titles[0][:60]

        if decision == "YES":
            events[i]["indices"].extend(events[j]["indices"])
            events[j]["indices"] = []
            merged_set.add(j)
            merged += 1
            merge_log.append(
                "  MERGE [%d+%d] %s"
                % (
                    len(events[i]["indices"]) - len(events[j]["indices"]),
                    len(events[j]["indices"]) if j not in merged_set else 0,
                    shared,
                )
            )
            print(
                "  [%d/%d] YES %s | %s + %s"
                % (idx + 1, len(candidates), shared, a_sample, b_sample)
            )
        else:
            print(
                "  [%d/%d] NO  %s | %s + %s"
                % (idx + 1, len(candidates), shared, a_sample, b_sample)
            )

    events = [ev for ev in events if ev["indices"]]
    return events, merged


print("\n--- LLM merge candidates ---")
llm_candidates = find_llm_candidates(all_events)
print(
    "Candidates (1 shared specific, same subject, date overlap): %d"
    % len(llm_candidates)
)

if LLM_MERGE and llm_candidates:
    print("\nRunning LLM review...")
    all_events, llm_merged = llm_merge_review(all_events, llm_candidates)
    print("LLM merged: %d pairs" % llm_merged)
elif llm_candidates:
    # Dry run: show candidates without calling LLM
    print("\nDry run (use --llm-merge to call LLM):")
    for idx, (i, j, shared) in enumerate(llm_candidates[:20]):
        a = titles[all_events[i]["indices"][0]]["title_display"][:70]
        b = titles[all_events[j]["indices"][0]]["title_display"][:70]
        print(
            "  [%d+%d] %s | %s/%s"
            % (
                len(all_events[i]["indices"]),
                len(all_events[j]["indices"]),
                shared,
                all_events[i]["subject"],
                all_events[j]["subject"],
            )
        )
        print("    A: %s" % a)
        print("    B: %s" % b)
    if len(llm_candidates) > 20:
        print("  ... and %d more" % (len(llm_candidates) - 20))

all_events.sort(key=lambda e: -len(e["indices"]))

print()
print("=== FACETED CLUSTERING RESULTS ===")
print("Emerged events: %d" % len(all_events))
print("Titles in events: %d" % total_assigned)
print("Remainder (catchall): %d" % total_remainder)
print("Catchall rate: %d%%" % (total_remainder * 100 // n))
print()

print("Top 30 events:")
for ev in all_events[:30]:
    sample = titles[ev["indices"][0]]["title_display"][:70]
    dates = [
        titles[i]["pubdate_utc"] for i in ev["indices"] if titles[i].get("pubdate_utc")
    ]
    date_range = ""
    if dates:
        d1, d2 = min(dates), max(dates)
        date_range = "%s-%s" % (d1.strftime("%m/%d"), d2.strftime("%m/%d"))
    print(
        "  [%3d] %s/%s anchor=%-25s %s"
        % (len(ev["indices"]), ev["sector"], ev["subject"], ev["anchor"], date_range)
    )
    print("        %s" % sample)

# Spot check: Iraq soldier vs Congo
print("\n=== SPOT CHECK: Iraq/Congo separation ===")
for ev in all_events:
    titles_text = " ".join(titles[i]["title_display"] for i in ev["indices"])
    if "Iraq" in titles_text and ("Congo" in titles_text or "Goma" in titles_text):
        print("MIXED! anchor=%s, %d titles" % (ev["anchor"], len(ev["indices"])))
        for i in ev["indices"][:5]:
            print("  %s" % titles[i]["title_display"][:80])
        break
else:
    print("No Iraq/Congo mixing found.")

# Spot check: Epstein vs schoolchildren
print("\n=== SPOT CHECK: Epstein/schoolchildren separation ===")
for ev in all_events:
    titles_text = " ".join(titles[i]["title_display"] for i in ev["indices"])
    if "Epstein" in titles_text and (
        "agression" in titles_text.lower() or "schoolchildren" in titles_text.lower()
    ):
        print("MIXED! anchor=%s, %d titles" % (ev["anchor"], len(ev["indices"])))
        for i in ev["indices"][:5]:
            print("  %s" % titles[i]["title_display"][:80])
        break
else:
    print("No Epstein/schoolchildren mixing found.")

if not WRITE:
    print("\nDRY RUN. Use --write to save to DB.")
    conn.close()
    sys.exit(0)

# === WRITE TO DB ===
MONTH = "2026-03-01"

# Build CTM map (track -> ctm_id), create if needed
track_to_ctm = {}
for track in ["geo_security", "geo_politics", "geo_economy", "geo_society"]:
    cur.execute(
        "SELECT id FROM ctm WHERE centroid_id = %s AND month = %s AND track = %s",
        (CENTROID, MONTH, track),
    )
    row = cur.fetchone()
    if row:
        track_to_ctm[track] = row[0]
    else:
        ctm_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO ctm (id, centroid_id, month, track, title_count) "
            "VALUES (%s, %s, %s, %s, 0)",
            (ctm_id, CENTROID, MONTH, track),
        )
        track_to_ctm[track] = ctm_id
conn.commit()

# Clean existing events for this centroid+month
for ctm_id in track_to_ctm.values():
    cur.execute(
        "DELETE FROM event_strategic_narratives WHERE event_id IN "
        "(SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (ctm_id,),
    )
    cur.execute(
        "DELETE FROM event_v3_titles WHERE event_id IN "
        "(SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (ctm_id,),
    )
    cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))
conn.commit()
print("\nCleaned existing events.")

# Build all_clusters in the format rebuild_centroid expects
all_clusters = []
for ev in all_events:
    all_clusters.append(
        {
            "sector": ev["sector"],
            "subject": ev["subject"],
            "indices": ev["indices"],
            "anchor": ev.get("anchor"),
        }
    )
# Add catchall singles
for (sector, subject), indices in l1_groups.items():
    for i in indices:
        # Check if already assigned to an event
        assigned = False
        for ev in all_events:
            if i in ev["indices"]:
                assigned = True
                break
        if not assigned:
            all_clusters.append({"sector": sector, "subject": subject, "indices": [i]})

# Write events
written = 0
for cl in all_clusters:
    track = SECTOR_TO_TRACK.get(cl["sector"], "geo_politics")
    ctm_id = track_to_ctm.get(track)
    if not ctm_id:
        ctm_id = track_to_ctm.get("geo_politics")
    if not ctm_id:
        continue

    geo_type, geo_key = tag_geo(cl["indices"], titles, CENTROID)
    eid = str(uuid.uuid4())
    tids = [titles[i]["id"] for i in cl["indices"]]
    dates = [
        titles[i]["pubdate_utc"] for i in cl["indices"] if titles[i]["pubdate_utc"]
    ]
    d = max(dates) if dates else MONTH
    fs = min(dates) if dates else None
    is_ca = len(cl["indices"]) < 2

    # Store anchor as topic_core for story grouping in UI
    anchor = cl.get("anchor", "")

    cur.execute(
        "INSERT INTO events_v3 (id,ctm_id,source_batch_count,date,first_seen,"
        "last_active,event_type,bucket_key,is_catchall,topic_core,created_at,updated_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())",
        (eid, ctm_id, len(tids), d, fs, d, geo_type, geo_key, is_ca, anchor or None),
    )
    for tid in tids:
        cur.execute(
            "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s::uuid) "
            "ON CONFLICT DO NOTHING",
            (eid, tid),
        )
    written += 1

conn.commit()

# Update CTM title counts
for track, ctm_id in track_to_ctm.items():
    cur.execute(
        "UPDATE ctm SET title_count = (SELECT count(*) FROM event_v3_titles et "
        "JOIN events_v3 e ON e.id = et.event_id WHERE e.ctm_id = %s) "
        "WHERE id = %s",
        (ctm_id, ctm_id),
    )
conn.commit()

# Delete empty CTMs
cur.execute(
    "DELETE FROM ctm WHERE centroid_id = %s AND month = %s AND title_count = 0",
    (CENTROID, MONTH),
)
conn.commit()

print("Written %d events." % written)
conn.close()
