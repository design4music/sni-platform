"""
Merge fragmented clusters into ~200 meaningful topics.

Input: 1405 visible clusters (events_v3 for a CTM)
Output: ~150-250 clusters via merged_into FK (soft merge, reversible)

Three passes (most reliable first):
  Pass 1: Title word Dice (>= 0.6) -- merge near-identical cluster titles
  Pass 2: Tag overlap (>= 2 shared tags) -- merge clusters with same signals
  Pass 3: Title-to-large-cluster matching -- absorb small clusters into the
           nearest large cluster by word overlap (lower threshold 0.35)

All merges use merged_into FK: absorbed cluster -> representative cluster.
Representatives always have the highest source count.
"""

import re
import sys
from collections import Counter, defaultdict

import psycopg2

sys.path.insert(0, ".")
sys.stdout.reconfigure(errors="replace")

MONTH = "2026-03-01"
CENTROID = sys.argv[1] if len(sys.argv) > 1 else "AMERICAS-USA"
TRACK = sys.argv[2] if len(sys.argv) > 2 else "geo_security"
DRY_RUN = "--dry-run" in sys.argv

STOP_WORDS = frozenset(
    "the a an in of on for to and is are was were with from at by as its it be "
    "has had have that this or but not no new over after into about up out more "
    "says said will could would may amid set than been also would should".split()
)

# Pass 1 config
DICE_THRESHOLD = 0.55
# Pass 2 config
TAG_OVERLAP_MIN = 2
# Pass 3 config
ABSORB_THRESHOLD = 0.35  # word overlap to absorb small into large
LARGE_CLUSTER_MIN = 10  # "large" = 10+ sources


def tokenize(text):
    words = set(re.findall(r"[a-z][a-z0-9]+", text.lower()))
    return words - STOP_WORDS


def dice(a, b):
    if not a or not b:
        return 0.0
    return 2 * len(a & b) / (len(a) + len(b))


def word_overlap(small_words, big_words):
    """Fraction of small's words found in big (with fuzzy 4-char prefix match)."""
    if not small_words or not big_words:
        return 0.0
    matches = 0
    for sw in small_words:
        for bw in big_words:
            if sw == bw:
                matches += 1
                break
            if len(sw) >= 4 and len(bw) >= 4 and (sw in bw or bw in sw):
                matches += 1
                break
    return matches / len(small_words)


# ---------------------------------------------------------------
conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/sni_v2")
cur = conn.cursor()

cur.execute(
    "SELECT id FROM ctm WHERE centroid_id = %s AND track = %s AND month = %s",
    (CENTROID, TRACK, MONTH),
)
ctm_id = cur.fetchone()[0]

# Reset any previous merges for this CTM
if not DRY_RUN:
    cur.execute(
        "UPDATE events_v3 SET merged_into = NULL WHERE ctm_id = %s AND merged_into IS NOT NULL",
        (ctm_id,),
    )
    conn.commit()
    print("Reset %d previous merges" % cur.rowcount)

# Fetch all visible clusters
cur.execute(
    """
    SELECT e.id, e.source_batch_count, e.title, e.tags
    FROM events_v3 e
    WHERE e.ctm_id = %s AND NOT e.is_catchall AND e.merged_into IS NULL
    ORDER BY e.source_batch_count DESC
    """,
    (ctm_id,),
)

clusters = []
for r in cur.fetchall():
    clusters.append(
        {
            "id": r[0],
            "src": r[1],
            "title": r[2] or "",
            "tags": set(r[3] or []),
            "words": tokenize(r[2] or ""),
        }
    )

n = len(clusters)
print("Clusters: %d" % n)

# Dynamic domain stop words from cluster titles
word_freq = Counter()
for c in clusters:
    for w in c["words"]:
        word_freq[w] += 1
domain_stop_cutoff = max(20, int(n * 0.12))
domain_stops = {w for w, cnt in word_freq.items() if cnt >= domain_stop_cutoff}
print(
    "Domain stop words (>=%d clusters): %s"
    % (domain_stop_cutoff, sorted(domain_stops, key=lambda w: -word_freq[w])[:10])
)

# Apply domain stops
for c in clusters:
    c["clean_words"] = c["words"] - domain_stops

# ---------------------------------------------------------------
# Union-Find for merge tracking
# ---------------------------------------------------------------
parent = {c["id"]: c["id"] for c in clusters}
size = {c["id"]: c["src"] for c in clusters}  # use src count as weight


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(a_id, b_id):
    """Merge b into a (a = larger/representative)."""
    ra, rb = find(a_id), find(b_id)
    if ra == rb:
        return False
    # Always keep the one with more sources as representative
    if size[rb] > size[ra]:
        ra, rb = rb, ra
    parent[rb] = ra
    size[ra] += size[rb]
    return True


