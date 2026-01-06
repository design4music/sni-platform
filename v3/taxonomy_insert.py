"""Insert CANADA taxonomy items"""

import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config

conn = psycopg2.connect(
    host=config.db_host,
    port=config.db_port,
    database=config.db_name,
    user=config.db_user,
    password=config.db_password,
)

try:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO taxonomy_v3 (item_raw, item_type, aliases, centroid_id)
            VALUES
                ('Royal Bank of Canada', 'org', '{"ar": ["رويال بنك أوف كندا"], "en": ["RBC"], "ru": ["Королевский банк Канады"], "zh": ["加拿大皇家银行"], "ja": ["ロイヤルバンク・オブ・カナダ"]}'::jsonb, 'AMERICAS-CANADA'),
                ('TD Bank', 'org', '{"ar": ["تي دي بنك"], "ru": ["ТД Банк"], "zh": ["道明银行"], "ja": ["TDバンク"]}'::jsonb, 'AMERICAS-CANADA'),
                ('Shopify', 'org', '{"ar": ["شوبيفاي"], "ru": ["Шопифай"], "zh": ["Shopify电商平台"], "ja": ["ショピファイ"]}'::jsonb, 'AMERICAS-CANADA'),
                ('BlackBerry', 'org', '{"ar": ["بلاك بيري"], "ru": ["БлэкБерри"], "zh": ["黑莓公司"], "ja": ["ブラックベリー"]}'::jsonb, 'AMERICAS-CANADA'),
                ('Bombardier', 'org', '{"ar": ["بومباردييه"], "ru": ["Бомбардье"], "zh": ["庞巴迪公司"], "ja": ["ボンバルディア"]}'::jsonb, 'AMERICAS-CANADA'),
                ('CAE', 'org', '{"ar": ["سي اي اي"], "ru": ["КАЕ"], "zh": ["CAE飞行模拟器公司"], "ja": ["CAE"]}'::jsonb, 'AMERICAS-CANADA'),
                ('Canadian Natural Resources', 'org', '{"ar": ["الموارد الطبيعية الكندية"], "ru": ["Канадские природные ресурсы"], "zh": ["加拿大自然资源公司"], "ja": ["カナディアン・ナチュラル・リソーシズ"]}'::jsonb, 'AMERICAS-CANADA'),
                ('Suncor', 'org', '{"ar": ["سينكور"], "ru": ["Санкор"], "zh": ["森科能源"], "ja": ["サンコー"]}'::jsonb, 'AMERICAS-CANADA'),
                ('Barrick Gold', 'org', '{"ar": ["باريك جولد"], "ru": ["Баррик Голд"], "zh": ["巴里克黄金公司"], "ja": ["バリック・ゴールド"]}'::jsonb, 'AMERICAS-CANADA'),
                ('Teck Resources', 'org', '{"ar": ["تيك ريسورسز"], "ru": ["Тек Ресурсез"], "zh": ["泰克资源"], "ja": ["テック・リソーシズ"]}'::jsonb, 'AMERICAS-CANADA'),
                ('OpenText', 'org', '{"ar": ["أوبن تيكست"], "ru": ["ОпенТекст"], "zh": ["OpenText软件公司"], "ja": ["オープンテキスト"]}'::jsonb, 'AMERICAS-CANADA'),
                ('Celestica', 'org', '{"ar": ["سيليستيكا"], "ru": ["Селестика"], "zh": ["赛莱斯蒂卡电子制造"], "ja": ["セレスティカ"]}'::jsonb, 'AMERICAS-CANADA');
        """
        )

    conn.commit()
    print("OK: Successfully inserted 8 taxonomy items for AMERICAS-CANADA")

    # Verify
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT item_raw, item_type
            FROM taxonomy_v3
            WHERE centroid_id = 'AMERICAS-CANADA'
            ORDER BY item_type, item_raw
        """
        )
        print("\nInserted items:")
        for row in cur.fetchall():
            print(f"  - {row[1]}: {row[0]}")

except Exception as e:
    conn.rollback()
    print(f"X Error: {e}")
    import traceback

    traceback.print_exc()

finally:
    conn.close()
