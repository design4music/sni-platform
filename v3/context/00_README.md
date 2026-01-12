# Context-of-Context Bootstrap (SNI)

This folder defines the **Context of Context (CoC)** for the SNI project.
Its purpose is to preserve intent, prevent architectural drift, and ensure
that all development work accumulates judgment rather than resetting it.

---

## Mandatory Session Bootstrap (Claude Code)

Before performing **any** of the following:
- reading source code
- reviewing git status
- inspecting the database
- proposing changes or refactors
- answering implementation questions

Claude Code **must read and internalize** the following files,
**in this exact order**:

1. `10_ProjectContract.md`
   (What this project is, and what must not drift)

2. `20_ProjectModel.md`
   (How the system actually works, conceptually)

3. `30_DecisionLog.yml`
   (Why key design decisions were made; closed debates)

Only **after** these are read may Claude Code consult:
4. `V3_PIPELINE_STATUS.md`  
   (Current implementation state: files, schemas, scripts, status)

Only then may Claude Code:
- inspect code
- inspect database schemas
- suggest or implement changes

---

## Authority Rules

- Files in this folder are **authoritative over code and status documents**.
- `V3_PIPELINE_STATUS.md` is descriptive, not prescriptive.
- No change to project intent or model may occur silently.

---

## Change Discipline

- New requirements or refactors that affect intent or structure
  must result in a DecisionLog entry.
- Claude Code must not update ProjectContract or ProjectModel
  without explicitly proposing a patch for human approval.

### Major Additions (2026-01-05/06)

**Taxonomy Tools Suite** (`v3/taxonomy_tools/`)
Automated analysis and maintenance tools for taxonomy management:

- **Static Subsumption Pruner** - Remove redundant aliases (836 pruned, 6.5%)
- **Coverage Profiler** - Measure alias effectiveness per centroid/language
- **Snapshot/Restore** - Safety backups for taxonomy state
- **NameBombs Detector** - Identify emerging proper names leaking into OOS
- **OOS Keyword Candidates** - Detect general keywords missing from taxonomy

All tools produce **reports only** (no auto-writes). Designed for daily pipeline integration.

**Documentation**: `60_TaxonomyTools.md`

---

## Reminder

This system is intentionally simple.
If it feels redundant, it is working.