# RAI Analysis Pipeline: End-to-End Trace

**Example:** Event `bc97c377` — "Trump and Netanyahu meet in Washington to discuss US nuclear talks with Iran"
**Narrative:** "Iran as victim of US pressure" (84 sources)
**Date:** 2026-02-21

---

## Stage 1: WorldBrief Frontend -> WB API Route

**Request:** `POST /api/rai-analyse`

```json
{ "narrative_id": "ff86dfeb-63be-4a30-bf98-3c50f884b81d" }
```

**What the API route does:**
1. Auth check (session required)
2. DB cache lookup (rai_full_analysis on narratives table)
3. SQL join to get narrative + parent event + CTM + centroid context
4. Build payload, call RAI, save results to DB

---

## Stage 2: WB API Route -> RAI Endpoint

**Request:** `POST https://rai-backend-ldy4.onrender.com/api/v1/worldbrief/analyze`

**Payload sent to RAI** (~1.5 KB):

```json
{
  "content_type": "event_narrative",
  "format": "json",
  "narrative": {
    "label": "Iran as victim of US pressure",
    "moral_frame": "Hero: Iran (defending sovereignty, seeking equitable deal), Villain: US/Israel (warmongering, imposing unfair demands)",
    "description": "This frame presents Iran as a sovereign nation seeking fair negotiations...",
    "source_count": 84,
    "top_sources": ["IRNA English", "PressTV", "Al Jazeera", "tass.com", "rt.com", "Ahram Online", "Khaleej Times", "France 24"],
    "sample_titles": [
      {"title": "Turkey, Egypt, Qatar working to organize Witkoff meeting with Iranian officials"},
      {"title": "Iran - U.S. Negotiations Are Fruitful, Iranian Foreign Minister Tells CNN"},
      "... (15 titles total)"
    ]
  },
  "context": {
    "centroid_id": "AMERICAS-USA",
    "track": "geo_politics",
    "event_title": "Trump and Netanyahu meet in Washington to discuss US nuclear talks with Iran"
  }
}
```

---

## Stage 3: RAI App -> DeepSeek LLM

RAI's `process_worldbrief_request()` builds a prompt from 3 pieces:

### 3a. System frame (~400 chars)
```
You are operating under the **Real Artificial Intelligence (RAI) Framework**.
This is a **media framing analysis** of news coverage from the WorldBrief intelligence platform.

Your task:
- Evaluate whether this narrative adequately represents the event
- Identify what perspectives or facts are missing
- Assess source diversity and potential echo-chamber effects
- Detect framing bias and moral simplification
```

### 3b. Narrative + Context data (~1,200 chars)
The payload fields formatted as markdown: geopolitical context, narrative frame, moral frame, description, source count, top sources, 15 sample headlines.

### 3c. RAI Analytical Modules (~10,000 chars -- THE BULK)
6 modules selected for `event_narrative` type:
- **CL-0:** Input Clarity and Narrative Normalization
- **NL-1:** Cause-Effect Chain Analysis
- **NL-3:** Competing Narratives Contrast
- **FL-2:** Asymmetrical Amplification Awareness
- **FL-3:** Source Independence Audit
- **SL-8:** Systemic Blind Spots and Vulnerabilities

Each module includes:
- Purpose statement
- Core questions (3-4 each)
- Philosophical anchoring (2-3 "premises" with full paragraph explanations, e.g. D1.1, D3.3, D6.2)
- Wisdom guidance (1-3 aphorisms)

### 3d. Scoring instruction (~500 chars)
```
After your analysis, output a structured scoring block on its own line:
SCORES: {"adequacy": <0.0-1.0>, "bias_detected": <0.0-1.0>, ...}
```

**Total prompt: ~12,600 chars / ~3,150 tokens**

The prompt is module-heavy: **~80% is RAI framework boilerplate** (module definitions, premises, wisdom quotes). Only ~20% is actual event-specific data.

---

## Stage 4: DeepSeek Response -> RAI App

DeepSeek returns ~6,000 chars of prose analysis in ~36 seconds.

### Raw structure (before parsing):
- Multiple `##` sections (but DeepSeek actually put everything under one heading)
- Each module addressed sequentially: CL-0, NL-1, NL-3, FL-2, FL-3, SL-8
- SCORES JSON block at the end

