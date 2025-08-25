#!/usr/bin/env python3
"""
Refresh materialized views for event signals pipeline in correct dependency order
"""

import logging
import os
import time

import psycopg2

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection using environment variables."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "narrative_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def refresh_materialized_view(conn, view_name):
    """Refresh a single materialized view with timing."""
    start_time = time.time()
    cur = conn.cursor()
    try:
        logger.info(f"Refreshing {view_name}...")
        cur.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}")
        conn.commit()
        elapsed = time.time() - start_time
        logger.info(f"✓ {view_name} refreshed successfully ({elapsed:.1f}s)")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to refresh {view_name}: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()


def main():
    """Refresh all event signals pipeline materialized views in dependency order."""
    logger.info("Starting event signals pipeline refresh")

    # Exact refresh order as specified
    refresh_order = [
        "shared_keywords_lib_norm_30d",
        "keyword_hubs_30d",
        "event_tokens_clean_30d",
        "eventlike_title_bigrams_30d",
        "event_signals_30d",
        "event_anchored_triads_30d",
    ]

    try:
        conn = get_db_connection()

        total_start = time.time()
        success_count = 0

        for view_name in refresh_order:
            if refresh_materialized_view(conn, view_name):
                success_count += 1
            else:
                logger.error(f"Stopping refresh pipeline due to failure on {view_name}")
                return False

        total_elapsed = time.time() - total_start
        logger.info(
            f"All {success_count}/{len(refresh_order)} views refreshed successfully ({total_elapsed:.1f}s total)"
        )

        # Get final counts for verification
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM event_signals_30d")
            signal_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM event_anchored_triads_30d")
            triad_count = cur.fetchone()[0]

            logger.info(
                f"Pipeline ready: {signal_count} event signals, {triad_count} triads"
            )

        finally:
            cur.close()

        return True

    except Exception as e:
        logger.error(f"Pipeline refresh failed: {e}")
        return False
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
