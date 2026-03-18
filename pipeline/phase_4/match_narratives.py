"""
Phase 4.2f: Match events to strategic narratives (mechanical, no LLM).

Two matching strategies, merged with dedup:

1. **CTM structural match** (high recall)
   - Uses the centroid/track/bucket graph: events assigned to narrative's
     actor_centroid in a matching track, with bilateral bucket pointing to
     a related centroid. No keyword/label matching needed.

2. **Label-based match** (cross-centroid reach)
   - Three hard gates: protagonist in labels, protagonist action class, 3+ keywords
   - Catches events filed under OTHER centroids that still involve the protagonist

Links events with confidence >= THRESHOLD.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2
from psycopg2.extras import Json, RealDictCursor, execute_values

from core.config import config

THRESHOLD = 0.55

# Keywords shorter than this are ignored (avoids "us", "ai", "UN" false positives)
MIN_KEYWORD_LEN = 3

# Map centroid suffixes to actor-label prefixes used in title_labels
CENTROID_TO_PREFIX = {
    "USA": "US",
    "CHINA": "CN",
    "RUSSIA": "RU",
    "UK": "UK",
    "IRAN": "IR",
    "ISRAEL": "IL",
    "INDIA": "IN",
    "JAPAN": "JP",
    "TURKEY": "TR",
    "SAUDI": "SA",
    "GERMANY": "DE",
    "FRANCE": "FR",
    "BRAZIL": "BR",
    "AUSTRALIA": "AU",
    "PAKISTAN": "PK",
    "CANADA": "CA",
    "KOREA": "KR",
    "SOUTHKOREA": "KR",
    "NORKOREA": "KP",
    "TAIWAN": "TW",
    "MEXICO": "MX",
    "NIGERIA": "NG",
    "SOUTHAFRICA": "ZA",
    "UKRAINE": "UA",
    "BELARUS": "BY",
    "PALESTINE": "PS",
    "ETHIOPIA": "ET",
    "KENYA": "KE",
    "DRC": "CD",
    "MONGOLIA": "MN",
    "HONGKONG": "HK",
    "NEWZEALAND": "NZ",
    "PAPUANEWGUINEA": "PG",
    "VENEZUELA": "VE",
    "CUBA": "CU",
    "COLOMBIA": "CO",
    "EU": "EU",
    "NATO": "NATO",
}

# Map narrative domains to geo_* track names
DOMAIN_TO_TRACK = {
    "SECURITY": "geo_security",
    "FOREIGN_POLICY": "geo_politics",
    "ECONOMY": "geo_economy",
    "ENERGY": "geo_energy",
    "HUMANITARIAN": "geo_humanitarian",
    "INFORMATION": "geo_information",
    "GOVERNANCE": "geo_politics",
    "TECHNOLOGY": "geo_economy",
    "MEDIA": "geo_information",
    "SOCIETY": "geo_politics",
}

# Map actor-label prefixes back to centroid IDs (reverse of CENTROID_TO_PREFIX)
# Built at module load from CENTROID_TO_PREFIX + manual additions
PREFIX_TO_CENTROID = {
    "US": "AMERICAS-USA",
    "CN": "ASIA-CHINA",
    "RU": "EUROPE-RUSSIA",
    "UK": "EUROPE-UK",
    "IR": "MIDEAST-IRAN",
    "IL": "MIDEAST-ISRAEL",
    "IN": "ASIA-INDIA",
    "JP": "ASIA-JAPAN",
    "TR": "MIDEAST-TURKEY",
    "SA": "MIDEAST-SAUDI",
    "DE": "EUROPE-GERMANY",
    "FR": "EUROPE-FRANCE",
    "BR": "AMERICAS-BRAZIL",
    "AU": "OCEANIA-AUSTRALIA",
    "PK": "ASIA-PAKISTAN",
    "CA": "AMERICAS-CANADA",
    "KR": "ASIA-SOUTHKOREA",
    "KP": "ASIA-NORKOREA",
    "TW": "ASIA-TAIWAN",
    "MX": "AMERICAS-MEXICO",
    "NG": "AFRICA-NIGERIA",
    "ZA": "AFRICA-SOUTHAFRICA",
    "UA": "EUROPE-UKRAINE",
    "BY": "EUROPE-BELARUS",
    "PS": "MIDEAST-PALESTINE",
    "ET": "AFRICA-ETHIOPIA",
    "KE": "AFRICA-KENYA",
    "CD": "AFRICA-DRC",
    "VE": "AMERICAS-VENEZUELA",
    "CU": "AMERICAS-CUBA",
    "EU": "NON-STATE-EU",
    "NATO": "NON-STATE-NATO",
    "HU": "EUROPE-VISEGRAD",
    "MN": "ASIA-MONGOLIA",
    "HK": "ASIA-HONGKONG",
}


# Map common country/org names in keywords to centroid IDs
KEYWORD_TO_CENTROID = {
    "ukraine": "EUROPE-UKRAINE",
    "russia": "EUROPE-RUSSIA",
    "china": "ASIA-CHINA",
    "iran": "MIDEAST-IRAN",
    "israel": "MIDEAST-ISRAEL",
    "india": "ASIA-INDIA",
    "japan": "ASIA-JAPAN",
    "turkey": "MIDEAST-TURKEY",
    "saudi": "MIDEAST-SAUDI",
    "germany": "EUROPE-GERMANY",
    "france": "EUROPE-FRANCE",
    "canada": "AMERICAS-CANADA",
    "brazil": "AMERICAS-BRAZIL",
    "pakistan": "ASIA-PAKISTAN",
    "taiwan": "ASIA-TAIWAN",
    "korea": "ASIA-SOUTHKOREA",
    "australia": "OCEANIA-AUSTRALIA",
    "mexico": "AMERICAS-MEXICO",
    "nato": "NON-STATE-NATO",
    "european union": "NON-STATE-EU",
    "eu ": "NON-STATE-EU",
    "hezbollah": "MIDEAST-LEBANON",
    "hamas": "MIDEAST-PALESTINE",
    "houthi": "MIDEAST-YEMEN",
    "cuba": "AMERICAS-CUBA",
    "venezuela": "AMERICAS-VENEZUELA",
    "donbas": "EUROPE-UKRAINE",
    "crimea": "EUROPE-UKRAINE",
    "kyiv": "EUROPE-UKRAINE",
    "palestine": "MIDEAST-PALESTINE",
    "gaza": "MIDEAST-PALESTINE",
    "arctic": "EUROPE-NORDIC",
    "greenland": "EUROPE-NORDIC",
    "sahel": "AFRICA-SAHEL",
    "mali": "AFRICA-SAHEL",
    "niger": "AFRICA-SAHEL",
    "burkina": "AFRICA-SAHEL",
    "chad": "AFRICA-SAHEL",
    "africa": "AFRICA-WEST",
    "nigeria": "AFRICA-NIGERIA",
    "kenya": "AFRICA-KENYA",
    "ethiopia": "AFRICA-ETHIOPIA",
    "south africa": "AFRICA-SOUTHAFRICA",
    "congo": "AFRICA-DRC",
    "somalia": "AFRICA-HORN",
    "al-shabaab": "AFRICA-HORN",
    "syria": "MIDEAST-LEVANT",
    "lebanon": "MIDEAST-LEVANT",
    "iraq": "MIDEAST-LEVANT",
    "yemen": "MIDEAST-YEMEN",
    "afghanistan": "ASIA-AFGHANISTAN",
    "taliban": "ASIA-AFGHANISTAN",
    "kashmir": "ASIA-INDIA",
    "xinjiang": "ASIA-CHINA",
    "hong kong": "ASIA-HONGKONG",
    "south china sea": "ASIA-SOUTHEAST",
    "asean": "ASIA-SOUTHEAST",
    "balkans": "EUROPE-BALKANS",
    "serbia": "EUROPE-BALKANS",
    "kosovo": "EUROPE-BALKANS",
    "baltic": "EUROPE-BALTIC",
    "hungary": "EUROPE-VISEGRAD",
    "orban": "EUROPE-VISEGRAD",
    "mercosur": "AMERICAS-SOUTHERNCONE",
    "argentina": "AMERICAS-SOUTHERNCONE",
}


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def _derive_protagonist_prefix(actor_centroid, actor_prefixes=None):
    """Derive the protagonist actor-label prefix from centroid id."""
    if not actor_centroid:
        return None
    suffix = actor_centroid.split("-")[-1]
    if suffix in CENTROID_TO_PREFIX:
        return CENTROID_TO_PREFIX[suffix]
    if len(suffix) == 2:
        return suffix
    if actor_prefixes and len(actor_prefixes) == 1:
        return actor_prefixes[0]
    return None


def load_narratives(cur):
    """Load active strategic narratives with protagonist prefix and related centroids."""
    cur.execute(
        """
        SELECT id, keywords, action_classes, actor_prefixes, actor_types, domains,
               actor_centroid, related_centroids
        FROM strategic_narratives
        WHERE is_active = true
        """
    )
    rows = cur.fetchall()
    narratives = []
    for r in rows:
        raw_kw = r["keywords"] or []
        keywords = set(k.lower() for k in raw_kw if len(k) >= MIN_KEYWORD_LEN)
        prefixes = list(r["actor_prefixes"] or [])
        protagonist = _derive_protagonist_prefix(r["actor_centroid"], prefixes)

        # Derive related centroids from non-protagonist prefixes
        related = set(r["related_centroids"] or [])
        for p in prefixes:
            if p != protagonist and p in PREFIX_TO_CENTROID:
                related.add(PREFIX_TO_CENTROID[p])

        # Also derive from keywords that name countries/orgs
        for kw in r["keywords"] or []:
            kw_upper = kw.upper().replace(" ", "")
            if kw_upper in CENTROID_TO_PREFIX:
                cent_id = PREFIX_TO_CENTROID.get(CENTROID_TO_PREFIX[kw_upper])
                if cent_id and cent_id != r["actor_centroid"]:
                    related.add(cent_id)
            # Direct keyword -> centroid for common names
            kw_lower = kw.lower()
            for name, cent in KEYWORD_TO_CENTROID.items():
                if name in kw_lower and cent != r["actor_centroid"]:
                    related.add(cent)

        # Map domains to track names
        tracks = set()
        for d in r["domains"] or []:
            if d in DOMAIN_TO_TRACK:
                tracks.add(DOMAIN_TO_TRACK[d])

        narratives.append(
            {
                "id": r["id"],
                "keywords": keywords,
                "action_classes": set(r["action_classes"] or []),
                "actor_prefixes": prefixes,
                "actor_types": set(r["actor_types"] or []),
                "domains": set(r["domains"] or []),
                "protagonist": protagonist,
                "is_regional": protagonist is None,
                "actor_centroid": r["actor_centroid"],
                "related_centroids": related,
                "tracks": tracks,
            }
        )
    return narratives


# ── Strategy 1: CTM structural match ──────────────────────────────


def ctm_structural_match(cur, narratives):
    """Find events by centroid + track + bilateral bucket.

    For each narrative with an actor_centroid:
      - Grab events from that centroid in matching tracks
      - Filter to bilateral events whose bucket_key is a related centroid
      - Also include domestic events (they're about the protagonist's own actions)
    """
    links = {}  # (event_id, narrative_id) -> (confidence, signals)

    for nar in narratives:
        if not nar["actor_centroid"] or not nar["tracks"]:
            continue

        track_list = list(nar["tracks"])
        related = list(nar["related_centroids"])

        # Posture narrative: single-country, no related centroids.
        # Grab events from protagonist's centroid in matching tracks,
        # but require at least 1 keyword hit in title+summary to filter noise.
        if not related:
            if not nar["keywords"]:
                continue
            cur.execute(
                """
                SELECT e.id AS event_id, e.title, e.summary, e.bucket_key, c.centroid_id
                FROM events_v3 e
                JOIN ctm c ON c.id = e.ctm_id
                WHERE c.centroid_id = %s
                  AND c.track = ANY(%s)
                  AND e.merged_into IS NULL
                  AND e.is_catchall = false
                  AND e.title IS NOT NULL
                """,
                [nar["actor_centroid"], track_list],
            )
            for ev in cur.fetchall():
                text = ((ev["title"] or "") + " " + (ev["summary"] or "")).lower()
                matched = []
                for kw in nar["keywords"]:
                    if " " in kw:
                        if all(w in text for w in kw.split()):
                            matched.append(kw)
                    elif kw in text:
                        matched.append(kw)
                if matched:
                    key = (ev["event_id"], nar["id"])
                    links[key] = (
                        0.70,
                        {
                            "method": "ctm_posture",
                            "centroid": ev["centroid_id"],
                            "bucket": ev["bucket_key"],
                            "matched_keywords": matched,
                        },
                    )
            continue

        # Forward: protagonist centroid -> bilateral with related
        cur.execute(
            """
            SELECT e.id AS event_id, e.title, e.bucket_key, c.centroid_id
            FROM events_v3 e
            JOIN ctm c ON c.id = e.ctm_id
            WHERE c.centroid_id = %s
              AND c.track = ANY(%s)
              AND e.merged_into IS NULL
              AND e.is_catchall = false
              AND e.title IS NOT NULL
              AND e.bucket_key = ANY(%s)
            """,
            [nar["actor_centroid"], track_list, related],
        )
        for ev in cur.fetchall():
            key = (ev["event_id"], nar["id"])
            links[key] = (
                0.85,
                {
                    "method": "ctm_structural",
                    "centroid": ev["centroid_id"],
                    "bucket": ev["bucket_key"],
                },
            )

        # Reverse: related centroids -> bilateral with protagonist
        cur.execute(
            """
            SELECT e.id AS event_id, e.title, e.bucket_key, c.centroid_id
            FROM events_v3 e
            JOIN ctm c ON c.id = e.ctm_id
            WHERE c.centroid_id = ANY(%s)
              AND c.track = ANY(%s)
              AND e.merged_into IS NULL
              AND e.is_catchall = false
              AND e.title IS NOT NULL
              AND e.bucket_key = %s
            """,
            [related, track_list, nar["actor_centroid"]],
        )
        for ev in cur.fetchall():
            key = (ev["event_id"], nar["id"])
            if key not in links:
                links[key] = (
                    0.80,
                    {
                        "method": "ctm_reverse",
                        "centroid": ev["centroid_id"],
                        "bucket": ev["bucket_key"],
                    },
                )

    return links


# ── Strategy 2: Label-based match ─────────────────────────────────


def _fetch_events(cur, batch_size, all_events=False):
    """Fetch events with per-actor action+domain pairs for label matching."""
    where_unlinked = (
        ""
        if all_events
        else """
        AND NOT EXISTS (
            SELECT 1 FROM event_strategic_narratives esn WHERE esn.event_id = e.id
        )"""
    )
    cur.execute(
        """
        SELECT
            e.id AS event_id,
            e.tags,
            e.title,
            e.summary,
            ARRAY_AGG(DISTINCT tl.actor) FILTER (WHERE tl.actor IS NOT NULL) AS actors,
            ARRAY_AGG(DISTINCT tl.action_class) FILTER (WHERE tl.action_class IS NOT NULL) AS action_classes,
            ARRAY_AGG(DISTINCT tl.domain) FILTER (WHERE tl.domain IS NOT NULL) AS domains,
            ARRAY_AGG(DISTINCT tl.actor || '::' || tl.action_class)
                FILTER (WHERE tl.actor IS NOT NULL AND tl.action_class IS NOT NULL) AS actor_actions
        FROM events_v3 e
        JOIN event_v3_titles evt ON evt.event_id = e.id
        JOIN title_labels tl ON tl.title_id = evt.title_id
        WHERE e.is_catchall = false
        """
        + where_unlinked
        + """
        GROUP BY e.id
        LIMIT %s
        """,
        (batch_size,),
    )
    return cur.fetchall()


def _build_event_text(event):
    """Build a lowercase text blob from tags + title + summary for keyword matching."""
    parts = []
    for tag in event["tags"] or []:
        parts.append(tag.lower())
    if event["title"]:
        parts.append(event["title"].lower())
    if event.get("summary"):
        parts.append(event["summary"].lower())
    return " ".join(parts)


def score_event(event, narrative, event_text=None):
    """Label-based scoring with three hard gates."""
    signals = {}

    actors = event["actors"] or []
    actor_actions = set(event["actor_actions"] or [])
    protagonist = narrative["protagonist"]

    # --- Protagonist gate ---
    protagonist_present = False
    if protagonist:
        for actor in actors:
            if actor and (actor == protagonist or actor.startswith(protagonist + "_")):
                protagonist_present = True
                break
    else:
        # Regional: require at least one prefix in event labels
        if narrative["actor_prefixes"]:
            for prefix in narrative["actor_prefixes"]:
                for actor in actors:
                    if actor and (actor == prefix or actor.startswith(prefix + "_")):
                        protagonist_present = True
                        break
                if protagonist_present:
                    break
        else:
            protagonist_present = True
    signals["protagonist"] = protagonist_present

    if not protagonist_present:
        return 0.0, signals

    # --- Protagonist action match ---
    action_score = 0.0
    if narrative["action_classes"] and protagonist:
        protagonist_actions = set()
        for aa in actor_actions:
            parts = aa.split("::", 1)
            if len(parts) == 2 and (
                parts[0] == protagonist or parts[0].startswith(protagonist + "_")
            ):
                protagonist_actions.add(parts[1])
        if protagonist_actions:
            overlap = len(protagonist_actions & narrative["action_classes"])
            if overlap > 0:
                ratio = overlap / len(narrative["action_classes"])
                action_score = min(1.0, ratio * 2)
        signals["protagonist_actions"] = sorted(protagonist_actions)
    elif narrative["action_classes"]:
        event_actions = set(event["action_classes"] or [])
        if event_actions:
            overlap = len(event_actions & narrative["action_classes"])
            ratio = overlap / len(narrative["action_classes"])
            action_score = min(1.0, ratio * 2)
    signals["action_class"] = round(action_score, 3)

    # --- Keyword match ---
    # Multi-word keywords ("Russia threat") match if ALL words are present.
    # Minimum hits scale with keyword set size: at least 30% of keywords
    # must match, with a floor of 2.
    kw_score = 0.0
    if narrative["keywords"]:
        if event_text is None:
            event_text = _build_event_text(event)
        matched = []
        for kw in narrative["keywords"]:
            if " " in kw:
                if all(w in event_text for w in kw.split()):
                    matched.append(kw)
            else:
                if kw in event_text:
                    matched.append(kw)
        min_hits = max(2, round(len(narrative["keywords"]) * 0.3))
        if len(matched) >= min_hits:
            ratio = len(matched) / len(narrative["keywords"])
            kw_score = min(1.0, ratio * 3)
        signals["matched_keywords"] = matched
    signals["keyword"] = round(kw_score, 3)

    # --- Domain overlap ---
    domain_score = 0.0
    event_domains = set(event["domains"] or [])
    if narrative["domains"] and event_domains:
        domain_score = 1.0 if event_domains & narrative["domains"] else 0.0
    signals["domain"] = round(domain_score, 3)

    # --- Hard gates ---
    if narrative["keywords"] and kw_score == 0:
        return 0.0, signals
    if protagonist and narrative["action_classes"] and action_score == 0:
        return 0.0, signals

    confidence = 0.40 * kw_score + 0.35 * action_score + 0.25 * domain_score
    signals["method"] = "label_match"
    return round(confidence, 4), signals


def label_based_match(events, narratives):
    """Score events against narratives using labels/keywords."""
    links = {}
    for ev in events:
        event_text = _build_event_text(ev)
        for nar in narratives:
            conf, sigs = score_event(ev, nar, event_text)
            if conf >= THRESHOLD:
                key = (ev["event_id"], nar["id"])
                links[key] = (conf, sigs)
    return links


# ── Main: merge both strategies ───────────────────────────────────


def match_events(batch_size=2000, dry_run=False, rescore=False):
    """Match events to active strategic narratives. Returns link count."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            narratives = load_narratives(cur)
            if not narratives:
                print("No active strategic narratives -- skipping")
                return 0

            n_regional = sum(1 for n in narratives if n["is_regional"])
            print(
                "Loaded %d narratives (%d regional, %d with protagonist)"
                % (len(narratives), n_regional, len(narratives) - n_regional)
            )

            if rescore:
                cur.execute("SELECT COUNT(*) FROM event_strategic_narratives")
                old_count = cur.fetchone()["count"]
                print("Rescore mode: clearing %d existing links" % old_count)
                cur.execute("DELETE FROM event_strategic_narratives")
                conn.commit()

            # Strategy 1: CTM structural
            ctm_links = ctm_structural_match(cur, narratives)
            print("CTM structural: %d candidate links" % len(ctm_links))

            # Strategy 2: Label-based
            events = _fetch_events(cur, batch_size, all_events=rescore)
            if events:
                print("Label matching: scoring %d events..." % len(events))
                lbl_links = label_based_match(events, narratives)
                print("Label match: %d candidate links" % len(lbl_links))
            else:
                lbl_links = {}

            # Merge: keep higher confidence when both match
            merged = dict(ctm_links)
            for key, (conf, sigs) in lbl_links.items():
                if key not in merged or conf > merged[key][0]:
                    merged[key] = (conf, sigs)

            print("Merged: %d unique links" % len(merged))

            if dry_run or not merged:
                return len(merged)

            rows = [
                (eid, nid, conf, Json(sigs))
                for (eid, nid), (conf, sigs) in merged.items()
            ]
            execute_values(
                cur,
                """
                INSERT INTO event_strategic_narratives (event_id, narrative_id, confidence, matched_signals)
                VALUES %s
                ON CONFLICT DO NOTHING
                """,
                rows,
                page_size=500,
            )
            conn.commit()
            print("Inserted %d event-narrative links" % len(rows))
            return len(rows)
    finally:
        conn.close()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    rescore = "--rescore" in sys.argv
    batch = 50000 if rescore else 2000
    match_events(batch_size=batch, dry_run=dry, rescore=rescore)
