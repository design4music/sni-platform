#!/usr/bin/env python3
"""
Update existing Event Families with standardized taxonomies
Maps current values to new standardized event_type and geography values
"""

import sys
from pathlib import Path
from typing import Dict, Tuple

from loguru import logger
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.database import get_db_session


def create_event_type_mapping() -> Dict[str, str]:
    """Create mapping from current event_type values to standardized values"""
    return {
        # Military/Security Operations
        "Military Operation": "Strategy/Tactics",
        "Military Operations": "Strategy/Tactics",
        "Military/Security Incident": "Strategy/Tactics",
        "Military Incident": "Strategy/Tactics",
        "Military Strike/International Incident": "Strategy/Tactics",
        "Military Operations/Regional Conflict": "Strategy/Tactics",
        "Military Incident/Border Security": "Strategy/Tactics",
        "Military Conflict": "Strategy/Tactics",
        "Military Policy Change": "Strategy/Tactics",
        "Military Operation/Political Policy": "Strategy/Tactics",
        "Military Display/Diplomatic Summit": "Strategy/Tactics",
        "Military cooperation/Regional security": "Alliances/Geopolitics",
        # Political Violence
        "Political Violence/Assassination": "Domestic Politics",
        # Diplomatic Relations
        "Diplomatic Relations": "Diplomacy/Negotiations",
        "Diplomatic Scandal": "Diplomacy/Negotiations",
        "Diplomacy/Nuclear Agreement": "Diplomacy/Negotiations",
        "Diplomacy": "Diplomacy/Negotiations",
        "Diplomatic Summit": "Diplomacy/Negotiations",
        "Diplomacy/Armed Conflict": "Diplomacy/Negotiations",
        "Diplomatic crisis/Nuclear negotiations": "Diplomacy/Negotiations",
        # Domestic Politics
        "Domestic Politics": "Domestic Politics",
        "Domestic Policy": "Domestic Politics",
        "Domestic Politics/Protests": "Domestic Politics",
        "Domestic Security Policy": "Domestic Politics",
        # International Relations
        "International Conflict/Sanctions": "Sanctions/Economy",
        "International Security Agreement": "Alliances/Geopolitics",
        "Military Conflict/International Diplomacy": "Alliances/Geopolitics",
        "Military conflict/International security": "Alliances/Geopolitics",
        # Economic/Trade
        "Geopolitical Tensions/Trade Policy": "Sanctions/Economy",
        "Economic Diplomacy": "Sanctions/Economy",
        "Economic Policy/Trade Sanctions": "Sanctions/Economy",
        "Trade Agreement": "Sanctions/Economy",
        # Other Categories
        "Political Scandal/Dismissal": "Domestic Politics",
        "Financial Crime/Scandal": "Legal/ICC",
        "Immigration Enforcement": "Domestic Politics",
        "Immigration policy/Foreign relations": "Domestic Politics",
        "Armed conflict/Humanitarian crisis": "Humanitarian",
    }


def create_geography_mapping() -> Dict[str, str]:
    """Create mapping from current geography values to standardized theater codes"""
    return {
        # North America
        "United States": "NAMERICA",
        "United States, Utah": "NAMERICA",
        "United States/Utah": "NAMERICA",
        "United States/International": "NAMERICA",
        "Chicago, USA": "NAMERICA",
        "Carib Sea/International Waters": "NAMERICA",
        # Europe
        "France": "EUROPE",
        "Ukraine": "EUROPE",
        "Poland/Eastern Europe": "EUROPE",
        "Poland-Ukraine border region": "EUROPE",
        "Ukraine/Eastern Europe": "EUROPE",
        "Ukraine, Europe": "EUROPE",
        "Ukraine, Russia, European Union": "EUROPE",
        "Poland, Belarus, Russia": "EUROPE",
        "European Union": "EUROPE",
        "Europe/Latin America": "EUROPE",  # Primarily European context
        "United Kingdom": "EUROPE",
        "Russia": "EUROPE",  # For European security context
        # Middle East
        "Middle East": "MEAST",
        "Middle East/International": "MEAST",
        "Qatar/Middle East": "MEAST",
        "Doha, Qatar": "MEAST",
        "Gaza Strip": "MEAST",
        "Gaza/Middle East": "MEAST",
        "Gaza City, West Bank": "MEAST",
        "Israel, Gaza, Middle East": "MEAST",
        # Asia-Pacific
        "China, Beijing": "ASIA",
        "Beijing, China": "ASIA",
        "Asia-Pacific": "ASIA",
        "Asia-Pacific, North America": "ASIA",  # Primary theater is Asia-Pacific
        # Global/Multi-theater
        "Global": "GLOBAL",
        "Virtual Summit": "VIRTUAL",
        # Mixed cases - assign to primary theater
        "United Kingdom, United States": "GLOBAL",  # Trans-Atlantic
        "United States, Israel, Qatar": "GLOBAL",  # Multi-theater event
    }


