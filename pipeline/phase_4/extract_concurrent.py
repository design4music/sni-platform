"""
Concurrent label extraction for multiple CTMs.

Runs Phase 3.1 extraction with parallel LLM calls across CTMs.
Uses threading (not asyncio) since the LLM calls are synchronous httpx.

Usage:
    python -m pipeline.phase_4.extract_concurrent --centroid EUROPE-FRANCE --month 2026-03-01
    python -m pipeline.phase_4.extract_concurrent --ctm-ids id1,id2,id3
"""

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")

import psycopg2

from core.config import config
from pipeline.phase_3_1.extract_labels import (
    build_system_prompt,
    build_user_prompt,
    call_llm,
    parse_llm_response,
    write_to_db,
)


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def extract_batch(sys_prompt, batch):
    """Extract labels for a single batch of 25 titles. Thread-safe."""
    try:
        response = call_llm(sys_prompt, build_user_prompt(batch))
        return parse_llm_response(response, batch)
    except Exception as e:
        print("    Batch error: %s" % e, flush=True)
        return []


def extract_ctm(ctm_id, track, concurrency=5):
    """Extract all titles for a CTM with concurrent batches."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT t.id, t.title_display FROM titles_v3 t "
        "JOIN title_assignments ta ON t.id = ta.title_id WHERE ta.ctm_id = %s",
        (ctm_id,),
    )
    all_titles = [{"id": str(r[0]), "title_display": r[1]} for r in cur.fetchall()]

    if not all_titles:
        conn.close()
        return 0, 0

    sys_prompt = build_system_prompt()
    batches = []
    for i in range(0, len(all_titles), 25):
        batches.append(all_titles[i : i + 25])

    all_results = []
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(extract_batch, sys_prompt, batch): i
            for i, batch in enumerate(batches)
        }
        done = 0
        for future in as_completed(futures):
            results = future.result()
            all_results.extend(results)
            done += 1
            if done % 3 == 0 or done == len(batches):
                print(
                    "    %s: %d/%d batches, %d results (%.0fs)"
                    % (track, done, len(batches), len(all_results), time.time() - t0),
                    flush=True,
                )

    write_to_db(conn, all_results)
    conn.commit()
    conn.close()

    return len(all_titles), len(all_results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--centroid", type=str)
    parser.add_argument("--month", type=str, default="2026-03-01")
    parser.add_argument("--ctm-ids", type=str, help="Comma-separated CTM IDs")
    parser.add_argument("--concurrency", type=int, default=5, help="Parallel LLM calls")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip CTMs where sector is already populated",
    )
    args = parser.parse_args()

    conn = get_connection()
    cur = conn.cursor()

    if args.ctm_ids:
        ctm_ids = args.ctm_ids.split(",")
        cur.execute("SELECT id, track FROM ctm WHERE id = ANY(%s::uuid[])", (ctm_ids,))
    elif args.centroid:
        cur.execute(
            "SELECT id, track FROM ctm WHERE centroid_id = %s AND month = %s",
            (args.centroid, args.month),
        )
    else:
        parser.error("Provide --centroid or --ctm-ids")
        return

    ctms = [(str(r[0]), r[1]) for r in cur.fetchall()]

    if args.skip_existing:
        # Check which CTMs already have sector extracted
        filtered = []
        for ctm_id, track in ctms:
            cur.execute(
                "SELECT count(*) FILTER (WHERE tl.sector IS NOT NULL), count(*) "
                "FROM title_assignments ta "
                "LEFT JOIN title_labels tl ON tl.title_id = ta.title_id "
                "WHERE ta.ctm_id = %s",
                (ctm_id,),
            )
            with_sector, total = cur.fetchone()
            # Skip if >90% already have sector
            if total > 0 and with_sector / total > 0.9:
                print("Skipping %s (%d/%d have sector)" % (track, with_sector, total))
            else:
                filtered.append((ctm_id, track))
        ctms = filtered

    conn.close()

    print("Extracting %d CTMs (concurrency=%d):" % (len(ctms), args.concurrency))
    for ctm_id, track in ctms:
        print("  %s %s" % (ctm_id[:8], track))

    t0 = time.time()
    total_titles = 0
    total_parsed = 0

    for ctm_id, track in ctms:
        print("\n--- %s ---" % track, flush=True)
        titles, parsed = extract_ctm(ctm_id, track, concurrency=args.concurrency)
        total_titles += titles
        total_parsed += parsed
        print("  %d/%d parsed" % (parsed, titles))

    print(
        "\nDone. %d/%d total titles in %.0fs"
        % (total_parsed, total_titles, time.time() - t0)
    )


if __name__ == "__main__":
    main()
