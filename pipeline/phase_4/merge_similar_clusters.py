"""
Phase 4.1b: Dice Merge of Similar Clusters

Merges clusters with high title-word overlap. Three passes:
  1. Within-family: clusters in the same family (aggressive, Dice >= 0.45)
  2. Cross-family same-bucket: clusters in same bucket, different families (Dice >= 0.55)
  3. Cross-bucket: clusters in different buckets entirely (Dice >= 0.60)

Uses soft delete via merged_into FK (reversible). Smaller cluster merges
into larger one. Source counts are updated on the surviving cluster.

Pipeline position: after Phase 4.1a (mechanical titles), before Phase 4.5a (LLM polish).

Usage:
    python pipeline/phase_4/merge_similar_clusters.py --ctm-id <uuid>
    python pipeline/phase_4/merge_similar_clusters.py --centroid AMERICAS-USA --track geo_security
    python pipeline/phase_4/merge_similar_clusters.py --centroid AMERICAS-USA --track geo_security --dry-run
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import HIGH_FREQ_ORGS, HIGH_FREQ_PERSONS, config

# --- Config ---

# Dice thresholds per merge pass (higher = more conservative)
DICE_WITHIN_FAMILY = 0.45
DICE_CROSS_FAMILY = 0.55
DICE_CROSS_BUCKET = 0.60

# Ubiquity: entities appearing in >15% of CTM titles are not discriminating
UBIQUITY_THRESHOLD = 0.15

STOP_WORDS = frozenset(
    "the a an in of on for to and is are was were with from at by as its it be "
    "has had have that this or but not no new over after into about up out more "
    "says said will could would may amid us set than been also".split()
)


# --- Helpers ---


def tokenize(text):
    words = set(re.findall(r"[a-z][a-z0-9]+", (text or "").lower()))
    return words - STOP_WORDS


def dice(a, b):
    if not a or not b:
        return 0.0
    return 2 * len(a & b) / (len(a) + len(b))


# --- DB ---


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


def load_clusters(conn, ctm_id):
    """Load all mergeable clusters with titles, family_id, bucket, and entity signals."""
    cur = conn.cursor()
    cur.execute(
        """SELECT id, title, source_batch_count, family_id, bucket_key, event_type
           FROM events_v3
           WHERE ctm_id = %s AND NOT is_catchall AND merged_into IS NULL
           ORDER BY source_batch_count DESC""",
        (ctm_id,),
    )
    clusters = {}
    for r in cur.fetchall():
        clusters[r[0]] = {
            "id": r[0],
            "title": r[1] or "",
            "src": r[2],
            "family_id": r[3],
            "bucket_key": r[4],
            "event_type": r[5],
            "words": tokenize(r[1]),
            "persons": set(),
            "orgs": set(),
            "places": set(),
        }

    if not clusters:
        cur.close()
        return [], set()

    # Load entity signals per cluster
    cluster_ids = [str(cid) for cid in clusters]
    cur.execute(
        """SELECT et.event_id, tl.persons, tl.orgs, tl.places
           FROM event_v3_titles et
           JOIN title_labels tl ON tl.title_id = et.title_id
           WHERE et.event_id = ANY(%s::uuid[])""",
        (cluster_ids,),
    )
    for r in cur.fetchall():
        c = clusters.get(r[0])
        if not c:
            continue
        for p in r[1] or []:
            c["persons"].add(p.upper())
        for o in r[2] or []:
            c["orgs"].add(o)
        for p in r[3] or []:
            c["places"].add(p)

    # Compute ubiquitous entities across the CTM
    all_persons = defaultdict(int)
    all_orgs = defaultdict(int)
    all_places = defaultdict(int)
    for c in clusters.values():
        for p in c["persons"]:
            all_persons[p] += 1
        for o in c["orgs"]:
            all_orgs[o] += 1
        for p in c["places"]:
            all_places[p] += 1

    n_clusters = len(clusters)
    threshold = n_clusters * UBIQUITY_THRESHOLD
    ubiquitous = set()
    for p, cnt in all_persons.items():
        if cnt >= threshold or p in HIGH_FREQ_PERSONS:
            ubiquitous.add(("person", p))
    for o, cnt in all_orgs.items():
        if cnt >= threshold or o in HIGH_FREQ_ORGS:
            ubiquitous.add(("org", o))
    for p, cnt in all_places.items():
        if cnt >= threshold:
            ubiquitous.add(("place", p))

    cur.close()
    cluster_list = sorted(clusters.values(), key=lambda c: -c["src"])
    return cluster_list, ubiquitous


def execute_merge(conn, anchor_id, victim_id, dry_run=False):
    """Merge victim into anchor: move titles, update counts, soft-delete."""
    if dry_run:
        return

    cur = conn.cursor()

    # Move title links from victim to anchor
    cur.execute(
        """UPDATE event_v3_titles SET event_id = %s
           WHERE event_id = %s
           AND title_id NOT IN (SELECT title_id FROM event_v3_titles WHERE event_id = %s)""",
        (str(anchor_id), str(victim_id), str(anchor_id)),
    )

    # Delete duplicate title links
    cur.execute(
        "DELETE FROM event_v3_titles WHERE event_id = %s",
        (str(victim_id),),
    )

    # Update anchor source count
    cur.execute(
        """UPDATE events_v3 SET source_batch_count = (
               SELECT COUNT(*) FROM event_v3_titles WHERE event_id = %s
           ) WHERE id = %s""",
        (str(anchor_id), str(anchor_id)),
    )

    # Soft-delete victim
    cur.execute(
        "UPDATE events_v3 SET merged_into = %s WHERE id = %s",
        (str(anchor_id), str(victim_id)),
    )

    cur.close()


# --- Merge passes ---


def has_entity_overlap(a, b, ubiquitous):
    """Check if two clusters share at least one non-ubiquitous entity."""
    # Filter out ubiquitous entities
    a_persons = {p for p in a["persons"] if ("person", p) not in ubiquitous}
    b_persons = {p for p in b["persons"] if ("person", p) not in ubiquitous}
    if a_persons & b_persons:
        return True

    a_orgs = {o for o in a["orgs"] if ("org", o) not in ubiquitous}
    b_orgs = {o for o in b["orgs"] if ("org", o) not in ubiquitous}
    if a_orgs & b_orgs:
        return True

    a_places = {p for p in a["places"] if ("place", p) not in ubiquitous}
    b_places = {p for p in b["places"] if ("place", p) not in ubiquitous}
    if a_places & b_places:
        return True

    return False


def merge_pass(
    clusters,
    threshold,
    group_fn,
    pass_name,
    conn,
    dry_run,
    ubiquitous,
    require_entity_overlap=False,
):
    """Run a merge pass. group_fn returns a grouping key for each cluster."""
    groups = defaultdict(list)
    for c in clusters:
        key = group_fn(c)
        if key is not None:
            groups[key].append(c)

    merged_count = 0
    skipped_no_entity = 0
    merged_ids = set()

    for key, members in groups.items():
        if len(members) < 2:
            continue

        # Sort by size descending -- larger clusters are anchors
        members.sort(key=lambda c: -c["src"])

        for i, candidate in enumerate(members):
            if candidate["id"] in merged_ids:
                continue
            for j in range(i + 1, len(members)):
                other = members[j]
                if other["id"] in merged_ids:
                    continue
                d = dice(candidate["words"], other["words"])
                if d >= threshold:
                    # Entity overlap gate
                    if require_entity_overlap:
                        if not has_entity_overlap(candidate, other, ubiquitous):
                            skipped_no_entity += 1
                            continue

                    # Merge smaller into larger
                    anchor = candidate
                    victim = other
                    if victim["src"] > anchor["src"]:
                        anchor, victim = victim, anchor

                    print(
                        "    %.2f  [%d src] %s"
                        % (
                            d,
                            victim["src"],
                            (victim["title"] or "?")[:60],
                        )
                    )
                    print(
                        "      -> [%d src] %s"
                        % (
                            anchor["src"],
                            (anchor["title"] or "?")[:60],
                        )
                    )

                    execute_merge(conn, anchor["id"], victim["id"], dry_run)
                    merged_ids.add(victim["id"])
                    anchor["src"] += victim["src"]
                    anchor["words"] = anchor["words"] | victim["words"]
                    # Merge entity sets too for subsequent comparisons
                    anchor["persons"] = anchor["persons"] | victim["persons"]
                    anchor["orgs"] = anchor["orgs"] | victim["orgs"]
                    anchor["places"] = anchor["places"] | victim["places"]
                    merged_count += 1

    if skipped_no_entity:
        print("    (%d pairs skipped: no shared entity)" % skipped_no_entity)

    if merged_count:
        conn.commit()

    return merged_count, merged_ids


# --- Main ---


def process_ctm(ctm_id=None, centroid=None, track=None, dry_run=False):
    """Run all three merge passes on a CTM.

    Returns total number of merges performed.
    """
    conn = get_connection()
    try:
        ctm = get_ctm_info(conn, ctm_id, centroid, track)
        if not ctm:
            print("CTM not found")
            return 0

        ctm_id_str = str(ctm["id"])
        print("=== Dice Merge %s ===" % ("(DRY RUN)" if dry_run else ""))
        print("  %s / %s / %s" % (ctm["centroid_id"], ctm["track"], ctm["month"]))

        clusters, ubiquitous = load_clusters(conn, ctm_id_str)
        print("  %d clusters loaded" % len(clusters))
        if ubiquitous:
            print(
                "  Ubiquitous: %s"
                % ", ".join("%s:%s" % (t, v) for t, v in sorted(ubiquitous))[:120]
            )

        # Check titles exist
        no_title = sum(1 for c in clusters if not c["words"])
        if no_title > len(clusters) * 0.5:
            print(
                "  WARNING: %d/%d clusters have no title. Run Phase 4.1a first."
                % (
                    no_title,
                    len(clusters),
                )
            )

        total_merged = 0

        # Pass 1: Within-family merge (no entity gate -- same family is safe)
        print("\n  Pass 1: Within-family (Dice >= %.2f)" % DICE_WITHIN_FAMILY)
        count, merged_ids = merge_pass(
            clusters,
            DICE_WITHIN_FAMILY,
            lambda c: str(c["family_id"]) if c["family_id"] else None,
            "within-family",
            conn,
            dry_run,
            ubiquitous,
            require_entity_overlap=False,
        )
        print("  -> %d merges" % count)
        total_merged += count
        clusters = [c for c in clusters if c["id"] not in merged_ids]

        # Pass 2: Cross-family same-bucket (require entity overlap)
        print(
            "\n  Pass 2: Cross-family same-bucket (Dice >= %.2f, entity gate)"
            % DICE_CROSS_FAMILY
        )
        count, merged_ids = merge_pass(
            clusters,
            DICE_CROSS_FAMILY,
            lambda c: "%s:%s" % (c["event_type"], c["bucket_key"] or "domestic"),
            "cross-family",
            conn,
            dry_run,
            ubiquitous,
            require_entity_overlap=True,
        )
        print("  -> %d merges" % count)
        total_merged += count
        clusters = [c for c in clusters if c["id"] not in merged_ids]

        # Pass 3: Cross-bucket (require entity overlap)
        print(
            "\n  Pass 3: Cross-bucket (Dice >= %.2f, entity gate)" % DICE_CROSS_BUCKET
        )
        count, merged_ids = merge_pass(
            clusters,
            DICE_CROSS_BUCKET,
            lambda c: "all",
            "cross-bucket",
            conn,
            dry_run,
            ubiquitous,
            require_entity_overlap=True,
        )
        print("  -> %d merges" % count)
        total_merged += count

        print("\n  Total: %d merges" % total_merged)
        return total_merged
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 4.1b: Dice Merge of Similar Clusters"
    )
    parser.add_argument("--ctm-id", type=str, help="CTM ID")
    parser.add_argument("--centroid", type=str, help="Centroid ID")
    parser.add_argument("--track", type=str, help="Track name")
    parser.add_argument("--dry-run", action="store_true", help="Report only")
    args = parser.parse_args()

    if not args.ctm_id and not (args.centroid and args.track):
        print("ERROR: provide --ctm-id or --centroid + --track")
        sys.exit(1)

    result = process_ctm(
        ctm_id=args.ctm_id,
        centroid=args.centroid,
        track=args.track,
        dry_run=args.dry_run,
    )
    print("\nDone. %d merges." % result)
