"""Convert 51 recently updated items to language-code alias format"""

import json
import sys
from pathlib import Path

import psycopg2

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import config


def fix_alias_format():
    """Convert flat array aliases to language-code structure"""

    # All 51 items with proper language-code structure
    items = [
        # Batch 1
        {
            "item_raw": "Golan Heights",
            "aliases": {
                "ar": ["هضبة الجولان"],
                "de": ["Golanhöhen"],
                "en": ["Golan Heights"],
                "es": ["Altos del Golán"],
                "fr": ["Plateau du Golan"],
                "hi": ["गोलान हाइट्स"],
                "it": ["Alture del Golan"],
                "ja": ["ゴラン高原"],
                "ru": ["Голанские высоты"],
                "zh": ["戈兰高地"],
            },
        },
        {
            "item_raw": "Golani Brigade",
            "aliases": {
                "ar": ["لواء جولاني"],
                "de": ["Golani-Brigade"],
                "en": ["Golani Brigade"],
                "es": ["Brigada Golani"],
                "fr": ["Brigade Golani"],
                "hi": ["गोलानी ब्रिगेड"],
                "it": ["Brigata Golani"],
                "ja": ["ゴラニ旅団"],
                "ru": ["бригада «Голани»"],
                "zh": ["戈兰尼旅"],
            },
        },
        {
            "item_raw": "Haifa",
            "aliases": {
                "ar": ["حيفا"],
                "de": ["Haifa"],
                "en": ["Haifa"],
                "es": ["Haifa"],
                "fr": ["Haïfa"],
                "hi": ["हाइफा"],
                "it": ["Haifa"],
                "ja": ["ハイファ"],
                "ru": ["Хайфа"],
                "zh": ["海法"],
            },
        },
        {
            "item_raw": "Hayat Tahrir al-Sham",
            "aliases": {
                "ar": ["هيئة تحرير الشام"],
                "de": ["Hayat Tahrir al-Scham", "HTS"],
                "en": ["Hayat Tahrir al-Sham", "HTS"],
                "es": ["Hayat Tahrir al-Sham", "HTS"],
                "fr": ["Hayat Tahrir al-Cham", "HTS"],
                "hi": ["हयात तहरीर अल-शाम"],
                "it": ["Hayat Tahrir al-Sham", "HTS"],
                "ja": ["シャーム解放委員会"],
                "ru": ["Хайят Тахрир аш-Шам", "ХТШ"],
                "zh": ["沙姆解放组织", "HTS"],
            },
        },
        {
            "item_raw": "Homs",
            "aliases": {
                "ar": ["حمص"],
                "de": ["Homs"],
                "en": ["Homs"],
                "es": ["Homs"],
                "fr": ["Homs"],
                "hi": ["होम्स"],
                "it": ["Homs"],
                "ja": ["ホムス"],
                "ru": ["Хомс"],
                "zh": ["霍姆斯"],
            },
        },
        {
            "item_raw": "Syrian Democratic Forces",
            "aliases": {
                "ar": ["قوات سوريا الديمقراطية"],
                "de": ["Syrische Demokratische Kräfte", "SDF"],
                "en": ["Syrian Democratic Forces", "SDF"],
                "es": ["Fuerzas Democráticas Sirias", "FDS"],
                "fr": ["Forces démocratiques syriennes", "FDS"],
                "hi": ["सीरियन डेमोक्रेटिक फोर्सेस"],
                "it": ["Forze Democratiche Siriane", "FDS"],
                "ja": ["シリア民主軍", "SDF"],
                "ru": ["Сирийские демократические силы", "СДС"],
                "zh": ["叙利亚民主力量", "SDF"],
            },
        },
        {
            "item_raw": "Taiz",
            "aliases": {
                "ar": ["تعز"],
                "de": ["Taizz"],
                "en": ["Taiz", "Ta'izz"],
                "es": ["Taiz"],
                "fr": ["Taëz"],
                "hi": ["ताइज़"],
                "it": ["Taiz"],
                "ja": ["タイズ"],
                "ru": ["Таиз"],
                "zh": ["塔伊兹"],
            },
        },
        {
            "item_raw": "Tartus",
            "aliases": {
                "ar": ["طرطوس"],
                "de": ["Tartus"],
                "en": ["Tartus"],
                "es": ["Tartus"],
                "fr": ["Tartous"],
                "hi": ["टार्टस"],
                "it": ["Tartus"],
                "ja": ["タルトゥース"],
                "ru": ["Тартус"],
                "zh": ["塔尔图斯"],
            },
        },
        {
            "item_raw": "Tel Aviv",
            "aliases": {
                "ar": ["تل أبيب"],
                "de": ["Tel Aviv"],
                "en": ["Tel Aviv", "Tel Aviv-Yafo"],
                "es": ["Tel Aviv"],
                "fr": ["Tel Aviv"],
                "hi": ["तेल अवीव"],
                "it": ["Tel Aviv"],
                "ja": ["テルアビブ"],
                "ru": ["Тель-Авив"],
                "zh": ["特拉维夫"],
            },
        },
        {
            "item_raw": "THAAD",
            "aliases": {
                "ar": ["ثاد"],
                "de": ["THAAD"],
                "en": ["THAAD", "Terminal High Altitude Area Defense"],
                "es": ["THAAD"],
                "fr": ["THAAD"],
                "hi": ["थाड"],
                "it": ["THAAD"],
                "ja": ["THAAD"],
                "ru": ["THAAD", "Противоракетный комплекс THAAD"],
                "zh": ["萨德", "THAAD"],
            },
        },
        {
            "item_raw": "Tiger Forces",
            "aliases": {
                "ar": ["قوات النمر"],
                "de": ["Tiger-Kräfte"],
                "en": ["Tiger Forces", "Tiger Division"],
                "es": ["Fuerzas Tigre"],
                "fr": ["Forces du Tigre"],
                "hi": ["टाइगर फोर्सेस"],
                "it": ["Forze della Tigre"],
                "ja": ["タイガー部隊"],
                "ru": ["«Тигровые силы»"],
                "zh": ["老虎部队"],
            },
        },
        {
            "item_raw": "Unit 8200",
            "aliases": {
                "ar": ["الوحدة 8200"],
                "de": ["Einheit 8200"],
                "en": ["Unit 8200"],
                "es": ["Unidad 8200"],
                "fr": ["Unité 8200"],
                "hi": ["यूनिट 8200"],
                "it": ["Unità 8200"],
                "ja": ["8200部隊"],
                "ru": ["подразделение 8200"],
                "zh": ["8200部队"],
            },
        },
        {
            "item_raw": "Hassi Messaoud",
            "aliases": {
                "ar": ["حاسي مسعود"],
                "de": ["Hassi Messaoud"],
                "en": ["Hassi Messaoud"],
                "es": ["Hassi Messaoud"],
                "fr": ["Hassi Messaoud"],
                "hi": ["हस्सी मस्सौद"],
                "it": ["Hassi Messaoud"],
                "ja": ["ハッシ・メサウド"],
                "ru": ["Хасси-Месауд"],
                "zh": ["哈西迈萨乌德"],
            },
        },
        {
            "item_raw": "Abdelmadjid Tebboune",
            "aliases": {
                "ar": ["عبد المجيد تبون"],
                "de": ["Abdelmadjid Tebboune"],
                "en": ["Abdelmadjid Tebboune", "President Tebboune"],
                "es": ["Abdelmadjid Tebboune"],
                "fr": ["Abdelmadjid Tebboune"],
                "hi": ["अब्देलमजीद तेब्बौने"],
                "it": ["Abdelmadjid Tebboune"],
                "ja": ["アブデルマジド・テブン"],
                "ru": ["Абдельмаджид Теббун"],
                "zh": ["阿卜杜勒马吉德·特本"],
            },
        },
        {
            "item_raw": "Sonatrach",
            "aliases": {
                "ar": ["سوناطراك"],
                "de": ["Sonatrach"],
                "en": ["Sonatrach"],
                "es": ["Sonatrach"],
                "fr": ["Sonatrach"],
                "hi": ["सोनात्राच"],
                "it": ["Sonatrach"],
                "ja": ["ソナトラック"],
                "ru": ["Сонатрак"],
                "zh": ["索纳塔克"],
            },
        },
        # Batch 2
        {
            "item_raw": "Abqaiq",
            "aliases": {
                "ar": ["بقيق"],
                "de": ["Abqaiq"],
                "en": ["Abqaiq"],
                "es": ["Abqaiq"],
                "fr": ["Abqaiq"],
                "hi": ["अबकैक"],
                "it": ["Abqaiq"],
                "ja": ["アブカイク"],
                "ru": ["Абкайк"],
                "zh": ["布盖格"],
            },
        },
        {
            "item_raw": "Abu Mohammad al-Julani",
            "aliases": {
                "ar": ["أبو محمد الجولاني"],
                "de": ["Abu Mohammed al-Dschulani"],
                "en": ["Abu Mohammad al-Julani", "al-Julani"],
                "es": ["Abu Mohammad al-Julani"],
                "fr": ["Abou Mohammed al-Joulani"],
                "hi": ["अबू मोहम्मद अल-जुलानी"],
                "it": ["Abu Mohammad al-Julani"],
                "ja": ["アブ・ムハンマド・アル＝ジュラーニ"],
                "ru": ["Абу Мухаммад аль-Джулани"],
                "zh": ["阿布·穆罕默德·朱拉尼"],
            },
        },
        {
            "item_raw": "Aman",
            "aliases": {
                "ar": ["أمان"],
                "de": ["Aman"],
                "en": ["Aman", "Israeli Military Intelligence"],
                "es": ["Aman"],
                "fr": ["Aman"],
                "hi": ["अमन"],
                "it": ["Aman"],
                "ja": ["アマン"],
                "ru": ["Аман"],
                "zh": ["阿曼"],
            },
        },
        {
            "item_raw": "Arak",
            "aliases": {
                "ar": ["آراك"],
                "de": ["Arak"],
                "en": ["Arak", "Arak Heavy Water Reactor"],
                "es": ["Arak"],
                "fr": ["Arak"],
                "hi": ["अराक"],
                "it": ["Arak"],
                "ja": ["アラク"],
                "ru": ["Арак"],
                "zh": ["阿拉克"],
            },
        },
        {
            "item_raw": "Arrow 3",
            "aliases": {
                "ar": ["السهم 3"],
                "de": ["Arrow 3"],
                "en": ["Arrow 3", "Arrow III"],
                "es": ["Arrow 3"],
                "fr": ["Arrow 3"],
                "hi": ["एरो 3"],
                "it": ["Arrow 3"],
                "ja": ["アロー3"],
                "ru": ["«Хец-3»"],
                "zh": ["箭-3"],
            },
        },
        {
            "item_raw": "Bab al-Mandab",
            "aliases": {
                "ar": ["باب المندب"],
                "de": ["Bab al-Mandab"],
                "en": ["Bab al-Mandab", "Bab el-Mandeb"],
                "es": ["Bab el-Mandeb"],
                "fr": ["Bab el-Mandeb"],
                "hi": ["बाब अल-मंदब"],
                "it": ["Bab el-Mandeb"],
                "ja": ["バブ・エル・マンデブ海峡"],
                "ru": ["Баб-эль-Мандебский пролив"],
                "zh": ["曼德海峡"],
            },
        },
        {
            "item_raw": "Bandar Abbas",
            "aliases": {
                "ar": ["بندر عباس"],
                "de": ["Bandar Abbas"],
                "en": ["Bandar Abbas"],
                "es": ["Bandar Abbas"],
                "fr": ["Bandar Abbas"],
                "hi": ["बंदर अब्बास"],
                "it": ["Bandar Abbas"],
                "ja": ["バンダレ・アッバース"],
                "ru": ["Бендер-Аббас"],
                "zh": ["阿巴斯港"],
            },
        },
        {
            "item_raw": "Bekaa Valley",
            "aliases": {
                "ar": ["وادي البقاع"],
                "de": ["Bekaa-Tal"],
                "en": ["Bekaa Valley"],
                "es": ["Valle de la Becá"],
                "fr": ["Vallée de la Bekaa"],
                "hi": ["बेकाआ वैली"],
                "it": ["Valle della Beqa"],
                "ja": ["ベッカーバレー"],
                "ru": ["долина Бекаа"],
                "zh": ["贝卡谷地"],
            },
        },
        {
            "item_raw": "Burkan",
            "aliases": {
                "ar": ["بركان"],
                "de": ["Burkan"],
                "en": ["Burkan", "Burkan missile"],
                "es": ["Burkan"],
                "fr": ["Burkan"],
                "hi": ["बुर्कान"],
                "it": ["Burkan"],
                "ja": ["ブルカン"],
                "ru": ["«Буркан»"],
                "zh": ["火山"],
            },
        },
        {
            "item_raw": "Chabahar",
            "aliases": {
                "ar": ["تشابهار"],
                "de": ["Tschabahar"],
                "en": ["Chabahar", "Chah Bahar"],
                "es": ["Chabahar"],
                "fr": ["Tchah Bahar"],
                "hi": ["चाबहार"],
                "it": ["Chabahar"],
                "ja": ["チャーバハール"],
                "ru": ["Чебахар"],
                "zh": ["恰巴哈尔"],
            },
        },
        {
            "item_raw": "David's Sling",
            "aliases": {
                "ar": ["قذيفة داوود"],
                "de": ["Davids Schleuder"],
                "en": ["David's Sling"],
                "es": ["Honda de David"],
                "fr": ["Fronde de David"],
                "hi": ["डेविड्स स्लिंग"],
                "it": ["Fionda di Davide"],
                "ja": ["デイビッドスリング"],
                "ru": ["«Праща Давида»"],
                "zh": ["大卫弹弓"],
            },
        },
        {
            "item_raw": "Deir ez-Zor",
            "aliases": {
                "ar": ["دير الزور"],
                "de": ["Deir ez-Zor"],
                "en": ["Deir ez-Zor", "Deir al-Zor"],
                "es": ["Deir ez-Zor"],
                "fr": ["Deir ez-Zor"],
                "hi": ["देइर एज़ ज़ोर"],
                "it": ["Deir ez-Zor"],
                "ja": ["デイル・エッゾール"],
                "ru": ["Дейр-эз-Зор"],
                "zh": ["代尔祖尔"],
            },
        },
        {
            "item_raw": "Fateh-110",
            "aliases": {
                "ar": ["فتح 110"],
                "de": ["Fateh-110"],
                "en": ["Fateh-110"],
                "es": ["Fateh-110"],
                "fr": ["Fateh-110"],
                "hi": ["फतेह-110"],
                "it": ["Fateh-110"],
                "ja": ["ファテフ110"],
                "ru": ["«Фатех-110»"],
                "zh": ["征服者-110"],
            },
        },
        {
            "item_raw": "Fordow",
            "aliases": {
                "ar": ["فوردو"],
                "de": ["Fordow"],
                "en": ["Fordow", "Fordow Nuclear Facility"],
                "es": ["Fordow"],
                "fr": ["Fordow"],
                "hi": ["फोर्डो"],
                "it": ["Fordow"],
                "ja": ["フォルドウ"],
                "ru": ["Фордо"],
                "zh": ["福尔多"],
            },
        },
        {
            "item_raw": "Givati Brigade",
            "aliases": {
                "ar": ["لواء جفعاتي"],
                "de": ["Givati-Brigade"],
                "en": ["Givati Brigade"],
                "es": ["Brigada Givati"],
                "fr": ["Brigade Givati"],
                "hi": ["गिवती ब्रिगेड"],
                "it": ["Brigata Givati"],
                "ja": ["ギヴァティ旅団"],
                "ru": ["бригада «Гивати»"],
                "zh": ["吉瓦提旅"],
            },
        },
        # Batch 3
        {
            "item_raw": "Ismail Haniyeh",
            "aliases": {
                "ar": ["إسماعيل هنية"],
                "de": ["Ismail Haniyeh"],
                "en": ["Ismail Haniyeh"],
                "es": ["Ismail Haniyeh"],
                "fr": ["Ismaïl Haniyeh"],
                "hi": ["इस्माइल हनिया"],
                "it": ["Ismail Haniyeh"],
                "ja": ["イスマーイール・ハニーヤ"],
                "ru": ["Исмаил Хания"],
                "zh": ["伊斯梅尔·哈尼亚"],
            },
        },
        {
            "item_raw": "Hezbollah",
            "aliases": {
                "ar": ["حزب الله"],
                "de": ["Hisbollah"],
                "en": ["Hezbollah", "Hizbullah", "Party of God"],
                "es": ["Hezbolá"],
                "fr": ["Hezbollah"],
                "hi": ["हेज़बोल्लाह"],
                "it": ["Hezbollah"],
                "ja": ["ヒズボラ"],
                "ru": ["Хезболла"],
                "zh": ["真主党"],
            },
        },
        {
            "item_raw": "Masoud Pezeshkian",
            "aliases": {
                "ar": ["مسعود بزشكيان"],
                "de": ["Massud Peseschkian"],
                "en": ["Masoud Pezeshkian"],
                "es": ["Masud Pezeshkian"],
                "fr": ["Massoud Pezeshkian"],
                "hi": ["मसूद पेज़ेशकियान"],
                "it": ["Masoud Pezeshkian"],
                "ja": ["マスード・ペゼシュキヤン"],
                "ru": ["Масуд Пезешкиан"],
                "zh": ["马苏德·佩泽什基安"],
            },
        },
        {
            "item_raw": "Port Said",
            "aliases": {
                "ar": ["بورسعيد"],
                "de": ["Port Said"],
                "en": ["Port Said"],
                "es": ["Port Said"],
                "fr": ["Port-Saïd"],
                "hi": ["पोर्ट सईद"],
                "it": ["Port Said"],
                "ja": ["ポートサイド"],
                "ru": ["Порт-Саид"],
                "zh": ["塞得港"],
            },
        },
        {
            "item_raw": "Istanbul",
            "aliases": {
                "ar": ["إسطنبول"],
                "de": ["Istanbul"],
                "en": ["Istanbul", "Constantinople"],
                "es": ["Estambul"],
                "fr": ["Istanbul"],
                "hi": ["इस्तांबुल"],
                "it": ["Istanbul"],
                "ja": ["イスタンブール"],
                "ru": ["Стамбул"],
                "zh": ["伊斯坦布尔"],
            },
        },
        {
            "item_raw": "Izmir",
            "aliases": {
                "ar": ["إزمير"],
                "de": ["Izmir", "Smyrna"],
                "en": ["Izmir", "Smyrna"],
                "es": ["Esmirna"],
                "fr": ["Izmir"],
                "hi": ["इज़मिर"],
                "it": ["Smirne"],
                "ja": ["イズミル"],
                "ru": ["Измир"],
                "zh": ["伊兹密尔"],
            },
        },
        {
            "item_raw": "Aden",
            "aliases": {
                "ar": ["عدن"],
                "de": ["Aden"],
                "en": ["Aden"],
                "es": ["Adén"],
                "fr": ["Aden"],
                "hi": ["एडन"],
                "it": ["Aden"],
                "ja": ["アデン"],
                "ru": ["Аден"],
                "zh": ["亚丁"],
            },
        },
        {
            "item_raw": "Houthis",
            "aliases": {
                "ar": ["الحوثيون"],
                "de": ["Huthis"],
                "en": ["Houthis", "Ansar Allah"],
                "es": ["Huthíes"],
                "fr": ["Houthis"],
                "hi": ["हौथिस"],
                "it": ["Houthi"],
                "ja": ["フーシ"],
                "ru": ["хуситы"],
                "zh": ["胡塞武装"],
            },
        },
        {
            "item_raw": "Bashar al-Assad",
            "aliases": {
                "ar": ["بشار الأسد"],
                "de": ["Baschar al-Assad"],
                "en": ["Bashar al-Assad"],
                "es": ["Bashar al-Ásad"],
                "fr": ["Bachar el-Assad"],
                "hi": ["बशर अल-असद"],
                "it": ["Bashar al-Assad"],
                "ja": ["バッシャール・アル＝アサド"],
                "ru": ["Башар Асад"],
                "zh": ["巴沙尔·阿萨德"],
            },
        },
        {
            "item_raw": "Mashhad",
            "aliases": {
                "ar": ["مشهد"],
                "de": ["Maschhad"],
                "en": ["Mashhad"],
                "es": ["Mashhad"],
                "fr": ["Mechhed"],
                "hi": ["मशहद"],
                "it": ["Mashhad"],
                "ja": ["マシュハド"],
                "ru": ["Мешхед"],
                "zh": ["马什哈德"],
            },
        },
        {
            "item_raw": "Hassan Nasrallah",
            "aliases": {
                "ar": ["حسن نصر الله"],
                "de": ["Hassan Nasrallah"],
                "en": ["Hassan Nasrallah"],
                "es": ["Hasan Nasralá"],
                "fr": ["Hassan Nasrallah"],
                "hi": ["हसन नसरुल्लाह"],
                "it": ["Hassan Nasrallah"],
                "ja": ["ハサン・ナスラッラー"],
                "ru": ["Хасан Насралла"],
                "zh": ["哈桑·纳斯鲁拉"],
            },
        },
        {
            "item_raw": "Abu Dhabi",
            "aliases": {
                "ar": ["أبو ظبي"],
                "de": ["Abu Dhabi"],
                "en": ["Abu Dhabi"],
                "es": ["Abu Dabi"],
                "fr": ["Abou Dhabi"],
                "hi": ["अबू धाबी"],
                "it": ["Abu Dhabi"],
                "ja": ["アブダビ"],
                "ru": ["Абу-Даби"],
                "zh": ["阿布扎比"],
            },
        },
        {
            "item_raw": "Tamim bin Hamad",
            "aliases": {
                "ar": ["تميم بن حمد"],
                "de": ["Tamim bin Hamad"],
                "en": ["Tamim bin Hamad", "Emir Tamim"],
                "es": ["Tamim bin Hamad"],
                "fr": ["Tamim ben Hamad"],
                "hi": ["तमीम बिन हमद"],
                "it": ["Tamim bin Hamad"],
                "ja": ["タミーム・ビン・ハマド"],
                "ru": ["Тамим бин Хамад"],
                "zh": ["塔米姆·本·哈马德"],
            },
        },
        {
            "item_raw": "Kuwait",
            "aliases": {
                "ar": ["الكويت"],
                "de": ["Kuwait"],
                "en": ["Kuwait", "State of Kuwait"],
                "es": ["Kuwait"],
                "fr": ["Koweït"],
                "hi": ["कुवैत"],
                "it": ["Kuwait"],
                "ja": ["クウェート"],
                "ru": ["Кувейт"],
                "zh": ["科威特"],
            },
        },
        {
            "item_raw": "Gaza",
            "aliases": {
                "ar": ["غزة"],
                "de": ["Gaza"],
                "en": ["Gaza", "Gaza Strip"],
                "es": ["Gaza"],
                "fr": ["Gaza"],
                "hi": ["गाजा"],
                "it": ["Gaza"],
                "ja": ["ガザ"],
                "ru": ["Газа"],
                "zh": ["加沙"],
            },
        },
        {
            "item_raw": "Jenin",
            "aliases": {
                "ar": ["جنين"],
                "de": ["Dschenin"],
                "en": ["Jenin"],
                "es": ["Yenín"],
                "fr": ["Jénine"],
                "hi": ["जेनिन"],
                "it": ["Jenin"],
                "ja": ["ジェニン"],
                "ru": ["Дженин"],
                "zh": ["杰宁"],
            },
        },
        {
            "item_raw": "Hebron",
            "aliases": {
                "ar": ["الخليل"],
                "de": ["Hebron"],
                "en": ["Hebron", "Al-Khalil"],
                "es": ["Hebrón"],
                "fr": ["Hébron"],
                "hi": ["हेब्रोन"],
                "it": ["Hebron"],
                "ja": ["ヘブロン"],
                "ru": ["Хеврон"],
                "zh": ["希伯伦"],
            },
        },
        {
            "item_raw": "Nablus",
            "aliases": {
                "ar": ["نابلس"],
                "de": ["Nablus"],
                "en": ["Nablus"],
                "es": ["Nablus"],
                "fr": ["Naplouse"],
                "hi": ["नाब्लस"],
                "it": ["Nablus"],
                "ja": ["ナーブルス"],
                "ru": ["Наблус"],
                "zh": ["纳布卢斯"],
            },
        },
        {
            "item_raw": "Islamic Jihad",
            "aliases": {
                "ar": ["الجهاد الإسلامي"],
                "de": ["Islamischer Dschihad"],
                "en": ["Islamic Jihad", "Palestinian Islamic Jihad"],
                "es": ["Yihad Islámica"],
                "fr": ["Jihad islamique"],
                "hi": ["इस्लामिक जिहाद"],
                "it": ["Jihad Islamica"],
                "ja": ["イスラム聖戦"],
                "ru": ["Исламский джихад"],
                "zh": ["伊斯兰圣战组织"],
            },
        },
        {
            "item_raw": "Yahya Sinwar",
            "aliases": {
                "ar": ["يحيى السنوار"],
                "de": ["Jahja al-Sinwar"],
                "en": ["Yahya Sinwar"],
                "es": ["Yahya Sinwar"],
                "fr": ["Yahya Sinouar"],
                "hi": ["यह्या सिनवार"],
                "it": ["Yahya Sinwar"],
                "ja": ["ヤヒヤ・シンワル"],
                "ru": ["Яхья Синуар"],
                "zh": ["叶海亚·辛瓦尔"],
            },
        },
        {
            "item_raw": "Fatah",
            "aliases": {
                "ar": ["فتح"],
                "de": ["Fatah"],
                "en": ["Fatah"],
                "es": ["Fatah"],
                "fr": ["Fatah"],
                "hi": ["फतह"],
                "it": ["Fatah"],
                "ja": ["ファタハ"],
                "ru": ["ФАТХ"],
                "zh": ["法塔赫"],
            },
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
            print("Converting 51 items to language-code alias format...\n")

            for item in items:
                cur.execute(
                    """
                    UPDATE taxonomy_v3
                    SET aliases = %s::jsonb,
                        updated_at = NOW()
                    WHERE item_raw = %s
                    RETURNING id
                """,
                    (json.dumps(item["aliases"]), item["item_raw"]),
                )
                result = cur.fetchone()
                if result:
                    lang_count = len(item["aliases"])
                    total_aliases = sum(len(v) for v in item["aliases"].values())
                    print(
                        f"  [FIXED] {item['item_raw']:30} -> {lang_count} languages, {total_aliases} aliases"
                    )

            conn.commit()
            print(
                f"\nSuccessfully converted {len(items)} items to language-code format!"
            )

        conn.close()
        return True

    except Exception as e:
        print(f"Conversion failed: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = fix_alias_format()
    sys.exit(0 if success else 1)
