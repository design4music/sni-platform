-- Asset flows: directed structural supply relationships between strategic
-- assets ("Jamnagar receives crude from Ras Tanura via Hormuz"). Rendered
-- on selection only. Every flow must carry as_of + source + confidence --
-- the platform asserts the report, not the fact.

CREATE TABLE IF NOT EXISTS asset_flows (
  id              text PRIMARY KEY,
  commodity       text NOT NULL,
  from_asset      text NOT NULL REFERENCES strategic_assets(id),
  to_asset        text NOT NULL REFERENCES strategic_assets(id),
  via_asset_ids   text[] NOT NULL DEFAULT '{}',
  geometry        jsonb,                            -- LineString, precomputed offline
  magnitude_class text NOT NULL DEFAULT 'secondary', -- major | secondary
  status          text NOT NULL DEFAULT 'active',    -- active | suspended | historical
  as_of           date NOT NULL,
  source          text NOT NULL,
  confidence      text NOT NULL DEFAULT 'high',      -- high | medium | low
  notes           text,
  created_at      timestamptz NOT NULL DEFAULT now()
);
