-- Update regional centroid labels to shorter, cleaner names
-- Run with: psql -U postgres -d sni_v2 -f update_regional_labels.sql

UPDATE centroids_v3 SET label = 'Southern Europe' WHERE id = 'EUROPE-SOUTH';
UPDATE centroids_v3 SET label = 'Nordic Countries' WHERE id = 'EUROPE-NORDIC';
UPDATE centroids_v3 SET label = 'Balkans' WHERE id = 'EUROPE-BALKANS';
UPDATE centroids_v3 SET label = 'Visegrad Group' WHERE id = 'EUROPE-VISEGRAD';

UPDATE centroids_v3 SET label = 'Central America' WHERE id = 'AMERICAS-CENTRAL';
UPDATE centroids_v3 SET label = 'Caribbean' WHERE id = 'AMERICAS-CARIBBEAN';
UPDATE centroids_v3 SET label = 'Andean Region' WHERE id = 'AMERICAS-ANDEAN';
UPDATE centroids_v3 SET label = 'Southern Cone' WHERE id = 'AMERICAS-SOUTHERNCONE';

UPDATE centroids_v3 SET label = 'West Africa' WHERE id = 'AFRICA-WEST';
UPDATE centroids_v3 SET label = 'Central Africa' WHERE id = 'AFRICA-CENTRAL';
UPDATE centroids_v3 SET label = 'East Africa' WHERE id = 'AFRICA-EAST';
UPDATE centroids_v3 SET label = 'Southern Africa' WHERE id = 'AFRICA-SOUTHERN';
UPDATE centroids_v3 SET label = 'Sahel Region' WHERE id = 'AFRICA-SAHEL';
UPDATE centroids_v3 SET label = 'Horn of Africa' WHERE id = 'AFRICA-HORN';

UPDATE centroids_v3 SET label = 'Southeast Asia' WHERE id = 'ASIA-SOUTHEAST';
UPDATE centroids_v3 SET label = 'Central Asia' WHERE id = 'ASIA-CENTRAL';
UPDATE centroids_v3 SET label = 'South Asia' WHERE id = 'ASIA-SOUTHASIA';

UPDATE centroids_v3 SET label = 'Levant' WHERE id = 'MIDEAST-LEVANT';
UPDATE centroids_v3 SET label = 'Maghreb' WHERE id = 'MIDEAST-MAGHREB';
UPDATE centroids_v3 SET label = 'Gulf States' WHERE id = 'MIDEAST-GULF';

UPDATE centroids_v3 SET label = 'Melanesia' WHERE id = 'OCEANIA-MELANESIA';
UPDATE centroids_v3 SET label = 'Micronesia' WHERE id = 'OCEANIA-MICRONESIA';
UPDATE centroids_v3 SET label = 'Polynesia' WHERE id = 'OCEANIA-POLYNESIA';

-- Verify changes
SELECT id, label, iso_codes FROM centroids_v3 WHERE id LIKE '%-' AND array_length(iso_codes, 1) > 3 ORDER BY label;
