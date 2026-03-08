# WorldBrief -- Media Lift Pitch Deck
## Slide-by-slide content for Google Slides

---

### SLIDE 1: Title

**WorldBrief**
Structured Intelligence from Global News -- Compressed, Connected, Examined

worldbrief.info

Media Lift 2026 Application

> Speaker notes: Brief intro -- WorldBrief compresses thousands of daily headlines into structured, country-level intelligence briefings organized by strategic domain, connected across time and geography, and examined for narrative adequacy.

---

### SLIDE 2: The Problem

**The world is complex. News coverage of it is flat.**

- Thousands of headlines published daily -- but no structure, no connections, no depth
- Readers drown in volume: the same story appears in dozens of outlets with no synthesis
- No existing tool connects the same story across countries, tracks its evolution over months, or reveals which perspectives are missing
- AI chatbots summarize but discard structure; analyst briefings provide structure but don't scale
- Media narratives go unexamined: are they adequate representations of structural realities and long-term tendencies, or surface-level reactions?

> Speaker notes: The problem isn't lack of information -- it's lack of *compressed, structured intelligence*. A policy professional tracking US-China relations today must manually scan dozens of sources, mentally group related headlines, and somehow track how the story evolved from last month. WorldBrief does this automatically. The deeper problem is that media narratives are rarely assessed for adequacy -- do they reflect structural realities or just the news cycle?

---

### SLIDE 3: The Solution

**WorldBrief: A mechanical-first intelligence pipeline**

**WorldBrief compresses the global news stream into structured, interconnected intelligence**

- Ingests thousands of headlines daily from 200+ RSS sources across 40+ languages (continuously expanding)
- Maps every headline to 85 geographic and thematic centroids (countries, regions, systems like NATO, OPEC, EU)
- Classifies into strategic tracks (Security, Diplomacy, Economy, Governance, Energy, Tech, Environment, Humanitarian)
- Clusters hundreds of articles into dozens of tight event summaries -- connected across time and geography
- Events accumulate as interconnected entities: saga chains link the same story across months, epics connect it across borders
- Analytical layer assesses the adequacy of media narratives against structural realities

**Mechanical where possible. AI where necessary.**

> Speaker notes: The core value proposition is *compression with structure*. A user opens a country page and sees the month's developments organized by strategic domain, each containing tightly summarized events built from dozens or hundreds of source articles. These events aren't isolated -- they chain across months (sagas) and across countries (epics), building time depth. The system doesn't just aggregate -- it structures, connects, and then allows the user to examine whether the resulting media narratives adequately reflect long-term tendencies and structural realities.

---

### SLIDE 4: How It Works (Pipeline)

**From raw headlines to structured intelligence in 4 automated phases**

Phase 1: **Ingest** -- RSS feeds, deduplication, publisher extraction (every 12h)
Phase 2: **Match** -- Assign to countries/systems via 5,000+ keyword patterns (every 15min)
Phase 3: **Classify** -- Extract entities, signals, strategic tracks via LLM (every 15min)
Phase 4: **Structure** -- Cluster into events, generate summaries, detect cross-border stories (every 30min)

On-demand: **Analyse** -- Narrative frame extraction + bias analysis (user-triggered)

Fully automated daemon, running 24/7. No manual curation.

> Speaker notes: The pipeline runs as a 4-slot daemon. Ingestion every 12 hours, classification every 15 minutes, clustering every 30 minutes, enrichment every 6 hours. The system processes ~2,000 headlines/day and currently tracks ~85 centroids across all continents.

---

### SLIDE 5: Product -- Live at worldbrief.info

[6 screenshots, arranged 3x2 or 2x3 grid, each with a short caption below]

**1. Home Page**
Interactive world map, trending carousel, region navigation, live stats (200+ feeds, 40+ languages, 85 centroids). Entry point to any country or system.

**2. Country Page**
One country, all strategic tracks at a glance. Monthly summaries, track cards with title counts, top signals sidebar, month-by-month navigation. Frozen months show executive overview.

**3. Event Detail**
Dozens of sources compressed into one structured summary. Tags, source count, date range. Story Timeline links the same story across months. Source headlines expandable for full transparency.

**4. Narrative Analysis**
Adequacy assessment with sidebar scores, coverage stats (publisher HHI, language distribution, geographic focus, top persons). LLM-selected analytical modules examine narrative frames against structural realities.

**5. Signal Observatory**
Interactive co-occurrence network: which entities appear together across the global news stream. Seven signal types (persons, orgs, places, commodities, policies, systems, named events) with activity heatmaps.

