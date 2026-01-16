# SNI — Engineering Playbook (Appendix D)

**Audience:** AI builders (Claude Code, DeepSeek, etc.) and human reviewers.

**Scope:** Project‑specific guardrails for building and running SNI. Keep this document living; update with small diffs and log changes in `docs/CHANGELOG.md`.

**Cross‑links:**

- Main concept/context: *sni_headlines_narrative_intelligence_context_pack_v_1.md*
- Vocabularies: *sni_appendices_a_b_actors_mechanisms.md*
- UI overview: *sni_ui_spec_v_1_draft.md*

---

## D.1 Repository & layout

- **Single source of truth for config** → `sni/config.py` exposes **typed** settings; all modules import from it. No ad‑hoc `os.getenv` reads elsewhere.
- **Directories**
  - `apps/ingest/` – RSS fetch, normalize
  - `apps/filter/` – filtering, actor extraction, gating
  - `apps/generate/` – multipass generate EFs and FNs
  - `apps/merge/`, `apps/arc/`
  - `db/` – migrations, seeds, schema snapshots
  - `docs/` – context/specs; tickets under `docs/tickets/`
  - `scripts/` – one‑shot utilities (idempotent)
  - `tests/` – smoke + contract tests
- **File placement**: `.md` only in `/docs/`; schema SQL only in `/db/`.
- **Naming**: snake\_case for code; kebab‑case for scripts; no `final_v2.py`.

## D.2 Config, secrets, environments

- **Local only** uses `.env`; CI/prod read env vars or secret store.
- **Settings immutability**: read once on start; expose `settings.VERSION`, `settings.ENV`.
- **No secrets in repo**; provide `.env.example` with placeholders.
- **Runtime pins**: pin Python/Node in `runtime.txt` / `.tool-versions`.

## D.3 Dependencies & reproducibility

- **Exact versions** only (`requirements.txt`/lockfile); no floating `>=`.
- **Determinism**: all thresholds/constants live in `core/config.py`.
- **Randomness**: if sampling is used anywhere, set seed and record it in `runs`.

## D.4 Database & schema hygiene

- **One DB connection module**: `sni/db.py` with pooling/timeouts; everyone imports it.
- **UTC everywhere**; timestamps stored as UTC.
- **Migrations**: each schema change adds `/db/migrations/YYMMDDHHMM_description.sql` with **up/down**; never mutate live tables.
- **Constraints**: `items.content_hash` unique; proper PK/FKs on `events`, `narratives`; `arcs.member_event_ids` allowed for MVP but plan `arc_events` later.
- **Idempotent ingest**: use UPSERT on `content_hash`.
- **Provenance**: each batch writes to `runs` with input set hash, prompt id, params, output refs.

## D.5 ETL & ingest quality

- **HTTP discipline**: honor ETag/If‑Modified‑Since; retry with backoff (max 3); per‑host rate limits.
- **Normalization**: Unicode NFKC, collapse whitespace, strip exact ` – Publisher` suffix, drop non‑informative emoji/symbols.
- **Lang detection**: store code or `null`; don’t block pipeline.
- **Logging**: per‑feed counters (fetched/inserted/dupes/errors) and durations.
- **Idempotence**: same feed at T+0 produces 0 new rows.

## D.6 Clustering & guardrails (CLUST‑1)

- **Actor detection**: alias‑map string match first (from Appendix A); NER optional.
- **Strategic gate v2**: pure function returns `{keep: bool, score: float, reason: str}`; maintain test fixtures.
- **Typed contract:** implement as `GateResult` **dataclass** (or `TypedDict`) with fields\
  `keep: bool`, `score: float`, `reason: str`, `anchors: list[str]` *(which anchor phrases fired)* for transparent audits and easy testing.
[outdated]
- **Guarded mechanisms**: enforce issuer→instrument→target uniformity (sanctions/export\_controls/asset\_freeze/travel\_ban/strike\_airstrike/platform\_ban). Split mixed triples.
- **Thresholds**: constants – dedupe 0.95; bucket 0.60; merge 0.85.
- **Caps**: bucket ≤100 items; GEN payload ≤8k tokens.
- **De‑dup**: cosine 0.95 plus trigram/Jaccard as tie‑breaker.
[end of outdated]

