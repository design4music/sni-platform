// Sitemap index — 3 structural sitemaps + one entry per monthly daily sitemap.
// Reads available months from sitemap_cache (daily-YYYY-MM keys) so it stays
// current automatically as the cron adds new months.

import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

const SITE_URL = 'https://www.worldbrief.info';

export async function GET() {
  const [dailyRows, eventRows] = await Promise.all([
    query<{ name: string }>(`SELECT name FROM sitemap_cache WHERE name LIKE 'daily-%' ORDER BY name DESC`),
    query<{ name: string }>(`SELECT name FROM sitemap_cache WHERE name LIKE 'events-%' ORDER BY name DESC`),
  ]);

  const dailySitemaps = dailyRows
    .map(r => {
      const month = r.name.slice('daily-'.length);
      return `  <sitemap>\n    <loc>${SITE_URL}/sitemap-daily.xml?month=${month}</loc>\n  </sitemap>`;
    })
    .join('\n');

  const eventSitemaps = eventRows
    .map(r => {
      const month = r.name.slice('events-'.length);
      return `  <sitemap>\n    <loc>${SITE_URL}/sitemap-events.xml?month=${month}</loc>\n  </sitemap>`;
    })
    .join('\n');

  const body = `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>${SITE_URL}/sitemap-geo.xml</loc>
  </sitemap>
  <sitemap>
    <loc>${SITE_URL}/sitemap-sources.xml</loc>
  </sitemap>
  <sitemap>
    <loc>${SITE_URL}/sitemap-static.xml</loc>
  </sitemap>
${dailySitemaps}
${eventSitemaps}
</sitemapindex>
`;

  return new Response(body, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, max-age=60, s-maxage=3600',
    },
  });
}