### Scores returned:
```json
{
  "adequacy": 0.25,
  "bias_detected": 0.95,
  "coherence": 0.9,
  "evidence_quality": 0.3,
  "blind_spots": [
    "Iran's pre-2015 nuclear concealment and post-JCPOA expansion as causal factors",
    "Details of Iran's regional proxy activities and their link to negotiations",
    "Internal political debates within US/Israel shaping policy"
  ],
  "conflicts": [
    "Victimhood vs. Rogue Actor framing",
    "Sovereign rights vs. non-proliferation obligations",
    "Moral narrative vs. realist strategic bargaining"
  ],
  "synthesis": "The narrative is a highly coherent but one-sided strategic frame that amplifies Iran's victimhood to gain moral leverage, while systematically excluding the historical context, adversarial perspectives, and regional complexities that define the nuclear standoff."
}
```

### Analysis quality observations:
- **Good:** The analysis is genuinely insightful. It identifies the start-point bias, echo-chamber sourcing, blind spots (nuclear concealment history, regional proxy activities, domestic politics).
- **Bad:** It's LONG. One massive blob of text under a single heading. Reads like an academic paper, not actionable intelligence.
- **Problem:** DeepSeek produced only 1 section (instead of per-module sections) because it used `### ` (h3) sub-headings instead of `## ` (h2) headings. The parser splits on `## ` so everything ends up in one section.

---

## Stage 5: RAI App -> WB Frontend

**Response from RAI** (what WB gets back):

```json
{
  "full_analysis": [
    {
      "heading": "### **RAI Media Framing Analysis: ...**",
      "paragraphs": ["<one giant paragraph per module>", "...", "..."]
    }
  ],
  "scores": { "adequacy": 0.25, "bias_detected": 0.95, ... },
  "metadata": {
    "model_used": "deepseek",
    "modules_executed": 6,
    "processing_time": 36.17
  }
}
```

The frontend renders sections from `full_analysis` and the overlay shows the prose.

---

## Pipeline Timing

| Stage | Duration |
|-------|----------|
| WB -> RAI (network) | ~1s |
| RAI prompt construction | <0.1s |
| RAI -> DeepSeek (LLM) | **~36s** |
| Response parsing | <0.1s |
| RAI -> WB (network) | ~1s |
| DB save | <0.1s |
| **Total** | **~38s** |

The LLM call dominates. The prompt is ~3,150 input tokens; the response is ~1,500 output tokens.

---

## Key Findings

### 1. Prompt is 80% framework boilerplate
The 6 RAI modules with their premises and wisdom quotes consume ~10,000 of 12,600 chars. The actual event-specific data (narrative, sources, headlines) is only ~2,500 chars. The LLM receives a wall of philosophical anchoring for every single request, regardless of the event.

### 2. Section parsing is broken
DeepSeek uses `### ` (h3) sub-headings within a single `## ` section. The parser splits on `## ` so the entire analysis collapses into one blob. Either the prompt needs to instruct the LLM to use `## ` for each module, or the parser needs to handle `### ` too.

### 3. Output is verbose and academic
The analysis reads like a policy paper. For WB users, the key insights are buried in long paragraphs. The 3 blind spots and 3 conflicts in the scores are actually the most useful output -- they're sharp and actionable. The prose analysis adds context but overwhelms.

### 4. The triangulation adds latency, not value
WB sends data to RAI, which just reformats it into a prompt and sends to DeepSeek. RAI's value-add is the module selection and premise injection. But if we pre-bake the right prompt for WB use cases, we can call DeepSeek directly and skip the network hop. The RAI framework's philosophical premises could be distilled into a compact system prompt.

### 5. What "better" analysis looks like for WB
- **Shorter:** 3-5 crisp paragraphs, not 8 dense ones
- **Structured:** Clear headings that users can scan
- **Sharp:** 1-3 screaming blind spots, not 7 mild ones
- **Contrastive:** "This narrative says X. The opposing narrative says Y. The truth is probably Z."
- **Risk:** Being too sharp means occasionally being wrong. Nuance is a safety net.

---

## Options for Optimization

### Option A: Optimize the RAI prompt
- Strip philosophical premises down to 1-liners
- Reduce modules from 6 to 3-4 (e.g., NL-3 + FL-3 + SL-8)
- Add explicit output format instructions ("Use ## for each section, max 3 sentences per section")
- Keep RAI as intermediary but make it leaner

### Option B: Direct DeepSeek from WB (RAI-mini)
- Embed a compact analytical framework directly in WB codebase
- System prompt with distilled RAI principles (~500 tokens instead of 3,000)
- Faster (skip RAI network hop), simpler deployment
- r-a-i.org continues separately as demo/full-analysis tool

### Option C: Hybrid
- WB calls DeepSeek directly with a compact prompt for everyday analysis
- "Deep Analysis" button still calls full RAI for users who want the academic deep-dive
- Best of both: fast sharp analysis by default, full RAI on demand
