-- Tighten FN2's topic_keywords to truly Iran-nuclear scope, and populate
-- the new publishers column on each narrative with editorially-curated
-- publisher → stance assignments.
-- 2026-05-07
--
-- Pairs with the publisher-stance bucketing rewrite of the bootstrap.
-- See db/migrations/20260507_friction_nodes_v2_publishers_col.sql for
-- column rationale.
--
-- Curation principle: each narrative's publisher list reflects the outlet's
-- KNOWN editorial stance on Iran nuclear specifically. Wire services
-- (Reuters/AP/AFP) and Indian outlets are intentionally OMITTED — their
-- coverage on this FN is more neutral/pragmatic and doesn't cleanly map.
-- They can be revisited with stance data from outlet_entity_stance later.

BEGIN;

-- ---------------------------------------------------------------------
-- 1. Tighten FN2 topic_keywords (drop generic "uranium"/"enrichment"/
--    "centrifuge"/"weapons-grade" alone — those caught NK/general nuclear
--    coverage. Keep only Iran-nuclear-specific terms.)
-- ---------------------------------------------------------------------
UPDATE friction_nodes
SET topic_keywords = ARRAY[
    -- Sites (Iran-specific)
    'Natanz',
    'Fordow',
    'Bushehr',
    'Arak',
    -- Iran + nuclear paired phrases
    'Iran nuclear',
    'Iran''s nuclear',
    'Iranian nuclear',
    'Tehran nuclear',
    'Tehran''s nuclear',
    'Iran atomic',
    'Iran''s atomic',
    'Iranian atomic',
    'Iran enrichment',
    'Iran''s enrichment',
    'Iranian enrichment',
    'enrichment in Iran',
    'enriched uranium' ,        -- almost always Iran-context in current cycle
    'JCPOA',                    -- always Iran
    'IAEA Iran',
    'Iran IAEA',
    -- Programs / talks / officials (Iran-specific)
    'Iran nuclear chief',
    'Iran nuclear talks',
    'US-Iran nuclear',
    'Iran-US nuclear',
    'Iran nuclear deal',
    'Iran nuclear program',
    'Iranian nuclear program',
    'Iran nuclear sites',
    'Iran''s nuclear sites',
    'Iran nuclear facility',
    'Iran nuclear facilities',
    'Iran''s nuclear facilities',
    'attacks on Iran''s nuclear',
    'strike on Iran''s nuclear',
    'strike on Natanz',
    'attack on Natanz',
    -- Tech (paired with Iran context)
    'Iran centrifuge',
    'Iran''s centrifuge'
],
updated_at = now()
WHERE id = 'iran_nuclear_program';

-- ---------------------------------------------------------------------
-- 2. EXISTENTIAL THREAT — US conservative + mainstream + Israeli outlets.
--    These cover Iran nuclear as a "problem to deny capability" through
--    sanctions, strikes, or denial.
-- ---------------------------------------------------------------------
UPDATE narratives_v2
SET publishers = ARRAY[
    -- US (conservative + mainstream both align on "Iran shouldn't have nuke")
    'Fox News',
    'Wall Street Journal',
    'WSJ',
    'New York Post',
    'CNN',
    'New York Times',
    'The New York Times',
    'Washington Post',
    'The Washington Post',
    'Bloomberg',
    'NPR',
    'MSNBC',
    -- Israeli (all generally critical of Iran nuclear, varying intensity)
    'Jerusalem Post',
    'The Jerusalem Post',
    'Times of Israel',
    'Haaretz',
    'i24NEWS',
    'JNS',
    'Israel Hayom',
    'Ynet',
    -- Pro-Western / pro-Ukraine alignment
    'Kyiv Post'
],
updated_at = now()
WHERE id = 'west_iran_nuclear_threat';

-- ---------------------------------------------------------------------
-- 3. SOVEREIGN RIGHT — Iranian state media + Iran-aligned regional voices.
-- ---------------------------------------------------------------------
UPDATE narratives_v2
SET publishers = ARRAY[
    'Press TV',
    'IRNA',
    'Fars News',
    'Fars News Agency',
    'Tasnim News',
    'Mehr News',
    'Al Manar',
    'Al Mayadeen'
],
updated_at = now()
WHERE id = 'iran_nuclear_sovereign_right';

-- ---------------------------------------------------------------------
-- 4. EU DIPLOMACY — E3 + EU mainstream + UK + EU-institutional outlets.
--    Stance: preserve diplomacy, snapback, JCPOA-plus.
-- ---------------------------------------------------------------------
UPDATE narratives_v2
SET publishers = ARRAY[
    -- UK
    'BBC',
    'BBC World',
    'The Guardian',
    'Financial Times',
    'The Independent',
    'The Times',
    -- France
    'Le Monde',
    'Le Figaro',
    'France 24',
    'France 24 (EN)',
    'RFI',
    'Liberation',
    -- Germany
    'FAZ',
    'Frankfurter Allgemeine Zeitung',
    'Suddeutsche Zeitung',
    'Deutsche Welle',
    'DW',
    'Der Spiegel',
    'Spiegel',
    'Tagesspiegel',
    'Handelsblatt',
    -- Italy
    'ANSA',
    'La Repubblica',
    'Corriere della Sera',
    'La Stampa',
    'Il Sole 24 Ore',
    -- Spain
    'El Pais',
    'El País',
    'El Mundo',
    'ABC España',
    'La Vanguardia',
    -- EU institutional
    'Euronews',
    'Politico Europe',
    'Politico EU',
    'Euractiv',
    'EUobserver'
],
updated_at = now()
WHERE id = 'eu_diplomatic_preservation_norm';

-- ---------------------------------------------------------------------
-- 5. MULTIPOLAR / ANTI-HEGEMONIC — Russian + Chinese state + Iran-friendly
--    anti-Western outlets.
-- ---------------------------------------------------------------------
UPDATE narratives_v2
SET publishers = ARRAY[
    -- Russia
    'RT',
    'RT News',
    'TASS',
    'TASS (EN)',
    'Sputnik',
    'RIA Novosti',
    -- China
    'Xinhua',
    'Global Times',
    'China Daily',
    'CGTN',
    -- Anti-Western Pan-Arab / Latin American / others
    'Al Jazeera',
    'Al Jazeera English',
    'TeleSUR',
    'Granma',
    -- Pakistan (often Iran-friendly anti-Western framing)
    'Express Tribune',
    'The Express Tribune',
    'Dawn'
],
updated_at = now()
WHERE id = 'multipolar_systemic_alternative';

-- ---------------------------------------------------------------------
-- 6. GULF HEDGING — Saudi/UAE/Egypt/Turkish outlets in mediator mode.
--    Stance: regional de-escalation, Saudi-Iran rapprochement, IMEC.
-- ---------------------------------------------------------------------
UPDATE narratives_v2
SET publishers = ARRAY[
    -- Saudi
    'Arab News',
    'Saudi Gazette',
    'Al Arabiya',
    'Al Arabiya English',
    'Asharq Al-Awsat',
    -- UAE
    'The National',
    'Khaleej Times',
    'Gulf News',
    'Emirates News Agency',
    'WAM',
    -- Egypt
    'Al-Ahram',
    'Al Ahram',
    'Egypt Today',
    'Daily News Egypt',
    -- Turkey (regional mediator role)
    'Anadolu Agency',
    'Anadolu Ajansı',
    'Daily Sabah',
    'TRT World',
    'Hurriyet',
    'Hurriyet Daily News'
],
updated_at = now()
WHERE id = 'gulf_regional_de_escalation';

COMMIT;
