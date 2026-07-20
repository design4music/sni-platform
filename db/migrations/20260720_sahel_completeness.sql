-- Sahel theater: bilingual completeness fields (spec §6, 2026-07-20).
-- name_de / description_en / description_de / editorial_summary_en+de on the
-- theater and all five atomics.
--
-- Descriptions are NEUTRAL and EVERGREEN (feedback_fn_descriptions_neutral):
-- they say what the friction node covers, not who is right. All framing lives
-- in narratives_v2. Editorial summaries may state measured facts of the current
-- period but must not adopt a camp's language.
--
-- Terminology care: the armed groups are named by their own designations
-- (JNIM, ISWAP, Boko Haram) or as "armed groups" / "jihadist groups" -- the
-- descriptor those groups use of themselves and that reporting uses neutrally.
-- The Tuareg formations are "separatist" / "autonomy-seeking", not "terrorist",
-- which is one camp's designation and belongs in its narrative.

BEGIN;

-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
    name_de = 'Militärische Übergangszone Sahel',
    description_en = 'The Sahel and Lake Chad basin as a single conflict zone: jihadist insurgency, Tuareg separatism in northern Mali, military governments consolidating power after successive coups, the competition to replace France as the region''s security patron, and the rupture of relations with Paris.',
    description_de = 'Die Sahelzone und das Tschadseebecken als zusammenhängende Konfliktzone: dschihadistischer Aufstand, Tuareg-Separatismus in Nordmali, Militärregierungen, die nach aufeinanderfolgenden Putschen ihre Macht festigen, der Wettstreit um Frankreichs Nachfolge als Sicherheitspatron der Region und der Bruch der Beziehungen zu Paris.',
    editorial_summary_en = 'Coverage in the first half of 2026 is dominated by a single sequence: a coordinated JNIM and Tuareg offensive that killed Mali''s defence minister, blockaded Bamako and took Kidal, while Russia''s Africa Corps withdrew from the town it had helped hold. Around it sit the Lake Chad war against Boko Haram and ISWAP, party dissolutions in Burkina Faso and Niger''s exit from the ICC, and Burkina Faso''s severing of diplomatic relations with France.',
    editorial_summary_de = 'Die Berichterstattung im ersten Halbjahr 2026 wird von einer einzigen Abfolge bestimmt: eine koordinierte Offensive von JNIM und Tuareg-Verbänden, die Malis Verteidigungsminister tötete, Bamako blockierte und Kidal einnahm, während sich Russlands Africa Corps aus der Stadt zurückzog, die es hatte halten helfen. Daneben stehen der Krieg am Tschadsee gegen Boko Haram und ISWAP, Parteiauflösungen in Burkina Faso, Nigers Austritt aus dem Internationalen Strafgerichtshof und der Abbruch der diplomatischen Beziehungen Burkina Fasos zu Frankreich.',
    updated_at = NOW()
WHERE id = 'sahel_theater';

-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
    name_de = 'Dschihadistischer Aufstand und territorialer Wettstreit',
    description_en = 'Operations by jihadist armed groups across the Sahel and the Lake Chad basin -- JNIM, Islamic State affiliates, Boko Haram and ISWAP -- and the counterinsurgency campaigns waged against them by national armies and their foreign partners, including the civilian toll of both.',
    description_de = 'Operationen dschihadistischer bewaffneter Gruppen in der Sahelzone und im Tschadseebecken -- JNIM, Ableger des Islamischen Staats, Boko Haram und ISWAP -- sowie die Aufstandsbekämpfung durch nationale Armeen und ihre ausländischen Partner, einschließlich der zivilen Opfer beider Seiten.',
    editorial_summary_en = 'The largest node in the theater. In 2026 JNIM moved from rural control to pressure on capitals, blockading Bamako''s fuel supply and mounting coordinated raids on multiple cities; Islamic State claimed an assault on Niamey''s airport. In the Lake Chad basin, Boko Haram and ISWAP continued mass abductions and attacks on military positions. Rights monitors and Amnesty documented large civilian death tolls from army airstrikes on both sides of the Nigeria-Sahel divide.',
    editorial_summary_de = 'Der größte Knoten des Theaters. 2026 ging JNIM von der Kontrolle ländlicher Räume zum Druck auf Hauptstädte über, blockierte Bamakos Treibstoffversorgung und führte koordinierte Angriffe auf mehrere Städte; der Islamische Staat reklamierte einen Angriff auf den Flughafen von Niamey. Im Tschadseebecken setzten Boko Haram und ISWAP Massenentführungen und Angriffe auf Militärstellungen fort. Menschenrechtsbeobachter und Amnesty dokumentierten hohe zivile Opferzahlen durch Luftangriffe der Armeen auf beiden Seiten der nigerianisch-sahelischen Grenze.',
    updated_at = NOW()
