-- Extend users table with profile, social auth, and paywall fields
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider TEXT DEFAULT 'email';
ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS focus_centroid TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_expires_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT;

-- Extend entity_analyses to support user-submitted analyses
ALTER TABLE entity_analyses ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE entity_analyses ADD COLUMN IF NOT EXISTS input_text TEXT;
ALTER TABLE entity_analyses ADD COLUMN IF NOT EXISTS title TEXT;
