"""
Phase 4.1: Event Family Assembly (D-056 adjacent-day chain rule)

Groups day-beat clusters into families by chaining clusters that share the
same beat triple AND dominant_entity AND have adjacent dates (gap <= 1 day).

Pipeline position: after Phase 4 day-beat clustering.
See docs/context/CLUSTERING_REDESIGN.md (LOCK-4).

Usage:
    python -m pipeline.phase_4.assemble_families --ctm-id <uuid>
    python -m pipeline.phase_4.assemble_families --centroid AMERICAS-USA --track geo_security
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

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.config import HIGH_FREQ_ORGS, HIGH_FREQ_PERSONS, config

# Maximum gap (in days) between adjacent clusters in a chain.
MAX_DAY_GAP = 1

ENTITY_FIELDS = ("places", "persons", "orgs", "named_events", "industries")


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def get_ctm_info(conn, ctm_id=None, centroid=None, track=None):
    """Get CTM info by ID or by centroid+track (most recent month)."""
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


def _entity_token(sig_type, value):
    """Normalized entity token, or None if it's high-frequency noise."""
    if sig_type == "persons":
        norm = (value or "").upper()
        if norm in HIGH_FREQ_PERSONS:
            return None
        return "persons:" + norm
    if sig_type == "orgs":
        if (value or "") in HIGH_FREQ_ORGS:
            return None
        return "orgs:" + value
    return "{}:{}".format(sig_type, value)


