export async function GET() {
  const content = `# WorldBrief

> AI-powered global news intelligence platform. Multilingual coverage from 180+ media sources organized by country, theme, and narrative frame.

WorldBrief aggregates reporting from international media across 6 continents and dozens of languages, then structures it into navigable briefings by geography and strategic theme.

## Content Structure

- **Countries & Regions**: Each country has strategic tracks (politics, economy, security, diplomacy, society, technology). Example: /c/AMERICAS-USA, /c/EUROPE-GERMANY
- **Tracks**: Topic-level summaries within each country. Example: /c/AMERICAS-USA/t/geo_politics
- **Events/Topics**: Individual news stories tracked across sources with narrative frame analysis. Example: /events/{uuid}
- **Epics**: Cross-country stories that span multiple regions. Example: /epics/iran-nuclear-talks
- **Regions**: Continental groupings (Americas, Europe, Asia, Middle East, Africa, Oceania). Example: /region/europe

## Features

- Multilingual source aggregation (English, Arabic, Chinese, Russian, French, German, Spanish, and more)
- Narrative frame extraction: identifies competing editorial stances (pro/against/neutral) in news coverage
- Coverage assessment: publisher diversity, language distribution, geographic blind spots
- Signal tracking: persons, organizations, places, commodities, policies, systems

## Pages

- Homepage: https://worldbrief.info/
- Monthly Intelligence: https://worldbrief.info/epics
- Media Sources: https://worldbrief.info/sources
- About: https://worldbrief.info/about
- Method & Disclaimer: https://worldbrief.info/disclaimer
`;

  return new Response(content, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
