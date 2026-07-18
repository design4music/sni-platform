-- Add primary_target column to friction_nodes
-- Specifies the main geographic focus/target of the friction node
-- Used to disambiguate events in multi-centroid theaters
-- 2026-06-21

ALTER TABLE friction_nodes
ADD COLUMN primary_target TEXT;

-- Create index for performance
CREATE INDEX idx_friction_nodes_primary_target ON friction_nodes(primary_target);

-- Comment for clarity
COMMENT ON COLUMN friction_nodes.primary_target IS
  'Primary geographic target of this friction node. Used in event matching to disambiguate keywords across theaters. E.g., australia_china_theater has primary_target=OCEANIA-AUSTRALIA so "strike capacity" only matches events affecting Australia, not Taiwan.';