WHERE id = 'sahel_jihadist_insurgency';

-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
    name_de = 'Tuareg-Separatismus und die Frage Nordmalis',
    description_en = 'The unresolved status of northern Mali and the Tuareg-led armed movements that claim it, including their control of Kidal and their relations with both the central government and the jihadist groups operating in the same territory.',
    description_de = 'Der ungeklärte Status Nordmalis und die tuareg-geführten bewaffneten Bewegungen, die ihn beanspruchen -- einschließlich ihrer Kontrolle über Kidal und ihres Verhältnisses sowohl zur Zentralregierung als auch zu den im selben Gebiet operierenden dschihadistischen Gruppen.',
    editorial_summary_en = 'Tuareg formations took full control of Kidal in 2026 after an arrangement under which Russian forces withdrew from the town, and declared that the government in Bamako would fall. They claimed coordinated attacks jointly with JNIM -- a tactical alignment between a secular separatist movement and an al-Qaeda affiliate that both Bamako and Moscow cite as grounds to treat the two as one.',
    editorial_summary_de = 'Tuareg-Verbände übernahmen 2026 die vollständige Kontrolle über Kidal, nachdem sich russische Kräfte im Rahmen einer Vereinbarung aus der Stadt zurückgezogen hatten, und erklärten, die Regierung in Bamako werde fallen. Sie reklamierten koordinierte Angriffe gemeinsam mit JNIM -- eine taktische Annäherung zwischen einer säkularen Separatistenbewegung und einem al-Qaida-Ableger, die Bamako wie Moskau als Grund anführen, beide als eines zu behandeln.',
    updated_at = NOW()
WHERE id = 'sahel_tuareg_separatism';

-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
    name_de = 'Junta-Konsolidierung und souveränistische Neuausrichtung',
    description_en = 'How the military governments that took power in Mali, Burkina Faso, Niger and Guinea consolidate control -- party bans, media suspensions, treatment of international bodies and postponed transitions -- and the sovereigntist doctrine they advance to justify it.',
    description_de = 'Wie die Militärregierungen, die in Mali, Burkina Faso, Niger und Guinea die Macht übernahmen, ihre Kontrolle festigen -- Parteiverbote, Mediensperren, der Umgang mit internationalen Institutionen und verschobene Übergänge -- und die souveränistische Doktrin, mit der sie dies begründen.',
    editorial_summary_en = 'Burkina Faso dissolved all political parties and Guinea dissolved forty, including the main opposition. Niger withdrew from the International Criminal Court, describing it as an instrument of neocolonial repression, and suspended French media outlets. The UN human-rights office in Burkina Faso closed after being suspended. Mali''s leadership assumed the defence portfolio directly after the minister was killed.',
    editorial_summary_de = 'Burkina Faso löste sämtliche politischen Parteien auf, Guinea vierzig, darunter die wichtigste Opposition. Niger trat aus dem Internationalen Strafgerichtshof aus, den es als Instrument neokolonialer Repression bezeichnete, und suspendierte französische Medien. Das UN-Menschenrechtsbüro in Burkina Faso schloss nach seiner Suspendierung. Malis Führung übernahm das Verteidigungsressort direkt, nachdem der Minister getötet worden war.',
    updated_at = NOW()
