"""
Populate iso_codes for geographic centroids in centroids_v3.

Maps centroid IDs to ISO 3166-1 alpha-2 country codes for map visualization.
Systemic centroids (SYS-*) are skipped (no geographic footprint).
"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config

# ISO code mappings for geographic centroids
ISO_MAPPINGS = {
    # AMERICAS - Countries
    "AMERICAS-USA": ["US"],
    "AMERICAS-CANADA": ["CA"],
    "AMERICAS-MEXICO": ["MX"],
    "AMERICAS-BRAZIL": ["BR"],
    "AMERICAS-ARGENTINA": ["AR"],
    "AMERICAS-CHILE": ["CL"],
    "AMERICAS-COLOMBIA": ["CO"],
    "AMERICAS-VENEZUELA": ["VE"],
    "AMERICAS-PERU": ["PE"],
    "AMERICAS-CUBA": ["CU"],

    # AMERICAS - Regions
    "AMERICAS-CARIBBEAN": [
        "AG", "BS", "BB", "BZ", "DM", "DO", "GD", "GT", "HT", "HN", "JM",
        "KN", "LC", "NI", "PA", "SV", "TT", "VC"
    ],
    "AMERICAS-CENTRAL": ["BZ", "CR", "SV", "GT", "HN", "NI", "PA"],
    "AMERICAS-SOUTH": [
        "AR", "BO", "BR", "CL", "CO", "EC", "GY", "PY", "PE", "SR", "UY", "VE"
    ],
    "AMERICAS-ANDEAN": ["BO", "CO", "EC", "PE", "VE"],
    "AMERICAS-SOUTHERNCONE": ["AR", "CL", "PY", "UY"],

    # EUROPE - Major Countries
    "EUROPE-GERMANY": ["DE"],
    "EUROPE-FRANCE": ["FR"],
    "EUROPE-UK": ["GB"],
    "EUROPE-ITALY": ["IT"],
    "EUROPE-SPAIN": ["ES"],
    "EUROPE-POLAND": ["PL"],
    "EUROPE-UKRAINE": ["UA"],
    "EUROPE-RUSSIA": ["RU"],
    "EUROPE-TURKEY": ["TR"],
    "EUROPE-GREECE": ["GR"],
    "EUROPE-NETHERLANDS": ["NL"],
    "EUROPE-BELGIUM": ["BE"],
    "EUROPE-SWEDEN": ["SE"],
    "EUROPE-NORWAY": ["NO"],
    "EUROPE-DENMARK": ["DK"],
    "EUROPE-FINLAND": ["FI"],
    "EUROPE-AUSTRIA": ["AT"],
    "EUROPE-SWITZERLAND": ["CH"],
    "EUROPE-PORTUGAL": ["PT"],
    "EUROPE-CZECHIA": ["CZ"],
    "EUROPE-ROMANIA": ["RO"],
    "EUROPE-HUNGARY": ["HU"],
    "EUROPE-SERBIA": ["RS"],
    "EUROPE-BELARUS": ["BY"],

    # EUROPE - Regions
    "EUROPE-BALTICS": ["EE", "LV", "LT"],
    "EUROPE-BALTIC": ["EE", "LV", "LT"],  # Alternate naming
    "EUROPE-BALKANS": ["AL", "BA", "BG", "HR", "XK", "ME", "MK", "RO", "RS", "SI"],
    "EUROPE-BALKANS-EAST": ["BG", "RO"],
    "EUROPE-BENELUX": ["BE", "NL", "LU"],
    "EUROPE-NORDICS": ["DK", "FI", "IS", "NO", "SE"],
    "EUROPE-NORDIC": ["DK", "FI", "IS", "NO", "SE"],  # Alternate naming
    "EUROPE-VISEGRAD": ["CZ", "HU", "PL", "SK"],
    "EUROPE-CAUCASUS": ["AM", "AZ", "GE"],
    "EUROPE-ALPINE": ["AT", "CH", "LI"],
    "EUROPE-SOUTH": ["GR", "IT", "PT", "ES", "CY", "MT"],

    # ASIA - Major Countries
    "ASIA-CHINA": ["CN"],
    "ASIA-INDIA": ["IN"],
    "ASIA-JAPAN": ["JP"],
    "ASIA-SOUTH_KOREA": ["KR"],
    "ASIA-SOUTHKOREA": ["KR"],  # Alternate naming
    "ASIA-NORTH_KOREA": ["KP"],
    "ASIA-NORKOREA": ["KP"],  # Alternate naming
    "ASIA-PAKISTAN": ["PK"],
    "ASIA-BANGLADESH": ["BD"],
    "ASIA-INDONESIA": ["ID"],
    "ASIA-VIETNAM": ["VN"],
    "ASIA-THAILAND": ["TH"],
    "ASIA-PHILIPPINES": ["PH"],
    "ASIA-MALAYSIA": ["MY"],
    "ASIA-SINGAPORE": ["SG"],
    "ASIA-MYANMAR": ["MM"],
    "ASIA-TAIWAN": ["TW"],
    "ASIA-MONGOLIA": ["MN"],
    "ASIA-AFGHANISTAN": ["AF"],
    "ASIA-KAZAKHSTAN": ["KZ"],
    "ASIA-UZBEKISTAN": ["UZ"],
    "ASIA-SRI_LANKA": ["LK"],
    "ASIA-HONGKONG": ["HK"],

    # ASIA - Regions
    "ASIA-CENTRAL": ["KZ", "KG", "TJ", "TM", "UZ"],
    "ASIA-SOUTHEAST": ["BN", "KH", "ID", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"],
    "ASIA-SOUTH": ["AF", "BD", "BT", "IN", "MV", "NP", "PK", "LK"],
    "ASIA-SOUTHASIA": ["AF", "BD", "BT", "IN", "MV", "NP", "PK", "LK"],  # Alternate naming
    "ASIA-CAUCASUS": ["AM", "AZ", "GE"],
    "ASIA-HIMALAYA": ["BT", "NP"],

    # MIDDLE EAST
    "MIDEAST-SAUDI_ARABIA": ["SA"],
    "MIDEAST-SAUDI": ["SA"],  # Alternate naming
    "MIDEAST-IRAN": ["IR"],
    "MIDEAST-IRAQ": ["IQ"],
    "MIDEAST-SYRIA": ["SY"],
    "MIDEAST-YEMEN": ["YE"],
    "MIDEAST-UAE": ["AE"],
    "MIDEAST-ISRAEL": ["IL"],
    "MIDEAST-PALESTINE": ["PS"],
    "MIDEAST-JORDAN": ["JO"],
    "MIDEAST-LEBANON": ["LB"],
    "MIDEAST-KUWAIT": ["KW"],
    "MIDEAST-QATAR": ["QA"],
    "MIDEAST-BAHRAIN": ["BH"],
    "MIDEAST-OMAN": ["OM"],
    "MIDEAST-TURKEY": ["TR"],
    "MIDEAST-EGYPT": ["EG"],
    "MIDEAST-SUDAN": ["SD"],

    # MIDEAST - Regions
    "MIDEAST-GULF": ["BH", "IQ", "KW", "OM", "QA", "SA", "AE"],
    "MIDEAST-LEVANT": ["IL", "JO", "LB", "PS", "SY"],
    "MIDEAST-MAGHREB": ["DZ", "LY", "MA", "MR", "TN"],

    # AFRICA - North Africa / Maghreb
    "AFRICA-EGYPT": ["EG"],
    "AFRICA-ALGERIA": ["DZ"],
    "AFRICA-MOROCCO": ["MA"],
    "AFRICA-TUNISIA": ["TN"],
    "AFRICA-LIBYA": ["LY"],
    "AFRICA-MAURITANIA": ["MR"],
    "AFRICA-SUDAN": ["SD"],
    "AFRICA-SOUTH_SUDAN": ["SS"],

    # AFRICA - Sub-Saharan
    "AFRICA-NIGERIA": ["NG"],
    "AFRICA-ETHIOPIA": ["ET"],
    "AFRICA-KENYA": ["KE"],
    "AFRICA-SOUTH_AFRICA": ["ZA"],
    "AFRICA-SOUTHAFRICA": ["ZA"],  # Alternate naming
    "AFRICA-DRC": ["CD"],
    "AFRICA-GHANA": ["GH"],
    "AFRICA-TANZANIA": ["TZ"],
    "AFRICA-UGANDA": ["UG"],
    "AFRICA-SOMALIA": ["SO"],
    "AFRICA-ZIMBABWE": ["ZW"],
    "AFRICA-SENEGAL": ["SN"],
    "AFRICA-MALI": ["ML"],
    "AFRICA-NIGER": ["NE"],
    "AFRICA-CHAD": ["TD"],
    "AFRICA-CAMEROON": ["CM"],
    "AFRICA-RWANDA": ["RW"],
    "AFRICA-MOZAMBIQUE": ["MZ"],

    # AFRICA - Regions
    "AFRICA-MAGHREB": ["DZ", "LY", "MA", "MR", "TN"],
    "AFRICA-SAHEL": ["BF", "TD", "ML", "MR", "NE", "NG", "SN"],
    "AFRICA-WEST": [
        "BJ", "BF", "CV", "CI", "GM", "GH", "GN", "GW", "LR", "ML", "MR",
        "NE", "NG", "SN", "SL", "TG"
    ],
    "AFRICA-EAST": [
        "BI", "KM", "DJ", "ER", "ET", "KE", "MG", "MW", "MU", "MZ", "RW",
        "SC", "SO", "SS", "TZ", "UG", "ZM", "ZW"
    ],
    "AFRICA-CENTRAL": ["AO", "CM", "CF", "TD", "CG", "CD", "GQ", "GA", "ST"],
    "AFRICA-SOUTHERN": ["BW", "LS", "NA", "ZA", "SZ"],
    "AFRICA-HORN": ["DJ", "ER", "ET", "SO"],

    # OCEANIA
    "OCEANIA-AUSTRALIA": ["AU"],
    "OCEANIA-NEW_ZEALAND": ["NZ"],
    "OCEANIA-NEWZEALAND": ["NZ"],  # Alternate naming
    "OCEANIA-PAPUA_NEW_GUINEA": ["PG"],
    "OCEANIA-PAPUANEWGUINEA": ["PG"],  # Alternate naming
    "OCEANIA-FIJI": ["FJ"],
    "OCEANIA-PACIFIC": [
        "FJ", "KI", "MH", "FM", "NR", "PW", "PG", "WS", "SB", "TO", "TV", "VU"
    ],
    "OCEANIA-MELANESIA": ["FJ", "NC", "PG", "SB", "VU"],
    "OCEANIA-MICRONESIA": ["FM", "GU", "KI", "MH", "MP", "NR", "PW"],
    "OCEANIA-POLYNESIA": ["AS", "CK", "PF", "NU", "PN", "WS", "TK", "TO", "TV", "WF"],

    # NON-STATE ACTORS (no ISO codes - these won't have map highlights)
    # These are intentionally left out - no geographic mapping
    # "NON-STATE-ISIS": None,
    # "NON-STATE-AL-QAEDA": None,
    # "NON-STATE-NATO": None,
    # "NON-STATE-EU": None,
    # etc.
}


def populate_iso_codes():
    """Populate iso_codes for all geographic centroids"""

    conn = psycopg2.connect(
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
        user=config.db_user,
        password=config.db_password,
    )

    try:
        # First, run the migration to add the column
        print("Adding iso_codes column...")
        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE centroids_v3
                ADD COLUMN IF NOT EXISTS iso_codes TEXT[]
            """)
        conn.commit()
        print("Column added successfully\n")

        # Get all centroids
        with conn.cursor() as cur:
            cur.execute("SELECT id, label, class FROM centroids_v3 ORDER BY id")
            centroids = cur.fetchall()

        print(f"Found {len(centroids)} centroids\n")
        print("=" * 70)
        print("POPULATING ISO CODES")
        print("=" * 70)

        updated_count = 0
        skipped_count = 0
        missing_count = 0

        for centroid_id, label, cls in centroids:
            if cls == "systemic":
                print(f"SKIP: {centroid_id:30s} (systemic - no geography)")
                skipped_count += 1
                continue

            if centroid_id in ISO_MAPPINGS:
                iso_codes = ISO_MAPPINGS[centroid_id]
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE centroids_v3 SET iso_codes = %s WHERE id = %s",
                        (iso_codes, centroid_id),
                    )
                conn.commit()
                codes_str = ", ".join(iso_codes)
                print(f"OK:   {centroid_id:30s} -> [{codes_str}]")
                updated_count += 1
            else:
                print(f"MISS: {centroid_id:30s} (no mapping found)")
                missing_count += 1

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total centroids:      {len(centroids)}")
        print(f"Updated with codes:   {updated_count}")
        print(f"Skipped (systemic):   {skipped_count}")
        print(f"Missing mappings:     {missing_count}")

        if missing_count > 0:
            print("\nNOTE: Missing mappings need manual addition to ISO_MAPPINGS dict")

    finally:
        conn.close()


if __name__ == "__main__":
    populate_iso_codes()
