-- Horn of Africa: theater-level narrative cards + completeness fields, and the
-- retirement of one atomic narrative that measured out (2026-07-20).
--
-- ---------------------------------------------------------------------------
-- PART 1 -- RETIRE ethiopia_partnership_normalisation.
--
-- Drafted as the +1 counterweight on ethiopia_regional_confrontation and
-- measured at 3 titles, ALL from CGTN, one of which ("Eritrea human trafficking
-- suspect faces verdict in Dutch court") is not even on-frame. Checked against
-- the Australia lesson (a suspiciously LOW count is usually a recall gap from
-- drafting vocabulary out of one camp's headlines only): it is NOT a recall gap
-- here. Every CGTN/China Daily/Global Times/RT/TASS/Xinhua/ANSA title in this
-- atomic's centroid scope carrying its anchors totals 3, all CGTN. The bloc
-- covers Ethiopia as a development and arms partner (Chinese-built wind farm,
-- buses converted to gas, Russian drones, trade tripled) and simply does not
-- take a position on Tigray or Eritrea.
--
-- Per the Cuba lesson (a stance can have NO constituency -- retire it, do not
-- keyword-stuff it), this leaves ethiopia_regional_confrontation with two
-- narratives, BOTH negative (-1 Western alarm, -2 Egyptian revisionism). That
-- asymmetry is the honest finding: no publisher bloc in the ingest set argues
-- Addis Ababa's case on this confrontation. Addis's own denials do exist
-- ("no expansionist intentions", "not being dragged into war") but are carried
-- by publishers already committed to other coalitions, so publisher-based
-- routing cannot isolate them into a card.
--
-- ---------------------------------------------------------------------------
-- PART 2 -- THEATER CARDS (spec §5.5).
--
-- The theater has no fn_anchor bundle and never matches titles. THEATER_ROLLUP_SQL
-- sources each card from the member atomics' title_narratives where
-- sign(atomic.stance) = sign(theater.stance) AND publisher IN the card's list.
-- The count is UNCAPPED over (sign, publisher), so the one hard rule is:
-- publisher-DISJOINT within each sign bucket. Five cards, like south_asia_theater.
--
--   POSITIVE bucket (2 cards, disjoint):
--     +2 new_partnerships     -- Israeli outlets  (pulls somaliland_statehood_earned)
--     +1 regional_stabilisers -- Turkish/Kenyan/Egyptian (pulls somali_state_rebuilding)
--
--   NEGATIVE bucket (3 cards, disjoint):
--     -1 western_alarm        -- Western wires/analysis/UN
--     -2 sovereignty_bloc     -- Arab/Turkish sovereignty-and-non-interference
--     -2 russian_iranian      -- Russian and Iranian state media
--
-- A publisher MAY appear on both a positive and a negative card (opposite signs
-- pull different-signed atomic titles, so nothing double-counts) -- Daily Nation,
-- The Standard, Egypt Today and Al-Ahram all do, deliberately.
--
-- Known and accepted roll-up artifact: the roll-up keys on sign + publisher
-- only, NOT on which atomic. So Anadolu/Al Jazeera titles from
-- ethiopia_renewed_war_alarm (-1) surface under the -2 sovereignty card too.
-- Sign is still correct and framing_keywords rank the samples; this is inherent
-- to the §5.5 design, not a coalition error.
--
-- ---------------------------------------------------------------------------
-- PART 3 -- Completeness fields (spec §6), bilingual, theater + all 3 atomics.
-- Descriptions are NEUTRAL and evergreen per feedback_fn_descriptions_neutral --
-- all framing lives in narratives_v2 above, never here.

BEGIN;

-- ===========================================================================
-- PART 1
-- ===========================================================================
UPDATE narratives_v2
SET is_active = false, updated_at = NOW()
WHERE id = 'ethiopia_partnership_normalisation';

-- ===========================================================================
-- PART 2 -- theater cards
-- ===========================================================================
INSERT INTO narratives_v2 (
    id, fn_id, name_en, name_de, claim_en, claim_de,
    stance, stance_label_en, stance_label_de,
    actor_centroids, publishers, framing_keywords, framing_required,
    display_order, is_active
) VALUES
(
 'horn_new_partnerships', 'horn_africa_theater',
 'New partnerships remaking the Horn',
 'Neue Partnerschaften ordnen das Horn neu',
 'A long-frozen map is finally moving: recognition, basing agreements and minerals deals are creating relationships that the old insistence on inherited borders had blocked for decades.',
 'Eine lange eingefrorene Landkarte kommt in Bewegung: Anerkennung, Stützpunktabkommen und Rohstoffverträge schaffen Beziehungen, die das alte Beharren auf ererbten Grenzen jahrzehntelang verhindert hatte.',
 2, 'Realignment as opportunity', 'Neuordnung als Chance',
 ARRAY['AFRICA-HORN','MIDEAST-ISRAEL'],
 ARRAY['Jerusalem Post','Times of Israel','i24NEWS','Haaretz','News24'],
 ARRAY['recognition','historic','partnership','agreement','minerals','Anerkennung','Partnerschaft'],
 false, 1, true
),
(
 'horn_regional_stabilisers', 'horn_africa_theater',
 'Regional partners rebuilding state capacity',
 'Regionale Partner bauen Staatlichkeit wieder auf',
 'Turkish, Gulf and East African engagement is doing the unglamorous work of reconstituting functioning states in the Horn -- training armies, drilling for energy, reopening borders and trade.',
 'Türkisches, arabisches und ostafrikanisches Engagement leistet die unspektakuläre Arbeit, funktionierende Staaten am Horn wiederherzustellen: Armeen ausbilden, Energie erschließen, Grenzen und Handel wieder öffnen.',
 1, 'Stabilisation through partnership', 'Stabilisierung durch Partnerschaft',
 ARRAY['AFRICA-HORN','MIDEAST-TURKEY','MIDEAST-EGYPT'],
 ARRAY['Anadolu Agency','Daily Sabah','TRT World','Daily Nation','The Standard','Egypt Today','Al-Ahram','ANSA'],
 ARRAY['transformation','renewal','institutions','cooperation','partnership','training','trade','Wiederaufbau','Partnerschaft'],
 false, 2, true
),
(
 'horn_western_alarm', 'horn_africa_theater',
 'Western alarm at fragmentation and famine',
 'Westliche Alarmrufe über Zerfall und Hungersnot',
 'Reporting from Western outlets and UN agencies converges on deterioration: a northern Ethiopian war restarting, famine returning as aid collapses, piracy back at sea, and diplomatic recognition being auctioned for bases and minerals.',
 'Berichte westlicher Medien und von UN-Organisationen laufen auf eine Verschlechterung hinaus: ein wieder aufflammender Krieg im Norden Äthiopiens, eine mit dem Wegbrechen der Hilfe zurückkehrende Hungersnot, erneute Piraterie und diplomatische Anerkennung, die gegen Stützpunkte und Rohstoffe versteigert wird.',
 -1, 'Alarm at deterioration', 'Alarm über die Verschlechterung',
 ARRAY['AFRICA-HORN'],
 ARRAY['Reuters','BBC World','BBC','AFP','AFP Fact Check','Deutsche Welle','The Guardian','Financial Times','Le Monde','UN News','The Economist','Associated Press','France 24','France 24 (EN)','Die Zeit','Der Standard','IISS','Kurier','The Telegraph','Der Spiegel','Bloomberg','CNN','Atlantic Council','Japan Times','Straits Times','DR','Military Times','Defense News'],
 ARRAY['brink','fears','famine','hunger','clashes','piracy','drone','atrocities','civilian','Krieg','Hungersnot','Piraterie'],
 false, 3, true
),
(
 'horn_sovereignty_bloc', 'horn_africa_theater',
 'Sovereignty and non-interference',
 'Souveränität und Nichteinmischung',
 'Arab and Turkish coverage frames the realignment as a set of violations: inherited borders must hold, an outside power cannot confer statehood on a secessionist region, and upstream control of shared water is a standing threat to downstream states.',
 'Arabische und türkische Berichterstattung deutet die Neuordnung als eine Reihe von Verstößen: Ererbte Grenzen müssen halten, eine fremde Macht kann einer sezessionistischen Region keine Staatlichkeit verleihen, und die Kontrolle über gemeinsame Wasserressourcen am Oberlauf bleibt eine Dauerbedrohung für die Anrainer flussabwärts.',
 -2, 'Borders and sovereignty violated', 'Verletzte Grenzen und Souveränität',
 ARRAY['AFRICA-HORN','MIDEAST-EGYPT','MIDEAST-TURKEY'],
 ARRAY['Al Jazeera','Al Arabiya','Arab News','Dawn','The National'],
 ARRAY['sovereignty','territorial integrity','illegal','null and void','condemn','reject','water','dam','Souveränität','verurteilen'],
 false, 4, true
),
(
 'horn_russian_iranian_counter', 'horn_africa_theater',
 'Russian and Iranian counter-framing',
 'Russische und iranische Gegendarstellung',
 'Russian and Iranian state media read the Horn primarily as a theatre of American and Israeli overreach -- airstrikes, blocked peacekeeping funding and coastal basing -- rather than as a set of local disputes.',
 'Russische und iranische Staatsmedien lesen das Horn vorrangig als Schauplatz amerikanischer und israelischer Übergriffigkeit -- Luftangriffe, blockierte Mittel für Friedensmissionen, Stützpunkte an der Küste -- und nicht als eine Reihe lokaler Konflikte.',
 -2, 'Blame external intervention', 'Die Einmischung von außen ist schuld',
 ARRAY['AFRICA-HORN','AMERICAS-USA'],
 ARRAY['RT','Press TV','TASS (EN)','Sputnik'],
 ARRAY['airstrike','intervention','base','imperial','blockade','foreign','Luftangriff','Einmischung'],
 false, 5, true
);

-- ===========================================================================
-- PART 3 -- completeness fields (neutral, evergreen, bilingual)
-- ===========================================================================
UPDATE friction_nodes SET
  description_en = 'The Horn of Africa is being reordered by overlapping disputes: the contested international status of Somaliland, an unresolved confrontation between Ethiopia and its northern and downstream neighbours, and the uneven reconstruction of the Somali state. Outside powers -- Israel, Turkey, Egypt, the Gulf states, the United States and China -- are all party to at least one of them.',
  description_de = 'Das Horn von Afrika wird durch mehrere ineinandergreifende Konflikte neu geordnet: den umstrittenen völkerrechtlichen Status Somalilands, eine ungelöste Konfrontation zwischen Äthiopien und seinen nördlichen wie flussabwärts gelegenen Nachbarn und den ungleichmäßigen Wiederaufbau des somalischen Staates. Auswärtige Mächte -- Israel, die Türkei, Ägypten, die Golfstaaten, die USA und China -- sind an mindestens einem davon beteiligt.',
  editorial_summary_en = 'Coverage in 2026 is dominated by the recognition of Somaliland and the reaction to it, with a renewed war risk in northern Ethiopia and a fragile Somali state as the two other persistent strands.',
  editorial_summary_de = 'Die Berichterstattung des Jahres 2026 wird von der Anerkennung Somalilands und den Reaktionen darauf bestimmt; das erneute Kriegsrisiko im Norden Äthiopiens und ein fragiler somalischer Staat sind die beiden weiteren durchgehenden Stränge.',
  updated_at = NOW()
WHERE id = 'horn_africa_theater';

UPDATE friction_nodes SET
  description_en = 'Somaliland declared independence from Somalia in 1991 and has governed itself since without broad international recognition. Israel''s recognition and exchange of ambassadors, alongside discussions of port access, critical minerals and military basing, has made its status an active international dispute involving Somalia, the African Union, Arab and Muslim states, Turkey and the United States.',
  description_de = 'Somaliland erklärte 1991 seine Unabhängigkeit von Somalia und regiert sich seither selbst, ohne breite internationale Anerkennung. Israels Anerkennung und der Austausch von Botschaftern haben den Status -- zusammen mit Gesprächen über Hafenzugang, kritische Rohstoffe und Militärstützpunkte -- zu einem aktiven internationalen Konflikt gemacht, an dem Somalia, die Afrikanische Union, arabische und muslimische Staaten, die Türkei und die USA beteiligt sind.',
  editorial_summary_en = 'The single largest strand of Horn coverage in 2026, and the one that pulls the most outside powers in.',
  editorial_summary_de = 'Der mit Abstand größte Berichterstattungsstrang am Horn im Jahr 2026 -- und derjenige, der die meisten auswärtigen Mächte einbezieht.',
  updated_at = NOW()
WHERE id = 'somaliland_recognition_contest';

UPDATE friction_nodes SET
  description_en = 'Ethiopia faces simultaneous disputes on several fronts: the unravelling of the Pretoria settlement that ended the Tigray war, accusations of Eritrean troop movements across the northern border, a long-running disagreement with Egypt over control of the Nile dam, and Addis Ababa''s stated pursuit of sovereign access to the sea.',
  description_de = 'Äthiopien steht gleichzeitig an mehreren Fronten in Konflikten: dem Zerfall des Abkommens von Pretoria, das den Tigray-Krieg beendete, Vorwürfen eritreischer Truppenbewegungen über die Nordgrenze, einer langjährigen Auseinandersetzung mit Ägypten über die Kontrolle des Nilstaudamms und dem erklärten Streben Addis Abebas nach einem souveränen Zugang zum Meer.',
  editorial_summary_en = 'Tigray and Eritrea are one fused story in the 2026 record, not two; the Egyptian dimension has shifted from water alone to regional alignment.',
  editorial_summary_de = 'Tigray und Eritrea sind im Material von 2026 eine zusammenhängende Geschichte, nicht zwei; die ägyptische Dimension hat sich vom reinen Wasserstreit zur regionalen Bündnispolitik verlagert.',
  updated_at = NOW()
WHERE id = 'ethiopia_regional_confrontation';

UPDATE friction_nodes SET
  description_en = 'The Somali federal government is contesting control of its territory and coastline simultaneously: an insurgency by al-Shabaab, a peacekeeping mission facing a funding crisis, disputed federal elections that have produced armed clashes in Mogadishu, and a resurgence of piracy off the eastern seaboard. Turkey, the United States, Egypt and Gulf states are all engaged.',
  description_de = 'Die somalische Bundesregierung ringt gleichzeitig um die Kontrolle über ihr Territorium und ihre Küste: ein Aufstand von al-Shabaab, eine Friedensmission in der Finanzierungskrise, umstrittene Bundeswahlen mit bewaffneten Zusammenstößen in Mogadischu und ein Wiederaufleben der Piraterie vor der Ostküste. Die Türkei, die USA, Ägypten und Golfstaaten sind engagiert.',
  editorial_summary_en = 'Deliberately a broad slice: insurgency, the AU mission, the election crisis and piracy are one story about state capacity, not four separate ones.',
  editorial_summary_de = 'Bewusst breit geschnitten: Aufstand, AU-Mission, Wahlkrise und Piraterie sind eine einzige Geschichte über staatliche Handlungsfähigkeit, nicht vier getrennte.',
  updated_at = NOW()
WHERE id = 'somalia_state_security';

COMMIT;
