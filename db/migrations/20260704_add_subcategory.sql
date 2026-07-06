-- Sub-class dimension for the strategic-asset map (nuclear vs hydro,
-- rare_earths vs copper, ...). Populated from the registry; enables future
-- per-type map filtering as a pure data query, no re-curation.
ALTER TABLE strategic_assets ADD COLUMN IF NOT EXISTS subcategory text;
