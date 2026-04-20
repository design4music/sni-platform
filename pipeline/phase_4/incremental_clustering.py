"""
Phase 4: D-056 Day-Beat Clustering

Clusters titles by (date, actor, action_class, target) day-beat with
single-link entity overlap. Day = atomic clustering unit. No bucket partition;
bucket assigned post-clustering.

See docs/context/CLUSTERING_REDESIGN.md.

Usage:
    python -m pipeline.phase_4.incremental_clustering --ctm-id <id> [--write]
"""

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2

from core.config import HIGH_FREQ_ORGS, HIGH_FREQ_PERSONS, config
from core.publisher_filter import filter_publisher_signals, load_publisher_patterns


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


# =============================================================================
# DATABASE
# =============================================================================


def load_titles_chronological(conn, ctm_id: str) -> list:
    """Load titles in chronological order (oldest first).

    D-056: also fetches actor/action_class/target (beat triple) and industries.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            t.id, t.title_display, t.pubdate_utc, t.centroid_ids,
            tl.persons, tl.orgs, tl.places, tl.commodities,
            tl.policies, tl.systems, tl.named_events,
            tl.actor, tl.action_class, tl.target, tl.industries
        FROM titles_v3 t
        JOIN title_assignments ta ON t.id = ta.title_id
        LEFT JOIN title_labels tl ON t.id = tl.title_id
        WHERE ta.ctm_id = %s
        ORDER BY t.pubdate_utc ASC
        """,
        (ctm_id,),
    )
    rows = cur.fetchall()
    titles = []
    for r in rows:
        titles.append(
            {
                "id": str(r[0]),
                "title_display": r[1],
                "pubdate_utc": r[2],
                "centroid_ids": r[3] or [],
                "persons": r[4] or [],
                "orgs": r[5] or [],
                "places": r[6] or [],
                "commodities": r[7] or [],
                "policies": r[8] or [],
                "systems": r[9] or [],
                "named_events": r[10] or [],
                "actor": r[11],
                "action_class": r[12],
                "target": r[13],
                "industries": r[14] or [],
            }
        )
    return titles


def load_new_titles_only(conn, ctm_id: str) -> list:
    """Load titles assigned to this CTM that are NOT yet linked to any event.

    Same as load_titles_chronological but excludes titles already in event_v3_titles.
    On first run (no events exist), returns all titles -- equivalent to cold path.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            t.id, t.title_display, t.pubdate_utc, t.centroid_ids,
            tl.persons, tl.orgs, tl.places, tl.commodities,
            tl.policies, tl.systems, tl.named_events,
            tl.actor, tl.action_class, tl.target, tl.industries
        FROM titles_v3 t
        JOIN title_assignments ta ON t.id = ta.title_id
        LEFT JOIN title_labels tl ON t.id = tl.title_id
        WHERE ta.ctm_id = %s
        AND t.id NOT IN (
            SELECT evt.title_id FROM event_v3_titles evt
            JOIN events_v3 e ON evt.event_id = e.id
            WHERE e.ctm_id = %s
        )
        ORDER BY t.pubdate_utc ASC
        """,
        (ctm_id, ctm_id),
    )
    rows = cur.fetchall()
    titles = []
    for r in rows:
        titles.append(
            {
                "id": str(r[0]),
                "title_display": r[1],
                "pubdate_utc": r[2],
                "centroid_ids": r[3] or [],
                "persons": r[4] or [],
                "orgs": r[5] or [],
                "places": r[6] or [],
                "commodities": r[7] or [],
                "policies": r[8] or [],
                "systems": r[9] or [],
                "named_events": r[10] or [],
                "actor": r[11],
                "action_class": r[12],
                "target": r[13],
                "industries": r[14] or [],
            }
        )
    return titles


def is_geo_centroid(centroid_id: str) -> bool:
    """GEO centroids look like AMERICAS-USA; SYS centroids start with SYS-."""
    return not centroid_id.startswith("SYS-")


