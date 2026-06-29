import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

// Event sitemaps split by month (events-YYYY-MM cache keys).
// Only prose-bearing events (summary IS NOT NULL) are included.
export async function GET(request: Request) {
  const month = new URL(request.url).searchParams.get('month');
  if (!month) {
    return new Response('Pass ?month=YYYY-MM', { status: 400 });
  }

  const rows = await query<{ content: string }>(
    `SELECT content FROM sitemap_cache WHERE name = $1`,
    [`events-${month}`],
  );
  if (!rows.length) {
    return new Response('Sitemap not yet generated — run the revalidate-sitemap cron.', {
      status: 503,
      headers: { 'Retry-After': '3600' },
    });
  }
  return new Response(rows[0].content, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, s-maxage=86400',
    },
  });
}
