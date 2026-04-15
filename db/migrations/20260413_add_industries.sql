-- ELO v3.0.1 industries entity field
-- Adds a closed-vocab multi-value industry tag to title_labels.
-- See docs/context/BEATS_TAXONOMY_V3_DRAFT.md and core/ontology.py INDUSTRIES.
-- Reversible: drop the column to roll back.

ALTER TABLE title_labels
    ADD COLUMN IF NOT EXISTS industries text[];

-- Optional: lightweight check to prevent free-form junk. The app-side
-- validation in extract_labels.py is the primary enforcement, but the
-- DB constraint catches drift.
-- NOTE: keeping this permissive (NULL allowed) since most existing rows
-- will not have this field populated until re-extraction.
