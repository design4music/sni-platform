// Sitemap index — points Google at the four page-type sitemaps.
// Each child sitemap reads a pre-generated XML blob from sitemap_cache
// (single PK lookup), so there is no cold-start latency for Googlebot.
//
// sitemap-geo.xml    — regions, centroids, centroid/about pages
// sitemap-daily.xml  — daily brief pages (/c/*/t/*/YYYY-MM-DD)
// sitemap-sources.xml — /sources + per-outlet + per-outlet/month pages
// sitemap-static.xml  — top-level informational pages

export const dynamic = 'force-dynamic';

const SITE_URL = 'https://www.worldbrief.info';

export async function GET() {
  const body = `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>${SITE_URL}/sitemap-geo.xml</loc>
  </sitemap>
  <sitemap>
    <loc>${SITE_URL}/sitemap-daily.xml</loc>
  </sitemap>
  <sitemap>
    <loc>${SITE_URL}/sitemap-sources.xml</loc>
  </sitemap>
  <sitemap>
    <loc>${SITE_URL}/sitemap-static.xml</loc>
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
