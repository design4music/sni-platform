"""Re-extract labels + faceted cluster + generate titles for all France CTMs."""

import sys
import uuid
from collections import defaultdict

sys.path.insert(0, ".")
if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")

import psycopg2

from core.config import HIGH_FREQ_ORGS, HIGH_FREQ_PERSONS, config
from pipeline.phase_3_1.extract_labels import (
    build_system_prompt,
    build_user_prompt,
    call_llm,
    parse_llm_response,
    write_to_db,
)

CENTROID = "EUROPE-FRANCE"

FRANCE_CTMS = [
    ("38d72cc8-1c9f-4c06-a975-a4321b1608b7", "geo_security"),
    ("02b32fc7-344f-4fc3-9cbf-570390fa70e2", "geo_politics"),
    ("8a3fecb1-30e7-449c-b7d7-8f967bfd0b07", "geo_information"),
    ("3b124a3d-dcfc-497d-9877-868b430dbc87", "geo_economy"),
    ("8909f436-eff6-4389-8e41-faec385ec14a", "geo_humanitarian"),
    ("fa01272c-c2f8-4f01-b830-64f022844b72", "geo_energy"),
]


def is_geo(c):
    return not c.startswith("SYS-") and not c.startswith("NON-STATE-")


def load_titles(conn, ctm_id):
    cur = conn.cursor()
    cur.execute(
        """SELECT t.id, t.title_display, t.pubdate_utc, t.centroid_ids,
                  tl.sector, tl.subject, tl.target, tl.action_class,
                  tl.persons, tl.orgs, tl.places
           FROM titles_v3 t
           JOIN title_assignments ta ON t.id = ta.title_id
           LEFT JOIN title_labels tl ON t.id = tl.title_id
           WHERE ta.ctm_id = %s ORDER BY t.pubdate_utc""",
        (ctm_id,),
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
            "action_class": r[7],
            "persons": r[8] or [],
            "orgs": r[9] or [],
            "places": r[10] or [],
        }
        for r in cur.fetchall()
    ]


def extract_labels_for_ctm(conn, ctm_id):
    """Re-extract labels with sector/subject for all titles in a CTM."""
    cur = conn.cursor()
    cur.execute(
        "SELECT t.id, t.title_display FROM titles_v3 t "
        "JOIN title_assignments ta ON t.id = ta.title_id WHERE ta.ctm_id = %s",
        (ctm_id,),
    )
    all_titles = [{"id": str(r[0]), "title_display": r[1]} for r in cur.fetchall()]

    sys_prompt = build_system_prompt()
    batch_size = 25
    all_results = []

    for i in range(0, len(all_titles), batch_size):
        batch = all_titles[i : i + batch_size]
        usr_prompt = build_user_prompt(batch)
        try:
            response = call_llm(sys_prompt, usr_prompt)
            results = parse_llm_response(response, batch)
            all_results.extend(results)
        except Exception as e:
            print("    Batch error: %s" % e)

    write_to_db(conn, all_results)
    conn.commit()
    return len(all_titles), len(all_results)


def bucket_titles(titles):
    domestic = []
    bilateral = defaultdict(list)
    for t in titles:
        foreign = [c for c in t["centroid_ids"] if c != CENTROID and is_geo(c)]
        if not foreign:
            domestic.append(t)
        else:
            bilateral[foreign[0]].append(t)
    return domestic, dict(bilateral)


def cluster_faceted(bucket_titles):
    clusters = []
    for i, t in enumerate(bucket_titles):
        sector = t["sector"] or "UNKNOWN"
        subject = t["subject"]
        target = t["target"] or "NONE"
        persons = {
            p.upper() for p in t["persons"] if p.upper() not in HIGH_FREQ_PERSONS
        }
        orgs = {o.upper() for o in t["orgs"] if o.upper() not in HIGH_FREQ_ORGS}

        best_cluster = None
        best_score = 0

        for cl in clusters:
            if cl["sector"] != sector:
                continue
            score = 1
            if subject and cl["subject"]:
                if subject == cl["subject"]:
                    score += 2
                else:
                    continue
            elif subject or cl["subject"]:
                score += 0.5
            if target != "NONE" and cl["target"] != "NONE" and target == cl["target"]:
                score += 1
            if persons & cl["persons"]:
                score += 1
            if orgs & cl["orgs"]:
                score += 1
            if score > best_score:
                best_score = score
                best_cluster = cl

        if best_cluster and best_score >= 3:
            best_cluster["indices"].append(i)
            best_cluster["persons"] |= persons
            best_cluster["orgs"] |= orgs
            if best_cluster["target"] == "NONE" and target != "NONE":
                best_cluster["target"] = target
        else:
            clusters.append(
                {
                    "sector": sector,
                    "subject": subject,
                    "target": target,
                    "persons": persons,
                    "orgs": orgs,
                    "indices": [i],
                }
            )
    return clusters


