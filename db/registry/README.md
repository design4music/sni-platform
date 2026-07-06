# Strategic Asset Registry

Single source of truth for the strategic-asset map layer. Every asset the
map shows is defined here, in one YAML file per category. The database is
**generated** from these files (`scripts/generate_asset_registry.py`) --
never edited directly. To change the map, edit a registry file and
regenerate.

## Why a registry

Inclusion is **source-anchored**, not editorial guesswork: every asset
cites the ranking authority and the metric that earned its place
(`ranking_source`, `rank_note`). This makes the list reproducible,
auditable, and correctable -- a reviewer can check "top wheat producers by
USDA PSD" and find what's missing. See
`docs/fn_map_data_sources.md` for the per-category authority table.

## Row schema

```yaml
- id: strait_of_hormuz            # stable slug, snake_case, globally unique
  name_en: Strait of Hormuz
  name_de: Strasse von Hormus     # ASCII only: ue/oe/ae/ss
  category: chokepoint            # map display category (drives color/glyph)
  subcategory: strait             # sub-class for future per-type filtering
  asset_type: chokepoint          # facility | port | chokepoint | production_cluster | corridor | pipeline
  # GEOMETRY (specify ONE, or omit entirely to preserve existing DB geometry
  # on reconcile -- existing LineStrings/GEM routes/searoute corridors are
  # never regenerated). New assets provide one of:
  lon: 56.30                      # point [lon, lat] -> Point
  lat: 26.57
  # hull: [[56.0,26.3],[56.6,26.9], ...]   # polygon ring -> Polygon (clusters)
  # line: [[56.0,26.3],[56.6,26.9]]        # LineString (new chokepoints/lanes)
  commodities: [oil, gas]         # lowercase slugs; subcategory-consistent
  centroid_ids: [MIDEAST-GULF]    # ONLY valid centroids_v3 ids; [] if none
  criticality: 5                  # 1-5; 5 = systemic single point of failure
  ranking_source: "EIA World Oil Transit Chokepoints"
  rank_note: "~20% of global petroleum liquids transit; no bypass at scale"
  description_en: >-
    One-sentence strategic description: who depends on it, what breaks.
  description_de: >-
    German translation (ASCII).
```

## Conventions

- **ids are permanent.** Reconciliation matches existing DB rows by id;
  renaming an id retires the old asset and creates a new one.
- **subcategory is the future filter dimension.** Keep it consistent with
  the taxonomy below so a "nuclear only" / "rare earths only" filter is a
  pure data query.
- **Coordinates:** points get lon/lat; production_clusters and corridors
  get a `hull` (4-6 vertex ring, schematic). Generator closes the ring.
- **ASCII only** everywhere (Windows console rule).
- **Every row needs ranking_source + rank_note** -- no unsourced assets.

## Subcategory taxonomy

| category      | subcategories |
|---------------|---------------|
| chokepoint    | strait, canal, sea_route |
| port          | container, energy, bulk, multipurpose |
| oil           | field, refinery, terminal, storage |
| gas           | field, lng_export, lng_import, processing |
| power         | nuclear, hydro, coal, gas_fired, wind, solar |
| minerals      | copper, iron_ore, bauxite, nickel, cobalt, lithium, uranium, rare_earths, gold, tin, graphite, pgm, zinc |
| agriculture   | wheat, rice, corn, soy, palm_oil, sugar, coffee, cocoa, fisheries, fertilizer |
| tech          | semiconductor_fab, data_center, cable_landing, chemicals |
| pipeline      | oil_pipeline, gas_pipeline |
| corridor      | sea_lane |

## Files

One file per category: `chokepoints.yaml`, `ports.yaml`, `oil.yaml`,
`gas.yaml`, `power.yaml`, `minerals.yaml`, `agriculture.yaml`, `tech.yaml`,
`pipelines.yaml`, `corridors.yaml`.
