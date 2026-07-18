-- latam_hemispheric_theater: replace dead centroid references.
--
-- AMERICAS-CHILE, AMERICAS-ARGENTINA, AMERICAS-PERU and AMERICAS-BOLIVIA
-- do not exist in taxonomy_v3. The real centroids covering those countries
-- are AMERICAS-SOUTHERNCONE (AR/CL/PY/UY) and AMERICAS-ANDEAN (CO/EC/BO/PE/GY),
-- both with active centroid_anchor rows.
--
-- Effect: latam_lithium_minerals stops being blind to every lithium producer
-- except Brazil. Note this only restores the centroid leg of the attribution
-- conjunction -- these atomics still have no fn_anchor bundle and no
-- narratives_v2 rows, so they attribute nothing until those are built.

UPDATE friction_nodes
SET centroid_ids = ARRAY[
        'AMERICAS-USA',
        'ASIA-CHINA',
        'AMERICAS-BRAZIL',
        'AMERICAS-SOUTHERNCONE',
        'AMERICAS-ANDEAN'
    ],
    updated_at = now()
WHERE id = 'latam_hemispheric_theater';

UPDATE friction_nodes
SET centroid_ids = ARRAY[
        'ASIA-CHINA',
        'AMERICAS-USA',
        'AMERICAS-SOUTHERNCONE',
        'AMERICAS-ANDEAN'
    ],
    updated_at = now()
WHERE id = 'latam_lithium_minerals';
