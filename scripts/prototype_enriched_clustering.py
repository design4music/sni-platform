"""
Prototype: Enriched clustering (all labels within buckets) + mechanical titles

Same bucketed approach as production Phase 4, but _extract_tokens uses ALL
title_labels fields (actor, target, action_class, subject, sector) plus
the existing entity signals (persons, orgs, places, etc.).

Also generates mechanical titles from aggregated labels.

Usage:
    python scripts/prototype_enriched_clustering.py AMERICAS-USA geo_politics --dry-run
    python scripts/prototype_enriched_clustering.py AMERICAS-USA geo_politics --write
"""

import argparse
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import (
    HIGH_FREQ_ORGS,
    HIGH_FREQ_PERSONS,
    SIGNAL_TYPES,
    config,
    get_track_discriminators,
)
from core.publisher_filter import filter_publisher_signals, load_publisher_patterns

# --- Config ---

MONTH = "2026-03-01"
ANCHOR_LOCK_THRESHOLD = 5
EMERGENCE_THRESHOLD = 3
JOIN_THRESHOLD = 0.25
MIN_BILATERAL_TITLES = 3

GEO_PREFIXES = (
    "AMERICAS-",
    "EUROPE-",
    "ASIA-",
    "AFRICA-",
    "MIDEAST-",
    "OCEANIA-",
)

# Structural labels to skip (too generic for clustering)
STRUCTURAL_SKIP = {
    "actor": {"NONE", "MEDIA_OUTLET", "MULTIPLE_STATES"},
    "target": {"NONE"},
    "subject": {"BILATERAL_RELATIONS"},
    "action_class": set(),
    "sector": set(),
}

# Weights for ALL signal types
WEIGHTS = {
    # Structural labels
    "actor": 1.5,
    "target": 2.0,
    "action_class": 1.0,
    "subject": 1.0,
    "sector": 0.3,
    # Entity signals
    "persons": 2.5,
    "orgs": 1.5,
    "places": 2.0,
    "commodities": 2.0,
    "policies": 2.0,
    "systems": 1.5,
    "named_events": 3.0,
}

STRUCTURAL_LABELS = ["actor", "target", "action_class", "subject", "sector"]


def is_geo_centroid(c):
    return any(c.startswith(p) for p in GEO_PREFIXES)


# --- IncrementalTopic with ALL labels ---


