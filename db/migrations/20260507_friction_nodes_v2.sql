-- Friction nodes + new narratives shadow architecture
-- 2026-05-07
-- See out/concept_friction_nodes_and_narratives_v2.md for design rationale.
--
-- Strategy: parallel new tables; existing strategic_narratives stays untouched
-- and will be retired later. Shadow-route /friction-nodes/[slug] reads from
-- these new tables only. No confidence scores anywhere; no LLM matcher
-- integration in this slice.
--
-- Naming note: only `narratives_v2` carries the v2 suffix, because the legacy
-- `narratives` table (entity-level media-stance) already occupies the bare name.
-- All other tables (friction_nodes, event_friction_nodes, friction_node_narratives,
-- title_narratives) are net-new and use clean names.

BEGIN;

-- ============================================================
-- friction_nodes : the contested phenomena (curated, atomic)
-- ============================================================
CREATE TABLE IF NOT EXISTS friction_nodes (
    id              text PRIMARY KEY,
    name_en         text NOT NULL,
    name_de         text,
    description_en  text,
    description_de  text,
    centroid_ids    text[],
    topic_keywords  text[],
    is_active       boolean NOT NULL DEFAULT true,
    display_order   int,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_friction_nodes_active ON friction_nodes (is_active);

-- ============================================================
-- narratives_v2 : the framing-explicit narrative library (post-v2 worksheet)
-- ============================================================
CREATE TABLE IF NOT EXISTS narratives_v2 (
    id                 text PRIMARY KEY,
    name_en            text NOT NULL,
    name_de            text,
    claim_en           text NOT NULL,
    claim_de           text,
    actor_centroids    text[] NOT NULL,
    tier               text CHECK (tier IN ('operational', 'ideological')),
    narrative_type     text CHECK (narrative_type IN ('all_in', 'stand_by')),
    framing_keywords   text[],   -- loaded vocabulary, diagnostic
    topic_keywords     text[],   -- neutral routing terms
    is_active          boolean NOT NULL DEFAULT true,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_narratives_v2_active ON narratives_v2 (is_active);
CREATE INDEX IF NOT EXISTS idx_narratives_v2_actor_centroids ON narratives_v2 USING gin (actor_centroids);
CREATE INDEX IF NOT EXISTS idx_narratives_v2_framing_kw ON narratives_v2 USING gin (framing_keywords);
CREATE INDEX IF NOT EXISTS idx_narratives_v2_topic_kw ON narratives_v2 USING gin (topic_keywords);

-- ============================================================
-- friction_node_narratives : which narratives_v2 apply to which FN, with stance
-- ============================================================
CREATE TABLE IF NOT EXISTS friction_node_narratives (
    fn_id            text NOT NULL REFERENCES friction_nodes(id) ON DELETE CASCADE,
    narrative_id     text NOT NULL REFERENCES narratives_v2(id) ON DELETE CASCADE,
    stance_label_en  text NOT NULL,
    stance_label_de  text,
    notes_en         text,
    notes_de         text,
    display_order    int NOT NULL DEFAULT 0,
    created_at       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (fn_id, narrative_id)
);
CREATE INDEX IF NOT EXISTS idx_fn_narratives_fn ON friction_node_narratives (fn_id, display_order);
CREATE INDEX IF NOT EXISTS idx_fn_narratives_narrative ON friction_node_narratives (narrative_id);

-- ============================================================
-- event_friction_nodes : event is about this FN's contested phenomenon
-- (events come in pre-neutralized; this link is "topic match", not "frame match")
-- ============================================================
CREATE TABLE IF NOT EXISTS event_friction_nodes (
    event_id     uuid NOT NULL REFERENCES events_v3(id) ON DELETE CASCADE,
    fn_id        text NOT NULL REFERENCES friction_nodes(id) ON DELETE CASCADE,
    created_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (event_id, fn_id)
);
CREATE INDEX IF NOT EXISTS idx_event_fn_fn ON event_friction_nodes (fn_id);

-- ============================================================
-- title_narratives : title is framed through this narrative's lens
-- (titles preserve framing language; this is where narrative attribution lives)
-- ============================================================
CREATE TABLE IF NOT EXISTS title_narratives (
    title_id       uuid NOT NULL REFERENCES titles_v3(id) ON DELETE CASCADE,
    narrative_id   text NOT NULL REFERENCES narratives_v2(id) ON DELETE CASCADE,
    created_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (title_id, narrative_id)
);
CREATE INDEX IF NOT EXISTS idx_title_narratives_narrative ON title_narratives (narrative_id);
CREATE INDEX IF NOT EXISTS idx_title_narratives_title ON title_narratives (title_id);

COMMIT;
