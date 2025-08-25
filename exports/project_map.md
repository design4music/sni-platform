Project Map (brief)

Repository overview
- Language and stack: Primarily Python (ETL, data processing, API); SQL for schema/migrations. No clear Node.js app present.
- Package files: package-lock.json present; package.json not found. Suggests Node tooling is not actively used here.

Key top-level directories
- etl_pipeline/: Main data/ETL pipeline code and Docker configs.
- database_migrations/: SQL migration scripts and change management.
- sql/: SQL queries/verification scripts.
- data/: Data inputs/outputs/configs (details not expanded in this brief).
- scripts/: Operational/maintenance utilities.
- exports/: Generated reports and helper docs (this file lives here).
- tests/: Test assets and checks.
- .github/: CI/automation metadata.

ETL pipeline breakdown (etl_pipeline/)
- api/: API layer/helpers used by pipeline.
- clustering/: Keyword/topic clustering logic and related utilities.
- config/: Centralized configuration.
- core/: Core pipeline utilities/components.
- database/: Database access/helpers for the pipeline.
- extraction/: Content extraction/parsing.
- ingestion/: Data ingestion (feeds, loaders, etc.).
- keywords/: Keyword handling, filtering, and cleanup.
- processing/: Downstream processing stages.
- taxonomy/: Taxonomy/spec assets.
- Docker files: docker-compose.yml (+ override/prod) and Dockerfile for containerized runs.

Notable top-level Python modules/scripts
- strategic_narrative_api.py: API/service entry points and routing.
- database_models.py: ORM/data models.
- deployment_config.py: Deployment/runtime configuration.
- strategic_narrative_schema.sql: Core DB schema definition.
- rss_ingestion.py: RSS/news feed ingestion.
- process_full_corpus.py: End-to-end/full-corpus processing driver.

Environment and docs
- .env and .env.example: Runtime configuration.
- README.md, API_CONTRACT_v1.md, api_documentation.md: Project and API documentation.

Frontend/UI status
- No ui/ folder detected; no package.json present. No dedicated frontend identified in this snapshot.
