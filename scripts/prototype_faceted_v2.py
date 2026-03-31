"""Faceted clustering v2: bilateral mega-merge built into clustering.

Bilateral events: group by subject + target + week (coarse, few big clusters)
Domestic events: group by anchor signal (fine, many small clusters)

Usage:
    python scripts/prototype_faceted_v2.py AMERICAS-USA geo_security
    python scripts/prototype_faceted_v2.py AMERICAS-USA geo_security --write
"""

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

CENTROID = sys.argv[1] if len(sys.argv) > 1 else "AMERICAS-USA"
TRACK = sys.argv[2] if len(sys.argv) > 2 else "geo_security"
WRITE = "--write" in sys.argv
MONTH = "2026-03-01"

# Load CTM
cur.execute(
    "SELECT id FROM ctm WHERE centroid_id = %s AND track = %s AND month = %s",
    (CENTROID, TRACK, MONTH),
)
row = cur.fetchone()
if not row:
    print("CTM not found")
    sys.exit(1)
CTM_ID = row[0]

# Load all strategic titles for this centroid
cur.execute(
    """
    SELECT t.id, t.title_display, t.pubdate_utc, t.centroid_ids,
           tl.sector, tl.subject, tl.actor, tl.action_class, tl.target,
           tl.persons, tl.orgs, tl.places, tl.named_events
    FROM titles_v3 t
    JOIN title_labels tl ON tl.title_id = t.id
    WHERE %s = ANY(t.centroid_ids)
    AND t.pubdate_utc >= %s AND t.pubdate_utc < (%s::date + interval '1 month')
    AND t.processing_status = 'assigned'
    AND tl.sector IS NOT NULL AND tl.sector != 'NON_STRATEGIC'
    AND COALESCE(tl.sector, '') != ''
""",
    (CENTROID, MONTH, MONTH),
)
titles = []
for r in cur.fetchall():
    # Determine track from sector
    sector = r[4]
    track_for_title = SECTOR_TO_TRACK.get(sector, "geo_politics")
    if track_for_title != TRACK:
        continue
    titles.append(
        {
            "id": str(r[0]),
            "title_display": r[1],
            "pubdate_utc": r[2],
            "centroid_ids": r[3] or [],
            "sector": r[4],
            "subject": r[5],
            "actor": r[6],
            "action_class": r[7],
            "target": r[8],
            "persons": r[9] or [],
            "orgs": r[10] or [],
            "places": r[11] or [],
            "named_events": r[12] or [],
        }
    )

n = len(titles)
print("%s/%s: %d strategic titles" % (CENTROID, TRACK, n))

# --- Determine bilateral vs domestic per title ---
home_iso = set()
cur.execute("SELECT iso_codes FROM centroids_v3 WHERE id = %s", (CENTROID,))
row = cur.fetchone()
if row and row[0]:
    home_iso = set(row[0])


def is_bilateral(t):
    tgt = t.get("target") or ""
    if not tgt or tgt == "NONE":
        return False, None
    # Check if target points to a foreign centroid
    for v in tgt.split(","):
        v = v.strip()
        if (
            v
            and v != "NONE"
            and v not in home_iso
            and not v.startswith(CENTROID.split("-")[1][:2])
        ):
            return True, v
    return False, None


def week_of(dt):
    if not dt:
        return "W0"
    day = dt.day
    if day <= 7:
        return "W1"
    if day <= 14:
        return "W2"
    if day <= 21:
        return "W3"
    return "W4"


# --- CLUSTERING ---
# Bilateral: subject + target + week
# Domestic: subject + anchor signal + temporal gap

# Step 1: Split bilateral vs domestic
bilateral_groups = defaultdict(list)  # (subject, target, week) -> [indices]
domestic_titles = []  # indices

for i, t in enumerate(titles):
    is_bi, target_code = is_bilateral(t)
    if is_bi and target_code:
        key = (t["subject"], target_code, week_of(t["pubdate_utc"]))
        bilateral_groups[key].append(i)
    else:
        domestic_titles.append(i)