def load_clusters(cur, ctm_id):
    """Load clusters with their beat triple + dominant entity derived from titles.

    Returns list of dicts: {id, date, source_count, beat, dominant_entity}.
    Singletons and clusters without a beat triple are still returned (they just
    won't form families).
    """
    cur.execute(
        """SELECT id, date, source_batch_count
             FROM events_v3
            WHERE ctm_id = %s AND NOT is_catchall AND merged_into IS NULL
            ORDER BY date ASC""",
        (ctm_id,),
    )
    rows = cur.fetchall()
    if not rows:
        return []

    clusters = {
        row[0]: {
            "id": row[0],
            "date": row[1],
            "source_count": row[2] or 0,
            "beats": Counter(),
            "tiered": {t: Counter() for t in ENTITY_FIELDS},
        }
        for row in rows
    }

    cur.execute(
        """SELECT et.event_id,
                  tl.actor, tl.action_class, tl.target,
                  tl.places, tl.persons, tl.orgs, tl.named_events, tl.industries
             FROM event_v3_titles et
             JOIN title_labels tl ON tl.title_id = et.title_id
            WHERE et.event_id = ANY(%s::uuid[])""",
        ([str(cid) for cid in clusters.keys()],),
    )

    for r in cur.fetchall():
        c = clusters.get(r[0])
        if not c:
            continue
        c["beats"][(r[1], r[2], r[3])] += 1
        c.setdefault("targets", Counter())[r[3] or "NONE"] += 1
        for sig_type, vals in zip(ENTITY_FIELDS, (r[4], r[5], r[6], r[7], r[8])):
            for v in vals or []:
                tok = _entity_token(sig_type, v)
                if tok:
                    c["tiered"][sig_type][tok] += 1

    # Tier preference with majority-coverage gate.
    # Prefer places -> named_events -> persons -> orgs -> industries, but the
    # chosen anchor must appear in >= 50% of the cluster's titles. Otherwise
    # fall through. This prevents a minority place (e.g., 11/223 Karachi titles
    # inside a 223-title Khamenei cluster) from hijacking the family anchor.
    # Clusters with no >=50% anchor become standalone (no family).
    FAMILY_TIER_ORDER = ("places", "named_events", "persons", "orgs", "industries")

    out = []
    for c in clusters.values():
        beat = c["beats"].most_common(1)[0][0] if c["beats"] else (None, None, None)
        dominant = None
        threshold = max(1, c["source_count"] // 2)
        for tier in FAMILY_TIER_ORDER:
            counter = c["tiered"][tier]
            if not counter:
                continue
            token, count = counter.most_common(1)[0]
            if count >= threshold:
                dominant = token
                break
        targets = c.get("targets") or Counter()
        target = targets.most_common(1)[0][0] if targets else "NONE"
        out.append(
            {
                "id": c["id"],
                "date": c["date"],
                "source_count": c["source_count"],
                "beat": beat,
                "dominant_entity": dominant,
                "target": target,
            }
        )
    return out


def chain_families(clusters):
    """Group clusters by (dominant_entity, target), then chain by adjacent dates.

    Entity-only chaining collapsed narrative hubs like Paris (elections +
    US-China talks + Macron-Russia + court rulings) into one blob. Adding
    `target` separates stories that share a location but are aimed at
    different counterparties: (Paris, CN) for trade talks, (Paris, RU) for
    Macron diplomacy, (Paris, NONE) for elections and courts. Target is more
    stable across days within one arc than action_class or actor.
    """
    groups = defaultdict(list)
    for c in clusters:
        if not c["dominant_entity"] or not c["date"]:
            continue
        groups[(c["dominant_entity"], c.get("target") or "NONE")].append(c)

    families = []
    for key, members in groups.items():
        members.sort(key=lambda x: x["date"])
        chain = [members[0]]
        for prev, curr in zip(members, members[1:]):
            gap = (curr["date"] - prev["date"]).days
            if gap <= MAX_DAY_GAP:
                chain.append(curr)
            else:
                if len(chain) >= 2:
                    families.append(_make_family(key, chain))
                chain = [curr]
        if len(chain) >= 2:
            families.append(_make_family(key, chain))
    return families


def _make_family(key, chain):
    dominant_entity, target = key
    beat_counter = Counter(c["beat"] for c in chain if c["beat"] != (None, None, None))
    beat = beat_counter.most_common(1)[0][0] if beat_counter else (None, None, None)
    return {
        "beat": beat,
        "dominant_entity": dominant_entity,
        "target": target,
        "clusters": chain,
        "cluster_count": len(chain),
        "source_count": sum(c["source_count"] for c in chain),
        "first_seen": min(c["date"] for c in chain),
        "last_active": max(c["date"] for c in chain),
    }


def write_families(conn, ctm_id, families):
    """Wipe-and-replace all event_families for this CTM."""
    cur = conn.cursor()

    cur.execute("UPDATE events_v3 SET family_id = NULL WHERE ctm_id = %s", (ctm_id,))
    cur.execute("DELETE FROM event_families WHERE ctm_id = %s", (ctm_id,))

    written = 0
    for f in families:
        fam_id = str(uuid.uuid4())
        spine_value = f["dominant_entity"].split(":", 1)[-1]
        spine_type = f["dominant_entity"].split(":", 1)[0]
        actor, action, target = f["beat"]
        title = "{} ({} -> {})".format(spine_value, actor or "?", action or "?")

        cur.execute(
            """INSERT INTO event_families
               (id, ctm_id, title, domain, cluster_count, source_count,
                first_seen, last_active, spine_type, spine_value,
                created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())""",
            (
                fam_id,
                ctm_id,
                title,
                spine_type,
                f["cluster_count"],
                f["source_count"],
                f["first_seen"],
                f["last_active"],
                spine_type,
                spine_value,
            ),
        )
        cluster_ids = [str(c["id"]) for c in f["clusters"]]
        cur.execute(
            "UPDATE events_v3 SET family_id = %s WHERE id = ANY(%s::uuid[])",
            (fam_id, cluster_ids),
        )
        written += 1

    conn.commit()
    cur.close()
    print("  Wrote {} families".format(written))


def assemble_families_for_ctm(conn, ctm_id):
    cur = conn.cursor()
    clusters = load_clusters(cur, ctm_id)
    cur.close()
    if not clusters:
        print("  No clusters")
        return [], []
    families = chain_families(clusters)
    return families, clusters


def print_report(families, clusters):
    if not clusters:
        return
    in_families = sum(f["cluster_count"] for f in families)
    standalones = len(clusters) - in_families
    print(
        "  {} clusters: {} families ({} clusters chained), {} standalone".format(
            len(clusters), len(families), in_families, standalones
        )
    )
    families_sorted = sorted(families, key=lambda f: -f["source_count"])
    for f in families_sorted[:10]:
        print(
            "    [{:2d} clusters, {:5d} src] {} {}-{}".format(
                f["cluster_count"],
                f["source_count"],
                f["dominant_entity"],
                f["first_seen"],
                f["last_active"],
            )
        )
    if len(families) > 10:
        print("    ... +{} more".format(len(families) - 10))


def process_ctm(ctm_id=None, centroid=None, track=None, dry_run=False, force=False):
    """Main entry point. `track` and `force` are accepted for backward compat
    but not used (D-056 chaining is purely structural)."""
    conn = get_connection()
    try:
        ctm = get_ctm_info(conn, ctm_id, centroid, track)
        if not ctm:
            print("CTM not found")
            return 0

        print("=== Family Assembly D-056 {} ===".format("(DRY RUN)" if dry_run else ""))
        print(
            "  {} / {} / {} ({} titles)".format(
                ctm["centroid_id"], ctm["track"], ctm["month"], ctm["title_count"]
            )
        )

        families, clusters = assemble_families_for_ctm(conn, ctm["id"])
        print_report(families, clusters)

        if dry_run:
            return 0

        write_families(conn, ctm["id"], families)
        return len(families)
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 4.1: D-056 adjacent-day family assembly"
    )
    parser.add_argument("--ctm-id", type=str, help="CTM ID to process")
    parser.add_argument("--centroid", type=str, help="Centroid ID")
    parser.add_argument("--track", type=str, help="Track name")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--force", action="store_true", help="(ignored, kept for compat)"
    )
    args = parser.parse_args()

    if not args.ctm_id and not (args.centroid and args.track):
        print("ERROR: provide --ctm-id or --centroid + --track")
        sys.exit(1)

    process_ctm(
        ctm_id=args.ctm_id,
        centroid=args.centroid,
        track=args.track,
        dry_run=args.dry_run,
        force=args.force,
    )
