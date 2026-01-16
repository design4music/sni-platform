# SNI Project Contract (L3)

## Project Identity
Strategic Narrative Intelligence (SNI) is a **mechanical-first intelligence pipeline**
for extracting, aggregating, and summarizing **strategic narratives** from global news.

The system prioritizes:
- Determinism over cleverness
- Structural adequacy over semantic elegance
- Coverage before purity
- Auditability before abstraction

SNI is **not** a semantic search engine, recommender system, or opinion generator.

---

## Core Design Commitments (Non-Negotiable)

### 1. Mechanical First, LLM Second
- Structural operations (matching, grouping, aggregation) MUST be mechanical.
- LLMs are used only where human-like judgment is required:
  - Strategic track classification
  - Event deduplication
  - Narrative summarization
- No LLM participates in clustering or centroid assignment.

### 2. Centroid-Based Architecture
- All narrative aggregation is anchored to **explicit centroids**.
- Centroids are stable, curated narrative anchors.
- No graph-based clustering, no emergent topic modeling.

(Neo4j-style graph clustering is explicitly deprecated.)

### 3. CTM as the Atomic Intelligence Unit
- The Centroid–Track–Month (CTM) is the **core analytical object**.
- All downstream intelligence (events, summaries, UI) is derived from CTMs.
- Titles are inputs; CTMs are products.

### 4. Many-to-Many Reality Preservation
- Titles may belong to multiple centroids.
- Titles may contribute to multiple CTMs.
- Forced single assignment is considered information loss.

### 5. Strategic Focus Constraint
- SNI explicitly excludes:
  - Culture
  - Sports
  - Entertainment
  - Lifestyle
- Stop-word and taxonomy filtering are mandatory safeguards.

### 6. Database-Centric Truth
- PostgreSQL is the single source of truth.
- Files, prompts, and configs support the DB — not vice versa.
- No parallel “shadow models” of state are allowed.

---

## Operational Philosophy

- Pipelines must be restartable, observable, and debuggable.
- Simplicity beats theoretical optimality.
- Every abstraction must justify itself in reduced failure modes.

This contract changes **rarely**.
Any modification requires an explicit `change_of_intent` decision.

---

## DEVELOPMENT PRINCIPLE: MINIMAL, FOCUSED IMPLEMENTATION

**THIS IS A HARD RULE - NOT A SUGGESTION**

### Code Philosophy
- **Write ONLY what is needed NOW** - Not what might be needed later
- **No "just in case" features** - No premature abstractions
- **No overengineering** - Resist the urge to add complexity because you can
- **50 lines > 200 lines** - Shorter, focused code is always better
- **If unsure, go simpler** - When in doubt, choose the minimal approach

### Examples of What NOT to Do
- ❌ Adding wrapper methods that just call existing methods
- ❌ Implementing features for future steps before they're needed
- ❌ Creating elaborate class hierarchies when a simple function works
- ❌ Writing extensive docstrings when the code is self-explanatory
- ❌ Adding singleton patterns, factory patterns, etc. unless absolutely necessary

### What TO Do Instead
- ✅ Implement exactly what the current step requires
- ✅ Use the simplest approach that works
- ✅ Add features incrementally when actually needed
- ✅ Keep functions and classes focused on one job
- ✅ Ask "Can this be simpler?" before writing

**Remember**: This project values working code over perfect code. Ship minimal, iterate if needed.