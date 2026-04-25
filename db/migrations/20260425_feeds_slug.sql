-- Add a stable, URL-safe slug to feeds for per-outlet routes.
--
-- Backfilled by scripts/backfill_feed_slugs.py which:
--   - lowercases + transliterates German umlauts (ü->ue, ö->oe, ä->ae, ß->ss)
--   - strips remaining diacritics
--   - replaces non-alphanumeric runs with "-"
--   - trims leading/trailing "-"
--   - appends "-<lang>" on collisions, then numeric suffix as a final tiebreaker
--
-- Examples:
--   "Der Spiegel"      -> der-spiegel
--   "Süddeutsche Zeitung" -> sueddeutsche-zeitung
--   "TASS"             -> tass
--   "TASS Russian"     -> tass-russian      (no collision yet)
--   collision case:    -> tass / tass-en (if a second outlet's slug clashes)

ALTER TABLE feeds
    ADD COLUMN IF NOT EXISTS slug TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_feeds_slug ON feeds (slug)
    WHERE slug IS NOT NULL;
