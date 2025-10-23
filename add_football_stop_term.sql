-- Add generic football/soccer terms to STOP_LIST
-- These are broad sport terms that should block non-strategic content

-- Insert football term
INSERT INTO taxonomy_terms (category_id, name_en, terms, is_active)
VALUES (
    'sport_football',
    'football',
    '{
        "head_en": "football",
        "aliases": {
            "en": ["football", "soccer"],
            "es": ["fútbol", "futbol"],
            "de": ["Fußball", "Fussball"],
            "fr": ["football"],
            "ru": ["футбол"],
            "ar": ["كرة القدم"],
            "zh": ["足球"]
        }
    }'::jsonb,
    TRUE
)
ON CONFLICT DO NOTHING;