def get_ctm_info(conn, ctm_id: str) -> dict:
    cur = conn.cursor()
    cur.execute(
        "SELECT id, centroid_id, track, month FROM ctm WHERE id = %s",
        (ctm_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "id": str(row[0]),
        "centroid_id": row[1],
        "track": row[2],
        "month": row[3],
    }


# =============================================================================
# D-056 TIME-WINDOWED CLUSTERING (day = atomic unit)
# =============================================================================
#
# Replaces signal-only IncrementalTopic clustering. Two titles share a cluster
# if and only if they share (actor, action_class, target) AND publication date
# AND at least one entity (with n-gram fallback for entity-empty titles).
#
# Bucketing happens AFTER clustering, not before. Caller passes ALL titles for
# the CTM with no bucket partition.
#
# See docs/context/CLUSTERING_REDESIGN.md and DecisionLog D-056.

NGRAM_STOPWORDS = frozenset(
    {
        "the",
        "a",
        "an",
        "of",
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "by",
        "from",
        "as",
        "is",
        "are",
        "was",
        "were",
        "and",
        "or",
        "but",
        "not",
        "be",
        "been",
        "has",
        "have",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "after",
        "before",
        "over",
        "into",
    }
)


def _extract_discriminating_entities(title: dict) -> set:
    """All entity tokens minus high-frequency persons/orgs (TRUMP, NATO, ...)."""
    entities = set()
    for sig_type in ("persons", "orgs", "places", "named_events", "industries"):
        for v in title.get(sig_type) or []:
            normalized = v.upper() if sig_type == "persons" else v
            if sig_type == "persons" and normalized in HIGH_FREQ_PERSONS:
                continue
            if sig_type == "orgs" and normalized in HIGH_FREQ_ORGS:
                continue
            entities.add("{}:{}".format(sig_type, normalized))
    return entities


def _compute_ngrams(titles: list) -> set:
    """3-word lowercase n-grams from title text, stopwords stripped."""
    grams = set()
    for t in titles:
        text = (t.get("title_display") or "").lower()
        text = re.sub(r"[^\w\s]", " ", text)
        words = [w for w in text.split() if w not in NGRAM_STOPWORDS and len(w) > 1]
        for i in range(len(words) - 2):
            grams.add(" ".join(words[i : i + 3]))
    return grams


def _can_merge(a: dict, b: dict) -> bool:
    """Two cluster-dicts can merge if they share at least one entity, OR
    (when at least one side has no entities) at least one n-gram."""
    if a["entities"] and b["entities"]:
        return bool(a["entities"] & b["entities"])
    # N-gram fallback: one or both sides have no discriminating entities
    if a.get("ngrams") is None:
        a["ngrams"] = _compute_ngrams(a["titles"])
    if b.get("ngrams") is None:
        b["ngrams"] = _compute_ngrams(b["titles"])
    if a["ngrams"] and b["ngrams"]:
        return bool(a["ngrams"] & b["ngrams"])
    return False


def _single_link_by_entity(titles: list) -> list:
    """Greedy single-link clustering on entity overlap.

    Each title starts as its own cluster. Clusters merge if they share at least
    one entity. Iterates until no more merges happen.
    """
    clusters = []
    for t in titles:
        clusters.append(
            {
                "titles": [t],
                "entities": _extract_discriminating_entities(t),
                "ngrams": None,
            }
        )

    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(clusters):
            j = i + 1
            while j < len(clusters):
                if _can_merge(clusters[i], clusters[j]):
                    clusters[i]["titles"].extend(clusters[j]["titles"])
                    clusters[i]["entities"] |= clusters[j]["entities"]
                    if clusters[j].get("ngrams"):
                        if clusters[i].get("ngrams") is None:
                            clusters[i]["ngrams"] = set()
                        clusters[i]["ngrams"] |= clusters[j]["ngrams"]
                    clusters.pop(j)
                    changed = True
                else:
                    j += 1
            i += 1
    return clusters


def _pick_dominant_entity(titles: list) -> str:
    """Most-frequent discriminating entity across the cluster's titles.

    This IS the cluster's spine - derived from data, no separate assignment.
    Returns a string like "places:Hormuz" or None if no discriminating entity.
    """
    counter = Counter()
    for t in titles:
        for sig_type in ("persons", "orgs", "places", "named_events", "industries"):
            for v in t.get(sig_type) or []:
                normalized = v.upper() if sig_type == "persons" else v
                if sig_type == "persons" and normalized in HIGH_FREQ_PERSONS:
                    continue
                if sig_type == "orgs" and normalized in HIGH_FREQ_ORGS:
                    continue
                counter["{}:{}".format(sig_type, normalized)] += 1
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def _pick_bucket_key(titles: list, home_centroid_id: str) -> tuple:
    """Bucket assignment (D-056 LOCK-2, corrected).

    Phase 2 always tags the home centroid on every title assigned to a CTM, so
    the original "any title has home centroid -> domestic" rule fired on
    everything. Use foreign GEO centroids as the discriminator instead.

    Returns (event_type, bucket_key):
    - No title has any foreign GEO centroid -> ("domestic", None)
    - Most cluster titles share one foreign GEO centroid -> ("bilateral", <centroid>)
    - Multiple foreign GEOs spread thin -> ("other_international", None)
    """
    foreign_counter = Counter()
    titles_with_foreign = 0
    for t in titles:
        foreign = [
            c
            for c in (t.get("centroid_ids") or [])
            if c != home_centroid_id and is_geo_centroid(c)
        ]
        if foreign:
            titles_with_foreign += 1
            for c in foreign:
                foreign_counter[c] += 1

    if not foreign_counter:
        return ("domestic", None)

    top_centroid, top_count = foreign_counter.most_common(1)[0]
    # Bilateral only if top foreign centroid appears in >= half of ALL cluster
    # titles, not half of titles-with-foreign-centroids. Phase 2 cross-tags
    # stories topically (e.g., Michigan synagogue -> MIDEAST-ISRAEL), so a
    # minority co-tag must not hijack the bucket.
    total = len(titles)
    if top_count * 2 >= total:
        return ("bilateral", top_centroid)
    return ("domestic", None)


# Text-similarity merge: catches cross-beat fragmentation of one event.
# The LLM labels one story across multiple beat triples (e.g., tanker crash
# appears as SECURITY_INCIDENT + STATEMENT + MILITARY_OPERATION rescue).
# Title text is the orthogonal signal that ignores these label splits.

_TEXT_STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "are",
        "was",
        "were",
        "has",
        "have",
        "had",
        "but",
        "not",
        "its",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "says",
        "said",
        "say",
        "told",
        "tells",
        "tell",
        "report",
        "reports",
        "reported",
        "about",
        "after",
        "before",
        "over",
        "into",
        "out",
        "than",
        "then",
        "now",
        "new",
        "just",
        "also",
        "more",
        "most",
        "some",
        "any",
        "all",
        "who",
        "what",
        "why",
        "when",
        "how",
        "here",
        "there",
        "only",
        "even",
        "still",
        "yet",
        "ago",
        "under",
        "between",
        "amid",
        "against",
        "per",
        "via",
        "live",
        "blog",
        "latest",
        "breaking",
        "news",
        "update",
        "updates",
        "watch",
        "video",
        "photos",
        "image",
        "images",
        "exclusive",
    }
)

