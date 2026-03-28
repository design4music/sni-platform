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


all_events = []
total_assigned = 0
total_remainder = 0

for (sector, subject), indices in l1_groups.items():
    # Count anchor frequency within group
    group_freq = Counter()
    title_anchor_map = {}
    for i in indices:
        a = get_anchors(i)
        title_anchor_map[i] = a
        for s in a:
            group_freq[s] += 1

    group_size = len(indices)
    valid_anchors = {
        s for s, c in group_freq.items() if c >= ANCHOR_MIN and c < group_size * 0.50
    }

    # Assign each title to best anchor
    anchor_groups = defaultdict(list)
    remainder = []
    for i in indices:
        ta = title_anchor_map[i] & valid_anchors
        if ta:
            best = max(ta, key=lambda a: group_freq[a])
            anchor_groups[best].append(i)
        else:
            remainder.append(i)

    # Temporal split within each anchor group
    for anchor, members in anchor_groups.items():
        for event_indices in temporal_split(members):
            if len(event_indices) >= 2:
                all_events.append(
                    {
                        "sector": sector,
                        "subject": subject,
                        "anchor": anchor,
                        "indices": event_indices,
                    }
                )
                total_assigned += len(event_indices)
            else:
                remainder.extend(event_indices)

    # Fallback: title text anchors for remainder
    if remainder:
        word_freq = Counter()
        title_words_map = {}
        for i in remainder:
            words = title_content_words(titles[i]["title_display"])
            title_words_map[i] = words
            for w in words:
                word_freq[w] += 1

        text_anchors = {
            w
            for w, c in word_freq.items()
            if c >= ANCHOR_MIN and c < len(remainder) * 0.50
        }
        text_groups = defaultdict(list)
        final_remainder = []
        for i in remainder:
            tw = title_words_map[i] & text_anchors
            if tw:
                best = max(tw, key=lambda w: word_freq[w])
                text_groups[best].append(i)
            else:
                final_remainder.append(i)

        for anchor_word, members in text_groups.items():
            for event_indices in temporal_split(members):
                if len(event_indices) >= 2:
                    all_events.append(
                        {
                            "sector": sector,
                            "subject": subject,
                            "anchor": "TXT:" + anchor_word,
                            "indices": event_indices,
                        }
                    )
                    total_assigned += len(event_indices)
                else:
                    final_remainder.extend(event_indices)

        total_remainder += len(final_remainder)
    else:
        pass  # no remainder

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
        {"sector": ev["sector"], "subject": ev["subject"], "indices": ev["indices"]}
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

    cur.execute(
        "INSERT INTO events_v3 (id,ctm_id,source_batch_count,date,first_seen,"
        "last_active,event_type,bucket_key,is_catchall,created_at,updated_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())",
        (eid, ctm_id, len(tids), d, fs, d, geo_type, geo_key, is_ca),
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
