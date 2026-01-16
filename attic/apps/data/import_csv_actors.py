#!/usr/bin/env python3
"""
Import actors from actors.csv with Wikidata enrichment
Uses existing curated list, enriches with multi-lingual aliases
Handles countries, organizations, regions, movements
"""

import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, List

import requests
from loguru import logger
from sqlalchemy import text

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.config import get_config  # noqa: E402
from core.database import get_db_session  # noqa: E402

# Wikidata SPARQL endpoint
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
REQUEST_DELAY = 1.0


def query_wikidata(sparql_query: str) -> List[Dict]:
    """Execute SPARQL query against Wikidata and return results"""
    headers = {"Accept": "application/json", "User-Agent": "SNI-v2-EntityImporter/1.0"}

    try:
        response = requests.get(
            WIKIDATA_SPARQL,
            params={"query": sparql_query, "format": "json"},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        return data.get("results", {}).get("bindings", [])

    except Exception as e:
        logger.error(f"Wikidata query failed: {e}")
        return []


def fetch_multilingual_labels(qid: str) -> Dict[str, List[str]]:
    """Fetch labels and aliases for an entity in multiple languages"""
    if not qid:
        return {}

    query = f"""
    SELECT ?label ?lang WHERE {{
      VALUES ?item {{ wd:{qid} }}
      {{ ?item rdfs:label ?label. }}
      UNION
      {{ ?item skos:altLabel ?label. }}
      BIND(LANG(?label) AS ?lang)
      FILTER(?lang IN ("en", "es", "fr", "de", "it", "ru", "zh", "ar", "hi", "ja"))
    }}
    """

    results = query_wikidata(query)

    aliases = {}
    for binding in results:
        label = binding.get("label", {}).get("value", "")
        lang = binding.get("lang", {}).get("value", "")

        if label and lang:
            if lang not in aliases:
                aliases[lang] = []
            if label not in aliases[lang]:
                aliases[lang].append(label)

    return aliases


def parse_csv_aliases(row: Dict) -> Dict[str, List[str]]:
    """Parse aliases from CSV columns"""
    aliases = {}

    # Map CSV columns to language codes
    lang_columns = {
        "en": "aliases_en",
        "es": "aliases_es",
        "fr": "aliases_fr",
        "de": "aliases_de",
        "it": "aliases_it",
        "ru": "aliases_ru",
        "zh": "aliases_zh",
        "ar": "aliases_ar",
        "hi": "aliases_hi",
        "ja": "aliases_ja",
    }

    for lang, col in lang_columns.items():
        aliases_str = row.get(col, "").strip()
        if aliases_str:
            # Split by pipe, clean up
            alias_list = [a.strip() for a in aliases_str.split("|") if a.strip()]
            if alias_list:
                aliases[lang] = alias_list

    return aliases


def merge_aliases(
    csv_aliases: Dict[str, List[str]], wikidata_aliases: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """Merge CSV and Wikidata aliases, preferring CSV"""
    merged = csv_aliases.copy()

    for lang, labels in wikidata_aliases.items():
        if lang in merged:
            # Add Wikidata aliases that aren't already in CSV
            for label in labels:
                if label not in merged[lang]:
                    merged[lang].append(label)
        else:
            # No CSV aliases for this language, use Wikidata
            merged[lang] = labels

    return merged


def determine_entity_type(kind: str) -> str:
    """
    Map CSV 'kind' field to entity_type enum.

    Args:
        kind: Value from actors.csv kind column

    Returns:
        Entity type: COUNTRY, ORG, CAPITAL, or ORG (default)
    """
    kind_lower = kind.lower().strip()

    if kind_lower == "country":
        return "COUNTRY"
    elif kind_lower == "capital":
        return "CAPITAL"
    elif kind_lower in ["org", "organization", "movement", "region", "alliance"]:
        return "ORG"
    else:
        # Default to ORG for unknown kinds
        logger.warning(f"Unknown kind '{kind}', defaulting to ORG")
        return "ORG"


def import_actors_from_csv():
    """Import actors from actors.csv with Wikidata enrichment"""
    config = get_config()
    csv_path = config.project_root / "data" / "actors.csv"

    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return

    logger.info(f"Reading actors from {csv_path}")

    actors = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity_id = row.get("entity_id", "").strip()
            kind = row.get("kind", "").strip()
            iso_code = row.get("iso_code", "").strip()
            wikidata_qid = row.get("wikidata_qid", "").strip()

            # Parse CSV aliases
            csv_aliases = parse_csv_aliases(row)

            # Get name from aliases_en (first one) or entity_id
            name_en = csv_aliases.get("en", [entity_id.replace("_", " ").title()])[0]

            # Get domain hints
            domains_hint = row.get("domains_hint", "").strip()
            domains = domains_hint.split("|") if domains_hint else []

            # Determine entity type
            entity_type = determine_entity_type(kind)

            actors.append(
                {
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "iso_code": iso_code if iso_code else None,
                    "wikidata_qid": wikidata_qid,
                    "name_en": name_en,
                    "domains_hint": domains,
                    "csv_aliases": csv_aliases,
                }
            )

    logger.info(f"Found {len(actors)} actors in CSV")

    # Enrich with Wikidata aliases
    enriched_count = 0
    with get_db_session() as session:
        for i, actor in enumerate(actors):
            entity_id = actor["entity_id"]
            wikidata_qid = actor["wikidata_qid"]
            name_en = actor["name_en"]

            logger.info(f"Processing {entity_id} ({i+1}/{len(actors)})")

            # Get CSV aliases
            csv_aliases = actor.get("csv_aliases", {})

            # Fetch multi-lingual aliases from Wikidata
            if wikidata_qid:
                logger.info(
                    f"  Fetching Wikidata aliases for {name_en} (Q{wikidata_qid})"
                )
                wikidata_aliases = fetch_multilingual_labels(wikidata_qid)
                time.sleep(REQUEST_DELAY)

                # Merge CSV (priority) with Wikidata
                aliases = merge_aliases(csv_aliases, wikidata_aliases)
                enriched_count += 1
            else:
                logger.warning(
                    f"  No Wikidata QID for {entity_id}, using CSV aliases only"
                )
                aliases = csv_aliases

            # Insert into database
            try:
                stmt = text(
                    """
                    INSERT INTO data_entities
                    (entity_id, entity_type, iso_code, wikidata_qid, name_en,
                     aliases, domains_hint)
                    VALUES
                    (:entity_id, :entity_type, :iso_code, :wikidata_qid, :name_en,
                     :aliases, :domains_hint)
                    ON CONFLICT (entity_id) DO UPDATE SET
                        entity_type = EXCLUDED.entity_type,
                        iso_code = EXCLUDED.iso_code,
                        wikidata_qid = EXCLUDED.wikidata_qid,
                        name_en = EXCLUDED.name_en,
                        aliases = EXCLUDED.aliases,
                        domains_hint = EXCLUDED.domains_hint,
                        updated_at = NOW()
                """
                )

                session.execute(
                    stmt,
                    {
                        "entity_id": entity_id,
                        "entity_type": actor["entity_type"],
                        "iso_code": actor.get("iso_code"),
                        "wikidata_qid": wikidata_qid if wikidata_qid else None,
                        "name_en": name_en,
                        "aliases": json.dumps(aliases),
                        "domains_hint": actor.get("domains_hint"),
                    },
                )

                logger.info(
                    f"  ✓ Inserted/updated {entity_id} ({actor['entity_type']})"
                )

            except Exception as e:
                logger.error(f"  ✗ Failed to insert {entity_id}: {e}")

        session.commit()

    logger.info("\n=== Import Complete ===")
    logger.info(f"Total actors imported: {len(actors)}")
    logger.info(f"Enriched with Wikidata: {enriched_count}")

    # Show summary by entity type
    with get_db_session() as session:
        result = session.execute(
            text(
                """
            SELECT entity_type, COUNT(*) as count
            FROM data_entities
            WHERE entity_type IN ('COUNTRY', 'ORG', 'CAPITAL')
            GROUP BY entity_type
            ORDER BY entity_type
        """
            )
        )

        logger.info("\nEntity counts by type:")
        for row in result:
            logger.info(f"  {row.entity_type}: {row.count}")


if __name__ == "__main__":
    import_actors_from_csv()
