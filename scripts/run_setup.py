#!/usr/bin/env python3
"""
SNI-v2 Complete Setup Runner
One-command setup for the entire SNI-v2 system
"""

import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger


def run_command(cmd, description, cwd=None):
    """Run a command and handle errors"""
    logger.info(f"Running: {description}")

    try:
        subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd or project_root,
        )
        logger.success(f"✅ {description}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed:")
        logger.error(f"Command: {cmd}")
        logger.error(f"Error: {e.stderr}")
        return False


def check_prerequisites():
    """Check if required tools are available"""
    logger.info("Checking prerequisites...")

    checks = {
        "python --version": "Python",
        "psql --version": "PostgreSQL client",
        "createdb --version": "PostgreSQL createdb",
    }

    all_good = True
    for cmd, tool in checks.items():
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
            logger.success(f"✅ {tool} available")
        except subprocess.CalledProcessError:
            logger.warning(f"⚠️  {tool} not found (some features may not work)")
            if tool == "Python":
                all_good = False

    return all_good


def install_python_packages():
    """Install Python dependencies"""
    return run_command("pip install -r requirements.txt", "Installing Python packages")


def setup_environment():
    """Setup environment file"""
    env_template = project_root / ".env.template"
    env_file = project_root / ".env"

    if not env_file.exists() and env_template.exists():
        env_file.write_text(env_template.read_text())
        logger.info("Created .env file from template - please edit with your settings")
        return True
    else:
        logger.info(".env file already exists")
        return True


def create_database():
    """Create the SNI database"""
    return run_command(
        "python scripts/setup_database.py", "Creating database and tables"
    )


def download_spacy_models():
    """Download required spaCy models"""
    models = ["en_core_web_sm"]  # Start with English

    success = True
    for model in models:
        if not run_command(
            f"python -m spacy download {model}", f"Downloading spaCy model: {model}"
        ):
            success = False

    return success


def verify_setup():
    """Verify the setup is working"""
    logger.info("Verifying setup...")

    # Test imports
    try:
        from core.config import get_config
        from core.database import check_database_connection, get_database_stats

        config = get_config()
        logger.info(f"✅ Configuration loaded - Database: {config.database.name}")

        if check_database_connection():
            logger.success("✅ Database connection successful")

            stats = get_database_stats()
            logger.info("Database tables:")
            for table, count in stats.items():
                logger.info(f"  📋 {table}: {count}")

            return True
        else:
            logger.error("❌ Database connection failed")
            return False

    except Exception as e:
        logger.error(f"❌ Setup verification failed: {e}")
        return False


def main():
    """Main setup function"""
    logger.info("🚀 Starting SNI-v2 complete setup...")

    # Step 1: Check prerequisites
    if not check_prerequisites():
        logger.error("Prerequisites check failed")
        sys.exit(1)

    # Step 2: Setup environment
    if not setup_environment():
        logger.error("Environment setup failed")
        sys.exit(1)

    # Step 3: Install Python packages
    if not install_python_packages():
        logger.error("Python package installation failed")
        sys.exit(1)

    # Step 4: Download spaCy models
    if not download_spacy_models():
        logger.warning(
            "Some spaCy models failed to download - multilingual features may be limited"
        )

    # Step 5: Create database
    if not create_database():
        logger.error("Database setup failed")
        sys.exit(1)

    # Step 6: Verify setup
    if not verify_setup():
        logger.error("Setup verification failed")
        sys.exit(1)

    logger.success("🎉 SNI-v2 setup completed successfully!")
    logger.info(
        """
Next steps:
1. Edit .env file with your actual database credentials
2. Run: python scripts/test_setup.py to validate everything works
3. Start developing or run the API: python api/main.py
    """
    )


if __name__ == "__main__":
    main()