## D.7 LLM usage (GEN‑1/MERGE/ARC)

- **Prompt templates** under `apps/generate/prompts/`, versioned (`v1`, `v2`…), referenced by **explicit id** in `runs.prompt_version`.
- **Inputs‑only facts**: Event.shared\_facts is intersection; no new facts/numbers/actors. Narrative/Arc theses may paraphrase with hedging.
- **Budgeting**: log token usage and estimate cost per bucket.
- **Retries**: at‑most‑once for GEN‑1; on failure, record in `runs` and leave bucket pending.
- **No live web** in LLM prompts; all inputs come from `items`.

## D.8 Observability & ops

- **Structured logs** (JSON): `phase`, counts, timings, thresholds, model version.
- **Metrics**: gate keep‑rate, merge decisions, LLM success rate, token totals.
- **Crash policy**: fail a single feed/ef without halting the whole run; end‑of‑run failure summary.
- **framing\_disagreement\_rate**: percentage of Events that yield **≥2 Framed Narratives** (per batch and rolling 7/30-day).

## D.9 Performance & cost

- **Batch I/O**: DB insert/read in 100‑item batches.
- **Parallelism**: cap concurrent feeds (backfill 5–10; daily 2–4).
- **Caching**: cache embeddings for `title_norm` keyed by `content_hash`.

## D.10 Security & data handling

- **PII**: not expected; if encountered, store headline only—no extras.
- **URLs**: keep Google News URLs; never unwrap to publisher.
- **Secrets**: rotate keys regularly; no secrets in `docs/` or code.

## D.11 Tests & Definition of Done (DoD)

- **Smoke tests**
  - Ingest: run on a known sample feed → assert inserted/dupe counts and idempotency on second run.
  - GEN‑1: run on 1 tiny batch → schema‑valid Event/Narrative JSON produced.
- **Contract tests**
  - **Guarded mechanisms**: fixtures where mixed `issuer→target` headlines must be split into separate EFs.
- **DoD checklist (for any change)**
  1. Tests added/updated; CI green.
  2. `docs/CHANGELOG.md` updated with rationale.
  3. `runs` records the new `prompt_version` or component version.

## D.12 Code style & documentation

- **Style**: `black` + `ruff`; no unused imports; type hints on public functions; docstrings for modules.
- **Docs**: all design notes in `/docs`; keep the Context Pack and this Playbook in sync.
- **READMEs**: each `apps/*` folder has a 10‑line README: purpose, inputs, outputs, how to run locally.

## D.13 CI/CD (lightweight)

- **CI steps**: lint → type‑check (optional) → tests → build.
- **Branch policy**: PRs only; no direct push to `main`.
- **Artifacts**: store built CLI wheels/containers for reproducibility.

## D.14 Environments & releases

- **Envs**: `local` (dev laptop), `staging` (optional), `prod`.
- **Release tagging**: semantic tags `vMAJOR.MINOR.PATCH` on `main` when promoted.
- **Config diff**: log `settings` diff per release in `runs` metadata.

## D.15 Data retention & backup

- **Backups**: nightly DB snapshot; retain 7 daily + 4 weekly.
- **Retention**: raw `items` kept indefinitely (headlines are small). Can prune `runs.output_ref` blobs older than N months.

## D.16 Incident response

- **On merge mistakes**: mark Events as `superseded_by` and re‑run MERGE; keep originals for audit.
- **On bad bucket**: set `bucket_state = quarantined`, add `quarantine_reason`, and exclude from GEN‑1.
- **On prompt regressions**: roll back `prompt_version` via config; regenerate only affected buckets.

## D.17 Quality gates (pre‑commit & pre‑merge)

- **Pre‑commit**: run `ruff --fix` and `black`; refuse commit on lint errors.
- **Pre‑merge**: CI must be green; golden tests must pass; if thresholds changed, require a short rationale PR note.

---

**Mantra:** *Minimum complexity, maximum clarity.* Trade 5% performance for 50% readability when it reduces risk. When uncertain, pause and add a 3‑line note to `docs/decisions.md` before proceeding.

