# fn-map Render Deploy Runbook

Status: **Step 1 EXECUTED 2026-07-07 ~21:30-22:15 CET** -- all 39
migrations rc=0 (skipped: sudan + ukraine main seeds and ukraine
iteration_3, already applied to Render in May; australia anchor bundle,
known ON CONFLICT failure). Scripts run: registry generator (340 assets),
7 anchor bundles, 7 bootstraps, evidence compute (33 links). Verified:
efn grew 15,945 -> 17,279 (the 1,334 new-theater events), narratives 72
and title_narratives 48,395 UNCHANGED, iran 3,388 member events, mexico
1,284, panama 21, haiti 29, iran->kharg evidence link present, zero old
generic ids. Pre-deploy backup: render_predeploy_20260707.dump in the
render_sync_vol docker volume. **Step 2 (code) still pending.**

Step 1 (DB) can run independently of Step 2
(code); the live site is unaffected by Step 1 because main-branch code
never queries the new tables.

**Why this list is trusted:** local was rebuilt this morning from a fresh
Render dump and then this exact sequence was applied on top -- today's
local rebuild was the deploy rehearsal. Local's current state IS the
expected post-deploy Render state (minus news ingested since the dump).

## The sync model (permanent rule)

- News data (titles/events/briefs): Render is the source of truth; flows
  Render -> local only, for QA.
- Structural content (registry YAML, migrations, curated anchor-bundle
  JSONs): git is the source of truth; applied to BOTH DBs with the same
  files. Never move structural content as a data dump.
- Code: git; Render frontend deploy is manual from the dashboard.

## Step 1 -- database (no user-visible change)

Pre-flight:
1. FULL Render backup via the PG18 docker pattern (pg_dump -Fc). Keep the
   file; it is the rollback for everything below.
2. Sanity queries on Render: friction_nodes count (~31 expected),
   event_friction_nodes count, narratives_v2 count (~72), and confirm
   strategic_assets does NOT exist yet.

Apply, in this order (psql via docker postgres:18 against Render, each
file checked for DELETE/TRUNCATE/DROP + cascade blast radius first --
safe_db_migrate.py is local-only by design, so on Render this check is
manual; only 20260621_seed_global_friction_nodes_corrected.sql contains a
DELETE and it is patched to skip rows with live children):

  Drift fixes (repo migrations never applied to Render):
    20260513_friction_node_sudan_civil_war_seed.sql   -- SKIP if sudan_civil_war exists; else apply the
                                                         friction_nodes INSERT only (bundle already live)
    20260519_friction_node_ukraine_war_theater_seed.sql -- check first: narratives already on Render,
                                                         FN rows may be too; apply only if missing
    20260519_friction_node_ukraine_iteration_2.sql
    20260519_friction_node_ukraine_iteration_3.sql
    20260620_add_global_fn_centroids.sql
    20260620_seed_friction_nodes_v2.sql
    20260620_seed_global_friction_nodes.sql
    20260620_seed_global_friction_nodes_part2.sql
    20260621_seed_global_friction_nodes_corrected.sql  -- PATCHED; verify header before running
    20260621_add_primary_target_to_friction_nodes.sql
    20260621_set_primary_target_friction_nodes.sql
    20260623_fn_anchor_europe_atomics.sql
    (20260621_fn_anchor_australia_china_theater.sql KNOWN-FAILS on
     ON CONFLICT spec; skip -- bundle can be applied later via the
     apply-tool if wanted)

  fn-map core:
    20260629_add_outlet_description.sql
    20260629_add_sitemap_cache.sql
    20260703_strategic_assets.sql
    20260703_seed_strategic_assets.sql
    20260703_seed_assets_batch2.sql
    20260703_seed_assets_batch3.sql
    20260703_centroid_map_points.sql
    20260703_fn_anchor_points.sql
    20260703_fn_asset_assignments.sql
    20260703_deactivate_linear_assets.sql
    20260703_fix_linear_geometries.sql
    20260703_gem_pipeline_routes.sql
    20260703_seed_trade_corridors.sql
    20260704_add_subcategory.sql
    20260704_seed_oil_everything.sql
    20260704_seed_gas_everything.sql
    20260704_seed_mining_deep.sql
    20260704_seed_agri_food.sql
    20260704_seed_power_plants.sql
    20260704_seed_tech_infra.sql
    20260704_seed_russia_power_grain.sql
    20260704_asset_flows.sql
    20260704_seed_oil_flows.sql

  2026-07-07 session:
    20260707_fn_id_naming.sql
    20260707_latam_theater_split.sql
    20260707_panama_centroid_fix.sql
    20260707_theater_asset_wiring.sql
    20260707_iran_theater_asset_fix.sql
    20260707_iran_theater_asset_fix2.sql
    20260707_theater_asset_backfill.sql
    20260707_fn_asset_evidence.sql

Then scripts, with Render env vars (DB_HOST/PORT/NAME/USER/PASSWORD --
scripts read individual vars, NOT DATABASE_URL):
    python scripts/generate_asset_registry.py          -- 340 assets reconcile
    python scripts/apply_fn_anchor_bundle.py --json docs/context/fn_anchor_bundles_20260707/<each of 7>.json --mode apply
    python scripts/bootstrap_friction_node.py --fn-id <each of the 7 new atomics>
    python scripts/compute_fn_asset_evidence.py        -- ~3 min

Verify (compare against local values from 2026-07-07):
    strategic_assets: 340 active
    friction_nodes: 33 active theaters; iran_theater member events ~3.4k
    fn_asset_evidence: ~30 links; iran->kharg present
    event_friction_nodes count UNCHANGED from pre-flight
    narratives_v2 count >= pre-flight (never lower)

Rollback: restore the pre-flight dump.

## Step 2 -- code (after local visual QA)

1. Merge fn-map -> main (ask/confirm), git push (confirm separately).
2. Manual frontend deploy from the Render dashboard (no auto-deploy).
3. Cache bust: POST /api/admin/revalidate-cache with x-revalidate-token.
4. Smoke-check the live map: Iran glowing, Kharg pressed with headline
   count, flows render on Jamnagar/Hormuz selection.

## Step 3 -- steady state

- fn_asset_evidence recompute: manual after deploy; then wire a cron or
  daemon Slot 4 step (ticket).
- All future structural edits: registry YAML / migration / curated JSON in
  git, applied to both DBs. No exceptions.
- Render -> local pull only when local QA needs fresh news data.
