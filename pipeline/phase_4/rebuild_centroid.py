"""
Full centroid rebuild: extract labels -> normalize -> cross-track cluster -> assign CTMs -> generate titles.

Usage:
    python -m pipeline.phase_4.rebuild_centroid --centroid EUROPE-FRANCE --month 2026-03-01
    python -m pipeline.phase_4.rebuild_centroid --centroid EUROPE-FRANCE --month 2026-03-01 --write
    python -m pipeline.phase_4.rebuild_centroid --centroid EUROPE-FRANCE --month 2026-03-01 --write --titles
"""

import argparse
import asyncio
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")

import community as community_louvain
import networkx as nx
import psycopg2

from core.config import HIGH_FREQ_ORGS, config

UBIQUITOUS_RATIO = 0.10  # labels in >10% of titles are ubiquitous for this centroid


def compute_ubiquitous_labels(titles, ratio=UBIQUITOUS_RATIO):
    """Find labels that appear in too many titles to be discriminating.

    Returns a set of label strings (e.g. {"PER:MACRON", "PLC:PARIS"}).
    Dynamic replacement for hardcoded protagonist/home_cities dicts.
    """
    n = len(titles)
    if n < 20:
        return set()
    counts = Counter()
    for t in titles:
        for p in t.get("persons", []):
            counts["PER:" + p.upper()] += 1
        for p in t.get("places", []):
            counts["PLC:" + p.upper()] += 1
        for o in t.get("orgs", []):
            counts["ORG:" + o.upper()] += 1
    threshold = n * ratio
    result = {lbl for lbl, c in counts.items() if c >= threshold}
    if result:
        print(
            "Ubiquitous labels (>%d%%): %s"
            % (
                int(ratio * 100),
                ", ".join(
                    "%s(%d%%)" % (lbl, counts[lbl] * 100 // n) for lbl in sorted(result)
                ),
            )
        )
    return result


# Sector -> track mapping (4-track model, March 2026+)
# Politics, Security, Economy (incl. energy/tech/infrastructure), Society (incl. health)
SECTOR_TO_TRACK = {
    "MILITARY": "geo_security",
    "INTELLIGENCE": "geo_security",
    "SECURITY": "geo_security",
    "DIPLOMACY": "geo_politics",
    "GOVERNANCE": "geo_politics",
    "ECONOMY": "geo_economy",
    "ENERGY_RESOURCES": "geo_economy",
    "TECHNOLOGY": "geo_economy",
    "INFRASTRUCTURE": "geo_economy",
    "HEALTH_ENVIRONMENT": "geo_society",
    "SOCIETY": "geo_society",
    "UNKNOWN": "geo_politics",
}

# Subjects filtered before clustering (low strategic value, noise-heavy)
FILTERED_SUBJECTS = {"MEDIA_PRESS", "DEMOGRAPHICS"}

# Minimum cluster size for geo_society track (higher bar than other tracks)
SOCIETY_MIN_CLUSTER = 10


def is_geo(c):
    return not c.startswith("SYS-") and not c.startswith("NON-STATE-")


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def load_all_titles(conn, centroid_id, month):
    """Load all titles for a centroid+month directly (no title_assignments)."""
    cur = conn.cursor()
    cur.execute(
        """SELECT t.id, t.title_display, t.pubdate_utc, t.centroid_ids,
                  tl.sector, tl.subject, tl.target, tl.domain,
                  tl.persons, tl.orgs, tl.places, tl.named_events,
                  tl.actor, tl.action_class
           FROM titles_v3 t
           LEFT JOIN title_labels tl ON t.id = tl.title_id
           WHERE %s = ANY(t.centroid_ids)
             AND t.processing_status = 'assigned'
             AND t.pubdate_utc >= %s::date
             AND t.pubdate_utc < %s::date + INTERVAL '1 month'
           ORDER BY t.pubdate_utc""",
        (centroid_id, month, month),
    )
    return [
        {
            "id": str(r[0]),
            "title_display": r[1],
            "pubdate_utc": r[2],
            "centroid_ids": r[3] or [],
            "sector": r[4],
            "subject": r[5],
            "target": r[6],
            "domain": r[7],
            "persons": r[8] or [],
            "orgs": r[9] or [],
            "places": r[10] or [],
            "named_events": r[11] or [],
            "actor": r[12] or "",
            "action_class": r[13] or "",
        }
        for r in cur.fetchall()
    ]


def _primary_actor(actor_str):
    """Return the primary actor from a possibly comma-separated actor field."""
    if not actor_str:
        return "UNKNOWN"
    return actor_str.split(",")[0].strip()


def _identity_labels(t, ubiquitous):
    """Build the set of specific identity labels for a title.

    Prefixed to avoid collision: TGT:, PLC:, PER:, ORG:, EVT:
    Excludes: ubiquitous labels (dynamically computed), high-freq orgs, NONE target.
    """
    labels = set()
    tgt = t.get("target") or ""
    if tgt and tgt != "NONE":
        for v in tgt.split(","):
            v = v.strip()
            if v and v != "NONE":
                labels.add("TGT:" + v)
    for p in t.get("places", []):
        lbl = "PLC:" + p.upper()
        if lbl not in ubiquitous:
            labels.add(lbl)
    for p in t.get("persons", []):
        lbl = "PER:" + p.upper()
        if lbl not in ubiquitous:
            labels.add(lbl)
    for o in t.get("orgs", []):
        if o.upper() not in HIGH_FREQ_ORGS:
            labels.add("ORG:" + o.upper())
    for e in t.get("named_events", []):
        labels.add("EVT:" + e)
    return labels


def _louvain_split(indices, titles, sector, subject, ubiquitous, temporal_mode="off"):
    """Louvain community detection on identity-label Jaccard similarity.

    Titles with zero identity labels are merged into the largest community
    within their sector+subject group (they belong to the topic area but
    can't be further discriminated).
    """
    label_sets = {i: _identity_labels(titles[i], ubiquitous) for i in indices}

    has_labels = [i for i in indices if label_sets[i]]
    no_labels = [i for i in indices if not label_sets[i]]

    if not has_labels:
        return [{"sector": sector, "subject": subject, "indices": indices}]

    G = nx.Graph()
    G.add_nodes_from(has_labels)
    for a in range(len(has_labels)):
        for b in range(a + 1, len(has_labels)):
            ia, ib = has_labels[a], has_labels[b]
            la, lb = label_sets[ia], label_sets[ib]
            shared = la & lb
            if shared:
                jaccard = len(shared) / len(la | lb)
                if temporal_mode == "soft":
                    da = titles[ia].get("pubdate_utc")
                    db = titles[ib].get("pubdate_utc")
                    if da and db:
                        days_apart = abs((da - db).days)
                        if days_apart > 2:
                            jaccard *= max(
                                0.3, 1.0 - (days_apart - 2) * TEMPORAL_DECAY_RATE
                            )
                G.add_edge(ia, ib, weight=jaccard)

    partition = community_louvain.best_partition(G, weight="weight")
    communities = defaultdict(list)
    for node, cid in partition.items():
        communities[cid].append(node)

    # Merge zero-label titles into the largest community
    if no_labels and communities:
        largest_cid = max(communities, key=lambda c: len(communities[c]))
        communities[largest_cid].extend(no_labels)

    return [
        {"sector": sector, "subject": subject, "indices": members}
        for members in communities.values()
    ]


# Louvain only runs on groups at or above this size.
# Below threshold: the entire sector+subject group becomes one topic.
LOUVAIN_SPLIT_THRESHOLD = 50

# Anchor keyword thresholds
ANCHOR_MIN_COUNT = 8  # signal must appear in >= 8 titles to be an anchor
ANCHOR_MAX_RATIO = 0.40  # signal must appear in < 40% of group (otherwise too generic)

# Temporal proximity settings
TEMPORAL_WINDOW_DAYS = 5  # hard mode: split clusters spanning > this many days
TEMPORAL_GAP_DAYS = 3  # hard mode: natural gap threshold for split points
TEMPORAL_DECAY_RATE = 0.07  # soft mode: edge weight decay per day beyond 2-day grace


def _find_anchor_keywords(indices, titles, ubiquitous, centroid_id):
    """Find specific, frequent signals that can pre-split a large group.

    An anchor keyword is a signal (person, org, place, named_event, target)
    that appears in >= ANCHOR_MIN_COUNT titles but < ANCHOR_MAX_RATIO of the
    group. These are specific enough to identify a distinct sub-story.

    Excludes: ubiquitous labels (already filtered in _identity_labels) and
    the centroid's own country as a target (TGT:RU for Russia, TGT:FR for France, etc.)

    Returns dict: {anchor_label: [title_indices]}
    """
    label_sets = {i: _identity_labels(titles[i], ubiquitous) for i in indices}

    # Build set of self-target labels to exclude (e.g., TGT:RU for EUROPE-RUSSIA)
    # The centroid country part maps to common target codes
    _CENTROID_TO_TGT = {
        "FRANCE": {"TGT:FR"},
        "RUSSIA": {"TGT:RU"},
        "UK": {"TGT:GB", "TGT:UK"},
        "GERMANY": {"TGT:DE"},
        "USA": {"TGT:US"},
        "CHINA": {"TGT:CN"},
        "UKRAINE": {"TGT:UA"},
        "ISRAEL": {"TGT:IL"},
        "IRAN": {"TGT:IR"},
        "INDIA": {"TGT:IN"},
        "TURKEY": {"TGT:TR"},
    }
    country = centroid_id.split("-", 1)[1] if "-" in centroid_id else centroid_id
    self_targets = _CENTROID_TO_TGT.get(country, set())

    # Count label frequency across the group
    label_counts = Counter()
    for i in indices:
        for lbl in label_sets[i]:
            # Exclude self-targets (ubiquitous labels already filtered)
            if lbl in self_targets:
                continue
            label_counts[lbl] += 1

    group_size = len(indices)
    anchors = {}
    for label, count in label_counts.most_common():
        if count < ANCHOR_MIN_COUNT:
            break
        if count >= group_size * ANCHOR_MAX_RATIO:
            continue  # too generic (e.g., PER:PUTIN in Russia)
        # This label is specific enough to be an anchor
        members = [i for i in indices if label in label_sets[i]]
        anchors[label] = members

    return anchors


def _anchor_split(indices, titles, sector, subject, ubiquitous, centroid_id):
    """Pre-split a large group by anchor keywords before Louvain.

    1. Find anchor keywords (specific, frequent signals)
    2. Assign each title to its best-matching anchor (most shared anchors)
    3. Titles matching no anchor go to a "remainder" group
    4. Each anchor group and the remainder get Louvain or stay as-is
    """
    anchors = _find_anchor_keywords(indices, titles, ubiquitous, centroid_id)

    if not anchors:
        # No anchor keywords found -- fall through to Louvain
        return None

    label_sets = {i: _identity_labels(titles[i], ubiquitous) for i in indices}

    # Assign each title to its best anchor (most shared anchor labels)
    anchor_labels = set(anchors.keys())
    assigned = {}  # title_index -> anchor_label
    for i in indices:
        title_anchors = label_sets[i] & anchor_labels
        if not title_anchors:
            continue
        # Pick the anchor that has the most titles (prefer larger groups)
        best = max(title_anchors, key=lambda a: len(anchors[a]))
        assigned[i] = best

    # Group by assigned anchor
    anchor_groups = defaultdict(list)
    remainder = []
    for i in indices:
        if i in assigned:
            anchor_groups[assigned[i]].append(i)
        else:
            remainder.append(i)

    # Only use anchor split if it actually creates meaningful groups
    real_groups = [g for g in anchor_groups.values() if len(g) >= ANCHOR_MIN_COUNT]
    if len(real_groups) < 2:
        return None  # anchor split didn't help

    results = []
    for anchor_label, members in anchor_groups.items():
        if len(members) < ANCHOR_MIN_COUNT:
            remainder.extend(members)
            continue
        results.append({"sector": sector, "subject": subject, "indices": members})

    # Remainder becomes its own group (may get Louvain-split later)
    if remainder:
        results.append({"sector": sector, "subject": subject, "indices": remainder})

    return results


def _actor_country(actor_str):
    """Extract country code from a prefixed actor like UA_ARMED_FORCES -> UA."""
    if not actor_str or "_" not in actor_str:
        return None
    prefix = actor_str.split("_")[0]
    if len(prefix) == 2 and prefix.isalpha():
        return prefix
    return None


def _primary_target(title, home_iso_codes):
    """Extract the directional story axis for a title.

    Encodes WHO does WHAT to WHOM as a directional axis:
    - RU_ARMED_FORCES -> UA = ">UA" (home actor targets Ukraine)
    - UA_ARMED_FORCES -> RU = "<UA" (foreign actor targets home)
    - CORPORATION -> IR = ">IR" (home actor targets Iran)
    - IR_ARMED_FORCES -> IL = ">IR" (foreign-on-foreign, use actor)

    The > and < prefixes ensure "Russia strikes Ukraine" and "Ukraine
    strikes Russia" end up in different groups even though both involve UA.
    """
    tgt = title.get("target") or ""
    actor = title.get("actor") or ""
    actor_country = _actor_country(actor)

    # Find first foreign target
    foreign_target = None
    if tgt and tgt != "NONE":
        for v in tgt.split(","):
            v = v.strip()
            if v and v != "NONE" and v not in home_iso_codes:
                foreign_target = v
                break

    actor_is_home = not actor_country or actor_country in home_iso_codes

    if foreign_target:
        if actor_is_home:
            return ">" + foreign_target  # home attacks foreign
        else:
            # Foreign actor attacks foreign target -- group by actor
            return ">" + (actor_country or foreign_target)

    # No foreign target -- check if foreign actor targets home
    if actor_country and actor_country not in home_iso_codes:
        return "<" + actor_country  # foreign attacks home

    return "DOMESTIC"


# Minimum titles for a target group to become its own cluster axis
TARGET_SPLIT_MIN = 3


def _target_split(indices, titles, sector, subject, home_iso_codes):
    """Split a sector+subject group by primary target.

    Titles targeting the same foreign country form a sub-group (story axis).
    Small target groups (< TARGET_SPLIT_MIN) merge into DOMESTIC remainder.
    """
    target_groups = defaultdict(list)
    for i in indices:
        tgt = _primary_target(titles[i], home_iso_codes)
        target_groups[tgt].append(i)

    # Only split if there are 2+ meaningful target groups
    real_groups = {
        t: idx for t, idx in target_groups.items() if len(idx) >= TARGET_SPLIT_MIN
    }
    if len(real_groups) < 2:
        return None  # no meaningful split

    # Absorb small target groups into DOMESTIC
    domestic = list(target_groups.get("DOMESTIC", []))
    for tgt, idx in target_groups.items():
        if tgt != "DOMESTIC" and tgt not in real_groups:
            domestic.extend(idx)

    result = []
    for tgt, idx in real_groups.items():
        if tgt == "DOMESTIC":
            continue
        result.append({"sector": sector, "subject": subject, "indices": idx})

    if domestic:
        result.append({"sector": sector, "subject": subject, "indices": domestic})

    return result if len(result) >= 2 else None


def _process_group(
    indices,
    titles,
    sector,
    subject,
    ubiquitous,
    centroid_id,
    temporal_mode="off",
):
    """Process a single group through anchor split -> Louvain pipeline."""
    # Try anchor keyword split first
    anchor_groups = _anchor_split(
        indices, titles, sector, subject, ubiquitous, centroid_id
    )

    results = []
    sub_groups = (
        anchor_groups
        if anchor_groups
        else [{"sector": sector, "subject": subject, "indices": indices}]
    )

    for group in sub_groups:
        if len(group["indices"]) >= LOUVAIN_SPLIT_THRESHOLD:
            subclusters = _louvain_split(
                group["indices"],
                titles,
                sector,
                subject,
                ubiquitous,
                temporal_mode,
            )
            results.extend(subclusters)
        elif len(group["indices"]) > 3:
            results.append(group)
        else:
            results.append(group)

    return results


def cluster_topdown(titles, centroid_id, temporal_mode="off", ubiquitous=None):
    """4-level clustering:
      L1: sector + subject  (domain grouping)
      L1.5: primary target split  (separate story axes by foreign target)
      L2: anchor keyword split  (specific frequent signals)
      L3: Louvain on identity labels  (community detection)

    Small groups stay as a single topic. Target split separates e.g.
    "Israel strikes Iran" from "Russia strikes Ukraine" within MILITARY/AERIAL.
    """
    if ubiquitous is None:
        ubiquitous = compute_ubiquitous_labels(titles)

    # Derive home ISO codes for target split
    _CENTROID_TO_ISO = {
        "FRANCE": {"FR"},
        "RUSSIA": {"RU"},
        "UK": {"GB", "UK"},
        "GERMANY": {"DE"},
        "USA": {"US"},
        "CHINA": {"CN"},
        "UKRAINE": {"UA"},
        "ISRAEL": {"IL"},
        "IRAN": {"IR"},
        "INDIA": {"IN"},
        "TURKEY": {"TR"},
        "BALTIC": {"EE", "LV", "LT"},
    }
    country = centroid_id.split("-", 1)[1] if "-" in centroid_id else centroid_id
    home_iso_codes = _CENTROID_TO_ISO.get(country, set())

    # Level 1: group by (sector, subject)
    l1_groups = defaultdict(list)
    for i, t in enumerate(titles):
        l1_groups[(t["sector"] or "UNKNOWN", t["subject"])].append(i)

    all_clusters = []

    for (sector, subject), l1_idx in l1_groups.items():
        if len(l1_idx) <= 3:
            all_clusters.append(
                {"sector": sector, "subject": subject, "indices": l1_idx}
            )
            continue

        if len(l1_idx) < LOUVAIN_SPLIT_THRESHOLD:
            # Below threshold: keep as one topic
            all_clusters.append(
                {"sector": sector, "subject": subject, "indices": l1_idx}
            )
            continue

        # L1.5: split by primary target (story axis)
        target_groups = _target_split(l1_idx, titles, sector, subject, home_iso_codes)

        if target_groups:
            for tg in target_groups:
                if len(tg["indices"]) >= LOUVAIN_SPLIT_THRESHOLD:
                    all_clusters.extend(
                        _process_group(
                            tg["indices"],
                            titles,
                            sector,
                            subject,
                            ubiquitous,
                            centroid_id,
                            temporal_mode,
                        )
                    )
                elif len(tg["indices"]) > 3:
                    all_clusters.append(tg)
                else:
                    all_clusters.append(tg)
        else:
            # No target split -- process the whole group
            all_clusters.extend(
                _process_group(
                    l1_idx,
                    titles,
                    sector,
                    subject,
                    ubiquitous,
                    centroid_id,
                    temporal_mode,
                )
            )

    return all_clusters


def _tokenize(text):
    """Tokenize headline into content words (no hardcoded stop words)."""
    words = set()
    for w in text.lower().split():
        w = w.strip(".,;:!?\"'()[]{}|-")
        if w and len(w) > 2:
            words.add(w)
    return words


def _corpus_content_words(titles, indices, min_doc_ratio=0.02, max_doc_ratio=0.6):
    """Extract discriminating content words from a title corpus.

    Filters by document frequency: words appearing in <2% or >60% of titles
    are excluded (too rare = noise, too common = stop-word equivalent).
    No hardcoded vocabulary -- works across any language.
    """
    all_words = [_tokenize(titles[i].get("title_display", "")) for i in indices]
    doc_freq = Counter()
    for ws in all_words:
        for w in ws:
            doc_freq[w] += 1
    n = len(indices)
    min_count = max(2, int(n * min_doc_ratio))
    max_count = int(n * max_doc_ratio)
    valid = {w for w, c in doc_freq.items() if min_count <= c <= max_count}
    return valid, doc_freq, all_words


# Minimum core features shared by >= 40% of top 10 to consider cluster coherent
COHERENCE_MIN_CORE = 3
COHERENCE_TOP_N = 10
COHERENCE_FEATURE_RATIO = 0.4  # feature must appear in >= 40% of top titles


def _title_features(title, labels, valid_words=None):
    """Build combined feature set: raw content words + normalized labels.

    If valid_words is provided, only include words in that set (corpus-filtered).
    Otherwise include all words > 2 chars (for small clusters where corpus stats
    aren't meaningful).
    """
    features = set()
    for w in _tokenize(title.get("title_display", "")):
        if valid_words is None or w in valid_words:
            features.add("W:" + w)
    features.update(labels)
    return features


def compute_coherence(cluster, titles, ubiquitous):
    """Score cluster coherence and select core titles.

    Returns (core_indices, coherence_score, all_scores).
    - core_indices: top N title indices by centrality score
    - coherence_score: number of core features (shared by >= 40% of top N)
    - all_scores: centrality score per title index (for stats)
    """
    indices = cluster["indices"]
    # All clusters go through coherence check regardless of size

    # Build feature sets: corpus-filtered words + labels
    valid_words, _, _ = _corpus_content_words(titles, indices)
    label_sets = {i: _identity_labels(titles[i], ubiquitous) for i in indices}
    feature_sets = {
        i: _title_features(titles[i], label_sets[i], valid_words) for i in indices
    }

    # Count corpus frequency of each feature
    corpus_freq = Counter()
    for i in indices:
        for f in feature_sets[i]:
            corpus_freq[f] += 1

    n = len(indices)

    # Feature weight: downweight features that appear in too many titles.
    # A feature in 80%+ of titles is near-ubiquitous (like "russia" for Russia)
    # and gets half weight. Features in 40-80% get full weight (discriminating).
    # Features in < 5% are noise (too rare to indicate coherence).
    def feature_weight(feat):
        ratio = corpus_freq[feat] / n
        if ratio >= 0.8:
            return 0.5  # ubiquitous: still counts but less
        if ratio < 0.05:
            return 0.5  # very rare: less reliable
        return 1.0

    # Score each title: weighted sum of corpus freq, normalized by size
    scores = {}
    for i in indices:
        fs = feature_sets[i]
        if not fs:
            scores[i] = 0
            continue
        scores[i] = sum(corpus_freq[f] * feature_weight(f) for f in fs) / len(fs)

    # Select top N by centrality
    ranked = sorted(indices, key=lambda i: -scores[i])
    core = ranked[:COHERENCE_TOP_N]

    # Count core features: features shared by >= 40% of top N titles.
    # Ubiquitous features (in 80%+ of ALL cluster titles) don't count as
    # evidence of coherence -- they appear in every cluster for this centroid.
    core_feature_freq = Counter()
    for i in core:
        for f in feature_sets[i]:
            core_feature_freq[f] += 1

    threshold = max(2, int(len(core) * COHERENCE_FEATURE_RATIO))
    core_features = [
        f
        for f, c in core_feature_freq.items()
        if c >= threshold and corpus_freq[f] / n < 0.8
    ]

    # Entity concentration check for borderline clusters (core_features 3-4).
    # If the cluster barely passes on vocabulary alone, require at least one
    # identity label (PER/ORG/PLC/EVT) in >= 30% of top titles.
    # Strong clusters (5+ core features) pass regardless -- they have enough
    # shared vocabulary to be coherent even without a named entity anchor.
    if len(core_features) <= 4:
        entity_prefixes = ("PER:", "ORG:", "PLC:", "EVT:")
        has_anchor_entity = any(
            f.startswith(entity_prefixes) and c >= max(2, int(len(core) * 0.3))
            for f, c in core_feature_freq.items()
        )
        if not has_anchor_entity:
            return core, 0, scores  # borderline + no entity anchor = incoherent

    return core, len(core_features), scores


def filter_incoherent_clusters(clusters, titles, ubiquitous):
    """Apply coherence gate: dissolve clusters with no coherent core.

    Returns (coherent_clusters, dissolved_indices, stats).
    """
    coherent = []
    dissolved = []
    stats = {"coherent": 0, "dissolved": 0, "dissolved_titles": 0}

    for cl in clusters:
        if len(cl["indices"]) <= 3:
            # Tiny clusters: keep as-is (they become catchall anyway)
            coherent.append(cl)
            continue

        core, score, _ = compute_coherence(cl, titles, ubiquitous)

        if score >= COHERENCE_MIN_CORE:
            coherent.append(cl)
            stats["coherent"] += 1
        else:
            dissolved.extend(cl["indices"])
            stats["dissolved"] += 1
            stats["dissolved_titles"] += len(cl["indices"])

    # Dissolved titles become individual catchall entries
    for i in dissolved:
        t = titles[i]
        coherent.append(
            {
                "sector": t.get("sector") or "UNKNOWN",
                "subject": t.get("subject"),
                "indices": [i],
            }
        )

    return coherent, stats


def _temporal_split_clusters(clusters, titles, max_spread=TEMPORAL_WINDOW_DAYS):
    """Hard temporal: split clusters whose titles span > max_spread days.

    Splits at natural temporal gaps (>= TEMPORAL_GAP_DAYS between consecutive
    titles). Falls back to fixed windows if no natural gaps exist.
    """
    result = []
    stats = {"checked": 0, "split": 0, "produced": 0}

    for cl in clusters:
        indices = cl["indices"]
        if len(indices) <= 5:
            result.append(cl)
            continue

        dated = [
            (i, titles[i]["pubdate_utc"])
            for i in indices
            if titles[i].get("pubdate_utc")
        ]
        if len(dated) < 2:
            result.append(cl)
            continue

        dated.sort(key=lambda x: x[1])
        spread = (dated[-1][1] - dated[0][1]).days
        stats["checked"] += 1

        if spread <= max_spread:
            result.append(cl)
            continue

        # Find natural gaps
        split_points = []
        for k in range(1, len(dated)):
            gap = (dated[k][1] - dated[k - 1][1]).days
            if gap >= TEMPORAL_GAP_DAYS:
                split_points.append(k)

        if split_points:
            sub_clusters = []
            prev = 0
            for sp in split_points:
                sub_clusters.append([i for i, _ in dated[prev:sp]])
                prev = sp
            sub_clusters.append([i for i, _ in dated[prev:]])
        else:
            # No natural gaps -- fixed windows
            base = dated[0][1]
            buckets = defaultdict(list)
            for i, d in dated:
                bucket = (d - base).days // max_spread
                buckets[bucket].append(i)
            sub_clusters = list(buckets.values())

        # Undated titles go to largest sub-cluster
        no_date = [i for i in indices if not titles[i].get("pubdate_utc")]
        if no_date and sub_clusters:
            largest = max(range(len(sub_clusters)), key=lambda k: len(sub_clusters[k]))
            sub_clusters[largest].extend(no_date)

        # Only keep if it produces 2+ meaningful groups
        meaningful = [sc for sc in sub_clusters if len(sc) >= 2]
        tiny = [i for sc in sub_clusters if len(sc) < 2 for i in sc]

        if len(meaningful) < 2:
            result.append(cl)
            continue

        stats["split"] += 1
        for sc in meaningful:
            result.append(
                {"sector": cl["sector"], "subject": cl["subject"], "indices": sc}
            )
            stats["produced"] += 1
        for i in tiny:
            result.append(
                {"sector": cl["sector"], "subject": cl["subject"], "indices": [i]}
            )

    return result, stats


def _print_temporal_stats(clusters, titles):
    """Print temporal spread distribution for emerged clusters."""
    buckets = {"0-2d": 0, "3-5d": 0, "6-10d": 0, "11+d": 0}
    spreads = []
    for cl in clusters:
        dates = [
            titles[i]["pubdate_utc"]
            for i in cl["indices"]
            if titles[i].get("pubdate_utc")
        ]
        if len(dates) < 2:
            buckets["0-2d"] += 1
            spreads.append(0)
            continue
        spread = (max(dates) - min(dates)).days
        spreads.append(spread)
        if spread <= 2:
            buckets["0-2d"] += 1
        elif spread <= 5:
            buckets["3-5d"] += 1
        elif spread <= 10:
            buckets["6-10d"] += 1
        else:
            buckets["11+d"] += 1

    print("\nTemporal spread (emerged clusters):")
    for label, count in buckets.items():
        pct = count * 100 // len(spreads) if spreads else 0
        print("  %s: %d (%d%%)" % (label, count, pct))
    if spreads:
        spreads.sort()
        print("  Median: %d days" % spreads[len(spreads) // 2])


# Cluster merge thresholds
CLUSTER_MERGE_JACCARD = 0.20  # shared / union of identity labels
CLUSTER_MERGE_DATE_DAYS = 3  # date ranges must overlap within this tolerance
CLUSTER_MERGE_MIN_SHARED = (
    3  # at least N shared identity labels (excl. ubiquitous labels + targets)
)


def _merge_matching_clusters(clusters, titles, ubiquitous):
    """Merge clusters that represent the same event.

    Two clusters match if:
    - Same sector (subject may differ -- NUCLEAR vs DEFENSE_POLICY for same speech)
    - Date ranges overlap within CLUSTER_MERGE_DATE_DAYS tolerance
    - >= CLUSTER_MERGE_MIN_SHARED identity labels in common (excl. ubiquitous)
    - Identity label Jaccard >= CLUSTER_MERGE_JACCARD
    """
    mergeable = [c for c in clusters if len(c["indices"]) >= 2]
    singles = [c for c in clusters if len(c["indices"]) < 2]

    if len(mergeable) < 2:
        return clusters, {"merges": 0, "details": []}

    # Compute profile per cluster: sector, date range, identity labels
    profiles = []
    for cl in mergeable:
        labels = set()
        dates = []
        for i in cl["indices"]:
            labels.update(_identity_labels(titles[i], ubiquitous))
            if titles[i].get("pubdate_utc"):
                dates.append(titles[i]["pubdate_utc"])
        profiles.append(
            {
                "sector": cl["sector"],
                "labels": labels,
                "min_date": min(dates) if dates else None,
                "max_date": max(dates) if dates else None,
            }
        )

    # Find ubiquitous targets per sector (appear in >25% of clusters)
    # These are too generic for merge matching (e.g., TGT:IR for France during Iran war)
    sector_label_freq = defaultdict(lambda: defaultdict(int))
    sector_count = defaultdict(int)
    for p in profiles:
        sector_count[p["sector"]] += 1
        for lbl in p["labels"]:
            if lbl.startswith("TGT:"):
                sector_label_freq[p["sector"]][lbl] += 1

    ubiquitous_targets = set()
    for sector, freqs in sector_label_freq.items():
        n = sector_count[sector]
        for lbl, count in freqs.items():
            if n >= 4 and count >= n * 0.25:
                ubiquitous_targets.add((sector, lbl))

    if ubiquitous_targets:
        print(
            "Merge: excluding ubiquitous targets: %s"
            % ", ".join(
                "%s(%s)" % (lbl, sec) for sec, lbl in sorted(ubiquitous_targets)
            )
        )

    # Remove ubiquitous targets from profiles
    for p in profiles:
        p["labels"] -= {lbl for sec, lbl in ubiquitous_targets if sec == p["sector"]}

    # Union-find for merging
    parent = list(range(len(mergeable)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    details = []
    for i in range(len(mergeable)):
        for j in range(i + 1, len(mergeable)):
            ri, rj = find(i), find(j)
            if ri == rj:
                continue

            pi, pj = profiles[ri], profiles[rj]

            if pi["sector"] != pj["sector"]:
                continue

            # Date overlap check
            if pi["min_date"] and pj["min_date"] and pi["max_date"] and pj["max_date"]:
                gap = max(
                    (pj["min_date"] - pi["max_date"]).days,
                    (pi["min_date"] - pj["max_date"]).days,
                )
                if gap > CLUSTER_MERGE_DATE_DAYS:
                    continue

            shared = pi["labels"] & pj["labels"]
            if len(shared) < CLUSTER_MERGE_MIN_SHARED:
                continue

            union = pi["labels"] | pj["labels"]
            jaccard = len(shared) / len(union) if union else 0
            if jaccard < CLUSTER_MERGE_JACCARD:
                continue

            # Merge j into i
            parent[rj] = ri
            pi["labels"] = union
            if pj["min_date"] and (
                not pi["min_date"] or pj["min_date"] < pi["min_date"]
            ):
                pi["min_date"] = pj["min_date"]
            if pj["max_date"] and (
                not pi["max_date"] or pj["max_date"] > pi["max_date"]
            ):
                pi["max_date"] = pj["max_date"]
            top_shared = sorted(shared)[:4]
            details.append(
                "  [%d]+[%d] %s/%s shared=%d: %s"
                % (
                    len(mergeable[ri]["indices"]),
                    len(mergeable[rj]["indices"]),
                    pi["sector"],
                    mergeable[ri]["subject"] or "?",
                    len(shared),
                    ", ".join(top_shared),
                )
            )

    # Rebuild merged clusters
    groups = defaultdict(list)
    for i in range(len(mergeable)):
        groups[find(i)].extend(mergeable[i]["indices"])

    result = []
    for root, indices in groups.items():
        result.append(
            {
                "sector": mergeable[root]["sector"],
                "subject": mergeable[root]["subject"],
                "indices": indices,
            }
        )
    result.extend(singles)

    merge_count = len(mergeable) - len(groups)
    return result, {"merges": merge_count, "details": details}


# ---------------------------------------------------------------------------
# LLM-assisted topic merge (post mechanical merge, pre DB write)
# ---------------------------------------------------------------------------

LLM_CANDIDATE_MERGE_PROMPT = """\
You receive candidate pairs of topic clusters that MAY describe the same story.
Each pair shows two clusters with their sector/subject, signals, date range, and a sample headline.

For each pair, decide: MERGE (same story) or SKIP (different stories).

Rules:
- MERGE if they describe the same event, announcement, or policy (even across different subjects)
- Different locations = different stories (Hormuz vs Mediterranean, Iraq vs Congo)
- Different actors/targets = likely different stories unless clearly the same incident
- DO NOT merge topics that merely share a theme or sector
- DO NOT merge if the only link is the country name or its leader

Return JSON: {"merge": [1, 2, 5], "skip": [3, 4]}
- Numbers = pair IDs that should merge / should not merge
ONLY return the JSON."""


def _build_cluster_profile(cluster, titles, ubiquitous):
    """Build a compact signal profile for a cluster (for LLM merge input)."""
    labels = Counter()
    dates = []
    for i in cluster["indices"]:
        t = titles[i]
        for p in t.get("persons", []):
            lbl = "PER:" + p.upper()
            if lbl not in ubiquitous:
                labels[lbl] += 1
        for o in t.get("orgs", []):
            if o.upper() not in HIGH_FREQ_ORGS:
                labels["ORG:" + o.upper()] += 1
        for pl in t.get("places", []):
            lbl = "PLC:" + pl.upper()
            if lbl not in ubiquitous:
                labels[lbl] += 1
        for ne in t.get("named_events", []):
            labels["EVT:" + ne] += 1
        tgt = t.get("target") or ""
        if tgt and tgt != "NONE":
            for v in tgt.split(","):
                v = v.strip()
                if v and v != "NONE":
                    labels["TGT:" + v] += 1
        if t.get("pubdate_utc"):
            dates.append(t["pubdate_utc"])

    # Top signals by frequency (most distinctive)
    top = [lbl for lbl, _ in labels.most_common(6)]

    # Pick a representative headline (shortest English-looking title from cluster)
    sample = ""
    for i in cluster["indices"]:
        t = titles[i].get("title_display") or ""
        if t and all(ord(c) < 256 for c in t[:20]):
            if not sample or len(t) < len(sample):
                sample = t
    if not sample:
        sample = titles[cluster["indices"][0]].get("title_display", "")
    sample = sample[:90]

    return {
        "sector": cluster["sector"],
        "subject": cluster.get("subject") or "?",
        "n": len(cluster["indices"]),
        "signals": top,
        "labels": labels,
        "sample": sample,
        "min_date": min(dates) if dates else None,
        "max_date": max(dates) if dates else None,
    }


def _find_merge_candidates(profiles, track_clusters):
    """Find candidate pairs for LLM merge using signal overlap.

    Returns list of (idx_a, idx_b, shared_signals) tuples.
    """
    candidates = []
    for i in range(len(profiles)):
        for j in range(i + 1, len(profiles)):
            pi, pj = profiles[i], profiles[j]

            # Date overlap check: skip if no temporal overlap (7-day buffer)
            if pi["min_date"] and pj["min_date"] and pi["max_date"] and pj["max_date"]:
                from datetime import timedelta

                buffer = timedelta(days=7)
                if pi["max_date"] + buffer < pj["min_date"]:
                    continue
                if pj["max_date"] + buffer < pi["min_date"]:
                    continue

            # Signal overlap: Jaccard on label keys (ignoring counts)
            keys_i = set(pi["labels"].keys())
            keys_j = set(pj["labels"].keys())
            shared = keys_i & keys_j
            union = keys_i | keys_j
            if not union or len(shared) < 2:
                continue
            # Require strong Jaccard on non-target labels AND a location/event anchor
            # TGT labels are too generic (country codes overlap across unrelated stories)
            nontgt_i = {k for k in keys_i if not k.startswith("TGT:")}
            nontgt_j = {k for k in keys_j if not k.startswith("TGT:")}
            nontgt_shared = nontgt_i & nontgt_j
            nontgt_union = nontgt_i | nontgt_j
            if not nontgt_union or not nontgt_shared:
                continue
            nontgt_jaccard = len(nontgt_shared) / len(nontgt_union)

            place_event_shared = [
                s for s in nontgt_shared if s.startswith(("PLC:", "EVT:"))
            ]
            person_shared = [s for s in nontgt_shared if s.startswith("PER:")]
            same_sector = pi["sector"] == pj["sector"]
            same_subject = (
                same_sector and pi["subject"] == pj["subject"] and pi["subject"] != "?"
            )

            # Cross-sector: require 2+ shared places/events (strong location anchor)
            # Same sector different subject: require 1+ shared place/event
            # Same subject: shared person is enough
            if same_subject:
                has_anchor = place_event_shared or len(person_shared) >= 1
            elif same_sector:
                has_anchor = len(place_event_shared) >= 1
            else:
                has_anchor = len(place_event_shared) >= 2

            if nontgt_jaccard >= 0.20 and has_anchor:
                candidates.append((i, j, sorted(nontgt_shared)[:5]))

    return candidates


def _format_candidate_pair(pair_id, pi, pj, shared):
    """Format a candidate pair for LLM input."""

    def fmt(p):
        sig_str = ", ".join(p["signals"]) if p["signals"] else "none"
        date_str = ""
        if p["min_date"] and p["max_date"]:
            d0 = (
                p["min_date"].strftime("%b %d")
                if hasattr(p["min_date"], "strftime")
                else str(p["min_date"])[:10]
            )
            d1 = (
                p["max_date"].strftime("%b %d")
                if hasattr(p["max_date"], "strftime")
                else str(p["max_date"])[:10]
            )
            date_str = " %s-%s" % (d0, d1)
        return '[%d titles] %s/%s | %s%s\n   "%s"' % (
            p["n"],
            p["sector"],
            p["subject"],
            sig_str,
            date_str,
            p["sample"],
        )

    shared_str = ", ".join(shared) if shared else "none"
    return "Pair %d (shared: %s):\n  A: %s\n  B: %s" % (
        pair_id,
        shared_str,
        fmt(pi),
        fmt(pj),
    )


async def _llm_merge_clusters(clusters, titles, ubiquitous):
    """LLM-assisted merge via candidate pairs.

    1. Build signal profiles for all emerged clusters per track
    2. Pre-compute candidate pairs (shared signals / date overlap)
    3. Send only candidates to LLM for yes/no confirmation
    4. Apply confirmed merges in memory
    """
    from core.llm_utils import extract_json

    emerged = [c for c in clusters if len(c["indices"]) >= 2]
    singles = [c for c in clusters if len(c["indices"]) < 2]

    if len(emerged) < 2:
        return clusters, {"llm_merges": 0, "details": []}

    by_track = defaultdict(list)
    for c in emerged:
        track = SECTOR_TO_TRACK.get(c["sector"], "geo_politics")
        by_track[track].append(c)

    all_merged = []
    total_merges = 0
    details = []

    for track, track_clusters in by_track.items():
        if len(track_clusters) < 2:
            all_merged.extend(track_clusters)
            continue

        # Build profiles
        profiles = [
            _build_cluster_profile(c, titles, ubiquitous) for c in track_clusters
        ]

        # Find candidate pairs
        candidates = _find_merge_candidates(profiles, track_clusters)
        if not candidates:
            print("  LLM merge for %s: no candidates" % track)
            all_merged.extend(track_clusters)
            continue

        print(
            "  LLM merge for %s (%d clusters, %d candidates)..."
            % (track, len(track_clusters), len(candidates))
        )

        # Format candidate pairs for LLM
        lines = []
        for pair_id, (i, j, shared) in enumerate(candidates, 1):
            lines.append(
                _format_candidate_pair(pair_id, profiles[i], profiles[j], shared)
            )

        pairs_text = "\n\n".join(lines)

        headers = {
            "Authorization": "Bearer %s" % config.deepseek_api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "model": config.llm_model,
            "messages": [
                {"role": "system", "content": LLM_CANDIDATE_MERGE_PROMPT},
                {"role": "user", "content": pairs_text},
            ],
            "temperature": 0.1,
            "max_tokens": 500,
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "%s/chat/completions" % config.deepseek_api_url,
                    headers=headers,
                    json=payload,
                )
                if resp.status_code != 200:
                    print("    LLM error: HTTP %d" % resp.status_code)
                    all_merged.extend(track_clusters)
                    continue

            raw = resp.json()["choices"][0]["message"]["content"]
            result = extract_json(raw)
        except Exception as e:
            print("    LLM error: %s" % e)
            all_merged.extend(track_clusters)
            continue

        if not result or "merge" not in result:
            print("    LLM: could not parse response")
            all_merged.extend(track_clusters)
            continue

        # Apply confirmed pairs directly (no transitive chaining)
        # Each cluster can only be absorbed once; larger cluster wins as anchor
        absorbed = set()  # clusters already consumed
        groups = defaultdict(list)  # anchor_idx -> [absorbed indices]

        for pair_id in sorted(result["merge"]):
            if 0 < pair_id <= len(candidates):
                ci, cj, _ = candidates[pair_id - 1]
                if ci in absorbed or cj in absorbed:
                    continue
                # Larger = anchor
                if len(track_clusters[ci]["indices"]) >= len(
                    track_clusters[cj]["indices"]
                ):
                    anchor, other = ci, cj
                else:
                    anchor, other = cj, ci
                if anchor not in absorbed:
                    groups[anchor].append(other)
                    absorbed.add(other)

        merged_indices = set()
        for anchor_idx, absorbed_list in groups.items():
            anchor = track_clusters[anchor_idx]
            merged_titles = []
            for idx in absorbed_list:
                other = track_clusters[idx]
                anchor["indices"].extend(other["indices"])
                merged_indices.add(idx)
                total_merges += 1
                merged_titles.append(
                    "[%d] %s/%s"
                    % (
                        len(other["indices"]),
                        other["sector"],
                        other.get("subject", "?"),
                    )
                )

            detail = "    [%d] %s/%s <- %s" % (
                len(anchor["indices"]),
                anchor["sector"],
                anchor.get("subject", "?"),
                " + ".join(merged_titles),
            )
            details.append(detail)
            print(detail)

        for i, c in enumerate(track_clusters):
            if i not in merged_indices:
                all_merged.append(c)

    all_merged.extend(singles)
    return all_merged, {"llm_merges": total_merges, "details": details}


def assign_track(cluster, titles):
    """Assign a cluster to its best-fit track based on sector."""
    # Use sector of the cluster (not domain)
    return SECTOR_TO_TRACK.get(cluster["sector"], "geo_politics")


def tag_geo(cluster_indices, titles, centroid_id):
    """Tag a cluster as domestic or bilateral.

    Requires the top foreign centroid to appear in >= 10% of titles,
    otherwise noise (e.g. 2/119) doesn't flip a domestic cluster to bilateral.
    """
    foreign_counts = Counter()
    for i in cluster_indices:
        for c in titles[i]["centroid_ids"]:
            if c != centroid_id and is_geo(c):
                foreign_counts[c] += 1

    if not foreign_counts:
        return "domestic", None

    top_centroid, top_count = foreign_counts.most_common(1)[0]
    if top_count < len(cluster_indices) * 0.5:
        return "domestic", None
    return "bilateral", top_centroid


def rebuild(
    centroid_id,
    month,
    write=False,
    generate_titles=False,
    temporal_mode="off",
    only_track=None,
):
    conn = get_connection()
    cur = conn.cursor()

    # Load CTMs
    cur.execute(
        "SELECT id, track FROM ctm WHERE centroid_id = %s AND month = %s",
        (centroid_id, month),
    )
    ctm_map = {str(r[0]): r[1] for r in cur.fetchall()}
    track_to_ctm = {}
    for ctm_id, track in ctm_map.items():
        track_to_ctm[track] = ctm_id

    print("Centroid: %s, Month: %s" % (centroid_id, month))
    print("CTMs: %d" % len(ctm_map))
    for ctm_id, track in ctm_map.items():
        print("  %s %s" % (ctm_id[:8], track))

    # Load all titles for centroid+month (independent of CTM/title_assignments)
    titles = load_all_titles(conn, centroid_id, month)
    print("\nTotal titles: %d" % len(titles))

    # Check sector coverage
    with_sector = sum(1 for t in titles if t["sector"])
    print(
        "With sector: %d/%d (%d%%)"
        % (with_sector, len(titles), with_sector * 100 // len(titles) if titles else 0)
    )

    if with_sector < len(titles) * 0.8:
        print("\nWARNING: <80%% sector coverage. Run extract_concurrent first:")
        print(
            "  python -m pipeline.phase_4.extract_concurrent --centroid %s --month %s"
            % (centroid_id, month)
        )
        if not write:
            print("Continuing with dry run anyway...")

    # Filter out non-strategic titles + low-value subjects
    before = len(titles)
    titles = [
        t
        for t in titles
        if t["sector"] != "NON_STRATEGIC" and t["subject"] not in FILTERED_SUBJECTS
    ]
    filtered = before - len(titles)
    if filtered:
        print("Filtered %d non-strategic titles (%d remain)" % (filtered, len(titles)))

    # Signal normalization now happens at Phase 3.1 extraction time

    # Topic groups
    groups = defaultdict(list)
    for i, t in enumerate(titles):
        key = (t["sector"] or "UNKNOWN", t["subject"])
        groups[key].append(i)

    print("\nTopic groups (5+):")
    for key in sorted(groups, key=lambda k: -len(groups[k])):
        if len(groups[key]) >= 5:
            track = SECTOR_TO_TRACK.get(key[0], "geo_politics")
            print(
                "  %s/%s: %d -> %s"
                % (key[0], key[1] or "NULL", len(groups[key]), track)
            )

    # Compute ubiquitous labels once
    ubiquitous = compute_ubiquitous_labels(titles)

    # Cluster
    print("\nClustering (temporal=%s)..." % temporal_mode)
    all_clusters = cluster_topdown(titles, centroid_id, temporal_mode, ubiquitous)

    # Hard temporal mode: split temporally diffuse clusters before coherence
    if temporal_mode == "hard":
        all_clusters, temp_stats = _temporal_split_clusters(all_clusters, titles)
        if temp_stats["split"]:
            print(
                "Temporal split: %d clusters split -> %d sub-clusters"
                % (temp_stats["split"], temp_stats["produced"])
            )

    # Coherence gate: dissolve incoherent clusters
    all_clusters, coh_stats = filter_incoherent_clusters(
        all_clusters, titles, ubiquitous
    )
    if coh_stats["dissolved"] > 0:
        print(
            "Coherence gate: %d clusters dissolved (%d titles -> catchall)"
            % (coh_stats["dissolved"], coh_stats["dissolved_titles"])
        )

    # Merge matching clusters (same sector + date overlap + shared labels)
    all_clusters, merge_stats = _merge_matching_clusters(
        all_clusters, titles, ubiquitous
    )
    if merge_stats["merges"]:
        print("Mechanical merge: %d pairs merged" % merge_stats["merges"])
        for line in merge_stats["details"]:
            print(line)

    # LLM-assisted merge (catches cross-subject duplicates mechanical merge misses)
    print("\nLLM topic merge...")
    all_clusters, llm_stats = asyncio.run(
        _llm_merge_clusters(all_clusters, titles, ubiquitous)
    )
    if llm_stats["llm_merges"]:
        print("LLM merge: %d additional merges" % llm_stats["llm_merges"])
    else:
        print("LLM merge: no additional merges")

    # Apply higher threshold for geo_society (need significant clusters, not noise)
    society_dissolved = 0
    for c in all_clusters:
        track = SECTOR_TO_TRACK.get(c["sector"], "geo_politics")
        if track == "geo_society" and len(c["indices"]) < SOCIETY_MIN_CLUSTER:
            society_dissolved += len(c["indices"])
            c["indices"] = c["indices"][:1]  # reduce to single-title -> catchall
    if society_dissolved:
        print(
            "Society threshold (%d): dissolved %d titles"
            % (SOCIETY_MIN_CLUSTER, society_dissolved)
        )

    emerged = sorted(
        [c for c in all_clusters if len(c["indices"]) >= 2],
        key=lambda c: -len(c["indices"]),
    )
    catchall = [c for c in all_clusters if len(c["indices"]) < 2]
    print(
        "Results: %d emerged, %d catchall (%d%%)"
        % (len(emerged), len(catchall), len(catchall) * 100 // len(titles))
    )

    # Temporal spread stats
    _print_temporal_stats(emerged, titles)

    # Show top clusters
    print("\nTop 15 clusters:")
    for cl in emerged[:15]:
        track = assign_track(cl, titles)
        geo_type, geo_key = tag_geo(cl["indices"], titles, centroid_id)
        sample = titles[cl["indices"][0]]["title_display"][:70]
        print(
            "  [%d] %s/%s -> %s | %s %s"
            % (
                len(cl["indices"]),
                cl["sector"],
                cl["subject"] or "NULL",
                track,
                geo_type,
                geo_key or "",
            )
        )
        print("    %s" % sample)

    if not write:
        print("\nDRY RUN. Use --write to apply.")
        conn.close()
        return

    # Write to DB
    print("\nWriting to DB...")

    # Clean events for target CTMs
    if only_track:
        target_ctm = track_to_ctm.get(only_track)
        if not target_ctm:
            print("ERROR: no CTM found for track '%s'" % only_track)
            conn.close()
            return
        all_ctm_ids = [target_ctm]
        print("  Writing only track: %s (CTM %s)" % (only_track, target_ctm[:8]))
    else:
        all_ctm_ids = list(ctm_map.keys())
    for ctm_id in all_ctm_ids:
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
        cur.execute(
            "UPDATE events_v3 SET merged_into = NULL WHERE merged_into IN "
            "(SELECT id FROM events_v3 WHERE ctm_id = %s)",
            (ctm_id,),
        )
        cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))
    conn.commit()
    print("  Cleaned %d CTMs" % len(all_ctm_ids))

    # Write clusters
    written = 0
    skipped = 0
    for cl in all_clusters:
        track = assign_track(cl, titles)
        if only_track and track != only_track:
            continue
        ctm_id = track_to_ctm.get(track)
        if not ctm_id:
            # Fall back to geo_politics if no CTM for this track
            ctm_id = track_to_ctm.get("geo_politics")
            if not ctm_id:
                skipped += len(cl["indices"])
                continue

        geo_type, geo_key = tag_geo(cl["indices"], titles, centroid_id)
        eid = str(uuid.uuid4())
        tids = [titles[i]["id"] for i in cl["indices"]]
        dates = [
            titles[i]["pubdate_utc"] for i in cl["indices"] if titles[i]["pubdate_utc"]
        ]
        d = max(dates) if dates else month
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
                "INSERT INTO event_v3_titles (event_id,title_id) "
                "VALUES (%s,%s) ON CONFLICT DO NOTHING",
                (eid, tid),
            )
        written += 1

    conn.commit()

    if skipped:
        print("  WARNING: %d titles skipped (no CTM for track)" % skipped)

    # Summary per CTM
    for ctm_id, track in ctm_map.items():
        cur.execute(
            "SELECT count(*), count(*) FILTER (WHERE NOT is_catchall), "
            "max(source_batch_count) FILTER (WHERE NOT is_catchall) "
            "FROM events_v3 WHERE ctm_id = %s",
            (ctm_id,),
        )
        r = cur.fetchone()
        print("  %s: %d events (%d emerged, max %d)" % (track, r[0], r[1], r[2] or 0))

    print("Total: %d events written" % written)

    # Generate titles
    if generate_titles:
        print("\nGenerating titles...")
        from pipeline.phase_4.generate_event_summaries_4_5a import process_events

        for ctm_id, track in ctm_map.items():
            print("  %s..." % track, flush=True)
            asyncio.run(process_events(max_events=300, ctm_id=ctm_id))

    conn.close()
    print("\nDone.")


def load_unlinked_titles(conn, centroid_id, month):
    """Load titles not yet assigned to any event for this centroid+month."""
    cur = conn.cursor()
    cur.execute(
        """SELECT t.id, t.title_display, t.pubdate_utc, t.centroid_ids,
                  tl.sector, tl.subject, tl.target, tl.domain,
                  tl.persons, tl.orgs, tl.places, tl.named_events,
                  tl.actor, tl.action_class
           FROM titles_v3 t
           LEFT JOIN title_labels tl ON t.id = tl.title_id
           WHERE %s = ANY(t.centroid_ids)
             AND t.processing_status = 'assigned'
             AND t.pubdate_utc >= %s::date
             AND t.pubdate_utc < %s::date + INTERVAL '1 month'
             AND NOT EXISTS (
                 SELECT 1 FROM event_v3_titles et
                 JOIN events_v3 e ON e.id = et.event_id
                 WHERE et.title_id = t.id
                   AND e.ctm_id IN (SELECT id FROM ctm WHERE centroid_id = %s AND month = %s)
             )
           ORDER BY t.pubdate_utc""",
        (centroid_id, month, month, centroid_id, month),
    )
    return [
        {
            "id": str(r[0]),
            "title_display": r[1],
            "pubdate_utc": r[2],
            "centroid_ids": r[3] or [],
            "sector": r[4],
            "subject": r[5],
            "target": r[6],
            "domain": r[7],
            "persons": r[8] or [],
            "orgs": r[9] or [],
            "places": r[10] or [],
            "named_events": r[11] or [],
            "actor": r[12] or "",
            "action_class": r[13] or "",
        }
        for r in cur.fetchall()
    ]


def load_existing_event_profiles(conn, centroid_id, month, ubiquitous):
    """Load identity profiles for existing non-catchall events."""
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM ctm WHERE centroid_id = %s AND month = %s",
        (centroid_id, month),
    )
    ctm_ids = [str(r[0]) for r in cur.fetchall()]
    if not ctm_ids:
        return []

    cur.execute(
        """SELECT e.id, e.ctm_id,
                  tl.target, tl.persons, tl.orgs, tl.places, tl.named_events,
                  tl.sector, t.pubdate_utc
           FROM events_v3 e
           JOIN event_v3_titles et ON et.event_id = e.id
           JOIN titles_v3 t ON t.id = et.title_id
           LEFT JOIN title_labels tl ON tl.title_id = t.id
           WHERE e.ctm_id = ANY(%s::uuid[])
             AND NOT e.is_catchall
             AND e.merged_into IS NULL""",
        (ctm_ids,),
    )

    events = defaultdict(lambda: {"labels": set(), "dates": [], "sectors": Counter()})
    for row in cur.fetchall():
        eid = str(row[0])
        ev = events[eid]
        ev["ctm_id"] = str(row[1])
        t_dict = {
            "target": row[2],
            "persons": row[3] or [],
            "orgs": row[4] or [],
            "places": row[5] or [],
            "named_events": row[6] or [],
        }
        if row[7]:
            ev["sectors"][row[7]] += 1
        ev["labels"].update(_identity_labels(t_dict, ubiquitous))
        if row[8]:
            ev["dates"].append(row[8])

    result = []
    for eid, ev in events.items():
        sector = ev["sectors"].most_common(1)[0][0] if ev["sectors"] else "UNKNOWN"
        result.append(
            {
                "event_id": eid,
                "ctm_id": ev["ctm_id"],
                "sector": sector,
                "labels": ev["labels"],
                "min_date": min(ev["dates"]) if ev["dates"] else None,
                "max_date": max(ev["dates"]) if ev["dates"] else None,
            }
        )
    return result


def find_best_match(cluster, titles, existing, ubiquitous):
    """Find the best existing event match for a new cluster."""
    labels = set()
    dates = []
    for i in cluster["indices"]:
        labels.update(_identity_labels(titles[i], ubiquitous))
        if titles[i].get("pubdate_utc"):
            dates.append(titles[i]["pubdate_utc"])

    min_date = min(dates) if dates else None
    max_date = max(dates) if dates else None

    best = None
    best_jaccard = 0
    for ep in existing:
        if ep["sector"] != cluster["sector"]:
            continue
        if min_date and max_date and ep["min_date"] and ep["max_date"]:
            gap = max(
                (ep["min_date"] - max_date).days,
                (min_date - ep["max_date"]).days,
            )
            if gap > CLUSTER_MERGE_DATE_DAYS:
                continue
        shared = labels & ep["labels"]
        if len(shared) < CLUSTER_MERGE_MIN_SHARED:
            continue
        union = labels | ep["labels"]
        jaccard = len(shared) / len(union) if union else 0
        if jaccard >= CLUSTER_MERGE_JACCARD and jaccard > best_jaccard:
            best_jaccard = jaccard
            best = ep
    return best


def incremental_update(centroid_id, month, write=False):
    """Cluster only unlinked titles and match against existing events."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, track FROM ctm WHERE centroid_id = %s AND month = %s",
        (centroid_id, month),
    )
    ctm_map = {str(r[0]): r[1] for r in cur.fetchall()}
    track_to_ctm = {track: ctm_id for ctm_id, track in ctm_map.items()}

    print("Centroid: %s, Month: %s (incremental)" % (centroid_id, month))

    titles = load_unlinked_titles(conn, centroid_id, month)
    print("Unlinked titles: %d" % len(titles))

    if not titles:
        print("Nothing to cluster.")
        conn.close()
        return

    before = len(titles)
    titles = [
        t
        for t in titles
        if t["sector"]
        and t["sector"] != "NON_STRATEGIC"
        and t["subject"] not in FILTERED_SUBJECTS
    ]
    filtered = before - len(titles)
    if filtered:
        print("Filtered %d non-strategic titles: %d remain" % (filtered, len(titles)))

    if not titles:
        print("No strategic titles to cluster.")
        conn.close()
        return

    ubiquitous = compute_ubiquitous_labels(titles)

    clusters = cluster_topdown(
        titles, centroid_id, temporal_mode="hard", ubiquitous=ubiquitous
    )
    clusters, _ = _temporal_split_clusters(clusters, titles)
    clusters, _ = filter_incoherent_clusters(clusters, titles, ubiquitous)
    clusters, _ = _merge_matching_clusters(clusters, titles, ubiquitous)

    emerged = [c for c in clusters if len(c["indices"]) >= 2]
    catchall = [c for c in clusters if len(c["indices"]) < 2]
    print(
        "Clustered: %d emerged, %d catchall (%d%%)"
        % (
            len(emerged),
            len(catchall),
            len(catchall) * 100 // len(titles) if titles else 0,
        )
    )

    existing = load_existing_event_profiles(conn, centroid_id, month, ubiquitous)
    print("Existing events to match against: %d" % len(existing))

    matched_count = 0
    created_count = 0

    for cl in clusters:
        n = len(cl["indices"])
        match = find_best_match(cl, titles, existing, ubiquitous)
        track = assign_track(cl, titles)
        ctm_id = track_to_ctm.get(track) or track_to_ctm.get("geo_politics")

        if match:
            matched_count += 1
            if n >= 3:
                print(
                    "  MATCH [%d] %s/%s -> event %s"
                    % (n, cl["sector"], cl["subject"] or "?", match["event_id"][:8])
                )
            if write and ctm_id:
                tids = [titles[i]["id"] for i in cl["indices"]]
                for tid in tids:
                    cur.execute(
                        "INSERT INTO event_v3_titles (event_id, title_id) "
                        "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (match["event_id"], tid),
                    )
                cur.execute(
                    "UPDATE events_v3 SET source_batch_count = "
                    "(SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s), "
                    "updated_at = NOW() WHERE id = %s",
                    (match["event_id"], match["event_id"]),
                )
        else:
            created_count += 1
            if n >= 3:
                sample = titles[cl["indices"][0]]["title_display"][:60]
                print(
                    "  NEW   [%d] %s/%s: %s"
                    % (n, cl["sector"], cl["subject"] or "?", sample)
                )
            if write and ctm_id:
                eid = str(uuid.uuid4())
                tids = [titles[i]["id"] for i in cl["indices"]]
                geo_type, geo_key = tag_geo(cl["indices"], titles, centroid_id)
                dates = [
                    titles[i]["pubdate_utc"]
                    for i in cl["indices"]
                    if titles[i]["pubdate_utc"]
                ]
                d = max(dates) if dates else month
                fs = min(dates) if dates else None
                is_ca = n < 2
                cur.execute(
                    "INSERT INTO events_v3 (id,ctm_id,source_batch_count,date,"
                    "first_seen,last_active,event_type,bucket_key,is_catchall,"
                    "created_at,updated_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())",
                    (eid, ctm_id, len(tids), d, fs, d, geo_type, geo_key, is_ca),
                )
                for tid in tids:
                    cur.execute(
                        "INSERT INTO event_v3_titles (event_id,title_id) "
                        "VALUES (%s,%s) ON CONFLICT DO NOTHING",
                        (eid, tid),
                    )

    if write:
        conn.commit()

    print(
        "\n%s: %d matched existing, %d new events"
        % ("WRITTEN" if write else "DRY RUN", matched_count, created_count)
    )
    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild all events for a centroid using cross-track clustering"
    )
    parser.add_argument("--centroid", required=True)
    parser.add_argument("--month", default="2026-03-01")
    parser.add_argument("--write", action="store_true", help="Write to DB")
    parser.add_argument(
        "--titles", action="store_true", help="Generate titles after clustering"
    )
    parser.add_argument(
        "--temporal",
        choices=["off", "soft", "hard"],
        default="off",
        help="Temporal proximity mode: off (baseline), soft (Louvain edge decay), hard (split diffuse clusters)",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Incremental mode: cluster only unlinked titles, match against existing events",
    )
    parser.add_argument(
        "--track",
        help="Only write clusters for this track (e.g. geo_security). Others left untouched.",
    )
    args = parser.parse_args()

    if args.incremental:
        incremental_update(args.centroid, args.month, write=args.write)
    else:
        rebuild(
            args.centroid,
            args.month,
            write=args.write,
            generate_titles=args.titles,
            temporal_mode=args.temporal,
            only_track=args.track,
        )


if __name__ == "__main__":
    main()
