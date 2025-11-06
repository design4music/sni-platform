"""Update/insert final batch of taxonomy items with comprehensive multilingual aliases"""

import json
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def upsert_batch3_aliases():
    """Update or insert 21 more taxonomy items with full multilingual aliases"""

    items = [
        {
            "item_raw": "Ismail Haniyeh",
            "item_type": "person",
            "centroid_ids": ["MIDEAST-PALESTINE"],
            "aliases": [
                "إسماعيل هنية",
                "Ismail Haniyeh",
                "Ismaïl Haniyeh",
                "इस्माइल हनिया",
                "イスマーイール・ハニーヤ",
                "Исмаил Хания",
                "伊斯梅尔·哈尼亚",
            ],
        },
        {
            "item_raw": "Hezbollah",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-LEBANON", "MIDEAST-ISRAEL"],
            "aliases": [
                "حزب الله",
                "Hisbollah",
                "Hezbollah",
                "Hizbullah",
                "Party of God",
                "Hezbolá",
                "हेज़बोल्लाह",
                "ヒズボラ",
                "Хезболла",
                "真主党",
            ],
        },
        {
            "item_raw": "Masoud Pezeshkian",
            "item_type": "person",
            "centroid_ids": ["MIDEAST-IRAN"],
            "aliases": [
                "مسعود بزشكيان",
                "Massud Peseschkian",
                "Masoud Pezeshkian",
                "Masud Pezeshkian",
                "Massoud Pezeshkian",
                "मसूद पेज़ेशकियान",
                "マスード・ペゼシュキヤン",
                "Масуд Пезешкиан",
                "马苏德·佩泽什基安",
            ],
        },
        {
            "item_raw": "Port Said",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-EGYPT"],
            "aliases": [
                "بورسعيد",
                "Port Said",
                "Port-Saïd",
                "पोर्ट सईद",
                "ポートサイド",
                "Порт-Саид",
                "塞得港",
            ],
        },
        {
            "item_raw": "Istanbul",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-TURKEY"],
            "aliases": [
                "إسطنبول",
                "Istanbul",
                "Constantinople",
                "Estambul",
                "इस्तांबुल",
                "イスタンブール",
                "Стамбул",
                "伊斯坦布尔",
            ],
        },
        {
            "item_raw": "Izmir",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-TURKEY"],
            "aliases": [
                "إزمير",
                "Izmir",
                "Smyrna",
                "Esmirna",
                "इज़मिर",
                "Smirne",
                "イズミル",
                "Измир",
                "伊兹密尔",
            ],
        },
        {
            "item_raw": "Aden",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-YEMEN"],
            "aliases": [
                "عدن",
                "Aden",
                "Adén",
                "एडन",
                "アデン",
                "Аден",
                "亚丁",
            ],
        },
        {
            "item_raw": "Houthis",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-YEMEN"],
            "aliases": [
                "الحوثيون",
                "Huthis",
                "Houthis",
                "Ansar Allah",
                "Huthíes",
                "हौथिस",
                "Houthi",
                "フーシ",
                "хуситы",
                "胡塞武装",
            ],
        },
        {
            "item_raw": "Bashar al-Assad",
            "item_type": "person",
            "centroid_ids": ["MIDEAST-SYRIA"],
            "aliases": [
                "بشار الأسد",
                "Baschar al-Assad",
                "Bashar al-Assad",
                "Bashar al-Ásad",
                "Bachar el-Assad",
                "बशर अल-असद",
                "バッシャール・アル＝アサド",
                "Башар Асад",
                "巴沙尔·阿萨德",
            ],
        },
        {
            "item_raw": "Mashhad",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-IRAN"],
            "aliases": [
                "مشهد",
                "Maschhad",
                "Mashhad",
                "Mechhed",
                "मशहद",
                "マシュハド",
                "Мешхед",
                "马什哈德",
            ],
        },
        {
            "item_raw": "Hassan Nasrallah",
            "item_type": "person",
            "centroid_ids": ["MIDEAST-LEBANON"],
            "aliases": [
                "حسن نصر الله",
                "Hassan Nasrallah",
                "Hasan Nasralá",
                "हसन नसरुल्लाह",
                "ハサン・ナスラッラー",
                "Хасан Насралла",
                "哈桑·纳斯鲁拉",
            ],
        },
        {
            "item_raw": "Abu Dhabi",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-GULF"],
            "aliases": [
                "أبو ظبي",
                "Abu Dhabi",
                "Abu Dabi",
                "Abou Dhabi",
                "अबू धाबी",
                "アブダビ",
                "Абу-Даби",
                "阿布扎比",
            ],
        },
        {
            "item_raw": "Tamim bin Hamad",
            "item_type": "person",
            "centroid_ids": ["MIDEAST-GULF"],
            "aliases": [
                "تميم بن حمد",
                "Tamim bin Hamad",
                "Emir Tamim",
                "Tamim ben Hamad",
                "तमीम बिन हमद",
                "タミーム・ビン・ハマド",
                "Тамим бин Хамад",
                "塔米姆·本·哈马德",
            ],
        },
        {
            "item_raw": "Kuwait",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-GULF"],
            "aliases": [
                "الكويت",
                "Kuwait",
                "State of Kuwait",
                "Koweït",
                "कुवैत",
                "クウェート",
                "Кувейт",
                "科威特",
            ],
        },
        {
            "item_raw": "Gaza",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-PALESTINE"],
            "aliases": [
                "غزة",
                "Gaza",
                "Gaza Strip",
                "गाजा",
                "ガザ",
                "Газа",
                "加沙",
            ],
        },
        {
            "item_raw": "Jenin",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-PALESTINE"],
            "aliases": [
                "جنين",
                "Dschenin",
                "Jenin",
                "Yenín",
                "Jénine",
                "जेनिन",
                "ジェニン",
                "Дженин",
                "杰宁",
            ],
        },
        {
            "item_raw": "Hebron",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-PALESTINE"],
            "aliases": [
                "الخليل",
                "Hebron",
                "Al-Khalil",
                "Hebrón",
                "Hébron",
                "हेब्रोन",
                "ヘブロン",
                "Хеврон",
                "希伯伦",
            ],
        },
        {
            "item_raw": "Nablus",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-PALESTINE"],
            "aliases": [
                "نابلس",
                "Nablus",
                "Naplouse",
                "नाब्लस",
                "ナーブルス",
                "Наблус",
                "纳布卢斯",
            ],
        },
        {
            "item_raw": "Islamic Jihad",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-PALESTINE"],
            "aliases": [
                "الجهاد الإسلامي",
                "Islamischer Dschihad",
                "Islamic Jihad",
                "Palestinian Islamic Jihad",
                "Yihad Islámica",
                "Jihad islamique",
                "इस्लामिक जिहाद",
                "Jihad Islamica",
                "イスラム聖戦",
                "Исламский джихад",
                "伊斯兰圣战组织",
            ],
        },
        {
            "item_raw": "Yahya Sinwar",
            "item_type": "person",
            "centroid_ids": ["MIDEAST-PALESTINE"],
            "aliases": [
                "يحيى السنوار",
                "Jahja al-Sinwar",
                "Yahya Sinwar",
                "Yahya Sinouar",
                "यह्या सिनवार",
                "ヤヒヤ・シンワル",
                "Яхья Синуар",
                "叶海亚·辛瓦尔",
            ],
        },
        {
            "item_raw": "Fatah",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-PALESTINE"],
            "aliases": [
                "فتح",
                "Fatah",
                "फतह",
                "ファタハ",
                "ФАТХ",
                "法塔赫",
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
            print("Upserting batch 3 taxonomy items with comprehensive aliases...\n")

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
            print(
                f"\nSuccessfully processed {len(items)} taxonomy items (batch 3 - FINAL)!"
            )

        conn.close()
        return True

    except Exception as e:
        print(f"Upsert failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = upsert_batch3_aliases()
    sys.exit(0 if success else 1)
