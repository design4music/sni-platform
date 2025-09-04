# SNI — Appendices A & B (Actors + Mechanisms)

**Purpose:** This companion document holds the vocabularies that are referenced by the main Context Pack. Storage uses canonical **codes/IDs**; UI may localize display strings.

---

## Appendix A — Actor Canonicalization (Starter Sheet)

> Minimal, extensible alias list. Use canonical IDs for storage; aliases are for matching only. Grow slowly.

**Schema (CSV columns)**
```
entity_id,kind,iso_code,wikidata_qid,aliases_en,aliases_es,aliases_fr,aliases_ru,aliases_zh,domains_hint
```
- **entity_id**: our canonical key (country: ISO‑3166 alpha‑2; org/movement: short code like EU, NATO, BRICS, etc.).
- **kind**: country | org | movement | institution | region.
- **aliases_*:** semicolon‑separated; include endonyms + common exonyms; keep short.
- **domains_hint:** optional site hints that imply the actor.

**Canonical rows (initial set; extend with your 60‑actor list)**
```
US,country,US,Q30,"United States;USA;U.S.;Washington","Estados Unidos","États‑Unis","США;Соединённые Штаты","美国;美方","whitehouse.gov;state.gov"
CN,country,CN,Q148,"China;PRC;Beijing","China;RP China","Chine;RPC","Китай;КНР","中国;中华人民共和国;中方","gov.cn;xinhua.net;globaltimes.cn"
RU,country,RU,Q159,"Russia;Russian Federation;Moscow","Rusia","Russie","Россия;РФ","俄罗斯;俄方","kremlin.ru;mid.ru;rt.com"
UA,country,UA,Q212,"Ukraine;Kyiv","Ucrania","Ukraine","Украина","乌克兰","kmu.gov.ua;unian.ua"
TW,country,TW,Q865,"Taiwan;ROC;Taipei","Taiwán","Taïwan","Тайвань","台湾;台北","mofa.gov.tw"
IL,country,IL,Q801,"Israel;Jerusalem","Israel","Israël","Израиль","以色列","mfa.gov.il;timesofisrael.com"
IR,country,IR,Q794,"Iran;Tehran;Islamic Republic","Irán","Iran","Иран","伊朗","irna.ir;mehrnews.com"
TR,country,TR,Q43,"Türkiye;Turkey;Ankara","Turquía","Turquie","Турция","土耳其","tccb.gov.tr;aa.com.tr"
IN,country,IN,Q668,"India;New Delhi","India","Inde","Индия","印度","mea.gov.in;pmindia.gov.in"
JP,country,JP,Q17,"Japan;Tokyo","Japón","Japon","Япония","日本","go.jp;nhk.or.jp"
KR,country,KR,Q884,"South Korea;ROK;Seoul","Corea del Sur","Corée du Sud","Южная Корея","韩国;南韩","korea.kr;yonhapnews.co.kr"
KP,country,KP,Q423,"North Korea;DPRK;Pyongyang","Corea del Norte","Corée du Nord","КНДР;Северная Корея","朝鲜;北韩","kcna.kp"
GB,country,GB,Q145,"United Kingdom;UK;Britain;London","Reino Unido","Royaume‑Uni","Великобритания","英国","gov.uk;bbc.co.uk"
DE,country,DE,Q183,"Germany;Berlin","Alemania","Allemagne","Германия","德国","bundesregierung.de"
FR,country,FR,Q142,"France;Paris","Francia","France","Франция","法国","elysee.fr;gouvernement.fr"
IT,country,IT,Q38,"Italy;Rome","Italia","Italie","Италия","意大利","gov.it;ansa.it"
ES,country,ES,Q29,"Spain;Madrid","España","Espagne","Испания","西班牙","lamoncloa.gob.es;rtve.es"
PL,country,PL,Q36,"Poland;Warsaw","Polonia","Pologne","Польша","波兰","gov.pl"
BR,country,BR,Q155,"Brazil;Brasília","Brasil","Brésil","Бразилия","巴西","gov.br"
MX,country,MX,Q96,"Mexico;Ciudad de México","México","Mexique","Мексика","墨西哥","gob.mx"
CA,country,CA,Q16,"Canada;Ottawa","Canadá","Canada","Канада","加拿大","canada.ca"
AU,country,AU,Q408,"Australia;Canberra","Australia","Australie","Австралия","澳大利亚","pm.gov.au;abc.net.au"
SA,country,SA,Q851,"Saudi Arabia;Riyadh","Arabia Saudita","Arabie saoudite","Саудовская Аравия","沙特阿拉伯","spa.gov.sa;arabnews.com"
AE,country,AE,Q878,"UAE;United Arab Emirates;Abu Dhabi","EAU;Emiratos Árabes","Émirats arabes unis","ОАЭ","阿联酋","wam.ae;thenationalnews.com"
QA,country,QA,Q846,"Qatar;Doha","Catar","Qatar","Катар","卡塔尔","mofa.gov.qa;aljazeera.com"
EG,country,EG,Q79,"Egypt;Cairo","Egipto","Égypte","Египет","埃及","sis.gov.eg"
ZA,country,ZA,Q258,"South Africa;Pretoria","Sudáfrica","Afrique du Sud","ЮАР","南非","gov.za;news24.com"
NG,country,NG,Q1033,"Nigeria;Abuja","Nigeria","Nigéria","Нигерия","尼日利亚",""
ID,country,ID,Q252,"Indonesia;Jakarta","Indonesia","Indonésie","Индонезия","印度尼西亚",""
PK,country,PK,Q843,"Pakistan;Islamabad","Pakistán","Pakistan","Пакистан","巴基斯坦",""
BD,country,BD,Q902,"Bangladesh;Dhaka","Bangladés;Bangladesh","Bangladesh","Бангладеш","孟加拉国",""
TH,country,TH,Q869,"Thailand;Bangkok","Tailandia","Thaïlande","Таиланд","泰国",""
VN,country,VN,Q881,"Vietnam;Hanoi","Vietnam","Viêt Nam","Вьетнам","越南",""
AR,country,AR,Q414,"Argentina;Buenos Aires","Argentina","Argentine","Аргентина","阿根廷",""
CL,country,CL,Q298,"Chile;Santiago","Chile","Chili","Чили","智利",""
CO,country,CO,Q739,"Colombia;Bogotá","Colombia","Colombie","Колумбия","哥伦比亚",""
KZ,country,KZ,Q232,"Kazakhstan;Astana","Kazajistán","Kazakhstan","Казахстан","哈萨克斯坦",""
VA,country,VA,Q237,"Vatican;Holy See;Vatican City","Vaticano;Santa Sede","Vatican;Saint‑Siège","Ватикан;Святой Престол","梵蒂冈;圣座","vatican.va"
CH,country,CH,Q39,"Switzerland;Bern","Suiza","Suisse","Швейцария","瑞士","admin.ch"
SG,country,SG,Q334,"Singapore","Singapur","Singapour","Сингапур","新加坡","gov.sg"
NO,country,NO,Q20,"Norway;Oslo","Noruega","Norvège","Норвегия","挪威","regjeringen.no"
HK,region,HK,Q8646,"Hong Kong;HKSAR","Hong Kong","Hong Kong","Гонконг","香港","gov.hk"
CATALONIA,region,,Q5705,"Catalonia","Cataluña","Catalogne","Каталония","加泰罗尼亚","gencat.cat"
SCOTLAND,region,,Q22,"Scotland","Escocia","Écosse","Шотландия","苏格兰","gov.scot"
KRG,institution,,Q2037304,"Kurdish Regional Government;KRG;Kurdistan Region","Gobierno Regional del Kurdistán","Gouvernement régional du Kurdistan","Правительство Курдистана;КРГ","库尔德斯坦自治区政府","gov.krd"
MM,country,MM,Q836,"Myanmar;Burma;Naypyidaw","Myanmar;Birmania","Myanmar;Birmanie","Мьянма","缅甸",""
BY,country,BY,Q184,"Belarus;Minsk","Bielorrusia;Belarús","Biélorussie;Bélarus","Беларусь","白俄罗斯;白俄",""
VE,country,VE,Q717,"Venezuela;Caracas","Venezuela","Venezuela","Венесуэла","委内瑞拉",""
CU,country,CU,Q241,"Cuba;Havana","Cuba","Cuba","Куба","古巴",""
EU,org,,Q458,"EU;European Union;Brussels","UE;Unión Europea","UE;Union européenne","ЕС;Евросоюз","欧盟","europa.eu;consilium.europa.eu"
NATO,org,,Q7184,"NATO;Alliance","OTAN","OTAN","НАТО","北约","nato.int"
UN,org,,Q1065,"UN;United Nations","ONU","ONU","ООН","联合国","un.org"
BRICS,org,,Q19724459,"BRICS","BRICS","BRICS","БРИКС","金砖国家","brics2024.gov.za"
SCO,org,,Q133255,"SCO;Shanghai Cooperation Organisation","OCS","OCS","ШОС","上合组织","sectsco.org"
ASEAN,org,,Q476033,"ASEAN","ASEAN","ASEAN","АСЕАН","东盟","asean.org"
G20,org,,Q166864,"G20","G20","G20","G20","二十国集团","g20.org"
G7,org,,Q170481,"G7","G7","G7","G7","七国集团","g7hiroshima.go.jp"
IMF,org,,Q188354,"IMF;Fund","FMI","FMI","МВФ","国际货币基金组织","imf.org"
WB,org,,Q7164,"World Bank","Banco Mundial","Banque mondiale","Всемирный банк","世界银行","worldbank.org"
WHO,org,,Q7817,"WHO;World Health Organization","OMS","OMS","ВОЗ","世界卫生组织","who.int"
GCC,org,,Q80985,"GCC;Gulf Cooperation Council","CCG","CCG","СCC;ССАГПЗ","海合会","gcc-sg.org"
OPEC,org,,Q703173,"OPEC","OPEP","OPEP","ОПЕК","欧佩克","opec.org"
AFRICAN_UNION,org,,Q7159,"African Union;AU","Unión Africana","Union africaine","Африканский союз","非洲联盟","au.int"
ARAB_LEAGUE,org,,Q7172,"Arab League","Liga Árabe","Ligue arabe","Лига арабских государств","阿拉伯国家联盟","lasportal.org"
MERCOSUR,org,,Q4264,"MERCOSUR;Southern Common Market","MERCOSUR;Mercado Común del Sur","MERCOSUR;Marché commun du Sud","МЕРКОСУР","南方共同市场","mercosur.int"
EAEU,org,,Q4173083,"Eurasian Economic Union;EAEU","Unión Económica Euroasiática","Union économique eurasiatique","Евразийский экономический союз;ЕАЭС","欧亚经济联盟","eaeunion.org"
PACIFIC_ALLIANCE,org,,Q7122288,"Pacific Alliance","Alianza del Pacífico","Alliance du Pacifique","Тихоокеанский альянс","太平洋联盟","alianzapacifico.net"
HAMAS,movement,,Q193388,"Hamas","Hamás","Hamas","Хамас","哈马斯","hamas.ps"
HEZBOLLAH,movement,,Q1048,"Hezbollah;Hizbullah","Hezbolá","Hezbollah","Хезболла","真主党","almanar.com.lb"
TALIBAN,movement,,Q131136,"Taliban","Talibán","Taliban","Талибан","塔利班","alemarahenglish.af"
```
> Add your full 60‑actor list and keep aliases concise; avoid long variant dumps.

