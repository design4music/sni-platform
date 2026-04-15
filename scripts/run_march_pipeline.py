"""
Run Phase 4.1a + 4.1 + 4.1b on all March 2026 CTMs.

Phase 4.1a: Mechanical title generation
Phase 4.1:  Family assembly
Phase 4.1b: Dice merge

Does NOT run LLM family summaries (4.5a-fam) -- that's expensive and separate.

Usage:
    python scripts/run_march_pipeline.py
    python scripts/run_march_pipeline.py --dry-run
"""

import argparse
import sys
import time
from pathlib import Path

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config
from pipeline.phase_4.assemble_families import process_ctm as assemble_families

MONTH = "2026-03-01"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    cur = conn.cursor()
    cur.execute(
        """SELECT id, centroid_id, track, title_count
           FROM ctm
           WHERE month = %s AND title_count >= 3
           ORDER BY title_count DESC""",
        (MONTH,),
    )
    ctms = cur.fetchall()
    cur.close()
    conn.close()

    print("=== March 2026 Pipeline: 4.1a + 4.1 + 4.1b ===")
    print("  %d CTMs, %d total titles" % (len(ctms), sum(r[3] for r in ctms)))
    if args.dry_run:
        print("  DRY RUN -- will report only for family assembly")
    print()

    total_titles = 0
    total_families = 0
    total_merges = 0
    errors = []
    start = time.time()

    for i, (ctm_id, centroid_id, track, title_count) in enumerate(ctms, 1):
        ctm_id_str = str(ctm_id)
        print(
            "[%d/%d] %s / %s (%d titles)"
            % (i, len(ctms), centroid_id, track, title_count)
        )

        try:
            # Phase 4.1: Family assembly (D-056)
            if args.dry_run:
                families = assemble_families(ctm_id=ctm_id_str, dry_run=True)
            else:
                families = assemble_families(ctm_id=ctm_id_str, force=True)
            total_families += families

        except Exception as e:
            print("  ERROR: %s" % e)
            errors.append((centroid_id, track, str(e)))

    elapsed = time.time() - start
    print("\n=== SUMMARY ===")
    print("  CTMs processed: %d" % len(ctms))
    print("  Titles generated: %d" % total_titles)
    print("  Families created: %d" % total_families)
    print("  Merges performed: %d" % total_merges)
    print("  Errors: %d" % len(errors))
    print("  Time: %.0f seconds" % elapsed)

    if errors:
        print("\n  Errors:")
        for c, t, e in errors:
            print("    %s / %s: %s" % (c, t, e))


if __name__ == "__main__":
    main()
