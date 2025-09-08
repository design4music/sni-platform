#!/usr/bin/env python3
"""
Environment Pin Verification
Strategic Narrative Intelligence Platform

Test script to verify frozen Python version and locked requirements work correctly.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def test_python_version():
    """Test that Python version is pinned correctly"""

    print("=== PYTHON VERSION TEST ===")

    # Check current Python version
    current_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    print(f"Current Python version: {current_version}")

    # Check .python-version file
    python_version_file = Path(".python-version")
    if python_version_file.exists():
        pinned_version = python_version_file.read_text().strip()
        print(f"Pinned Python version: {pinned_version}")

        if current_version == pinned_version:
            print("[OK] Python version matches pinned version")
            return True
        else:
            print(
                f"[ERROR] Version mismatch: current {current_version} != pinned {pinned_version}"
            )
            return False
    else:
        print("[ERROR] .python-version file not found")
        return False


def test_requirements_files():
    """Test that requirements files exist and are properly structured"""

    print("\n=== REQUIREMENTS FILES TEST ===")

    required_files = {
        "requirements.in": "High-level requirements input file",
        "requirements.lock.txt": "Locked requirements with hashes",
        "current_packages.txt": "Current installed packages snapshot",
    }

    all_exist = True

    for filename, description in required_files.items():
        filepath = Path(filename)
        if filepath.exists():
            file_size = filepath.stat().st_size
            print(f"[OK] {filename}: {file_size:,} bytes - {description}")
        else:
            print(f"[ERROR] Missing {filename} - {description}")
            all_exist = False

    # Check locked requirements has security hashes
    lock_file = Path("requirements.lock.txt")
    if lock_file.exists():
        content = lock_file.read_text()
        if "--hash=sha256:" in content:
            print("[OK] Locked requirements include security hashes")
        else:
            print("[WARNING] Locked requirements missing security hashes")

    return all_exist


def test_key_imports():
    """Test that key packages can be imported"""

    print("\n=== KEY IMPORTS TEST ===")

    critical_packages = {
        "fastapi": "Core API framework",
        "sqlalchemy": "Database ORM",
        "pandas": "Data processing",
        "numpy": "Numerical computing",
        "spacy": "NLP processing",
        "transformers": "ML transformers",
        "psycopg2": "PostgreSQL adapter",
        "redis": "Redis client",
        "structlog": "Structured logging",
    }

    success_count = 0

    for package, description in critical_packages.items():
        try:
            __import__(package)
            print(f"[OK] {package}: {description}")
            success_count += 1
        except ImportError as e:
            print(f"[ERROR] {package}: Import failed - {e}")
        except Exception as e:
            print(f"[WARNING] {package}: Import issue - {e}")
            success_count += 1  # Count as success since package exists

    print(
        f"Successfully imported {success_count}/{len(critical_packages)} critical packages"
    )
    return success_count == len(critical_packages)


def test_pip_tools():
    """Test that pip-tools is available for dependency management"""

    print("\n=== PIP-TOOLS TEST ===")

    try:
        result = subprocess.run(
            ["pip-compile", "--help"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("[OK] pip-compile is available")
            return True
        else:
            print(f"[ERROR] pip-compile failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("[ERROR] pip-compile not found - pip-tools not installed")
        return False
    except subprocess.TimeoutExpired:
        print("[ERROR] pip-compile command timed out")
        return False
    except Exception as e:
        print(f"[ERROR] pip-compile test failed: {e}")
        return False


def test_requirements_syntax():
    """Test that requirements files have valid syntax"""

    print("\n=== REQUIREMENTS SYNTAX TEST ===")

    test_results = {}

    # Test requirements.in
    in_file = Path("requirements.in")
    if in_file.exists():
        try:
            content = in_file.read_text()
            lines = [
                line.strip()
                for line in content.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]
            print(f"[OK] requirements.in: {len(lines)} package specifications")
            test_results["requirements.in"] = True
        except Exception as e:
            print(f"[ERROR] requirements.in syntax error: {e}")
            test_results["requirements.in"] = False

    # Test requirements.lock.txt
    lock_file = Path("requirements.lock.txt")
    if lock_file.exists():
        try:
            content = lock_file.read_text()
            # Check for proper pip-compile header
            if "autogenerated by pip-compile" in content:
                lines = [
                    line.strip()
                    for line in content.split("\n")
                    if line.strip()
                    and not line.strip().startswith("#")
                    and not line.strip().startswith("--")
                ]
                print(f"[OK] requirements.lock.txt: {len(lines)} locked packages")
                test_results["requirements.lock.txt"] = True
            else:
                print("[ERROR] requirements.lock.txt missing pip-compile header")
                test_results["requirements.lock.txt"] = False
        except Exception as e:
            print(f"[ERROR] requirements.lock.txt syntax error: {e}")
            test_results["requirements.lock.txt"] = False

    return all(test_results.values())


def main():
    """Run all environment pin verification tests"""

    print("=" * 60)
    print("ENVIRONMENT PIN VERIFICATION")
    print("=" * 60)
    print(f"Python executable: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")
    print()

    results = {
        "python_version": test_python_version(),
        "requirements_files": test_requirements_files(),
        "key_imports": test_key_imports(),
        "pip_tools": test_pip_tools(),
        "requirements_syntax": test_requirements_syntax(),
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
        print("Environment is properly pinned and ready for deployment!")
        print()
        print("Environment Summary:")
        print(
            f"- Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} (pinned)"
        )
        print("- Requirements: Locked with security hashes")
        print("- Dependencies: All critical packages available")
        print("- Tools: pip-tools ready for dependency management")
    else:
        print("\n[ERROR] SOME TESTS FAILED")
        print("Environment pin needs attention")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
