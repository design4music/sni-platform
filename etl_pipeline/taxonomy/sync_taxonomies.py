#!/usr/bin/env python3
"""
Taxonomy synchronization script for CLUST-1 MVP.
Loads local taxonomy files and syncs to database.
"""

import json
import logging
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_batch

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection using environment variables."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "narrative_intelligence"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def load_json_file(filepath):
    """Load JSON file, return empty list if file doesn't exist or is empty."""
    try:
        if not Path(filepath).exists():
            logger.warning(f"File {filepath} does not exist, returning empty list")
            return []

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                logger.warning(f"File {filepath} is empty, returning empty list")
                return []
            return json.loads(content)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load {filepath}: {e}, returning empty list")
        return []


def sync_topics(conn, topics_data, source):
    """Sync topics to taxonomy_topics table."""
    if not topics_data:
        logger.info(f"No topics data for source {source}, skipping")
        return

    cur = conn.cursor()
    try:
        # Prepare data for upsert
        topic_rows = []
        for topic in topics_data:
            topic_rows.append(
                (
                    topic.get("topic_id"),
                    topic.get("name"),
                    topic.get(
                        "source", source
                    ),  # Use topic's source or fallback to parameter
                    topic.get("parent_id"),
                    topic.get("path", []),
                )
            )

        # Upsert topics
        upsert_sql = """
            INSERT INTO taxonomy_topics (topic_id, name, source, parent_id, path)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (topic_id) DO UPDATE SET
                name = EXCLUDED.name,
                source = EXCLUDED.source,
                parent_id = EXCLUDED.parent_id,
                path = EXCLUDED.path
        """
        execute_batch(cur, upsert_sql, topic_rows)
        logger.info(f"Synced {len(topic_rows)} topics for source {source}")

    except Exception as e:
        logger.error(f"Failed to sync topics for {source}: {e}")
        raise
    finally:
        cur.close()


def sync_aliases(conn, aliases_data):
    """Sync aliases to taxonomy_aliases table."""
    if not aliases_data:
        logger.info("No aliases data, skipping")
        return

    cur = conn.cursor()
    try:
        # Prepare data for upsert
        alias_rows = []
        for alias_entry in aliases_data:
            alias_rows.append(
                (
                    alias_entry.get("topic_id"),
                    alias_entry.get("alias"),
                    alias_entry.get("lang", "en"),
                )
            )

        # Upsert aliases
        upsert_sql = """
            INSERT INTO taxonomy_aliases (topic_id, alias, lang)
            VALUES (%s, %s, %s)
            ON CONFLICT (topic_id, alias, lang) DO NOTHING
        """
        execute_batch(cur, upsert_sql, alias_rows)
        logger.info(f"Synced {len(alias_rows)} aliases")

    except Exception as e:
        logger.error(f"Failed to sync aliases: {e}")
        raise
    finally:
        cur.close()


def sync_mappings(conn, mappings_data):
    """Sync mappings to taxonomy_mappings table."""
    if not mappings_data:
        logger.info("No mappings data, skipping")
        return

    cur = conn.cursor()
    try:
        # Prepare data for upsert
        mapping_rows = []
        for mapping in mappings_data:
            mapping_rows.append(
                (
                    mapping.get("from_source"),
                    mapping.get("from_id"),
                    mapping.get("to_topic_id"),
                )
            )

        # Upsert mappings
        upsert_sql = """
            INSERT INTO taxonomy_mappings (from_source, from_id, to_topic_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (from_source, from_id) DO UPDATE SET
                to_topic_id = EXCLUDED.to_topic_id
        """
        execute_batch(cur, upsert_sql, mapping_rows)
        logger.info(f"Synced {len(mapping_rows)} mappings")

    except Exception as e:
        logger.error(f"Failed to sync mappings: {e}")
        raise
    finally:
        cur.close()


