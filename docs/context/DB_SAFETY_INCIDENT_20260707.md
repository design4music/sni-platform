# DB Safety Incident, 2026-07-07 -- postmortem and hardening

## What happened

While replaying historical migrations onto a freshly-pulled local copy of
the Render production database (to refresh stale local data before an
fn-map visual QA pass), one migration --
`20260621_seed_global_friction_nodes_corrected.sql` -- contained:

```sql
DELETE FROM friction_nodes WHERE is_active = true OR fn_type = 'theater' OR fn_type = 'atomic';
```

This migration was written months earlier against an empty/dev database,
where the blanket reset-and-reseed was harmless. Replayed against the
freshly-pulled copy of production data, it deleted essentially every
`friction_nodes` row. `event_friction_nodes.fn_id` has `ON DELETE CASCADE`
to `friction_nodes.id` (as does `narratives_v2.fn_id`) -- so the DELETE
silently cascaded and wiped **15,945 real event-linkage rows** (and would
have taken any `narratives_v2` rows too, had more existed at the time).
No error. No warning. The subsequent `INSERT ... ON CONFLICT (id) DO
NOTHING` in the same file re-created most `friction_nodes` rows, masking
the damage -- the parent table looked fine; only the invisible child data
was gone.

**Root cause of not catching it in advance:** before running the file, I
checked `information_schema.referential_constraints.update_rule` (which
was `NO ACTION`) but not `delete_rule` (which was `CASCADE`). Checking the
wrong column of the same view gave false confidence.

**Blast radius:** local development database only. Render (production)
was only ever read from (`pg_dump`), never written to, during this
incident -- production was not at risk at any point.

## Recovery

The original `pg_dump` (taken minutes earlier, before any local replay)
was still on disk. Recovery: drop the FK constraint, `pg_restore
--data-only --table=event_friction_nodes` from the untouched original dump
(recovers the exact 15,945 rows), delete the handful of rows now orphaned
because their parent `friction_nodes` id had also been renamed/removed by
later migrations, re-add the FK exactly as it was. Verified: row count
matched, zero orphans, `iran_theater` event counts matched the live
production website exactly.

## Hardening applied

1. **`scripts/safe_db_migrate.py`** -- mandatory wrapper for applying any
   migration going forward. Before touching data it: (a) takes a full
   `pg_dump` backup to `db/backups/<target>_<timestamp>.dump` (gitignored),
   (b) scans the SQL for `DELETE`/`TRUNCATE`/`DROP TABLE`/`DROP COLUMN`,
   and for any `DELETE FROM <table>` found, queries
   `information_schema` for `ON DELETE CASCADE` children and prints the
   **current row count** of each -- the exact number that silently
   vanished this time, shown up front instead of discovered after the
   fact. Refuses to proceed unless `--yes-i-checked` is passed once the
   report has been read. `--target render` is deliberately not wired up --
   applying to production is a separate, explicit, human-run step.
2. **The migration itself is patched** (see its updated header comment):
   the DELETE now excludes any row with live `event_friction_nodes` or
   `narratives_v2` children, and its INSERT already had `ON CONFLICT DO
   NOTHING`. It is safe to re-run today, including as part of the eventual
   Render deploy -- but must go through `safe_db_migrate.py`, not raw
   `psql < file.sql`.
3. **Going forward:** every `.sql` migration, on any database that holds
   real pipeline data (local or Render), goes through
   `scripts/safe_db_migrate.py`. Raw `docker exec ... psql < file.sql` is
   for read-only queries only.

## The one rule that would have prevented this

Before running any `DELETE`/`TRUNCATE`/`DROP`, check `delete_rule` (not
just `update_rule`) on every FK referencing the target table. If any is
`CASCADE`, the blast radius is the CHILD table's row count, not the
parent's. `scripts/safe_db_migrate.py` now does this automatically, every
time, unconditionally.
