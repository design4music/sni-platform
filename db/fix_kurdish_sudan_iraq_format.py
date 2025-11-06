"""Convert Kurdish, Sudanese, and Iraqi items to language-code format"""

import json
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def fix_kurdish_sudan_iraq_format():
    """Convert 18 items to language-code alias format"""

    # Reconstructing from the user's original data
    items_by_name = {
        "Rojava": {
            "ar": ["روجافا"],
            "de": ["Rojava"],
            "en": ["Rojava", "Syrian Kurdistan", "Western Kurdistan"],
            "es": ["Rojava"],
            "fr": ["Rojava"],
            "hi": ["रोजावा"],
            "it": ["Rojava"],
            "ja": ["ロジャヴァ"],
            "ru": ["Рожава"],
            "zh": ["罗贾瓦"],
        },
        "Kurdistan": {
            "ar": ["كردستان"],
            "de": ["Kurdistan"],
            "en": ["Kurdistan", "Kurdish region", "Kurdish lands"],
            "es": ["Kurdistán"],
            "fr": ["Kurdistan"],
            "hi": ["कुर्दिस्तान"],
            "it": ["Kurdistan"],
            "ja": ["クルディスタン"],
            "ru": ["Курдистан"],
            "zh": ["库尔德斯坦"],
        },
        "Kurds": {
            "ar": ["الأكراد"],
            "de": ["Kurden"],
            "en": ["Kurds", "Kurdish people"],
            "es": ["kurdos"],
            "fr": ["Kurdes"],
            "hi": ["कुर्द"],
            "it": ["curdi"],
            "ja": ["クルド人"],
            "ru": ["курды"],
            "zh": ["库尔德人"],
        },
        "Kurdish": {
            "ar": ["كردي"],
            "de": ["kurdisch"],
            "en": ["Kurdish"],
            "es": ["kurdo"],
            "fr": ["kurde"],
            "hi": ["कुर्दिश"],
            "it": ["curdo"],
            "ja": ["クルドの"],
            "ru": ["курдский"],
            "zh": ["库尔德的"],
        },
        "PKK": {
            "ar": ["حزب العمال الكردستاني"],
            "de": ["PKK", "Arbeiterpartei Kurdistans"],
            "en": ["PKK", "Kurdistan Workers' Party"],
            "es": ["PKK", "Partido de los Trabajadores de Kurdistán"],
            "fr": ["PKK", "Parti des travailleurs du Kurdistan"],
            "hi": ["पीकेके", "कुर्दिस्तान वर्कर्स पार्टी"],
            "it": ["PKK", "Partito dei Lavoratori del Kurdistan"],
            "ja": ["PKK", "クルディスタン労働者党"],
            "ru": ["ПКК", "Курдская рабочая партия"],
            "zh": ["库尔德工人党", "PKK"],
        },
        "YPG": {
            "ar": ["وحدات حماية الشعب"],
            "de": ["YPG", "Volksschutzeinheiten"],
            "en": ["YPG", "People's Protection Units"],
            "es": ["YPG", "Unidades de Protección Popular"],
            "fr": ["YPG", "Unités de protection du peuple"],
            "hi": ["वाईपीजी", "पीपल्स प्रोटेक्शन यूनिट्स"],
            "it": ["YPG", "Unità di Protezione Popolare"],
            "ja": ["YPG", "人民防衛部隊"],
            "ru": ["ЮПГ", "Отряды народной самообороны"],
            "zh": ["人民保护部队", "YPG"],
        },
        "Peshmerga": {
            "ar": ["البشمركة"],
            "de": ["Peschmerga"],
            "en": ["Peshmerga", "Kurdish fighters"],
            "es": ["Peshmerga"],
            "fr": ["Peshmerga"],
            "hi": ["पेशमर्गा"],
            "it": ["Peshmerga"],
            "ja": ["ペシュメルガ"],
            "ru": ["пешмерга"],
            "zh": ["佩什梅格"],
        },
        "Sudanese Armed Forces": {
            "ar": ["القوات المسلحة السودانية"],
            "de": ["Sudanesische Streitkräfte"],
            "en": ["Sudanese Armed Forces", "SAF"],
            "es": ["Fuerzas Armadas de Sudán"],
            "fr": ["Forces armées soudanaises"],
            "hi": ["सूडानी सशस्त्र बल"],
            "it": ["Forze Armate Sudanesi"],
            "ja": ["スーダン軍"],
            "ru": ["Суданские вооруженные силы"],
            "zh": ["苏丹武装部队"],
        },
        "Rapid Support Forces": {
            "ar": ["قوات الدعم السريع"],
            "de": ["Schnelle Unterstützungskräfte", "RSF"],
            "en": ["Rapid Support Forces", "RSF"],
            "es": ["Fuerzas de Apoyo Rápido"],
            "fr": ["Forces de soutien rapide"],
            "hi": ["रैपिड सपोर्ट फोर्सेस"],
            "it": ["Forze di Supporto Rapido"],
            "ja": ["迅速支援部隊"],
            "ru": ["Силы быстрой поддержки"],
            "zh": ["快速支援部队"],
        },
        "Abdel Fattah al-Burhan": {
            "ar": ["عبد الفتاح البرهان"],
            "de": ["Abdel Fattah al-Burhan"],
            "en": ["Abdel Fattah al-Burhan", "General al-Burhan"],
            "es": ["Abdel Fattah al-Burhan"],
            "fr": ["Abdel Fattah al-Bourhane"],
            "hi": ["अब्देल फतह अल-बुरहान"],
            "it": ["Abdel Fattah al-Burhan"],
            "ja": ["アブデルファタハ・アルブルハン"],
            "ru": ["Абдель Фаттах аль-Бурхан"],
            "zh": ["阿卜杜勒·法塔赫·布尔汉"],
        },
        "Mohamed Hamdan Dagalo": {
            "ar": ["محمد حمدان دقلو"],
            "de": ["Mohamed Hamdan Dagalo", "Hemedti"],
            "en": ["Mohamed Hamdan Dagalo", "Hemedti"],
            "es": ["Mohamed Hamdan Dagalo"],
            "fr": ["Mohamed Hamdan Dagalo"],
            "hi": ["मोहम्मद हमदान दागालो"],
            "it": ["Mohamed Hamdan Dagalo"],
            "ja": ["モハメド・ハムダン・ダガロ"],
            "ru": ["Мохамед Хамдан Дагало"],
            "zh": ["穆罕默德·哈姆丹·达加洛"],
        },
        "Port Sudan": {
            "ar": ["بورتسودان"],
            "de": ["Port Sudan"],
            "en": ["Port Sudan"],
            "es": ["Port Sudan"],
            "fr": ["Port-Soudan"],
            "hi": ["पोर्ट सूडान"],
            "it": ["Port Sudan"],
            "ja": ["ポートスーダン"],
            "ru": ["Порт-Судан"],
            "zh": ["苏丹港"],
        },
        "Darfur": {
            "ar": ["دارفور"],
            "de": ["Darfur"],
            "en": ["Darfur"],
            "es": ["Darfur"],
            "fr": ["Darfour"],
            "hi": ["दारफुर"],
            "it": ["Darfur"],
            "ja": ["ダルフール"],
            "ru": ["Дарфур"],
            "zh": ["达尔富尔"],
        },
        "Erbil": {
            "ar": ["أربيل", "هولير"],
            "de": ["Erbil", "Arbela"],
            "en": ["Erbil", "Arbil", "Hawler"],
            "es": ["Erbil", "Arbela"],
            "fr": ["Erbil", "Arbèle"],
            "hi": ["अर्बिल", "एर्बिल"],
            "it": ["Erbil", "Arbela"],
            "ja": ["エルビル", "アルビール"],
            "ru": ["Эрбиль", "Арбиль"],
            "zh": ["埃尔比勒", "艾尔比勒"],
        },
        "Basra": {
            "ar": ["البصرة"],
            "de": ["Basra"],
            "en": ["Basra", "Al-Basrah", "Basrah"],
            "es": ["Basora"],
            "fr": ["Bassora"],
            "hi": ["बसरा", "बस्रा"],
            "it": ["Bassora"],
            "ja": ["バスラ"],
            "ru": ["Басра"],
            "zh": ["巴士拉", "巴斯拉"],
        },
        "Mosul": {
            "ar": ["الموصل"],
            "de": ["Mosul"],
            "en": ["Mosul", "Al-Mawsil"],
            "es": ["Mosul"],
            "fr": ["Mossoul"],
            "hi": ["मोसुल", "मूसिल"],
            "it": ["Mosul"],
            "ja": ["モースル"],
            "ru": ["Мосул"],
            "zh": ["摩苏尔", "摩蘇爾"],
        },
        "Popular Mobilization Forces": {
            "ar": ["الحشد الشعبي", "قوات الحشد الشعبي"],
            "de": ["Volksmobilisierungskräfte", "PMF"],
            "en": [
                "Popular Mobilization Forces",
                "PMF",
                "Hashd al-Shaabi",
                "Popular Mobilization Units",
            ],
            "es": ["Fuerzas de Movilización Popular", "PMF"],
            "fr": ["Forces de mobilisation populaire", "PMF"],
            "hi": ["पॉपुलर मोबिलाइजेशन फोर्सेस", "पीएमएफ"],
            "it": ["Forze di Mobilitazione Popolare", "PMF"],
            "ja": ["人民動員隊", "PMF"],
            "ru": ["Народные мобилизационные силы", "ПМС"],
            "zh": ["人民动员力量", "人民动员组织", "PMF"],
        },
        "Kurdistan Regional Government": {
            "ar": ["حكومة إقليم كردستان"],
            "de": ["Regionale Regierung Kurdistans", "KRG"],
            "en": [
                "Kurdistan Regional Government",
                "KRG",
                "Kurdish Regional Government",
            ],
            "es": ["Gobierno Regional del Kurdistán", "KRG"],
            "fr": ["Gouvernement régional du Kurdistan", "KRG"],
            "hi": ["कुर्दिस्तान क्षेत्रीय सरकार", "केआरजी"],
            "it": ["Governo Regionale del Kurdistan", "KRG"],
            "ja": ["クルディスタン地域政府", "KRG"],
            "ru": ["Региональное правительство Курдистана", "ПКК"],
            "zh": ["库尔德斯坦地区政府", "库区", "KRG"],
        },
    }

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
            print("Converting 18 items to language-code alias format...\n")

            for item_name, aliases in items_by_name.items():
                cur.execute(
                    """
                    UPDATE taxonomy_v3
                    SET aliases = %s::jsonb,
                        updated_at = NOW()
                    WHERE item_raw = %s
                    RETURNING id
                """,
                    (json.dumps(aliases), item_name),
                )
                result = cur.fetchone()
                if result:
                    lang_count = len(aliases)
                    total_aliases = sum(len(v) for v in aliases.values())
                    print(
                        f"  [FIXED] {item_name:35} -> {lang_count} languages, {total_aliases} aliases"
                    )
                else:
                    print(f"  [NOT FOUND] {item_name}")

            conn.commit()
            print("\nSuccessfully converted 18 items to language-code format!")

        conn.close()
        return True

    except Exception as e:
        print(f"Conversion failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = fix_kurdish_sudan_iraq_format()
    sys.exit(0 if success else 1)
