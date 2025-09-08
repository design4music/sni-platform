#!/usr/bin/env python3
"""
Download and parse IPTC Media Topics taxonomy from their CV server.
This will expand our taxonomy from 20 to 1,200+ topics.
"""

import json
import logging
import sys
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_requests_session():
    """Setup requests session with retry strategy."""
    session = requests.Session()

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Set headers to mimic a browser
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    )

    return session


def download_iptc_taxonomy(format_type="rdf"):
    """Download IPTC Media Topics taxonomy."""
    session = setup_requests_session()

    # Try different format URLs
    urls_to_try = [
        f"http://cv.iptc.org/newscodes/mediatopic/?format={format_type}",
        "http://cv.iptc.org/newscodes/mediatopic/?format=json-ld",
        "http://cv.iptc.org/newscodes/mediatopic/?format=rdf",
        f"http://cv.iptc.org/newscodes/mediatopic.{format_type}",
    ]

    for url in urls_to_try:
        try:
            logger.info(f"Trying to download from: {url}")
            response = session.get(url, timeout=30)

            if response.status_code == 200:
                logger.info(f"Successfully downloaded from {url}")
                logger.info(f"Content-Type: {response.headers.get('content-type')}")
                logger.info(f"Response size: {len(response.content)} bytes")

                # Try to parse as JSON
                try:
                    data = response.json()
                    return data, url
                except json.JSONDecodeError:
                    logger.warning("Response not valid JSON, trying as text")
                    return response.text, url

            else:
                logger.warning(f"Failed to download from {url}: {response.status_code}")

        except Exception as e:
            logger.warning(f"Error downloading from {url}: {e}")
            continue

    return None, None


def parse_iptc_json_ld(data):
    """Parse JSON-LD format IPTC data."""
    topics = []
    aliases = []

    try:
        # Handle different JSON-LD structures
        if isinstance(data, dict):
            if "@graph" in data:
                concepts = data["@graph"]
            elif "@context" in data:
                concepts = [data]  # Single concept
            else:
                concepts = [data]
        elif isinstance(data, list):
            concepts = data
        else:
            logger.error("Unexpected data structure")
            return topics, aliases

        for concept in concepts:
            if not isinstance(concept, dict):
                continue

            # Extract topic ID
            topic_id = concept.get("@id") or concept.get("id")
            if not topic_id:
                continue

            # Clean topic ID
            if topic_id.startswith("http://cv.iptc.org/newscodes/mediatopic/"):
                code = topic_id.replace("http://cv.iptc.org/newscodes/mediatopic/", "")
            else:
                code = topic_id

            # Extract labels
            pref_label = concept.get("skos:prefLabel") or concept.get("prefLabel")
            alt_labels = concept.get("skos:altLabel") or concept.get("altLabel") or []

            # Handle different label formats
            if isinstance(pref_label, dict):
                name = (
                    pref_label.get("@value") or pref_label.get("en") or str(pref_label)
                )
            elif isinstance(pref_label, list) and pref_label:
                name = pref_label[0]
                if isinstance(name, dict):
                    name = name.get("@value") or name.get("en") or str(name)
            else:
                name = str(pref_label) if pref_label else code

            # Extract broader concept (parent)
            broader = concept.get("skos:broader") or concept.get("broader")
            parent_id = None
            if broader:
                if isinstance(broader, dict):
                    parent_id = broader.get("@id")
                elif isinstance(broader, list) and broader:
                    parent_id = (
                        broader[0]
                        if isinstance(broader[0], str)
                        else broader[0].get("@id")
                    )
                elif isinstance(broader, str):
                    parent_id = broader

                # Clean parent ID
                if parent_id and parent_id.startswith(
                    "http://cv.iptc.org/newscodes/mediatopic/"
                ):
                    parent_id = parent_id.replace(
                        "http://cv.iptc.org/newscodes/mediatopic/", ""
                    )

            # Create topic entry
            topic_entry = {
                "topic_id": f"iptc:{code}",
                "name": name,
                "source": "IPTC",
                "parent_id": f"iptc:{parent_id}" if parent_id else None,
                "path": [],  # Will be computed later
            }
            topics.append(topic_entry)

            # Create main alias
            aliases.append({"topic_id": f"iptc:{code}", "alias": name, "lang": "en"})

            # Add alternative labels as aliases
            if alt_labels:
                if not isinstance(alt_labels, list):
                    alt_labels = [alt_labels]

                for alt_label in alt_labels:
                    if isinstance(alt_label, dict):
                        alias_text = alt_label.get("@value") or alt_label.get("en")
                    else:
                        alias_text = str(alt_label)

                    if alias_text and alias_text != name:
                        aliases.append(
                            {
                                "topic_id": f"iptc:{code}",
                                "alias": alias_text,
                                "lang": "en",
                            }
                        )

        logger.info(f"Parsed {len(topics)} topics and {len(aliases)} aliases")
        return topics, aliases

    except Exception as e:
        logger.error(f"Error parsing JSON-LD data: {e}")
        return topics, aliases