---

## Appendix B — Mechanism Taxonomy v1.0 (Frozen; classification by anchors)

> Labels are **English codes**. We classify titles by semantic similarity to **anchor phrases** (2–3 per label). UI can localize names later; storage keeps codes.

**Schema**
```
code,label,guarded,anchors_en,scope_note
```
- **guarded = yes** → enforce issuer→instrument→target uniformity in buckets (never mix pairs).

### MVP Core‑20 (in use now)
```
sanctions,Sanctions,yes,"imposes sanctions;blacklists entity;announces sanctions",State sanctions on states/orgs/people
export_controls,Export controls,yes,"restricts chip exports;imposes export curbs;licensing requirements",Limits on tech/dual‑use trade
strike_airstrike,Air/missile strike,yes,"airstrikes hit;missile barrage;precision strike",Kinetic strike from air/missile
ground_incursion,Ground incursion,no,"cross‑border incursion;ground offensive;pushes into",Cross‑border/territorial push
missile_test,Missile/rocket test,no,"test‑fires missile;launches rocket;ballistic test",Demonstrative launches/tests
ceasefire_talks,Ceasefire talks,no,"truce talks;mediated ceasefire;ceasefire negotiations",Talks aimed at halting hostilities
peace_process,Peace process,no,"peace talks;framework agreement;roadmap",Longer‑horizon settlement tracks
summit_meeting,Summit/meeting,no,"leaders meet;summit convenes;bilateral talks",Leader or minister‑level meets
diplomatic_statement,Diplomatic statement,no,"warns;condemns;urges",Official statements/notes
aid_package,Aid package (mil/hum),no,"announces aid package;military assistance;humanitarian aid",Financial/material assistance
arms_transfer,Arms transfer/sale,no,"approves arms sale;delivers weapons;defense package",Defense equipment transfers
defense_deal,Defense cooperation,no,"defense pact;security agreement;base access",Formal defense agreements
regulation_policy,Regulation/policy,no,"passes bill;issues regulation;approves law",Domestic policy change
court_ruling,Court ruling,no,"court blocks;judge rules;strikes down",Judicial decisions
election,Election,no,"wins election;runoff scheduled;votes counted",Electoral events
protest_unrest,Protest/unrest,no,"protests erupt;mass demonstrations;clashes",Collective action/riots
platform_ban,Platform ban,yes,"bans X nationwide;platform suspended;blocked",Nationwide or state‑level platform blocking
cyber_operation,Cyber operation,no,"hacking campaign;cyberattack;intrusion",Offensive/defensive cyber activity
energy_supply,Energy supply/no‑supply,no,"pipeline halted;cuts gas;power shortage",Energy flow decisions
trade_agreement,Trade deal,no,"signs trade agreement;FTA;tariff‑free",International trade pacts
```

