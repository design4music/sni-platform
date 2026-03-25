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

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")

import community as community_louvain
import networkx as nx
import psycopg2

from core.config import HIGH_FREQ_ORGS, config
from pipeline.phase_4.normalize_signals import normalize_title_signals

# CTM protagonist exclusion
CTM_PROTAGONIST = {
    "EUROPE-FRANCE": {"MACRON"},
    "AMERICAS-USA": {"TRUMP"},
    "EUROPE-RUSSIA": {"PUTIN"},
    "ASIA-CHINA": {"XI"},
    "EUROPE-UKRAINE": {"ZELENSKY"},
    "MIDEAST-ISRAEL": {"NETANYAHU"},
    "MIDEAST-IRAN": {"KHAMENEI"},
    "EUROPE-GERMANY": {"MERZ"},
    "EUROPE-UK": {"STARMER"},
    "MIDEAST-TURKEY": {"ERDOGAN"},
    "ASIA-INDIA": {"MODI"},
}

# Capital/dominant cities to exclude from clustering identity signals per CTM.
# These cities appear in too many unrelated domestic stories to be discriminating.
CTM_HOME_CITIES = {
    "EUROPE-FRANCE": {"PARIS"},
    "AMERICAS-USA": {"WASHINGTON", "WASHINGTON DC", "NEW YORK"},
    "EUROPE-RUSSIA": {"MOSCOW"},
    "ASIA-CHINA": {"BEIJING"},
    "EUROPE-UKRAINE": {"KYIV", "KIEV"},
    "MIDEAST-ISRAEL": {"TEL AVIV", "JERUSALEM"},
    "MIDEAST-IRAN": {"TEHRAN"},
    "EUROPE-GERMANY": {"BERLIN"},
    "EUROPE-UK": {"LONDON"},
    "MIDEAST-TURKEY": {"ANKARA", "ISTANBUL"},
    "ASIA-INDIA": {"NEW DELHI", "DELHI"},
}

# Sector -> track mapping (replaces domain-based Phase 3.3)
SECTOR_TO_TRACK = {
    "MILITARY": "geo_security",
    "INTELLIGENCE": "geo_security",
    "SECURITY": "geo_security",
    "DIPLOMACY": "geo_politics",
    "GOVERNANCE": "geo_politics",
    "ECONOMY": "geo_economy",
    "ENERGY_RESOURCES": "geo_energy",
    "TECHNOLOGY": "geo_economy",
    "HEALTH_ENVIRONMENT": "geo_humanitarian",
    "SOCIETY": "geo_humanitarian",
    "INFRASTRUCTURE": "geo_economy",
    "UNKNOWN": "geo_politics",
}


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


def _identity_labels(t, protagonist, home_cities):
    """Build the set of specific identity labels for a title.

    Prefixed to avoid collision: TGT:, PLC:, PER:, ORG:, EVT:
    Excludes: home cities, high-freq orgs, NONE target.
    Does NOT exclude protagonist here -- actor+action_class gate already
    groups by story type, so protagonist is a valid discriminator within group.
    """
    labels = set()
    tgt = t.get("target") or ""
    if tgt and tgt != "NONE":
        for v in tgt.split(","):
            v = v.strip()
            if v and v != "NONE":
                labels.add("TGT:" + v)
    for p in t.get("places", []):
        if p.upper() not in home_cities:
            labels.add("PLC:" + p.upper())
    for p in t.get("persons", []):
        labels.add("PER:" + p.upper())
    for o in t.get("orgs", []):
        if o.upper() not in HIGH_FREQ_ORGS:
            labels.add("ORG:" + o.upper())
    for e in t.get("named_events", []):
        labels.add("EVT:" + e)
    return labels


def _louvain_split(indices, titles, sector, subject, protagonist, home_cities):
    """Louvain community detection on identity-label Jaccard similarity.

    Titles with zero identity labels are merged into the largest community
    within their sector+subject group (they belong to the topic area but
    can't be further discriminated).
    """
    label_sets = {
        i: _identity_labels(titles[i], protagonist, home_cities) for i in indices
    }

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
                G.add_edge(ia, ib, weight=len(shared) / len(la | lb))

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


def _find_anchor_keywords(indices, titles, protagonist, home_cities, centroid_id):
    """Find specific, frequent signals that can pre-split a large group.

    An anchor keyword is a signal (person, org, place, named_event, target)
    that appears in >= ANCHOR_MIN_COUNT titles but < ANCHOR_MAX_RATIO of the
    group. These are specific enough to identify a distinct sub-story.

    Excludes: protagonist persons, home cities, and the centroid's own
    country as a target (TGT:RU for Russia, TGT:FR for France, etc.)

    Returns dict: {anchor_label: [title_indices]}
    """
    label_sets = {
        i: _identity_labels(titles[i], protagonist, home_cities) for i in indices
    }

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
            # Exclude protagonist and self-targets
            if lbl.startswith("PER:") and lbl[4:] in protagonist:
                continue
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


