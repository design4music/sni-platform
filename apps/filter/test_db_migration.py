#!/usr/bin/env python3
"""
Test script to validate CSV → DB migration for vocabulary loading
Compares entity counts and ensures DB-backed loader works correctly
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger  # noqa: E402


def test_db_loader():
    """Test database-backed vocabulary loader"""
    logger.info("Testing database-backed vocabulary loader...")

    from apps.filter.vocab_loader_db import (load_actor_aliases,
                                             load_go_people_aliases,
                                             validate_vocabularies)

    # Run validation
    validation = validate_vocabularies()

    logger.info("\n=== Database Vocabulary Validation ===")
    logger.info(f"Database accessible: {validation['db_accessible']}")
    logger.info(f"Actor entities: {validation['actors_count']}")
    logger.info(f"People entities: {validation['go_people_count']}")
    logger.info(f"Total actor aliases: {validation['total_actor_aliases']}")
    logger.info(f"Total people aliases: {validation['total_go_people_aliases']}")

    if validation["errors"]:
        logger.error("\nErrors encountered:")
        for error in validation["errors"]:
            logger.error(f"  - {error}")
        return False

    # Test individual loaders
    logger.info("\n=== Testing Individual Loaders ===")

    actors = load_actor_aliases()
    logger.info(f"Loaded {len(actors)} actor entities")
    if actors:
        sample_actor = list(actors.keys())[0]
        logger.info(f"  Sample: {sample_actor} → {actors[sample_actor][:3]}...")

    people = load_go_people_aliases()
    logger.info(f"Loaded {len(people)} people entities")
    if people:
        sample_person = list(people.keys())[0]
        logger.info(f"  Sample: {sample_person} → {people[sample_person][:3]}...")

    return True


def test_csv_loader():
    """Test legacy CSV-backed vocabulary loader"""
    logger.info("\nTesting legacy CSV vocabulary loader...")

    from apps.filter.vocab_loader import validate_vocabularies

    try:
        # Run validation
        validation = validate_vocabularies()

        logger.info("\n=== CSV Vocabulary Validation ===")
        logger.info(f"Actors file exists: {validation['actors_file_exists']}")
        logger.info(f"People file exists: {validation['go_people_file_exists']}")
        logger.info(f"Actor entities: {validation['actors_count']}")
        logger.info(f"People entities: {validation['go_people_count']}")
        logger.info(f"Total actor aliases: {validation['total_actor_aliases']}")
        logger.info(f"Total people aliases: {validation['total_go_people_aliases']}")

        if validation["errors"]:
            logger.error("\nErrors encountered:")
            for error in validation["errors"]:
                logger.error(f"  - {error}")
            return False

        return True
    except Exception as e:
        logger.warning(f"CSV loader not available: {e}")
        return False


def compare_csv_vs_db():
    """Compare CSV and DB loader outputs"""
    logger.info("\n" + "=" * 60)
    logger.info("COMPARING CSV vs DATABASE LOADERS")
    logger.info("=" * 60)

    try:
        # Load from CSV
        from apps.filter.vocab_loader import load_actor_aliases as csv_actors
        from apps.filter.vocab_loader import \
            load_go_people_aliases as csv_people

        csv_actor_dict = csv_actors()
        csv_people_dict = csv_people()

        # Load from DB
        from apps.filter.vocab_loader_db import load_actor_aliases as db_actors
        from apps.filter.vocab_loader_db import \
            load_go_people_aliases as db_people

        db_actor_dict = db_actors()
        db_people_dict = db_people()

        # Compare actors
        logger.info("\n=== ACTOR COMPARISON ===")
        logger.info(f"CSV actors: {len(csv_actor_dict)}")
        logger.info(f"DB actors: {len(db_actor_dict)}")

        csv_only = set(csv_actor_dict.keys()) - set(db_actor_dict.keys())
        db_only = set(db_actor_dict.keys()) - set(csv_actor_dict.keys())
        common = set(csv_actor_dict.keys()) & set(db_actor_dict.keys())

        if csv_only:
            logger.warning(f"Entities only in CSV: {len(csv_only)}")
            logger.warning(f"  Examples: {list(csv_only)[:5]}")

        if db_only:
            logger.info(f"Entities only in DB: {len(db_only)}")
            logger.info(f"  Examples: {list(db_only)[:5]}")

        logger.info(f"Common entities: {len(common)}")

        # Compare people
        logger.info("\n=== PEOPLE COMPARISON ===")
        logger.info(f"CSV people: {len(csv_people_dict)}")
        logger.info(f"DB people: {len(db_people_dict)}")

        csv_only = set(csv_people_dict.keys()) - set(db_people_dict.keys())
        db_only = set(db_people_dict.keys()) - set(csv_people_dict.keys())
        common = set(csv_people_dict.keys()) & set(db_people_dict.keys())

        if csv_only:
            logger.warning(f"Entities only in CSV: {len(csv_only)}")
            logger.warning(f"  Examples: {list(csv_only)[:5]}")

        if db_only:
            logger.info(f"Entities only in DB: {len(db_only)}")
            logger.info(f"  Examples: {list(db_only)[:5]}")

        logger.info(f"Common entities: {len(common)}")

    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        return False

    return True


def test_strategic_gate():
    """Test that strategic gate works with DB-backed loader"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING STRATEGIC GATE WITH DB LOADER")
    logger.info("=" * 60)

    from apps.filter.strategic_gate import StrategicGate

    try:
        gate = StrategicGate()
        logger.info("Successfully initialized StrategicGate with DB loader")

        # Test with sample titles
        test_cases = [
            "Biden announces new sanctions against Russia",
            "China increases military presence in Taiwan Strait",
            "Fashion Week debuts new designer collections",
            "NATO discusses security arrangements",
            "Celebrity wedding breaks internet records",
        ]

        logger.info("\n=== Testing Sample Titles ===")
        for title in test_cases:
            result = gate.filter_title(title)
            status = "KEEP" if result.keep else "REJECT"
            logger.info(f"[{status}] {title}")
            logger.info(f"  Reason: {result.reason}, Actor: {result.actor_hit}")

        return True

    except Exception as e:
        logger.error(f"Strategic gate test failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("VOCABULARY LOADER MIGRATION TEST")
    logger.info("=" * 60)

    # Test DB loader
    db_success = test_db_loader()

    # Test CSV loader (if available)
    csv_success = test_csv_loader()

    # Compare if both available
    if db_success and csv_success:
        compare_csv_vs_db()

    # Test strategic gate integration
    gate_success = test_strategic_gate()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Database loader: {'PASS' if db_success else 'FAIL'}")
    logger.info(f"CSV loader: {'PASS' if csv_success else 'FAIL/SKIPPED'}")
    logger.info(f"Strategic gate: {'PASS' if gate_success else 'FAIL'}")

    if db_success and gate_success:
        logger.info("\nMIGRATION SUCCESSFUL - Ready to use DB-backed vocabularies!")
    else:
        logger.error("\nMIGRATION INCOMPLETE - Check errors above")
