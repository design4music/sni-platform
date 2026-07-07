-- LatAm theater split: retire the continent-wide grab-bag latam_theater,
-- replace with six conflict-system theaters at the same granularity as
-- other continents. Current as of 2026-07: post-intervention Venezuela
-- (Maduro captured Jan 2026, Operation Absolute Resolve), US-Mexico
-- cartel/military-pressure standoff, Panama Canal ports seizure (Feb 2026,
-- Hutchison eviction, Chinese retaliation threats), Haiti gang collapse.
-- Runs AFTER 20260707_fn_id_naming.sql (uses renamed cuba_*/latam_* ids).
-- NOT yet on live (latam_theater is local-only); safe to restructure.
-- New atomics need fn_anchor bundles (extractor workflow) before they
-- accumulate events -- tracked as a post-merge step.

BEGIN;

-- 1. Retire the grab-bag.
UPDATE friction_nodes SET is_active = false, updated_at = now()
  WHERE id = 'latam_theater';

-- 2. Reframe the Venezuela atomics post-intervention.
UPDATE friction_nodes SET
  name_en = 'Venezuela post-intervention transition',
  name_de = 'Venezuelas Uebergang nach der Intervention',
  description_en = 'The contested transition after Maduro''s capture: acting-government legitimacy, opposition claims, and the struggle over Venezuela''s political future.',
  description_de = 'Der umkaempfte Uebergang nach Maduros Gefangennahme: Legitimitaet der amtierenden Regierung, Ansprueche der Opposition und der Kampf um Venezuelas politische Zukunft.',
  updated_at = now()
WHERE id = 'venezuela_political_transition';

UPDATE friction_nodes SET
  name_en = 'US intervention and coercion of Venezuela',
  name_de = 'US-Intervention und Druck auf Venezuela',
  description_en = 'The US posture after Operation Absolute Resolve: military presence, oil-for-access arrangements, recognition politics and the international-law dispute.',
  description_de = 'Die US-Haltung nach der Operation Absolute Resolve: Militaerpraesenz, Oel-gegen-Zugang-Vereinbarungen, Anerkennungspolitik und der voelkerrechtliche Streit.',
  updated_at = now()
WHERE id = 'us_venezuela_relations';

-- 3. New atomic FNs (Mexico, Panama, Haiti).
INSERT INTO friction_nodes
  (id, name_en, name_de, description_en, description_de,
   centroid_ids, is_active, fn_type, scope, primary_target)
