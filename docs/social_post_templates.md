# Social Post Templates -- Review Doc

## Post Type 1: TRENDING EVENT

**Trigger:** Event with trending score, 10+ sources, last 3 days, has summary.
**Frequency:** Up to 8/day.
**Dedup:** Word overlap >60% against recently posted titles.

### Example:

```
<b>Iran's Supreme Leader Ali Khamenei has been killed, triggering a succession process.</b>

Iran's state media confirmed that Supreme Leader Ayatollah Ali Khamenei has been killed. The event marks the end of his 37-year rule over the country. An interim leadership council has been formed to oversee the transition...

Iran > Politics: 179 articles, 75 outlets, 12 languages
Read the full story, view sources and explore media narratives [link]

Trending story tracked by WorldBrief -- AI-powered, fully automated media intelligence with worldwide reach.
worldbrief.info
```

### Structure:
1. **Bold title**
2. Summary (truncated to 300 chars)
3. Topic path > Track: stats line (articles, outlets, languages)
4. CTA link to event page
5. Footer

---

## Post Type 2: CTM SPOTLIGHT

**Trigger:** CTM with summary, 50+ titles, not frozen, not posted in 7 days.
**Frequency:** Up to 3/day.
**Current problem:** Posts CTMs with empty/stub summaries like "No significant events reported."

### Example (good):

```
<b>Gulf States</b> -- Security

Loud blasts were heard over Dubai and Doha for a second day, with witnesses reporting explosions and smoke. US Central Command confirmed Iranian ballistic missiles targeted Al Udeid Air Base in Qatar...

Tracking 425 headlines
Explore the topic, view event timeline and related coverage [link]

Topic spotlight from WorldBrief -- AI-powered, fully automated media intelligence with worldwide reach.
worldbrief.info
```

### Example (bad -- currently posted):

```
<b>Germany</b> -- Security

No significant domestic or international events involving Germany were reported for March 2026.

Tracking 68 headlines
Explore the topic, view event timeline and related coverage [link]
```

### Proposed fix:
- Require summary_text LENGTH >= 200 (filters out stubs)
- Require title_count >= 100 (more meaningful topics)
- Order by title_count DESC (post the most active topics first)

---

## Post Type 3: NARRATIVE OF THE DAY

**Trigger:** Event with 20+ sources, last 48h, has summary. Extracts narrative frames via LLM, then calls RAI API for analysis.
**Frequency:** Up to 2/day, after 06:00 UTC.
**Dedup:** Against both narrative and trending posted titles.

### Example:

```
<b>Narrative of the Day</b>

<b>Iran's Supreme Leader Ali Khamenei has been killed, triggering a succession process.</b>

- <b>Khamenei as Tyrant, Death Liberates</b>: This frame portrays Khamenei's death as a positive event, ending a brutal...
- <b>Regime as Victim, Vows Righteous Revenge</b>: This frame presents the killing as an unjustified act of aggression...
- <b>Geopolitical Power Vacuum Analysis</b>: This frame focuses neutrally on the mechanics of succession, regional...

Coverage adequacy: 7/10
Blind spots: Civilian impact, economic consequences

Media narratives rarely agree. WorldBrief uses AI to extract competing frames from global coverage and assess what's missing.

Read full AI analysis [link] | View event and sources [link]

Narrative of the Day from WorldBrief -- AI-powered, fully automated media intelligence with worldwide reach.
worldbrief.info
```

### Structure:
1. "Narrative of the Day" header
2. Bold event title
3. 2-3 narrative frames with labels and descriptions
4. RAI scores: adequacy, blind spots
5. RAI synthesis excerpt
6. Two CTA links (analysis page + event page)
7. Footer

---

## Open Questions

1. **CTM spotlight quality gate** -- what minimum summary length / title count makes a CTM worth posting?
2. **Should CTM spotlight include event count?** -- "12 events tracked" would show activity level.
3. **Narrative footer** -- should we add a one-liner explaining what narrative analysis IS? E.g. "Media narratives rarely agree. WorldBrief uses AI to extract competing frames and assess what's missing."
4. **Posting cadence** -- currently 1h daemon interval (testing). Production: 3h? More?
5. **New post types to consider?**
   - "Signal of the Day" -- a trending person/org/policy with sparkline-style description
   - "Weekly digest" -- summary of top 5 stories of the week
   - "New topic alert" -- when a brand new CTM appears with rapid growth
