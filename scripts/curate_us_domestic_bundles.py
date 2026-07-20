"""Emit curated fn_anchor bundles for the us_domestic_theater atomics.

Curation of the Deepseek drafts in out/extraction/. Every atomic here sits on a
bare {AMERICAS-USA} participant gate with primary_target=AMERICAS-USA, so per
FN_THEATER_BUILD_SPEC §2 alias purity is the ONLY precision lever -- aliases are
OR'd, and a single generic verb admits the whole US feed. The drafts arrived with
the usual four failure modes and all four are corrected below:

  1. Phrase variants (vocab rule 3). Epstein came back with 20 of them
     ("Epstein files/probe/case/panel/hearing/..."); the EN matcher is word-START
     prefix so bare `Epstein` already catches every one.
  2. Stance vocabulary (vocab rule 5). `rigged`, `election denial`,
     `voter suppression`, `election subversion` are framing_keywords, not topic
     gate.
  3. Cross-atomic collisions. `redistricting`/`voting rights` were in the
     judicial draft (they are electoral); `deportation`/`asylum` too (immigration);
     `Secret Service` was in the loyalty draft (it is political violence);
     bare `Supreme Court` was in the fed AND violence drafts.
  4. Third-party leaders (vocab rule 4). The loyalty draft contained `Trump`
     outright, which on a USA gate matches nearly the entire corpus.

Measured collisions encoded here (do not re-derive):
  Warsh   c warship        Bondi c Bondi Beach      Supreme Court -> IN/KR/NG/EE/AU
  Hegseth -> Iran war      special counsel -> Yoon  militia -> 3 USA-only of 69
  assassination -> Khamenei/Kirk/Obi              FCC -> SpaceX/Amazon/Charter
  Maxwell c Maxwell House                         impeach -> 129 USA-only of 509

Matcher semantics that drove choices (bootstrap_friction_node.py):
  EN, all-caps <=4 chars  -> case-SENSITIVE whole word  (ICE, DHS, TPS, GOP, FOMC)
  EN, everything else     -> case-insensitive word-START prefix, NO trailing \\M
  non-EN                  -> pure substring, no boundary protection at all

Run: python scripts/curate_us_domestic_bundles.py
Writes out/extraction/<fn_id>__curated.json for each atomic.
"""

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "out" / "extraction"
LANGS = ["ar", "de", "en", "es", "fr", "hi", "it", "ja", "ru", "zh"]


def term(name, **langs):
    aliases = {k: [] for k in LANGS}
    for k, v in langs.items():
        aliases[k] = v
    return {"term": name, "type": "entity", "aliases": aliases}


