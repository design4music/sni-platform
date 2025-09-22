#!/usr/bin/env python3
"""
Verify Migration 005: EF Context Enhancement
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from sqlalchemy import inspect, text

from core.database import get_db_session


def verify_migration():
    """Verify the EF context enhancement migration was applied correctly"""

    logger.info("Verifying Migration 005: EF Context Enhancement...")

    try:
        with get_db_session() as session:
            inspector = inspect(session.bind)

            # 1. Check event_families table changes
            logger.info("Checking event_families table...")
            ef_columns = {
                col["name"] for col in inspector.get_columns("event_families")
            }

            # Verify removed columns
            removed_fields = {"promotion_score", "event_start", "event_end"}
            still_present = removed_fields.intersection(ef_columns)
            if still_present:
                logger.error(
                    f"Fields should be removed but still present: {still_present}"
                )
                return False
            logger.success(f"✓ Removed fields: {removed_fields}")

            # Verify kept field
            if "confidence_score" not in ef_columns:
                logger.error("confidence_score field was incorrectly removed")
                return False
            logger.success("✓ Kept field: confidence_score")

            # Verify added field
            if "ef_context" not in ef_columns:
                logger.error("ef_context field was not added")
                return False
            logger.success("✓ Added field: ef_context")

            # 2. Check centroids table
            logger.info("Checking centroids table...")
            tables = inspector.get_table_names()
            if "centroids" not in tables:
                logger.error("centroids table was not created")
                return False

            centroids_columns = {
                col["name"] for col in inspector.get_columns("centroids")
            }
            expected_centroids_cols = {
                "id",
                "label",
                "keywords",
                "actors",
                "theaters",
                "created_at",
                "updated_at",
            }
            if not expected_centroids_cols.issubset(centroids_columns):
                missing = expected_centroids_cols - centroids_columns
                logger.error(f"Missing centroids columns: {missing}")
                return False
            logger.success("✓ Centroids table created with correct columns")

            # 3. Check centroids data
            logger.info("Checking centroids data...")
            result = session.execute(text("SELECT COUNT(*) FROM centroids")).scalar()
            if result != 25:
                logger.error(f"Expected 25 centroids, found {result}")
                return False
            logger.success(f"✓ Found {result} centroids")

            # 4. Check indexes
            logger.info("Checking indexes...")
            indexes = inspector.get_indexes("event_families")
            ef_index_names = {idx["name"] for idx in indexes}
            expected_ef_indexes = {
                "idx_event_families_ef_context",
                "idx_event_families_primary_theater",
            }

            centroids_indexes = inspector.get_indexes("centroids")
            centroids_index_names = {idx["name"] for idx in centroids_indexes}
            expected_centroids_indexes = {
                "idx_centroids_keywords",
                "idx_centroids_actors",
                "idx_centroids_theaters",
            }

            ef_missing = expected_ef_indexes - ef_index_names
            centroids_missing = expected_centroids_indexes - centroids_index_names

            if ef_missing:
                logger.warning(f"Missing event_families indexes: {ef_missing}")
            if centroids_missing:
                logger.warning(f"Missing centroids indexes: {centroids_missing}")

            if not ef_missing and not centroids_missing:
                logger.success("✓ All expected indexes found")

            # 5. Check trigger function
            logger.info("Checking trigger function...")
            result = session.execute(
                text(
                    "SELECT COUNT(*) FROM pg_proc WHERE proname = 'update_updated_at_column'"
                )
            ).scalar()
            if result == 0:
                logger.error("update_updated_at_column function not found")
                return False
            logger.success("✓ Trigger function exists")

            # 6. Sample a few centroids
            logger.info("Sampling centroid data...")
            sample_centroids = session.execute(
                text("SELECT id, label FROM centroids LIMIT 5")
            ).fetchall()
            for centroid in sample_centroids:
                logger.info(f"  {centroid.id}: {centroid.label}")

        logger.success("🎉 Migration 005 verification completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


if __name__ == "__main__":
    success = verify_migration()
    sys.exit(0 if success else 1)
