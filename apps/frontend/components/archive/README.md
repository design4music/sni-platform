# Archived frontend components

Components retired from active pages but kept importable in case the
comparative analysis surface (which still reads legacy stance-clustered
narrative data) needs them during rewire.

| File | Retired | Reason |
|---|---|---|
| `StanceClusterCard.tsx` | 2026-04-24 (D-071) | Rendered per-event stance clusters from the retired stance-clustered narrative extraction. Removed from the event page sidebar in `f8b0f4e`. Once `/analysis/comparative/...` is rewired off the legacy `narratives` rows, delete outright. |
