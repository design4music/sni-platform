"""
Two-pass event family assembly.

Pass 1 (LLM):  Read ALL cluster titles -> identify distinct stories + keywords
Pass 2 (Mech): Assign every cluster to best-matching story by keyword+tag overlap

Pre-step: absorb tiny fragments (<5 src) into nearest anchor by tag overlap,
          so the LLM sees ~300 items not 1400.
"""

import json
import re
import sys

import httpx
import psycopg2

sys.path.insert(0, ".")
sys.stdout.reconfigure(errors="replace")

from core.config import config  # noqa: E402

# --- Configuration ---
CENTROID = sys.argv[1] if len(sys.argv) > 1 else "AMERICAS-USA"
TRACK = sys.argv[2] if len(sys.argv) > 2 else "geo_security"
MONTH = "2026-03-01"

# Centroid display names (just the ones we'll test)
CENTROID_NAMES = {
    "AMERICAS-USA": "United States",
    "MIDEAST-IRAN": "Iran",
    "MIDEAST-ISRAEL": "Israel",
    "EUROPE-FRANCE": "France",
    "EUROPE-RUSSIA": "Russia",
    "ASIA-CHINA": "China",
}

TRACK_LABELS = {
    "geo_security": "Security & Defense",
    "geo_politics": "Politics & Governance",
    "geo_economy": "Economy & Trade",
    "geo_society": "Society & Culture",
}

FRAGMENT_THRESHOLD = 5  # clusters with fewer sources = fragments
MIN_TAG_OVERLAP = 1  # need at least 1 shared tag to absorb

# ---------------------------------------------------------------
conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/sni_v2")
cur = conn.cursor()

cur.execute(
    "SELECT id FROM ctm WHERE centroid_id = %s AND track = %s AND month = %s",
    (CENTROID, TRACK, MONTH),
)
row = cur.fetchone()
if not row:
    print("CTM not found: %s %s %s" % (CENTROID, TRACK, MONTH))
    sys.exit(1)
ctm_id = row[0]

# Fetch ALL clusters with tags and date range
cur.execute(
    """
    SELECT e.id, e.source_batch_count, e.title, e.tags,
           min(t.pubdate_utc)::date as first_date,
           max(t.pubdate_utc)::date as last_date
    FROM events_v3 e
    JOIN event_v3_titles et ON et.event_id = e.id
    JOIN titles_v3 t ON t.id = et.title_id
    WHERE e.ctm_id = %s AND NOT e.is_catchall AND e.merged_into IS NULL
    GROUP BY e.id, e.source_batch_count, e.title, e.tags
    ORDER BY e.source_batch_count DESC
    """,
    (ctm_id,),
)

clusters = []
for r in cur.fetchall():
    clusters.append(
        {
            "db_id": r[0],
            "src": r[1],
            "title": r[2] or "Untitled",
            "tags": r[3] or [],
            "first": r[4],
            "last": r[5],
        }
    )

total_src = sum(c["src"] for c in clusters)
n_total = len(clusters)
centroid_name = CENTROID_NAMES.get(CENTROID, CENTROID)
track_label = TRACK_LABELS.get(TRACK, TRACK)

print("CTM: %s %s %s" % (CENTROID, TRACK, MONTH))
print("Total clusters: %d, total sources: %d" % (n_total, total_src))

# ---------------------------------------------------------------
# PRE-REDUCTION: absorb fragments into nearest anchor
# ---------------------------------------------------------------
anchors = [c for c in clusters if c["src"] >= FRAGMENT_THRESHOLD]
fragments = [c for c in clusters if c["src"] < FRAGMENT_THRESHOLD]

