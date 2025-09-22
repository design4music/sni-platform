#!/usr/bin/env python3
"""
Check centroids data
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from sqlalchemy import text

from core.database import get_db_session


def check_centroids():
    """Check centroid data"""

    try:
        with get_db_session() as session:
            # Get all centroids
            result = session.execute(
                text("SELECT id, label FROM centroids ORDER BY id")
            ).fetchall()

            logger.info(f"Found {len(result)} centroids:")
            for centroid in result:
                logger.info(f"  {centroid.id}: {centroid.label}")

            # Check for duplicates
            ids = [c.id for c in result]
            duplicates = [id for id in set(ids) if ids.count(id) > 1]
            if duplicates:
                logger.error(f"Duplicate IDs found: {duplicates}")
            else:
                logger.success("No duplicate IDs found")

    except Exception as e:
        logger.error(f"Check failed: {e}")


if __name__ == "__main__":
    check_centroids()
