-- Pull pipelines and sea corridors off the map. Hand-drawn waypoint
-- routes read as untrustworthy next to precisely-placed point assets.
-- Rows stay (is_active = false) so re-activation with properly mapped
-- geometries (e.g. Global Energy Monitor GeoJSON) is a one-line flip.

UPDATE strategic_assets SET is_active = false
WHERE asset_type IN ('pipeline', 'corridor');
