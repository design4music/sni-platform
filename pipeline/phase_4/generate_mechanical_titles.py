"""
Phase 4.1a: Mechanical Title Generation

Generates readable titles for clusters from aggregated title_labels signals.
No LLM calls. Titles are functional (good for Dice merge) not polished.

Clusters with N+ English titles get the most central English headline.
Small/non-English clusters get a signal-template title.

Pipeline position: after Phase 4.1 (family assembly), before Phase 4.1b (Dice merge).

Usage:
    python pipeline/phase_4/generate_mechanical_titles.py --ctm-id <uuid>
    python pipeline/phase_4/generate_mechanical_titles.py --centroid AMERICAS-USA --track geo_security
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import config

# --- Config ---

# Clusters with this many+ English titles use central headline selection
CENTRAL_TITLE_MIN_ENGLISH = 3

STOP_WORDS = frozenset(
    "the a an in of on for to and is are was were with from at by as its it be "
    "has had have that this or but not no new over after into about up out more "
    "says said will could would may amid us set than been also".split()
)

# --- Signal-to-text mappings ---

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
    "KYODO",
    "YONHAP",
    "XINHUA",
    "TASS",
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
    "CENTCOM",
}
UBIQ_PERSONS = {"TRUMP", "BIDEN", "PUTIN", "XI", "ZELENSKY"}

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
    "AU_EXECUTIVE": "Australia",
    "KR_EXECUTIVE": "South Korea",
    "SA_EXECUTIVE": "Saudi Arabia",
    "TR_EXECUTIVE": "Turkey",
    "PK_EXECUTIVE": "Pakistan",
}

ACTION_PHRASES = {
    "MILITARY_OPERATION": "military action",
    "PRESSURE": "pressure",
    "LAW_ENFORCEMENT_OPERATION": "law enforcement",
    "SECURITY_INCIDENT": "security incident",
    "NATURAL_EVENT": "natural event",
    "MARKET_SHOCK": "market shock",
    "RESOURCE_ALLOCATION": "resource allocation",
    "POLICY_CHANGE": "policy change",
    "ELECTORAL_EVENT": "election",
    "STATEMENT": "statement",
    "INFORMATION_INFLUENCE": "influence operation",
    "INFRASTRUCTURE_DEVELOPMENT": "development",
    "STRATEGIC_REALIGNMENT": "strategic shift",
    "ALLIANCE_COORDINATION": "coordination",
    "ECONOMIC_PRESSURE": "economic pressure",
    "COMMERCIAL_TRANSACTION": "commercial deal",
    "CAPABILITY_TRANSFER": "capability transfer",
    "REGULATORY_ACTION": "regulatory action",
    "CIVIL_ACTION": "civil action",
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
    "SUMMIT": "summit",
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
    "VE": "Venezuela",
    "BR": "Brazil",
    "MX": "Mexico",
    "SA": "Saudi Arabia",
    "TR": "Turkey",
    "PK": "Pakistan",
    "KR": "South Korea",
    "AU": "Australia",
}

SKIP_PLACES = {
    "White House",
    "Mar-a-Lago",
    "Middle East",
    "Gulf",
    "MIDDLE_EAST",
    "Capitol Hill",
}


# --- Title generation ---


def tokenize(text):
    words = set(re.findall(r"[a-z][a-z0-9]+", (text or "").lower()))
    return words - STOP_WORDS


def pick_central_headline(titles_with_lang):
    """Pick the most representative English title by word frequency centrality."""
    all_words = Counter()
    title_data = []
    for title_text, lang in titles_with_lang:
        words = tokenize(title_text)
        title_data.append((title_text, words, lang))
        all_words.update(words)

    if not title_data:
        return None

    best_score = -1
    best_title = None

    for title_text, words, lang in title_data:
        if not words:
            continue
        lang_boost = 1.0 if lang == "en" else 0.3
        score = sum(all_words[w] for w in words) / len(words) * lang_boost
        if score > best_score:
            best_score = score
            best_title = title_text

    return best_title


def generate_signal_title(actors, targets, actions, subjects, places, persons, orgs, n):
    """Generate title from aggregated label signals."""
    min_share = max(2, n * 0.2)

    # Lead entity: person > good_org > other_org > actor
    lead = None
    for p, cnt in persons.most_common(3):
        if p not in UBIQ_PERSONS and cnt >= min_share:
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

    # Place
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


# --- DB operations ---


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def get_ctm_info(conn, ctm_id=None, centroid=None, track=None):
    cur = conn.cursor()
    if ctm_id:
        cur.execute(
            "SELECT id, centroid_id, track, month, title_count "
            "FROM ctm WHERE id = %s",
            (ctm_id,),
        )
    else:
        cur.execute(
            "SELECT id, centroid_id, track, month, title_count "
            "FROM ctm WHERE centroid_id = %s AND track = %s "
            "ORDER BY month DESC LIMIT 1",
            (centroid, track),
        )
    row = cur.fetchone()
    cur.close()
    if not row:
        return None
    return {
        "id": row[0],
        "centroid_id": row[1],
        "track": row[2],
        "month": row[3],
        "title_count": row[4],
    }


def process_ctm(ctm_id=None, centroid=None, track=None, force=False):
    """Generate mechanical titles for all clusters in a CTM.

    Only overwrites titles that are NULL or were previously generated
    mechanically (starts with a known actor pattern). Preserves LLM titles
    unless force=True.

    Returns number of titles generated.
    """
    conn = get_connection()
    try:
        ctm = get_ctm_info(conn, ctm_id, centroid, track)
        if not ctm:
            print("CTM not found")
            return 0

        ctm_id_str = str(ctm["id"])
        print("=== Mechanical Title Generation ===")
        print("  %s / %s / %s" % (ctm["centroid_id"], ctm["track"], ctm["month"]))

        cur = conn.cursor()

        # Get all non-catchall, non-merged clusters
        if force:
            cur.execute(
                """SELECT id, title, source_batch_count
                   FROM events_v3
                   WHERE ctm_id = %s AND NOT is_catchall AND merged_into IS NULL
                   ORDER BY source_batch_count DESC""",
                (ctm_id_str,),
            )
        else:
            # Only clusters without titles
            cur.execute(
                """SELECT id, title, source_batch_count
                   FROM events_v3
                   WHERE ctm_id = %s AND NOT is_catchall AND merged_into IS NULL
                     AND (title IS NULL OR title = '')
                   ORDER BY source_batch_count DESC""",
                (ctm_id_str,),
            )

        clusters = cur.fetchall()
        if not clusters:
            print("  No clusters need titles")
            cur.close()
            return 0

        print("  %d clusters to process" % len(clusters))

        generated = 0
        central = 0

        for event_id, existing_title, src_count in clusters:
            # Load title texts + languages for central headline selection
            cur.execute(
                """SELECT t.title_display, t.detected_language
                   FROM event_v3_titles et
                   JOIN titles_v3 t ON t.id = et.title_id
                   WHERE et.event_id = %s""",
                (str(event_id),),
            )
            title_rows = cur.fetchall()

            # Count English titles
            en_titles = [(r[0], r[1]) for r in title_rows if (r[1] or "en") == "en"]

            # Strategy: central headline if enough English titles, else signal template
            new_title = None

            if len(en_titles) >= CENTRAL_TITLE_MIN_ENGLISH:
                new_title = pick_central_headline(title_rows)
                if new_title:
                    central += 1

            if not new_title:
                # Load labels for signal template
                cur.execute(
                    """SELECT tl.actor, tl.target, tl.action_class, tl.subject,
                              tl.places, tl.persons, tl.orgs
                       FROM event_v3_titles et
                       JOIN title_labels tl ON tl.title_id = et.title_id
                       WHERE et.event_id = %s""",
                    (str(event_id),),
                )
                label_rows = cur.fetchall()

                actors, targets, actions, subjects = (
                    Counter(),
                    Counter(),
                    Counter(),
                    Counter(),
                )
                places, persons, orgs = Counter(), Counter(), Counter()

                for r in label_rows:
                    if r[0] and r[0] != "NONE":
                        actors[r[0]] += 1
                    if r[1] and r[1] != "NONE":
                        targets[r[1]] += 1
                    if r[2]:
                        actions[r[2]] += 1
                    if r[3]:
                        subjects[r[3]] += 1
                    for p in r[4] or []:
                        places[p] += 1
                    for p in r[5] or []:
                        persons[p.upper()] += 1
                    for o in r[6] or []:
                        orgs[o] += 1

                new_title = generate_signal_title(
                    actors,
                    targets,
                    actions,
                    subjects,
                    places,
                    persons,
                    orgs,
                    len(label_rows),
                )

            if new_title:
                if len(new_title) > 500:
                    new_title = new_title[:497] + "..."
                cur.execute(
                    "UPDATE events_v3 SET title = %s WHERE id = %s",
                    (new_title, str(event_id)),
                )
                generated += 1

        conn.commit()
        cur.close()
        print(
            "  Generated %d titles (%d central headline, %d signal template)"
            % (
                generated,
                central,
                generated - central,
            )
        )
        return generated
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 4.1a: Mechanical Title Generation"
    )
    parser.add_argument("--ctm-id", type=str, help="CTM ID")
    parser.add_argument("--centroid", type=str, help="Centroid ID")
    parser.add_argument("--track", type=str, help="Track name")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing titles"
    )
    args = parser.parse_args()

    if not args.ctm_id and not (args.centroid and args.track):
        print("ERROR: provide --ctm-id or --centroid + --track")
        sys.exit(1)

    result = process_ctm(
        ctm_id=args.ctm_id,
        centroid=args.centroid,
        track=args.track,
        force=args.force,
    )
    print("\nDone. %d titles generated." % result)
