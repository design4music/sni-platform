"""Seed meta_narratives from narrative_taxonomy.yaml."""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2
import psycopg2.extras

from core.config import config

YAML_PATH = Path(__file__).parent.parent.parent / "docs" / "narrative_taxonomy.yaml"


def seed():
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    rows = data.get("meta_narratives", [])
    if not rows:
        print("No meta_narratives found in YAML")
        return

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    try:
        with conn.cursor() as cur:
            for i, mn in enumerate(rows):
                cur.execute(
                    """
                    INSERT INTO meta_narratives (id, name, description, signals, sort_order)
                    VALUES (%s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        signals = EXCLUDED.signals,
                        sort_order = EXCLUDED.sort_order
                    """,
                    (
                        mn["id"],
                        mn["name"],
                        mn["description"].strip(),
                        psycopg2.extras.Json(mn.get("signals", {})),
                        i,
                    ),
                )
            conn.commit()
            print("Seeded %d meta_narratives" % len(rows))
    except Exception as e:
        conn.rollback()
        print("Seed failed: %s" % e)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
