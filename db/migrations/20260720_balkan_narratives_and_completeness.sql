-- Balkan theater: narratives (atomic + theater roll-up) and bilingual
-- completeness fields. 2026-07-20. LOCAL first.
--
-- Coalition design notes:
--   * serbia_government_legitimacy: two disjoint publisher coalitions
--     (Russian/Chinese state press vs independent regional + Western
--     mainstream) -- no shared-publisher risk, framing_required=false.
--   * balkan_foreign_capital: the SAME wire pool (Reuters, Euronews,
--     Bloomberg, eKathimerini, Albanian Daily News...) carries both PM
--     Rama's own defense of the resort deal ("vows to push on", "hybrid
--     war") and the protest/environmental critique -- publisher alone
--     cannot disambiguate, so both narratives use framing_required=true
--     (spec sec 5 mechanism, same shape as Ukraine's corruption own-goal
--     split, but here the split is on WHOSE quote a wire outlet is
--     carrying, not on a normally-supportive camp turning critic).
--   * No rift-exploitation card on foreign_capital: RT/Press TV coverage
--     (2 titles total) is plain wire reporting of the protests, not a
--     distinct anti-Western framing -- folds into the rejection narrative.
--   * Theater roll-up (sec 5.5): positive bucket splits into two disjoint
--     cards (Russian/Chinese-state vs Western-wire, real publisher
--     disjointness, verified). Negative bucket is ONE card, not two --
--     Serbia-protest and Albania-resort critical coverage share ~9
--     generalist wire publishers (Guardian, Reuters, Bloomberg, Euronews,
--     Al Jazeera...), so two separate -2 cards would double-count; merged
--     into a single cross-cutting "elite capture" card instead.

BEGIN;

