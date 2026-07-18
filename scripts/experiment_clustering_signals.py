"""
Experiment: measure impact of adding sector/subject/actor/target to clustering.

Compares current clustering (entity signals only) vs enriched clustering
(entity signals + structural labels) for USA security March 2026.

Does NOT modify any data. Read-only analysis.
"""

import sys
from collections import Counter, defaultdict

import psycopg2

sys.stdout.reconfigure(errors="replace")

MONTH = "2026-03-01"
CENTROID = sys.argv[1] if len(sys.argv) > 1 else "AMERICAS-USA"
TRACK = sys.argv[2] if len(sys.argv) > 2 else "geo_security"

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/sni_v2")
cur = conn.cursor()

cur.execute(
    "SELECT id FROM ctm WHERE centroid_id = %s AND track = %s AND month = %s",
    (CENTROID, TRACK, MONTH),
)
ctm_id = cur.fetchone()[0]

# Load all clusters with their title-level labels
print("Loading clusters and title labels...")
cur.execute(
    """
    SELECT e.id, e.source_batch_count, e.title, e.bucket_key, e.event_type
    FROM events_v3 e
    WHERE e.ctm_id = %s AND NOT e.is_catchall AND e.merged_into IS NULL
    ORDER BY e.source_batch_count DESC
""",
    (ctm_id,),
)

clusters = {}
for r in cur.fetchall():
    clusters[r[0]] = {
        "id": r[0],
        "src": r[1],
        "title": r[2] or "",
        "bucket_key": r[3],
        "event_type": r[4],
        "sectors": Counter(),
        "subjects": Counter(),
        "actors": Counter(),
        "targets": Counter(),
        "action_classes": Counter(),
        "places": Counter(),
        "persons": Counter(),
        "orgs": Counter(),
    }

cluster_ids = [str(cid) for cid in clusters.keys()]
cur.execute(
    """
    SELECT et.event_id, tl.sector, tl.subject, tl.actor, tl.target,
           tl.action_class, tl.places, tl.persons, tl.orgs
    FROM event_v3_titles et
    JOIN title_labels tl ON tl.title_id = et.title_id
    WHERE et.event_id = ANY(%s::uuid[])
""",
    (cluster_ids,),
)

for r in cur.fetchall():
    c = clusters.get(r[0])
    if not c:
        continue
    if r[1]:
        c["sectors"][r[1]] += 1
    if r[2]:
        c["subjects"][r[2]] += 1
    if r[3]:
        c["actors"][r[3]] += 1
    if r[4]:
        c["targets"][r[4]] += 1
    if r[5]:
        c["action_classes"][r[5]] += 1
    for p in r[6] or []:
        c["places"][p] += 1
    for p in r[7] or []:
        c["persons"][p] += 1
    for o in r[8] or []:
        c["orgs"][o] += 1

n = len(clusters)
print("Loaded %d clusters" % n)

# --- Analysis 1: Direction mixing ---
print("\n=== ANALYSIS 1: Direction Mixing ===")
print("Clusters where US->IR and IR->US titles are mixed (opposing directions)")

mixed = []
for cid, c in clusters.items():
    us_to_ir = (
        sum(v for k, v in c["actors"].items() if k.startswith("US")) > 0
        and c["targets"].get("IR", 0) > 0
    )
    ir_to_us = sum(v for k, v in c["actors"].items() if k.startswith("IR")) > 0 and any(
        v > 0 for k, v in c["targets"].items() if k.startswith("US")
    )

    if us_to_ir and ir_to_us:
        us_count = sum(v for k, v in c["actors"].items() if k.startswith("US"))
        ir_count = sum(v for k, v in c["actors"].items() if k.startswith("IR"))
        mixed.append((c, us_count, ir_count))

print("  Mixed direction clusters: %d / %d" % (len(mixed), n))
print("  Top 10 by size:")
for c, us_cnt, ir_cnt in sorted(mixed, key=lambda x: -x[0]["src"])[:10]:
    dom_actor = c["actors"].most_common(1)[0][0] if c["actors"] else "?"
    dom_target = c["targets"].most_common(1)[0][0] if c["targets"] else "?"
    print(
        "    %4d src | %s->%s (US:%d IR:%d) | %s"
        % (c["src"], dom_actor, dom_target, us_cnt, ir_cnt, c["title"][:55])
    )

# --- Analysis 2: Subject homogeneity ---
print("\n=== ANALYSIS 2: Subject Homogeneity ===")
print("Do clusters have a dominant subject, or are they mixed?")

subject_purity = []
for c in clusters.values():
    total = sum(c["subjects"].values())
    if total == 0:
        continue
    top_subj, top_cnt = c["subjects"].most_common(1)[0]
    purity = top_cnt / total
    subject_purity.append((c, purity, top_subj, total))

bins = {">=90%": 0, "70-89%": 0, "50-69%": 0, "<50%": 0}
for c, p, s, t in subject_purity:
    if p >= 0.9:
        bins[">=90%"] += 1
    elif p >= 0.7:
        bins["70-89%"] += 1
    elif p >= 0.5:
        bins["50-69%"] += 1
    else:
        bins["<50%"] += 1

