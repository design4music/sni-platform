"""Run SQL migration file."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from core.config import config


def run_migration(sql_file: str):
    """Run a SQL migration file."""
    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    with open(sql_file, "r") as f:
        sql = f.read()

    cur = conn.cursor()
    print("Running migration: %s" % sql_file)

    try:
        cur.execute(sql)
        conn.commit()
        print("Migration completed successfully")
    except Exception as e:
        conn.rollback()
        print("Migration failed: %s" % e)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python db/run_migration.py <sql_file>")
        sys.exit(1)

    run_migration(sys.argv[1])
