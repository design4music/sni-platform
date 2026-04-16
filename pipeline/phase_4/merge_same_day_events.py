"""Phase 4.0b: Same-day event merge (post-clustering, pre-promotion).

Merges fragmented events within the same (ctm_id, date) using a hybrid
of entity overlap and title-word Dice similarity. Biggest absorbs smaller.
Runs after Phase 4 clustering and before Phase 4.5a promotion.

No LLM calls. Pure mechanical merge based on title_labels signals.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import config

DICE_THRESHOLD = 0.4
MIN_SHARED_ENTITIES = 1

STOP_WORDS = frozenset(
    "the a an in on of to for and or is are was were with by at from as that "
    "this it its be has have had not but after over says said could new us s t "
    "will during about between into than more out up no may".split()
)

HIGH_FREQ_ENTITIES = frozenset(
    {"TRUMP", "BIDEN", "NATO", "UN", "EU", "PUTIN", "NETANYAHU", "KHAMENEI"}
)


def get_conn():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def _title_words(text):
    if not text:
        return set()
    words = set()
    for w in text.lower().split():
        w = w.strip(".,;:!?\"'()[]{}|-")
        if w and len(w) > 1 and w not in STOP_WORDS:
            words.add(w)
    return words


def _dice(a, b):
    if not a or not b:
        return 0
    return 2 * len(a & b) / (len(a) + len(b))


def load_events_with_signals(conn, ctm_id):
    """Load all events for CTM with their entity signals, grouped by date."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT e.id::text, e.date, e.title, e.source_batch_count
          FROM events_v3 e
         WHERE e.ctm_id = %s AND e.merged_into IS NULL AND e.is_catchall = false
         ORDER BY e.date, e.source_batch_count DESC
        """,
        (ctm_id,),
    )
    events_by_date = {}
    all_events = []
    for eid, date, title, src in cur.fetchall():
        ev = {
            "id": eid,
            "date": date,
            "title": title,
            "src": src,
            "title_words": _title_words(title),
        }
        all_events.append(ev)
        events_by_date.setdefault(date, []).append(ev)

    # Batch-load signals for all events
    if all_events:
        event_ids = [e["id"] for e in all_events]
        cur.execute(
            """
            SELECT et.event_id::text, tl.persons, tl.orgs, tl.places,
                   tl.named_events, tl.action_class
              FROM event_v3_titles et
              JOIN title_labels tl ON tl.title_id = et.title_id
             WHERE et.event_id = ANY(%s::uuid[])
            """,
            (event_ids,),
        )
        sig_map = {}
        for eid, persons, orgs, places, named, action in cur.fetchall():
            if eid not in sig_map:
                sig_map[eid] = {
                    "persons": set(),
                    "orgs": set(),
                    "places": set(),
                    "named": set(),
                    "actions": Counter(),
                }
            s = sig_map[eid]
            for p in persons or []:
                s["persons"].add(p)
            for o in orgs or []:
                s["orgs"].add(o)
            for pl in places or []:
                s["places"].add(pl)
            for ne in named or []:
                s["named"].add(ne)
            if action:
                s["actions"][action] += 1

        for ev in all_events:
            s = sig_map.get(ev["id"], {})
            ev["entities"] = (
                s.get("persons", set())
                | s.get("orgs", set())
                | s.get("places", set())
                | s.get("named", set())
            )
            acts = s.get("actions", Counter())
            ev["action"] = acts.most_common(1)[0][0] if acts else None

    cur.close()
    return events_by_date


def merge_day(events):
    """Greedy same-day merge. Returns list of (anchor_id, [absorbed_ids])."""
    events = sorted(events, key=lambda e: -e["src"])
    merges = []
    absorbed = set()

    for i, anchor in enumerate(events):
        if anchor["id"] in absorbed:
            continue
        group_ids = []
        a_ents = anchor.get("entities", set()) - HIGH_FREQ_ENTITIES
        a_words = set(anchor["title_words"])

        for j in range(i + 1, len(events)):
            cand = events[j]
            if cand["id"] in absorbed:
                continue
            c_ents = cand.get("entities", set()) - HIGH_FREQ_ENTITIES

            entity_match = (
                len(a_ents & c_ents) >= MIN_SHARED_ENTITIES
                and anchor.get("action") == cand.get("action")
                and anchor.get("action") is not None
            )
            title_match = _dice(a_words, cand["title_words"]) >= DICE_THRESHOLD

            if entity_match or title_match:
                group_ids.append(cand["id"])
                absorbed.add(cand["id"])
                a_ents |= c_ents
                a_words |= cand["title_words"]

        if group_ids:
            merges.append((anchor["id"], group_ids))

    return merges


def apply_merges(conn, merges):
    """Move titles from absorbed events to anchors, delete absorbed events."""
    cur = conn.cursor()
    total_absorbed = 0
    for anchor_id, absorbed_ids in merges:
        for abs_id in absorbed_ids:
            # Move titles to anchor
            cur.execute(
                """
                UPDATE event_v3_titles SET event_id = %s
                 WHERE event_id = %s
                   AND title_id NOT IN (
                     SELECT title_id FROM event_v3_titles WHERE event_id = %s
                   )
                """,
                (anchor_id, abs_id, anchor_id),
            )
            # Delete leftover duplicate title links
            cur.execute("DELETE FROM event_v3_titles WHERE event_id = %s", (abs_id,))
            # Clean up absorbed event
            cur.execute(
                "DELETE FROM event_strategic_narratives WHERE event_id = %s",
                (abs_id,),
            )
            cur.execute("DELETE FROM events_v3 WHERE id = %s", (abs_id,))
            total_absorbed += 1

        # Update anchor source count
        cur.execute(
            """
            UPDATE events_v3 SET source_batch_count = (
                SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
            ) WHERE id = %s
            """,
            (anchor_id, anchor_id),
        )
    conn.commit()
    cur.close()
    return total_absorbed


def process_ctm(ctm_id, dry_run=False):
    """Run same-day merge on all dates for a CTM. Returns stats."""
    conn = get_conn()
    try:
        events_by_date = load_events_with_signals(conn, ctm_id)
        total_merges = 0
        total_absorbed = 0

        for date in sorted(events_by_date.keys()):
            day_events = events_by_date[date]
            if len(day_events) < 2:
                continue
            merges = merge_day(day_events)
            if not merges:
                continue
            n_absorbed = sum(len(ids) for _, ids in merges)
            total_merges += len(merges)
            total_absorbed += n_absorbed

            if dry_run:
                for anchor_id, absorbed_ids in merges:
                    anchor = next(e for e in day_events if e["id"] == anchor_id)
                    print(
                        "  %s [%d src] %s <- +%d"
                        % (
                            date,
                            anchor["src"],
                            (anchor["title"] or "??")[:60],
                            len(absorbed_ids),
                        )
                    )
            else:
                apply_merges(conn, merges)

        return {"merge_groups": total_merges, "absorbed": total_absorbed}
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ctm-id", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    stats = process_ctm(args.ctm_id, dry_run=args.dry_run)
    print("DONE", stats)


if __name__ == "__main__":
    main()
