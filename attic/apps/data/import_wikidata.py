#!/usr/bin/env python3
"""
Import entities from Wikidata to data_entities table
Expands beyond CSV files to get comprehensive entity coverage
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
from loguru import logger
from sqlalchemy import text

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database import get_db_session  # noqa: E402

# Wikidata SPARQL endpoint
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

# Rate limiting: Wikidata allows ~60 requests/minute
REQUEST_DELAY = 1.0  # seconds between requests


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


def extract_value(binding: Dict, key: str) -> Optional[str]:
    """Extract value from SPARQL binding"""
    if key in binding:
        return binding[key].get("value", "").split("/")[-1]  # Get QID or value
    return None


def fetch_multilingual_labels(qid: str) -> Dict[str, List[str]]:
    """Fetch labels and aliases for an entity in multiple languages"""
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
            if label not in aliases[lang]:  # Avoid duplicates
                aliases[lang].append(label)

    return aliases


def fetch_countries_with_capitals() -> List[Dict]:
    """Fetch all countries with their capitals from Wikidata"""
    logger.info("Fetching countries with capitals from Wikidata...")

    # First get basic country list
    query = """
    SELECT DISTINCT ?country ?countryLabel ?iso ?capital ?capitalLabel
    WHERE {
      ?country wdt:P31 wd:Q6256;          # Instance of country
               wdt:P297 ?iso.              # ISO 3166-1 alpha-2 code

      OPTIONAL { ?country wdt:P36 ?capital. }  # Capital

      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en".
      }
    }
    ORDER BY ?iso
    """

    results = query_wikidata(query)

    countries = []
    seen_iso = set()

    for i, binding in enumerate(results):
        iso = extract_value(binding, "iso")
        if not iso or iso in seen_iso:
            continue

        seen_iso.add(iso)

        country_qid = extract_value(binding, "country")
        country_name = binding.get("countryLabel", {}).get("value", "")
        capital_qid = extract_value(binding, "capital")
        capital_name = binding.get("capitalLabel", {}).get("value", "")

        # Fetch multi-lingual aliases for country
        logger.info(f"Fetching aliases for {country_name} ({i+1}/{len(results)})")
        country_aliases = fetch_multilingual_labels(country_qid)
        time.sleep(REQUEST_DELAY)

        countries.append(
            {
                "entity_id": iso,
                "entity_type": "COUNTRY",
                "iso_code": iso,
                "wikidata_qid": country_qid,
                "name_en": country_name,
                "capital_qid": capital_qid,
                "capital_name": capital_name,
                "aliases": country_aliases,
            }
        )

        # Add capital as separate entity
        if capital_qid and capital_name:
            logger.info(f"Fetching aliases for capital {capital_name}")
            capital_aliases = fetch_multilingual_labels(capital_qid)
            time.sleep(REQUEST_DELAY)

            countries.append(
                {
                    "entity_id": f"{iso}_CAPITAL",
                    "entity_type": "CAPITAL",
                    "iso_code": iso,
                    "wikidata_qid": capital_qid,
                    "name_en": capital_name,
                    "country_entity_id": iso,
                    "aliases": capital_aliases,
                }
            )

    logger.info(f"Fetched {len(countries)} country/capital entities")
    return countries


def fetch_organizations() -> List[Dict]:
    """Fetch major international organizations from Wikidata"""
    logger.info("Fetching organizations from Wikidata...")

    # Major intergovernmental organizations
    org_qids = [
        "Q458",  # EU
        "Q7184",  # NATO
        "Q1065",  # UN
        "Q7825",  # UNSC
        "Q7817",  # WHO
        "Q188354",  # IMF
        "Q7164",  # World Bank
        "Q80985",  # GCC
        "Q7159",  # African Union
        "Q7172",  # Arab League
        "Q133255",  # SCO
        "Q476033",  # ASEAN
        "Q166864",  # G20
        "Q170481",  # G7
        "Q4173083",  # EAEU
        "Q4264",  # MERCOSUR
    ]

    query = f"""
    SELECT ?org ?orgLabel
    WHERE {{
      VALUES ?org {{ {' '.join(f'wd:{qid}' for qid in org_qids)} }}

      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en".
      }}
    }}
    """

    results = query_wikidata(query)

    organizations = []
    for i, binding in enumerate(results):
        org_qid = extract_value(binding, "org")
        org_name = binding.get("orgLabel", {}).get("value", "")

        # Fetch multi-lingual aliases
        logger.info(f"Fetching aliases for {org_name} ({i+1}/{len(results)})")
        org_aliases = fetch_multilingual_labels(org_qid)
        time.sleep(REQUEST_DELAY)

        # Generate entity_id from name
        entity_id = org_name.upper().replace(" ", "_").replace("-", "_")
        entity_id = "".join(c for c in entity_id if c.isalnum() or c == "_")

        organizations.append(
            {
                "entity_id": entity_id,
                "entity_type": "ORG",
                "wikidata_qid": org_qid,
                "name_en": org_name,
                "aliases": org_aliases,
            }
        )

    logger.info(f"Fetched {len(organizations)} organizations")
    return organizations


def fetch_current_leaders() -> List[Dict]:
    """Fetch current heads of state/government from Wikidata"""
    logger.info("Fetching current world leaders from Wikidata...")

    query = """
    SELECT DISTINCT ?person ?personLabel ?countryISO ?position ?positionLabel
    WHERE {
      # Heads of state or government
      VALUES ?position { wd:Q48352 wd:Q2285706 }  # Head of state, head of government

      ?person wdt:P39 ?position;           # Position held
              wdt:P27 ?country.            # Country of citizenship

      ?country wdt:P297 ?countryISO.       # Get ISO code

      # Filter to current (no end date)
      FILTER NOT EXISTS { ?person p:P39/pq:P582 ?endDate. }

      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en".
      }
    }
    LIMIT 100
    """

    results = query_wikidata(query)

    leaders = []
    seen_persons = set()

    for i, binding in enumerate(results):
        person_qid = extract_value(binding, "person")
        if person_qid in seen_persons:
            continue

        seen_persons.add(person_qid)

        person_name = binding.get("personLabel", {}).get("value", "")
        country_iso = extract_value(binding, "countryISO")

        # Fetch multi-lingual aliases
        logger.info(f"Fetching aliases for {person_name} ({i+1}/{len(seen_persons)})")
        person_aliases = fetch_multilingual_labels(person_qid)
        time.sleep(REQUEST_DELAY)

        # Generate entity_id from name
        entity_id = person_name.lower().replace(" ", "_").replace("-", "_")
        entity_id = "".join(c for c in entity_id if c.isalnum() or c == "_")

        leaders.append(
            {
                "entity_id": entity_id,
                "entity_type": "PERSON",
                "wikidata_qid": person_qid,
                "name_en": person_name,
                "country_entity_id": country_iso,
                "aliases": person_aliases,
            }
        )

    logger.info(f"Fetched {len(leaders)} world leaders")
    return leaders


def insert_entities(entities: List[Dict]) -> int:
    """Insert entities into data_entities table"""
    if not entities:
        return 0

    inserted = 0

    with get_db_session() as session:
        for entity in entities:
            try:
                # Get aliases (already parsed from Wikidata)
                aliases = entity.get("aliases", {})

                # Build insert statement
                stmt = text(
                    """
                    INSERT INTO data_entities
                    (entity_id, entity_type, iso_code, wikidata_qid, name_en,
                     aliases, capital_entity_id, country_entity_id)
                    VALUES
                    (:entity_id, :entity_type, :iso_code, :wikidata_qid, :name_en,
                     :aliases, :capital_entity_id, :country_entity_id)
                    ON CONFLICT (entity_id) DO UPDATE SET
                        wikidata_qid = EXCLUDED.wikidata_qid,
                        name_en = EXCLUDED.name_en,
                        aliases = EXCLUDED.aliases,
                        updated_at = NOW()
                """
                )

                session.execute(
                    stmt,
                    {
                        "entity_id": entity["entity_id"],
                        "entity_type": entity["entity_type"],
                        "iso_code": entity.get("iso_code"),
                        "wikidata_qid": entity.get("wikidata_qid"),
                        "name_en": entity["name_en"],
                        "aliases": json.dumps(aliases),
                        "capital_entity_id": entity.get("capital_entity_id"),
                        "country_entity_id": entity.get("country_entity_id"),
                    },
                )

                inserted += 1

            except Exception as e:
                logger.warning(
                    f"Failed to insert entity {entity.get('entity_id')}: {e}"
                )

        session.commit()

    logger.info(f"Inserted/updated {inserted} entities")
    return inserted


def import_all():
    """Import all entity types from Wikidata"""
    logger.info("Starting Wikidata entity import...")

    total_imported = 0

    # Import countries and capitals
    logger.info("=== Importing Countries & Capitals ===")
    countries = fetch_countries_with_capitals()
    time.sleep(REQUEST_DELAY)
    total_imported += insert_entities(countries)

    # Import organizations
    logger.info("\n=== Importing Organizations ===")
    organizations = fetch_organizations()
    time.sleep(REQUEST_DELAY)
    total_imported += insert_entities(organizations)

    # Import world leaders
    logger.info("\n=== Importing World Leaders ===")
    leaders = fetch_current_leaders()
    time.sleep(REQUEST_DELAY)
    total_imported += insert_entities(leaders)

    logger.info("\n=== Import Complete ===")
    logger.info(f"Total entities imported: {total_imported}")

    # Show summary
    with get_db_session() as session:
        result = session.execute(
            text(
                """
            SELECT entity_type, COUNT(*) as count
            FROM data_entities
            GROUP BY entity_type
            ORDER BY entity_type
        """
            )
        )

        logger.info("\nEntity counts by type:")
        for row in result:
            logger.info(f"  {row.entity_type}: {row.count}")


if __name__ == "__main__":
    import_all()
