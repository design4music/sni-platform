INSERT INTO taxonomy_categories (category_id, name_en, is_positive) VALUES ('politics_elections', 'Politics – Elections', TRUE) ON CONFLICT (category_id) DO NOTHING;
INSERT INTO taxonomy_categories (category_id, name_en, is_positive) VALUES ('politics_diplomacy', 'Politics – Diplomacy', TRUE) ON CONFLICT (category_id) DO NOTHING;
INSERT INTO taxonomy_categories (category_id, name_en, is_positive) VALUES ('politics_legislation', 'Politics – Legislation', TRUE) ON CONFLICT (category_id) DO NOTHING;
INSERT INTO taxonomy_categories (category_id, name_en, is_positive) VALUES ('politics_governance', 'Politics – Governance', TRUE) ON CONFLICT (category_id) DO NOTHING;
INSERT INTO taxonomy_categories (category_id, name_en, is_positive) VALUES ('politics_international_relations', 'Politics – International relations', TRUE) DO NOTHING;
INSERT INTO taxonomy_categories (category_id, name_en, is_positive) VALUES ('politics_ideology', 'Politics – Ideology', TRUE) ON CONFLICT (category_id) DO NOTHING;
INSERT INTO taxonomy_categories (category_id, name_en, is_positive) VALUES ('politics_movements', 'Politics – Movements', TRUE) ON CONFLICT (category_id) DO NOTHING;