def _anchor_split(
    indices, titles, sector, subject, protagonist, home_cities, centroid_id
):
    """Pre-split a large group by anchor keywords before Louvain.

    1. Find anchor keywords (specific, frequent signals)
    2. Assign each title to its best-matching anchor (most shared anchors)
    3. Titles matching no anchor go to a "remainder" group
    4. Each anchor group and the remainder get Louvain or stay as-is
    """
    anchors = _find_anchor_keywords(
        indices, titles, protagonist, home_cities, centroid_id
    )

    if not anchors:
        # No anchor keywords found -- fall through to Louvain
        return None

    label_sets = {
        i: _identity_labels(titles[i], protagonist, home_cities) for i in indices
    }

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


def cluster_topdown(titles, centroid_id):
    """3-level clustering:
      L1: sector + subject  (domain grouping)
      L1.5: anchor keyword split  (specific frequent signals pre-split large groups)
      L2: Louvain on identity labels  (only for groups >= LOUVAIN_SPLIT_THRESHOLD)

    Small groups stay as a single topic. Large groups get anchor-split first
    (if specific keywords exist), then Louvain runs on each sub-group.
    """
    protagonist = CTM_PROTAGONIST.get(centroid_id, set())
    home_cities = CTM_HOME_CITIES.get(centroid_id, set())

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

        # L1.5: try anchor keyword split first
        anchor_groups = _anchor_split(
            l1_idx, titles, sector, subject, protagonist, home_cities, centroid_id
        )

        if anchor_groups:
            # Anchor split succeeded -- apply Louvain to each sub-group if large enough
            for group in anchor_groups:
                if len(group["indices"]) >= LOUVAIN_SPLIT_THRESHOLD:
                    subclusters = _louvain_split(
                        group["indices"],
                        titles,
                        sector,
                        subject,
                        protagonist,
                        home_cities,
                    )
                    all_clusters.extend(subclusters)
                elif len(group["indices"]) > 3:
                    all_clusters.append(group)
                else:
                    all_clusters.append(group)
        else:
            # No anchors -- Louvain on the whole group
            subclusters = _louvain_split(
                l1_idx, titles, sector, subject, protagonist, home_cities
            )
            all_clusters.extend(subclusters)

    return all_clusters


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


MERGE_STOP_WORDS = {
    "the",
    "a",
    "an",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "and",
    "or",
    "with",
    "as",
    "by",
    "is",
    "are",
    "its",
    "after",
    "from",
    "new",
    "says",
    "has",
    "have",
    "will",
    "been",
    "over",
    "amid",
    "not",
    "but",
    "was",
    "were",
    "that",
    "this",
    "more",
    "than",
    "into",
    "about",
    "could",
    "would",
    "also",
    "other",
    "calls",
    "plans",
    "announces",
    "faces",
    "france",
    "french",
    "european",  # centroid-specific noise for France
}

DICE_MERGE_THRESHOLD = 0.40  # slightly above Phase 4.1's 0.35 to reduce false positives


def _event_title_words(title):
    """Extract content words from a generated event title."""
    if not title:
        return set()
    words = set()
    for w in title.lower().split():
        w = w.strip(".,;:!?\"'()[]")
        if w and w not in MERGE_STOP_WORDS and len(w) > 2:
            words.add(w)
    return words