VALUES
(
  'mexico_cartel_war',
  'Cartel war and state response',
  'Kartellkrieg und staatliche Antwort',
  'Major operations against CJNG and Sinaloa, cartel-leader captures and deaths, and the militarisation of Mexican internal security.',
  'Grossoperationen gegen CJNG und Sinaloa, Festnahmen und Tode von Kartellfuehrern und die Militarisierung der inneren Sicherheit Mexikos.',
  ARRAY['AMERICAS-MEXICO','AMERICAS-USA'], true, 'atomic', 'regional', 'AMERICAS-MEXICO'
),
(
  'us_mexico_military_pressure',
  'US military-action pressure and Mexican sovereignty',
  'US-Militaerdruck und mexikanische Souveraenitaet',
  'US demands for direct military action against cartels on Mexican soil -- strikes, joint raids, an AUMF debate -- against Mexico''s sovereignty red line.',
  'US-Forderungen nach direkten Militaeraktionen gegen Kartelle auf mexikanischem Boden -- Schlaege, gemeinsame Razzien, eine AUMF-Debatte -- gegen Mexikos rote Linie der Souveraenitaet.',
  ARRAY['AMERICAS-MEXICO','AMERICAS-USA'], true, 'atomic', 'regional', 'AMERICAS-MEXICO'
),
(
  'us_mexico_trade_border',
  'Tariffs, border and migration leverage',
  'Zoelle, Grenze und Migration als Druckmittel',
  'Tariff threats, border enforcement and migration policy as bargaining instruments in the US-Mexico relationship.',
  'Zolldrohungen, Grenzsicherung und Migrationspolitik als Verhandlungsinstrumente in den Beziehungen zwischen USA und Mexiko.',
  ARRAY['AMERICAS-MEXICO','AMERICAS-USA'], true, 'atomic', 'regional', 'AMERICAS-MEXICO'
),
(
  'panama_ports_dispute',
  'Canal ports dispute and Hutchison eviction',
  'Streit um die Kanalhaefen und Hutchison-Verdraengung',
  'Panama''s seizure of the Balboa and Cristobal terminals from CK Hutchison after a Supreme Court ruling, and Beijing''s threatened retaliation.',
  'Panamas Uebernahme der Terminals Balboa und Cristobal von CK Hutchison nach einem Urteil des Obersten Gerichts und Pekings angedrohte Vergeltung.',
  ARRAY['AMERICAS-CENTRAL-AMERICA','AMERICAS-USA','ASIA-CHINA'], true, 'atomic', 'regional', 'AMERICAS-CENTRAL-AMERICA'
),
(
  'panama_canal_transit_security',
  'Canal transit security and neutrality',
  'Transitsicherheit und Neutralitaet des Kanals',
  'Ship-detention accusations, neutrality-treaty politics and the canal''s exposure to US-China escalation and drought-driven capacity limits.',
  'Vorwuerfe von Schiffsfestsetzungen, Neutralitaetsvertragspolitik und die Anfaelligkeit des Kanals fuer US-chinesische Eskalation und duerrebedingte Kapazitaetsgrenzen.',
  ARRAY['AMERICAS-CENTRAL-AMERICA','AMERICAS-USA','ASIA-CHINA'], true, 'atomic', 'regional', 'AMERICAS-CENTRAL-AMERICA'
),
(
  'haiti_gang_control',
  'Gang control of Port-au-Prince',
  'Bandenkontrolle ueber Port-au-Prince',
  'Armed gangs control most of the capital and are expanding into other departments: killings, kidnapping, sexual violence and mass displacement.',
  'Bewaffnete Banden kontrollieren den Grossteil der Hauptstadt und dehnen sich in weitere Departements aus: Toetungen, Entfuehrungen, sexuelle Gewalt und Massenvertreibung.',
  ARRAY['AMERICAS-CARIBBEAN'], true, 'atomic', 'regional', 'AMERICAS-CARIBBEAN'
),
(
  'haiti_international_mission',
  'International stabilisation mission politics',
  'Politik der internationalen Stabilisierungsmission',
  'UN Security Council wrangling, mission funding and force generation, and the politics of who stabilises Haiti and on what mandate.',
  'Ringen im UN-Sicherheitsrat, Missionsfinanzierung und Truppenstellung sowie die Politik darum, wer Haiti mit welchem Mandat stabilisiert.',
  ARRAY['AMERICAS-CARIBBEAN','AMERICAS-USA'], true, 'atomic', 'regional', 'AMERICAS-CARIBBEAN'
)
ON CONFLICT (id) DO NOTHING;

-- 4. New theaters.
INSERT INTO friction_nodes
  (id, name_en, name_de, description_en, description_de, centroid_ids,
   is_active, fn_type, scope, primary_target, member_fn_ids,
   affected_asset_ids, anchor_point)
