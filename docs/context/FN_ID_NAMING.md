# FN ID Naming Convention

**Status**: evergreen reference. Applies to every new friction_nodes row.
Established 2026-07-07 (migration `20260707_fn_id_naming.sql` renamed 45
legacy generic slugs). Companion to `FN_ANCHOR_VOCABULARY_SPEC.md`.

## The rule

```
id = <geo>_<phenomenon>
```

- **geo** is one of:
  - a country token: `us`, `russia`, `iran`, `turkey`, `mexico`, `cuba`,
    `haiti`, `venezuela`, `myanmar` ... (full name style, matching the
    existing corpus -- not ISO-2, which collides with English words and
    violates the anchor spec's 2-char token rule);
  - an actor-first country pair: `us_china_`, `india_pakistan_`,
    `japan_china_`, `russia_nato_`, `china_australia_`;
  - an established region/system token: `eu`, `nato`, `arctic`, `sahel`,
    `scs`, `latam`, `caucasus`, `korea`, `drc`, `indus`, `aukus`,
    `transatlantic`.
- **phenomenon** is 1-3 atoms: `trade_tariffs`, `gas_leverage`,
  `wagner_presence`, `memory_wars`.

## Why

A bare-phenomenon id (`migration_pressures`, `regime_survival`,
`nuclear_arms_control`) is ambiguous the moment a second region has the
same phenomenon -- and every phenomenon eventually has a second region.
Ids are permanent (URLs, event_friction_nodes, narratives_v2,
taxonomy_v3 anchor bundles all reference them), so ambiguity compounds.

## Tests before creating an FN id

1. **The second-region test**: if this phenomenon appeared on another
   continent tomorrow, would the id still unambiguously mean THIS one?
2. **The grep test**: does `grep <id>` across the repo return only this
   FN's concern?
3. **No 2-char geo tokens** (`IS`, `IN` substring hazards -- same rule as
   the anchor spec).
4. **Theaters end in `_theater`**; atomics never do.

## Rename mechanics (when unavoidable)

Ids are referenced by: `event_friction_nodes.fn_id` (FK, NO ACTION),
`narratives_v2.fn_id` (FK, NO ACTION), `taxonomy_v3.linked_id`
(fn_anchor bundles, no FK), `friction_nodes.member_fn_ids` (arrays),
and live URLs `/friction-nodes/<id>`. Use the copy -> repoint children ->
patch arrays -> delete-old pattern from `20260707_fn_id_naming.sql`, and
apply the same migration to Render in the same deploy window.
