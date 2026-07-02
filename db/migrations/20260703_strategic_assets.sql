-- Strategic assets: static geopolitical/economic infrastructure layer.
-- Phase 1 of the risk-intelligence direction: assets are the stable ground
-- truth; friction nodes press on them; stress renders on the map.
-- Later phases (asset_flows dependency table) are additive and do not
-- modify this schema.

CREATE TABLE IF NOT EXISTS strategic_assets (
  id             text PRIMARY KEY,        -- slug, e.g. 'strait_of_hormuz'
  name_en        text NOT NULL,
  name_de        text,
  asset_type     text NOT NULL,           -- chokepoint | port | pipeline | production_cluster | corridor | facility
  geometry       jsonb NOT NULL,          -- GeoJSON geometry: Point | LineString | Polygon ([lon, lat] order)
  commodities    text[] NOT NULL DEFAULT '{}',
  centroid_ids   text[] NOT NULL DEFAULT '{}',  -- existing centroids_v3 ids this asset touches
  criticality    smallint NOT NULL DEFAULT 3,   -- 1-5, hand-assigned strategic importance
  meta           jsonb,                   -- type-specific attributes (capacity, throughput, operator)
  description_en text,
  description_de text,
  is_active      boolean NOT NULL DEFAULT true,
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now()
);

-- FNs press on assets. Empty array = no assets assigned (yet).
ALTER TABLE friction_nodes ADD COLUMN IF NOT EXISTS affected_asset_ids text[] NOT NULL DEFAULT '{}';

-- 'regional' FNs render via their assets on the map.
-- 'global' FNs (US-China, US-Russia...) are relationships, not places:
-- they render in the strategic-competitions strip, never as map geometry.
ALTER TABLE friction_nodes ADD COLUMN IF NOT EXISTS scope text NOT NULL DEFAULT 'regional';