**6. Signal Page**
Single entity deep-dive. Weekly mention timeline, geographic distribution, theme breakdown by track, relationship highlights showing co-occurring signals and linked events.

Available in English and German.

> Speaker notes: Walk through the product live if possible. Key narrative: (1) Home -- the global view, (2) Country -- strategic compression of one nation's developments, (3) Event -- how hundreds of articles become one tight summary with time depth, (4) Analysis -- the intellectual core, assessing narrative adequacy, (5-6) Signals -- the entity layer that connects everything.

---

### SLIDE 6: What Makes WorldBrief Different

| | Google News | AI Chatbots | Analyst Briefings | **WorldBrief** |
|---|---|---|---|---|
| Structured by country + domain | -- | -- | Yes | **Yes** |
| Automated, scalable | Yes | Yes | -- | **Yes** |
| Source transparency | Partial | -- | -- | **Yes** |
| Narrative adequacy analysis | -- | -- | -- | **Yes** |
| Cross-border story tracking | -- | -- | Partial | **Yes** |
| Monthly narrative evolution | -- | -- | Partial | **Yes** |
| Cost per briefing | Free | ~$20/mo | $500-5,000/mo | **Low** |

> Speaker notes: We sit in an empty quadrant. Automated intelligence products (Google News, Perplexity) lack structure. Structured intelligence products (Stratfor, RANE) are manual and expensive. WorldBrief combines automation with structural depth. The narrative analysis layer is unique -- no competitor systematically assesses whether media coverage adequately reflects structural realities.

---

### SLIDE 7: Analytical Methodology (RAI Engine)

**Assessing the adequacy of media narratives -- not just what's said, but what's structural**

The RAI engine originated as research for a book on analytical methodology. It evolved into a working framework with 33 analytical modules and 46 premises that examine media narratives against:

- **Structural realities** -- Do coverage patterns reflect actual power structures, economic dependencies, and institutional arrangements?
- **Long-term tendencies** -- Is reporting reactive to events or aware of underlying trajectories?
- **Coverage architecture** -- Publisher concentration, language distribution, geographic representation, actor focus
- **Narrative framing** -- Which competing interpretations exist? Which are absent?

The system computes hard statistics from the database (no guessing), then an LLM selects the 3 most relevant modules per story and produces a data-driven assessment.

**Dual use:** The methodology is designed to power the product *and* to train human analysts -- a structured approach to evaluating media narratives that can be taught independently of the software.

> Speaker notes: This is the intellectual core of WorldBrief. Most "bias detection" tools count sentiment or political leaning. Our approach is fundamentally different -- it asks whether media narratives are *adequate* representations of structural realities. This comes from an analytical tradition, not a tech tradition. The framework was originally conceived as a book on analytical methodology; the software implementation makes it scalable. This dual nature -- product feature and teachable methodology -- is a unique positioning asset.

---

### SLIDE 8: Market Opportunity

**Target segments:**

1. **Informed news consumers** -- anyone who wants a broader, structured overview of international developments without reading dozens of sources daily
2. **Media professionals** -- journalists, editors, foreign correspondents needing structured cross-border context
3. **Policy & government** -- diplomatic staff, think tanks, NGOs tracking geopolitical developments
4. **Corporate intelligence** -- risk teams, compliance, international affairs departments
5. **Education & research** -- IR students, media studies, political science; the analytical methodology as a training tool for future analysts

**Market sizing:**
- Global news intelligence market: ~$4B (Stratfor, Janes, RANE, Dataminr)
- AI-powered news tools growing 25%+ annually
- Underserved mid-market: too sophisticated for Google News, priced out of Stratfor

**Geographic entry point:** DACH region (German localization already live)

> Speaker notes: The immediate opportunity is the mid-market. Stratfor charges $500+/month. Google News is free but unstructured. WorldBrief targets the gap: structured intelligence at an accessible price point. Hamburg / DACH is the natural starting market given German localization and the Media Lift network.

---

### SLIDE 9: Business Model

**Freemium SaaS**

**Free tier:**
- Browse all country briefings and event summaries
- Signal Observatory (trending entities, co-occurrence network)
- Search across all centroids and events

**Premium tier (target: EUR 15-30/month):**
- Narrative frame extraction (on-demand, per story)
- RAI narrative adequacy analysis with coverage scores
- Epic cross-border story tracking with per-country perspectives
- Data-driven analytical content (ongoing development)
- Priority access to new features

**Infrastructure:**
- Authentication system live (NextAuth v5)
- Stripe integration researched and scoped (~2 days implementation)
- LLM costs scale with premium usage only (free tier = zero LLM cost)

