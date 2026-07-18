# WorldBrief -- Tech Background for LinkedIn

## Raw Facts & Numbers

| Metric | Value |
|--------|-------|
| Development start | September 2025 (v3 rewrite; v1 concept since July 2025) |
| Active dev days | 62 days across ~5 months |
| Commits | 195 |
| Python codebase | ~22,000 LOC |
| Frontend (TypeScript) | ~3,500 LOC (Next.js/React, rest is generated/config) |
| SQL migrations | 29 |
| Pipeline phases | 9 (Phase 1 through 4.5b) |
| RSS feeds monitored | 132 (Google News, multi-language) |
| Languages detected | 34 |
| Unique publishers | 261 |
| Centroids (narrative anchors) | 85 (geo + systemic) |
| Taxonomy aliases | 261 curated entries |
| Theaters (regions) | 7 |
| Strategic tracks per centroid | up to 6 (politics, economy, security, energy, humanitarian, information) |
| Titles ingested (Jan 2026) | ~42,000 |
| Daily ingestion rate | 3,000-6,000 headlines |
| CTMs (Jan, frozen) | 437 |
| Events clustered (total) | ~5,100 |
| Tech stack | Python, PostgreSQL (pgvector), Next.js 16, Docker, Render |
| LLM provider | DeepSeek (cost-effective; Anthropic/OpenAI for specific tasks) |
| Team | 1 person + AI pair programming (Claude) |
| Total cost to date | Under $200 in LLM API calls |

---

## Section 1: What WorldBrief Is

**One-liner**: An automated intelligence pipeline that turns thousands of daily news
headlines into structured, country-by-country strategic briefings.

**Longer version**: WorldBrief monitors 132 RSS feeds across 34 languages, ingests
3,000-6,000 headlines daily, and processes them through a 9-phase pipeline that
matches headlines to 85 geopolitical and thematic anchors (centroids), classifies
them into strategic domains (politics, economy, security, energy, humanitarian,
information), clusters related headlines into coherent topics, and generates
readable intelligence summaries. The output is organized as monthly briefings
per country per domain -- a cross-sectional view of global strategic activity.

**What it is NOT**: Not a news aggregator, not a search engine, not sentiment
analysis. It's a structured analytical pipeline that produces intelligence products
similar to what a team of analysts would create manually.

---

## Section 2: Architecture Highlights

### Mechanical-First Design Philosophy
The core design principle: structural operations (matching, clustering, aggregation)
are deterministic and mechanical. LLMs are used only where human judgment is
genuinely needed -- strategic relevance gating, event summarization, narrative
synthesis. This makes the system reproducible, auditable, and cheap to run.

### The Pipeline (9 Phases)
```
RSS Feeds --> Ingestion --> Centroid Matching --> Label Extraction
--> Entity Backfill --> Intel Gating --> Topic Clustering
--> Topic Aggregation --> Event Summaries --> Monthly Digests
```

- **Phases 1-2**: Mechanical. Hash-based alias matching against a curated taxonomy.
  Handles diacritics, CJK scripts, hyphenated compounds, multi-centroid assignment.
- **Phase 3.1**: Single LLM call extracts structured labels (Actor->Action->Domain)
  AND typed signals (persons, orgs, places, commodities, policies, systems).
- **Phase 3.3**: LLM gates for strategic relevance (rejects sports, entertainment,
  local crime), then assigns domain track. Mechanical pre-gating skips LLM for
  obvious accepts (~30% cost reduction).
- **Phase 4**: Signal-based incremental clustering. Titles group into topics based
  on weighted signal overlap (not embeddings, not LLM). Anchor-locking prevents
  topic drift. Non-destructive -- existing events survive re-runs.
- **Phase 4.5a/b**: LLM generates readable summaries per event and per CTM.

### The Data Model: CTM
CTM = Centroid + Track + Month. This is the atomic intelligence unit.
Example: "USA / Economy / January 2026" is one CTM containing all economy-related
topics about the US that month. 437 CTMs were produced for January across 85
countries and themes.

### Frontend
Next.js server-rendered dashboard. Read-only -- zero intelligence in the frontend.
Interactive map, country pages with monthly summaries, drill-down to individual
topics with source attribution. Frozen months get executive-level cross-domain
overviews.

### PostgreSQL-Native
No Redis queues, no Elasticsearch, no vector databases for production.
Single PostgreSQL instance (with pgvector extension) handles everything:
data storage, pipeline state, full-text queries, scheduling.

---

## Section 3: Technical Challenges

### Clustering Quality (the hardest problem)
This has been the central engineering challenge since July 2025.

**v1 (Jul-Aug 2025)**: Neo4j graph clustering with PageRank. Opaque, expensive,
unpredictable cluster boundaries. Abandoned.

**v2 (Sep-Oct 2025)**: Moved to PostgreSQL-only with LLM-based event extraction.
Better, but LLM clustering was non-deterministic -- same input could produce
different groupings on re-runs. Expensive at scale.

**v3 (Nov 2025 - present)**: Mechanical signal-based clustering. Typed signals
(persons, orgs, places, etc.) extracted once by LLM, then clustering is purely
mechanical. Key innovations:
- **Anchor locking**: First 5 titles define a topic's identity signals, then lock.
  Later titles match against anchors but can't change topic identity.