print(
    "Bilateral: %d groups, %d titles"
    % (len(bilateral_groups), sum(len(v) for v in bilateral_groups.values()))
)
print("Domestic: %d titles" % len(domestic_titles))

# Step 2: Domestic clustering — same as faceted v1 (anchor signal + temporal)
UBIQUITOUS_RATIO = 0.10
ANCHOR_MIN = 3
TIME_GAP_DAYS = 1

# Signal frequency for domestic titles
sig_freq = Counter()
for i in domestic_titles:
    t = titles[i]
    for p in t["persons"]:
        sig_freq["PER:" + p.upper()] += 1
    for o in t["orgs"]:
        sig_freq["ORG:" + o.upper()] += 1
    for p in t["places"]:
        sig_freq["PLC:" + p.upper()] += 1
    for e in t["named_events"]:
        sig_freq["EVT:" + e] += 1

dom_n = len(domestic_titles)
ubiquitous = {
    s for s, c in sig_freq.items() if dom_n > 0 and c > dom_n * UBIQUITOUS_RATIO
}


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
        anchors.add("EVT:" + e)
    return anchors


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


# Domestic anchor clustering
dom_groups = defaultdict(list)
dom_remainder = []

# Group by subject first
dom_by_subject = defaultdict(list)
for i in domestic_titles:
    dom_by_subject[titles[i]["subject"]].append(i)

for subject, indices in dom_by_subject.items():
    # Find anchors within subject group
    group_freq = Counter()
    title_anchors = {}
    for i in indices:
        a = get_anchors(i)
        title_anchors[i] = a
        for s in a:
            group_freq[s] += 1

    valid = {
        s for s, c in group_freq.items() if c >= ANCHOR_MIN and c < len(indices) * 0.50
    }

    anchor_groups = defaultdict(list)
    remainder = []
    for i in indices:
        ta = title_anchors[i] & valid
        if ta:
            best = max(ta, key=lambda a: group_freq[a])
            anchor_groups[best].append(i)
        else:
            remainder.append(i)

    for anchor, members in anchor_groups.items():
        for chunk in temporal_split(members):
            if len(chunk) >= 2:
                dom_groups[("DOM", subject, anchor)].extend(chunk)
            else:
                remainder.extend(chunk)

    dom_remainder.extend(remainder)

# --- BUILD ALL CLUSTERS ---
all_events = []

BILATERAL_SPLIT_THRESHOLD = 50  # sub-split large bilateral clusters by signal anchor

# Bilateral mega-clusters — sub-split large ones
for (subject, target, week), indices in bilateral_groups.items():
    if len(indices) < 2:
        dom_remainder.extend(indices)
        continue

    anchor = "TGT:" + target

    if len(indices) <= BILATERAL_SPLIT_THRESHOLD:
        # Small enough: keep as one event
        all_events.append(
            {
                "sector": titles[indices[0]]["sector"],
                "subject": subject,
                "anchor": anchor,
                "indices": indices,
            }
        )
    else:
        # Too large: sub-split by signal anchor within this group
        sub_freq = Counter()
        sub_anchors = {}
        for i in indices:
            a = get_anchors(i)
            sub_anchors[i] = a
            for s in a:
                sub_freq[s] += 1

        # Valid sub-anchors: 3+ titles, <50% of group
        valid_sub = {
            s
            for s, c in sub_freq.items()
            if c >= ANCHOR_MIN and c < len(indices) * 0.50
        }

        sub_groups = defaultdict(list)
        sub_remainder = []
        for i in indices:
            ta = sub_anchors[i] & valid_sub
            if ta:
                best = max(ta, key=lambda a: sub_freq[a])
                sub_groups[best].append(i)
            else:
                sub_remainder.append(i)

        for sub_anchor, members in sub_groups.items():
            for chunk in temporal_split(members):
                if len(chunk) >= 2:
                    all_events.append(
                        {
                            "sector": titles[chunk[0]]["sector"],
                            "subject": subject,
                            "anchor": "%s/%s" % (anchor, sub_anchor),
                            "indices": chunk,
                        }
                    )
                else:
                    sub_remainder.extend(chunk)

        # Remainder stays as one event (the "general" bucket for this bilateral+week)
        if len(sub_remainder) >= 2:
            all_events.append(
                {
                    "sector": titles[sub_remainder[0]]["sector"],
                    "subject": subject,
                    "anchor": anchor + " (general)",
                    "indices": sub_remainder,
                }
            )
        else:
            dom_remainder.extend(sub_remainder)

