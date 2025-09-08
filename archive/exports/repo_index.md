Repo Index Snapshot

Top-level directories:
- .claude/
- .git/
- .github/
- .ruff_cache/
- archive/
- data/
- database_migrations/
- etl_pipeline/
- exports/
- scripts/
- sql/
- tests/
- __pycache__/

Top-level notable files:
- README.md
- strategic_narrative_api.py
- api_documentation.md, API_CONTRACT_v1.md
- requirements.txt, requirements.in, requirements.lock.txt, requirements_ingestion.txt
- deployment_config.py, database_models.py
- strategic_narrative_schema.sql and other *.sql (schema, queries, migrations, validation)
- Various utility scripts (ingestion, processing, clustering, verification, tests)
- package-lock.json (note: package.json not found at top-level)

Key folders by role:
- Pipelines: etl_pipeline/
  - Substructure: api/, clustering/, config/, core/, database/, extraction/, ingestion/, keywords/, processing/, taxonomy/
  - Also includes: Dockerfile and docker-compose* files, requirements.txt, README.md
- Backend:
  - strategic_narrative_api.py (Python API at repo root)
  - etl_pipeline/api/ (API component likely used within the pipeline)
- Database (DB):
  - database_migrations/ (SQL migration scripts)
  - sql/ (additional SQL scripts)
  - strategic_narrative_schema.sql (schema definition)
  - database_models.py (ORM/models)
  - etl_pipeline/database/ (pipeline DB utilities/config)
- UI:
  - No dedicated UI directory found (no ui/, frontend/, or web/ detected)

Node package files:
- package.json: NOT FOUND in top-level or etl_pipeline sub-tree (depth<=2 scanned)
- package-lock.json: FOUND at top-level (size: 82 bytes)

Notes / next checks:
- The presence of package-lock.json without package.json suggests either an accidental commit of the lock file or package.json exists deeper or is gitignored. Next step would be to scan remaining subdirectories for package.json by name.
