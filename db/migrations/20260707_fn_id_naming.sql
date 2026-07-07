-- FN id naming pass: geographically-abstract slugs get a geo prefix.
-- Convention (see docs/context/FN_ID_NAMING.md): id = <geo>_<phenomenon>,
-- geo = country, actor-first pair (us_china_...), or established region
-- token (eu, nato, arctic, sahel, scs, latam, caucasus, korea, drc, indus).
--
-- Rename mechanics: friction_nodes.id is referenced by
-- event_friction_nodes.fn_id (FK), narratives_v2.fn_id (FK),
-- taxonomy_v3.linked_id (fn_anchor bundles, no FK), and theater
-- member_fn_ids arrays. FKs are NO ACTION, so: copy row under new id ->
-- repoint children -> patch member arrays -> delete old row. Idempotent
-- (skips ids that no longer exist). MUST also be applied to Render on
-- deploy; live /friction-nodes/<id> URLs change (accepted: pilot surface).

BEGIN;

DO $$
DECLARE m RECORD;
BEGIN
  FOR m IN
    SELECT * FROM (VALUES
      ('critical_resources',            'arctic_resources_competition'),
      ('military_presence',             'arctic_military_presence'),
      ('shipping_routes',               'arctic_shipping_routes'),
      ('security_alignment',            'aukus_security_alignment'),
      ('economic_coercion',             'china_australia_economic_coercion'),
      ('migration_burden_sharing',      'eu_migration_burden_sharing'),
      ('budget_and_sovereignty',        'eu_budget_sovereignty'),
      ('strategic_autonomy',            'eu_strategic_autonomy'),
      ('defence_dependence',            'europe_us_defence_dependence'),
      ('critical_minerals_competition', 'drc_minerals_competition'),
      ('regional_intervention_forces',  'drc_intervention_forces'),
      ('cross_border_militancy',        'india_pakistan_militancy'),
      ('nuclear_deterrence_balance',    'india_pakistan_nuclear_balance'),
      ('water_sharing_indus',           'indus_water_sharing'),
      ('historical_memory_conflicts',   'japan_china_memory_wars'),
      ('peninsula_deterrence',          'korea_peninsula_deterrence'),
      ('reunification_and_identity',    'korea_reunification_identity'),
      ('ethnic_armed_conflicts',        'myanmar_ethnic_conflicts'),
      ('china_border_influence',        'myanmar_china_influence'),
      ('nato_deterrence',               'russia_nato_deterrence'),
      ('sanctions_and_economy',         'russia_sanctions_economy'),
      ('energy_security_leverage',      'russia_gas_leverage'),
      ('french_withdrawal_legacy',      'sahel_french_withdrawal'),
      ('russian_security_presence',     'sahel_wagner_presence'),
      ('regional_regime_consolidation', 'sahel_junta_consolidation'),
      ('freedom_of_navigation',         'scs_freedom_of_navigation'),
      ('reef_militarisation',           'scs_reef_militarisation'),
      ('fisheries_conflict',            'scs_fisheries_conflict'),
      ('technology_restrictions',       'us_china_tech_restrictions'),
      ('trade_and_tariffs',             'us_china_trade_tariffs'),
      ('investment_screening',          'us_china_investment_screening'),
      ('strategic_supply_chains',       'us_china_supply_chains'),
      ('federal_state_authority',       'us_federal_state_authority'),
      ('immigration_border_politics',   'us_immigration_border'),
      ('culture_war_conflicts',         'us_culture_wars'),
      ('nuclear_arms_control',          'us_russia_arms_control'),
      ('election_interference',         'us_russia_election_interference'),
      ('regional_power_competition',    'caucasus_power_competition'),
      ('embargo_and_sanctions',         'cuba_embargo_sanctions'),
      ('migration_pressures',           'cuba_migration_exodus'),
      ('regime_survival',               'cuba_regime_survival'),
      ('infrastructure_influence',      'latam_infrastructure_influence'),
      ('trade_dependence',              'latam_trade_dependence'),
      ('strategic_resources',           'latam_lithium_minerals'),
      ('sanctions_and_oil',             'venezuela_sanctions_oil')
    ) AS t(old_id, new_id)
  LOOP
    IF NOT EXISTS (SELECT 1 FROM friction_nodes WHERE id = m.old_id) THEN
      CONTINUE;  -- already renamed (idempotent re-run)
    END IF;
    IF EXISTS (SELECT 1 FROM friction_nodes WHERE id = m.new_id) THEN
      RAISE EXCEPTION 'rename target % already exists', m.new_id;
    END IF;

    INSERT INTO friction_nodes
      (id, name_en, name_de, description_en, description_de, centroid_ids,
       is_active, display_order, created_at, updated_at,
       editorial_summary_en, editorial_summary_de, fn_type, member_fn_ids,
       primary_target, affected_asset_ids, scope, anchor_point)
    SELECT
      m.new_id, name_en, name_de, description_en, description_de, centroid_ids,
      is_active, display_order, created_at, now(),
      editorial_summary_en, editorial_summary_de, fn_type, member_fn_ids,
      primary_target, affected_asset_ids, scope, anchor_point
    FROM friction_nodes WHERE id = m.old_id;

    UPDATE event_friction_nodes SET fn_id = m.new_id WHERE fn_id = m.old_id;
    UPDATE narratives_v2        SET fn_id = m.new_id WHERE fn_id = m.old_id;
    UPDATE taxonomy_v3          SET linked_id = m.new_id
      WHERE linked_id = m.old_id AND taxonomy_function LIKE 'fn_%';
    UPDATE friction_nodes
      SET member_fn_ids = array_replace(member_fn_ids, m.old_id, m.new_id)
      WHERE m.old_id = ANY(member_fn_ids);

    DELETE FROM friction_nodes WHERE id = m.old_id;
  END LOOP;
END $$;

-- Dedupe: greenland_sovereignty (0 events) duplicates greenland_control.
-- europe_us_theater keeps the concept via the shared atomic (multi-
-- membership is legal); the empty duplicate is deactivated.
UPDATE friction_nodes
  SET member_fn_ids = array_replace(member_fn_ids, 'greenland_sovereignty', 'greenland_control')
  WHERE 'greenland_sovereignty' = ANY(member_fn_ids);
UPDATE friction_nodes SET is_active = false, updated_at = now()
  WHERE id = 'greenland_sovereignty';

-- Orphan fix: russia_sanctions_regime (1,803 events) belonged to no theater.
UPDATE friction_nodes
  SET member_fn_ids = array_append(member_fn_ids, 'russia_sanctions_regime'),
      updated_at = now()
  WHERE id = 'russia_europe_theater'
    AND NOT ('russia_sanctions_regime' = ANY(member_fn_ids));

COMMIT;
