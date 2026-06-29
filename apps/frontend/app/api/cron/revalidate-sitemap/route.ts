/**
 * POST /api/cron/revalidate-sitemap
 *
 * Generates all four sitemap XML blobs and stores them in sitemap_cache.
 * Each sitemap route (sitemap-geo.xml, sitemap-daily.xml, etc.) does a single
 * PK lookup against this table — no DB fan-out at request time, no cold-start
 * race condition.
 *
 * Run daily at 04:00 UTC via .github/workflows/revalidate-sitemap.yml.
 * Auth: header `x-revalidate-token: <REVALIDATE_API_KEY>`.
 */

import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { REGIONS } from '@/lib/types';

const SITE_URL = 'https://www.worldbrief.info';

function xmlEscape(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function wrapUrlset(inner: string): string {
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${inner}
</urlset>
`;
}

function urlBlock(
  path: string,
  opts: { lastmod?: string; freq: string; prio: number },
): string {
  const en = xmlEscape(`${SITE_URL}${path}`);
  const de = xmlEscape(`${SITE_URL}/de${path}`);
  const lastmodTag = opts.lastmod ? `\n    <lastmod>${opts.lastmod}</lastmod>` : '';
  const entry = (loc: string) =>
    `  <url>
    <loc>${loc}</loc>${lastmodTag}
    <changefreq>${opts.freq}</changefreq>
    <priority>${opts.prio.toFixed(1)}</priority>
    <xhtml:link rel="alternate" hreflang="en" href="${en}" />
    <xhtml:link rel="alternate" hreflang="de" href="${de}" />
    <xhtml:link rel="alternate" hreflang="x-default" href="${en}" />
  </url>`;
  return `${entry(en)}\n${entry(de)}`;
}

async function generateGeo(): Promise<{ xml: string; count: number }> {
  const centroids = await query<{ id: string }>(
    `SELECT id FROM centroids_v3 WHERE is_active = true ORDER BY id`,
  );

  const parts: string[] = [];

  for (const key of Object.keys(REGIONS)) {
    parts.push(urlBlock(`/region/${key.toLowerCase()}`, { freq: 'daily', prio: 0.8 }));
  }
  for (const c of centroids) {
    parts.push(urlBlock(`/c/${c.id}`, { freq: 'daily', prio: 0.8 }));
    parts.push(urlBlock(`/c/${c.id}/about`, { freq: 'monthly', prio: 0.5 }));
  }

  const count = (Object.keys(REGIONS).length + centroids.length * 2) * 2;
  return { xml: wrapUrlset(parts.join('\n')), count };
}

async function generateDaily(): Promise<{ xml: string; count: number }> {
  const rows = await query<{
    centroid_id: string;
    track: string;
    date: string;
    generated_at: string;
  }>(
    `SELECT c.id AS centroid_id,
            ctm.track,
            db.date::text,
            db.generated_at::text
       FROM daily_briefs db
       JOIN ctm ON ctm.id = db.ctm_id
       JOIN centroids_v3 c ON c.id = ctm.centroid_id
      WHERE c.is_active = true
      ORDER BY db.date DESC, c.id, ctm.track
      LIMIT 50000`,
  );

  const parts = rows.map(r => {
    const path = `/c/${r.centroid_id}/t/${r.track}/${r.date}`;
    const lastmod = r.generated_at
      ? new Date(r.generated_at).toISOString()
      : `${r.date}T00:00:00.000Z`;
    return urlBlock(path, { lastmod, freq: 'monthly', prio: 0.7 });
  });

  return { xml: wrapUrlset(parts.join('\n')), count: rows.length * 2 };
}

async function generateSources(): Promise<{ xml: string; count: number }> {
  const [feeds, months] = await Promise.all([
    query<{ slug: string }>(
      `SELECT slug FROM feeds WHERE is_active = true AND slug IS NOT NULL ORDER BY slug`,
    ),
    query<{ slug: string; m: string }>(
      `SELECT f.slug, TO_CHAR(d.month, 'YYYY-MM') AS m
         FROM feeds f
         JOIN (
           SELECT outlet_name AS feed_name, month FROM outlet_entity_stance
           UNION
           SELECT feed_name, month FROM mv_publisher_stats_monthly
         ) d ON d.feed_name = f.name
        WHERE f.is_active = true AND f.slug IS NOT NULL
        ORDER BY f.slug, d.month DESC`,
    ),
  ]);

  const parts: string[] = [urlBlock('/sources', { freq: 'weekly', prio: 0.5 })];
  for (const f of feeds) {
    parts.push(urlBlock(`/sources/${f.slug}`, { freq: 'weekly', prio: 0.4 }));
  }
  for (const r of months) {
    parts.push(urlBlock(`/sources/${r.slug}/${r.m}`, { freq: 'monthly', prio: 0.5 }));
  }

  return { xml: wrapUrlset(parts.join('\n')), count: (1 + feeds.length + months.length) * 2 };
}

function generateStatic(): { xml: string; count: number } {
  const pages = [
    { path: '/', freq: 'daily', prio: 1.0 },
    { path: '/about', freq: 'monthly', prio: 0.4 },
    { path: '/methodology', freq: 'monthly', prio: 0.3 },
    { path: '/pricing', freq: 'monthly', prio: 0.5 },
    { path: '/faq', freq: 'monthly', prio: 0.4 },
    { path: '/known-issues', freq: 'monthly', prio: 0.3 },
    { path: '/terms', freq: 'monthly', prio: 0.2 },
    { path: '/privacy', freq: 'monthly', prio: 0.2 },
  ];

  const parts = pages.map(p => urlBlock(p.path, { freq: p.freq, prio: p.prio }));
  return { xml: wrapUrlset(parts.join('\n')), count: pages.length * 2 };
}

async function upsertCache(name: string, xml: string): Promise<void> {
  await query(
    `INSERT INTO sitemap_cache (name, content, generated_at)
     VALUES ($1, $2, now())
     ON CONFLICT (name) DO UPDATE SET content = EXCLUDED.content, generated_at = now()`,
    [name, xml],
  );
}

export async function POST(req: NextRequest) {
  const token = req.headers.get('x-revalidate-token');
  const expected = process.env.REVALIDATE_API_KEY;
  if (!expected) {
    return NextResponse.json({ error: 'REVALIDATE_API_KEY not set' }, { status: 500 });
  }
  if (token !== expected) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  const [geo, daily, sources] = await Promise.all([
    generateGeo(),
    generateDaily(),
    generateSources(),
  ]);
  const staticSitemap = generateStatic();

  await Promise.all([
    upsertCache('geo', geo.xml),
    upsertCache('daily', daily.xml),
    upsertCache('sources', sources.xml),
    upsertCache('static', staticSitemap.xml),
  ]);

  return NextResponse.json({
    ok: true,
    generated_at: new Date().toISOString(),
    counts: {
      geo: geo.count,
      daily: daily.count,
      sources: sources.count,
      static: staticSitemap.count,
    },
  });
}
