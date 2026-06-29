import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET() {
  const rows = await query<{ content: string }>(
    `SELECT content FROM sitemap_cache WHERE name = $1`,
    ['geo'],
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