def update_event_families_taxonomies() -> Tuple[int, int]:
    """
    Update existing Event Families with standardized taxonomies

    Returns:
        Tuple of (event_type_updates, geography_updates)
    """
    logger.info("=== UPDATING EVENT FAMILIES TAXONOMIES ===")

    event_type_mapping = create_event_type_mapping()
    geography_mapping = create_geography_mapping()

    event_type_updates = 0
    geography_updates = 0

    with get_db_session() as session:
        # Get all Event Families
        families = session.execute(
            text(
                """
            SELECT id, title, event_type, geography 
            FROM event_families 
            ORDER BY created_at DESC
        """
            )
        ).fetchall()

        logger.info(f"Found {len(families)} Event Families to process")

        for family in families:
            updates = []
            params = {"family_id": str(family.id)}

            # Update event_type if mapping exists
            if family.event_type in event_type_mapping:
                new_event_type = event_type_mapping[family.event_type]
                if new_event_type != family.event_type:
                    updates.append("event_type = :new_event_type")
                    params["new_event_type"] = new_event_type
                    event_type_updates += 1
                    logger.info(
                        f"Event Type: '{family.event_type}' → '{new_event_type}'"
                    )
            else:
                logger.warning(
                    f"No mapping for event_type: '{family.event_type}' (EF: {family.title})"
                )

            # Update geography if mapping exists
            if family.geography in geography_mapping:
                new_geography = geography_mapping[family.geography]
                if new_geography != family.geography:
                    updates.append("geography = :new_geography")
                    params["new_geography"] = new_geography
                    geography_updates += 1
                    logger.info(f"Geography: '{family.geography}' → '{new_geography}'")
            else:
                logger.warning(
                    f"No mapping for geography: '{family.geography}' (EF: {family.title})"
                )

            # Apply updates if any
            if updates:
                update_query = f"""
                UPDATE event_families 
                SET {', '.join(updates)}, updated_at = NOW()
                WHERE id = :family_id
                """
                session.execute(text(update_query), params)

        session.commit()

    logger.info("Taxonomy updates completed:")
    logger.info(f"  Event type updates: {event_type_updates}")
    logger.info(f"  Geography updates: {geography_updates}")

    return event_type_updates, geography_updates


def verify_taxonomy_compliance() -> None:
    """Verify all Event Families now use standardized taxonomies"""
    logger.info("=== VERIFYING TAXONOMY COMPLIANCE ===")

    standardized_event_types = {
        "Strategy/Tactics",
        "Humanitarian",
        "Alliances/Geopolitics",
        "Diplomacy/Negotiations",
        "Sanctions/Economy",
        "Domestic Politics",
        "Procurement/Force-gen",
        "Tech/Cyber/OSINT",
        "Legal/ICC",
        "Information/Media/Platforms",
        "Energy/Infrastructure",
    }

    standardized_geographies = {
        "NAMERICA",
        "EUROPE",
        "MEAST",
        "ASIA",
        "AFRICA",
        "LATAM",
        "GLOBAL",
        "VIRTUAL",
    }

    with get_db_session() as session:
        # Check event_type compliance
        non_standard_types = session.execute(
            text(
                """
            SELECT DISTINCT event_type, COUNT(*) as count
            FROM event_families 
            WHERE event_type NOT IN :valid_types
            GROUP BY event_type
            ORDER BY count DESC
        """
            ),
            {"valid_types": tuple(standardized_event_types)},
        ).fetchall()

        if non_standard_types:
            logger.warning("Non-standard event_type values found:")
            for row in non_standard_types:
                logger.warning(f"  {row.count}x '{row.event_type}'")
        else:
            logger.info("✓ All event_type values are compliant")

        # Check geography compliance
        non_standard_geos = session.execute(
            text(
                """
            SELECT DISTINCT geography, COUNT(*) as count
            FROM event_families 
            WHERE geography NOT IN :valid_geos
            GROUP BY geography  
            ORDER BY count DESC
        """
            ),
            {"valid_geos": tuple(standardized_geographies)},
        ).fetchall()

        if non_standard_geos:
            logger.warning("Non-standard geography values found:")
            for row in non_standard_geos:
                logger.warning(f"  {row.count}x '{row.geography}'")
        else:
            logger.info("✓ All geography values are compliant")


def main():
    """Main entry point"""
    try:
        # Update taxonomies
        event_updates, geo_updates = update_event_families_taxonomies()

        # Verify compliance
        verify_taxonomy_compliance()

        logger.info("Taxonomy standardization complete!")
        logger.info(f"Total updates: {event_updates + geo_updates}")

    except Exception as e:
        logger.error(f"Taxonomy update failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
