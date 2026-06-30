import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

// Handles /sitemaps/daily-YYYY-MM.xml and /sitemaps/events-YYYY-MM.xml.
// Cache keys in sitemap_cache match the filename without .xml.
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ name: string }> },
) {
  const { name } = await params;
  const cacheKey = name.replace(/\.xml$/, '');

  if (!/^(daily|events)-\d{4}-\d{2}$/.test(cacheKey)) {
    return new Response('Not found', { status: 404 });
  }

  const rows = await query<{ content: string }>(
    `SELECT content FROM sitemap_cache WHERE name = $1`,
    [cacheKey],
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
