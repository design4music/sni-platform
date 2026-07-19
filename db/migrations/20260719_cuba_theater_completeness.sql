-- Cuba theater: bilingual completeness fields (spec §6), 2026-07-19.
--
-- description_* and editorial_summary_* for the theater and all five active
-- atomics. Descriptions are NEUTRAL and EVERGREEN -- they state what the node
-- covers, not who is right. All stance framing lives in narratives_v2.
--
-- cuba_migration_exodus is deactivated and deliberately left untouched.

BEGIN;

UPDATE friction_nodes SET
 description_en = 'The confrontation between the United States and Cuba, comprising the US sanctions and blockade instruments applied to the island, the energy and humanitarian crisis on it, the outside states supplying it, the threat of US military action, and the Cuban government''s internal position.',
 description_de = 'Die Konfrontation zwischen den Vereinigten Staaten und Kuba: die US-Sanktions- und Blockadeinstrumente gegen die Insel, die dortige Energie- und humanitäre Krise, die Staaten, die sie beliefern, die Drohung mit US-Militäraktionen und die innere Lage der kubanischen Regierung.',
 editorial_summary_en = 'Coverage in this window is dominated by a US campaign to cut off Cuba''s fuel imports, the island-wide power failures and shortages that followed, and the resulting contest over supply between Washington and Havana''s outside partners. Alongside it run an escalating US military signal in the Caribbean and a legal campaign against the Cuban leadership.',
 editorial_summary_de = 'Die Berichterstattung in diesem Zeitraum wird von einer US-Kampagne zur Unterbindung kubanischer Treibstoffimporte bestimmt, von den darauf folgenden landesweiten Stromausfällen und Engpässen sowie vom Ringen um Nachschub zwischen Washington und Havannas äußeren Partnern. Daneben laufen ein eskalierendes US-Militärsignal in der Karibik und ein juristisches Vorgehen gegen die kubanische Führung.',
 updated_at = NOW()
WHERE id = 'cuba_theater';

UPDATE friction_nodes SET
 description_en = 'US economic and legal instruments applied to Cuba: the embargo and its executive orders, sanctions designations of Cuban state and military-run enterprises, secondary sanctions reaching foreign shippers and hotel operators, expropriation and compensation claims, and criminal charges against Cuban officials.',
 description_de = 'Wirtschaftliche und juristische Instrumente der USA gegenüber Kuba: das Embargo und seine Dekrete, Sanktionslistungen kubanischer Staats- und Militärunternehmen, Sekundärsanktionen gegen ausländische Reedereien und Hotelbetreiber, Enteignungs- und Entschädigungsklagen sowie Strafverfahren gegen kubanische Amtsträger.',
 editorial_summary_en = 'The instrument set widened during this window from the long-standing embargo to an executive order targeting fuel supply, designations of the military conglomerate GAESA and the Moa nickel operation, withdrawal by foreign shipping and hotel groups under threat of secondary sanctions, a Supreme Court opening for expropriation claims, and an indictment of a former Cuban president.',
 editorial_summary_de = 'Das Instrumentarium weitete sich in diesem Zeitraum vom langjährigen Embargo aus: ein Dekret gegen die Treibstoffversorgung, Listungen des Militärkonglomerats GAESA und des Nickelbetriebs Moa, Rückzug ausländischer Reederei- und Hotelgruppen unter Androhung von Sekundärsanktionen, eine Öffnung des Supreme Court für Enteignungsklagen und eine Anklage gegen einen früheren kubanischen Präsidenten.',
 updated_at = NOW()
WHERE id = 'cuba_embargo_sanctions';

UPDATE friction_nodes SET
 description_en = 'The failure of Cuba''s electricity supply and the shortages that follow from it: national and regional blackouts, exhaustion of fuel reserves, rationing, and the effects on hospitals, food, water, sanitation and transport.',
 description_de = 'Der Zusammenbruch der kubanischen Stromversorgung und die daraus folgenden Engpässe: landesweite und regionale Stromausfälle, erschöpfte Treibstoffreserven, Rationierung sowie die Auswirkungen auf Kliniken, Nahrung, Wasser, Abfallentsorgung und Verkehr.',
 editorial_summary_en = 'Cuba''s grid failed repeatedly during this window, at times island-wide, after the government reported its fuel reserves exhausted. Reporting covers rationing plans, closed hotels and suspended flights, uncollected refuse in Havana, hospital supply failures, and United Nations warnings of humanitarian collapse. Whether the cause is the US fuel blockade or long-term under-investment is itself contested.',
 editorial_summary_de = 'Kubas Stromnetz fiel in diesem Zeitraum wiederholt aus, zeitweise landesweit, nachdem die Regierung ihre Treibstoffreserven für erschöpft erklärt hatte. Berichtet wird über Rationierungspläne, geschlossene Hotels und gestrichene Flüge, nicht abgeholten Müll in Havanna, Versorgungsausfälle in Kliniken und Warnungen der Vereinten Nationen vor einem humanitären Zusammenbruch. Ob die Ursache die US-Treibstoffblockade oder jahrzehntelange Unterinvestition ist, ist selbst umstritten.',
 updated_at = NOW()
