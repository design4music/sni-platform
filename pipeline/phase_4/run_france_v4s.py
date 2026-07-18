"""France/security: extract + normalize + cluster v4s."""

import sys
import uuid
from collections import defaultdict

sys.path.insert(0, ".")
if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")

import psycopg2

from core.config import HIGH_FREQ_ORGS, config
from pipeline.phase_3_1.extract_labels import (
    build_system_prompt,
    build_user_prompt,
    call_llm,
    parse_llm_response,
    write_to_db,
)
from pipeline.phase_4.normalize_signals import normalize_title_signals

CTM_ID = "38d72cc8-1c9f-4c06-a975-a4321b1608b7"
CENTROID = "EUROPE-FRANCE"
PROTAGONIST = {"MACRON"}


def is_geo(c):
    return not c.startswith("SYS-") and not c.startswith("NON-STATE-")


def cluster(bl):
    clusters = []
    for i, t in enumerate(bl):
        sector = t["sector"] or "UNKNOWN"
        subject = t["subject"]
        target = t["target"] or "NONE"
        places = set(t["places"])
        persons = {p.upper() for p in t["persons"] if p.upper() not in PROTAGONIST}
        orgs = {o.upper() for o in t["orgs"] if o.upper() not in HIGH_FREQ_ORGS}
        named_ev = set(t["named_events"])

        best_cl, best_score = None, 0
        for cl in clusters:
            if cl["sector"] != sector:
                continue
            score = 1.0
            if subject and cl["subject"]:
                if subject == cl["subject"]:
                    score += 2.0
                else:
                    continue
            elif subject or cl["subject"]:
                score += 0.5

            geo_match = False
            if target != "NONE" and cl["target"] != "NONE" and target == cl["target"]:
                score += 1.5
                geo_match = True
            if places & cl["places"]:
                score += 2.0
                geo_match = True
            if persons & cl["persons"]:
                score += 1.5
                geo_match = True
            if orgs & cl["orgs"]:
                score += 1.5
                geo_match = True
            if named_ev & cl["named_events"]:
                score += 1.5
                geo_match = True

            if score >= 3.0 and not geo_match:
                continue
            if score > best_score:
                best_score = score
                best_cl = cl

        if best_cl and best_score >= 4.0:
            best_cl["indices"].append(i)
            best_cl["persons"] |= persons
            best_cl["orgs"] |= orgs
            best_cl["places"] |= places
            best_cl["named_events"] |= named_ev
        else:
            clusters.append(
                {
                    "sector": sector,
                    "subject": subject,
                    "target": target,
                    "persons": persons,
                    "orgs": orgs,
                    "places": places,
                    "named_events": named_ev,
                    "indices": [i],
                }
            )
    return clusters


