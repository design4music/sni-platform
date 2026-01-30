"""
Phase 3.1: Event Label + Signal Extraction

Extracts structured event labels from titles using ELO (Event Label Ontology) v2.0.
Labels follow: PRIMARY_ACTOR -> ACTION_CLASS -> DOMAIN (-> OPTIONAL_TARGET)
Also extracts typed signals (persons, orgs, places, etc.) and entity_countries.

Position in pipeline: After Phase 2 (centroid matching), before Phase 3.2 (entity backfill)
"""
