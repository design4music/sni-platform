"""Debug Italian title matches"""

import re
import sys
import unicodedata
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def normalize_text(text: str) -> str:
    """Normalize text using v2 taxonomy_extractor logic"""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace(".", "")
    text = re.sub(r"\s+", " ", text.lower()).strip()
    return text


# Problem titles
titles = {
    "cc5f9a88-f73f-4540-803f-88c32c6af3b8": "Femminicidio nel Veronese: uccide la ex compagna. «Numero smisurato di coltellate». Arrestato l'uomo, si era tolto il braccialetto elettronico",
    "21926b27-6576-4bde-aaf3-e5a85631db6b": "Pd, Merola: «Scelgo i riformisti, Bonaccini non vuole il dibattito»",
    "3cc30f95-da0f-4ecb-959a-1372fa6a3ac5": "Verona, uccide la compagna a coltellate: aveva il braccialetto ma era riuscito a toglierselo",
    "7f506e26-05be-4872-ba2a-ba84aa9c37d3": "Pausa nella Bassa Bergamasca per il Venice Simplon Orient Express",
    "52c315c7-a77c-47b8-b6e7-91f023cd3260": "Oncologia, il Premio per giovani ricercatori",
}

conn = psycopg2.connect(
    host=config.db_host,
    port=config.db_port,
    database=config.db_name,
    user=config.db_user,
    password=config.db_password,
)

with conn.cursor() as cur:
    # Get all Israeli items with their aliases
    cur.execute(
        """
        SELECT item_raw, item_type, centroid_ids, aliases
        FROM taxonomy_v3
        WHERE 'MIDEAST-ISRAEL' = ANY(centroid_ids)
        ORDER BY item_raw
    """
    )
    israeli_items = cur.fetchall()

print("Checking Israeli taxonomy items against Italian titles...")
print("=" * 80)

for title_id, title_text in titles.items():
    print(f"\nTitle: {title_text}")
    normalized_title = normalize_text(title_text)
    print(f"Normalized: {normalized_title}")

    matches = []
    for item_raw, item_type, centroid_ids, aliases in israeli_items:
        # Check item_raw
        normalized_item = normalize_text(item_raw)
        if normalized_item and normalized_item in normalized_title:
            matches.append((item_raw, item_type, "item_raw", normalized_item))

        # Check aliases
        if aliases:
            for lang, alias_list in aliases.items():
                for alias in alias_list:
                    normalized_alias = normalize_text(alias)
                    if normalized_alias and normalized_alias in normalized_title:
                        matches.append(
                            (item_raw, item_type, f"alias ({lang})", normalized_alias)
                        )

    if matches:
        print("MATCHES:")
        for item_raw, item_type, source, matched_text in matches:
            print(f"  - {item_raw} ({item_type}) via {source}: '{matched_text}'")
    else:
        print("  No matches found!")

conn.close()
