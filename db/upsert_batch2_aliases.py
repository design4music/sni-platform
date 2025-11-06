"""Update/insert second batch of taxonomy items with comprehensive multilingual aliases"""

import json
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def upsert_batch2_aliases():
    """Update or insert 15 more taxonomy items with full multilingual aliases"""

    items = [
        {
            "item_raw": "Abqaiq",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-SAUDI"],
            "aliases": ["بقيق", "Abqaiq", "अबकैक", "アブカイク", "Абкайк", "布盖格"],
        },
        {
            "item_raw": "Abu Mohammad al-Julani",
            "item_type": "person",
            "centroid_ids": ["MIDEAST-SYRIA"],
            "aliases": [
                "أبو محمد الجولاني",
                "Abu Mohammed al-Dschulani",
                "Abu Mohammad al-Julani",
                "al-Julani",
                "Abou Mohammed al-Joulani",
                "अबू मोहम्मद अल-जुलानी",
                "アブ・ムハンマド・アル＝ジュラーニ",
                "Абу Мухаммад аль-Джулани",
                "阿布·穆罕默德·朱拉尼",
            ],
        },
        {
            "item_raw": "Aman",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-ISRAEL"],
            "aliases": [
                "أمان",
                "Aman",
                "Israeli Military Intelligence",
                "अमन",
                "アマン",
                "Аман",
                "阿曼",
            ],
        },
        {
            "item_raw": "Arak",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-IRAN"],
            "aliases": [
                "آراك",
                "Arak",
                "Arak Heavy Water Reactor",
                "अराक",
                "アラク",
                "Арак",
                "阿拉克",
            ],
        },
        {
            "item_raw": "Arrow 3",
            "item_type": "model",
            "centroid_ids": ["MIDEAST-ISRAEL"],
            "aliases": [
                "السهم 3",
                "Arrow 3",
                "Arrow III",
                "एरो 3",
                "アロー3",
                "«Хец-3»",
                "箭-3",
            ],
        },
        {
            "item_raw": "Bab al-Mandab",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-YEMEN"],
            "aliases": [
                "باب المندب",
                "Bab al-Mandab",
                "Bab el-Mandeb",
                "बाब अल-मंदब",
                "バブ・エル・マンデブ海峡",
                "Баб-эль-Мандебский пролив",
                "曼德海峡",
            ],
        },
        {
            "item_raw": "Bandar Abbas",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-IRAN"],
            "aliases": [
                "بندر عباس",
                "Bandar Abbas",
                "बंदर अब्बास",
                "バンダレ・アッバース",
                "Бендер-Аббас",
                "阿巴斯港",
            ],
        },
        {
            "item_raw": "Bekaa Valley",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-LEBANON"],
            "aliases": [
                "وادي البقاع",
                "Bekaa-Tal",
                "Bekaa Valley",
                "Valle de la Becá",
                "Vallée de la Bekaa",
                "बेकाआ वैली",
                "Valle della Beqa",
                "ベッカーバレー",
                "долина Бекаа",
                "贝卡谷地",
            ],
        },
        {
            "item_raw": "Burkan",
            "item_type": "model",
            "centroid_ids": ["MIDEAST-YEMEN"],
            "aliases": [
                "بركان",
                "Burkan",
                "Burkan missile",
                "बुर्कान",
                "ブルカン",
                "«Буркан»",
                "火山",
            ],
        },
        {
            "item_raw": "Chabahar",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-IRAN"],
            "aliases": [
                "تشابهار",
                "Tschabahar",
                "Chabahar",
                "Chah Bahar",
                "Tchah Bahar",
                "चाबहार",
                "チャーバハール",
                "Чебахар",
                "恰巴哈尔",
            ],
        },
        {
            "item_raw": "David's Sling",
            "item_type": "model",
            "centroid_ids": ["MIDEAST-ISRAEL"],
            "aliases": [
                "قذيفة داوود",
                "Davids Schleuder",
                "David's Sling",
                "Honda de David",
                "Fronde de David",
                "डेविड्स स्लिंग",
                "Fionda di Davide",
                "デイビッドスリング",
                "«Праща Давида»",
                "大卫弹弓",
            ],
        },
        {
            "item_raw": "Deir ez-Zor",
            "item_type": "geo",
            "centroid_ids": ["MIDEAST-SYRIA"],
            "aliases": [
                "دير الزور",
                "Deir ez-Zor",
                "Deir al-Zor",
                "देइर एज़ ज़ोर",
                "デイル・エッゾール",
                "Дейр-эз-Зор",
                "代尔祖尔",
            ],
        },
        {
            "item_raw": "Fateh-110",
            "item_type": "model",
            "centroid_ids": ["MIDEAST-IRAN"],
            "aliases": [
                "فتح 110",
                "Fateh-110",
                "फतेह-110",
                "ファテフ110",
                "«Фатех-110»",
                "征服者-110",
            ],
        },
        {
            "item_raw": "Fordow",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-IRAN"],
            "aliases": [
                "فوردو",
                "Fordow",
                "Fordow Nuclear Facility",
                "फोर्डो",
                "フォルドウ",
                "Фордо",
                "福尔多",
            ],
        },
        {
            "item_raw": "Givati Brigade",
            "item_type": "org",
            "centroid_ids": ["MIDEAST-ISRAEL"],
            "aliases": [
                "لواء جفعاتي",
                "Givati-Brigade",
                "Givati Brigade",
                "Brigada Givati",
                "Brigade Givati",
                "गिवती ब्रिगेड",
                "Brigata Givati",
                "ギヴァティ旅団",
                "бригада «Гивати»",
                "吉瓦提旅",
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
            print("Upserting batch 2 taxonomy items with comprehensive aliases...\n")

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
            print(f"\nSuccessfully processed {len(items)} taxonomy items (batch 2)!")

        conn.close()
        return True

    except Exception as e:
        print(f"Upsert failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = upsert_batch2_aliases()
    sys.exit(0 if success else 1)
