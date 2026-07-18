"""
Mechanical clustering v4: title similarity + shared signals + actor sets.

Approach (most reliable first):
  Pass 1: Title word similarity (Dice >= 0.6) -- merge near-identical headlines
  Pass 2: Signal overlap -- merge clusters sharing 2+ non-ubiquitous signals
  Pass 3: Actor+target grouping -- pool into theater buckets

No LLM. No hard sector/subject partitions. No 1-day temporal splits.
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

STOP_WORDS = frozenset(
    "the a an in of on for to and is are was were with from at by as its it be "
    "has had have that this or but not no new over after into about up out more "
    "says said will could would may amid set than been also would should".split()
)

# Dynamic domain stop words: computed per-CTM from word frequency
DOMAIN_STOP_THRESHOLD = 0.15  # words in >15% of titles = too common to discriminate

# Ubiquity threshold: signals in >8% of titles are too common to discriminate
UBIQ_THRESHOLD = 0.08
# Title similarity: Dice coefficient threshold for merging
TITLE_DICE_THRESHOLD = 0.65
# Signal overlap: minimum shared signals to merge two clusters
SIGNAL_MERGE_MIN = 2


def tokenize(text):
    words = set(re.findall(r"[a-z][a-z0-9]+", text.lower()))
    return words - STOP_WORDS


def dice(a, b):
    """Dice coefficient between two word sets."""
    if not a or not b:
        return 0.0
    return 2 * len(a & b) / (len(a) + len(b))


# ---------------------------------------------------------------
conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/sni_v2")
cur = conn.cursor()

cur.execute(
    "SELECT id FROM ctm WHERE centroid_id = %s AND track = %s AND month = %s",
    (CENTROID, TRACK, MONTH),
)
ctm_id = cur.fetchone()[0]

# Fetch all titles with labels for this CTM
cur.execute(
    """
    SELECT t.id, t.title_display, t.pubdate_utc::date,
           tl.actor, tl.target, tl.persons, tl.orgs, tl.places, tl.named_events
    FROM titles_v3 t
    JOIN title_labels tl ON tl.title_id = t.id
    JOIN title_assignments ta ON ta.title_id = t.id
    WHERE ta.ctm_id = %s
    ORDER BY t.pubdate_utc
    """,
    (ctm_id,),
)

titles = []
for r in cur.fetchall():
    title_text = r[1] or ""
    words = tokenize(title_text)

    # Build signal set (normalized lowercase)
    signals = set()
    for p in r[5] or []:
        signals.add("PER:" + p.lower())
    for o in r[6] or []:
        signals.add("ORG:" + o.lower())
    for p in r[7] or []:
        signals.add("PLC:" + p.lower())
    for e in r[8] or []:
        signals.add("EVT:" + e.lower())

    titles.append(
        {
            "id": r[0],
            "text": title_text,
            "date": r[2],
            "words": words,
            "signals": signals,
            "actor": (r[3] or "NONE").upper(),
            "target": (r[4] or "NONE").upper(),
        }
    )

n = len(titles)
print("Titles: %d" % n)

# ---------------------------------------------------------------
# Compute domain stop words dynamically (too common to discriminate)
# ---------------------------------------------------------------
word_freq = Counter()
for t in titles:
    for w in t["words"]:
        word_freq[w] += 1

domain_stop_cutoff = int(n * DOMAIN_STOP_THRESHOLD)
domain_stops = {w for w, c in word_freq.items() if c >= domain_stop_cutoff}
print(
    "Domain stop words (>=%d titles): %s"
    % (domain_stop_cutoff, sorted(domain_stops, key=lambda w: -word_freq[w])[:15])
)

# Remove domain stops from title word sets
for t in titles:
    t["words"] = t["words"] - domain_stops

# ---------------------------------------------------------------
# Compute signal frequency (for ubiquity filter)
# ---------------------------------------------------------------
sig_freq = Counter()
for t in titles:
    for s in t["signals"]:
        sig_freq[s] += 1

ubiq_cutoff = int(n * UBIQ_THRESHOLD)
ubiquitous = {s for s, c in sig_freq.items() if c >= ubiq_cutoff}
print("Ubiquitous signals (>=%d titles): %d" % (ubiq_cutoff, len(ubiquitous)))
for s in sorted(ubiquitous, key=lambda s: -sig_freq[s])[:10]:
    print("  %s (%d)" % (s, sig_freq[s]))

# Specific signals per title (non-ubiquitous)
for t in titles:
    t["specific_signals"] = t["signals"] - ubiquitous

# ---------------------------------------------------------------
# PASS 1: Title word similarity (Dice >= threshold)
# Greedy: largest-first, absorb similar titles
# ---------------------------------------------------------------
print("\n--- Pass 1: Title similarity (Dice >= %.2f) ---" % TITLE_DICE_THRESHOLD)

# Sort by date to process chronologically
cluster_id = list(range(n))  # union-find: each title starts as own cluster


def find(x):
    while cluster_id[x] != x:
        cluster_id[x] = cluster_id[cluster_id[x]]
        x = cluster_id[x]
    return x


def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        cluster_id[rb] = ra


# Build word-to-title index for faster matching
word_index = defaultdict(set)
for i, t in enumerate(titles):
    for w in t["words"]:
        if len(w) >= 4:  # only index significant words
            word_index[w].add(i)

# For each title, find candidates via shared significant words, then check Dice
merged_pass1 = 0
for i in range(n):
    if find(i) != i:
        continue  # already merged

    # Get candidate titles that share at least one 4+ char word
    candidates = set()
    for w in titles[i]["words"]:
        if len(w) >= 4 and len(word_index[w]) < n * 0.1:  # skip very common words
            candidates.update(word_index[w])
    candidates.discard(i)

    for j in candidates:
        if find(j) == find(i):
            continue  # already same cluster
        d = dice(titles[i]["words"], titles[j]["words"])
        if d >= TITLE_DICE_THRESHOLD:
            union(i, j)
            merged_pass1 += 1

# Count clusters after pass 1
pass1_clusters = defaultdict(list)
for i in range(n):
    pass1_clusters[find(i)].append(i)

print("Merged %d title pairs -> %d clusters" % (merged_pass1, len(pass1_clusters)))

# ---------------------------------------------------------------
# PASS 2: Signal overlap -- merge small clusters into larger ones
# Only merge if overlap is HIGH relative to the smaller cluster's signals.
# No cascading: only merge into clusters with 3+ titles (established clusters).
# ---------------------------------------------------------------
print("\n--- Pass 2: Signal overlap (merge small into matching large) ---")

# Build per-cluster signal profile
cluster_signals = {}
cluster_sizes = {}
for rep, members in pass1_clusters.items():
    signals = set()
    for i in members:
        signals.update(titles[i]["specific_signals"])
    cluster_signals[rep] = signals
    cluster_sizes[rep] = len(members)

# Sort clusters: largest first (they are merge targets, not sources)
reps_by_size = sorted(pass1_clusters.keys(), key=lambda r: -cluster_sizes[r])

# Build signal-to-cluster index (only for clusters with 3+ titles = established)
sig_to_large = defaultdict(set)
for rep in reps_by_size:
    if cluster_sizes[rep] >= 3:
        for s in cluster_signals.get(rep, set()):
            sig_to_large[s].add(rep)

# For each small cluster (1-2 titles), find best large cluster match
merged_pass2 = 0
for rep in reps_by_size:
    if cluster_sizes[rep] >= 2:
        continue  # established cluster, don't merge into others
    sigs = cluster_signals.get(rep, set())
    if not sigs:
        continue

    # Find best match among large clusters
    overlap_count = Counter()
    for s in sigs:
        for large_rep in sig_to_large[s]:
            if find(large_rep) != find(rep):
                overlap_count[find(large_rep)] += 1

    if not overlap_count:
        continue

    best_match, best_overlap = overlap_count.most_common(1)[0]
    # Require at least 2 shared signals AND >40% of small cluster's signals
    if best_overlap >= 2 and best_overlap >= len(sigs) * 0.4:
        union(rep, best_match)
        merged_pass2 += 1

# Rebuild clusters
pass2_clusters = defaultdict(list)
for i in range(n):
    pass2_clusters[find(i)].append(i)

print(
    "Merged %d small clusters -> %d total clusters"
    % (merged_pass2, len(pass2_clusters))
)

# ---------------------------------------------------------------
# Rebuild after pass 2
# ---------------------------------------------------------------
pass2_clusters = defaultdict(list)
for i in range(n):
    pass2_clusters[find(i)].append(i)

# Count singletons
singletons = sum(1 for m in pass2_clusters.values() if len(m) == 1)
print(
    "After pass 2: %d clusters, %d singletons (%.0f%%)"
    % (len(pass2_clusters), singletons, 100 * singletons / n)
)

# ---------------------------------------------------------------
# Report
# ---------------------------------------------------------------
print("\n=== RESULTS: %d clusters ===" % len(pass2_clusters))

# Sort by size
sorted_clusters = sorted(pass2_clusters.items(), key=lambda x: -len(x[1]))

# Size distribution
sizes = [len(m) for m in pass2_clusters.values()]
print(
    "Size distribution: 1=%d, 2-5=%d, 6-10=%d, 11-50=%d, 51+=%d"
    % (
        sum(1 for s in sizes if s == 1),
        sum(1 for s in sizes if 2 <= s <= 5),
        sum(1 for s in sizes if 6 <= s <= 10),
        sum(1 for s in sizes if 11 <= s <= 50),
        sum(1 for s in sizes if s > 50),
    )
)

print("\nTop 30 clusters:")
for rep, members in sorted_clusters[:30]:
    sample = titles[members[0]]["text"][:70]
    # Most common actor+target in cluster
    actors = Counter(titles[i]["actor"] for i in members)
    targets = Counter(titles[i]["target"] for i in members)
    top_actor = actors.most_common(1)[0][0] if actors else "?"
    top_target = targets.most_common(1)[0][0] if targets else "?"
    # Top specific signals
    all_sigs = Counter()
    for i in members:
        for s in titles[i]["specific_signals"]:
            all_sigs[s] += 1
    top_sigs = [s for s, _ in all_sigs.most_common(3)]
    print(
        "  %4d titles | %s->%s | %s | %s"
        % (
            len(members),
            top_actor[:15],
            top_target[:5],
            ", ".join(top_sigs)[:40],
            sample,
        )
    )

# Show the Russia-Iran intelligence example
print("\n--- Check: 'Russia intelligence Iran' ---")
for rep, members in sorted_clusters:
    for i in members:
        if (
            "russia" in titles[i]["text"].lower()
            and "intelligence" in titles[i]["text"].lower()
            and "iran" in titles[i]["text"].lower()
        ):
            print("  Cluster %d (%d titles):" % (rep, len(members)))
            for j in members[:5]:
                print("    %s" % titles[j]["text"][:80])
            if len(members) > 5:
                print("    ... +%d more" % (len(members) - 5))
            print()
            break

conn.close()