def merge_similar_topics(conn, ctm_ids):
    """Mechanical post-clustering merge pass.

    Within each sector+subject group, find events whose generated titles
    have Dice word overlap >= threshold. Merge smaller into larger by
    moving title links and deleting the smaller event.

    Only merges events that share the same ctm_id (same track).
    """
    cur = conn.cursor()

    # Load all non-catchall events with titles for these CTMs.
    # Use majority sector+subject from underlying titles for grouping.
    cur.execute(
        """SELECT e.id, e.title, e.source_batch_count, e.ctm_id,
                  (SELECT tl2.sector FROM event_v3_titles et2
                   JOIN title_labels tl2 ON tl2.title_id = et2.title_id
                   WHERE et2.event_id = e.id AND tl2.sector IS NOT NULL
                   GROUP BY tl2.sector ORDER BY COUNT(*) DESC LIMIT 1) as sector,
                  (SELECT tl3.subject FROM event_v3_titles et3
                   JOIN title_labels tl3 ON tl3.title_id = et3.title_id
                   WHERE et3.event_id = e.id AND tl3.subject IS NOT NULL
                   GROUP BY tl3.subject ORDER BY COUNT(*) DESC LIMIT 1) as subject
           FROM events_v3 e
           WHERE e.ctm_id = ANY(%s::uuid[])
             AND e.title IS NOT NULL
             AND NOT e.is_catchall""",
        (ctm_ids,),
    )
    rows = cur.fetchall()

    # Group by (ctm_id, sector) -- merge across subjects within same sector.
    # Subjects can disagree for the same story (e.g., MEDIATION vs SUMMIT
    # for "Zelensky visits Macron").
    groups = defaultdict(list)
    for eid, title, count, ctm_id, sector, subject in rows:
        groups[(str(ctm_id), sector)].append(
            {"id": str(eid), "title": title, "count": count or 0}
        )

    total_merged = 0
    for (ctm_id, sector, subject), events in groups.items():
        if len(events) < 2:
            continue

        # Sort by size descending (largest = anchor)
        events.sort(key=lambda e: -e["count"])
        word_sets = [_event_title_words(e["title"]) for e in events]

        # Find merge pairs
        merged_ids = set()
        for i in range(len(events)):
            if events[i]["id"] in merged_ids:
                continue
            for j in range(i + 1, len(events)):
                if events[j]["id"] in merged_ids:
                    continue
                wa, wb = word_sets[i], word_sets[j]
                if not wa or not wb:
                    continue
                dice = 2 * len(wa & wb) / (len(wa) + len(wb))
                if dice >= DICE_MERGE_THRESHOLD:
                    anchor_id = events[i]["id"]
                    candidate_id = events[j]["id"]
                    # Move titles, delete candidate
                    cur.execute(
                        "UPDATE event_v3_titles SET event_id = %s "
                        "WHERE event_id = %s",
                        (anchor_id, candidate_id),
                    )
                    cur.execute(
                        "DELETE FROM events_v3 WHERE id = %s",
                        (candidate_id,),
                    )
                    cur.execute(
                        """UPDATE events_v3
                           SET source_batch_count = (
                               SELECT COUNT(*) FROM event_v3_titles
                               WHERE event_id = %s
                           ), updated_at = NOW()
                           WHERE id = %s""",
                        (anchor_id, anchor_id),
                    )
                    merged_ids.add(candidate_id)
                    events[i]["count"] += events[j]["count"]
                    total_merged += 1
                    print(
                        "  MERGE [%d]+[%d] dice=%.2f: %s <- %s"
                        % (
                            events[i]["count"],
                            events[j]["count"],
                            dice,
                            events[i]["title"][:50],
                            events[j]["title"][:50],
                        )
                    )

    conn.commit()
    return total_merged


def rebuild(centroid_id, month, write=False, generate_titles=False):
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

    # Filter out non-strategic titles
    before = len(titles)
    titles = [t for t in titles if t["sector"] != "NON_STRATEGIC"]
    non_strat = before - len(titles)
    if non_strat:
        print("Filtered %d NON_STRATEGIC titles (%d remain)" % (non_strat, len(titles)))

    # Normalize signals
    print("\nNormalizing signals...")
    aliases = normalize_title_signals(
        titles, conn, ["places", "persons", "orgs", "named_events"]
    )
    for sig, am in aliases.items():
        new_only = {k: v for k, v in am.items() if k != v}
        if new_only:
            print("  %s: %s" % (sig, dict(list(new_only.items())[:5])))

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

    # Cluster
    print("\nClustering...")
    all_clusters = cluster_topdown(titles, centroid_id)
    emerged = sorted(
        [c for c in all_clusters if len(c["indices"]) >= 2],
        key=lambda c: -len(c["indices"]),
    )
    catchall = [c for c in all_clusters if len(c["indices"]) < 2]
    print(
        "Results: %d emerged, %d catchall (%d%%)"
        % (len(emerged), len(catchall), len(catchall) * 100 // len(titles))
    )

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

    # Clean ALL events for all CTMs of this centroid+month
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

        # Mechanical merge pass on generated titles
        print("\nMechanical merge pass (Dice >= %.2f)..." % DICE_MERGE_THRESHOLD)
        merged = merge_similar_topics(conn, all_ctm_ids)
        if merged:
            print("Merged %d topic pairs" % merged)
            # Re-generate titles for merged events (source count changed)
            print("Re-generating titles for merged events...")
            for ctm_id, track in ctm_map.items():
                asyncio.run(process_events(max_events=300, ctm_id=ctm_id))
        else:
            print("No merge candidates found")

    conn.close()
    print("\nDone.")


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
    args = parser.parse_args()

    rebuild(args.centroid, args.month, write=args.write, generate_titles=args.titles)


if __name__ == "__main__":
    main()
