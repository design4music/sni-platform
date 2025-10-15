-- public.centroids definition

-- Drop table

-- DROP TABLE public.centroids;

CREATE TABLE public.centroids (
	id varchar(50) NOT NULL,
	"label" text NOT NULL,
	keywords _text DEFAULT '{}'::text[] NULL,
	actors _text DEFAULT '{}'::text[] NULL,
	theaters _text DEFAULT '{}'::text[] NULL,
	created_at timestamp DEFAULT now() NULL,
	updated_at timestamp DEFAULT now() NULL,
	CONSTRAINT centroids_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_centroids_actors ON public.centroids USING gin (actors);
CREATE INDEX idx_centroids_keywords ON public.centroids USING gin (keywords);
CREATE INDEX idx_centroids_theaters ON public.centroids USING gin (theaters);

-- Table Triggers

create trigger update_centroids_updated_at before
update
    on
    public.centroids for each row execute function update_updated_at_column();


-- public.event_families definition

-- Drop table

-- DROP TABLE public.event_families;

CREATE TABLE public.event_families (
	id uuid DEFAULT gen_random_uuid() NOT NULL,
	title text NOT NULL,
	summary text NOT NULL,
	key_actors _text DEFAULT '{}'::text[] NULL,
	event_type text NOT NULL,
	primary_theater text NULL,
	source_title_ids _text DEFAULT '{}'::text[] NULL,
	confidence_score numeric(3, 2) NOT NULL,
	coherence_reason text NOT NULL,
	created_at timestamp DEFAULT now() NULL,
	updated_at timestamp DEFAULT now() NULL,
	processing_notes text NULL,
	ef_key varchar(64) NULL,
	status varchar(20) DEFAULT 'active'::character varying NULL,
	merged_into uuid NULL,
	merge_rationale text NULL,
	events jsonb DEFAULT '[]'::jsonb NULL,
	tags jsonb DEFAULT '[]'::jsonb NULL,
	ef_context jsonb DEFAULT '{}'::jsonb NULL,
	CONSTRAINT chk_event_type CHECK ((event_type = ANY (ARRAY['Strategy/Tactics'::text, 'Humanitarian'::text, 'Alliances/Geopolitics'::text, 'Diplomacy/Negotiations'::text, 'Sanctions/Economy'::text, 'Domestic Politics'::text, 'Procurement/Force-gen'::text, 'Tech/Cyber/OSINT'::text, 'Legal/ICC'::text, 'Information/Media/Platforms'::text, 'Energy/Infrastructure'::text]))),
	CONSTRAINT chk_primary_theater CHECK ((primary_theater = ANY (ARRAY['UKRAINE'::text, 'GAZA'::text, 'TAIWAN_STRAIT'::text, 'IRAN_NUCLEAR'::text, 'EUROPE_SECURITY'::text, 'US_DOMESTIC'::text, 'CHINA_TRADE'::text, 'MEAST_REGIONAL'::text, 'CYBER_GLOBAL'::text, 'CLIMATE_GLOBAL'::text, 'AFRICA_SECURITY'::text, 'KOREA_PENINSULA'::text, 'LATAM_REGIONAL'::text, 'ARCTIC'::text, 'GLOBAL_SUMMIT'::text]))),
	CONSTRAINT event_families_confidence_score_check CHECK (((confidence_score >= 0.0) AND (confidence_score <= 1.0))),
	CONSTRAINT event_families_pkey PRIMARY KEY (id)
);
CREATE UNIQUE INDEX idx_ef_key_active ON public.event_families USING btree (ef_key) WHERE ((status)::text = 'active'::text);
CREATE INDEX idx_event_families_confidence ON public.event_families USING btree (confidence_score DESC);
CREATE INDEX idx_event_families_created_at ON public.event_families USING btree (created_at DESC);
CREATE INDEX idx_event_families_ef_context ON public.event_families USING gin (ef_context);
CREATE INDEX idx_event_families_enrichment_queue ON public.event_families USING btree (status, created_at DESC) WHERE ((status)::text = 'seed'::text);
COMMENT ON INDEX public.idx_event_families_enrichment_queue IS 'Optimized for get_enrichment_queue() single query';
CREATE INDEX idx_event_families_primary_theater ON public.event_families USING btree (primary_theater);
CREATE INDEX idx_event_families_status ON public.event_families USING btree (status) WHERE ((status)::text = 'seed'::text);
COMMENT ON INDEX public.idx_event_families_status IS 'Speeds up P4 enrichment queue queries';
CREATE INDEX idx_status ON public.event_families USING btree (status);
CREATE INDEX idx_theater_type_active ON public.event_families USING btree (primary_theater, event_type) WHERE ((status)::text = 'active'::text);


-- public.feeds definition

-- Drop table

-- DROP TABLE public.feeds;

CREATE TABLE public.feeds (
	id uuid DEFAULT gen_random_uuid() NOT NULL,
	"name" varchar(255) NOT NULL,
	url text NOT NULL,
	language_code varchar(5) NOT NULL,
	country_code varchar(3) NULL,
	is_active bool DEFAULT true NULL,
	priority int4 DEFAULT 1 NULL,
	fetch_interval_minutes int4 DEFAULT 60 NULL,
	created_at timestamp DEFAULT now() NULL,
	updated_at timestamp DEFAULT now() NULL,
	source_domain text NULL,
	etag text NULL,
	last_modified text NULL,
	last_pubdate_utc timestamptz NULL,
	last_run_at timestamptz NULL,
	CONSTRAINT feeds_pkey PRIMARY KEY (id),
	CONSTRAINT feeds_url_key UNIQUE (url)
);
CREATE INDEX idx_feeds_active ON public.feeds USING btree (is_active) WHERE (is_active = true);
CREATE INDEX idx_feeds_is_active ON public.feeds USING btree (is_active) WHERE (is_active = true);
CREATE INDEX idx_feeds_language ON public.feeds USING btree (language_code);


-- public.runs definition

-- Drop table

-- DROP TABLE public.runs;

CREATE TABLE public.runs (
	id uuid DEFAULT gen_random_uuid() NOT NULL,
	phase varchar(20) NOT NULL,
	prompt_version varchar(50) NULL,
	input_ref text NULL,
	output_ref jsonb NULL,
	tokens_used int4 DEFAULT 0 NULL,
	cost_usd numeric(10, 4) DEFAULT 0 NULL,
	bucket_token_count int4 NULL,
	bucket_cost_estimate numeric(10, 4) NULL,
	created_at timestamp DEFAULT now() NULL,
	CONSTRAINT runs_pkey PRIMARY KEY (id)
);
CREATE INDEX idx_runs_phase ON public.runs USING btree (phase, created_at);


-- public.framed_narratives definition

-- Drop table

-- DROP TABLE public.framed_narratives;

CREATE TABLE public.framed_narratives (
	id uuid DEFAULT gen_random_uuid() NOT NULL,
	event_family_id uuid NOT NULL,
	frame_type text NOT NULL,
	frame_description text NOT NULL,
	stance_summary text NOT NULL,
	supporting_headlines _text DEFAULT '{}'::text[] NULL,
	supporting_title_ids _text DEFAULT '{}'::text[] NULL,
	key_language _text DEFAULT '{}'::text[] NULL,
	prevalence_score numeric(3, 2) NOT NULL,
	evidence_quality numeric(3, 2) NOT NULL,
	created_at timestamp DEFAULT now() NULL,
	updated_at timestamp DEFAULT now() NULL,
	rai_analysis jsonb NULL,
	CONSTRAINT framed_narratives_evidence_quality_check CHECK (((evidence_quality >= 0.0) AND (evidence_quality <= 1.0))),
	CONSTRAINT framed_narratives_pkey PRIMARY KEY (id),
	CONSTRAINT framed_narratives_prevalence_score_check CHECK (((prevalence_score >= 0.0) AND (prevalence_score <= 1.0))),
	CONSTRAINT framed_narratives_event_family_id_fkey FOREIGN KEY (event_family_id) REFERENCES public.event_families(id) ON DELETE CASCADE
);
CREATE INDEX idx_framed_narratives_event_family ON public.framed_narratives USING btree (event_family_id);
CREATE INDEX idx_framed_narratives_prevalence ON public.framed_narratives USING btree (prevalence_score DESC);
CREATE INDEX idx_framed_narratives_rai_analyzed ON public.framed_narratives USING btree (event_family_id) WHERE (rai_analysis IS NOT NULL);
CREATE INDEX idx_framed_narratives_rai_pending ON public.framed_narratives USING btree (created_at DESC) WHERE (rai_analysis IS NULL);


-- public.titles definition

-- Drop table

-- DROP TABLE public.titles;

CREATE TABLE public.titles (
	id uuid DEFAULT gen_random_uuid() NOT NULL,
	feed_id uuid NULL,
	title_original text NOT NULL,
	title_display text NOT NULL,
	url_gnews text NOT NULL,
	publisher_name varchar(255) NULL,
	publisher_domain varchar(255) NULL,
	pubdate_utc timestamp NULL,
	content_hash varchar(64) NULL,
	detected_language varchar(5) NULL,
	language_confidence float8 NULL,
	entities jsonb NULL,
	ingested_at timestamp DEFAULT now() NULL,
	created_at timestamp DEFAULT now() NULL,
	title_norm text NULL,
	gate_keep bool DEFAULT false NOT NULL,
	event_family_id uuid NULL,
	CONSTRAINT titles_content_hash_feed_id_key UNIQUE (content_hash, feed_id),
	CONSTRAINT titles_pkey PRIMARY KEY (id),
	CONSTRAINT uq_titles_hash_feed UNIQUE (content_hash, feed_id),
	CONSTRAINT titles_event_family_id_fkey FOREIGN KEY (event_family_id) REFERENCES public.event_families(id),
	CONSTRAINT titles_feed_id_fkey FOREIGN KEY (feed_id) REFERENCES public.feeds(id)
);
CREATE INDEX idx_titles_event_family_id ON public.titles USING btree (event_family_id);
COMMENT ON INDEX public.idx_titles_event_family_id IS 'Speeds up P3 EF member lookups';
CREATE INDEX idx_titles_feed ON public.titles USING btree (feed_id);
CREATE INDEX idx_titles_gate_keep ON public.titles USING btree (gate_keep) WHERE (gate_keep = true);
COMMENT ON INDEX public.idx_titles_gate_keep IS 'Speeds up strategic title filtering';
CREATE INDEX idx_titles_hash ON public.titles USING btree (content_hash);
CREATE INDEX idx_titles_ingested_at ON public.titles USING btree (ingested_at DESC);
CREATE INDEX idx_titles_language ON public.titles USING btree (detected_language);
CREATE INDEX idx_titles_pubdate_utc ON public.titles USING btree (pubdate_utc DESC);
CREATE INDEX idx_titles_published ON public.titles USING btree (pubdate_utc);
CREATE INDEX idx_titles_strategic_ready ON public.titles USING btree (gate_keep, event_family_id) WHERE ((gate_keep = true) AND (event_family_id IS NULL));
COMMENT ON INDEX public.idx_titles_strategic_ready IS 'Composite index for most common P3 query pattern';
CREATE INDEX idx_titles_unassigned ON public.titles USING btree (gate_keep, event_family_id) WHERE ((gate_keep = true) AND (event_family_id IS NULL));

