-- Add extraction_profile column to news_feeds table
-- LLM-learned per-feed extraction profiles

ALTER TABLE news_feeds
ADD COLUMN IF NOT EXISTS extraction_profile JSONB;

COMMENT ON COLUMN news_feeds.extraction_profile IS
'Per-feed/domain extraction profile learned by LLM. JSON schema: {version, scope, main_selector, title_selector, date_selector, author_selector, remove_selectors[], allow_tags[], junk_phrases[], pre_clean_regex[], post_clean_regex[], min_length, density_threshold, last_validated_at, source, notes}';