def parse_iptc_mediatopic(filepath):
    """Parse IPTC Media Topics JSON-LD file."""
    logger.info(f"Parsing IPTC Media Topics from {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'conceptSet' not in data:
            logger.error("No conceptSet found in IPTC file")
            return [], []
        
        concepts = data['conceptSet']
        logger.info(f"Found {len(concepts)} IPTC concepts")
        
        topics = []
        aliases = []
        
        # Build URI to concept mapping for parent resolution
        uri_to_concept = {c['uri']: c for c in concepts}
        
        for concept in concepts:
            # Extract topic ID from URI (last path segment)
            uri = concept['uri']
            topic_id = uri.split('/')[-1]
            
            # Get preferred label in English
            pref_labels = concept.get('prefLabel', {})
            name = pref_labels.get('en-GB') or pref_labels.get('en-US') or topic_id
            
            # Get broader concept (parent)
            broader = concept.get('broader', [])
            parent_id = None
            if broader:
                # broader is a list of URIs
                parent_uri = broader[0] if isinstance(broader, list) else broader
                parent_id = parent_uri.split('/')[-1]
            
            # Compute path from hierarchy
            path = []
            current_uri = uri
            visited = set()
            
            while current_uri and current_uri not in visited:
                visited.add(current_uri)
                current_concept = uri_to_concept.get(current_uri)
                if not current_concept:
                    break
                
                current_name = current_concept.get('prefLabel', {}).get('en-GB', '')
                if current_name and current_uri != uri:  # Don't include self
                    path.insert(0, current_name)
                
                # Move to parent
                current_broader = current_concept.get('broader', [])
                if current_broader:
                    current_uri = current_broader[0] if isinstance(current_broader, list) else current_broader
                else:
                    break
            
            # Create topic entry
            topic_entry = {
                "topic_id": f"iptc:{topic_id}",
                "name": name,
                "source": "IPTC",
                "parent_id": f"iptc:{parent_id}" if parent_id else None,
                "path": path
            }
            topics.append(topic_entry)
            
            # Create aliases for all languages
            for lang, label in pref_labels.items():
                if label and label.strip():
                    aliases.append({
                        "topic_id": f"iptc:{topic_id}",
                        "alias": label,
                        "lang": lang
                    })
        
        logger.info(f"Parsed {len(topics)} topics and {len(aliases)} aliases from IPTC")
        return topics, aliases
        
    except Exception as e:
        logger.error(f"Failed to parse IPTC file: {e}")
        return [], []


def main():
    """Main synchronization function."""
    logger.info("Starting taxonomy synchronization")

    # Define data file paths
    data_dir = Path(__file__).parent.parent.parent / "data"
    iptc_mediatopic_file = data_dir / "iptc_mediatopic.json"
    iptc_topics_file = data_dir / "iptc_topics.json" 
    iptc_aliases_file = data_dir / "iptc_aliases.json"
    gdelt_themes_file = data_dir / "gdelt_themes.json"

    try:
        # Connect to database
        conn = get_db_connection()

        try:
            # Parse IPTC Media Topics JSON-LD
            if iptc_mediatopic_file.exists():
                logger.info("Processing IPTC Media Topics JSON-LD file")
                iptc_topics, iptc_aliases = parse_iptc_mediatopic(iptc_mediatopic_file)
                
                if iptc_topics:
                    sync_topics(conn, iptc_topics, "IPTC")
                    sync_aliases(conn, iptc_aliases)
                    logger.info(f"Successfully synced {len(iptc_topics)} IPTC topics")
            else:
                # Fallback to old format files
                logger.info("Loading legacy IPTC files")
                iptc_topics = load_json_file(iptc_topics_file)
                iptc_aliases = load_json_file(iptc_aliases_file)
                
                sync_topics(conn, iptc_topics, "IPTC")
                sync_aliases(conn, iptc_aliases)

            # Load GDELT data
            gdelt_data = load_json_file(gdelt_themes_file)
            gdelt_topics = (
                gdelt_data.get("topics", []) if isinstance(gdelt_data, dict) else gdelt_data
            )
            gdelt_aliases = (
                gdelt_data.get("aliases", []) if isinstance(gdelt_data, dict) else []
            )
            
            if gdelt_topics:
                sync_topics(conn, gdelt_topics, "GDELT")
                sync_aliases(conn, gdelt_aliases)

            # Commit all changes
            conn.commit()
            logger.info("Taxonomy synchronization completed successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"Taxonomy synchronization failed: {e}")
            raise
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to sync taxonomies: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