def write_events(conn, ctm_id, clusters, bucket_list, event_type, bucket_key=None):
    cur = conn.cursor()
    for cl in clusters:
        eid = str(uuid.uuid4())
        tids = [bucket_list[i]["id"] for i in cl["indices"]]
        dates = [
            bucket_list[i]["pubdate_utc"]
            for i in cl["indices"]
            if bucket_list[i]["pubdate_utc"]
        ]
        is_ca = len(cl["indices"]) < 2
        d = max(dates) if dates else "2026-03-01"
        fs = min(dates) if dates else None
        cur.execute(
            "INSERT INTO events_v3 (id,ctm_id,source_batch_count,date,first_seen,"
            "last_active,event_type,bucket_key,is_catchall,created_at,updated_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())",
            (eid, ctm_id, len(tids), d, fs, d, event_type, bucket_key, is_ca),
        )
        for tid in tids:
            cur.execute(
                "INSERT INTO event_v3_titles (event_id,title_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                (eid, tid),
            )


def process_ctm(conn, ctm_id, track):
    print("\n" + "=" * 60)
    print("FRANCE / %s" % track)
    print("=" * 60)

    # Step 1: Re-extract labels
    print("Extracting labels with sector/subject...", flush=True)
    total, parsed = extract_labels_for_ctm(conn, ctm_id)
    print("  %d/%d parsed" % (parsed, total))

    # Step 2: Reload with new labels
    titles = load_titles(conn, ctm_id)
    domestic, bilateral = bucket_titles(titles)

    # Step 3: Cluster
    dom_cls = cluster_faceted(domestic)
    dom_emerged = [c for c in dom_cls if len(c["indices"]) >= 2]
    dom_catchall = [c for c in dom_cls if len(c["indices"]) < 2]
    print(
        "Domestic: %d titles -> %d emerged, %d catchall (%d%%)"
        % (
            len(domestic),
            len(dom_emerged),
            len(dom_catchall),
            len(dom_catchall) * 100 // len(domestic) if domestic else 0,
        )
    )

    bil_total_emerged = 0
    bil_total_catchall = 0
    all_bil_cls = {}
    for bk in sorted(bilateral, key=lambda k: -len(bilateral[k])):
        bl = bilateral[bk]
        cls = cluster_faceted(bl)
        all_bil_cls[bk] = cls
        emerged = [c for c in cls if len(c["indices"]) >= 2]
        catchall = [c for c in cls if len(c["indices"]) < 2]
        bil_total_emerged += len(emerged)
        bil_total_catchall += len(catchall)
        if emerged and len(bl) >= 5:
            print(
                "  %s: %d -> %d emerged, %d catchall"
                % (bk, len(bl), len(emerged), len(catchall))
            )
    print(
        "Bilateral total: %d emerged, %d catchall"
        % (bil_total_emerged, bil_total_catchall)
    )

    # Step 4: Write to DB
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM event_strategic_narratives WHERE event_id IN (SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (ctm_id,),
    )
    cur.execute(
        "DELETE FROM event_v3_titles WHERE event_id IN (SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (ctm_id,),
    )
    cur.execute(
        "UPDATE events_v3 SET merged_into = NULL WHERE merged_into IN (SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (ctm_id,),
    )
    cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (ctm_id,))
    conn.commit()

    write_events(conn, ctm_id, dom_cls, domestic, "domestic")
    for bk, bl in bilateral.items():
        write_events(conn, ctm_id, all_bil_cls.get(bk, []), bl, "bilateral", bk)
    conn.commit()

    # Count
    cur.execute(
        "SELECT count(*), count(*) FILTER (WHERE NOT is_catchall), "
        "max(source_batch_count) FILTER (WHERE NOT is_catchall) "
        "FROM events_v3 WHERE ctm_id = %s",
        (ctm_id,),
    )
    r = cur.fetchone()
    print("Written: %d total, %d emerged, max %d" % (r[0], r[1], r[2] or 0))

    return r[1]  # emerged count


def main():
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    total_emerged = 0
    for ctm_id, track in FRANCE_CTMS:
        emerged = process_ctm(conn, ctm_id, track)
        total_emerged += emerged

    # Generate titles for all France CTMs (including security)
    print("\n" + "=" * 60)
    print("GENERATING TITLES FOR ALL FRANCE CTMs")
    print("=" * 60)
    import asyncio

    from pipeline.phase_4.generate_event_summaries_4_5a import process_events

    all_ctm_ids = [c[0] for c in FRANCE_CTMS]

    for ctm_id in all_ctm_ids:
        cur = conn.cursor()
        cur.execute("SELECT centroid_id, track FROM ctm WHERE id = %s", (ctm_id,))
        row = cur.fetchone()
        print("\n--- %s / %s ---" % (row[0], row[1]), flush=True)
        asyncio.run(process_events(max_events=200, ctm_id=ctm_id))

    conn.close()
    print("\nAll done.")


if __name__ == "__main__":
    main()
