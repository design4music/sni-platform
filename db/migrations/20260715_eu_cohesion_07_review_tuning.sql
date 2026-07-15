-- eu_cohesion_theater — tuning pass after user review of the live pages.
-- (a) HUNGARY: real 2026 coverage is the post-Orbán TRANSITION (election, Magyar
--     cleanup, president ousted), whose headlines lack rule-of-law keywords -> the
--     +2 standards narrative missed them. Broaden its framing. And the -2 coercion
--     narrative was leaking Orbán's Russia-sanctions vetoes (russia_europe/ukraine
--     boundary) via 'sanction'/'blackmail' keywords -> strip those, keep only
--     rule-of-law-coercion terms.
-- (b) MIGRATION: 'Albania' as a framing keyword caught Albania-the-country
--     (enlargement, resort development), not just Italy's Albania migrant model ->
--     drop it; the migrant-protocol stories still match via other terms.
-- (c) RIFT -> COUNTER-FRAMING: per review, Moscow/Beijing aren't pure schadenfreude —
--     they favour direct state-to-state dealing over Brussels' supranational authority,
--     so they are structurally ALIGNED with the sovereigntist case against Brussels
--     (same negative cohesion-axis side) without endorsing any party. Re-label from
--     "rift-exploitation" to "counter-framing" and add the alignment nuance to claims.
-- (d) Deactivate the two 0-title Kremlin narratives (budget/realignment) — no such
--     commentary in the feed. Reversible.
-- (e) Relabel the theater -1 card: migration restriction is partly Brussels-led, so
--     "revolt against Brussels" overreached -> "National sovereignty and control".
-- Requires re-bootstrap of hungary + migration (keyword changes).
SET client_encoding TO 'UTF8';

-- ================= (a) HUNGARY =================
UPDATE narratives_v2 SET
  framing_keywords = ARRAY['rule of law','Rechtsstaatlichkeit','état de droit','stato di diritto','conditionality','Konditionalität','judicial independence','media freedom','Pressefreiheit','corruption','Korruption','anti-corruption','backsliding','democratic renewal','frozen funds','eingefrorene','recovery plan','transparency','Transparenz','new government','neue Regierung','Regierungswechsel','election','Neuwahl','oust','abgesetzt','transition','Aufarbeitung','clean-up'],
  updated_at = NOW()
WHERE id = 'hungary_eu_standards';

UPDATE narratives_v2 SET
  name_en = 'Brussels overreaches against a sovereign nation',
  name_de = 'Brüssel greift nach einem souveränen Land über',
  claim_en = 'Counter-framing (Russian state press, and the sovereignty case generally) holds that the conditionality fight and the funds freeze were Brussels overreaching against a democratically elected government and infringing national sovereignty. Moscow favours direct dealings with national capitals over Brussels'' supranational authority, so it amplifies the sovereigntist critique and every sign of EU heavy-handedness — aligned against Brussels rather than endorsing a specific Hungarian faction. Vocabulary: coercion, overreach, sovereignty, interference, diktat.',
  claim_de = 'Die Gegen-Rahmung (russische Staatspresse und die souveränistische Sichtweise allgemein) sieht im Konditionalitätsstreit und im Einfrieren der Mittel einen Übergriff Brüssels gegen eine demokratisch gewählte Regierung und eine Verletzung der nationalen Souveränität. Moskau bevorzugt direkte Beziehungen zu den nationalen Hauptstädten gegenüber der supranationalen Autorität Brüssels und verstärkt daher die souveränistische Kritik und jedes Zeichen von Brüsseler Härte — gegen Brüssel gerichtet, ohne eine ungarische Seite zu unterstützen.',
  framing_keywords = ARRAY['coercion','diktat','interfere','вмешательств','overreach','sovereignty','суверенитет','voting rights','лишени права','frozen funds','заморож','double standard','Bevormundung','Erpressung durch Brüssel'],
  stance_label_en = 'Russian counter-framing',
  stance_label_de = 'Russische Gegen-Rahmung',
  updated_at = NOW()
WHERE id = 'hungary_brussels_coercion';

-- ================= (b) MIGRATION =================
UPDATE narratives_v2 SET
  framing_keywords = ARRAY['control','Kontrolle','crackdown','tougher','deport','Abschiebung','irregular','illegal migration','offshore','remigration','pull factor','restrict','clampdown','overwhelmed','Grenzen schützen','secure border','return hub','tougher asylum'],
  updated_at = NOW()
WHERE id = 'migration_national_control';

UPDATE narratives_v2 SET
  claim_en = 'Counter-framing (Russian state press) presents EU migration as chaos, division and the failure of a hypocritical Europe — often measured against Russia''s own large migrant and refugee inflows and integration strains — amplifying the disputes between member states as evidence of decline rather than taking a side on asylum policy. Vocabulary: chaos, crisis, failure, hypocrisy, collapse.',
  claim_de = 'Die Gegen-Rahmung (russische Staatspresse) stellt die EU-Migration als Chaos, Spaltung und Scheitern eines heuchlerischen Europas dar — oft gemessen an Russlands eigenen großen Migranten- und Flüchtlingszuströmen und Integrationsproblemen — und verstärkt die Streitigkeiten zwischen den Mitgliedstaaten als Zeichen des Niedergangs, ohne in der Asylpolitik Partei zu ergreifen.',
  stance_label_en = 'Russian counter-framing',
  stance_label_de = 'Russische Gegen-Rahmung',
  updated_at = NOW()
WHERE id = 'migration_eu_failure_kremlin';

