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

1. `10__ProjectContract.md`  
   (What this project is, and what must not drift)

2. `20__ProjectModel.md`  
   (How the system actually works, conceptually)

3. `30__DecisionLog.yaml`  
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

---

## Reminder

This system is intentionally simple.
If it feels redundant, it is working.