# For each fragment, find anchor with most tag overlap
absorbed_count = 0
for frag in fragments:
    frag_tags = set(frag["tags"])
    if not frag_tags:
        continue

    best_anchor = None
    best_overlap = 0
    for anc in anchors:
        overlap = len(frag_tags & set(anc["tags"]))
        if overlap > best_overlap:
            best_overlap = overlap
            best_anchor = anc
    if best_anchor and best_overlap >= MIN_TAG_OVERLAP:
        best_anchor.setdefault("absorbed_src", 0)
        best_anchor["absorbed_src"] += frag["src"]
        best_anchor.setdefault("absorbed_ids", [])
        best_anchor["absorbed_ids"].append(frag)
        absorbed_count += 1

# Remaining unabsorbed fragments go to LLM as well
unabsorbed = [
    f for f in fragments if not any(f in a.get("absorbed_ids", []) for a in anchors)
]

# Build the LLM input list: anchors + unabsorbed fragments
llm_items = anchors + unabsorbed
llm_items.sort(key=lambda c: -c["src"])

print(
    "Anchors: %d, Absorbed fragments: %d, Unabsorbed: %d"
    % (len(anchors), absorbed_count, len(unabsorbed))
)
print("Items sent to LLM: %d" % len(llm_items))

# ---------------------------------------------------------------
# Target family count calibration
# ---------------------------------------------------------------
if total_src < 500:
    target_min, target_max = 3, 10
elif total_src < 2000:
    target_min, target_max = 8, 20
elif total_src < 5000:
    target_min, target_max = 15, 35
else:
    target_min, target_max = 25, 60

print("Target families: %d-%d" % (target_min, target_max))

# ---------------------------------------------------------------
# Build LLM input lines
# ---------------------------------------------------------------
lines = []
for i, c in enumerate(llm_items, 1):
    extra_src = c.get("absorbed_src", 0)
    display_src = c["src"] + extra_src
    tag_str = ", ".join(c["tags"][:3]) if c["tags"] else ""
    title = c["title"][:100]
    line = "%d. [%d src] %s" % (i, display_src, title)
    if tag_str:
        line += "  {%s}" % tag_str
    lines.append(line)

# ---------------------------------------------------------------
# PASS 1: Story Discovery
# ---------------------------------------------------------------
# Giant CTMs get an extra instruction about the general commentary bucket
is_giant = total_src >= 3000

GENERAL_COMMENTARY_BLOCK = (
    """
GENERAL COMMENTARY BUCKET:
Many clusters are meta-coverage that does NOT describe a specific event:
- "Trump says war will continue" / "Trump threatens" / "Trump vows"
- "experts warn about costs" / "analysts say"
- "conflict enters day N" / "war continues" / "tensions escalate"
- General status updates, opinion roundups, political warnings
These comment on the theater as a whole, not a specific operation or incident.
Create exactly ONE story titled "General [theater name] commentary and updates"
with keywords that match this generic vocabulary: "continues", "threatens",
"warns", "vows", "says", "costs", "risks", "escalates", "challenges",
"strategy", "progress", "winding down", "ahead".
"""
    if is_giant
    else ""
)