TEXT_DICE_THRESHOLD = 0.5


def _tokenize_title(text: str) -> set:
    if not text:
        return set()
    toks = set()
    for m in re.findall(r"[A-Za-z]{3,}", text):
        low = m.lower()
        if low in _TEXT_STOPWORDS:
            continue
        up = m.upper()
        if up in HIGH_FREQ_PERSONS or up in HIGH_FREQ_ORGS:
            continue
        toks.add(low)
    return toks


def _dice(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return 2.0 * len(a & b) / (len(a) + len(b))


def _dominant_place(titles: list) -> str:
    """Most-frequent place (or named_event) across a cluster's titles.
    Returns a prefixed token like 'places:Hormuz' or None if no place is
    extracted on any title. Titles mentioning multiple places each contribute
    once per place, but the MOST FREQUENT wins — so a single multi-place
    title cannot make a secondary place dominant.
    """
    counter = Counter()
    for t in titles:
        for p in t.get("places") or []:
            counter["places:" + p] += 1
        for ne in t.get("named_events") or []:
            counter["named_events:" + ne] += 1
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def _dominant_target(titles: list) -> str:
    """Most-frequent target across a cluster's titles. NONE if absent."""
    counter = Counter()
    for t in titles:
        counter[t.get("target") or "NONE"] += 1
    return counter.most_common(1)[0][0] if counter else "NONE"


def _merge_day_clusters(day_clusters: list) -> list:
    """Union-find merge of day-local clusters across beat triples.

    Two clusters on the same day merge when EITHER:
      1. They have the SAME (dominant place/named_event, dominant target).
         Both dimensions must match: place anchors the theater, target
         anchors the counterparty. Paris-elections (target NONE) stays
         separate from Paris-US-China-talks (target CN) even though both
         have dominant_place=Paris.
      2. Both clusters have NO dominant place AND any title pair across
         them has token-Dice >= TEXT_DICE_THRESHOLD. This fallback only
         fires for entity-empty fragments (e.g., Russia-Iran intelligence
         reports with empty places).
    """
    n = len(day_clusters)
    if n < 2:
        return day_clusters

    dominants = [
        (
            (_dominant_place(c["titles"]), _dominant_target(c["titles"]))
            if _dominant_place(c["titles"])
            else None
        )
        for c in day_clusters
    ]

    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Rule 1: same dominant place/named_event -> merge
    by_dominant = defaultdict(list)
    for i, d in enumerate(dominants):
        if d:
            by_dominant[d].append(i)
    for idx_list in by_dominant.values():
        for k in range(1, len(idx_list)):
            union(idx_list[0], idx_list[k])

    # Rule 2: Dice fallback, ONLY between clusters that both lack a dominant
    # place AND share the same dominant target. Without the target gate, Dice
    # at 0.5 blended "US kills Khamenei" (target=IR) with "Iran retaliates"
    # (target=US) on the same day because both share many surface tokens
    # ("khamenei", "iran", "us", "strike"). Target is the cleanest
    # discriminator when place is absent.
    cluster_title_tokens = [
        [_tokenize_title(t.get("title_display") or "") for t in c["titles"]]
        for c in day_clusters
    ]
    empty_targets = [
        _dominant_target(day_clusters[i]["titles"]) if not dominants[i] else None
        for i in range(n)
    ]
    empty_idx = [i for i in range(n) if not dominants[i]]
    for a_pos in range(len(empty_idx)):
        i = empty_idx[a_pos]
        ti = cluster_title_tokens[i]
        if not ti:
            continue
        for b_pos in range(a_pos + 1, len(empty_idx)):
            j = empty_idx[b_pos]
            if find(i) == find(j):
                continue
            if empty_targets[i] != empty_targets[j]:
                continue
            tj = cluster_title_tokens[j]
            if not tj:
                continue
            matched = False
            for a in ti:
                if matched:
                    break
                if not a:
                    continue
                for b in tj:
                    if not b:
                        continue
                    if _dice(a, b) >= TEXT_DICE_THRESHOLD:
                        union(i, j)
                        matched = True
                        break

    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(day_clusters[i])

    out = []
    for members in groups.values():
        if len(members) == 1:
            out.append(members[0])
            continue
        merged = {
            "titles": [],
            "entities": set(),
            "ngrams": None,
        }
        for c in members:
            merged["titles"].extend(c["titles"])
            merged["entities"] |= c.get("entities") or set()
        out.append(merged)
    return out


def cluster_by_day_beat(titles: list, home_centroid_id: str) -> list:
    """D-056 clustering: day = atomic unit, no bucket partition.

    Two-stage within each day:
      1. Group titles by beat triple; within each beat group, single-link
         merge on entity overlap (strict, tight clusters per beat).
      2. Across beat groups of the same day, merge clusters when ANY
         cross-cluster title pair has token-Dice >= TEXT_DICE_THRESHOLD.
         This captures fragments of one event labeled under different beats
         (Khamenei, Iraq tanker, Oslo embassy, etc.) without dropping the
         beat-triple rigor at stage 1.
    """
    if not titles:
        return []

    # Group by (date, beat), first at stage 1
    day_beat_groups = defaultdict(lambda: defaultdict(list))
    for t in titles:
        if not t.get("pubdate_utc"):
            continue
        date = t["pubdate_utc"].date()
        beat = (t.get("actor"), t.get("action_class"), t.get("target"))
        day_beat_groups[date][beat].append(t)

    all_clusters = []
    for date, beat_groups in day_beat_groups.items():
        day_clusters = []
        # Stage 1: entity-overlap single-link within each beat
        for beat, group in beat_groups.items():
            entity_clusters = _single_link_by_entity(group)
            for c in entity_clusters:
                c["_beat_hint"] = beat
                day_clusters.append(c)

        # Stage 2: dominant-entity + text-Dice merge across beats within the day
        day_clusters = _merge_day_clusters(day_clusters)

        # Enrich each surviving cluster with metadata
        for c in day_clusters:
            event_type, bucket_key = _pick_bucket_key(c["titles"], home_centroid_id)
            beat_counter = Counter()
            for t in c["titles"]:
                beat_counter[
                    (t.get("actor"), t.get("action_class"), t.get("target"))
                ] += 1
            beat = (
                beat_counter.most_common(1)[0][0]
                if beat_counter
                else (None, None, None)
            )
            c["date"] = date
            c["beat"] = beat
            c["dominant_entity"] = _pick_dominant_entity(c["titles"])
            c["event_type"] = event_type
            c["bucket_key"] = bucket_key
            c["source_count"] = len(c["titles"])
            c["first_date"] = date
            c["last_date"] = date
            all_clusters.append(c)

    return all_clusters


# =============================================================================
# DATABASE WRITE
# =============================================================================


def write_clusters_to_db(conn, clusters: list, ctm_id: str) -> int:
    """D-056: Write day-beat clusters to events_v3.

    No min_titles filter - singletons are kept (frontend filters by per-CTM
    percentile). No catchall event - singletons are just size-1 events_v3 rows.

    Returns: count of events written.
    """
    import uuid

    cur = conn.cursor()
    written = 0

    for c in clusters:
        event_id = str(uuid.uuid4())
        # Build summary from dominant entity + beat
        beat = c.get("beat") or (None, None, None)
        actor, action, target = beat
        anchor = c.get("dominant_entity")
        anchor_str = anchor.split(":", 1)[1] if anchor else "misc"
        summary_parts = []
        if actor:
            summary_parts.append(actor)
        if action:
            summary_parts.append(action)
        if target and target != "NONE":
            summary_parts.append("-> " + target)
        summary_parts.append("[" + anchor_str + "]")
        summary = " ".join(summary_parts)

        # Mechanical fallback title: pick the earliest title_display that has
        # a reasonable length. Phase 4.5a can overwrite this with an LLM title
        # later, but until then the cluster is human-readable and searchable.
        mechanical_title = None
        sorted_titles = sorted(
            c["titles"],
            key=lambda t: (
                t.get("pubdate_utc") or 0,
                -(len(t.get("title_display") or "")),
            ),
        )
        for t in sorted_titles:
            td = t.get("title_display")
            if td and len(td) >= 20:
                mechanical_title = td
                break
        if not mechanical_title and sorted_titles:
            mechanical_title = sorted_titles[0].get("title_display")

        try:
            cur.execute(
                """
                INSERT INTO events_v3 (
                    id, ctm_id, date, first_seen, title, summary, event_type, bucket_key,
                    source_batch_count, is_catchall, last_active
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event_id,
                    ctm_id,
                    c["date"],
                    c["first_date"],
                    mechanical_title,
                    summary,
                    c["event_type"],
                    c["bucket_key"],
                    c["source_count"],
                    False,
                    c["last_date"],
                ),
            )
            for title in c["titles"]:
                cur.execute(
                    """
                    INSERT INTO event_v3_titles (event_id, title_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (event_id, title["id"]),
                )
            written += 1
        except Exception as e:
            print("Failed to write cluster: {}".format(e))

    conn.commit()
    return written


# =============================================================================
# DAEMON INTERFACE
# =============================================================================


def _wipe_ctm_events(conn, ctm_id: str) -> None:
    """Delete all events_v3 rows (and downstream links) for a CTM."""
    cur = conn.cursor()
    cur.execute(
        """UPDATE events_v3 SET merged_into = NULL
           WHERE merged_into IN (SELECT id FROM events_v3 WHERE ctm_id = %s)""",
        (ctm_id,),
    )
    cur.execute(
        """DELETE FROM event_strategic_narratives
           WHERE event_id IN (SELECT id FROM events_v3 WHERE ctm_id = %s)""",
        (ctm_id,),
    )
    cur.execute(
        "DELETE FROM event_v3_titles WHERE event_id IN (SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (ctm_id,),
    )
    cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))