# Index for fast lookup
id_to_cluster = {c["id"]: c for c in clusters}

# ---------------------------------------------------------------
# PASS 1: Title word Dice (cluster titles, not raw headlines)
# ---------------------------------------------------------------
print("\n--- Pass 1: Title Dice >= %.2f ---" % DICE_THRESHOLD)

# Build word index for candidate lookup
word_to_ids = defaultdict(set)
for c in clusters:
    for w in c["clean_words"]:
        if len(w) >= 4:
            word_to_ids[w].add(c["id"])

merged_p1 = 0
for c in clusters:
    cid = find(c["id"])
    for w in c["clean_words"]:
        if len(w) < 4 or len(word_to_ids[w]) > n * 0.05:
            continue  # skip very common words
        for other_id in word_to_ids[w]:
            other = id_to_cluster[other_id]
            if find(other_id) == cid:
                continue
            d = dice(c["clean_words"], other["clean_words"])
            if d >= DICE_THRESHOLD:
                if union(c["id"], other_id):
                    merged_p1 += 1

# Count clusters after pass 1
reps_p1 = set(find(c["id"]) for c in clusters)
print("Merged %d pairs -> %d clusters" % (merged_p1, len(reps_p1)))

# ---------------------------------------------------------------
# PASS 2: Tag overlap (>= 2 shared non-ubiquitous tags)
# ---------------------------------------------------------------
print("\n--- Pass 2: Tag overlap >= %d shared tags ---" % TAG_OVERLAP_MIN)

# Compute tag frequency
tag_freq = Counter()
for c in clusters:
    for t in c["tags"]:
        tag_freq[t] += 1

tag_ubiq_cutoff = max(10, int(n * 0.03))  # 3% of clusters
ubiq_tags = {t for t, cnt in tag_freq.items() if cnt >= tag_ubiq_cutoff}
print("Ubiquitous tags: %s" % sorted(ubiq_tags, key=lambda t: -tag_freq[t])[:8])

# Specific tags per cluster
for c in clusters:
    c["specific_tags"] = c["tags"] - ubiq_tags

# Build tag-to-cluster index (using representatives)
tag_to_reps = defaultdict(set)
for c in clusters:
    rep = find(c["id"])
    for t in c["specific_tags"]:
        tag_to_reps[t].add(rep)

# Build per-rep tag sets
rep_tags = defaultdict(set)
for c in clusters:
    rep = find(c["id"])
    rep_tags[rep].update(c["specific_tags"])

# Only merge SMALL clusters (<=5 members) into LARGE ones (>5 members) via tag overlap.
# Prevents cascade between large clusters.
merged_p2 = 0

# Classify by size after Pass 1
rep_member_count = defaultdict(int)
for c in clusters:
    rep_member_count[find(c["id"])] += 1

small_reps_p2 = {r for r, cnt in rep_member_count.items() if cnt <= 5}
large_reps_p2 = {r for r, cnt in rep_member_count.items() if cnt > 5}

for small_rep in small_reps_p2:
    tags = rep_tags.get(small_rep, set())
    if len(tags) < TAG_OVERLAP_MIN:
        continue

    # Find best large cluster match
    overlap_count = Counter()
    for t in tags:
        for other_rep in tag_to_reps[t]:
            other = find(other_rep)
            if other != find(small_rep) and other in large_reps_p2:
                overlap_count[other] += 1

    if not overlap_count:
        continue
    best_match, best_shared = overlap_count.most_common(1)[0]
    other_tags = rep_tags.get(best_match, set())
    min_tags = min(len(tags), len(other_tags))
    if (
        best_shared >= TAG_OVERLAP_MIN
        and min_tags > 0
        and best_shared >= min_tags * 0.5
    ):
        if union(best_match, small_rep):
            merged_p2 += 1

reps_p2 = set(find(c["id"]) for c in clusters)
print("Merged %d pairs -> %d clusters" % (merged_p2, len(reps_p2)))

# ---------------------------------------------------------------
# PASS 3: Absorb small clusters into nearest large cluster
# Large = LARGE_CLUSTER_MIN+ sources (after previous merges)
# Match by word overlap on clean_words (threshold ABSORB_THRESHOLD)
# ---------------------------------------------------------------
print("\n--- Pass 3: Absorb small into large (overlap >= %.2f) ---" % ABSORB_THRESHOLD)

# Rebuild clusters per representative
rep_clusters = defaultdict(list)
for c in clusters:
    rep_clusters[find(c["id"])].append(c)

# Large clusters: build combined word set
large_reps = []
large_words = {}
for rep, members in rep_clusters.items():
    total_src = sum(m["src"] for m in members)
    if total_src >= LARGE_CLUSTER_MIN:
        words = set()
        for m in members:
            words.update(m["clean_words"])
        large_words[rep] = words
        large_reps.append(rep)