DISCOVERY_PROMPT = """\
Read %d news cluster titles from %s (%s), March 2026.

Each line: number, source count, headline, {key signals}.
Clusters are mechanically grouped headlines. Many cover fragments of one story.

TASK: Identify the %d-%d distinct STORIES this month.

A story = one specific developing situation. Defined by a SPINE -- the one
thing a reader would remember:
- A specific geographic chokepoint being blocked (Hormuz, Suez)
- A specific target being struck (Kharg Island, nuclear facility at Natanz)
- A specific person killed or making decisions (assassination, arrest)
- A specific military asset or unit deployed (carrier group, Marines)
- A specific domestic incident (shooting, protest, scandal)
- A specific policy action (funding vote, enforcement operation)

CRITICAL RULE -- NO MEGA-STORIES:
"US-Iran war" or "military strikes on Iran" is NOT a story -- it is a THEATER
containing many stories. Each distinct spine within a theater = separate story.
If a story has 30%%%%+ of all clusters, you MUST split it into specific threads.

Same spine, different days = ONE story (merge).
Different spines, same theater = DIFFERENT stories (split).
Consequence/reaction to event X = part of X (merge).
%s
KEYWORDS RULE:
Keywords must be SPECIFIC DISCRIMINATORS that distinguish this story from others.
BAD keywords: "Iran", "Trump", "strikes", "war" -- these match everything.
GOOD keywords: "Hormuz", "tanker", "escort", "blockade" (specific to Hormuz story).
GOOD keywords: "Kharg", "oil", "island", "refinery" (specific to Kharg story).
Each story's keywords should match ITS clusters and NOT match other stories.

For each story:
- title: 5-15 words naming the SPECIFIC spine
- keywords: 5-8 DISCRIMINATING terms (proper nouns, specific places, operations, unique verbs). Avoid terms shared across many stories.
- scale: "large" (50+ clusters), "medium" (15-49), "small" (<15)

Return JSON only:
{"stories": [{"title": "...", "keywords": [...], "scale": "..."}]}""" % (
    len(llm_items),
    centroid_name,
    track_label,
    target_min,
    target_max,
    GENERAL_COMMENTARY_BLOCK,
)

