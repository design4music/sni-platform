"""Seed strategic_narratives from narrative_taxonomy_v2.yaml."""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import psycopg2
import psycopg2.extras

from core.config import config

YAML_PATH = Path(__file__).parent.parent.parent / "docs" / "narrative_taxonomy_v2.yaml"


def seed():
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        items = yaml.safe_load(f)

    if not items:
        print("No strategic narratives found in YAML")
        return

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )
    try:
        inserted = 0
        updated = 0
        with conn.cursor() as cur:
            for sn in items:
                cur.execute(
                    """
                    INSERT INTO strategic_narratives (
                        id, meta_narrative_id, category, actor_centroid,
                        name, claim, normative_conclusion,
                        keywords, action_classes, actor_prefixes, actor_types, domains
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s::text[], %s::text[], %s::text[], %s::text[], %s::text[]
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        meta_narrative_id = EXCLUDED.meta_narrative_id,
                        category = EXCLUDED.category,
                        actor_centroid = EXCLUDED.actor_centroid,
                        name = EXCLUDED.name,
                        claim = EXCLUDED.claim,
                        normative_conclusion = EXCLUDED.normative_conclusion,
                        keywords = EXCLUDED.keywords,
                        action_classes = EXCLUDED.action_classes,
                        actor_prefixes = EXCLUDED.actor_prefixes,
                        actor_types = EXCLUDED.actor_types,
                        domains = EXCLUDED.domains,
                        updated_at = now()
                    """,
                    (
                        sn["id"],
                        sn["meta_narrative"],
                        sn.get("category"),
                        sn.get("actor_centroid"),
                        sn["name"],
                        sn.get("claim", "").strip() if sn.get("claim") else None,
                        sn.get("normative_conclusion"),
                        sn.get("keywords"),
                        sn.get("action_classes"),
                        sn.get("actor_prefixes"),
                        sn.get("actor_types"),
                        sn.get("domains"),
                    ),
                )
                if cur.statusmessage == "INSERT 0 1":
                    inserted += 1
                else:
                    updated += 1
            conn.commit()
        print(
            "Strategic narratives: %d inserted, %d updated (%d total)"
            % (inserted, updated, len(items))
        )
    except Exception as e:
        conn.rollback()
        print("Seed failed: %s" % e)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