print("Large clusters (>=%d src): %d" % (LARGE_CLUSTER_MIN, len(large_reps)))

# Small clusters: try to absorb into nearest large
absorbed_p3 = 0
for rep, members in rep_clusters.items():
    total_src = sum(m["src"] for m in members)
    if total_src >= LARGE_CLUSTER_MIN:
        continue  # already large

    # Combine words from all members
    small_words = set()
    for m in members:
        small_words.update(m["clean_words"])
    if not small_words:
        continue

    best_score = 0.0
    best_large = None
    for large_rep in large_reps:
        lr = find(large_rep)
        if lr == find(rep):
            continue
        # Skip mega-clusters (>300 src after merging) -- they've absorbed enough
        if size.get(lr, 0) > 300:
            continue
        sc = word_overlap(
            small_words, large_words.get(lr, large_words.get(large_rep, set()))
        )
        if sc > best_score:
            best_score = sc
            best_large = large_rep

    if best_large and best_score >= ABSORB_THRESHOLD:
        if union(best_large, rep):
            absorbed_p3 += 1

reps_p3 = set(find(c["id"]) for c in clusters)
print("Absorbed %d small clusters -> %d total clusters" % (absorbed_p3, len(reps_p3)))

# ---------------------------------------------------------------
# Results
# ---------------------------------------------------------------
final_clusters = defaultdict(list)
for c in clusters:
    final_clusters[find(c["id"])].append(c)

sizes = [sum(m["src"] for m in members) for members in final_clusters.values()]
member_counts = [len(members) for members in final_clusters.values()]

print("\n=== FINAL: %d clusters ===" % len(final_clusters))
print(
    "By merged-member count: 1=%d, 2-5=%d, 6-10=%d, 11-50=%d, 51+=%d"
    % (
        sum(1 for s in member_counts if s == 1),
        sum(1 for s in member_counts if 2 <= s <= 5),
        sum(1 for s in member_counts if 6 <= s <= 10),
        sum(1 for s in member_counts if 11 <= s <= 50),
        sum(1 for s in member_counts if s > 50),
    )
)
print(
    "By source count: 1-2=%d, 3-9=%d, 10-49=%d, 50-99=%d, 100+=%d"
    % (
        sum(1 for s in sizes if s <= 2),
        sum(1 for s in sizes if 3 <= s <= 9),
        sum(1 for s in sizes if 10 <= s <= 49),
        sum(1 for s in sizes if 50 <= s <= 99),
        sum(1 for s in sizes if s >= 100),
    )
)

print("\nTop 40 clusters:")
for rep in sorted(
    final_clusters.keys(), key=lambda r: -sum(m["src"] for m in final_clusters[r])
)[:40]:
    members = final_clusters[rep]
    total_src = sum(m["src"] for m in members)
    rep_cluster = id_to_cluster[rep]
    print(
        "  %5d src (%3d merged) | %s"
        % (total_src, len(members), rep_cluster["title"][:65])
    )

# Check specific cases
print("\n--- Check: Russia-Iran intelligence ---")
for rep, members in final_clusters.items():
    for m in members:
        if "russia" in m["title"].lower() and "intelligen" in m["title"].lower():
            total_src = sum(x["src"] for x in members)
            print("  Cluster %d src (%d merged):" % (total_src, len(members)))
            for x in sorted(members, key=lambda x: -x["src"])[:5]:
                print("    %3d src | %s" % (x["src"], x["title"][:70]))
            if len(members) > 5:
                print("    ... +%d more" % (len(members) - 5))
            break

print("\n--- Check: Submarine ---")
for rep, members in final_clusters.items():
    for m in members:
        if "submarine" in m["title"].lower() or "warship" in m["title"].lower():
            total_src = sum(x["src"] for x in members)
            print("  Cluster %d src (%d merged):" % (total_src, len(members)))
            for x in sorted(members, key=lambda x: -x["src"])[:5]:
                print("    %3d src | %s" % (x["src"], x["title"][:70]))
            if len(members) > 5:
                print("    ... +%d more" % (len(members) - 5))
            break

# ---------------------------------------------------------------
# Write merges to DB (if not dry run)
# ---------------------------------------------------------------
if not DRY_RUN:
    merge_count = 0
    for rep, members in final_clusters.items():
        for m in members:
            if m["id"] != rep:
                cur.execute(
                    "UPDATE events_v3 SET merged_into = %s WHERE id = %s",
                    (str(rep), str(m["id"])),
                )
                merge_count += 1
    conn.commit()
    print("\nWrote %d merges to DB" % merge_count)
else:
    print("\nDRY RUN -- no DB changes")

conn.close()