print("\n--- Pass 1: Story Discovery ---")
print("Sending %d items (%d tokens est)..." % (len(lines), len("\n".join(lines)) // 4))

resp = httpx.post(
    config.deepseek_api_url + "/chat/completions",
    headers={"Authorization": "Bearer " + config.deepseek_api_key},
    json={
        "model": config.llm_model,
        "messages": [
            {"role": "system", "content": DISCOVERY_PROMPT},
            {"role": "user", "content": "\n".join(lines)},
        ],
        "temperature": 0.1,
        "max_tokens": 8000,
    },
    timeout=300,
)

raw = resp.json()
if "error" in raw:
    print("API error: %s" % raw["error"])
    conn.close()
    sys.exit(1)

text = raw["choices"][0]["message"]["content"].strip()
usage = raw.get("usage", {})
print(
    "Tokens: %d in, %d out"
    % (usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
)

# Strip markdown code fences if present
text = re.sub(r"^```json\s*", "", text)
text = re.sub(r"\s*```$", "", text)

stories = None
try:
    stories = json.loads(text)
except Exception:
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            stories = json.loads(m.group(0))
        except Exception:
            pass

if not stories or "stories" not in stories:
    print("FAILED to parse stories")
    print(text[:800])
    conn.close()
    sys.exit(1)

stories = stories["stories"]
print("Identified %d stories:\n" % len(stories))
for s in stories:
    print("  [%6s] %s" % (s.get("scale", "?"), s["title"]))
    print("           kw: %s" % ", ".join(s.get("keywords", [])))

# ---------------------------------------------------------------
# PASS 2: Mechanical Assignment
# ---------------------------------------------------------------
print("\n--- Pass 2: Mechanical Assignment ---")

STOP_WORDS = frozenset(
    "the a an in of on for to and is are was were with from at by as its it be "
    "has had have that this or but not no new over after into about up out more "
    "says said will could would may amid us set than been also".split()
)


def word_match(w1, w2):
    """Fuzzy word match: exact, containment (4+ chars), or shared 4-char prefix."""
    if w1 == w2:
        return True
    if len(w1) >= 4 and len(w2) >= 4:
        if w1 in w2 or w2 in w1:
            return True
        # Shared prefix (iran/iranian, strike/strikes/striking)
        prefix = 0
        for a, b in zip(w1, w2):
            if a == b:
                prefix += 1
            else:
                break
        if prefix >= 4:
            return True
    return False


def tokenize(text):
    """Lowercase words, remove stop words and short words."""
    words = set(re.findall(r"[a-z][a-z0-9]+", text.lower()))
    return words - STOP_WORDS


def extract_tag_words(tags):
    """PLC:HORMUZ -> hormuz, person:trump -> trump."""
    words = set()
    for tag in tags:
        parts = tag.split(":")
        if len(parts) > 1:
            w = parts[1].lower().replace("_", " ").replace("-", " ")
            for token in w.split():
                if len(token) >= 3:
                    words.add(token)
    return words


# Build story keyword sets
story_kw_sets = []
for s in stories:
    kw = tokenize(s["title"])
    for w in s.get("keywords", []):
        kw.update(tokenize(w))
    story_kw_sets.append(kw)

# Compute IDF: keywords appearing in many stories get lower weight
import math  # noqa: E402

all_kw_union = set()
for skw in story_kw_sets:
    all_kw_union.update(skw)

kw_doc_freq = {}  # how many stories contain each keyword
for kw_word in all_kw_union:
    count = sum(
        1 for skw in story_kw_sets if any(word_match(kw_word, sw) for sw in skw)
    )
    kw_doc_freq[kw_word] = count

n_stories = len(stories)
kw_idf = {}
for kw_word, df in kw_doc_freq.items():
    kw_idf[kw_word] = math.log(n_stories / max(df, 1)) + 0.1  # +0.1 floor

# Show most/least discriminating keywords
by_idf = sorted(kw_idf.items(), key=lambda x: x[1])
print("\nLeast discriminating keywords: %s" % [(w, "%.2f" % v) for w, v in by_idf[:10]])
print("Most discriminating keywords: %s" % [(w, "%.2f" % v) for w, v in by_idf[-10:]])


def score_cluster_story(cluster_words, cluster_tag_words, story_kw, kw_idf):
    """Score how well a cluster matches a story. Uses IDF weighting."""
    all_cluster = cluster_words | cluster_tag_words
    if not all_cluster or not story_kw:
        return 0.0

    # Count fuzzy matches, weighted by keyword IDF
    total_weight = 0.0
    for cw in all_cluster:
        for sw in story_kw:
            if word_match(cw, sw):
                total_weight += kw_idf.get(sw, 1.0)
                break  # one match per cluster word

    # Normalize by cluster size
    return total_weight / len(all_cluster)


# After all scores computed, apply IDF-like penalty to stories that match too many clusters.
# A story matching 30%+ of clusters is probably too broad -- penalize it so more specific
# stories win the assignment.
def apply_specificity_penalty(clusters, stories, story_kw_sets, kw_idf):
    """Re-score with penalty for overly broad stories."""
    n = len(clusters)

    # Count how many clusters each story is BEST match for (before penalty)
    story_counts = {}
    for c in clusters:
        si = c["assigned_story"]
        story_counts[si] = story_counts.get(si, 0) + 1

    # Stories with >20% of clusters get penalized
    broad_stories = {si for si, cnt in story_counts.items() if cnt > n * 0.20}
    if not broad_stories:
        return False

    print(
        "Broad stories detected (>20%%): %s"
        % [stories[si]["title"][:50] for si in broad_stories]
    )

    # Re-score: for broad stories, halve the score. Then re-assign.
    changed = 0
    for c in clusters:
        c_words = tokenize(c["title"])
        c_tags = extract_tag_words(c["tags"])

        best_idx = 0
        best_score = -1
        for j, skw in enumerate(story_kw_sets):
            sc = score_cluster_story(c_words, c_tags, skw, kw_idf)
            if j in broad_stories:
                sc *= 0.5  # penalize broad stories
            if sc > best_score:
                best_score = sc
                best_idx = j

        if best_idx != c["assigned_story"]:
            changed += 1
        c["assigned_story"] = best_idx
        c["match_score"] = best_score

    print("Re-assigned %d clusters after specificity penalty" % changed)
    return changed > 0


# Assign ALL clusters (not just LLM items)
family_map = {}  # story_index -> [cluster dicts]

for c in clusters:
    c_words = tokenize(c["title"])
    c_tags = extract_tag_words(c["tags"])

    best_idx = 0
    best_score = -1
    for j, skw in enumerate(story_kw_sets):
        sc = score_cluster_story(c_words, c_tags, skw, kw_idf)
        if sc > best_score:
            best_score = sc
            best_idx = j

    c["assigned_story"] = best_idx
    c["match_score"] = best_score

# Apply specificity penalty to prevent black-hole stories
apply_specificity_penalty(clusters, stories, story_kw_sets, kw_idf)

# For giant CTMs: redirect low-confidence clusters to the general commentary family
general_idx = None
if is_giant:
    for j, s in enumerate(stories):
        title_lower = s["title"].lower()
        if "general" in title_lower and (
            "commentary" in title_lower or "updates" in title_lower
        ):
            general_idx = j
            break
    if general_idx is not None:
        # Count current family sizes
        fam_counts = {}
        for c in clusters:
            si = c["assigned_story"]
            fam_counts[si] = fam_counts.get(si, 0) + 1

        redirected = 0
        for c in clusters:
            si = c["assigned_story"]
            if si == general_idx:
                continue
            # Redirect if: low score, OR moderate score but in an oversized family
            if c["match_score"] < 0.35:
                c["assigned_story"] = general_idx
                redirected += 1
            elif c["match_score"] < 0.55 and fam_counts.get(si, 0) > n_total * 0.06:
                c["assigned_story"] = general_idx
                redirected += 1
        print(
            "Redirected %d low-confidence clusters to general commentary" % redirected
        )
    else:
        print("WARNING: no general commentary family found in LLM output")

# Build family map from final assignments
for c in clusters:
    family_map.setdefault(c["assigned_story"], []).append(c)

# Score distribution
scores = [c["match_score"] for c in clusters]
zero = sum(1 for s in scores if s == 0)
low = sum(1 for s in scores if 0 < s < 0.15)
med = sum(1 for s in scores if 0.15 <= s < 0.3)
high = sum(1 for s in scores if s >= 0.3)
print(
    "Score distribution: zero=%d, low(<0.15)=%d, med(0.15-0.3)=%d, high(0.3+)=%d"
    % (zero, low, med, high)
)

# ---------------------------------------------------------------
# RESULTS
# ---------------------------------------------------------------
print("\n========== RESULTS: %d stories ==========\n" % len(family_map))

sorted_stories = sorted(
    family_map.keys(),
    key=lambda k: -sum(c["src"] for c in family_map[k]),
)

total_assigned = 0
for si in sorted_stories:
    fam = family_map[si]
    fam_src = sum(c["src"] for c in fam)
    story = stories[si]
    total_assigned += len(fam)

    print("[%4d clusters, %5d src] %s" % (len(fam), fam_src, story["title"]))
    # Top 3 clusters by source count
    top = sorted(fam, key=lambda c: -c["src"])[:3]
    for c in top:
        print("   %4d src (%.2f) | %s" % (c["src"], c["match_score"], c["title"][:70]))
    # Worst match in family
    worst = min(fam, key=lambda c: c["match_score"])
    if worst["match_score"] < 0.1 and worst not in top:
        print(
            "   WEAK: %d src (%.2f) | %s"
            % (worst["src"], worst["match_score"], worst["title"][:70])
        )
    if len(fam) > 3:
        print("   ... +%d more" % (len(fam) - 3))
    print()

# Empty stories
empty = [i for i in range(len(stories)) if i not in family_map]
if empty:
    print("Stories with no clusters: %d" % len(empty))
    for si in empty:
        print("  - %s" % stories[si]["title"])

print(
    "\nSummary: %d clusters assigned to %d families (of %d stories identified)"
    % (total_assigned, len(family_map), len(stories))
)
print("Zero-score clusters: %d (%.1f%%)" % (zero, 100 * zero / n_total))

conn.close()