### Extended set (parked; not used for MVP classification)
```
asset_freeze,Asset freeze,yes,"freezes assets;seizes funds;blocks property",Financial blocking measures
travel_ban,Travel/visa ban,yes,"visa restrictions;travel ban;entry barred",Mobility restrictions on persons/entities
border_security,Border deployment,no,"deploys troops to border;border reinforcement",Security posture at border
recognition,Recognition/no‑recognition,no,"recognizes government;recognizes state;withdraws recognition",Diplomatic recognition disputes
referendum,Referendum,no,"holds referendum;votes on;plebiscite",Popular vote on specific question
coup_attempt,Coup/putsch,no,"coup attempt;military seizes;overthrows",Regime change attempts
censorship_law,Censorship/speech law,no,"criminalizes speech;online harms bill;content regulation",Legal speech restrictions
data_breach,Data breach/leak,no,"data leak;breach exposes;hacker publishes",Non‑state or corporate data incidents
pipeline_disruption,Pipeline/infra disruption,no,"pipeline explosion;dam sabotage;grid outage",Infrastructure shocks
tariff_duties,Tariff/duties,no,"raises tariffs;imposes duties;retaliatory tariffs",Trade taxes
space_launch,Space launch/test,no,"launches satellite;spacecraft liftoff;orbital test",Space activity
natural_disaster,Natural disaster,no,"earthquake;flooding;wildfire spreads",Non‑manmade disasters
public_health,Public health emergency,no,"declares health emergency;outbreak;WHO alert",Epidemic/pandemic alerts
market_controls,Market/price controls,no,"price cap;export ban on food;quota",Domestic/intl market management
```

**Classification rule of thumb:** compute embedding similarity from `title_norm` to each label’s anchor centroid; choose max above threshold; below threshold → `unspecified`.

