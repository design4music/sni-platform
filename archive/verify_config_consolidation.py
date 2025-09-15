#!/usr/bin/env python3
"""
Configuration Consolidation Verification
Strategic Narrative Intelligence Platform

Verifies that all scripts use centralized configuration and PostgreSQL extensions are available.
"""

import os
import sys

# Add project root to path
sys.path.append(".")


def test_centralized_config():
    """Test that centralized config is accessible and complete"""

    print("=== CENTRALIZED CONFIGURATION TEST ===")

    try:
        from etl_pipeline.core.config import get_config

        config = get_config()

        print("[OK] Centralized config import successful")

        # Test database config
        print(f"Database: {config.database.database}")
        print(f"Host: {config.database.host}:{config.database.port}")
        print(f"User: {config.database.username}")
        print(f"Password configured: {'Yes' if config.database.password else 'No'}")

        # Test Redis config
        print(f"Redis: {config.redis.host}:{config.redis.port}")
        print(f"Redis password configured: {'Yes' if config.redis.password else 'No'}")

        # Test API config
        print(f"API: {config.api.host}:{config.api.port}")
        print(f"Secret key configured: {'Yes' if config.api.secret_key else 'No'}")

        # Validate configuration
        validation_errors = config.validate()
        if validation_errors:
            print("[WARNING] Configuration validation issues:")
            for error in validation_errors:
                print(f"  - {error}")
        else:
            print("[OK] Configuration validation passed")

        return True

    except Exception as e:
        print(f"[ERROR] Centralized config test failed: {e}")
        return False


def test_database_extensions():
    """Test PostgreSQL extensions are available"""

    print("\n=== POSTGRESQL EXTENSIONS TEST ===")

    try:
        from etl_pipeline.core.config import get_config
        from etl_pipeline.core.database import (get_db_session,
                                                initialize_database)
        from sqlalchemy import text

        config = get_config()
        initialize_database(config.database)

        with get_db_session() as db:
            print("[OK] Database connection successful")

            # Check required extensions
            required_extensions = ["vector", "pg_trgm"]

            for ext_name in required_extensions:
                result = db.execute(
                    text("SELECT 1 FROM pg_extension WHERE extname = :ext"),
                    {"ext": ext_name},
                )
                if result.fetchone():
                    print(f"[OK] {ext_name} extension is available")
                else:
                    print(f"[ERROR] {ext_name} extension is NOT available")
                    return False

            return True

    except Exception as e:
        print(f"[ERROR] Database extensions test failed: {e}")
        return False


def test_script_compatibility():
    """Test that key scripts can import and use centralized config"""

    print("\n=== SCRIPT COMPATIBILITY TEST ===")

    scripts_to_test = [
        "cleanup_keywords.py",
        "clean_old_clusters.py",
        "test_reality_check.py",
        "strategic_narrative_api.py",
    ]

    success_count = 0

    for script in scripts_to_test:
        try:
            if os.path.exists(script):
                # Check if script imports centralized config
                with open(script, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "from etl_pipeline.core.config import get_config" in content:
                        print(f"[OK] {script} uses centralized config")
                        success_count += 1
                    elif "get_config()" in content:
                        print(f"[OK] {script} uses centralized config")
                        success_count += 1
                    else:
                        print(f"[WARNING] {script} may not use centralized config")
            else:
                print(f"[WARNING] {script} not found")

        except Exception as e:
            print(f"[ERROR] Error checking {script}: {e}")

    print(f"Scripts using centralized config: {success_count}/{len(scripts_to_test)}")
    return success_count == len(scripts_to_test)


def main():
    """Run all configuration consolidation tests"""

    print("=" * 60)
    print("CONFIGURATION CONSOLIDATION VERIFICATION")
    print("=" * 60)
    print()

    results = {
        "centralized_config": test_centralized_config(),
        "database_extensions": test_database_extensions(),
        "script_compatibility": test_script_compatibility(),
    }

    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS")
    print("=" * 60)

    for test_name, result in results.items():
        status = "[OK]" if result else "[ERROR]"
        print(f"{status} {test_name.replace('_', ' ').title()}")

    all_passed = all(results.values())

    if all_passed:
        print("\n[OK] ALL TESTS PASSED")
        print("Configuration consolidation is successful!")
        print("Single config surface established with .env and config.py")
        print("PostgreSQL extensions (vector, pg_trgm) are available")
        print("Scripts use centralized configuration")
    else:
        print("\n[ERROR] SOME TESTS FAILED")
        print("Configuration consolidation needs attention")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
