# Glossary

*Last updated: 2025-08-18 • Status: draft • Owner: Max (PO) / Claude Code (Engineer) • Repo: SNI*

* Keyword, Canonical form, Seed bucket, Hub term, Orphan, Centroid, Silhouette.
  
* Keyword: normalized 1–3 word n-gram used as a feature; cleaned, lemmatized, language-tagged.
* Canonical form: standard lexeme we map all variants to (“sanction” for “sanctions”).
* keyword\_canon\_map: surface variants → canonical form (+ link to canonical keyword row).
* Entity: named thing (person/org/place/event) with a stable ID.
* Seed bucket: first-pass grouping by lexical/Entity overlap before embeddings.
* Hub term: over-common token (top ~1%) that dilutes clustering; often removed.
* Orphan: item that didn’t meet min cluster size; shown as “thin signal”.
* Centroid: mean embedding vector of a cluster.
* Silhouette: cohesion/separation score in \[−1..1]; higher = better clustering.
* k-distance knee: heuristic to choose DBSCAN eps from nearest-neighbor curve.
* Cohesion: internal similarity metric we store per cluster.
* Digest: compact cluster summary (key facts + 2–3 reps).
* Macro cluster: merged clusters describing the same narrative arc.
* Thresholds: all tunable numbers collected in /05-config/thresholds.md.