VALUES
(
  'venezuela_theater',
  'Venezuela after the US intervention',
  'Venezuela nach der US-Intervention',
  'The US capture of Maduro opened a contested transition: acting-government legitimacy, oil restart under US terms, the legality dispute, and the unresolved Essequibo claim.',
  'Die US-Gefangennahme Maduros eroeffnete einen umkaempften Uebergang: Legitimitaet der amtierenden Regierung, Oel-Neustart zu US-Bedingungen, der Rechtsstreit und der ungeloeste Essequibo-Anspruch.',
  ARRAY['AMERICAS-VENEZUELA','AMERICAS-USA','AMERICAS-COLOMBIA','AMERICAS-BRAZIL','AMERICAS-GUYANA'],
  true, 'theater', 'regional', 'AMERICAS-VENEZUELA',
  ARRAY['venezuela_political_transition','us_venezuela_relations','venezuela_sanctions_oil','essequibo_dispute'],
  ARRAY['orinoco_heavy_oil_belt','paraguana_refining_center','stabroek_block'],
  '{"type":"Point","coordinates":[-66.9,10.5]}'::jsonb
),
(
  'mexico_theater',
  'US-Mexico security and trade confrontation',
  'Sicherheits- und Handelskonfrontation USA-Mexiko',
  'Washington''s push for direct military action against cartels, tariff leverage and border politics meet Mexico''s defence of sovereignty.',
  'Washingtons Druck fuer direkte Militaeraktionen gegen Kartelle, Zolldruck und Grenzpolitik treffen auf Mexikos Verteidigung der Souveraenitaet.',
  ARRAY['AMERICAS-MEXICO','AMERICAS-USA'],
  true, 'theater', 'regional', 'AMERICAS-MEXICO',
  ARRAY['mexico_cartel_war','us_mexico_military_pressure','us_mexico_trade_border'],
  ARRAY['manzanillo_mx_port','cantarell_field','ku_maloob_zaap_field'],
  '{"type":"Point","coordinates":[-99.1,19.4]}'::jsonb
),
(
  'panama_canal_theater',
  'US-China confrontation over the Panama Canal',
  'US-chinesische Konfrontation um den Panamakanal',
  'Port seizures, Chinese retaliation threats and transit politics have made the canal a front line of hemispheric great-power competition.',
  'Hafenuebernahmen, chinesische Vergeltungsdrohungen und Transitpolitik haben den Kanal zu einer Frontlinie des hemisphaerischen Grossmachtwettbewerbs gemacht.',
  ARRAY['AMERICAS-CENTRAL-AMERICA','AMERICAS-USA','ASIA-CHINA'],
  true, 'theater', 'regional', 'AMERICAS-CENTRAL-AMERICA',
  ARRAY['panama_ports_dispute','panama_canal_transit_security'],
  ARRAY['panama_canal','colon_port'],
  '{"type":"Point","coordinates":[-79.6,9.0]}'::jsonb
),
(
  'cuba_theater',
  'Cuba under maximum pressure',
  'Kuba unter Maximaldruck',
  'Embargo tightening, migration exodus and regime survival under intensified US pressure.',
  'Verschaerftes Embargo, Massenabwanderung und Regimeueberleben unter erhoehtem US-Druck.',
  ARRAY['AMERICAS-CUBA','AMERICAS-USA'],
  true, 'theater', 'regional', 'AMERICAS-CUBA',
  ARRAY['cuba_embargo_sanctions','cuba_migration_exodus','cuba_regime_survival'],
  ARRAY[]::text[],
  '{"type":"Point","coordinates":[-82.4,23.1]}'::jsonb
),
(
  'latam_hemispheric_theater',
  'US-China competition for Latin America',
  'US-chinesischer Wettbewerb um Lateinamerika',
  'Infrastructure finance, trade dependence and critical-minerals access as arenas of US-China competition across the region.',
  'Infrastrukturfinanzierung, Handelsabhaengigkeit und Zugang zu kritischen Mineralien als Arenen des US-chinesischen Wettbewerbs in der Region.',
  ARRAY['AMERICAS-USA','ASIA-CHINA','AMERICAS-BRAZIL','AMERICAS-CHILE','AMERICAS-ARGENTINA','AMERICAS-PERU','AMERICAS-BOLIVIA'],
  true, 'theater', 'regional', 'AMERICAS-BRAZIL',
  ARRAY['latam_infrastructure_influence','latam_trade_dependence','latam_lithium_minerals'],
  ARRAY['atacama_lithium_triangle','salar_de_uyuni_lithium','chilean_copper_belt','southern_peru_copper_belt'],
  '{"type":"Point","coordinates":[-47.9,-15.8]}'::jsonb
),
(
  'haiti_theater',
  'Haiti state collapse',
  'Haitis Staatszerfall',
  'Gang control of the capital, mass displacement and the politics of international stabilisation.',
  'Bandenherrschaft ueber die Hauptstadt, Massenvertreibung und die Politik internationaler Stabilisierung.',
  ARRAY['AMERICAS-CARIBBEAN','AMERICAS-USA'],
  true, 'theater', 'regional', 'AMERICAS-CARIBBEAN',
  ARRAY['haiti_gang_control','haiti_international_mission'],
  ARRAY[]::text[],
  '{"type":"Point","coordinates":[-72.3,18.5]}'::jsonb
)
ON CONFLICT (id) DO NOTHING;

COMMIT;
