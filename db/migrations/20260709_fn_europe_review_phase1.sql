-- FN Europe review, phase 1 (2026-07-09)
-- Decisions per Europe FN audit (out/fn_audit_EUROPE.md):
--   1. Merge russia_sanctions_economy into russia_sanctions_regime
--   2. Fold europe_sovereignty_theater into eu_cohesion_theater
--      (renamed "European political fragmentation", 8 members)
--   3. Deactivate us_russia_theater shadow members (arctic_competition,
--      ukraine_proxy_war -- duplicate arctic_theater / ukraine_war_theater)
--   4. Single-home greenland_control in europe_us_theater
--   5. Widen russia_europe_theater actor scope (DE/FR/UK/Visegrad/Nordic)
--   6. Replace dead centroid EUROPE-EU (not in centroids_v3, 0 titles) with
--      NON-STATE-EU on all 14 carriers; drop zero-title EUROPE-HUNGARY /
--      EUROPE-SLOVAKIA in favour of EUROPE-VISEGRAD where coverage lands.
--      Theaters keep a EUROPE-* centroid first: the frontend derives the
--      UI region from the first array element.
--
-- Idempotent. Only derived rows deleted: event_friction_nodes for the
-- deactivated russia_sanctions_economy (201 rows, regenerable by bootstrap).

BEGIN;

-- (6a) Dead centroid swap on every carrier, before explicit arrays below.
UPDATE friction_nodes
   SET centroid_ids = array_replace(centroid_ids, 'EUROPE-EU', 'NON-STATE-EU'),
       updated_at = NOW()
 WHERE 'EUROPE-EU' = ANY(centroid_ids);

-- (1) russia_sanctions_economy -> russia_sanctions_regime
UPDATE friction_nodes SET is_active = false, updated_at = NOW()
 WHERE id = 'russia_sanctions_economy';
UPDATE taxonomy_v3 SET is_active = false
 WHERE taxonomy_function = 'fn_anchor' AND linked_id = 'russia_sanctions_economy';
DELETE FROM event_friction_nodes WHERE fn_id = 'russia_sanctions_economy';
UPDATE friction_nodes
   SET member_fn_ids = array_remove(member_fn_ids, 'russia_sanctions_economy'),
       updated_at = NOW()
 WHERE id = 'russia_europe_theater';

-- (2) europe_sovereignty_theater folded into eu_cohesion_theater
UPDATE friction_nodes SET
    name_en = 'European political fragmentation',
    name_de = 'Politische Fragmentierung Europas',
    description_en = 'Contest over the EU''s internal cohesion and the sovereignty of its member states: rule-of-law and budget disputes, migration burden-sharing, and the rise of nationalist movements in Germany, France, Italy and post-Brexit Britain. The friction runs between Brussels institutions and national governments, and within member states themselves.',
    description_de = 'Auseinandersetzung um den inneren Zusammenhalt der EU und die Souveraenitaet ihrer Mitgliedstaaten: Rechtsstaatlichkeits- und Haushaltskonflikte, Streit um die Verteilung der Migrationslasten sowie das Erstarken nationalistischer Bewegungen in Deutschland, Frankreich, Italien und im Vereinigten Koenigreich nach dem Brexit. Die Friktion verlaeuft zwischen den Bruesseler Institutionen und den nationalen Regierungen sowie innerhalb der Mitgliedstaaten selbst.',
    centroid_ids = ARRAY['EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK','EUROPE-SOUTH','EUROPE-VISEGRAD','NON-STATE-EU'],
    member_fn_ids = ARRAY['hungary_rule_of_law','slovakia_alignment',
                          'eu_migration_burden_sharing','eu_budget_sovereignty',
                          'afd_and_german_polarisation','french_nationalist_challenge',
                          'post_brexit_realignment','italian_populist_government'],
    updated_at = NOW()
 WHERE id = 'eu_cohesion_theater';
UPDATE friction_nodes SET is_active = false, updated_at = NOW()
 WHERE id = 'europe_sovereignty_theater';

-- (3) us_russia_theater shadow members
UPDATE friction_nodes SET is_active = false, updated_at = NOW()
 WHERE id IN ('arctic_competition', 'ukraine_proxy_war');
UPDATE friction_nodes
   SET member_fn_ids = array_remove(array_remove(member_fn_ids,
                          'arctic_competition'), 'ukraine_proxy_war'),
       updated_at = NOW()
 WHERE id = 'us_russia_theater';

-- (4) greenland_control stays only in europe_us_theater
UPDATE friction_nodes
   SET member_fn_ids = array_remove(member_fn_ids, 'greenland_control'),
       updated_at = NOW()
 WHERE id = 'arctic_theater';

-- (5) russia_europe_theater actor scope (EUROPE-RUSSIA stays first)
UPDATE friction_nodes
   SET centroid_ids = ARRAY['EUROPE-RUSSIA','NON-STATE-EU','EUROPE-BALTIC',
                            'EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK',
                            'EUROPE-VISEGRAD','EUROPE-NORDIC','AMERICAS-USA'],
       updated_at = NOW()
 WHERE id = 'russia_europe_theater';

-- (6b) europe_us_theater: explicit order so a EUROPE-* id is first
-- (was EUROPE-EU-first; DE/FR/UK added -- that is where transatlantic
-- trade/defence coverage actually lands).
UPDATE friction_nodes
   SET centroid_ids = ARRAY['EUROPE-GERMANY','EUROPE-FRANCE','EUROPE-UK',
                            'NON-STATE-EU','AMERICAS-USA','ASIA-CHINA',
                            'EUROPE-GREENLAND'],
       updated_at = NOW()
 WHERE id = 'europe_us_theater';

-- (6c) Zero-title centroids EUROPE-HUNGARY / EUROPE-SLOVAKIA -> EUROPE-VISEGRAD
UPDATE friction_nodes
   SET centroid_ids = ARRAY['EUROPE-VISEGRAD','NON-STATE-EU'],
       updated_at = NOW()
 WHERE id = 'hungary_rule_of_law';
UPDATE friction_nodes
   SET centroid_ids = ARRAY['EUROPE-VISEGRAD','NON-STATE-EU','EUROPE-RUSSIA'],
       updated_at = NOW()
 WHERE id = 'slovakia_alignment';

COMMIT;
