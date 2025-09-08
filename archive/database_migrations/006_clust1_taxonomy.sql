-- 006_clust1_taxonomy.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Taxonomy
CREATE TABLE IF NOT EXISTS taxonomy_topics (
  topic_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('IPTC','GDELT','WIKIDATA')),
  parent_id TEXT NULL,
  path TEXT[]
);
CREATE TABLE IF NOT EXISTS taxonomy_aliases (
  topic_id TEXT REFERENCES taxonomy_topics(topic_id) ON DELETE CASCADE,
  alias TEXT NOT NULL,
  lang CHAR(2),
  PRIMARY KEY (topic_id, alias, lang)
);
CREATE INDEX IF NOT EXISTS idx_taxonomy_aliases_alias_trgm
  ON taxonomy_aliases USING GIN (alias gin_trgm_ops);

CREATE TABLE IF NOT EXISTS taxonomy_mappings (
  from_source TEXT NOT NULL,
  from_id TEXT NOT NULL,
  to_topic_id TEXT NOT NULL REFERENCES taxonomy_topics(topic_id),
  PRIMARY KEY (from_source, from_id)
);

-- Article -> topic
CREATE TABLE IF NOT EXISTS article_topics (
  article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
  topic_id TEXT REFERENCES taxonomy_topics(topic_id),
  score NUMERIC,
  source TEXT,
  PRIMARY KEY (article_id, topic_id)
);
CREATE INDEX IF NOT EXISTS idx_article_topics_topic ON article_topics(topic_id);
CREATE INDEX IF NOT EXISTS idx_article_topics_article ON article_topics(article_id);

-- Clusters
CREATE TABLE IF NOT EXISTS article_clusters (
  cluster_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  topic_key TEXT NOT NULL,
  top_topics TEXT[] NOT NULL,
  label TEXT,                              -- short human label
  lang CHAR(2),                            -- NULL = mixed-language cluster
  time_window TSTZRANGE NOT NULL,
  size INT NOT NULL,
  cohesion NUMERIC,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_clusters_topics ON article_clusters USING GIN (top_topics);
CREATE INDEX IF NOT EXISTS idx_clusters_lang ON article_clusters(lang);
CREATE INDEX IF NOT EXISTS idx_clusters_window ON article_clusters USING GIST (time_window);

CREATE TABLE IF NOT EXISTS article_cluster_members (
  cluster_id UUID REFERENCES article_clusters(cluster_id) ON DELETE CASCADE,
  article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
  weight NUMERIC,
  PRIMARY KEY (cluster_id, article_id)
);
CREATE INDEX IF NOT EXISTS idx_cluster_members_article ON article_cluster_members(article_id);