-- ================= (c) RIFT -> COUNTER-FRAMING (remaining atomic Kremlin narratives) =================
UPDATE narratives_v2 SET
  claim_en = 'Counter-framing (Russian state press) presents German measures against the AfD as political persecution and censorship by a state that lectures others on democracy. Moscow favours direct dealing with national forces over Brussels-aligned establishments, so it amplifies the polarisation and the anti-establishment case — adversarial to the German mainstream rather than an endorsement of the party''s programme. Vocabulary: persecution, censorship, crackdown, hypocrisy.',
  claim_de = 'Die Gegen-Rahmung (russische Staatspresse) stellt die deutschen Maßnahmen gegen die AfD als politische Verfolgung und Zensur eines Staates dar, der andere über Demokratie belehrt. Moskau bevorzugt den direkten Umgang mit nationalen Kräften gegenüber Brüssel-nahen Establishments und verstärkt daher die Polarisierung und die anti-etablierte Sichtweise — gegnerisch zum deutschen Mainstream, keine Zustimmung zum Programm der Partei.',
  stance_label_en = 'Russian counter-framing',
  stance_label_de = 'Russische Gegen-Rahmung',
  updated_at = NOW()
WHERE id = 'afd_persecution_kremlin';

UPDATE narratives_v2 SET
  claim_en = 'Counter-framing (Russian state press) presents French turmoil, government collapses and unrest as proof of a failing Western model and elite disconnect. Moscow prefers dealing with sovereign national leaderships over Brussels-aligned elites, so it amplifies the instability and the anti-establishment case rather than endorsing any French party. Vocabulary: chaos, collapse, crisis, decline.',
  claim_de = 'Die Gegen-Rahmung (russische Staatspresse) deutet die französischen Turbulenzen, Regierungsstürze und Unruhen als Beleg eines scheiternden westlichen Modells und abgehobener Eliten. Moskau bevorzugt den Umgang mit souveränen nationalen Führungen gegenüber Brüssel-nahen Eliten und verstärkt daher die Instabilität und die anti-etablierte Sichtweise, ohne eine französische Partei zu unterstützen.',
  stance_label_en = 'Russian counter-framing',
  stance_label_de = 'Russische Gegen-Rahmung',
  updated_at = NOW()
WHERE id = 'france_decline_kremlin';

UPDATE narratives_v2 SET
  stance_label_en = 'Russian & Chinese counter-framing',
  stance_label_de = 'Russische & chinesische Gegen-Rahmung',
  claim_en = 'Counter-framing (Russian and Chinese state media) presents the realignment as the collapse of a discredited European liberal centre and the vindication of forces opposed to Brussels and to Ukraine support. Moscow and Beijing favour a Europe of sovereign nations dealing bilaterally over Brussels'' supranational authority, so they amplify the shift as Western decline rather than endorsing a specific party. Vocabulary: collapse, decline, discredited, liberal elite.',
  claim_de = 'Die Gegen-Rahmung (russische und chinesische Staatsmedien) deutet die Neuordnung als Zusammenbruch einer diskreditierten europäischen liberalen Mitte und als Bestätigung der Kräfte gegen Brüssel und gegen die Ukraine-Unterstützung. Moskau und Peking bevorzugen ein Europa souveräner, bilateral handelnder Nationen gegenüber der supranationalen Autorität Brüssels und verstärken daher den Wandel als westlichen Niedergang, ohne eine bestimmte Partei zu unterstützen.',
  updated_at = NOW()
WHERE id = 'realignment_center_decline_kremlin';

-- ================= (d) deactivate 0-title Kremlin narratives =================
UPDATE narratives_v2 SET is_active = false, updated_at = NOW()
WHERE id IN ('budget_eu_decline_kremlin', 'realignment_center_decline_kremlin');

-- ================= (e) theater cards: relabel + alignment nuance =================
UPDATE narratives_v2 SET
  stance_label_en = 'National sovereignty and control',
  stance_label_de = 'Nationale Souveränität und Kontrolle',
  updated_at = NOW()
WHERE id = 'eu_sovereigntist_revolt';

UPDATE narratives_v2 SET
  name_en = 'Brussels overreach vindicates a Europe of sovereign nations',
  name_de = 'Brüsseler Übergriffigkeit bestätigt ein Europa souveräner Nationen',
  claim_en = 'Counter-framing (Russian and Chinese state media) reads every internal European dispute as evidence that Brussels coerces its members and that a Europe of sovereign nations dealing bilaterally would serve them better. Moscow and Beijing prefer direct relations with national capitals over the EU''s supranational authority, so they amplify the sovereigntist case and every sign of division — adversarial to Brussels and to European cohesion as a whole, not a genuine party in the internal disputes they magnify. Vocabulary: coercion, sovereignty, decline, hypocrisy, division.',
  claim_de = 'Die Gegen-Rahmung (russische und chinesische Staatsmedien) liest jeden inneren europäischen Streit als Beleg, dass Brüssel seine Mitglieder zwingt und dass ein Europa souveräner, bilateral handelnder Nationen ihnen besser diente. Moskau und Peking bevorzugen direkte Beziehungen zu den nationalen Hauptstädten gegenüber der supranationalen Autorität der EU und verstärken daher die souveränistische Sichtweise und jedes Zeichen der Spaltung — gegnerisch zu Brüssel und zur europäischen Kohäsion insgesamt, keine echte Partei in den vergrößerten Konflikten.',
  stance_label_en = 'Russian & Chinese counter-framing',
  stance_label_de = 'Russische & chinesische Gegen-Rahmung',
  updated_at = NOW()
WHERE id = 'eu_fracture_rift_exploitation';