# Domestic signal-clusters
for (_, subject, anchor), indices in dom_groups.items():
    all_events.append(
        {
            "sector": titles[indices[0]]["sector"],
            "subject": subject,
            "anchor": anchor,
            "indices": indices,
        }
    )

all_events.sort(key=lambda e: -len(e["indices"]))

total_clustered = sum(len(e["indices"]) for e in all_events)
print()
print("=== RESULTS ===")
print("Emerged events: %d" % len(all_events))
print("Titles in events: %d" % total_clustered)
print("Remainder (catchall): %d" % len(dom_remainder))
print("Catchall rate: %d%%" % (len(dom_remainder) * 100 // n if n else 0))

print()
print("Top 25 events:")
for ev in all_events[:25]:
    sample = titles[ev["indices"][0]]["title_display"][:65]
    dates = [
        titles[i]["pubdate_utc"] for i in ev["indices"] if titles[i].get("pubdate_utc")
    ]
    d1 = min(dates).strftime("%m/%d") if dates else "?"
    d2 = max(dates).strftime("%m/%d") if dates else "?"
    print(
        "  [%3d] %s/%s anchor=%-20s %s-%s"
        % (len(ev["indices"]), ev["sector"], ev["subject"], ev["anchor"][:20], d1, d2)
    )
    print("        %s" % sample)

if not WRITE:
    print("\nDRY RUN. Use --write to save.")
    conn.close()
    sys.exit(0)

# --- WRITE TO DB ---
# Clean this CTM's events
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

    cur.execute(
        "INSERT INTO events_v3 (id,ctm_id,source_batch_count,date,first_seen,"
        "last_active,event_type,bucket_key,is_catchall,topic_core,created_at,updated_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())",
        (eid, CTM_ID, len(tids), d, fs, d, geo_type, geo_key, False, anchor or None),
    )
    for tid in tids:
        cur.execute(
            "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s::uuid) "
            "ON CONFLICT DO NOTHING",
            (eid, tid),
        )
    written += 1

# Write catchall singles
for i in dom_remainder:
    eid = str(uuid.uuid4())
    t = titles[i]
    d = t["pubdate_utc"] or MONTH
    geo_type, geo_key = tag_geo([i], titles, CENTROID)
    cur.execute(
        "INSERT INTO events_v3 (id,ctm_id,source_batch_count,date,first_seen,"
        "last_active,event_type,bucket_key,is_catchall,created_at,updated_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())",
        (eid, CTM_ID, 1, d, d, d, geo_type, geo_key, True),
    )
    cur.execute(
        "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s::uuid) "
        "ON CONFLICT DO NOTHING",
        (eid, t["id"]),
    )
    written += 1

conn.commit()

# Assign first-headline titles
cur.execute(
    """
    UPDATE events_v3 e SET title = (
        SELECT t.title_display FROM event_v3_titles et
        JOIN titles_v3 t ON t.id = et.title_id
        WHERE et.event_id = e.id
        ORDER BY t.pubdate_utc DESC LIMIT 1
    ) WHERE e.ctm_id = %s AND e.title IS NULL
""",
    (CTM_ID,),
)
conn.commit()

print("Written %d events." % written)
conn.close()
