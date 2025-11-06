"""Update/insert taxonomy items with comprehensive multilingual aliases"""

import json
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def upsert_comprehensive_aliases():
    """Update or insert 15 taxonomy items with full multilingual aliases"""

    items = [
        {
            "item_raw": "Golan Heights",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-ISRAEL", "MIDEAST-SYRIA"],
            "aliases": [
                "هضبة الجولان",
                "Golanhöhen",
                "Golan Heights",
                "Altos del Golán",
                "Plateau du Golan",
                "गोलान हाइट्स",
                "Alture del Golan",
                "ゴラン高原",
                "Голанские высоты",
                "戈兰高地",
            ],
        },
        {
            "item_raw": "Golani Brigade",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-ISRAEL"],
            "aliases": [
                "لواء جولاني",
                "Golani-Brigade",
                "Golani Brigade",
                "Brigada Golani",
                "Brigade Golani",
                "गोलानी ब्रिगेड",
                "Brigata Golani",
                "ゴラニ旅団",
                "бригада «Голани»",
                "戈兰尼旅",
            ],
        },
        {
            "item_raw": "Haifa",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-ISRAEL"],
            "aliases": [
                "حيفا",
                "Haifa",
                "Haïfa",
                "हाइफा",
                "ハイファ",
                "Хайфа",
                "海法",
            ],
        },
        {
            "item_raw": "Hayat Tahrir al-Sham",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-SYRIA"],
            "aliases": [
                "هيئة تحرير الشام",
                "Hayat Tahrir al-Scham",
                "HTS",
                "Hayat Tahrir al-Sham",
                "Hayat Tahrir al-Cham",
                "हयात तहरीर अल-शाम",
                "シャーム解放委員会",
                "Хайят Тахрир аш-Шам",
                "ХТШ",
                "沙姆解放组织",
            ],
        },
        {
            "item_raw": "Homs",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-SYRIA"],
            "aliases": [
                "حمص",
                "Homs",
                "होम्स",
                "ホムス",
                "Хомс",
                "霍姆斯",
            ],
        },
        {
            "item_raw": "Syrian Democratic Forces",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-SYRIA"],
            "aliases": [
                "قوات سوريا الديمقراطية",
                "Syrische Demokratische Kräfte",
                "SDF",
                "Syrian Democratic Forces",
                "Fuerzas Democráticas Sirias",
                "FDS",
                "Forces démocratiques syriennes",
                "सीरियन डेमोक्रेटिक फोर्सेस",
                "Forze Democratiche Siriane",
                "シリア民主軍",
                "Сирийские демократические силы",
                "СДС",
                "叙利亚民主力量",
            ],
        },
        {
            "item_raw": "Taiz",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-YEMEN"],
            "aliases": [
                "تعز",
                "Taizz",
                "Taiz",
                "Ta'izz",
                "Taëz",
                "ताइज़",
                "タイズ",
                "Таиз",
                "塔伊兹",
            ],
        },
        {
            "item_raw": "Tartus",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-SYRIA"],
            "aliases": [
                "طرطوس",
                "Tartus",
                "Tartous",
                "टार्टस",
                "タルトゥース",
                "Тартус",
                "塔尔图斯",
            ],
        },
        {
            "item_raw": "Tel Aviv",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-ISRAEL"],
            "aliases": [
                "تل أبيب",
                "Tel Aviv",
                "Tel Aviv-Yafo",
                "तेल अवीव",
                "テルアビブ",
                "Тель-Авив",
                "特拉维夫",
            ],
        },
        {
            "item_raw": "THAAD",
            "item_type": "model",
            "centroid_ids": ["MIDEAST-SAUDI"],
            "aliases": [
                "ثاد",
                "THAAD",
                "Terminal High Altitude Area Defense",
                "थाड",
                "Противоракетный комплекс THAAD",
                "萨德",
            ],
        },
        {
            "item_raw": "Tiger Forces",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-SYRIA"],
            "aliases": [
                "قوات النمر",
                "Tiger-Kräfte",
                "Tiger Forces",
                "Tiger Division",
                "Fuerzas Tigre",
                "Forces du Tigre",
                "टाइगर फोर्सेस",
                "Forze della Tigre",
                "タイガー部隊",
                "«Тигровые силы»",
                "老虎部队",
            ],
        },
        {
            "item_raw": "Unit 8200",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-ISRAEL"],
            "aliases": [
                "الوحدة 8200",
                "Einheit 8200",
                "Unit 8200",
                "Unidad 8200",
                "Unité 8200",
                "यूनिट 8200",
                "Unità 8200",
                "8200部隊",
                "подразделение 8200",
                "8200部队",
            ],
        },
        {
            "item_raw": "Hassi Messaoud",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-MAGHREB"],
            "aliases": [
                "حاسي مسعود",
                "Hassi Messaoud",
                "हस्सी मस्सौद",
                "ハッシ・メサウド",
                "Хасси-Месауд",
                "哈西迈萨乌德",
            ],
        },
        {
            "item_raw": "Abdelmadjid Tebboune",
            "item_type": "person",
            "centroid_ids": ["MIDEAST-MAGHREB"],
            "aliases": [
                "عبد المجيد تبون",
                "Abdelmadjid Tebboune",
                "President Tebboune",
                "अब्देलमजीद तेब्बौने",
                "アブデルマジド・テブン",
                "Абдельмаджид Теббун",
                "阿卜杜勒马吉德·特本",
            ],
        },
        {
            "item_raw": "Sonatrach",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-MAGHREB"],
            "aliases": [
                "سوناطراك",
                "Sonatrach",
                "सोनात्राच",
                "ソナトラック",
                "Сонатрак",
                "索纳塔克",
            ],
        },
    ]

    try:
        conn = psycopg2.connect(
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
            user=config.db_user,
            password=config.db_password,
        )
        conn.autocommit = False

        with conn.cursor() as cur:
            print("Upserting taxonomy items with comprehensive aliases...\n")

            for item in items:
                # Check if item exists
                cur.execute(
                    """
                    SELECT id FROM taxonomy_v3
                    WHERE item_raw = %s
                """,
                    (item["item_raw"],),
                )
                existing = cur.fetchone()

                if existing:
                    # Update existing
                    cur.execute(
                        """
                        UPDATE taxonomy_v3
                        SET item_type = %s,
                            centroid_ids = %s,
                            aliases = %s::jsonb,
                            updated_at = NOW()
                        WHERE item_raw = %s
                        RETURNING id
                    """,
                        (
                            item["item_type"],
                            item["centroid_ids"],
                            json.dumps(item["aliases"]),
                            item["item_raw"],
                        ),
                    )
                    print(
                        f"  [UPDATED] {item['item_raw']:30} -> {len(item['aliases'])} aliases"
                    )
                else:
                    # Insert new
                    cur.execute(
                        """
                        INSERT INTO taxonomy_v3 (item_raw, item_type, centroid_ids, aliases, is_active)
                        VALUES (%s, %s, %s, %s::jsonb, true)
                        RETURNING id
                    """,
                        (
                            item["item_raw"],
                            item["item_type"],
                            item["centroid_ids"],
                            json.dumps(item["aliases"]),
                        ),
                    )
                    print(
                        f"  [INSERTED] {item['item_raw']:30} -> {len(item['aliases'])} aliases"
                    )

            conn.commit()
            print(f"\nSuccessfully processed {len(items)} taxonomy items!")

        conn.close()
        return True

    except Exception as e:
        print(f"Upsert failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = upsert_comprehensive_aliases()
    sys.exit(0 if success else 1)