def compute_paths(topics):
    """Compute hierarchical paths for topics."""
    topic_map = {t["topic_id"]: t for t in topics}

    def get_path(topic_id, visited=None):
        if visited is None:
            visited = set()

        if topic_id in visited:
            return []  # Circular reference

        topic = topic_map.get(topic_id)
        if not topic:
            return []

        visited.add(topic_id)

        if topic["parent_id"] and topic["parent_id"] in topic_map:
            parent_path = get_path(topic["parent_id"], visited)
            return parent_path + [topic["name"]]
        else:
            return [topic["name"]]

    for topic in topics:
        topic["path"] = get_path(topic["topic_id"])


def save_taxonomy_files(topics, aliases, output_dir):
    """Save taxonomy data to JSON files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # Save topics
    topics_file = output_dir / "iptc_topics.json"
    with open(topics_file, "w", encoding="utf-8") as f:
        json.dump(topics, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(topics)} topics to {topics_file}")

    # Save aliases
    aliases_file = output_dir / "iptc_aliases.json"
    with open(aliases_file, "w", encoding="utf-8") as f:
        json.dump(aliases, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(aliases)} aliases to {aliases_file}")

    return topics_file, aliases_file


def main():
    """Main function to download and process IPTC taxonomy."""
    logger.info("Starting IPTC Media Topics download")

    # Download taxonomy
    data, source_url = download_iptc_taxonomy()

    if not data:
        logger.error("Failed to download IPTC taxonomy")
        sys.exit(1)

    logger.info(f"Downloaded data from: {source_url}")

    # Parse the data
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.info("Saving raw response for debugging")
            with open("iptc_raw_response.txt", "w", encoding="utf-8") as f:
                f.write(data[:5000])  # First 5000 chars
            sys.exit(1)

    topics, aliases = parse_iptc_json_ld(data)

    if not topics:
        logger.error("No topics parsed from data")
        sys.exit(1)

    # Compute hierarchical paths
    compute_paths(topics)

    # Save to files
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"

    topics_file, aliases_file = save_taxonomy_files(topics, aliases, data_dir)

    # Print statistics
    logger.info(f"SUCCESS: Downloaded {len(topics)} topics and {len(aliases)} aliases")

    # Show sports-related topics
    sports_topics = [t for t in topics if "sport" in t["name"].lower()]
    logger.info(f"Found {len(sports_topics)} sports-related topics:")
    for topic in sports_topics[:10]:  # Show first 10
        logger.info(f"  - {topic['topic_id']}: {topic['name']}")

    print("\nFiles created:")
    print(f"  Topics: {topics_file}")
    print(f"  Aliases: {aliases_file}")
    print("\nNext step: Run sync_taxonomies.py to load into database")


if __name__ == "__main__":
    main()
