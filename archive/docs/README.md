# SNI Documentation (Starter Kit)

_Last updated: 2025-08-18 • Owner: Max (PO) • Maintainers: Claude Code, Agent_

This `/docs` folder is docs-as-code. Keep entries short and uniform.

## Lightweight index page

| Area            | Doc                     | Status        | Owner       | Last Updated |
|-----------------|-------------------------|---------------|-------------|--------------|
| Vision          | north-star.md           | draft         | Max         | 2025-08-18   |
| Architecture    | system-overview.md      | draft         | Max         | …            |
| Data            | schema-erd.md           | needs update  | Claude Code | …            |
| Pipelines       | clust-2.md              | WIP           | Claude Code | …            |
| Components      | keyworder.md            | draft         | Agent       | …            |
| Ops             | runbooks.md             | todo          | —           | —            |
| Decisions       | adr-0001.md             | draft         | Max         | …            |
| Glossary        | glossary.md             | WIP           | Max         | …            |


## Folder map

/docs
  /00-vision
    north-star.md            # 1-page product vision + non-goals
  /01-architecture
    system-overview.md       # box-and-arrows + dataflow
    environments.md          # local/staging/prod, secrets, keys
  /02-data
    schema-erd.md            # ERD + table inventory
    tables/                  # one file per table
      keywords.md
      keyword_canon_map.md
      article_clusters.md
      ...
  /03-pipelines
    clust-1.md               # Thematic grouping
    clust-2.md               # Narrative clustering (current focus)
    gen-1.md                 # Narrative builder
  /04-components
    extractor.md
    entity-recognizer.md
    keyworder.md
    clustering.md
    labeling.md
    digest-assembler.md
  /05-config
    thresholds.md            # all magic numbers live here
  /06-ops
    runbooks.md              # how to run, rerun, recover
    playbooks.md             # common incidents + fixes
    observability.md         # logs, metrics, alerts
  /07-quality
    gates.md                 # silhouette, min size, etc.
    metrics.md               # coverage, purity, orphan rate
  /08-decisions
    adr-0001.md              # Architecture Decision Records
  /09-glossary
    glossary.md              # canonical terms

