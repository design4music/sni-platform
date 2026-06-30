import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

const SITE_URL = 'https://www.worldbrief.info';

function xmlEscape(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

// Google News sitemap — only articles published in the last 48 hours.
// Covers EN daily brief pages. Google discovers DE alternates via hreflang.
export async function GET() {
  const rows = await query<{
    centroid_id: string;
    track: string;
    date: string;
    generated_at: string | null;
  }>(
    `SELECT c.id AS centroid_id, ctm.track, db.date::text, db.generated_at::text
       FROM daily_briefs db
       JOIN ctm ON ctm.id = db.ctm_id
       JOIN centroids_v3 c ON c.id = ctm.centroid_id
      WHERE c.is_active = true
        AND db.brief_en IS NOT NULL
        AND db.date >= CURRENT_DATE - INTERVAL '2 days'
      ORDER BY db.date DESC, c.id, ctm.track`,
  );

  const items = rows.map(r => {
    const loc = xmlEscape(`${SITE_URL}/c/${r.centroid_id}/t/${r.track}/${r.date}`);
    const pubDate = r.generated_at
      ? new Date(r.generated_at).toISOString()
      : `${r.date}T00:00:00Z`;
    const title = xmlEscape(`WorldBrief: ${r.centroid_id} ${r.track} ${r.date}`);
    return `  <url>
    <loc>${loc}</loc>
    <news:news>
      <news:publication>
        <news:name>WorldBrief</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>${pubDate}</news:publication_date>
      <news:title>${title}</news:title>
    </news:news>
  </url>`;
  });

  const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
${items.join('\n')}
</urlset>
`;

  return new Response(body, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, s-maxage=3600',
    },
  });
}
