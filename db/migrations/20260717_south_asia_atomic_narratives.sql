-- South Asia theater: atomic narratives (§5)
--
-- Coalition logic. This region has an unusually clean publisher structure: the
-- Indian bloc (ToI/HT/NDTV/The Hindu/Indian Express/WION/Republic/DD) and the
-- Pakistani bloc (Dawn/Express Tribune/The News International/The Nation) are
-- fully disjoint and both are openly stance-bearing, so framing_keywords are
-- NOT a hard filter on the national-bloc narratives (framing_required=false).
-- Publisher-name variants matter: "Times of India" AND "The Times of India",
-- "Indian Express" AND "The Indian Express", "Express Tribune" AND "The Express
-- Tribune", "Republic TV" AND "Republic World" are distinct strings in titles_v3.
--
-- NOTE on Afghanistan: the corpus contains NO Afghan domestic outlets (no Tolo,
-- Khaama, Pajhwok, Ariana). The Afghan side of the border war is carried by
-- Al Jazeera/TRT/Anadolu/RT/TASS, which relay the Taliban's accusations, plus
-- the Indian bloc -- which frames it explicitly as sovereignty violation
-- ("'Assault on Afghan sovereignty': India after UN report says hundreds of
-- civilians killed"). Hence the Indian bloc sits on the -2 card, not a card of
-- its own.
--
-- No rift-exploitation card anywhere here (contrast Arctic §5): that caveat is
-- for INTRA-WESTERN disputes where Russia/China are bystanders amplifying a
-- split. India and Pakistan are the principals; RT/TASS coverage is ordinary
-- conflict reporting, and per the us_china lesson the bloc was checked for a
-- distinctive line before being considered -- it does not push one here.
--
-- framing_required=true is used ONLY on balochistan_insurgency's Pakistani-state
-- card: bare 'Baloch' is an A2 toponym gate running ~85% on-topic, and the ~15%
-- residual is bus crashes and earthquakes datelined Balochistan. The framing
-- gate keeps that incident noise off the narrative card.

BEGIN;

-- ===========================================================================
-- pakistan_afghanistan_border  (223 events -- the theater's largest atomic)
-- ===========================================================================
INSERT INTO narratives_v2
  (id, fn_id, display_order, stance, stance_label_en, stance_label_de,
   name_en, name_de, claim_en, claim_de, publishers, framing_keywords,
   framing_required, actor_centroids, is_active)
VALUES
('pakafg_counterterror_necessity', 'pakistan_afghanistan_border', 1, 2,
 'Pakistani counter-terrorism necessity', 'Pakistanische Notwendigkeit der Terrorbekämpfung',
 'Strikes target militant sanctuaries Kabul refuses to close',
 'Angriffe zielen auf Militantenrückzugsgebiete, die Kabul nicht schließt',
 'Pakistani state-security framing (Pakistani press) holds that cross-border strikes hit Tehreek-e-Taliban sanctuaries on Afghan soil, that Kabul has failed to act against militants who attack Pakistani forces and civilians, and that Pakistan acted only after repeated attacks and demands for verifiable action went unanswered.',
 'Die pakistanische Sicherheitsdarstellung (pakistanische Presse) besagt, dass die grenzüberschreitenden Angriffe Rückzugsgebiete der Tehreek-e-Taliban auf afghanischem Boden treffen, dass Kabul nicht gegen Militante vorgegangen ist, die pakistanische Sicherheitskräfte und Zivilisten angreifen, und dass Pakistan erst handelte, nachdem wiederholte Angriffe und Forderungen nach überprüfbaren Schritten unbeantwortet blieben.',
 ARRAY['Dawn','Express Tribune','The Express Tribune','The News International','The Nation'],
 ARRAY['terrorist infrastructure','militant hideout','sanctuar','TTP','verifiable','Ghazab','retaliat','safe haven','Terrorinfrastruktur','Rückzugsgebiet','Vergeltung'],
 false, ARRAY['ASIA-PAKISTAN'], true),

('pakafg_afghan_sovereignty_violation', 'pakistan_afghanistan_border', 2, -2,
 'Afghan sovereignty violation', 'Verletzung der afghanischen Souveränität',
 'Pakistani strikes on Afghan territory are aggression against a sovereign state',
 'Pakistanische Angriffe auf afghanisches Gebiet sind Aggression gegen einen souveränen Staat',
 'Sovereignty-violation framing (Al Jazeera, Turkish and Russian outlets relaying Kabul''s account, plus the Indian press) treats the strikes as attacks on the territory of a sovereign state: the Taliban government accuses Pakistan of war crimes and of hitting a Kabul hospital, Afghan forces claim retaliatory strikes inside Pakistan, and New Delhi calls the campaign an assault on Afghan sovereignty and a threat to regional peace.',
 'Die Souveränitätsverletzungs-Darstellung (Al Jazeera, türkische und russische Medien, die Kabuls Version wiedergeben, sowie die indische Presse) betrachtet die Angriffe als Attacken auf das Gebiet eines souveränen Staates: Die Taliban-Regierung wirft Pakistan Kriegsverbrechen und den Beschuss eines Krankenhauses in Kabul vor, afghanische Kräfte melden Vergeltungsangriffe in Pakistan, und Neu-Delhi nennt die Kampagne einen Angriff auf die afghanische Souveränität und eine Bedrohung des regionalen Friedens.',
 ARRAY['Al Jazeera','TRT World','Anadolu Agency','RT','rt.com','TASS (EN)','Press TV','IRNA','NDTV','Times of India','The Times of India','Hindustan Times','The Hindu','Indian Express','The Indian Express','WION','Republic TV','Republic World','DD India'],
 ARRAY['sovereignty','war crime','aggression','violation','accuses','condemn','Souveränität','Kriegsverbrechen','Aggression','verurteil'],
 false, ARRAY['ASIA-AFGHANISTAN','ASIA-INDIA'], true),

('pakafg_civilian_harm_alarm', 'pakistan_afghanistan_border', 3, -1,
 'Civilian harm and escalation alarm', 'Alarm über zivile Opfer und Eskalation',
 'The border war is killing civilians and risks a wider conflict',
 'Der Grenzkrieg tötet Zivilisten und droht sich auszuweiten',
 'Civilian-harm framing (Western mainstream and wire services) centres the human cost and the escalation risk rather than either government''s case: casualty counts from strikes on Kabul and the border provinces, UN and aid-agency warnings, displaced and deported Afghans, and the repeated collapse of short ceasefires between two states now describing their relationship as open war.',
 'Die Darstellung ziviler Opfer (westliche Leitmedien und Nachrichtenagenturen) rückt die menschlichen Kosten und das Eskalationsrisiko in den Mittelpunkt statt der Position einer der beiden Regierungen: Opferzahlen nach Angriffen auf Kabul und die Grenzprovinzen, Warnungen der UN und von Hilfsorganisationen, vertriebene und abgeschobene Afghanen sowie das wiederholte Scheitern kurzer Waffenruhen zwischen zwei Staaten, die ihr Verhältnis inzwischen als offenen Krieg bezeichnen.',
 ARRAY['Reuters','BBC World','Associated Press','Deutsche Welle','France 24','France 24 (EN)','Die Zeit','NPR','The Guardian','Euronews','Al Arabiya','Khaleej Times','Arab News'],
 ARRAY['civilian','killed','hospital','casualt','displaced','refugee','ceasefire','UN','aid','Zivilist','getötet','Krankenhaus','Waffenruhe','Flüchtling'],
 false, ARRAY['ASIA-PAKISTAN','ASIA-AFGHANISTAN'], true),

-- ===========================================================================
-- kashmir_dispute  (157 events)
-- ===========================================================================
('kashmir_integral_to_india', 'kashmir_dispute', 1, 2,
 'Kashmir is integral to India', 'Kaschmir ist integraler Teil Indiens',
 'Jammu and Kashmir is Indian territory; Pakistan must vacate what it holds',
 'Jammu und Kaschmir ist indisches Territorium; Pakistan muss die besetzten Gebiete räumen',
 'Indian sovereignty framing (Indian press) treats Jammu and Kashmir, including the areas administered by Pakistan, as Indian territory and the dispute as closed: references to the territory by third parties are rejected as unwarranted interference, Pakistan is told to vacate Gilgit-Baltistan and the areas it holds, and the constitutional changes of 2019 are presented as settled internal matters.',
 'Die indische Souveränitätsdarstellung (indische Presse) betrachtet Jammu und Kaschmir einschließlich der von Pakistan verwalteten Gebiete als indisches Territorium und den Streit als beendet: Äußerungen Dritter zu dem Gebiet werden als unzulässige Einmischung zurückgewiesen, Pakistan wird aufgefordert, Gilgit-Baltistan und die von ihm gehaltenen Gebiete zu räumen, und die Verfassungsänderungen von 2019 gelten als geregelte innere Angelegenheit.',
 ARRAY['Times of India','The Times of India','Hindustan Times','NDTV','The Hindu','Indian Express','The Indian Express','WION','Republic TV','Republic World','DD India'],
 ARRAY['integral','vacate','unwarranted','internal matter','PoK','occupied','Article 370','territory','integraler','räumen','Territorium'],
 false, ARRAY['ASIA-INDIA'], true),

('kashmir_disputed_territory', 'kashmir_dispute', 2, -2,
 'Kashmir is a disputed territory', 'Kaschmir ist ein umstrittenes Gebiet',
 'Kashmir''s status is unresolved and its people are owed self-determination',
 'Kaschmirs Status ist ungeklärt, seiner Bevölkerung steht Selbstbestimmung zu',
 'Disputed-territory framing (Pakistani press and sympathetic Turkish and Gulf outlets) holds that Kashmir''s final status remains unresolved under UN resolutions, that India administers its portion by force and stands accused of rights violations and a crackdown, and that the territory''s people are entitled to self-determination rather than a settlement imposed from Delhi.',
 'Die Darstellung als umstrittenes Gebiet (pakistanische Presse sowie wohlwollende türkische und Golf-Medien) besagt, dass der endgültige Status Kaschmirs nach UN-Resolutionen ungeklärt bleibt, dass Indien seinen Teil mit Gewalt verwaltet und Vorwürfen von Menschenrechtsverletzungen und Repression ausgesetzt ist, und dass der Bevölkerung Selbstbestimmung zusteht statt einer von Delhi auferlegten Lösung.',
 ARRAY['Dawn','Express Tribune','The Express Tribune','The News International','The Nation','Anadolu Agency','TRT World','Arab News','Daily Sabah'],
 ARRAY['disputed','self-determination','UN resolution','occupied','crackdown','plebiscite','right','solidarity','umstritten','Selbstbestimmung','besetzt'],
 false, ARRAY['ASIA-PAKISTAN'], true),

('kashmir_rights_and_restrictions', 'kashmir_dispute', 3, -1,
 'Rights and restrictions under Indian administration', 'Rechte und Einschränkungen unter indischer Verwaltung',
 'Civil liberties and political normality remain curtailed in the valley',
 'Bürgerrechte und politische Normalität bleiben im Tal eingeschränkt',
 'Rights-focused framing (Western mainstream and wire services) reports the territory as Indian-administered and contested, and concentrates on conditions on the ground: detentions, security operations, curbs on protest and communications, the unrestored statehood of Jammu and Kashmir, and the gap between official accounts of normality and what residents describe.',
 'Die menschenrechtsorientierte Darstellung (westliche Leitmedien und Nachrichtenagenturen) beschreibt das Gebiet als indisch verwaltet und umstritten und konzentriert sich auf die Lage vor Ort: Festnahmen, Sicherheitsoperationen, Einschränkungen von Protest und Kommunikation, die nicht wiederhergestellte Eigenstaatlichkeit von Jammu und Kaschmir sowie die Kluft zwischen offiziellen Normalitätsdarstellungen und den Schilderungen der Bewohner.',
 ARRAY['Reuters','BBC World','Associated Press','Al Jazeera','Deutsche Welle','The Guardian','France 24','France 24 (EN)','Euronews'],
 ARRAY['Indian-administered','detention','crackdown','protest','restriction','statehood','rights','Festnahme','Einschränkung','Rechte'],
 false, ARRAY['ASIA-INDIA','ASIA-PAKISTAN'], true),

-- ===========================================================================
-- india_pakistan_militancy  (95 events)
-- ===========================================================================
('militancy_pakistan_sponsorship', 'india_pakistan_militancy', 1, 2,
 'Pakistani sponsorship of militancy', 'Pakistanische Unterstützung von Militanz',
 'Pakistan shelters and directs the groups that attack India',
 'Pakistan beherbergt und steuert die Gruppen, die Indien angreifen',
 'Sponsorship framing (Indian press) holds that Lashkar-e-Taiba, Jaish-e-Mohammed and allied groups operate from Pakistani soil with official tolerance or direction: investigators trace the Pahalgam attack to handlers across the border, designated figures remain at liberty, and Operation Sindoor is presented as a proportionate response that established a precedent for striking back.',
 'Die Unterstützungs-Darstellung (indische Presse) besagt, dass Lashkar-e-Taiba, Jaish-e-Mohammed und verbündete Gruppen mit offizieller Duldung oder Steuerung von pakistanischem Boden aus operieren: Ermittler führen den Anschlag von Pahalgam auf Hintermänner jenseits der Grenze zurück, gelistete Personen bleiben auf freiem Fuß, und die Operation Sindoor gilt als verhältnismäßige Antwort, die einen Präzedenzfall für Gegenschläge geschaffen hat.',
 ARRAY['Times of India','The Times of India','Hindustan Times','NDTV','The Hindu','Indian Express','The Indian Express','WION','Republic TV','Republic World','DD India'],
 ARRAY['sponsor','shelter','harbour','handler','terror','Lashkar','Sindoor','proxy','FATF','designat','Unterstützung','beherbergt'],
 false, ARRAY['ASIA-INDIA'], true),

('militancy_indian_pretext', 'india_pakistan_militancy', 2, -2,
 'Indian accusations as pretext', 'Indische Vorwürfe als Vorwand',
 'India weaponises unproven allegations to justify pressure and strikes',
 'Indien instrumentalisiert unbewiesene Vorwürfe, um Druck und Angriffe zu rechtfertigen',
 'Pretext framing (Pakistani press) holds that India has never substantiated its allegations over the Pahalgam attack, that the accusations serve domestic politics and a campaign to isolate Pakistan diplomatically, and that Pakistan is itself a principal victim of militant violence rather than its author.',
 'Die Vorwand-Darstellung (pakistanische Presse) besagt, dass Indien seine Vorwürfe zum Anschlag von Pahalgam nie belegt hat, dass die Anschuldigungen der Innenpolitik und einer Kampagne zur diplomatischen Isolierung Pakistans dienen und dass Pakistan selbst ein Hauptopfer militanter Gewalt ist und nicht deren Urheber.',
 ARRAY['Dawn','Express Tribune','The Express Tribune','The News International','The Nation'],
 ARRAY['false flag','propaganda','unsubstantiated','failed to substantiate','weaponisation','baseless','narrative','reject','isolation','haltlos','Vorwand'],
 false, ARRAY['ASIA-PAKISTAN'], true),

-- ===========================================================================
-- indus_water_sharing  (32 events)
-- ===========================================================================
('indus_treaty_obsolete', 'indus_water_sharing', 1, 2,
 'Treaty outdated; India''s rightful use', 'Vertrag überholt; Indiens rechtmäßige Nutzung',
 'The 1960 treaty no longer fits India''s needs and its terms are being revisited',
 'Der Vertrag von 1960 entspricht nicht mehr Indiens Bedarf und wird überprüft',
 'Treaty-revision framing (Indian press) holds that the Indus Waters Treaty was negotiated under conditions that no longer apply, that India''s position is consistent and lawful, and that a state which sponsors cross-border militancy cannot expect the water arrangement to continue unchanged; projects on the western rivers are presented as within India''s entitlement.',
 'Die Vertragsrevisions-Darstellung (indische Presse) besagt, dass der Indus-Wasservertrag unter Bedingungen ausgehandelt wurde, die nicht mehr gelten, dass Indiens Position konsistent und rechtmäßig ist und dass ein Staat, der grenzüberschreitende Militanz unterstützt, keine unveränderte Fortführung der Wasserregelung erwarten kann; Projekte an den westlichen Flüssen gelten als von Indiens Anspruch gedeckt.',
 ARRAY['Times of India','The Times of India','Hindustan Times','NDTV','The Hindu','Indian Express','The Indian Express','WION','Republic TV','Republic World','DD India'],
 ARRAY['outdated','obsolete','consistent','abeyance','renegotiat','rightful','entitle','review','fast-track','überholt','Anspruch'],
 false, ARRAY['ASIA-INDIA'], true),

('indus_water_weaponisation', 'indus_water_sharing', 2, -2,
 'Weaponisation of water', 'Instrumentalisierung des Wassers',
 'Suspending the treaty is coercion against a downstream population',
 'Die Aussetzung des Vertrags ist Zwang gegen eine flussabwärts lebende Bevölkerung',
 'Water-coercion framing (Pakistani press and sympathetic outlets) holds that the treaty remains valid, binding and operative, that no party may suspend it unilaterally, and that restricting or re-timing flows on which a downstream population depends for agriculture and drinking water is an act of coercion; the case is pressed at the UN Security Council and through arbitration.',
 'Die Wasserzwang-Darstellung (pakistanische Presse und wohlwollende Medien) besagt, dass der Vertrag gültig, bindend und in Kraft bleibt, dass keine Partei ihn einseitig aussetzen darf und dass die Beschränkung oder zeitliche Steuerung von Wassermengen, von denen eine flussabwärts lebende Bevölkerung für Landwirtschaft und Trinkwasser abhängt, ein Zwangsakt ist; der Fall wird vor dem UN-Sicherheitsrat und durch Schiedsverfahren verfolgt.',
 ARRAY['Dawn','Express Tribune','The Express Tribune','The News International','The Nation','Anadolu Agency','Arab News','Al Jazeera','TRT World'],
 ARRAY['weaponisation','water aggression','binding','restore','valid','unilateral','lifeline','arbitration','UNSC','Instrumentalisierung','bindend'],
 false, ARRAY['ASIA-PAKISTAN'], true),

-- ===========================================================================
-- balochistan_insurgency  (67 events)
-- framing_required=true on the state card: the A2 toponym gate admits ~15%
-- incident noise (bus crashes, earthquakes datelined Balochistan) and the
-- framing gate is what keeps it off the card.
-- ===========================================================================
('baloch_foreign_backed_insurgency', 'balochistan_insurgency', 1, 2,
 'Foreign-backed insurgency', 'Von außen unterstützter Aufstand',
 'The attacks are externally sponsored terrorism, not a domestic grievance',
 'Die Anschläge sind von außen gesteuerter Terrorismus, keine innenpolitische Beschwerde',
 'State-security framing (Pakistani press) treats the violence in Balochistan as externally sponsored terrorism rather than an indigenous political movement: officials link Baloch Liberation Army attacks to Indian backing, security operations are reported as counter-terrorism with militant death tolls, and the province''s mineral and port development is presented as the answer the militants aim to prevent.',
 'Die staatliche Sicherheitsdarstellung (pakistanische Presse) betrachtet die Gewalt in Belutschistan als von außen gesteuerten Terrorismus und nicht als einheimische politische Bewegung: Behörden bringen Anschläge der Belutschischen Befreiungsarmee mit indischer Unterstützung in Verbindung, Sicherheitsoperationen werden als Terrorbekämpfung mit Opferzahlen unter Militanten dargestellt, und die Erschließung der Bodenschätze und des Hafens der Provinz gilt als jene Antwort, die die Militanten verhindern wollen.',
 ARRAY['Dawn','Express Tribune','The Express Tribune','The News International','The Nation'],
 ARRAY['terrorist','militant','BLA','Indian-backed','India','proxy','security forces','killed','attack','operation','neutralis','Terrorist','Militante'],
 true, ARRAY['ASIA-PAKISTAN'], true),

('baloch_rights_repression', 'balochistan_insurgency', 2, -1,
 'Repression and disappearances', 'Repression und Verschwindenlassen',
 'The state answers Baloch grievances with force and detention',
 'Der Staat begegnet belutschischen Beschwerden mit Gewalt und Haft',
 'Rights framing (Western mainstream and wire services) centres the treatment of Baloch civilians and activists rather than either government''s security case: the life sentence handed to activist Mahrang Baloch, enforced disappearances, restrictions on peaceful protest, and the argument that a province held by force will not be pacified by mining investment.',
 'Die menschenrechtliche Darstellung (westliche Leitmedien und Nachrichtenagenturen) rückt den Umgang mit belutschischen Zivilisten und Aktivisten in den Mittelpunkt statt der Sicherheitsargumente einer Regierung: die lebenslange Haftstrafe für die Aktivistin Mahrang Baloch, Fälle von Verschwindenlassen, Einschränkungen friedlichen Protests und das Argument, dass eine mit Gewalt gehaltene Provinz nicht durch Bergbauinvestitionen befriedet wird.',
 ARRAY['Reuters','BBC World','Associated Press','Deutsche Welle','The Guardian','Al Jazeera','France 24','France 24 (EN)','Euronews'],
 ARRAY['Mahrang','activist','disappearance','rights','sentenced','protest','crackdown','detention','Aktivist','Verschwinden','Rechte'],
 false, ARRAY['ASIA-PAKISTAN'], true),

('baloch_pakistan_internal_failure', 'balochistan_insurgency', 3, -2,
 'Pakistan''s internal failure', 'Pakistans inneres Versagen',
 'The insurgency is Pakistan''s own governance failure, not foreign subversion',
 'Der Aufstand ist Pakistans eigenes Regierungsversagen, keine ausländische Unterwanderung',
 'Internal-failure framing (Indian press) rejects the sponsorship charge and treats the insurgency as evidence of Pakistani state failure: allegations of Indian involvement are dismissed as deflection from internal failings, the province is described as approaching civil war, and the scale of the violence is presented as the consequence of decades of neglect and coercive administration.',
 'Die Darstellung des inneren Versagens (indische Presse) weist den Vorwurf der Unterstützung zurück und betrachtet den Aufstand als Beleg für das Versagen des pakistanischen Staates: Vorwürfe indischer Beteiligung gelten als Ablenkung von inneren Defiziten, die Provinz wird als am Rande eines Bürgerkriegs beschrieben, und das Ausmaß der Gewalt gilt als Folge jahrzehntelanger Vernachlässigung und einer auf Zwang gestützten Verwaltung.',
 ARRAY['Times of India','The Times of India','Hindustan Times','NDTV','The Hindu','Indian Express','The Indian Express','WION','Republic TV','Republic World','DD India'],
 ARRAY['internal failing','baseless','civil war','deflect','reject','failure','unrest','neglect','inneres Versagen','haltlos','Bürgerkrieg'],
 false, ARRAY['ASIA-INDIA'], true)

ON CONFLICT (id) DO UPDATE SET
  fn_id = EXCLUDED.fn_id, display_order = EXCLUDED.display_order,
  stance = EXCLUDED.stance, stance_label_en = EXCLUDED.stance_label_en,
  stance_label_de = EXCLUDED.stance_label_de, name_en = EXCLUDED.name_en,
  name_de = EXCLUDED.name_de, claim_en = EXCLUDED.claim_en, claim_de = EXCLUDED.claim_de,
  publishers = EXCLUDED.publishers, framing_keywords = EXCLUDED.framing_keywords,
  framing_required = EXCLUDED.framing_required, actor_centroids = EXCLUDED.actor_centroids,
  is_active = EXCLUDED.is_active, updated_at = now();

COMMIT;
