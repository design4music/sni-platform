// Sitemap index — points Google at the two real sitemap files.
//
// Why this exists separately from app/sitemap.ts and
// app/sitemap-days.xml/route.ts: GSC marked both individual sitemaps
// "Couldn't fetch" during yesterday's OOM windows and is slow to retry.
// The index gives a fresh URL with no cached failure, and is also the
// standard pattern Google recommends for multi-sitemap sites.
//
// Static content; only changes when we add a new sitemap. Cached
// indefinitely.

export const revalidate = false;

const SITE_URL = 'https://www.worldbrief.info';

export async function GET() {
  const body = `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>${SITE_URL}/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>${SITE_URL}/sitemap-days.xml</loc>
  </sitemap>
</sitemapindex>
`;

  return new Response(body, {
    status: 200,
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, s-maxage=86400',
    },
  });
}