> Speaker notes: The architecture naturally supports freemium. Everything up to Phase 4.5b (summaries) runs automatically with fixed costs. The expensive LLM operations -- narrative extraction and bias analysis -- are on-demand and gated behind authentication. This means free users cost almost nothing, and premium features have clear value differentiation.

---

### SLIDE 10: Traction & Status

**Product:**
- Live at worldbrief.info since January 2026
- 200+ RSS sources (continuously expanding), 85 centroids, 8 strategic tracks
- ~2,000 headlines processed daily
- Full pipeline operational 24/7 (4-slot daemon architecture)
- English + German (bilingual)
- Authentication, on-demand extraction, narrative analysis all functional

**Technical milestones achieved:**
- Deterministic signal-based clustering (no LLM dependency for structure)
- Event saga chaining across months (story continuity tracking)
- Materialized view pattern for sub-100ms page loads
- 33-module analytical engine with data-driven premises

**Next milestones:**
- Payment integration (Stripe, scoped)
- User feedback loops and retention tracking
- Ongoing development of paid-tier data-driven analytical content
- B2B API for institutional customers

> Speaker notes: The product is not a prototype -- it's a working system processing real data every day. The pipeline has been running continuously since January. The technical foundation is solid; the next phase is market validation and go-to-market.

---

### SLIDE 11: Team

**Maksim Micheliov** -- Founder, Technology & Analytical Framework
20+ years in web development across the full spectrum -- from design to backend engineering to technical marketing. Years of independent research into how people interact with news products and process information at scale. Designed and built the entire WorldBrief stack: data pipeline, analytical engine, frontend. Author of the RAI analytical methodology -- originally conceived as a book on assessing media narrative adequacy, now implemented as a functional LLM-powered framework.

**Carolin Baur** -- Co-Founder, Product Strategy & User Experience
15 years at NXP Semiconductors across marketing and product roles -- bringing structured product thinking from a global technology company to the media intelligence space. Deep interest in international politics and a personal advocate for democracy, peace, and multiculturalism -- the values that WorldBrief is built to serve by making global news coverage more transparent and structurally examined.

> Speaker notes: The team is complementary by design. Maksim brings the technical architecture and analytical methodology -- the engine and the intellectual framework. Carolin brings product strategy, user experience thinking, and 15 years of marketing and product discipline from a major international company. Both share a conviction that informed citizens need better tools to understand the world -- not more noise, but more structure.

---

### SLIDE 12: The Ask -- Media Lift

**What we want from Media Lift:**

**Phase 1 (Product Validation, May-Aug):**
- Validate pricing and packaging with media industry mentors
- User interviews with journalists, editors, policy professionals in Hamburg/DACH
- Refine the analytical methodology based on practitioner feedback
- Define B2B vs B2C positioning

**Phase 2 (Go-to-Market, Aug-Nov):**
- Launch premium tier with Stripe payments
- First paying customers in DACH market
- Investor readiness (pitch, financials, metrics)
- Strategic partnerships with media organizations

**Why Hamburg:**
- NextMedia ecosystem aligns perfectly with Digital Journalism + AI intersection
- DACH is our launch market (German localization live)
- Access to 50+ media industry mentors for validation

> Speaker notes: Be specific about what you need. Media Lift is not just funding -- it's mentorship, validation, and network. The EUR 12,000 funding covers operational costs; the real value is structured access to media professionals who can validate whether WorldBrief solves a real workflow problem.

---

### SLIDE 13: Closing

**WorldBrief**
Thousands of articles. Dozens of structured events. Connected across time and geography. Examined for adequacy.

worldbrief.info
[contact email]

---

## Design Notes for Google Slides

**Recommended template style:** Clean, minimal, dark or navy background with white text. WorldBrief is an intelligence product -- the deck should feel professional and authoritative, not startup-playful.

**Suggested tools for visual polish:**
- **Gamma.app** -- paste this markdown, it generates a visual deck automatically (free tier = 10 slides)
- **Beautiful.ai** -- similar auto-layout from text input
- **SlidesGo / SlidesCarnival** -- free Google Slides templates to build manually
- **Google Slides + Unsplash plugin** -- for background images (world maps, data visualizations)

**Must-include visuals:**
1. Product screenshots (slides 5) -- take from worldbrief.info
2. Pipeline diagram (slide 4) -- simple left-to-right flow
3. Comparison table (slide 6) -- use the grid as-is
4. Market positioning quadrant (slide 8) -- 2x2: Automated vs Manual, Unstructured vs Structured

**Slide count:** 13 slides is within the typical 10-15 range for accelerator applications. Cut slides 7 (RAI detail) or 8 (market) if you need to trim.