-- ============ Atomic: serbia_government_legitimacy ============

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required, display_order
) VALUES
(
    'serbia_sovereignty_defense', 'serbia_government_legitimacy',
    'Belgrade''s resistance to Western pressure defends Serbia''s sovereign right to choose its own path',
    'Belgrads Widerstand gegen westlichen Druck verteidigt Serbiens souveränes Recht auf einen eigenen Kurs',
    'This framing, carried by Russian and Chinese state media, holds that Vucic''s refusal to sanction Russia, his defense of NIS against forced divestment, and his balancing between Brussels, Moscow and Beijing reflect a legitimate multi-vector foreign policy rather than defiance. Domestic protests are read as encouraged or exploited by outside actors seeking to force Serbia into an alignment it has not chosen, and continuity in Belgrade is presented as the safer course for the country''s energy security and independence.',
    'Diese von russischen und chinesischen Staatsmedien getragene Deutung sieht in Vucics Weigerung, Russland zu sanktionieren, seiner Verteidigung von NIS gegen eine erzwungene Veraeusserung und seinem Balancieren zwischen Bruessel, Moskau und Peking eine legitime multivektorale Aussenpolitik und keinen Trotz. Die innenpolitischen Proteste werden als von aussen ermutigt oder ausgenutzt gedeutet, mit dem Ziel, Serbien zu einer nicht gewaehlten Ausrichtung zu zwingen; Kontinuitaet in Belgrad gilt in dieser Lesart als der sicherere Kurs fuer Energiesicherheit und Unabhaengigkeit des Landes.',
    1, 'Sovereignty defense', 'Verteidigung der Souveraenitaet',
    ARRAY['EUROPE-BALKANS','EUROPE-RUSSIA','ASIA-CHINA'],
    ARRAY['TASS','TASS (EN)','RT','Lenta.ru','Gazeta.ru','Kommersant','Izvestia','RIA Novosti','CGTN','China Daily'],
    ARRAY['sovereign','sovereignty','won''t bow','resist pressure','independent course','multi-vector','national interest','energy security','refuses to sanction','wird keine Sanktionen','суверенит','энергетическая безопасность','не введет санкции'],
    false, 1
),
(
    'serbia_protest_accountability', 'serbia_government_legitimacy',
    'Systemic corruption and negligence behind the Novi Sad canopy collapse demand Vucic''s resignation',
    'Systemische Korruption und Fahrlaessigkeit hinter dem Einsturz des Vordachs von Novi Sad verlangen den Ruecktritt Vucics',
    'Carried by Serbia''s independent outlets and Western mainstream press, this framing holds that the fatal collapse of a renovated railway station canopy in Novi Sad exposed years of corrupt, unaccountable construction contracting under SNS rule. Student-led protests demanding justice, snap elections and Vucic''s resignation have met police crackdowns and pressure on public employees, read as further evidence of a government defending itself rather than reforming.',
    'Diese von unabhaengigen serbischen Medien und der westlichen Mainstream-Presse getragene Deutung sieht im toedlichen Einsturz eines renovierten Bahnhofsvordachs in Novi Sad den Beweis jahrelanger korrupter, unkontrollierter Bauvergabe unter der SNS-Herrschaft. Die von Studierenden angefuehrten Proteste, die Gerechtigkeit, vorgezogene Neuwahlen und Vucics Ruecktritt fordern, wurden mit Polizeieinsaetzen und Druck auf oeffentlich Bedienstete beantwortet -- fuer diese Lesart ein weiterer Beleg dafuer, dass sich die Regierung verteidigt, statt zu reformieren.',
    -2, 'Accountability protests', 'Rechenschaftsproteste',
    ARRAY['EUROPE-BALKANS','NON-STATE-EU'],
    ARRAY['N1 Serbia','Vijesti','N1','Reuters','The Guardian','Der Spiegel','Die Zeit','Der Standard','Tagesschau','Bloomberg','Al Jazeera','Euronews','Kurier','Novinite','Jerusalem Post','Daily Sabah','CNN'],
    ARRAY['resign','resignation','snap election','accountability','cover-up','negligence','crackdown','tear gas','corruption','impunity','Ruecktritt','Neuwahlen','ostavk','odgovornost','protest','prosvjed','demonstrac','student','izbor','blokad','blockade','nadstrešnic','canopy','Novi Sad'],
    true, 2
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
    stance = EXCLUDED.stance, stance_label_en = EXCLUDED.stance_label_en, stance_label_de = EXCLUDED.stance_label_de,
    actor_centroids = EXCLUDED.actor_centroids, publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords, framing_required = EXCLUDED.framing_required,
    display_order = EXCLUDED.display_order, updated_at = NOW();

-- ============ Atomic: balkan_foreign_capital ============

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required, display_order
) VALUES
(
    'balkan_investment_development', 'balkan_foreign_capital',
    'Foreign investment brings jobs, tourism and international partnership to the Western Balkans',
    'Auslandsinvestitionen bringen Arbeitsplaetze, Tourismus und internationale Partnerschaften auf den Westbalkan',
    'In this framing, carried by the same international wire outlets that report the controversy plus regional business press, foreign capital projects such as the Kushner-backed Sazan resort and Fincantieri''s shipbuilding partnership with Albania represent legitimate economic development that governments defend against what they characterize as politically motivated obstruction. Prime Minister Rama has publicly defended the resort project and framed opposition to it as external interference, insisting investment will proceed.',
    'In dieser von denselben internationalen Nachrichtenagenturen, die auch ueber die Kontroverse berichten, sowie von der regionalen Wirtschaftspresse getragenen Deutung stellen auslaendische Kapitalprojekte wie das von Kushner unterstuetzte Sazan-Resort und die Schiffbau-Partnerschaft von Fincantieri mit Albanien eine legitime wirtschaftliche Entwicklung dar, die Regierungen gegen das verteidigen, was sie als politisch motivierte Blockade bezeichnen. Ministerpraesident Rama hat das Resortprojekt oeffentlich verteidigt und den Widerstand dagegen als aeussere Einmischung eingeordnet und auf einer Fortsetzung der Investition bestanden.',
    1, 'Investment as opportunity', 'Investition als Chance',
    ARRAY['EUROPE-BALKANS','AMERICAS-USA','EUROPE-SOUTH'],
    ARRAY['Reuters','Bloomberg','Euronews','eKathimerini','ANSA','Albanian Daily News','EurActiv','Associated Press','BBC World','CNN','Deutsche Welle','Financial Times','France 24 (EN)','NPR','Sky News','Corriere della Sera','Der Spiegel','Die Zeit','Al Jazeera','The Guardian','Al-Ahram','El Mundo','Folha de S.Paulo','Haaretz','Helsinki Times','La Nación','MSNBC','News24','Novinite','The Australian','The Hindu','Times of Israel','WION'],
    ARRAY['vows','push on','defends','backs','hybrid war','won''t stop','denounces violence','shipbuilding','training partnership','memorandum of understanding','wirtschaftliche Chance','Investitionspartnerschaft'],
    true, 1
),
(
    'balkan_sovereignty_environmental_rejection', 'balkan_foreign_capital',
    E'\'Albania is not for sale\': a protected coastline is being privatised for elite foreign gain',
    E'„Albanien ist nicht zu verkaufen“: eine geschützte Küste wird für den Gewinn einer ausländischen Elite privatisiert',
    'This framing, carried by the same wire outlets under different keywords plus environmental and opposition voices, treats the Kushner-linked resort on the island of Sazan and the Zvernec wetland as a land grab that trades a protected coastline and Albania''s EU accession credibility for the enrichment of a politically connected few. Mass protests, police action against demonstrators and Brussels'' own warnings that the deal risks accession are read as confirmation that the project subverts environmental law and democratic accountability alike.',
    'Diese von denselben Nachrichtenagenturen unter anderen Stichworten sowie von Umwelt- und Oppositionsstimmen getragene Deutung behandelt das mit Kushner verbundene Resort auf der Insel Sazan und das Feuchtgebiet von Zvernec als Landraub, der eine geschuetzte Kueste und Albaniens Glaubwuerdigkeit im EU-Beitrittsprozess fuer die Bereicherung weniger politisch Verbundener opfert. Massenproteste, Polizeieinsaetze gegen Demonstrierende und Bruessels eigene Warnungen, das Geschaeft gefaehrde den Beitrittsprozess, gelten in dieser Lesart als Bestaetigung, dass das Projekt sowohl Umweltrecht als auch demokratische Rechenschaftspflicht untergraebt.',
    -2, 'Sovereignty & environmental rejection', 'Souveraenitaets- und Umweltablehnung',
    ARRAY['EUROPE-BALKANS','NON-STATE-EU'],
    ARRAY['Reuters','Bloomberg','Euronews','eKathimerini','ANSA','Albanian Daily News','EurActiv','Associated Press','BBC World','CNN','Deutsche Welle','Financial Times','France 24 (EN)','NPR','Sky News','Corriere della Sera','Der Spiegel','Die Zeit','Al Jazeera','The Guardian','RT','Press TV','Al-Ahram','El Mundo','Folha de S.Paulo','Haaretz','Helsinki Times','La Nación','MSNBC','News24','Novinite','The Australian','The Hindu','Times of Israel','WION'],
    ARRAY['not for sale','land grab','protected','wetland','privatising','environmental disaster','outrage','backlash','accession at risk','warns Albania','clashes','arrest protesters','corrupt','protest','rally','demonstrat','anger','controvers','erupt','violent','Proteste','Zusammenstoesse','concern','hurdle','flout','probe'],
    true, 2
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
    stance = EXCLUDED.stance, stance_label_en = EXCLUDED.stance_label_en, stance_label_de = EXCLUDED.stance_label_de,
    actor_centroids = EXCLUDED.actor_centroids, publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords, framing_required = EXCLUDED.framing_required,
    display_order = EXCLUDED.display_order, updated_at = NOW();

-- ============ Theater roll-up narratives (sec 5.5) ============
-- framing_required irrelevant at theater level (roll-up doesn't filter by it).

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required, display_order
) VALUES
(
    'balkan_theater_external_backing', 'balkan_theater',
    'Russia and China back the region''s governments as they resist Western-aligned pressure',
    'Russland und China unterstuetzen die Regierungen der Region in ihrem Widerstand gegen westlich ausgerichteten Druck',
    'Russian and Chinese state media portray Western and EU pressure on Balkan governments -- whether over sanctions, energy assets or scrutiny of foreign investment deals -- as unwarranted interference in sovereign decision-making, and frame continuity in each government''s own foreign-policy choices as the more stable path.',
    'Russische und chinesische Staatsmedien stellen westlichen und EU-Druck auf die Regierungen des Westbalkans -- ob wegen Sanktionen, Energieanlagen oder der Pruefung auslaendischer Investitionsvorhaben -- als unberechtigte Einmischung in souveraene Entscheidungen dar und werten die Kontinuitaet der aussenpolitischen Entscheidungen der jeweiligen Regierung als den stabileren Weg.',
    1, 'External backing against Western pressure', 'Externe Rueckendeckung gegen westlichen Druck',
    ARRAY['EUROPE-RUSSIA','ASIA-CHINA'],
    ARRAY['TASS','TASS (EN)','RT','Lenta.ru','Gazeta.ru','Kommersant','Izvestia','RIA Novosti','CGTN','China Daily'],
    ARRAY[]::text[],
    false, 1
),
(
    'balkan_theater_investment_opportunity', 'balkan_theater',
    'Foreign capital and international partnerships are framed as development opportunities governments are right to defend',
    'Auslaendisches Kapital und internationale Partnerschaften werden als Entwicklungschancen dargestellt, die Regierungen zu Recht verteidigen',
    'International wire coverage and regional business press present foreign investment projects, from shipbuilding partnerships to large resort developments, as legitimate economic opportunity, reporting governments'' own defense of the deals against domestic and EU objections as a reasonable stance rather than as complicity.',
    'Internationale Agenturberichterstattung und die regionale Wirtschaftspresse stellen auslaendische Investitionsprojekte, von Schiffbau-Partnerschaften bis zu grossen Resortentwicklungen, als legitime wirtschaftliche Chance dar und berichten ueber die eigene Verteidigung der Geschaefte durch die Regierungen gegen innenpolitische und EU-Einwaende als vertretbare Haltung und nicht als Mittaeterschaft.',
    1, 'Investment as opportunity', 'Investition als Chance',
    ARRAY['EUROPE-BALKANS','AMERICAS-USA','EUROPE-SOUTH'],
    ARRAY['Reuters','Bloomberg','Euronews','eKathimerini','ANSA','Albanian Daily News','EurActiv','Associated Press','BBC World','CNN','Deutsche Welle','Financial Times','France 24 (EN)','NPR','Sky News','Corriere della Sera','Der Spiegel','Die Zeit'],
    ARRAY[]::text[],
    false, 2
),
(
    'balkan_theater_accountability_deficit', 'balkan_theater',
    E'From a collapsed canopy to a privatised coastline, political elites are accused of prioritising power and profit over the public',
    E'Vom eingestürzten Vordach bis zur privatisierten Küste: politischen Eliten wird vorgeworfen, Macht und Profit über das Gemeinwohl zu stellen',
    'Independent regional outlets and Western mainstream press link Serbia''s protest movement, ignited by the fatal Novi Sad canopy collapse, with Albania''s Kushner-linked resort controversy as two faces of the same pattern: governing parties accused of shielding corrupt contracting, unaccountable land deals and politically connected beneficiaries from scrutiny, while demonstrators demand resignations, snap elections and legal accountability.',
    'Unabhaengige regionale Medien und die westliche Mainstream-Presse verbinden Serbiens durch den toedlichen Einsturz des Vordachs von Novi Sad ausgeloeste Protestbewegung mit der Kontroverse um das Kushner-verbundene Resort in Albanien als zwei Auspraegungen desselben Musters: Regierungsparteien wird vorgeworfen, korrupte Vergabepraxis, unkontrollierte Landgeschaefte und politisch vernetzte Nutzniesser vor Kontrolle zu schuetzen, waehrend Demonstrierende Ruecktritte, Neuwahlen und rechtliche Rechenschaft fordern.',
    -2, 'Elite capture and accountability deficit', 'Elitenbereicherung und Rechenschaftsdefizit',
    ARRAY['EUROPE-BALKANS','NON-STATE-EU'],
    ARRAY['N1 Serbia','Vijesti','N1','Reuters','The Guardian','Der Spiegel','Die Zeit','Der Standard','Tagesschau','Bloomberg','Al Jazeera','Euronews','Kurier','Novinite','Jerusalem Post','Daily Sabah','CNN','eKathimerini','ANSA','Albanian Daily News','EurActiv','Associated Press','BBC World','Deutsche Welle','Financial Times','France 24 (EN)','NPR','Sky News','Corriere della Sera'],
    ARRAY[]::text[],
    false, 3
)
ON CONFLICT (id) DO UPDATE SET
    name_en = EXCLUDED.name_en, name_de = EXCLUDED.name_de,
    claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
    stance = EXCLUDED.stance, stance_label_en = EXCLUDED.stance_label_en, stance_label_de = EXCLUDED.stance_label_de,
    actor_centroids = EXCLUDED.actor_centroids, publishers = EXCLUDED.publishers,
    framing_keywords = EXCLUDED.framing_keywords, framing_required = EXCLUDED.framing_required,
    display_order = EXCLUDED.display_order, updated_at = NOW();

-- ============ Bilingual completeness fields ============
-- No internal vocabulary ("theater", "node", "atomic") and no reference
-- to a fixed count of member phenomena, per editorial style rule.

UPDATE friction_nodes SET
    description_en = 'Serbia''s ruling party faces sustained protests after the fatal collapse of a renovated railway canopy in Novi Sad exposed years of unaccountable construction contracting, while Belgrade balances Western pressure over sanctions and energy assets against its ties to Moscow and Beijing. Albania''s coastline has become a flashpoint of its own, as a Kushner-linked resort development draws mass protests, environmental warnings and scrutiny from Brussels even as the government defends the investment as a driver of growth. Together they trace a recurring regional pattern: political elites courting foreign capital and foreign patrons while facing domestic demands for accountability.',
    description_de = 'Serbiens Regierungspartei sieht sich anhaltenden Protesten ausgesetzt, nachdem der toedliche Einsturz eines renovierten Bahnhofsvordachs in Novi Sad jahrelange unkontrollierte Bauvergabe offenlegte, waehrend Belgrad westlichen Druck wegen Sanktionen und Energieanlagen gegen seine Beziehungen zu Moskau und Peking abwaegt. Albaniens Kueste ist zu einem eigenen Brennpunkt geworden, seit ein mit Kushner verbundenes Resortprojekt Massenproteste, Umweltwarnungen und die Pruefung durch Bruessel auf sich zieht, waehrend die Regierung die Investition als Wachstumstreiber verteidigt. Gemeinsam zeichnen beide Faelle ein wiederkehrendes regionales Muster: politische Eliten, die auslaendisches Kapital und auslaendische Schutzmaechte umwerben, waehrend sie innenpolitisch mit Forderungen nach Rechenschaft konfrontiert sind.',
    editorial_summary_en = 'Coverage in mid-2026 centers on Serbia''s protest movement, sustained by demands for Vucic''s resignation and early elections since the fatal Novi Sad canopy collapse, alongside the government''s parallel resistance to Western pressure over Russian-owned energy assets. In Albania, a Trump-family-linked resort project on a protected coastline has drawn weeks of demonstrations, arrests and EU accession warnings, met by the government''s public defense of the deal as economic opportunity. Both episodes foreground the same underlying question across the region: whether ruling parties answer to their publics or to the capital, foreign and domestic, that sustains them.',
    editorial_summary_de = 'Die Berichterstattung Mitte 2026 konzentriert sich auf Serbiens Protestbewegung, getragen von Forderungen nach Vucics Ruecktritt und vorgezogenen Neuwahlen seit dem toedlichen Einsturz des Vordachs von Novi Sad, neben dem parallelen Widerstand der Regierung gegen westlichen Druck wegen russischer Energieanlagen. In Albanien haben ein mit der Trump-Familie verbundenes Resortprojekt an einer geschuetzten Kueste wochenlange Demonstrationen, Festnahmen und Warnungen zum EU-Beitritt ausgeloest, denen die Regierung mit einer oeffentlichen Verteidigung des Geschaefts als wirtschaftliche Chance begegnet. Beide Episoden werfen in der Region dieselbe grundlegende Frage auf: ob Regierungsparteien ihrer Oeffentlichkeit Rechenschaft schulden oder dem Kapital, auslaendisch wie inlaendisch, das sie stuetzt.',
    updated_at = NOW()
WHERE id = 'balkan_theater';

UPDATE friction_nodes SET
    description_en = 'Serbia''s ruling party under sustained pressure since the fatal collapse of a renovated railway station canopy in Novi Sad, which student-led protesters read as proof of systemic corruption in public contracting. Demonstrations demanding resignation and early elections continue alongside the government''s separate resistance to Western pressure over sanctioning Russia and divesting its stake in the Russian-owned oil company NIS.',
    description_de = 'Serbiens Regierungspartei steht seit dem toedlichen Einsturz eines renovierten Bahnhofsvordachs in Novi Sad unter anhaltendem Druck, den von Studierenden angefuehrte Protestierende als Beweis systemischer Korruption bei der oeffentlichen Auftragsvergabe werten. Die Demonstrationen mit Forderungen nach Ruecktritt und vorgezogenen Neuwahlen dauern an, parallel zum eigenstaendigen Widerstand der Regierung gegen westlichen Druck, Russland zu sanktionieren und ihren Anteil am russischen Oelkonzern NIS zu veraeussern.',
    editorial_summary_en = 'Sustained protests since the Novi Sad canopy collapse have put Serbia''s presidency under its most serious domestic challenge in years, with resignation calls, snap-election demands and periodic police crackdowns running alongside a separate track: Vucic''s continued refusal to sanction Russia and his defense of NIS''s US sanctions licence.',
    editorial_summary_de = 'Anhaltende Proteste seit dem Einsturz des Vordachs von Novi Sad stellen Serbiens Praesidentschaft vor die ernsteste innenpolitische Herausforderung seit Jahren, mit Ruecktrittsforderungen, Forderungen nach vorgezogenen Neuwahlen und wiederkehrenden Polizeieinsaetzen -- parallel zu einem zweiten Strang: Vucics anhaltender Weigerung, Russland zu sanktionieren, und seiner Verteidigung der US-Sanktionslizenz fuer NIS.',
    updated_at = NOW()
WHERE id = 'serbia_government_legitimacy';

UPDATE friction_nodes SET
    description_en = 'Foreign-backed development projects testing where Western Balkan governments draw the line between welcome investment and the sale of sovereign and environmental interests. The clearest case is a Kushner-linked luxury resort on Albania''s Sazan island, which has drawn sustained protests, environmental warnings over a protected coastline, and scrutiny from Brussels over its implications for EU accession, even as the government defends the deal as a source of jobs and growth.',
    description_de = 'Auslaendisch finanzierte Entwicklungsprojekte stellen die Frage, wo Regierungen des Westbalkans die Grenze zwischen willkommener Investition und dem Verkauf souveraener und oekologischer Interessen ziehen. Der deutlichste Fall ist ein mit Kushner verbundenes Luxusresort auf der albanischen Insel Sazan, das anhaltende Proteste, Umweltwarnungen wegen einer geschuetzten Kueste und die Pruefung durch Bruessel im Hinblick auf den EU-Beitrittsprozess ausgeloest hat, waehrend die Regierung das Geschaeft als Quelle fuer Arbeitsplaetze und Wachstum verteidigt.',
    editorial_summary_en = 'Weeks of protest in Tirana over the Kushner-backed Sazan resort have combined environmental objections -- construction on a protected wetland and coastline -- with warnings that the deal jeopardizes Albania''s EU accession credibility, against a government that has publicly defended the project and characterized opposition to it as politically motivated.',
    editorial_summary_de = 'Wochenlange Proteste in Tirana gegen das von Kushner unterstuetzte Sazan-Resort verbinden Umwelteinwaende -- Bauarbeiten auf einem geschuetzten Feuchtgebiet und Kuestenabschnitt -- mit Warnungen, das Geschaeft gefaehrde Albaniens Glaubwuerdigkeit im EU-Beitrittsprozess, gegenueber einer Regierung, die das Projekt oeffentlich verteidigt und den Widerstand dagegen als politisch motiviert bezeichnet hat.',
    updated_at = NOW()
WHERE id = 'balkan_foreign_capital';

COMMIT;
