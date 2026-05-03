# Archived frontend components

Components retired from active pages but kept importable in case the
comparative analysis surface (which still reads legacy stance-clustered
narrative data) needs them during rewire.

| File | Retired | Reason |
|---|---|---|
| `StanceClusterCard.tsx` | 2026-04-24 (D-071) | Rendered per-event stance clusters from the retired stance-clustered narrative extraction. Removed from the event page sidebar in `f8b0f4e`. Once `/analysis/comparative/...` is rewired off the legacy `narratives` rows, delete outright. |
| `RaiSidebar.tsx` | 2026-05-03 | Coverage Assessment block on event pages. Read `narratives.rai_signals`. Only 93 of 169,646 promoted events ever had this populated (one-shot extraction on 2026-02-19). Will be replaced by the comparative-analysis rewire (Asana 1214268284594725) once it lands. |
| `SignalDashboard.tsx` | 2026-05-03 | Topic Stats block on event pages. Read `narratives.signal_stats`. Only 1,116 of 169,646 events had this. Same retirement context as RaiSidebar. |