print("  Subject purity distribution:")
for label, cnt in bins.items():
    print("    %s: %d clusters" % (label, cnt))

# Low purity large clusters
low_purity_large = [
    (c, p, s, t) for c, p, s, t in subject_purity if p < 0.5 and c["src"] >= 20
]
print("\n  Low-purity (<50%%) large clusters (20+ src): %d" % len(low_purity_large))
for c, p, s, t in sorted(low_purity_large, key=lambda x: -x[0]["src"])[:10]:
    subs = ", ".join("%s:%d" % (k, v) for k, v in c["subjects"].most_common(3))
    print(
        "    %4d src | purity %.0f%% | %s | %s"
        % (c["src"], 100 * p, subs, c["title"][:45])
    )

# --- Analysis 3: What would sector+subject pre-grouping buy us? ---
print("\n=== ANALYSIS 3: Sector+Subject Pre-grouping ===")
print("If we grouped by dominant sector+subject BEFORE entity matching,")
print("how many fewer cross-subject merges would happen?")

# Simulate: assign each cluster to its dominant (sector, subject)
sector_subject_groups = defaultdict(list)
for c in clusters.values():
    dom_sector = c["sectors"].most_common(1)[0][0] if c["sectors"] else "UNKNOWN"
    dom_subject = c["subjects"].most_common(1)[0][0] if c["subjects"] else "UNKNOWN"
    sector_subject_groups[(dom_sector, dom_subject)].append(c)

print("  Unique (sector, subject) groups: %d" % len(sector_subject_groups))
print("\n  Top 15 groups:")
for (sec, subj), members in sorted(
    sector_subject_groups.items(), key=lambda x: -len(x[1])
)[:15]:
    total_src = sum(c["src"] for c in members)
    print("    %-12s %-22s %4d clusters %6d src" % (sec, subj, len(members), total_src))

# --- Analysis 4: What would actor->target direction split buy us? ---
print("\n=== ANALYSIS 4: Direction Split Potential ===")
print("For MIDEAST-IRAN bilateral clusters: if we split US->IR from IR->US")

iran_clusters = [c for c in clusters.values() if c["bucket_key"] == "MIDEAST-IRAN"]
print("  Total Iran bilateral clusters: %d" % len(iran_clusters))

us_attacking = 0
ir_retaliating = 0
ambiguous = 0
for c in iran_clusters:
    us_actors = sum(v for k, v in c["actors"].items() if k.startswith("US"))
    ir_actors = sum(v for k, v in c["actors"].items() if k.startswith("IR"))
    total = us_actors + ir_actors
    if total == 0:
        ambiguous += 1
    elif us_actors > ir_actors * 2:
        us_attacking += 1
    elif ir_actors > us_actors * 2:
        ir_retaliating += 1
    else:
        ambiguous += 1

print("  US->IR dominant: %d clusters" % us_attacking)
print("  IR->US dominant: %d clusters" % ir_retaliating)
print("  Ambiguous/mixed: %d clusters" % ambiguous)

# --- Analysis 5: Combined improvement estimate ---
print("\n=== ANALYSIS 5: Combined Improvement Estimate ===")
print("If we add sector+subject pre-filter + direction split:")

# Count current "problem clusters" that would be fixed
problem_mixed_dir = len(mixed)
problem_low_purity = len(low_purity_large)

print(
    "  Problem clusters (mixed direction): %d -> would be split into 2+ each"
    % problem_mixed_dir
)
print(
    "  Problem clusters (low subject purity, 20+ src): %d -> would go to correct group"
    % problem_low_purity
)
print(
    "  Total affected: ~%d clusters out of %d"
    % (problem_mixed_dir + problem_low_purity, n)
)

# What would the new clustering look like?
# Simulate: group by (bucket, dominant_direction, dominant_subject)
fine_groups = defaultdict(list)
for c in clusters.values():
    bucket = c["bucket_key"] or c["event_type"]
    dom_subj = c["subjects"].most_common(1)[0][0] if c["subjects"] else "UNK"

    # Direction for bilateral
    if c["bucket_key"]:
        us_actors = sum(v for k, v in c["actors"].items() if k.startswith("US"))
        ir_actors = sum(v for k, v in c["actors"].items() if k.startswith("IR"))
        direction = (
            "US>"
            if us_actors > ir_actors
            else ("IR>" if ir_actors > us_actors else "MX>")
        )
    else:
        direction = ""

    fine_groups[(bucket, direction, dom_subj)].append(c)

print("\n  Fine-grained groups (bucket + direction + subject): %d" % len(fine_groups))
print(
    "  vs current bucket-only groups: %d"
    % len(set(c["bucket_key"] or c["event_type"] for c in clusters.values()))
)
print(
    "  This means %dx more structure before entity matching"
    % (
        len(fine_groups)
        // max(
            1, len(set(c["bucket_key"] or c["event_type"] for c in clusters.values()))
        )
    )
)

conn.close()
print("\nDone.")