BUNDLES = {
    # -----------------------------------------------------------------------
    # A2 anchor == subject. `Epstein` is ~100% specific and already matched
    # 3,105 titles; it needs no domain verbs at all. Dropped every phrase
    # variant, plus `human trafficking`/`sex trafficking` (generic, would pull
    # unrelated trafficking coverage) and bare `Maxwell` (c Maxwell House;
    # `Ghislaine` is the unique form).
    # -----------------------------------------------------------------------
    "us_epstein_elite_network": [
        term(
            "Epstein",
            en=["Epstein"],
            ar=["إبستين"],
            hi=["एपस्टीन"],
            ja=["エプスタイン"],
            ru=["Эпштейн"],
            zh=["爱泼斯坦"],
        ),
        term(
            "Ghislaine Maxwell",
            en=["Ghislaine"],
            ar=["غيسلين ماكسويل"],
            hi=["गिस्लेन मैक्सवेल"],
            ja=["ギレーヌ・マクスウェル"],
            ru=["Гислейн Максвелл"],
            zh=["吉丝莲"],
        ),
        term("Giuffre", en=["Giuffre"], ru=["Джуффре"], zh=["朱弗雷"]),
        term("Wexner", en=["Wexner"], ru=["Векснер"]),
        term("Leon Black", en=["Leon Black"]),
        term("Mandelson", en=["Mandelson"], ru=["Мандельсон"]),
        term("Zorro Ranch", en=["Zorro Ranch", "Little St. James"]),
    ],
    # -----------------------------------------------------------------------
    # Interior enforcement ONLY. `border` deliberately absent -- that is
    # mexico_theater's terrain and the whole point of the re-scope. Dropped the
    # generic single words the draft proposed (arrest, raid, visa, migrant,
    # asylum, appeal) which on a country gate admit everything; kept named
    # agencies, named facilities and fixed target-nouns (spec §3 KEEP list).
    # ICE/DHS/TPS take the case-sensitive acronym path and are safe.
    # -----------------------------------------------------------------------
    "us_interior_immigration_enforcement": [
        term(
            "ICE",
            en=["ICE"],
            de=["ICE-Gewahrsam", "Einwanderungsbehörde"],
            es=["el ICE"],
            ar=["إدارة الهجرة والجمارك"],
            zh=["移民及海关执法局"],
            ja=["移民税関捜査局"],
            hi=["आईसीई"],
        ),
        term("DHS", en=["DHS", "Homeland Security"], de=["Heimatschutzministerium"]),
        term(
            "deportation",
            en=["deport"],
            de=["Abschiebung", "abgeschoben"],
            es=["deportación", "deportado"],
            fr=["expulsion"],
            it=["deportazione"],
            ar=["ترحيل"],
            hi=["निर्वासन"],
            ja=["強制送還"],
            ru=["депортация"],
            zh=["驱逐出境"],
        ),
        term(
            "immigration detention",
            en=[
                "immigration detention",
                "detention center",
                "detention centre",
                "detainee",
            ],
            de=["Haftanstalt", "Abschiebehaft"],
            es=["centro de detención"],
            fr=["centre de rétention"],
            ar=["مركز احتجاز"],
            ja=["収容施設"],
            ru=["центр содержания"],
            zh=["拘留中心"],
            hi=["हिरासत केंद्र"],
        ),
        term("expedited removal", en=["expedited removal", "removal flight"]),
        term("TPS", en=["TPS", "Temporary Protected Status"]),
        term(
            "sanctuary city",
            en=["sanctuary city", "sanctuary state"],
            de=["Zufluchtsstadt"],
            es=["ciudad santuario"],
        ),
        term("Alligator Alcatraz", en=["Alligator Alcatraz"]),
        term("border czar", en=["border czar"]),
    ],
    # -----------------------------------------------------------------------
    # Dropped the stance pillar (rigged, election denial, election subversion,
    # voter suppression) -> those are narratives_v2.framing_keywords. Added
    # `midterm`, which the draft missed entirely despite being the single
    # largest probe in this atomic (366 titles).
    # -----------------------------------------------------------------------
    "us_electoral_legitimacy": [
        term(
            "midterm",
            en=["midterm"],
            de=["Zwischenwahl"],
            es=["elecciones de mitad de mandato"],
            fr=["élections de mi-mandat"],
            it=["elezioni di midterm"],
            ar=["انتخابات التجديد النصفي"],
            hi=["मध्यावधि चुनाव"],
            ja=["中間選挙"],
            ru=["промежуточные выборы"],
            zh=["中期选举"],
        ),
        term(
            "redistricting",
            en=["redistricting", "congressional map", "voting map"],
            de=["Wahlbezirk", "Neuzuschnitt"],
            es=["redistribución de distritos"],
            fr=["redécoupage"],
            it=["ridefinizione dei collegi"],
            ja=["選挙区割り"],
            ru=["перекройка округов"],
            zh=["选区重划"],
            ar=["إعادة تقسيم الدوائر"],
            hi=["परिसीमन"],
        ),
        term("gerrymander", en=["gerrymander"]),
        term(
            "ballot",
            en=["ballot", "mail-in", "absentee"],
            de=["Briefwahl", "Stimmzettel"],
            es=["voto por correo", "papeleta"],
            fr=["vote par correspondance"],
            it=["voto per corrispondenza"],
            ar=["الاقتراع"],
            hi=["मतपत्र"],
            ja=["郵便投票"],
            ru=["бюллетень"],
            zh=["邮寄选票"],
        ),
        term(
            "voter ID",
            en=[
                "voter ID",
                "voter roll",
                "voter purge",
                "proof of citizenship",
                "citizenship requirement",
                "voter intimidation",
            ],
            de=["Wählerverzeichnis", "Wählerausweis"],
            es=["padrón electoral"],
            ru=["списки избирателей"],
            zh=["选民身份"],
        ),
        term("Voting Rights Act", en=["Voting Rights Act", "voting rights"]),
        term(
            "election fraud",
            en=[
                "election fraud",
                "election integrity",
                "election security",
                "election interference",
                "voting machine",
                "poll watcher",
            ],
            de=["Wahlbetrug", "Wahlintegrität"],
            es=["fraude electoral"],
            fr=["fraude électorale"],
            it=["frode elettorale"],
            ar=["تزوير الانتخابات"],
            hi=["चुनावी धोखाधड़ी"],
            ja=["選挙不正"],
            ru=["фальсификация выборов"],
            zh=["选举舞弊"],
        ),
        term(
            "primary election", en=["primary election", "electoral college", "turnout"]
        ),
    ],
    # -----------------------------------------------------------------------
    # Dropped the entire culture-war docket pillar the draft proposed (LGBT,
    # abortion, transgender, gun rights, Second Amendment, age verification,
    # campaign finance) -- that re-imports the retired us_culture_wars through
    # the back door. This atomic is the executive-vs-judiciary CONFLICT, not the
    # subject matter of the docket. Also dropped bare `Supreme Court` (1,798-title
    # firehose -> India/Korea/Nigeria/Estonia/Australia) and the generics
    # (block, defy, appeal, ruling, justice, uphold, contempt, pardon, sources).
    # Added the named justices, which are precise and were missing.
    # -----------------------------------------------------------------------
    "us_judicial_constraint": [
        # Bare `Supreme Court` measured 1,559 titles on the USA gate but ~20%
        # foreign -- Indian outlets alone are 244 (Hindu 104 / ToI 43 / Indian
        # Express 37 / NDTV 34 / HT 26), plus Daily Nation and Times of Israel.
        # A country-name regex said only 5% foreign, which was WRONG: those
        # headlines never name the country ("Walking On Demarcated Footpaths A
        # Fundamental Right: Supreme Court"). Publisher breakdown is the honest
        # test. So the bare form stays out and the Arctic compound-phrase escape
        # is used instead: US headline style is "Supreme Court rules/blocks/
        # upholds", Indian style is "Supreme Court: ..." or "...: Supreme Court".
        # Measured: 372 titles at ~9% foreign. Order rule makes these literal,
        # which is exactly why they discriminate.
        term(
            "SCOTUS",
            en=[
                "SCOTUS",
                "US Supreme Court",
                "U.S. Supreme Court",
                "Supreme Court justice",
                "chief justice",
                "Supreme Court rules",
                "Supreme Court ruling",
                "Supreme Court blocks",
                "Supreme Court upholds",
                "Supreme Court allows",
                "Supreme Court rejects",
                "Supreme Court denies",
                "Supreme Court strikes",
                "Supreme Court clears",
                "Supreme Court sides",
                "Supreme Court hears",
                "Supreme Court weighs",
                "Supreme Court backs",
                "Supreme Court lets",
                "Supreme Court tosses",
                "Supreme Court expands",
                "Supreme Court restores",
            ],
            de=["US-Supreme-Court", "Oberster Gerichtshof der USA"],
            es=["Tribunal Supremo de EE"],
            fr=["Cour suprême des États-Unis"],
            ar=["المحكمة العليا الأمريكية"],
            hi=["अमेरिकी सुप्रीम कोर्ट"],
            ja=["米連邦最高裁"],
            ru=["Верховный суд США"],
            zh=["美国最高法院"],
        ),
        term(
            "birthright citizenship",
            en=["birthright citizenship"],
            de=["Staatsbürgerschaftsrecht", "Geburtsortsprinzip"],
            es=["ciudadanía por nacimiento"],
            fr=["droit du sol"],
            it=["cittadinanza per nascita"],
            ar=["الجنسية بالولادة"],
            hi=["जन्मसिद्ध नागरिकता"],
            ja=["出生地主義"],
            ru=["гражданство по рождению"],
            zh=["出生公民权"],
        ),
        term(
            "federal judge",
            en=["federal judge", "appeals court", "district judge"],
            de=["Bundesrichter", "Berufungsgericht"],
            es=["juez federal"],
            fr=["juge fédéral"],
            it=["giudice federale"],
            ru=["федеральный судья"],
            zh=["联邦法官"],
            ja=["連邦判事"],
            ar=["قاض فيدرالي"],
            hi=["संघीय न्यायाधीश"],
        ),
        term(
            "injunction",
            en=["injunction", "shadow docket", "stay of the ruling"],
            de=["einstweilige Verfügung"],
            es=["medida cautelar"],
            fr=["injonction"],
            it=["ingiunzione"],
            ru=["судебный запрет"],
            zh=["禁令"],
        ),
        term(
            "separation of powers",
            en=[
                "separation of powers",
                "judicial independence",
                "judicial review",
                "unconstitutional",
                "presidential power",
                "executive power",
            ],
            de=["Gewaltenteilung", "verfassungswidrig", "Unabhängigkeit der Justiz"],
            es=["separación de poderes", "inconstitucional"],
            fr=["séparation des pouvoirs", "inconstitutionnel"],
            it=["separazione dei poteri", "incostituzionale"],
            ar=["فصل السلطات"],
            hi=["शक्तियों का पृथक्करण"],
            ja=["三権分立"],
            ru=["разделение властей"],
            zh=["三权分立", "违宪"],
        ),
        term(
            "executive order",
            en=["executive order"],
            de=["Dekret", "Verfügung"],
            es=["orden ejecutiva"],
            fr=["décret présidentiel"],
            it=["ordine esecutivo"],
            ar=["أمر تنفيذي"],
            hi=["कार्यकारी आदेश"],
            ja=["大統領令"],
            ru=["указ президента"],
            zh=["行政命令"],
        ),
        term(
            "justices",
            en=[
                "Clarence Thomas",
                "Coney Barrett",
                "Sotomayor",
                "Kavanaugh",
                "Gorsuch",
                "Ketanji",
                "Neil Gorsuch",
            ],
        ),
    ],
    # -----------------------------------------------------------------------
    # Dropped `Trump` (vocab rule 4 -- and on a USA gate it matches nearly
    # everything), `Hegseth`/`Pentagon`/`Stars and Stripes` (resolve to the Iran
    # war), `Secret Service` (belongs to us_political_violence), bare `FBI` (812
    # titles, mostly ordinary crime), `MAGA` (movement label), and the generic
    # personnel verbs (fired, sacked, ousted, removed, resign, nomination,
    # nominee, confirmation, cabinet, director, secretary, general, loyalty).
    # Named officials carry this atomic. `Pam Bondi` never bare `Bondi`.
    # -----------------------------------------------------------------------
    "us_executive_loyalty": [
        term(
            "Pam Bondi",
            en=["Pam Bondi"],
            ru=["Пэм Бонди"],
            zh=["帕姆·邦迪"],
            ja=["パム・ボンディ"],
            ar=["بام بوندي"],
        ),
        term("Kristi Noem", en=["Noem"], ru=["Ноэм"], zh=["诺姆"]),
        term(
            "Tulsi Gabbard",
            en=["Gabbard"],
            ru=["Габбард"],
            zh=["加巴德"],
            ja=["ギャバード"],
            ar=["غابارد"],
        ),
        term("Kash Patel", en=["Kash Patel"], ru=["Кэш Пател"], zh=["卡什·帕特尔"]),
        term("Todd Blanche", en=["Todd Blanche"]),
        term("Jay Clayton", en=["Jay Clayton"]),
        term(
            "attorney general",
            en=["attorney general"],
            de=["Justizministerin", "Justizminister", "Generalstaatsanwalt"],
            es=["fiscal general"],
            fr=["procureur général"],
            it=["procuratore generale"],
            ar=["المدعي العام"],
            hi=["अटॉर्नी जनरल"],
            ja=["司法長官"],
            ru=["генеральный прокурор"],
            zh=["司法部长"],
        ),
        term(
            "inspector general",
            en=["inspector general", "watchdog fired"],
            de=["Generalinspekteur"],
        ),
        term(
            "FBI director",
            en=["FBI director"],
            de=["FBI-Direktor"],
            es=["director del FBI"],
            ru=["директор ФБР"],
            zh=["联邦调查局局长"],
        ),
        term(
            "intelligence chief",
            en=["intelligence chief", "national intelligence"],
            de=["Geheimdienstchefin", "Geheimdienstchef"],
            es=["jefa de inteligencia"],
            ru=["глава разведки"],
            zh=["情报总监"],
        ),
        term(
            "cabinet shakeup",
            en=["cabinet shakeup", "cabinet reshuffle"],
            de=["Kabinettsumbildung"],
            es=["remodelación del gabinete"],
        ),
    ],
    # -----------------------------------------------------------------------
    # Dropped the ordinary-crime pillar the draft proposed (mass shooting,
    # school shooting, shooting, gun law, Second Amendment, death penalty,
    # hate crime, hate, vandalism, arrest, conviction, prosecutor, judge,
    # lawsuit, indictment) -- that is the Louisiana / Bondi Beach noise, not
    # political violence. Dropped bare `assassination` (-> Khamenei, Charlie
    # Kirk, Peter Obi) in favour of the compound forms, and bare `Supreme Court`.
    # -----------------------------------------------------------------------
    "us_political_violence": [
        term(
            "Secret Service",
            en=["Secret Service"],
            es=["Servicio Secreto"],
            ar=["الخدمة السرية"],
            hi=["सीक्रेट सर्विस"],
            ja=["シークレットサービス"],
            ru=["Секретная служба"],
            zh=["特勤局"],
        ),
        term(
            "assassination attempt",
            en=[
                "assassination attempt",
                "assassination plot",
                "attempted assassination",
            ],
            de=["Attentat", "Attentatsversuch"],
            es=["intento de asesinato", "atentado"],
            fr=["tentative d'assassinat"],
            it=["tentato omicidio", "attentato"],
            ar=["محاولة اغتيال"],
            hi=["हत्या का प्रयास"],
            ja=["暗殺未遂"],
            ru=["покушение"],
            zh=["暗杀未遂"],
        ),
        term(
            "political violence",
            en=["political violence", "politically motivated"],
            de=["politische Gewalt"],
            es=["violencia política"],
            fr=["violence politique"],
            it=["violenza politica"],
            ar=["العنف السياسي"],
            hi=["राजनीतिक हिंसा"],
            ja=["政治的暴力"],
            ru=["политическое насилие"],
            zh=["政治暴力"],
        ),
        term("Correspondents Dinner", en=["Correspondents"]),
        term("Cole Allen", en=["Cole Allen"]),
        term(
            "extremist plot",
            en=["extremist", "foiled plot", "sniper"],
            de=["Extremist"],
            es=["extremista"],
            ru=["экстремист"],
        ),
    ],
    # -----------------------------------------------------------------------
    # Dropped bare `FCC` (SpaceX/Amazon/Charter spectrum business dominates it)
    # and `Pentagon` (Iran war). Anchored on the regulator's ACTION, the
    # constitutional claim and the named cases. `Kimmel` was missing from the
    # draft despite being the largest cluster in this atomic.
    # -----------------------------------------------------------------------
    "us_press_freedom": [
        term("Kimmel", en=["Kimmel"], ru=["Киммел"], zh=["基梅尔"], ja=["キンメル"]),
        term(
            "broadcast licence",
            en=[
                "broadcast license",
                "broadcast licence",
                "license review",
                "FCC chair",
                "FCC orders",
                "FCC opens",
            ],
            de=["Sendelizenz", "Rundfunklizenz"],
            es=["licencia de emisión"],
            fr=["licence de diffusion"],
            it=["licenza di trasmissione"],
            ar=["رخصة البث"],
            ja=["放送免許"],
            ru=["вещательная лицензия"],
            zh=["广播执照"],
        ),
        term(
            "press freedom",
            en=["press freedom", "freedom of the press"],
            de=["Pressefreiheit"],
            es=["libertad de prensa"],
            fr=["liberté de la presse"],
            it=["libertà di stampa"],
            ar=["حرية الصحافة"],
            hi=["प्रेस की स्वतंत्रता"],
            ja=["報道の自由"],
            ru=["свобода прессы"],
            zh=["新闻自由"],
        ),
        term(
            "First Amendment",
            en=["First Amendment"],
            de=["Erster Verfassungszusatz"],
            es=["Primera Enmienda"],
            fr=["Premier Amendement"],
            it=["Primo Emendamento"],
            ru=["Первая поправка"],
            zh=["第一修正案"],
        ),
        term(
            "censorship",
            en=["censorship", "editorial independence"],
            de=["Zensur"],
            es=["censura"],
            fr=["censure"],
            it=["censura"],
            ar=["الرقابة"],
            hi=["सेंसरशिप"],
            ja=["検閲"],
            ru=["цензура"],
            zh=["审查"],
        ),
        term(
            "public broadcasting",
            en=["NPR", "PBS", "public broadcasting"],
            de=["öffentlich-rechtlicher Rundfunk"],
        ),
        term("Comey", en=["Comey"], ru=["Коми"], zh=["科米"]),
        term("CPJ", en=["CPJ", "Committee to Protect Journalists"]),
    ],
}


def main():
    for fn_id, bundle in BUNDLES.items():
        payload = {
            "metadata": {
                "fn_id": fn_id,
                "centroid": "AMERICAS-USA",
                "curated": "2026-07-19",
                "source": "curated from Deepseek draft; see module docstring",
            },
            "bundle": bundle,
        }
        path = OUT / f"{fn_id}__curated.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        n = sum(len(v) for t in bundle for v in t["aliases"].values())
        print(f"OK {fn_id}: {len(bundle)} terms, {n} aliases -> {path.name}")


if __name__ == "__main__":
    main()