def main():
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    cur = conn.cursor()

    # Step 1: Re-extract
    print("Step 1: Extracting labels...", flush=True)
    cur.execute(
        "SELECT t.id, t.title_display FROM titles_v3 t "
        "JOIN title_assignments ta ON t.id = ta.title_id WHERE ta.ctm_id = %s",
        (CTM_ID,),
    )
    all_titles = [{"id": str(r[0]), "title_display": r[1]} for r in cur.fetchall()]
    print("  %d titles" % len(all_titles))

    sys_prompt = build_system_prompt()
    all_results = []
    for i in range(0, len(all_titles), 25):
        batch = all_titles[i : i + 25]
        try:
            response = call_llm(sys_prompt, build_user_prompt(batch))
            results = parse_llm_response(response, batch)
            all_results.extend(results)
        except Exception as e:
            print("    Batch error: %s" % e)
        bn = i // 25 + 1
        total_b = (len(all_titles) + 24) // 25
        if bn % 3 == 0 or bn == total_b:
            print("  %d/%d extracted" % (len(all_results), len(all_titles)), flush=True)

    write_to_db(conn, all_results)
    conn.commit()
    print("  %d/%d parsed" % (len(all_results), len(all_titles)))

    # Step 2: Reload + normalize
    print("\nStep 2: Normalizing signals...", flush=True)
    cur.execute(
        """SELECT t.id, t.title_display, t.pubdate_utc, t.centroid_ids,
            tl.sector, tl.subject, tl.target, tl.action_class,
            tl.persons, tl.orgs, tl.places, tl.named_events
        FROM titles_v3 t JOIN title_assignments ta ON t.id = ta.title_id
        LEFT JOIN title_labels tl ON t.id = tl.title_id
        WHERE ta.ctm_id = %s ORDER BY t.pubdate_utc""",
        (CTM_ID,),
    )
    titles = [
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
            "named_events": r[11] or [],
        }
        for r in cur.fetchall()
    ]

    aliases = normalize_title_signals(
        titles, conn, ["places", "persons", "orgs", "named_events"]
    )
    for sig, am in aliases.items():
        new_only = {k: v for k, v in am.items() if k != v}
        if new_only:
            print("  %s: %s" % (sig, dict(list(new_only.items())[:8])))

    # Step 3: Bucket + cluster
    print("\nStep 3: Clustering...", flush=True)
    domestic = []
    bilateral = defaultdict(list)
    for t in titles:
        foreign = [c for c in t["centroid_ids"] if c != CENTROID and is_geo(c)]
        if not foreign:
            domestic.append(t)
        else:
            bilateral[foreign[0]].append(t)

    dom_cls = cluster(domestic)
    emerged = sorted(
        [c for c in dom_cls if len(c["indices"]) >= 2],
        key=lambda c: -len(c["indices"]),
    )
    catchall = [c for c in dom_cls if len(c["indices"]) < 2]
    print(
        "DOMESTIC: %d emerged, %d catchall (%d%%)"
        % (len(emerged), len(catchall), len(catchall) * 100 // len(domestic))
    )
    for cl in emerged:
        samples = [domestic[i]["title_display"][:75] for i in cl["indices"][:2]]
        print(
            "\n  [%d] %s/%s target=%s places=%s"
            % (
                len(cl["indices"]),
                cl["sector"],
                cl["subject"] or "NULL",
                cl["target"],
                list(cl["places"])[:4],
            )
        )
        for s in samples:
            print("    %s" % s)

    all_bil = {}
    print("\nBILATERAL:")
    for bk in sorted(bilateral, key=lambda k: -len(bilateral[k])):
        bl = bilateral[bk]
        cls = cluster(bl)
        all_bil[bk] = cls
        em = [c for c in cls if len(c["indices"]) >= 2]
        ca = sum(1 for c in cls if len(c["indices"]) < 2)
        if em:
            print("  %s: %d -> %d emerged, %d catchall" % (bk, len(bl), len(em), ca))

    # Write
    cur.execute(
        "DELETE FROM event_strategic_narratives WHERE event_id IN "
        "(SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (CTM_ID,),
    )
    cur.execute(
        "DELETE FROM event_v3_titles WHERE event_id IN "
        "(SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (CTM_ID,),
    )
    cur.execute(
        "UPDATE events_v3 SET merged_into = NULL WHERE merged_into IN "
        "(SELECT id FROM events_v3 WHERE ctm_id = %s)",
        (CTM_ID,),
    )
    cur.execute("DELETE FROM events_v3 WHERE ctm_id = %s", (CTM_ID,))
    conn.commit()

    def write(clusters, bl, et, bk=None):
        for cl in clusters:
            eid = str(uuid.uuid4())
            tids = [bl[i]["id"] for i in cl["indices"]]
            dates = [
                bl[i]["pubdate_utc"] for i in cl["indices"] if bl[i]["pubdate_utc"]
            ]
            d = max(dates) if dates else "2026-03-01"
            fs = min(dates) if dates else None
            cur.execute(
                "INSERT INTO events_v3 (id,ctm_id,source_batch_count,date,first_seen,"
                "last_active,event_type,bucket_key,is_catchall,created_at,updated_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())",
                (eid, CTM_ID, len(tids), d, fs, d, et, bk, len(cl["indices"]) < 2),
            )
            for tid in tids:
                cur.execute(
                    "INSERT INTO event_v3_titles (event_id,title_id) VALUES (%s,%s) "
                    "ON CONFLICT DO NOTHING",
                    (eid, tid),
                )

    write(dom_cls, domestic, "domestic")
    for bk, bl in bilateral.items():
        write(all_bil.get(bk, cluster(bl)), bl, "bilateral", bk)
    conn.commit()

    cur.execute(
        "SELECT count(*), count(*) FILTER (WHERE NOT is_catchall), "
        "count(*) FILTER (WHERE is_catchall), "
        "max(source_batch_count) FILTER (WHERE NOT is_catchall) "
        "FROM events_v3 WHERE ctm_id = %s",
        (CTM_ID,),
    )
    r = cur.fetchone()
    print(
        "\nFinal: %d total, %d emerged, %d catchall, max %d"
        % (r[0], r[1], r[2], r[3] or 0)
    )
    conn.close()


if __name__ == "__main__":
    main()