- **Track-specific weights**: Security topics weight places and weapons systems
  heavily; economy topics weight organizations and commodities.
- **Discriminators**: Prevent merging topics that share common signals but differ
  on key ones (e.g., two different Trump policy stories).
- **Geographic bucketing**: Automatic domestic/bilateral/international classification
  based on centroid ISO codes.
- **Non-destructive incremental runs**: Pipeline appends new titles to existing
  topics without destroying LLM-generated summaries.

This took 4 iterations and ~3 months to get right. The current system produces
coherent topics across 5,000+ events with zero LLM involvement in clustering.

### Multi-Language, Multi-Script Matching
Matching "Cote d'Ivoire" in a French headline, matching centroid aliases in Arabic
or Chinese scripts (no word boundaries), handling hyphenated compounds
("China-made" should match "China"), filtering Romance-language false positives
("il" matching Israel). Solved with script-aware tokenization, diacritic
normalization, and language-specific stop-word filtering.

### LLM Cost Control
Running LLM on 6,000 headlines/day across 9 phases could be expensive. Solved by:
- Mechanical pre-gating (~30% of titles skip LLM entirely)
- Combined extraction (labels + signals in single call)
- DeepSeek as primary provider (10-20x cheaper than GPT-4)
- Event-driven summary regeneration (only re-summarize what changed)
- Total spend: under $200 for 5 months of development + production

### Monthly Boundary Problem
Intelligence products need temporal boundaries (you want "January briefing",
not an ever-growing blob). Implemented monthly freeze: CTMs lock, cross-track
summaries generate, new month starts fresh. Frontend adapts layout for
frozen (archival) vs. live (current) months.

---

## Section 4: Human in the Loop -- My Role

### What I Built vs. What AI Built
I worked with Claude (Anthropic) as a pair programmer throughout. The division:

**My decisions (product/architecture)**:
- Defined the centroid-based architecture after evaluating (and discarding) graph
  clustering, embedding-based approaches, and pure LLM extraction
- Designed the CTM data model and the monthly freeze/rollover process
- Curated the taxonomy (85 centroids, aliases, track configurations)
- Defined the "mechanical first, LLM second" principle after observing LLM
  non-determinism in clustering
- Designed the signal-based clustering approach (anchor locking, weights,
  discriminators) after 3 failed iterations
- Made every prompt engineering decision (what to ask the LLM, what NOT to)
- QA'd every pipeline output, caught hallucinations, tuned thresholds
- Designed the frontend information architecture

**AI-assisted (implementation)**:
- Python pipeline code, SQL migrations, Next.js frontend
- Prompt drafting (I reviewed and iterated every prompt)
- Debugging (AI reads stack traces faster than I do)
- Refactoring (when I decided the architecture needed to change, AI helped
  execute the migration)

### How I Work with AI
- I treat AI as a senior engineer who needs clear product requirements
- I maintain project documentation that serves as context for every session
  (decision log, project contract, pipeline status)
- I review every line of generated code for correctness and simplicity
- I reject over-engineered solutions (my #1 rule: "50 lines > 200 lines")
- I make all architectural decisions; AI implements them
- When AI suggests an approach, I evaluate it against my domain knowledge
  (geopolitical analysis, strategic intelligence) before accepting

This is not "prompting an AI to write an app." This is product management,
systems design, and domain expertise applied through an AI-accelerated workflow.

---

## Section 5: What Makes This Interesting

### For Hiring Managers (PM/PO/Tech Lead)
- Solo-built a production system processing 6,000 items/day across 9 pipeline phases
- Made and documented 23 architectural decisions over 5 months
- Managed complexity: 85 centroids, 34 languages, 261 publishers, 29 DB migrations
- Demonstrated ability to evaluate and discard approaches (Neo4j -> LLM clustering
  -> mechanical clustering, 3 pivots)
- Shipped a working demo with real data, not a proof of concept
- AI-assisted development: 195 commits, 62 active days, ~25K LOC -- as a solo developer
- Strong grasp of where AI helps (implementation speed) and where it doesn't
  (architecture, domain judgment, quality)

### For Potential Collaborators / Investors
- Working product with real data (not mockups)
- Processes 132 feeds in 34 languages, 85 countries/themes
- Sub-$200 total infrastructure cost (PostgreSQL + DeepSeek)
- Designed for scale: mechanical-first means LLM costs grow sub-linearly
- Monthly briefing format maps directly to consulting/advisory deliverables
- Clear product-market fit in: geopolitical advisory, corporate intelligence,
  government briefing, journalism support
- Live demo available at [Render URL]

---

## Suggested Angles for the Post

**Option A: "I built a geopolitical intelligence system with AI -- here's what I learned"**
Focus on the journey, the pivots, what AI can and can't do. Good for job search angle.

**Option B: "WorldBrief: automated strategic briefings for 85 countries at $40/month"**
Focus on the product, the output, the cost efficiency. Good for collaboration/startup angle.

**Option C: "The hardest problem in AI-assisted development isn't code -- it's knowing what to build"**
Focus on PM/architecture decisions, the 3 clustering pivots, human judgment.
Speaks to both audiences.

**Option D: Combine B+C** -- lead with the product demo, then zoom into the
development story. Hook with the output, convince with the process.
