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


def load_all_titles(conn, ctm_ids):
    """Load titles from all CTMs at once."""
    cur = conn.cursor()
    cur.execute(
        """SELECT t.id, t.title_display, t.pubdate_utc, t.centroid_ids,
                  tl.sector, tl.subject, tl.target, tl.domain,
                  tl.persons, tl.orgs, tl.places, tl.named_events,
                  ta.ctm_id, ta.track
           FROM titles_v3 t
           JOIN title_assignments ta ON t.id = ta.title_id
           LEFT JOIN title_labels tl ON t.id = tl.title_id
           WHERE ta.ctm_id = ANY(%s::uuid[])
           ORDER BY t.pubdate_utc""",
        (ctm_ids,),
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
            "ctm_id": str(r[12]),
            "track": r[13],
        }
        for r in cur.fetchall()
    ]


def cluster_topdown(titles, centroid_id):
    """Top-down clustering: group by sector+subject, split by identity."""
    protagonist = CTM_PROTAGONIST.get(centroid_id, set())

    # Group by sector+subject
    groups = defaultdict(list)
    for i, t in enumerate(titles):
        key = (t["sector"] or "UNKNOWN", t["subject"])
        groups[key].append(i)

    # Split each group by identity signals
    all_clusters = []
    for (sector, subject), indices in groups.items():
        if len(indices) <= 3:
            all_clusters.append(
                {"sector": sector, "subject": subject, "indices": indices}
            )
            continue

        sub_clusters = []
        for i in indices:
            t = titles[i]
            places = set(t["places"])
            persons = {p.upper() for p in t["persons"] if p.upper() not in protagonist}
            orgs = {o.upper() for o in t["orgs"] if o.upper() not in HIGH_FREQ_ORGS}
            named_ev = set(t["named_events"])
            identity = places | orgs | named_ev | persons

            best_cl, best_n = None, 0
            for cl in sub_clusters:
                n = len(identity & cl["identity"])
                if n > best_n:
                    best_n = n
                    best_cl = cl

            if best_cl and best_n > 0:
                best_cl["indices"].append(i)
                best_cl["identity"] |= identity
            elif not identity:
                sub_clusters.append({"indices": [i], "identity": set(), "orphan": True})
            else:
                sub_clusters.append(
                    {"indices": [i], "identity": identity, "orphan": False}
                )

        # Merge orphans to largest real cluster
        real = [c for c in sub_clusters if not c.get("orphan")]
        orphans = [c for c in sub_clusters if c.get("orphan")]
        if real and orphans:
            largest = max(real, key=lambda c: len(c["indices"]))
            for o in orphans:
                largest["indices"].extend(o["indices"])
            sub_clusters = real

        for sc in sub_clusters:
            all_clusters.append(
                {"sector": sector, "subject": subject, "indices": sc["indices"]}
            )

    return all_clusters


def assign_track(cluster, titles):
    """Assign a cluster to its best-fit track based on sector."""
    # Use sector of the cluster (not domain)
    return SECTOR_TO_TRACK.get(cluster["sector"], "geo_politics")


def tag_geo(cluster_indices, titles, centroid_id):
    """Tag a cluster as domestic or bilateral."""
    foreign_counts = Counter()
    for i in cluster_indices:
        for c in titles[i]["centroid_ids"]:
            if c != centroid_id and is_geo(c):
                foreign_counts[c] += 1

    if not foreign_counts:
        return "domestic", None
    return "bilateral", foreign_counts.most_common(1)[0][0]


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

    # Load all titles
    titles = load_all_titles(conn, list(ctm_map.keys()))
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
            tracks = Counter(titles[i]["track"] for i in groups[key])
            track_str = ", ".join("%s=%d" % (t, c) for t, c in tracks.most_common(3))
            print(
                "  %s/%s: %d [%s]"
                % (key[0], key[1] or "NULL", len(groups[key]), track_str)
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
        track_votes = Counter(titles[i]["track"] for i in cl["indices"])
        cross = ""
        if len(track_votes) > 1:
            others = [
                "%s=%d" % (t, c)
                for t, c in track_votes.most_common()
                if t != track_votes.most_common(1)[0][0]
            ]
            cross = " (+" + ",".join(others) + ")"

        sample = titles[cl["indices"][0]]["title_display"][:70]
        print(
            "  [%d] %s/%s -> %s%s | %s %s"
            % (
                len(cl["indices"]),
                cl["sector"],
                cl["subject"] or "NULL",
                track,
                cross,
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
