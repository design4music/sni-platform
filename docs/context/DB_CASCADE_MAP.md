# DB Cascade Map & Delete-Safety Rule

Plain-English guide to `ON DELETE CASCADE` in this database, and the
standing rule for any statement that can remove data. Written after the
2026-07-07 incident (D-091) where a replayed migration's `DELETE FROM
friction_nodes` silently cascaded and wiped 15,945 real rows.

## What "ON DELETE CASCADE" means (the thing to understand)

A foreign key with `ON DELETE CASCADE` says: *"when a row in the PARENT
table is deleted, automatically delete every CHILD row that pointed to
it — no warning, no confirmation."* And children can have their own
cascading children, so one `DELETE` can chain through several tables.

The danger is that the `DELETE` you write looks tiny. `DELETE FROM
friction_nodes WHERE ...` reads like it touches ~150 rows. But because
`event_friction_nodes`, `narratives_v2`, and `fn_asset_evidence` all
cascade from it — and `title_narratives` cascades from `narratives_v2` —
that one statement can erase ~143,000 rows across four tables. The SQL
gives no hint; you only find out afterward.

## The live cascade forest (regenerate any time)

```
python scripts/safe_db_migrate.py --audit
```

This walks the FULL tree (not just direct children) and prints current
row counts, so the real blast radius is visible before you act. Snapshot
as of 2026-07-08 — the four that can destroy the platform:

| DELETE on this parent | cascades to | why it matters |
|---|---|---|
| `centroids_v3` (128) | **2.7M rows** — ctm -> events_v3 -> event_titles/friction/narratives | deleting centroids nukes nearly everything |
| `ctm` (1,981) | **2.7M rows** — events_v3 and all its children | same chain, one level down |
| `titles_v3` (348k) | **1.36M rows** — labels, assignments, narratives, event_titles | the raw layer; wipes all derived attribution |
| `friction_nodes` (154) | **143k rows** — event_friction_nodes, narratives_v2 -> title_narratives, fn_asset_evidence | the D-091 chain |

Smaller but still real: `strategic_narratives` (->88k), `narratives_v2`
(->84k), `events_v3` (->534k), `strategic_assets` (->31), `epics` (->0).

**Row count vs. real footprint — read this before trusting the totals.**
`events_v3` holds ~2.17M rows but only ~200k are live (~162k promoted +
~39k unpromoted); the other **~91% (1.97M) are `merged_into` tombstones**
— soft-deleted duplicates from the 30-min sibling-reconciliation pass
(D-057) that carry zero child rows. So the `--audit` cascade totals are
correct as "rows that would be deleted" but overstate real content ~11x
for anything chaining through `events_v3` (centroids_v3, ctm). The
meaningful live footprint: ~348k titles, ~200k events, ~394k event-title
links. Separate open item: nothing purges the tombstones, so events_v3
grows unboundedly (~2M in 6 months, most of the 650MB dump). A periodic
tombstone purge is a real maintenance opportunity — but it is itself a
multi-million-row DELETE and falls under the rule below.

## The rule (for humans and LLMs)

1. **Inserts default to `INSERT ... ON CONFLICT DO NOTHING`** (or
   `DO UPDATE` when a genuine upsert is intended). Idempotent, re-runnable,
   never destructive. This is the norm across the pipeline already
   (incremental clustering never wipes — D-022).

2. **No `DELETE` / `TRUNCATE` / `DROP` on a data table without explicit
   human confirmation in the conversation.** Not "it's probably fine" —
   confirmation. State what is affected, how many rows, and (crucially)
   the *cascade* total, then wait for a yes.

3. **Every `.sql` migration against a DB with real data goes through
   `scripts/safe_db_migrate.py`** — never raw `psql < file.sql`. The
   wrapper backs up first, then scans for DELETE/TRUNCATE/DROP and prints
   the recursive cascade blast radius, refusing to proceed without
   `--yes-i-checked`. Local-only by design; a Render deploy is a separate,
   explicit, manually-confirmed step.

4. **Before writing any migration that reduces data, run `--audit`** (or
   check the target table in the table above). If it is a cascade parent,
   the number that matters is the descendant total, not the parent's own
   row count.

5. **Prefer soft-delete / deactivate over hard delete.** This schema uses
   `is_active = false` widely (friction_nodes, strategic_assets,
   centroids_v3). Deactivating is reversible and never cascades. Reach for
   it first; hard `DELETE` is the last resort, gated by rules 2-4.

## Note on the cascades themselves

The `ON DELETE CASCADE` FKs are mostly correct as *schema* — they keep
derived tables consistent when a parent is legitimately removed (delete an
event, its title-links should go too). The danger is not the constraints;
it is running a broad `DELETE` written for an empty dev DB against
production data. The rule above addresses the operation, not the schema.
We are deliberately NOT removing the cascades (that would orphan-rot the
derived tables); we are gating the deletes.