WHERE id = 'cuba_energy_collapse';

UPDATE friction_nodes SET
 description_en = 'External supply to Cuba and the competition around it: oil and fuel cargoes, food and medical shipments, credit and aid from Russia, China, Venezuela, Mexico, Canada and European states, and US pressure on third countries to withhold them.',
 description_de = 'Versorgung Kubas von außen und der Wettbewerb darum: Öl- und Treibstoffladungen, Nahrungsmittel- und Medizinlieferungen, Kredite und Hilfe aus Russland, China, Venezuela, Mexiko, Kanada und europäischen Staaten sowie US-Druck auf Drittstaaten, sie zurückzuhalten.',
 editorial_summary_en = 'Russian tankers, a Chinese rice shipment, Mexican humanitarian cargoes and a suspended Pemex crude contract all feature in this window, alongside US measures aimed at the third parties supplying them. Shipping movements, diversions and arrivals were reported closely enough to function as a running indicator of the island''s position.',
 editorial_summary_de = 'Russische Tanker, eine chinesische Reislieferung, mexikanische Hilfsfrachten und ein ausgesetzter Pemex-Rohölvertrag prägen diesen Zeitraum, daneben US-Maßnahmen gegen die liefernden Drittparteien. Schiffsbewegungen, Kursänderungen und Ankünfte wurden so genau verfolgt, dass sie als laufender Indikator für die Lage der Insel dienten.',
 updated_at = NOW()
WHERE id = 'cuba_external_lifelines';

UPDATE friction_nodes SET
 description_en = 'The military dimension of US pressure on Cuba: naval and air deployments in the Caribbean, reconnaissance activity, the Guantánamo Bay base and contacts across it, US debate over authorisation for the use of force, and armed incidents around the island.',
 description_de = 'Die militärische Dimension des US-Drucks auf Kuba: Marine- und Luftverlegungen in der Karibik, Aufklärungstätigkeit, der Stützpunkt Guantánamo Bay und die Kontakte über ihn hinweg, die US-Debatte über eine Ermächtigung zum Einsatz von Gewalt sowie bewaffnete Zwischenfälle rund um die Insel.',
 editorial_summary_en = 'This window covers a carrier deployment to the Caribbean, increased surveillance flights off the Cuban coast, a rare meeting between the US Southern Command chief and Cuban officers at the edge of Guantánamo Bay, a Defense Secretary visit to the base, Senate votes on war powers, and a fatal exchange involving an armed group on a US-registered speedboat.',
 editorial_summary_de = 'Dieser Zeitraum umfasst die Verlegung eines Flugzeugträgers in die Karibik, verstärkte Aufklärungsflüge vor der kubanischen Küste, ein seltenes Treffen des Chefs des US-Südkommandos mit kubanischen Offizieren am Rand von Guantánamo Bay, einen Besuch des Verteidigungsministers auf dem Stützpunkt, Senatsabstimmungen über Kriegsvollmachten sowie einen tödlichen Zwischenfall mit einer bewaffneten Gruppe auf einem in den USA registrierten Schnellboot.',
 updated_at = NOW()
WHERE id = 'cuba_military_coercion';

UPDATE friction_nodes SET
 description_en = 'The Cuban government''s internal position: the Communist Party and state leadership, succession, treatment of dissent and political prisoners, protest and policing, and the scope and pace of economic reform.',
 description_de = 'Die innere Lage der kubanischen Regierung: die Kommunistische Partei und die Staatsführung, die Nachfolge, der Umgang mit Dissens und politischen Gefangenen, Proteste und Polizeieinsätze sowie Umfang und Tempo der Wirtschaftsreformen.',
 editorial_summary_en = 'During this window the government announced its largest economic reform package since 1959, released more than two thousand prisoners, and faced rare street protests over blackouts that ended in arrests. Reporting also covers speculation about who follows the current leadership and the position of the private sector.',
 editorial_summary_de = 'In diesem Zeitraum kündigte die Regierung ihr größtes Wirtschaftsreformpaket seit 1959 an, entließ mehr als zweitausend Gefangene und sah sich seltenen Straßenprotesten gegen Stromausfälle gegenüber, die mit Verhaftungen endeten. Berichtet wird auch über Spekulationen zur Nachfolge der Führung und über die Lage des Privatsektors.',
 updated_at = NOW()
WHERE id = 'cuba_regime_survival';

COMMIT;
