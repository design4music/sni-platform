-- fn_asset_evidence: DERIVED news-evidence links between theater FNs and
-- strategic assets (D-090 mechanism 2, "demonstrated reach", made
-- mechanical). A row means: >= threshold headlines in the last 90 days
-- match the asset's alias AND overlap the theater's centroid_ids -- the
-- same conjunction pattern as fn_anchor attribution.
--
-- Fully recomputable from titles_v3 at any time (rebuilt wholesale by
-- scripts/compute_fn_asset_evidence.py); the ON DELETE CASCADE FKs are
-- safe here precisely because nothing in this table is source data.
-- Static structural links (home territory, economic levers) stay on
-- friction_nodes.affected_asset_ids; this table adds the dynamic,
-- citation-backed layer on top.

CREATE TABLE IF NOT EXISTS fn_asset_evidence (
  fn_id            text NOT NULL REFERENCES friction_nodes(id) ON DELETE CASCADE,
  asset_id         text NOT NULL REFERENCES strategic_assets(id) ON DELETE CASCADE,
  n_titles_30d     int  NOT NULL,
  n_titles_90d     int  NOT NULL,
  last_seen        date,
  sample_title_ids uuid[] NOT NULL DEFAULT '{}',
  computed_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (fn_id, asset_id)
);
