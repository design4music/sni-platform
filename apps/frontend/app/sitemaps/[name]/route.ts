import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

// Monthly sitemaps served from sitemap_cache.
// URLs: /sitemaps/daily-2026-01.xml, /sitemaps/events-2026-06.xml, etc.
// Cache key = name without .xml suffix (e.g. "daily-2026-01").
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ name: string }> },
) {
  const { name } = await params;
  const cacheKey = name.replace(/\.xml$/, '');

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
