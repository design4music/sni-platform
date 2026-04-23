# LLM Cost Audit — 2026-04-22 (revised 2026-04-23)

**Trigger**: DeepSeek bill roughly doubled after pipeline v4.0 (day-centric
promotion, calendar views, centroid summaries). Pipeline stopped 2026-04-22
pending fixes. User reviewed findings 2026-04-23 and approved a tightened plan.

**Scope**: LLM call sites on the live daemon path. Excludes on-demand
extraction (RAI, user-triggered narrative extraction).

---

## 1. Where LLMs are called

| # | Phase | File | Slot | Trigger | Call shape |
|---|---|---|---|---|---|
| 1 | 2.1 Labels | `pipeline/phase_3_1/extract_labels.py` | Slot 2, 15 m | Unlabeled titles, batch=25, concur=5 | ~600 in → up to 4000 out |
| 2 | 5.1a Event prose (full) | `pipeline/phase_4/promote_and_describe_4_5a.py` → `llm_title_and_summary` | Slot 4, 3 h | Promoted ≥ 5 src, `title_de IS NULL` | EN+DE single-shot, 600–1400 out |
| 3 | 5.1b Title only | same file → `llm_title_only` | Slot 4 | Promoted < 5 src, no English source | ~200 in → 200 out |
| 4 | 5.1c DE batch translate | same file → `batch_translate_titles_de` | Slot 4 | mechanical-EN path, 20 titles/call | ~500 in → 1600 out |
| 5 | 5.2 Daily briefs | `pipeline/phase_4/generate_daily_brief_4_5d.py` | Slot 4 | Closed day × CTM with > 5 promoted | ~2000 in → up to 1500 out |
| 6 | 5.3 Narrative discovery | `pipeline/phase_4/match_narratives_llm.py` | Slot 4 | 142 ideological narratives, `only_new=True` | ~1500 in → up to 4000 out |
| 7 | 5.4 Narrative review | `pipeline/phase_4/review_narratives_llm.py` | Slot 4 | Operational matches not yet LLM-reviewed | ~2500 in → 500 out |
| 8 | **5.5 Centroid summaries** 🆕 2026-04-20 | `pipeline/phase_5/generate_centroid_summary.py` | Slot 4, 24 h time-stale, 100/run | ~285 active centroids, tier-1 bilingual | ~1500 in → **3000 out** |

---

## 2. Observed volumes (local DB, April through Apr 16)

- 274 active CTMs in April, **285 centroids** active on Render.
- 16 386 promoted events in April; 1 024 are ≥ 5 src.
- Small events: ~73% have an English source (mechanical + DE-batch), ~27% need
  LLM title calls (foreign-only → English translation required for SEO).
- 944 daily briefs across 15 days → **~63/day avg, peaks 100**.
- ~1 850 titles/day labeled → ~75 Phase 2.1 calls/day.

## 3. Estimated steady-state cost

| Phase | Calls/day | Tokens/day |
|---|---|---|
| 2.1 Labels | ~75 | ~375 k |
| 5.1a full prose | ~100 | ~200 k |
| 5.1b title only | ~400 | ~160 k |
| 5.1c DE batch | ~55 | ~130 k |
| 5.2 daily briefs | ~65 | ~230 k |
| 5.3 narrative discovery | ~80 | ~250 k |
| 5.4 narrative review | ~50 | ~125 k |
| **5.5 centroid summaries** | **~285** | **~1.3 M** |
| **Total** | | **~2.8 M tokens/day** |

---

## 4. Why the bill doubled — the five drivers

**4.1 Phase 5.5 is new since 2026-04-20 (D-065).** Biggest new line item.
`max_tokens=3000` tier-1 bilingual × ~285 centroids × 24 h staleness timer =
~1.3 M tokens/day of pure new cost. Plus a one-time ~1 M-token backfill.

**4.2 Per-event prose replaced per-CTM digests (D-058 + D-059).** Old world:
~150 CTM digest calls/month. New world: ~3 000 event-prose calls/day. Order
of magnitude jump. *Kept by design* — user confirmed every promoted event
needs a page.

**4.3 Bilingual single-shot everywhere (D-034).** ~2× output tokens per
call across 5.1 / 5.2 / 5.5. *Kept by design* — user confirmed DE pages need
to be pre-generated for DE traffic.