def process_ctm_for_daemon(conn, ctm_id: str, centroid_id: str, track: str) -> int:
    """Incremental daemon entry point.

    Clusters ONLY new (unlinked) titles, then matches resulting mini-clusters
    to existing events on the same date via entity overlap or title-word Dice.
    Matched titles are appended to the existing event; unmatched clusters
    create new events. Existing events are NEVER deleted or modified (their
    is_promoted, title, summary, daily_briefs are preserved).

    Returns: number of new events created (0 if no new titles or all matched).
    """
    new_titles = load_new_titles_only(conn, ctm_id)
    if not new_titles:
        return 0

    publisher_patterns = load_publisher_patterns(conn)
    for t in new_titles:
        t["orgs"] = filter_publisher_signals(t.get("orgs", []), publisher_patterns)

    # Cluster new titles among themselves (same algorithm as cold path)
    new_clusters = cluster_by_day_beat(new_titles, centroid_id)

    # Load existing events for affected dates so we can match against them
    affected_dates = {c["date"] for c in new_clusters}
    existing_events = _load_existing_events(conn, ctm_id, affected_dates)

    cur = conn.cursor()
    created = 0
    appended = 0

    for nc in new_clusters:
        match_id = _find_matching_event(nc, existing_events.get(nc["date"], []))
        if match_id:
            # Append titles to existing event
            for t in nc["titles"]:
                cur.execute(
                    "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (match_id, t["id"]),
                )
            # Update source count
            cur.execute(
                """UPDATE events_v3 SET source_batch_count = (
                       SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
                   ), last_active = GREATEST(last_active, %s)
                   WHERE id = %s""",
                (match_id, nc["date"], match_id),
            )
            appended += 1
        else:
            # Create new event
            import uuid as _uuid

            event_id = str(_uuid.uuid4())
            mechanical_title = _pick_mechanical_title(nc["titles"])
            beat = nc.get("beat") or (None, None, None)
            actor, action, target = beat
            anchor = nc.get("dominant_entity")
            anchor_str = anchor.split(":", 1)[1] if anchor else "misc"
            parts = []
            if actor:
                parts.append(actor)
            if action:
                parts.append(action)
            if target and target != "NONE":
                parts.append("-> " + target)
            parts.append("[" + anchor_str + "]")
            summary = " ".join(parts)

            cur.execute(
                """INSERT INTO events_v3 (
                       id, ctm_id, date, first_seen, title, summary,
                       event_type, bucket_key, source_batch_count,
                       is_catchall, last_active
                   ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    event_id,
                    ctm_id,
                    nc["date"],
                    nc["first_date"],
                    mechanical_title,
                    summary,
                    nc["event_type"],
                    nc["bucket_key"],
                    nc["source_count"],
                    False,
                    nc["last_date"],
                ),
            )
            for t in nc["titles"]:
                cur.execute(
                    "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (event_id, t["id"]),
                )
            created += 1
            # Add to existing_events so subsequent clusters can match against it
            existing_events.setdefault(nc["date"], []).append(
                _event_record(event_id, nc)
            )

    conn.commit()
    if appended or created:
        print(
            "  %s/%s: %d new titles -> %d appended to existing, %d new events"
            % (centroid_id, track, len(new_titles), appended, created)
        )
    return created


def _pick_mechanical_title(titles):
    """Pick earliest title_display with length >= 20 as fallback title."""
    sorted_titles = sorted(
        titles,
        key=lambda t: (t.get("pubdate_utc") or 0, -(len(t.get("title_display") or ""))),
    )
    for t in sorted_titles:
        td = t.get("title_display")
        if td and len(td) >= 20:
            return td
    return sorted_titles[0].get("title_display") if sorted_titles else None


def _load_existing_events(conn, ctm_id, dates):
    """Load existing events for specific dates with their entity signals."""
    if not dates:
        return {}
    cur = conn.cursor()
    date_list = list(dates)
    cur.execute(
        """SELECT e.id::text, e.date, e.title, e.source_batch_count
             FROM events_v3 e
            WHERE e.ctm_id = %s AND e.date = ANY(%s::date[])
              AND e.merged_into IS NULL""",
        (ctm_id, date_list),
    )
    events = {}
    id_list = []
    for eid, date, title, src in cur.fetchall():
        ev = {"id": eid, "date": date, "title": title, "src": src}
        events.setdefault(date, []).append(ev)
        id_list.append(eid)

    if id_list:
        cur.execute(
            """SELECT et.event_id::text, tl.persons, tl.orgs, tl.places,
                      tl.named_events, tl.action_class
                 FROM event_v3_titles et
                 JOIN title_labels tl ON tl.title_id = et.title_id
                WHERE et.event_id = ANY(%s::uuid[])""",
            (id_list,),
        )
        sig_map = {}
        for eid, persons, orgs, places, named, action in cur.fetchall():
            if eid not in sig_map:
                sig_map[eid] = {"entities": set(), "actions": Counter()}
            s = sig_map[eid]
            for p in persons or []:
                s["entities"].add(p)
            for o in orgs or []:
                s["entities"].add(o)
            for pl in places or []:
                s["entities"].add(pl)
            for ne in named or []:
                s["entities"].add(ne)
            if action:
                s["actions"][action] += 1

        for date_events in events.values():
            for ev in date_events:
                s = sig_map.get(ev["id"], {})
                ev["entities"] = s.get("entities", set())
                acts = s.get("actions", Counter())
                ev["action"] = acts.most_common(1)[0][0] if acts else None
                ev["title_words"] = set()
                if ev["title"]:
                    for w in ev["title"].lower().split():
                        w = w.strip(".,;:!?\"'()[]{}|-")
                        if w and len(w) > 1:
                            ev["title_words"].add(w)

    cur.close()
    return events


def _event_record(event_id, cluster):
    """Build a lightweight event dict from a cluster for matching."""
    entities = set()
    actions = Counter()
    for t in cluster["titles"]:
        for sig in ("persons", "orgs", "places", "named_events"):
            for v in t.get(sig) or []:
                entities.add(v)
        if t.get("action_class"):
            actions[t["action_class"]] += 1

    title_words = set()
    # Use first title for word matching
    first_title = cluster["titles"][0].get("title_display") or ""
    for w in first_title.lower().split():
        w = w.strip(".,;:!?\"'()[]{}|-")
        if w and len(w) > 1:
            title_words.add(w)

    return {
        "id": event_id,
        "date": cluster["date"],
        "title": first_title,
        "src": cluster["source_count"],
        "entities": entities,
        "action": actions.most_common(1)[0][0] if actions else None,
        "title_words": title_words,
    }


# Same thresholds as merge_same_day_events.py
_HIGH_FREQ = frozenset(
    {"TRUMP", "BIDEN", "NATO", "UN", "EU", "PUTIN", "NETANYAHU", "KHAMENEI"}
)
_STOP = frozenset(
    "the a an in on of to for and or is are was were with by at from as that "
    "this it its be has have had not but after over says said could new us s t "
    "will during about between into than more out up no may".split()
)


def _find_matching_event(new_cluster, existing_events):
    """Find best matching existing event for a new mini-cluster.

    Returns event_id if match found, None otherwise.
    Uses same hybrid logic as merge_same_day_events: entity overlap OR Dice.
    Prefers the biggest existing event when multiple match.
    """
    if not existing_events:
        return None

    nc_entities = set()
    nc_actions = Counter()
    for t in new_cluster["titles"]:
        for sig in ("persons", "orgs", "places", "named_events"):
            for v in t.get(sig) or []:
                nc_entities.add(v)
        if t.get("action_class"):
            nc_actions[t["action_class"]] += 1
    nc_ents = nc_entities - _HIGH_FREQ
    nc_action = nc_actions.most_common(1)[0][0] if nc_actions else None

    nc_words = set()
    for t in new_cluster["titles"]:
        td = t.get("title_display") or ""
        for w in td.lower().split():
            w = w.strip(".,;:!?\"'()[]{}|-")
            if w and len(w) > 1 and w not in _STOP:
                nc_words.add(w)

    best_id = None
    best_src = -1

    for ev in existing_events:
        ev_ents = ev.get("entities", set()) - _HIGH_FREQ
        shared = nc_ents & ev_ents
        entity_match = (
            len(shared) >= 1 and nc_action == ev.get("action") and nc_action is not None
        )

        ev_words = ev.get("title_words", set()) - _STOP
        dice = 0
        if nc_words and ev_words:
            dice = 2 * len(nc_words & ev_words) / (len(nc_words) + len(ev_words))
        title_match = dice >= 0.4

        if (entity_match or title_match) and ev["src"] > best_src:
            best_id = ev["id"]
            best_src = ev["src"]

    return best_id


# =============================================================================
# RECLUSTER FROM SCRATCH
# =============================================================================


def recluster_ctm(ctm_id: str, dry_run: bool = True, method: str = "signal"):
    """D-056: Wipe events for a CTM and recluster ALL titles using day-beat clustering.

    Day = atomic clustering unit. No bucket partition. Bucket assigned post-clustering.
    See docs/context/CLUSTERING_REDESIGN.md.

    Args:
        method: ignored (legacy parameter, only day-beat method exists now)

    Usage:
        python -m pipeline.phase_4.incremental_clustering --ctm-id <id> --recluster --write
    """
    conn = get_connection()
    ctm_info = get_ctm_info(conn, ctm_id)
    if not ctm_info:
        print("CTM not found: {}".format(ctm_id))
        conn.close()
        return

    centroid_id = ctm_info["centroid_id"]
    track = ctm_info["track"]
    print(
        "RECLUSTER (D-056): {} / {} / {}".format(centroid_id, track, ctm_info["month"])
    )

    all_titles = load_titles_chronological(conn, ctm_id)
    print("Total titles: {}".format(len(all_titles)))
    if not all_titles:
        print("No titles to cluster.")
        conn.close()
        return

    # Filter publisher signals (still useful since Phase 2 publisher leak persists)
    publisher_patterns = load_publisher_patterns(conn)
    for t in all_titles:
        t["orgs"] = filter_publisher_signals(t.get("orgs", []), publisher_patterns)

    # Cluster: day-beat with no bucket partition
    clusters = cluster_by_day_beat(all_titles, centroid_id)

    # Summary stats
    total_in_clusters = sum(c["source_count"] for c in clusters)
    by_type = Counter(c["event_type"] for c in clusters)
    by_size = sorted([c["source_count"] for c in clusters], reverse=True)
    multi_title = [c for c in clusters if c["source_count"] >= 2]
    print(
        "\n{} clusters covering {} titles ({} singletons)".format(
            len(clusters), total_in_clusters, len(clusters) - len(multi_title)
        )
    )
    print(
        "  by type: domestic={} bilateral={} other_international={}".format(
            by_type.get("domestic", 0),
            by_type.get("bilateral", 0),
            by_type.get("other_international", 0),
        )
    )
    print("  size distribution top 10: {}".format(by_size[:10]))

    # Show top clusters by source count
    clusters_sorted = sorted(clusters, key=lambda c: -c["source_count"])
    print("\nTop clusters:")
    for c in clusters_sorted[:15]:
        anchor = c.get("dominant_entity")
        anchor_str = anchor.split(":", 1)[1] if anchor else "no-entity"
        beat = c.get("beat") or (None, None, None)
        beat_str = "{}>{}>{}".format(beat[0] or "_", beat[1] or "_", beat[2] or "_")
        print(
            "  {:4d}  {}  {}  [{}]".format(
                c["source_count"], c["date"], beat_str[:50], anchor_str[:30]
            )
        )

    if dry_run:
        print("\nDRY RUN -- no database changes. Use --write to apply.")
        conn.close()
        return

    print("\nWiping existing events for CTM {}...".format(ctm_id))
    _wipe_ctm_events(conn, ctm_id)
    written = write_clusters_to_db(conn, clusters, ctm_id)
    conn.commit()
    print("  Created: {} new events".format(written))
    conn.close()


# =============================================================================
# MAIN (CLI)
# =============================================================================


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="D-056 day-beat clustering")
    parser.add_argument("--ctm-id", required=True, help="CTM ID to process")
    parser.add_argument(
        "--write", action="store_true", help="Apply changes (default: dry run)"
    )
    args = parser.parse_args()
    recluster_ctm(args.ctm_id, dry_run=not args.write)
