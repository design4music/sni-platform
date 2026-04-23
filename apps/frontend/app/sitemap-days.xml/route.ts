import { query } from '@/lib/db';

// Day-canonical sitemap. One URL per row in daily_briefs — the existing
// threshold (>5 promoted clusters) already gates these to rank-worthy
// content, so every row becomes an indexable page.
//
// Kept separate from /sitemap.xml so:
//   - day URLs (fast growth) and structural URLs (slow growth) evolve
//     independently
//   - we can monitor day-URL indexation separately in Search Console
//   - approaching Google's 50,000 URL cap doesn't force a migration of
//     the structural sitemap
//
// If the day count ever crosses the 50K cap, split by year/month via
// route segments (e.g. sitemap-days-2026-04.xml). Current headroom: at
// ~1,500 new briefs/month × 2 locales = 3,000 URLs/month, 50K is
// reached after ~16 months of growth.

export const revalidate = 86400;

const SITE_URL = 'https://worldbrief.info';
const SITEMAP_MAX = 50_000;

function xmlEscape(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

export async function GET() {
  const rows = await query<{
    centroid_id: string;
    track: string;
    date: string;
    generated_at: string;
  }>(
    `SELECT c.id AS centroid_id,
            ctm.track AS track,
            db.date::text AS date,
            db.generated_at::text AS generated_at
       FROM daily_briefs db
       JOIN ctm ON ctm.id = db.ctm_id
       JOIN centroids_v3 c ON c.id = ctm.centroid_id
      WHERE c.is_active = true
      ORDER BY db.date DESC, c.id, ctm.track
      LIMIT $1`,
    [SITEMAP_MAX]
  );

  const urls = rows.map(r => {
    const path = `/c/${r.centroid_id}/t/${r.track}/${r.date}`;
    const en = `${SITE_URL}${path}`;
    const de = `${SITE_URL}/de${path}`;
    const lastmod = r.generated_at
      ? new Date(r.generated_at).toISOString()
      : new Date(`${r.date}T00:00:00Z`).toISOString();
    return `  <url>
    <loc>${xmlEscape(en)}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
    <xhtml:link rel="alternate" hreflang="en" href="${xmlEscape(en)}" />
    <xhtml:link rel="alternate" hreflang="de" href="${xmlEscape(de)}" />
    <xhtml:link rel="alternate" hreflang="x-default" href="${xmlEscape(en)}" />
  </url>`;
  });

  const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${urls.join('\n')}
</urlset>
`;

  return new Response(body, {
    status: 200,
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, s-maxage=86400',
    },
  });
}