WHERE id = 'sahel_junta_consolidation';

-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
    name_de = 'Wettstreit um die Sicherheitspatronage',
    description_en = 'The competition to supply the Sahel states with security assistance after the departure of French and UN forces: Russia''s Africa Corps, Turkish drones and training, renewed United States engagement, and Moroccan offers of Atlantic access to the landlocked members of the Alliance of Sahel States.',
    description_de = 'Der Wettstreit um Sicherheitsunterstützung für die Sahelstaaten nach dem Abzug französischer und UN-Kräfte: Russlands Africa Corps, türkische Drohnen und Ausbildung, erneutes Engagement der Vereinigten Staaten sowie marokkanische Angebote eines Atlantikzugangs für die Binnenstaaten der Allianz der Sahelstaaten.',
    editorial_summary_en = 'The smallest node in the theater by volume but a persistent one. Africa Corps confirmed its withdrawal from Kidal, took casualties in rebel attacks and was reported retreating under jihadist pressure, while Moscow said its forces would stay in Mali and had helped stop an attempted coup. Niger''s president was received in Ankara as Türkiye expanded its training and drone footprint.',
    editorial_summary_de = 'Der volumenmäßig kleinste, aber beständige Knoten des Theaters. Das Africa Corps bestätigte seinen Rückzug aus Kidal, erlitt Verluste bei Rebellenangriffen und wich Berichten zufolge unter dschihadistischem Druck zurück, während Moskau erklärte, seine Kräfte blieben in Mali und hätten geholfen, einen Putschversuch zu stoppen. Nigers Präsident wurde in Ankara empfangen, während die Türkei ihre Ausbildungs- und Drohnenpräsenz ausweitete.',
    updated_at = NOW()
WHERE id = 'sahel_security_patron_contest';

-- ---------------------------------------------------------------------------
UPDATE friction_nodes SET
    name_de = 'Bruch mit Frankreich',
    description_en = 'The breakdown of relations between France and the Sahel states: severed diplomatic ties, expelled or withdrawn diplomats, prosecutions of French nationals on security charges, and the colonial-legacy arguments advanced on both sides.',
    description_de = 'Der Zusammenbruch der Beziehungen zwischen Frankreich und den Sahelstaaten: abgebrochene diplomatische Beziehungen, ausgewiesene oder abgezogene Diplomaten, Strafverfahren gegen französische Staatsangehörige wegen Sicherheitsdelikten und die auf beiden Seiten vorgebrachten Argumente zum kolonialen Erbe.',
    editorial_summary_en = 'Burkina Faso broke off diplomatic relations with France and Paris called the move hostile; France withdrew its diplomats. A French intelligence officer was sentenced to twenty years in Bamako for offences against state security, a charge Paris rejects. Niger''s leadership publicly blamed France for the jihadist assault on Niamey airport, and France advised its nationals to leave Mali.',
    editorial_summary_de = 'Burkina Faso brach die diplomatischen Beziehungen zu Frankreich ab; Paris nannte den Schritt feindselig und zog seine Diplomaten ab. Ein französischer Nachrichtendienstoffizier wurde in Bamako wegen Straftaten gegen die Staatssicherheit zu zwanzig Jahren verurteilt -- ein Vorwurf, den Paris zurückweist. Nigers Führung machte Frankreich öffentlich für den dschihadistischen Angriff auf den Flughafen von Niamey verantwortlich, und Frankreich empfahl seinen Staatsangehörigen, Mali zu verlassen.',
    updated_at = NOW()
WHERE id = 'sahel_france_rupture';

COMMIT;
