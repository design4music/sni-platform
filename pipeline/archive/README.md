# Archived pipeline modules

Modules retired from the active pipeline but kept importable for read-only
access to legacy data. Do not wire these into the daemon, freeze, or any
new script.

| File | Retired | Reason |
|---|---|---|
| `score_publisher_stance.py` | 2026-04-24 (D-071) | Per-publisher LLM stance scoring replaced by `outlet_entity_stance` matrix (D-072). Reads/writes the legacy `publisher_stance` table. |
| `extract_stance_narratives.py` | 2026-04-24 (D-071) | Per-event stance-clustered narrative extraction. Reads/writes legacy `narratives WHERE extraction_method='stance_clustered'`. The `/extract` event branch in `api/extraction_api.py` returns 410. |

Both produced data that the comparative analysis pages
(`/analysis/comparative/...`, `/analysis/user/...`) still read. Once those
pages are rewired off the legacy tables (Asana 1214268284594725), these
modules can be deleted outright.
