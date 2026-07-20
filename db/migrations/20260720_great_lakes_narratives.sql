-- Great Lakes theater: ATOMIC narratives (greenfield, 2026-07-20).
-- Nine narratives across the three atomics. Bilingual, full field set.
--
-- ---------------------------------------------------------------------------
-- THE DEFINING CONSTRAINT: THERE IS NO PRO-M23 / PRO-RWANDA CONSTITUENCY.
--
-- Checked before designing any coalition (the Cuba lesson: a stance can have no
-- constituency -- retire it, do not keyword-stuff). Every non-Western outlet in
-- the feed reports the M23 story neutrally or critically:
--   Daily Sabah  "M23 detaining, abusing thousands of civilians: HRW"
--   Al Jazeera   "US sanctions Rwandan army and top officials for supporting M23"
--   Anadolu      "DR Congo army accuses M23 rebels of deadly attacks"
--   CGTN         "M23 stage a drone attack on DR Congo airport"
--   RT           "Rebel spokesperson killed in DR Congo - media"  (1 title total)
--
-- So the sympathetic pole is NOT built as an endorsement narrative. It is built
-- as what the corpus actually contains: the accused parties REJECTING the
-- backing charge, carried by the outlets that print their response (Rwanda
-- "hits back", Kagame calls sanctions "insults", Kabila calls them
-- "unjustified"). That is an honest, attributable position held by parties to
-- the conflict -- not an invented endorsement bloc.
--
-- ---------------------------------------------------------------------------
-- WHERE THE RIFT-EXPLOITATION CARD APPLIES, AND WHERE IT DOES NOT (SCS lesson:
-- check whether the actor is a PARTY before reaching for it).
--
--   drc_peace_process        -> YES. The mediator is the United States; Russia
--                               and China are bystanders amplifying a
--                               sovereignty critique of Western pressure.
--   drc_minerals_competition -> NO. China is a PRINCIPAL here (Zijin, CMOC, the
--                               incumbent cobalt position, "Chinese Cobalt Plant
--                               Sickened Congo Town"). Its coverage therefore
--                               belongs on the dispute's OWN axis -- incumbent
--                               versus challenger for Congolese minerals -- not
--                               on a schadenfreude card.
--
-- ---------------------------------------------------------------------------
-- OWN-GOAL TOPIC (§5): drc_minerals_competition. The critical coverage spans
-- both camps -- the Guardian on global brands "likely using mineral that funds
-- rebels", the WSJ and Le Monde on a Chinese cobalt plant gassing a Congolese
-- town, 200 dead in the Rubaya collapse. Publisher alignment therefore does NOT
-- predict stance, so the development and human-cost narratives share the same
-- business/Western pool and are separated by framing_required with disjoint
-- keyword sets. Same pattern applied to m23_conflict (offensive vs civilian
-- toll) and drc_peace_process (progress vs stalling).
--
-- framing_keywords are multilingual (EN + FR + DE): French is 21% of this
-- corpus and France 24 is the single largest publisher (57 titles), so an
-- EN-only keyword set would under-fire badly (the Sahel lesson).
--
-- No DELETE; INSERT ... ON CONFLICT DO UPDATE. Reversible.

BEGIN;

-- ===========================================================================
-- A. m23_conflict
-- ===========================================================================

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'm23_externally_backed_offensive',
    'm23_conflict',
    'An externally backed offensive',
    'Eine von außen unterstützte Offensive',
    'M23 is not a self-sustaining local rebellion but a force armed and directed from across the border, able to seize cities, strike airports with drones and hold territory because a neighbouring state supplies it. The sanctions imposed on Rwandan commanders and on Joseph Kabila are the belated recognition of a cross-border war being fought through a proxy.',
    'M23 ist kein sich selbst tragender lokaler Aufstand, sondern eine von jenseits der Grenze bewaffnete und geführte Truppe, die Städte einnehmen, Flughäfen mit Drohnen angreifen und Gebiete halten kann, weil ein Nachbarstaat sie versorgt. Die Sanktionen gegen ruandische Kommandeure und gegen Joseph Kabila sind die späte Anerkennung eines grenzüberschreitenden Krieges, der über einen Stellvertreter geführt wird.',
    -2,
    'A cross-border proxy war',
    'Ein grenzüberschreitender Stellvertreterkrieg',
    ARRAY['AFRICA-DRC', 'AMERICAS-USA'],
    ARRAY['France 24', 'France 24 (EN)', 'Le Monde', 'Le Figaro', 'Reuters', 'Associated Press', 'The Guardian', 'BBC World', 'BBC', 'Deutsche Welle', 'Washington Post', 'Financial Times', 'The Economist', 'Swissinfo', 'ANSA', 'news.un.org', 'UN News', 'Al Jazeera', 'Anadolu Agency', 'Daily Sabah', 'TRT World', 'Daily Nation', 'The Standard', 'Punch Newspapers', 'Janes'],
    ARRAY['backing', 'backed', 'support for', 'supporting', 'proxy', 'sanctions', 'visa restrictions', 'Rwandan army', 'Rwandan officials', 'offensive', 'seized', 'captured', 'retake', 'retook', 'held', 'occupied', 'drone strike', 'drone attack', 'incursion', 'soutien', 'soutenu', 'appuyé', 'sanctions', 'offensive', 'conquise', 'contrôlé', 'frappe de drone', 'Unterstützung', 'unterstützt', 'Sanktionen', 'Offensive', 'Drohnenangriff'],
    true, 1, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'm23_civilian_toll',
    'm23_conflict',
    'The population pays for every advance',
    'Die Bevölkerung zahlt für jeden Vorstoß',
    'Whoever is judged responsible, the measurable result of this war is borne by civilians: thousands detained and abused in captured towns, mass displacement across the Burundian and Rwandan borders, aid workers killed by drones, and rights investigators documenting killings and rapes in Uvira. Territorial gains and losses change faster than the humanitarian damage they leave.',
    'Wer auch immer als verantwortlich gilt: Die messbaren Folgen dieses Krieges tragen die Zivilisten. Tausende werden in eroberten Städten festgehalten und misshandelt, Massen fliehen über die burundische und ruandische Grenze, Helfer sterben durch Drohnen, und Ermittler dokumentieren Tötungen und Vergewaltigungen in Uvira. Geländegewinne wechseln schneller als der humanitäre Schaden, den sie hinterlassen.',
    -1,
    'The humanitarian cost',
    'Die humanitären Kosten',
    ARRAY['AFRICA-DRC'],
    ARRAY['France 24', 'France 24 (EN)', 'Le Monde', 'Le Figaro', 'Reuters', 'Associated Press', 'The Guardian', 'BBC World', 'BBC', 'Deutsche Welle', 'Washington Post', 'The Economist', 'news.un.org', 'UN News', 'Al Jazeera', 'Anadolu Agency', 'Daily Sabah', 'TRT World', 'Daily Nation', 'The Standard', 'Der Spiegel'],
    ARRAY['civilian', 'civilians', 'displaced', 'displacement', 'refugee', 'refugees', 'abuse', 'abusing', 'detaining', 'detained', 'atrocities', 'killings', 'rapes', 'massacre', 'aid worker', 'humanitarian', 'hunger', 'human rights', 'HRW', 'trauma', 'civils', 'déplacés', 'réfugiés', 'atrocités', 'exactions', 'humanitaire', 'traumatismes', 'droits humains', 'Zivilisten', 'Vertriebene', 'Flüchtlinge', 'Gräueltaten', 'humanitär', 'Menschenrechte'],
    true, 2, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'm23_backing_charge_rejected',
    'm23_conflict',
    'The accused parties reject the charge',
    'Die Beschuldigten weisen den Vorwurf zurück',
    'Kigali and the figures named in Western sanctions dispute the proxy account entirely. They present the sanctions as insults that will not change Rwandan defence policy, describe the designations as unjustified, and point to the armed groups operating on the Congolese side of the border and to Kinshasa''s inability to protect its own eastern population as the actual origin of the fighting.',
    'Kigali und die in westlichen Sanktionen genannten Personen bestreiten die Stellvertreter-Darstellung vollständig. Sie bezeichnen die Sanktionen als Beleidigungen, die an Ruandas Verteidigungspolitik nichts ändern, nennen die Listungen ungerechtfertigt und verweisen auf die bewaffneten Gruppen auf kongolesischer Seite sowie auf Kinshasas Unfähigkeit, die eigene Bevölkerung im Osten zu schützen, als eigentlichen Ursprung der Kämpfe.',
    1,
    'The charge is disputed',
    'Der Vorwurf ist bestritten',
    ARRAY['AFRICA-DRC'],
    ARRAY['The Standard', 'Daily Nation', 'Mail & Guardian', 'Anadolu Agency', 'Al-Ahram', 'News24', 'RT', 'TASS (EN)', 'CGTN'],
    ARRAY['denies', 'denied', 'denounces', 'rejects', 'rejected', 'unjustified', 'unfounded', 'hits back', 'insults', 'sovereignty', 'internal affairs', 'self-defence', 'FDLR', 'genocidaires', 'Banyamulenge', 'Tutsi', 'dément', 'rejette', 'dénonce', 'injustifié', 'souveraineté', 'légitime défense', 'weist zurück', 'bestreitet', 'ungerechtfertigt', 'Souveränität', 'Selbstverteidigung'],
    true, 3, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

-- ===========================================================================
-- B. drc_peace_process
-- ===========================================================================

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'drc_accords_are_working',
    'drc_peace_process',
    'The accords are the route out of the war',
    'Die Abkommen sind der Weg aus dem Krieg',
    'External mediation is producing things the battlefield never did: a signed monitoring mechanism, prisoners released, humanitarian access agreed within fixed deadlines, and a commitment from both sides to protect civilians. Kinshasa is explicitly betting on the Washington track to secure the east, and the monitoring mission is being rebuilt around supporting the ceasefire rather than fighting a war.',
    'Die externe Vermittlung bringt hervor, was das Schlachtfeld nie erreicht hat: einen unterzeichneten Überwachungsmechanismus, freigelassene Gefangene, humanitären Zugang mit festen Fristen und die Zusage beider Seiten, Zivilisten zu schützen. Kinshasa setzt ausdrücklich auf den Washingtoner Weg, um den Osten zu sichern, und die Beobachtermission wird darauf ausgerichtet, den Waffenstillstand zu stützen statt Krieg zu führen.',
    2,
    'Mediation is delivering',
    'Vermittlung zeigt Wirkung',
    ARRAY['AFRICA-DRC', 'AMERICAS-USA'],
    ARRAY['France 24', 'France 24 (EN)', 'Le Monde', 'Reuters', 'Associated Press', 'Swissinfo', 'news.un.org', 'UN News', 'Al Jazeera', 'Anadolu Agency', 'Deutsche Welle', 'The Standard', 'Daily Nation', 'ANSA'],
    ARRAY['agreement', 'accord', 'signed', 'commit', 'commitment', 'progress', 'monitoring', 'release', 'released', 'prisoners', 'facilitate', 'de-escalate', 'breakthrough', 'holds', 'mechanism', 'accord', 'signé', 'engagement', 'progrès', 'libérer', 'libération', 'faciliter', 'désescalade', 'Abkommen', 'unterzeichnet', 'Fortschritt', 'Freilassung', 'Deeskalation'],
    true, 1, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'drc_accords_stalling',
    'drc_peace_process',
    'Signed, stalled, and unenforced',
    'Unterzeichnet, blockiert, nicht durchgesetzt',
    'The documents exist and the fighting continues. Peace deals are described by Kinshasa''s own spokesman as blocked by the conduct of the Rwandan president; the two sides trade accusations over a ceasefire neither observes; attacks continue while talks sit in Switzerland. Sanctions arrive after violations rather than preventing them, which makes the accords a record of intentions rather than a constraint on behaviour.',
    'Die Dokumente existieren, die Kämpfe gehen weiter. Friedensabkommen werden vom Sprecher Kinshasas selbst als blockiert durch das Verhalten des ruandischen Präsidenten beschrieben; beide Seiten werfen einander Verstöße gegen einen Waffenstillstand vor, den keine Seite einhält; Angriffe dauern an, während in der Schweiz verhandelt wird. Sanktionen folgen den Verstößen, statt sie zu verhindern -- die Abkommen sind damit eher ein Protokoll von Absichten als eine Schranke für das Handeln.',
    -1,
    'The process is not holding',
    'Der Prozess trägt nicht',
    ARRAY['AFRICA-DRC'],
    ARRAY['France 24', 'France 24 (EN)', 'Le Monde', 'Le Figaro', 'Reuters', 'Associated Press', 'The Guardian', 'BBC World', 'Deutsche Welle', 'Washington Post', 'Financial Times', 'news.un.org', 'UN News', 'Al Jazeera', 'Anadolu Agency', 'Daily Sabah', 'The Standard', 'Daily Nation', 'Janes'],
    ARRAY['stalled', 'stalling', 'stagnate', 'stagnant', 'no progress', 'violation', 'violating', 'violated', 'accuses', 'accusations', 'breach', 'collapse', 'fragile', 'delay', 'delayed', 'persists', 'stagnent', 'bloqué', 's''enlise', 'n''avance pas', 'violation', 'accuse', 'accusations', 'retard', 'ins Stocken', 'blockiert', 'Verstoß', 'Verzögerung', 'wirft vor'],
    true, 2, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'drc_mediation_as_interference',
    'drc_peace_process',
    'Peacemaking with a price tag',
    'Friedensstiftung mit Preisschild',
    'The mediation is read here as leverage rather than diplomacy: a settlement brokered by the same power that is negotiating access to Congolese deposits, with sanctions used as the instrument of pressure and African sovereignty as the cost. On this account the accords are less a peace framework than the political wrapper around a resource arrangement, and the states applying the pressure are parties to the outcome rather than neutral arbiters.',
    'Die Vermittlung wird hier als Druckmittel gelesen, nicht als Diplomatie: eine Regelung, vermittelt von derselben Macht, die zugleich über den Zugang zu kongolesischen Vorkommen verhandelt, mit Sanktionen als Druckinstrument und afrikanischer Souveränität als Preis. In dieser Lesart sind die Abkommen weniger ein Friedensrahmen als die politische Verpackung einer Rohstoffvereinbarung, und die Druck ausübenden Staaten sind Partei, nicht neutrale Schiedsrichter.',
    -2,
    'Pressure dressed as mediation',
    'Druck im Gewand der Vermittlung',
    ARRAY['AFRICA-DRC', 'AMERICAS-USA'],
    ARRAY['RT', 'TASS', 'TASS (EN)', 'Sputnik', 'RIA Novosti', 'Press TV', 'CGTN', 'Global Times', 'China Daily'],
    ARRAY['interference', 'meddling', 'neocolonial', 'neo-colonial', 'imperial', 'exploitation', 'resource grab', 'unilateral', 'pressure', 'hegemony', 'so-called', 'double standard', 'ingérence', 'néocolonial', 'impérial', 'pression', 'unilatéral', 'Einmischung', 'neokolonial', 'Druck', 'Doppelmoral'],
    false, 3, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

-- ===========================================================================
-- C. drc_minerals_competition  (own-goal topic -- three-stance gradient)
-- ===========================================================================

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'drc_minerals_as_development',
    'drc_minerals_competition',
    'Capital arriving at last',
    'Kapital, das endlich ankommt',
    'Demand for battery and data-centre metals is finally being converted into Congolese assets: a state mining champion under new leadership, a distressed cobalt producer rescued by an American buyer, exploration money flowing into lithium, copper exports to the United States multiplying, a reopened corridor to Zambian ports and a first domestic stock exchange. Export controls are treated here as a producer country learning to price what it owns.',
    'Die Nachfrage nach Batterie- und Rechenzentrumsmetallen wird endlich in kongolesische Werte umgesetzt: ein staatlicher Bergbaukonzern unter neuer Führung, ein angeschlagener Kobaltproduzent durch einen amerikanischen Käufer gerettet, Explorationsgelder für Lithium, vervielfachte Kupferexporte in die USA, ein wieder geöffneter Korridor zu sambischen Häfen und eine erste eigene Börse. Exportkontrollen gelten hier als ein Förderland, das lernt, seinen Besitz zu bepreisen.',
    2,
    'Investment and leverage',
    'Investitionen und Verhandlungsmacht',
    ARRAY['AFRICA-DRC', 'AMERICAS-USA'],
    ARRAY['Mining.com', 'Bloomberg', 'Financial Times', 'S&P Global', 'OilPrice', 'News24', 'Reuters', 'The Australian', 'Egypt Today'],
    ARRAY['deal', 'agreement', 'pact', 'investment', 'invest', 'stake', 'boom', 'growth', 'exploration', 'approve', 'approved', 'takeover', 'acquisition', 'corridor', 'stock market', 'exports', 'output', 'production', 'reopen', 'accord', 'investissement', 'croissance', 'exportations', 'production', 'Investition', 'Wachstum', 'Übernahme', 'Ausfuhren'],
    true, 1, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'drc_minerals_human_cost',
    'drc_minerals_competition',
    'The price is paid at the pit',
    'Bezahlt wird an der Grube',
    'The same supply chain that supplies the energy transition also produces two hundred dead in a single coltan collapse, a town reporting bleeding children after a cobalt plant leak, and consumer brands that cannot demonstrate their metal did not finance an armed group. Buyers describe their own due diligence as failing: deposits offered to foreign investors sit inside contested territory, and the paperwork does not survive contact with the pit.',
    'Dieselbe Lieferkette, die die Energiewende speist, produziert auch zweihundert Tote bei einem einzigen Coltan-Einsturz, eine Stadt mit blutenden Kindern nach einem Leck in einer Kobaltanlage und Markenhersteller, die nicht belegen können, dass ihr Metall keine bewaffnete Gruppe finanziert hat. Die Abnehmer bezeichnen ihre eigene Sorgfaltsprüfung als unzureichend: Vorkommen, die ausländischen Investoren angeboten werden, liegen in umkämpftem Gebiet, und die Papiere halten dem Vergleich mit der Grube nicht stand.',
    -1,
    'Human and environmental cost',
    'Menschliche und ökologische Kosten',
    ARRAY['AFRICA-DRC'],
    ARRAY['The Guardian', 'Wall Street Journal', 'Le Monde', 'France 24', 'France 24 (EN)', 'Deutsche Welle', 'Associated Press', 'BBC World', 'BBC', 'Al Jazeera', 'Folha de S.Paulo', 'Council on Foreign Relations', 'Daily Maverick', 'Globe and Mail', 'La Repubblica', 'Press TV', 'DR'],
    ARRAY['toxic', 'sickened', 'poison', 'gas leak', 'waste', 'collapse', 'landslide', 'killed', 'dead', 'buried', 'child', 'children', 'artisanal', 'funds rebels', 'atrocities', 'war zone', 'de-risk', 'due diligence', 'human rights', 'exploitation', 'toxique', 'rejets', 'éboulement', 'glissement de terrain', 'morts', 'enfants', 'artisanale', 'droits humains', 'giftig', 'Einsturz', 'Erdrutsch', 'Tote', 'Kinderarbeit', 'Menschenrechte'],
    true, 2, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES (
    'drc_minerals_as_resource_capture',
    'drc_minerals_competition',
    'A takeover of an established position',
    'Übernahme einer gewachsenen Position',
    'Seen from the incumbent side, the American entry is not new investment but the displacement of partners who built the refining and processing base over two decades, achieved through political leverage rather than commercial performance. Deposits are being tied to security guarantees, state mining leadership replaced during negotiations, and a producer country pressed into an exclusive alignment while its own officials call the terms constitutionally doubtful.',
    'Aus Sicht der etablierten Seite ist der amerikanische Einstieg keine neue Investition, sondern die Verdrängung von Partnern, die über zwei Jahrzehnte die Raffinerie- und Verarbeitungsbasis aufgebaut haben -- erreicht durch politischen Druck, nicht durch wirtschaftliche Leistung. Vorkommen werden an Sicherheitsgarantien geknüpft, die staatliche Bergbauführung während der Verhandlungen ausgetauscht und ein Förderland in eine exklusive Bindung gedrängt, während eigene Amtsträger die Bedingungen für verfassungsrechtlich zweifelhaft halten.',
    -2,
    'Displacement of incumbents',
    'Verdrängung der Etablierten',
    ARRAY['AFRICA-DRC', 'ASIA-CHINA'],
    ARRAY['CGTN', 'Global Times', 'China Daily', 'Xinhua', 'RT', 'TASS', 'TASS (EN)', 'Sputnik', 'RIA Novosti', 'Daily Nation'],
    ARRAY['grab', 'capture', 'seize', 'exclusive', 'displace', 'squeeze out', 'leverage', 'unconstitutional', 'flawed', 'sovereignty', 'neocolonial', 'neo-colonial', 'plunder', 'scramble', 'strings attached', 'inconstitutionnel', 'souveraineté', 'néocolonial', 'pillage', 'verfassungswidrig', 'Souveränität', 'neokolonial', 'Ausplünderung'],
    false, 3, true
) ON CONFLICT (id) DO UPDATE SET
    fn_id=EXCLUDED.fn_id, name_en=EXCLUDED.name_en, name_de=EXCLUDED.name_de,
    claim_en=EXCLUDED.claim_en, claim_de=EXCLUDED.claim_de, stance=EXCLUDED.stance,
    stance_label_en=EXCLUDED.stance_label_en, stance_label_de=EXCLUDED.stance_label_de,
    actor_centroids=EXCLUDED.actor_centroids, publishers=EXCLUDED.publishers,
    framing_keywords=EXCLUDED.framing_keywords, framing_required=EXCLUDED.framing_required,
    display_order=EXCLUDED.display_order, is_active=true, updated_at=NOW();

COMMIT;