class IncrementalTopic:
    def __init__(self, seed_title, topic_id):
        self.id = topic_id
        self.titles = [seed_title]
        self.anchor_signals = set()
        self.anchors_locked = False
        self.signal_counts = Counter()
        self._add_signals(seed_title)

    def _extract_tokens(self, title, for_matching=False):
        tokens = set()

        # Entity signals (array fields)
        for sig_type in SIGNAL_TYPES:
            for val in title.get(sig_type, []):
                normalized = val.upper() if sig_type == "persons" else val
                if for_matching:
                    if sig_type == "persons" and normalized in HIGH_FREQ_PERSONS:
                        continue
                    if sig_type == "orgs" and normalized in HIGH_FREQ_ORGS:
                        continue
                tokens.add("%s:%s" % (sig_type, normalized))

        # Structural labels (scalar fields)
        for label_type in STRUCTURAL_LABELS:
            val = title.get(label_type)
            if not val:
                continue
            if "," in val:
                parts = [p.strip() for p in val.split(",")]
                for part in parts:
                    if for_matching and part in STRUCTURAL_SKIP.get(label_type, set()):
                        continue
                    tokens.add("%s:%s" % (label_type, part))
            else:
                if for_matching and val in STRUCTURAL_SKIP.get(label_type, set()):
                    continue
                tokens.add("%s:%s" % (label_type, val))

        return tokens

    def _add_signals(self, title):
        tokens = self._extract_tokens(title, for_matching=False)
        for token in tokens:
            self.signal_counts[token] += 1

        if not self.anchors_locked:
            threshold = max(1, len(self.titles) // 2)
            self.anchor_signals = set()
            for token, count in self.signal_counts.items():
                if count >= threshold:
                    sig_type, val = token.split(":", 1)
                    if sig_type == "persons" and val in HIGH_FREQ_PERSONS:
                        continue
                    if sig_type == "orgs" and val in HIGH_FREQ_ORGS:
                        continue
                    # Skip generic structural values from anchors too
                    if sig_type in STRUCTURAL_SKIP and val in STRUCTURAL_SKIP[sig_type]:
                        continue
                    self.anchor_signals.add(token)
            if len(self.titles) >= ANCHOR_LOCK_THRESHOLD:
                self.anchors_locked = True

    def add_title(self, title):
        self.titles.append(title)
        self._add_signals(title)

    def match_score(self, title, discriminators):
        title_tokens = self._extract_tokens(title, for_matching=True)
        if not title_tokens:
            return 0.0

        # Discriminator conflicts
        if self.anchors_locked and discriminators:
            for sig_type in discriminators:
                anchor_sigs = {
                    t for t in self.anchor_signals if t.startswith(sig_type + ":")
                }
                title_sigs = {t for t in title_tokens if t.startswith(sig_type + ":")}
                if anchor_sigs and title_sigs and not (anchor_sigs & title_sigs):
                    return 0.0

        # Specificity gate for large topics
        if self.anchors_locked and len(self.titles) >= 30:
            specific_types = {
                "places",
                "named_events",
                "commodities",
                "policies",
                "actor",
                "action_class",
            }
            has_specific = any(
                token in self.anchor_signals
                for token in title_tokens
                if token.split(":")[0] in specific_types
            )
            if not has_specific:
                frequent = {
                    t
                    for t, c in self.signal_counts.items()
                    if c >= len(self.titles) // 4 and t.split(":")[0] in specific_types
                }
                if frequent and not (title_tokens & frequent):
                    return 0.0

        compare_set = (
            self.anchor_signals
            if self.anchors_locked
            else set(self.signal_counts.keys())
        )
        if not compare_set:
            return 0.0

        overlap = title_tokens & compare_set
        if not overlap:
            return 0.0

        score = 0.0
        for token in overlap:
            sig_type = token.split(":")[0]
            weight = WEIGHTS.get(sig_type, 1.0)
            anchor_boost = 1.5 if token in self.anchor_signals else 1.0
            score += weight * anchor_boost

        max_score = sum(WEIGHTS.get(t.split(":")[0], 1.0) * 1.5 for t in compare_set)
        return score / max_score if max_score > 0 else 0.0

    def get_anchor_summary(self):
        anchor_list = [(t, self.signal_counts[t]) for t in self.anchor_signals]
        anchor_list.sort(key=lambda x: -x[1])
        parts = [t for t, _ in anchor_list[:6]]
        return ", ".join(parts) if parts else "misc"


# --- Mechanical title generation ---

MEDIA_ORGS = {
    "ABC",
    "CNN",
    "BBC",
    "POLITICO",
    "FOX",
    "X",
    "NEW_YORK_TIMES",
    "WASHINGTON_POST",
    "REUTERS",
    "AP",
    "GLOBAL_TIMES",
    "AL_JAZEERA",
    "ASSOCIATED_PRESS",
    "NPR",
    "MSNBC",
    "THE_GUARDIAN",
    "NEWSWEEK",
    "AFP",
    "SKY_NEWS",
    "RT",
}
GENERIC_ORGS = {"PENTAGON", "WHITE HOUSE", "CONGRESS", "SENATE", "HOUSE"}
GOOD_ORGS = {
    "ICE",
    "FBI",
    "IRGC",
    "HEZBOLLAH",
    "HAMAS",
    "MOSSAD",
    "NATO",
    "EU",
    "UN",
    "IDF",
}

ACTOR_READABLE = {
    "US_EXECUTIVE": "US",
    "US_ARMED_FORCES": "US military",
    "US_LAW_ENFORCEMENT": "US law enforcement",
    "US_LEGISLATURE": "US Congress",
    "IR_ARMED_FORCES": "Iran military",
    "IR_EXECUTIVE": "Iran",
    "IR_DIPLOMATIC": "Iran diplomats",
    "IR_LEGISLATURE": "Iran parliament",
    "RU_EXECUTIVE": "Russia",
    "CN_EXECUTIVE": "China",
    "IL_EXECUTIVE": "Israel",
    "CORPORATION": "Corporate",
    "MULTIPLE_STATES": "International",
    "FR_EXECUTIVE": "France",
    "DE_EXECUTIVE": "Germany",
    "UK_EXECUTIVE": "UK",
    "JP_EXECUTIVE": "Japan",
    "IN_EXECUTIVE": "India",
}

ACTION_PHRASES = {
    "MILITARY_OPERATION": "military action",
    "DIPLOMATIC_PRESSURE": "diplomatic pressure",
    "POLITICAL_PRESSURE": "political pressure",
    "LAW_ENFORCEMENT_OPERATION": "law enforcement",
    "SECURITY_INCIDENT": "security incident",
    "RESOURCE_ALLOCATION": "resource allocation",
    "POLICY_CHANGE": "policy change",
    "INFORMATION_INFLUENCE": "public statements",
    "INFRASTRUCTURE_DEVELOPMENT": "development",
    "STRATEGIC_REALIGNMENT": "strategic shift",
    "ALLIANCE_COORDINATION": "alliance coordination",
    "ECONOMIC_PRESSURE": "economic pressure",
    "MEDIATION": "mediation",
    "CAPABILITY_TRANSFER": "capability transfer",
    "REGULATORY_ACTION": "regulatory action",
}

SUBJECT_Q = {
    "NAVAL": "naval",
    "AERIAL": "air",
    "GROUND_FORCES": "ground",
    "MISSILE": "missile",
    "NUCLEAR": "nuclear",
    "TERRORISM": "terror",
    "BORDER_SECURITY": "border",
    "DEFENSE_POLICY": "defense",
    "ESPIONAGE": "intelligence",
    "TRADE": "trade",
    "ELECTION": "election",
    "LEGISLATION": "legislative",
    "ALLIANCE": "alliance",
    "SUPPLY_CHAIN": "supply chain",
    "ENERGY": "energy",
    "SEMICONDUCTORS": "semiconductor",
    "AI": "AI",
    "R_AND_D": "R&D",
    "PROTEST": "protest",
}

TARGET_NAMES = {
    "IR": "Iran",
    "US": "US",
    "IL": "Israel",
    "RU": "Russia",
    "CN": "China",
    "UA": "Ukraine",
    "NATO": "NATO",
    "KP": "N.Korea",
    "AF": "Afghanistan",
    "FR": "France",
    "DE": "Germany",
    "JP": "Japan",
    "IN": "India",
    "EU": "EU",
    "SY": "Syria",
    "CU": "Cuba",
}


def generate_mechanical_title(topic):
    """Generate a readable title from aggregated label signals."""
    actors, targets, actions, subjects = Counter(), Counter(), Counter(), Counter()
    places, persons, orgs = Counter(), Counter(), Counter()
    n = len(topic.titles)

    for t in topic.titles:
        a = t.get("actor", "")
        if a and a != "NONE":
            actors[a] += 1
        tgt = t.get("target", "")
        if tgt and tgt != "NONE":
            targets[tgt] += 1
        ac = t.get("action_class", "")
        if ac:
            actions[ac] += 1
        s = t.get("subject", "")
        if s:
            subjects[s] += 1
        for p in t.get("places", []):
            places[p] += 1
        for p in t.get("persons", []):
            persons[p.upper()] += 1
        for o in t.get("orgs", []):
            orgs[o] += 1

    min_share = max(2, n * 0.2)

    # Lead entity
    lead = None
    for p, cnt in persons.most_common(3):
        if p not in HIGH_FREQ_PERSONS and cnt >= min_share:
            lead = p.title()
            break
    if not lead:
        for o, cnt in orgs.most_common(5):
            if o in GOOD_ORGS and cnt >= min_share:
                lead = o
                break
    if not lead:
        for o, cnt in orgs.most_common(5):
            if o not in MEDIA_ORGS and o not in GENERIC_ORGS and cnt >= min_share:
                lead = o
                break
    if not lead:
        top_actor = actors.most_common(1)[0][0] if actors else None
        if top_actor:
            lead = ACTOR_READABLE.get(top_actor, top_actor.replace("_", " ").title())
    if not lead:
        lead = "Coverage"

    # Action + subject
    top_action = actions.most_common(1)[0][0] if actions else None
    action_phrase = ACTION_PHRASES.get(top_action, "")
    top_subject = subjects.most_common(1)[0][0] if subjects else None
    subject_q = SUBJECT_Q.get(top_subject, "")
    mid = ("%s %s" % (subject_q, action_phrase)).strip() or "activity"

    # Target
    top_target = targets.most_common(1)[0][0] if targets else None
    target_name = TARGET_NAMES.get(top_target, top_target) if top_target else None

    # Place (significant only)
    SKIP_PLACES = {"White House", "Mar-a-Lago", "Middle East", "Gulf", "MIDDLE_EAST"}
    top_place = None
    for p, cnt in places.most_common(3):
        if p not in SKIP_PLACES and cnt >= min_share:
            top_place = p
            break

    # Assemble
    parts = [lead + ":"]
    parts.append(mid)
    if target_name:
        parts.append("/ %s" % target_name)
    if top_place:
        parts.append("(%s)" % top_place)
    return " ".join(parts)


# --- Bucketing (same as production) ---


def bucket_titles(titles, home_centroid):
    domestic = []
    bilateral_raw = defaultdict(list)
    multilateral = []

    for title in titles:
        centroid_ids = title.get("centroid_ids", [])
        foreign_geo = [
            c for c in centroid_ids if c != home_centroid and is_geo_centroid(c)
        ]
        if not foreign_geo:
            domestic.append(title)
        elif len(foreign_geo) == 1:
            bilateral_raw[foreign_geo[0]].append(title)
        else:
            multilateral.append(title)

    bucket_sizes = {k: len(v) for k, v in bilateral_raw.items()}
    for title in multilateral:
        centroid_ids = title.get("centroid_ids", [])
        foreign_geo = [
            c for c in centroid_ids if c != home_centroid and is_geo_centroid(c)
        ]
        if foreign_geo:
            best = max(foreign_geo, key=lambda c: bucket_sizes.get(c, 0))
            bilateral_raw[best].append(title)
            bucket_sizes[best] = bucket_sizes.get(best, 0) + 1

    bilateral = {}
    other_international = []
    for centroid_id, ctitles in bilateral_raw.items():
        if len(ctitles) >= MIN_BILATERAL_TITLES:
            bilateral[centroid_id] = ctitles
        else:
            other_international.extend(ctitles)

    return {
        "domestic": domestic,
        "bilateral": bilateral,
        "other_international": other_international,
    }


def iterate_buckets(buckets):
    if buckets["domestic"]:
        yield "domestic", None, sorted(
            buckets["domestic"], key=lambda t: t["pubdate_utc"] or ""
        )
    for bk in sorted(buckets["bilateral"], key=lambda x: -len(buckets["bilateral"][x])):
        yield "bilateral", bk, sorted(
            buckets["bilateral"][bk], key=lambda t: t["pubdate_utc"] or ""
        )
    if buckets["other_international"]:
        yield "other_international", None, sorted(
            buckets["other_international"], key=lambda t: t["pubdate_utc"] or ""
        )


# --- Clustering ---


def cluster_bucket(titles, discriminators):
    topics = []
    topic_counter = 0
    for title in titles:
        best_topic = None
        best_score = JOIN_THRESHOLD
        for topic in topics:
            score = topic.match_score(title, discriminators)
            if score > best_score:
                best_score = score
                best_topic = topic
        if best_topic:
            best_topic.add_title(title)
        else:
            topic_counter += 1
            topics.append(IncrementalTopic(title, topic_counter))
    return topics


# --- DB ---


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def load_titles(conn, ctm_id):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT t.id, t.title_display, t.pubdate_utc, t.centroid_ids,
               t.detected_language,
               tl.actor, tl.target, tl.action_class, tl.subject,
               tl.sector,
               tl.persons, tl.orgs, tl.places, tl.commodities,
               tl.policies, tl.systems, tl.named_events,
               tl.importance_score
        FROM titles_v3 t
        JOIN title_assignments ta ON t.id = ta.title_id
        LEFT JOIN title_labels tl ON t.id = tl.title_id
        WHERE ta.ctm_id = %s
        ORDER BY t.pubdate_utc ASC
    """,
        (ctm_id,),
    )
    rows = cur.fetchall()
    cur.close()
    titles = []
    for r in rows:
        titles.append(
            {
                "id": str(r[0]),
                "title_display": r[1],
                "pubdate_utc": r[2],
                "centroid_ids": r[3] or [],
                "detected_language": r[4] or "en",
                "actor": r[5] or "",
                "target": r[6] or "",
                "action_class": r[7] or "",
                "subject": r[8] or "",
                "sector": r[9] or "",
                "persons": r[10] or [],
                "orgs": r[11] or [],
                "places": r[12] or [],
                "commodities": r[13] or [],
                "policies": r[14] or [],
                "systems": r[15] or [],
                "named_events": r[16] or [],
                "importance_score": r[17] or 0.0,
            }
        )
    return titles


def wipe_ctm_events(conn, ctm_id):
    cur = conn.cursor()
    cur.execute(
        "UPDATE events_v3 SET merged_into = NULL "
        "WHERE merged_into IN (SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (ctm_id,),
    )
    cur.execute("UPDATE events_v3 SET family_id = NULL WHERE ctm_id = %s", (ctm_id,))
    cur.execute("DELETE FROM event_families WHERE ctm_id = %s", (ctm_id,))
    cur.execute(
        "DELETE FROM event_v3_titles WHERE event_id IN "
        "(SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (ctm_id,),
    )
    cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))
    conn.commit()
    cur.close()


def write_results(conn, ctm_id, all_topics, all_catchall):
    cur = conn.cursor()
    written = 0

    for event_type, bucket_key, topic in all_topics:
        if len(topic.titles) < 2:
            all_catchall.append((event_type, bucket_key, topic.titles))
            continue

        event_id = str(uuid.uuid4())
        dates = [t["pubdate_utc"] for t in topic.titles if t["pubdate_utc"]]
        first_date = min(dates).date() if dates else None
        last_date = max(dates).date() if dates else None
        title = generate_mechanical_title(topic)
        if len(title) > 500:
            title = title[:497] + "..."

        cur.execute(
            """INSERT INTO events_v3
               (id, ctm_id, date, first_seen, title, event_type, bucket_key,
                source_batch_count, is_catchall, last_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, false, %s)""",
            (
                event_id,
                ctm_id,
                first_date,
                first_date,
                title,
                event_type,
                bucket_key,
                len(topic.titles),
                last_date,
            ),
        )
        for t in topic.titles:
            cur.execute(
                "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s) "
                "ON CONFLICT DO NOTHING",
                (event_id, t["id"]),
            )
        written += 1

    # Catchall per bucket
    ca_groups = defaultdict(list)
    for event_type, bucket_key, titles in all_catchall:
        ca_groups[(event_type, bucket_key)].extend(titles)

    for (event_type, bucket_key), titles in ca_groups.items():
        if not titles:
            continue
        ca_id = str(uuid.uuid4())
        dates = [t["pubdate_utc"] for t in titles if t["pubdate_utc"]]
        first_date = min(dates).date() if dates else None
        cur.execute(
            """INSERT INTO events_v3
               (id, ctm_id, date, first_seen, title, event_type, bucket_key,
                source_batch_count, is_catchall)
            VALUES (%s, %s, %s, %s, 'Other coverage', %s, %s, %s, true)""",
            (
                ca_id,
                ctm_id,
                first_date,
                first_date,
                event_type,
                bucket_key,
                len(titles),
            ),
        )
        for t in titles:
            cur.execute(
                "INSERT INTO event_v3_titles (event_id, title_id) VALUES (%s, %s) "
                "ON CONFLICT DO NOTHING",
                (ca_id, t["id"]),
            )

    conn.commit()
    cur.close()
    return written


# --- Main ---


def main():
    parser = argparse.ArgumentParser(
        description="Prototype: enriched clustering + mechanical titles"
    )
    parser.add_argument("centroid", help="Centroid ID")
    parser.add_argument("track", help="Track name")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--month", default=MONTH)
    args = parser.parse_args()

    if not args.dry_run and not args.write:
        print("Specify --dry-run or --write")
        sys.exit(1)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title_count FROM ctm WHERE centroid_id = %s AND track = %s AND month = %s",
        (args.centroid, args.track, args.month),
    )
    row = cur.fetchone()
    if not row:
        print("CTM not found")
        return
    ctm_id, title_count = str(row[0]), row[1]
    cur.close()

    print("=== ENRICHED CLUSTERING (all labels, within buckets) ===")
    print(
        "  %s / %s / %s (%d titles)"
        % (args.centroid, args.track, args.month, title_count)
    )

    titles = load_titles(conn, ctm_id)
    print("  Loaded %d titles" % len(titles))

    publisher_patterns = load_publisher_patterns(conn)
    for t in titles:
        t["orgs"] = filter_publisher_signals(t.get("orgs", []), publisher_patterns)

    discriminators = list(get_track_discriminators(args.track).keys())
    print("  Discriminators: %s" % discriminators)

    # Signal coverage
    has_actor = sum(1 for t in titles if t["actor"] and t["actor"] != "NONE")
    has_entity = sum(1 for t in titles if t["persons"] or t["orgs"] or t["places"])
    print(
        "  Coverage: actor=%d entity=%d (of %d)" % (has_actor, has_entity, len(titles))
    )

    # Bucket
    buckets = bucket_titles(titles, args.centroid)
    print("\n  Buckets:")
    print("    Domestic: %d" % len(buckets["domestic"]))
    for bk in sorted(buckets["bilateral"], key=lambda x: -len(buckets["bilateral"][x]))[
        :10
    ]:
        print("    Bilateral %s: %d" % (bk, len(buckets["bilateral"][bk])))
    if len(buckets["bilateral"]) > 10:
        print("    ... +%d more" % (len(buckets["bilateral"]) - 10))
    print("    Other intl: %d" % len(buckets["other_international"]))

    # Cluster within each bucket
    all_topics = []
    all_catchall = []
    total_emerged = 0
    total_single = 0

    print("\n  Clustering per bucket:")
    for event_type, bucket_key, bucket_titles_list in iterate_buckets(buckets):
        topics = cluster_bucket(bucket_titles_list, discriminators)
        emerged = [t for t in topics if len(t.titles) >= 2]
        singles = [t for t in topics if len(t.titles) == 1]

        label = event_type if not bucket_key else "bilateral %s" % bucket_key
        print(
            "    %-35s %4d titles -> %3d topics (%d emerged)"
            % (
                label,
                len(bucket_titles_list),
                len(topics),
                len(emerged),
            )
        )

        for topic in topics:
            all_topics.append((event_type, bucket_key, topic))
        total_emerged += len(emerged)
        total_single += len(singles)

    total_in = sum(len(t.titles) for _, _, t in all_topics if len(t.titles) >= 2)

    print("\n=== RESULTS ===")
    print("  %d emerged topics, %d single-title" % (total_emerged, total_single))
    print(
        "  %d titles in topics, %d catchall (%.1f%%)"
        % (
            total_in,
            total_single,
            100 * total_single / len(titles) if titles else 0,
        )
    )

    # Size distribution
    sizes = sorted(
        [len(t.titles) for _, _, t in all_topics if len(t.titles) >= 2], reverse=True
    )
    print("  Top 10 sizes: %s" % sizes[:10])

    # Show top topics with mechanical titles
    emerged_list = [(et, bk, t) for et, bk, t in all_topics if len(t.titles) >= 2]
    emerged_list.sort(key=lambda x: -len(x[2].titles))
    print("\n  Top 20 topics:")
    for i, (et, bk, topic) in enumerate(emerged_list[:20]):
        mech_title = generate_mechanical_title(topic)
        bk_label = bk or "domestic"
        print(
            "    %3d. %4d titles  %-20s %s"
            % (
                i + 1,
                len(topic.titles),
                bk_label,
                mech_title[:80],
            )
        )

    if args.dry_run:
        print("\nDRY RUN -- no DB changes.")
        conn.close()
        return

    print("\nWiping existing events for CTM %s..." % ctm_id[:8])
    wipe_ctm_events(conn, ctm_id)
    print("Writing %d topics..." % total_emerged)
    written = write_results(conn, ctm_id, all_topics, all_catchall)
    print("Wrote %d events + catchalls" % written)

    # Run family assembly
    print("\nRunning family assembly...")
    from pipeline.phase_4.assemble_families import process_ctm

    process_ctm(ctm_id=ctm_id, force=True)

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
