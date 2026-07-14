# Conservative / Right-of-Center News Feeds Proposal

## Summary
14 conservative/right-of-center outlets selected for foreign-policy and geopolitics coverage depth. All outlets verified as active with correct domains (Google News RSS via site-search). Spans MAGA populist, establishment conservative, neoconservative, paleoconservative, and realist foreign-policy perspectives.

---

## Feeds Table

| Name | Domain | Country | Editorial Lean | FP Coverage | Google News RSS URL |
|------|--------|---------|-----------------|-------------|---------------------|
| **Breitbart** | breitbart.com | US | Populist/MAGA | Extensive world news section, national security focus | https://news.google.com/rss/search?q=site:breitbart.com&hl=en |
| **Daily Caller** | dailycaller.com | US | Right-wing populist | NATO, defense, military commitment articles | https://news.google.com/rss/search?q=site:dailycaller.com&hl=en |
| **Daily Wire** | dailywire.com | US | Right-wing conservative | Dedicated FP section, Iran, defense issues | https://news.google.com/rss/search?q=site:dailywire.com&hl=en |
| **Townhall** | townhall.com | US | Establishment conservative | Strong national defense advocacy, assertive FP positions | https://news.google.com/rss/search?q=site:townhall.com&hl=en |
| **Washington Times** | washingtontimes.com | US | Neoconservative | Hawkish, pro-Israel, global affairs coverage | https://news.google.com/rss/search?q=site:washingtontimes.com&hl=en |
| **Washington Examiner** | washingtonexaminer.com | US | Right-center | Dedicated FP section, military support, interventionist | https://news.google.com/rss/search?q=site:washingtonexaminer.com&hl=en |
| **National Review** | nationalreview.com | US | Establishment conservative | Prominent FP coverage, neoconservative/internationalist, intellectual depth | https://news.google.com/rss/search?q=site:nationalreview.com&hl=en |
| **American Conservative** | theamericanconservative.com | US | Paleoconservative | Strong FP coverage, explicitly anti-interventionist, realist | https://news.google.com/rss/search?q=site:theamericanconservative.com&hl=en |
| **National Interest** | nationalinterest.org | US | Foreign policy realism | Primary FP outlet, extensive geopolitics/security analysis, realist framework | https://news.google.com/rss/search?q=site:nationalinterest.org&hl=en |
| **Washington Free Beacon** | freebeacon.com | US | Neoconservative | Investigative journalism, international security focus | https://news.google.com/rss/search?q=site:freebeacon.com&hl=en |
| **RealClearWorld** | realclearworld.com | US | Center-right aggregator | Non-partisan global news aggregator, curated international coverage | https://news.google.com/rss/search?q=site:realclearworld.com&hl=en |
| **Commentary Magazine** | commentarymagazine.com | US | Neoconservative | Serious FP analysis, defense-focused, intellectual journal | https://news.google.com/rss/search?q=site:commentarymagazine.com&hl=en |
| **The Dispatch** | thedispatch.com | US | Center-right | Jonah Goldberg-led outlet, serious FP/national security analysis | https://news.google.com/rss/search?q=site:thedispatch.com&hl=en |
| **Spectator** | spectator.co.uk | GB | Right-center | Eurosceptic/Atlanticist, pro-Israel, geopolitical commentary | https://news.google.com/rss/search?q=site:spectator.co.uk&hl=en |

---

## Notes on Selection Criteria

### Included (Strong FP Coverage)
- All outlets verified to have **substantive, regular coverage** of foreign policy, defense, trade, or geopolitics
- Avoid outlets primarily focused on culture-war, lifestyle, or tabloid content
- Span ideological diversity within right-of-center (populist ↔ establishment; interventionist ↔ restraint; neoconservative ↔ paleoconservative)
- Prioritize outlets covering Europe-US tensions, NATO, China, Iran, trade wars, defense spending

### Excluded (Weak / No FP Coverage)
The following candidates were assessed and excluded:
- **Newsmax** – "America First" rhetoric but limited substantive FP analysis
- **The Federalist** – Religion/politics/culture focus; minimal serious foreign-affairs content
- **The Post Millennial** – Anti-woke/anti-progressive focus; no meaningful FP coverage
- **OANN** – Pro-Trump echo chamber; conspiracy theory prone; lacks geopolitical depth
- **New York Post** – Tabloid/gossip emphasis (Page Six); limited serious FP analysis
- **Fox Business** – Business/economics focus; minimal Foreign Policy subsection
- **GB News** – Culture wars focus; limited substantive geopolitics
- **UnHerd** – "Heterodox" framing but minimal foreign policy depth

---

## Geographic Coverage

- **US outlets**: 13
- **UK outlets**: 1 (Spectator UK – provides Atlanticist/Eurosceptic right-wing perspective)

---

## Ideological Spectrum

| Position | Outlets |
|----------|---------|
| **Populist/MAGA** | Breitbart, Daily Caller, Daily Wire |
| **Establishment conservative** | National Review, Townhall, Washington Examiner |
| **Neoconservative (interventionist)** | Washington Times, Washington Free Beacon, Commentary Magazine |
| **Realist foreign-policy** | National Interest, The American Conservative |
| **Center-right/institutional** | RealClearWorld, The Dispatch |
| **International (UK)** | Spectator UK |

---

## Geopolitics Coverage Focus Areas

All selected outlets show consistent coverage of:
- **Europe-US tensions** (NATO, Ukraine, energy, sanctions)
- **China policy** (trade, tech, military, Taiwan)
- **Middle East** (Iran, Israel, Saudi Arabia, proxies)
- **Defense/military** (procurement, strategy, spending)
- **Global trade** (tariffs, supply chains, alliances)
- **US grand strategy** (great power competition, retreat/engagement debates)

---

## Implementation Notes

1. All URLs use Google News RSS site-search format: `https://news.google.com/rss/search?q=site:DOMAIN&hl=en`
2. All feeds set to `language_code='en'`, `is_active=true`, `priority=1`, `fetch_interval_minutes=60`
3. Slugs generated in kebab-case from outlet names
4. Domains verified as current publishing domains (no redirects expected)
5. SQL migration uses `ON CONFLICT (url) DO NOTHING` for idempotence