**4.4 Daily briefs (5.2) is a new ongoing phase.** ~65 briefs/day × ~3500
tokens. *Kept by design* — user confirmed daily-brief pages are standalone
SEO targets; calendar UI embeds them but each day should rank individually.

**4.5 The April bill includes a one-time reprocess spike.** Jan/Feb/Mar
reprocess (D-061) consumed ~88 M tokens / ~€20. One-off, drops out of May.

**Conclusion**: of the structural drivers (4.1–4.4), only 4.1 is a true
anti-pattern — **time-based regeneration of content that hasn't actually
changed**. 4.2–4.4 are load-bearing for the SEO/content strategy.

---

## 5. The five questions — resolved

| Q | Question | Decision |
|---|---|---|
| Q1 | Does every promoted event need LLM prose? | **Yes** — every promoted event is a page; user-facing product requires it. |
| Q2 | 5.5 on-demand vs daemon? | **Daemon stays** — centroid pages need pre-generated content for Google. But **trigger must be content-change, not time**. |
| Q3 | DE lazy vs eager? | **Eager stays** — DE pages are for DE traffic; we need them indexable. |
| Q4 | Daily briefs vs calendar UI? | **Briefs stay** — individual days must rank as standalone pages. |
| Q5 | Telemetry? | **Yes, add it.** Prerequisite for all future cost discussions. |

---

## 6. Plan (approved 2026-04-23)

Five items. Ordered for safe execution; all land in one coherent change set.

### 6.1 Phase 5.5 content-based regeneration (**the real fix**)
Add `source_fingerprint` column to `centroid_summaries`. On each run, compute
the fingerprint from the current top-N events per track. Skip regeneration if
stored fingerprint matches. Keep a 7-day hard-max so stale-but-unchanged
centroids still get occasional refreshes.

**Files**: migration + `pipeline/phase_5/generate_centroid_summary.py` +
daemon query in `pipeline_daemon.py`.

### 6.2 5.5 tier-1 `max_tokens` 3000 → 1500
Output ceiling. Real responses run ~1000–1300 tokens; 3000 just lets the
model ramble when it wants to.

**Files**: `pipeline/phase_5/generate_centroid_summary.py` line 458.

### 6.3 Persist daemon `last_run` across restarts
New table `daemon_state(slot_name, last_run)`. Daemon reads on start,
writes after each slot completion. Fixes the "every deploy re-fires every
slot" cost leak.

**Files**: migration + `pipeline/runner/pipeline_daemon.py`.

### 6.4 Per-phase token logger
New table `llm_stats(phase, tokens_in, tokens_out, latency_ms, model,
status, created_at)`. Helper `core/llm_logger.py`. Best-effort writes
(never raise). Wrap every `call_llm`-like site in 8 phases. Afterward:
`SELECT phase, SUM(tokens_out) FROM llm_stats WHERE created_at::date = ...`
answers "who burned what" in one query.

**Files**: migration + new `core/llm_logger.py` + touch all 8 LLM phases.

### 6.5 Turn off worker `autoDeploy`
`render.yaml` currently has `autoDeploy: true` on the worker. Every commit
to main restarts the daemon. Combined with non-persisted `last_run` this
multiplies slot firings per deploy. Flip to `autoDeploy: false` on the
worker; keep web app on auto.

**Files**: `render.yaml`.

---

## 7. Explicitly *not* doing (from my first-pass list)

- ~~5.5 staleness 24 h → 72 h~~ — superseded by 6.1 (content-based beats any time window).
- ~~5.2 `DAILY_BRIEF_MIN_CLUSTERS` 5 → 8~~ — would reduce coverage of standalone day-pages, hurts SEO. Kept at 5.
- ~~5.2 `max_tokens` 1500 → 1000~~ — same risk of cutting real briefs short.
- ~~Demote 5.1b to mechanical~~ — foreign-only clusters still need an English title for indexable pages.
- ~~Structural restructures (Q1-Q4)~~ — user validated the current architecture.

## 8. What to read next

- `docs/context/PIPELINE_V4_ARCHITECTURE.md` — phase inventory + slot map.
- `docs/context/30_DecisionLog.yml` — D-030, D-034, D-058, D-059, D-065 shape
  current cost structure.
- `pipeline/runner/pipeline_daemon.py` — slot intervals + 5.5 budget caps.
- `pipeline/phase_5/generate_centroid_summary.py` — full 5.5 implementation.
