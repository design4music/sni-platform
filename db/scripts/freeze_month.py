"""
CTM Monthly Freeze Script

Freezes all CTMs for a given month:
1. Generates LLM summaries for large CTMs (>=30 titles) without summaries
2. Assigns canned text for small CTMs (<30 titles) without summaries
3. Sets is_frozen=true for all CTMs of the target month

Usage:
    # Manual freeze for specific month
    python db/scripts/freeze_month.py --month 2026-01 --dry-run
    python db/scripts/freeze_month.py --month 2026-01 --apply

    # Automatic freeze for previous month (for cron)
    python db/scripts/freeze_month.py --previous-month --apply

Cron setup (runs 1st of each month at 00:05 UTC):
    5 0 1 * * cd /path/to/SNI && python db/scripts/freeze_month.py --previous-month --apply >> /var/log/sni-freeze.log 2>&1
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2

from core.config import config

# Threshold for "large" CTMs that get LLM summaries
LARGE_CTM_THRESHOLD = 30

# Canned summary for small CTMs
SMALL_CTM_SUMMARY = "Limited coverage this month. See events for details."


def get_connection():
    return psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )


def get_month_stats(conn, month: str) -> dict:
    """Get statistics for CTMs in the target month."""
    cur = conn.cursor()

    # Total CTMs
    cur.execute(
        """
        SELECT COUNT(*) FROM ctm
        WHERE TO_CHAR(month, 'YYYY-MM') = %s
        """,
        (month,),
    )
    total = cur.fetchone()[0]

    # Already frozen
    cur.execute(
        """
        SELECT COUNT(*) FROM ctm
        WHERE TO_CHAR(month, 'YYYY-MM') = %s AND is_frozen = true
        """,
        (month,),
    )
    frozen = cur.fetchone()[0]

    # With summary
    cur.execute(
        """
        SELECT COUNT(*) FROM ctm
        WHERE TO_CHAR(month, 'YYYY-MM') = %s AND summary_text IS NOT NULL
        """,
        (month,),
    )
    with_summary = cur.fetchone()[0]

    # Large CTMs without summary
    cur.execute(
        """
        SELECT COUNT(*) FROM ctm
        WHERE TO_CHAR(month, 'YYYY-MM') = %s
          AND summary_text IS NULL
          AND title_count >= %s
        """,
        (month, LARGE_CTM_THRESHOLD),
    )
    large_no_summary = cur.fetchone()[0]

    # Small CTMs without summary (but with titles)
    cur.execute(
        """
        SELECT COUNT(*) FROM ctm
        WHERE TO_CHAR(month, 'YYYY-MM') = %s
          AND summary_text IS NULL
          AND title_count > 0
          AND title_count < %s
        """,
        (month, LARGE_CTM_THRESHOLD),
    )
    small_no_summary = cur.fetchone()[0]

    # Empty CTMs (no titles)
    cur.execute(
        """
        SELECT COUNT(*) FROM ctm
        WHERE TO_CHAR(month, 'YYYY-MM') = %s AND title_count = 0
        """,
        (month,),
    )
    empty = cur.fetchone()[0]

    return {
        "total": total,
        "frozen": frozen,
        "with_summary": with_summary,
        "large_no_summary": large_no_summary,
        "small_no_summary": small_no_summary,
        "empty": empty,
    }


def get_large_ctms_needing_summary(conn, month: str) -> list:
    """Get large CTMs that need LLM summaries."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, centroid_id, track, title_count
        FROM ctm
        WHERE TO_CHAR(month, 'YYYY-MM') = %s
          AND summary_text IS NULL
          AND title_count >= %s
          AND is_frozen = false
        ORDER BY title_count DESC
        """,
        (month, LARGE_CTM_THRESHOLD),
    )
    return cur.fetchall()


def get_small_ctms_needing_summary(conn, month: str) -> list:
    """Get small CTMs that need canned summaries."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, centroid_id, track, title_count
        FROM ctm
        WHERE TO_CHAR(month, 'YYYY-MM') = %s
          AND summary_text IS NULL
          AND title_count > 0
          AND title_count < %s
          AND is_frozen = false
        ORDER BY title_count DESC
        """,
        (month, LARGE_CTM_THRESHOLD),
    )
    return cur.fetchall()


def apply_canned_summaries(conn, month: str, dry_run: bool) -> int:
    """Apply canned summary to small CTMs."""
    small_ctms = get_small_ctms_needing_summary(conn, month)

    if not small_ctms:
        print("  No small CTMs need canned summaries")
        return 0

    print(f"  Applying canned summary to {len(small_ctms)} small CTMs...")

    if dry_run:
        for ctm_id, centroid, track, count in small_ctms[:5]:
            print(f"    [DRY-RUN] {centroid} / {track}: {count} titles")
        if len(small_ctms) > 5:
            print(f"    ... and {len(small_ctms) - 5} more")
        return len(small_ctms)

    cur = conn.cursor()
    cur.execute(
        """
        UPDATE ctm
        SET summary_text = %s, updated_at = NOW()
        WHERE TO_CHAR(month, 'YYYY-MM') = %s
          AND summary_text IS NULL
          AND title_count > 0
          AND title_count < %s
          AND is_frozen = false
        """,
        (SMALL_CTM_SUMMARY, month, LARGE_CTM_THRESHOLD),
    )
    updated = cur.rowcount
    conn.commit()
    print(f"  Applied canned summary to {updated} CTMs")
    return updated


async def generate_large_summaries(conn, month: str, dry_run: bool) -> int:
    """Generate LLM summaries for large CTMs."""
    from pipeline.phase_4.generate_summaries_4_5 import process_ctm_batch

    large_ctms = get_large_ctms_needing_summary(conn, month)

    if not large_ctms:
        print("  No large CTMs need LLM summaries")
        return 0

    print(f"  Generating LLM summaries for {len(large_ctms)} large CTMs...")

    if dry_run:
        for ctm_id, centroid, track, count in large_ctms:
            print(f"    [DRY-RUN] {centroid} / {track}: {count} titles")
        return len(large_ctms)

    # Process in batches
    await process_ctm_batch(max_ctms=len(large_ctms))
    return len(large_ctms)


def freeze_month(conn, month: str, dry_run: bool) -> int:
    """Set is_frozen=true for all CTMs in the month."""
    cur = conn.cursor()

    # Count unfrozen
    cur.execute(
        """
        SELECT COUNT(*) FROM ctm
        WHERE TO_CHAR(month, 'YYYY-MM') = %s AND is_frozen = false
        """,
        (month,),
    )
    unfrozen = cur.fetchone()[0]

    if unfrozen == 0:
        print("  All CTMs already frozen")
        return 0

    print(f"  Freezing {unfrozen} CTMs...")

    if dry_run:
        print(f"    [DRY-RUN] Would freeze {unfrozen} CTMs")
        return unfrozen

    cur.execute(
        """
        UPDATE ctm
        SET is_frozen = true, updated_at = NOW()
        WHERE TO_CHAR(month, 'YYYY-MM') = %s AND is_frozen = false
        """,
        (month,),
    )
    frozen = cur.rowcount
    conn.commit()
    print(f"  Frozen {frozen} CTMs")
    return frozen


def get_previous_month() -> str:
    """Get the previous month in YYYY-MM format."""
    today = datetime.now(timezone.utc)
    # Go to first day of current month, then subtract 1 day to get last month
    first_of_month = today.replace(day=1)
    last_month = first_of_month - timedelta(days=1)
    return last_month.strftime("%Y-%m")


async def main():
    parser = argparse.ArgumentParser(description="Freeze CTMs for a month")
    parser.add_argument("--month", type=str, help="Month to freeze (YYYY-MM)")
    parser.add_argument(
        "--previous-month",
        action="store_true",
        help="Automatically freeze the previous month (for cron jobs)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (required to make changes)"
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip LLM summary generation for large CTMs",
    )

    args = parser.parse_args()

    # Determine target month
    if args.previous_month:
        target_month = get_previous_month()
        print(f"Auto-detected previous month: {target_month}")
    elif args.month:
        target_month = args.month
    else:
        print("ERROR: Must specify --month YYYY-MM or --previous-month")
        sys.exit(1)

    if not args.dry_run and not args.apply:
        print("ERROR: Must specify --dry-run or --apply")
        sys.exit(1)

    dry_run = args.dry_run

    conn = get_connection()

    print("=" * 60)
    print(f"CTM FREEZE: {target_month}")
    print("=" * 60)

    # Get stats
    stats = get_month_stats(conn, target_month)
    print("\nMonth Statistics:")
    print(f"  Total CTMs: {stats['total']}")
    print(f"  Already frozen: {stats['frozen']}")
    print(f"  With summary: {stats['with_summary']}")
    print(
        f"  Large CTMs needing summary (>={LARGE_CTM_THRESHOLD} titles): {stats['large_no_summary']}"
    )
    print(
        f"  Small CTMs needing summary (<{LARGE_CTM_THRESHOLD} titles): {stats['small_no_summary']}"
    )
    print(f"  Empty CTMs (0 titles): {stats['empty']}")

    if stats["total"] == 0:
        print(f"\nNo CTMs found for {target_month}")
        conn.close()
        return

    # Step 1: Generate LLM summaries for large CTMs
    print("\nStep 1: LLM summaries for large CTMs")
    if args.skip_llm:
        print("  Skipped (--skip-llm)")
    else:
        await generate_large_summaries(conn, target_month, dry_run)

    # Step 2: Apply canned summaries to small CTMs
    print("\nStep 2: Canned summaries for small CTMs")
    apply_canned_summaries(conn, target_month, dry_run)

    # Step 3: Freeze all CTMs
    print("\nStep 3: Freeze all CTMs")
    freeze_month(conn, target_month, dry_run)

    # Final stats
    if not dry_run:
        final_stats = get_month_stats(conn, target_month)
        print("\nFinal Statistics:")
        print(f"  Frozen: {final_stats['frozen']}/{final_stats['total']}")
        print(f"  With summary: {final_stats['with_summary']}/{final_stats['total']}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
