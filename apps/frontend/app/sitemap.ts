import { MetadataRoute } from 'next';
import { query } from '@/lib/db';
import { REGIONS } from '@/lib/types';

// Revalidate daily — enough freshness for Google, doesn't hammer DB per crawl.
export const revalidate = 86400;

const SITE_URL = 'https://worldbrief.info';

// Google's hard limit is 50,000 URLs per sitemap. We pack structural pages
// (static + regions + centroids + tracks + calendars + narratives + epics +
// sources + signals + meta narratives) plus the most recent/relevant events,
// capped to stay under the ceiling. If total grows past the cap, fall back to
// splitting via generateSitemaps + a manual index route.
const SITEMAP_MAX_URLS = 48_000;

// Only events with a dedicated /events/[id] page (>= 5 sources) go in the
// sitemap. Lower-coverage clusters are still discoverable via calendar pages.
const EVENT_MIN_SOURCES = 5;

function alt(path: string) {
  return {
    languages: {
      de: `${SITE_URL}/de${path}`,
      'x-default': `${SITE_URL}${path}`,
    },
  };
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const entries: MetadataRoute.Sitemap = [];

  // Static pages
  const staticPages: Array<{ path: string; freq: MetadataRoute.Sitemap[number]['changeFrequency']; prio: number }> = [
    { path: '', freq: 'daily', prio: 1.0 },
    { path: '/trending', freq: 'daily', prio: 0.9 },
    { path: '/epics', freq: 'daily', prio: 0.9 },
    { path: '/narratives', freq: 'daily', prio: 0.8 },
    { path: '/narratives/map', freq: 'weekly', prio: 0.6 },
    { path: '/signals', freq: 'daily', prio: 0.7 },
    { path: '/sources', freq: 'weekly', prio: 0.5 },
    { path: '/about', freq: 'monthly', prio: 0.4 },
    { path: '/methodology', freq: 'monthly', prio: 0.3 },
    { path: '/pricing', freq: 'monthly', prio: 0.5 },
    { path: '/faq', freq: 'monthly', prio: 0.4 },
    { path: '/known-issues', freq: 'monthly', prio: 0.3 },
    { path: '/terms', freq: 'monthly', prio: 0.2 },
    { path: '/privacy', freq: 'monthly', prio: 0.2 },
  ];
  for (const p of staticPages) {
    entries.push({
      url: `${SITE_URL}${p.path || '/'}`,
      changeFrequency: p.freq,
      priority: p.prio,
      alternates: alt(p.path || '/'),
    });
  }

  // Region pages
  for (const key of Object.keys(REGIONS)) {
    const path = `/region/${key.toLowerCase()}`;
    entries.push({
      url: `${SITE_URL}${path}`,
      changeFrequency: 'daily',
      priority: 0.8,
      alternates: alt(path),
    });
  }

  // Centroid + track + calendar pages
  const ctmRows = await query<{ centroid_id: string; track: string | null }>(
    `SELECT c.id as centroid_id, ctm.track
       FROM centroids_v3 c
       LEFT JOIN (SELECT DISTINCT centroid_id, track FROM ctm) ctm ON ctm.centroid_id = c.id
      WHERE c.is_active = true
      ORDER BY c.id, ctm.track`
  );
  const centroidTracks = new Map<string, string[]>();
  for (const row of ctmRows) {
    if (!centroidTracks.has(row.centroid_id)) centroidTracks.set(row.centroid_id, []);
    if (row.track) centroidTracks.get(row.centroid_id)!.push(row.track);
  }
  for (const [centroidId, tracks] of centroidTracks) {
    entries.push({
      url: `${SITE_URL}/c/${centroidId}`,
      changeFrequency: 'daily',
      priority: 0.8,
      alternates: alt(`/c/${centroidId}`),
    });
    for (const track of tracks) {
      // Track URL (no date): general landing for the latest activity.
      // Day-canonical URLs in /sitemap-days.xml concentrate link equity
      // per specific date; keep this as a lower-priority landing page.
      entries.push({
        url: `${SITE_URL}/c/${centroidId}/t/${track}`,
        changeFrequency: 'daily',
        priority: 0.5,
        alternates: alt(`/c/${centroidId}/t/${track}`),
      });
    }
  }

  // Epics
  const epicRows = await query<{ slug: string; updated_at: string | null }>(
    `SELECT slug, updated_at::text FROM epics WHERE slug IS NOT NULL ORDER BY updated_at DESC NULLS LAST`
  );
  for (const e of epicRows) {
    const path = `/epics/${e.slug}`;
    entries.push({
      url: `${SITE_URL}${path}`,
      lastModified: e.updated_at ? new Date(e.updated_at) : undefined,
      changeFrequency: 'weekly',
      priority: 0.7,
      alternates: alt(path),
    });
  }

  // Strategic narratives + meta narratives
  const narrativeRows = await query<{ id: string }>(
    `SELECT id::text FROM strategic_narratives ORDER BY id`
  );
  for (const n of narrativeRows) {
    const path = `/narratives/${n.id}`;
    entries.push({
      url: `${SITE_URL}${path}`,
      changeFrequency: 'weekly',
      priority: 0.6,
      alternates: alt(path),
    });
  }
  const metaRows = await query<{ id: string }>(
    `SELECT id::text FROM meta_narratives ORDER BY id`
  );
  for (const m of metaRows) {
    const path = `/narratives/meta/${m.id}`;
    entries.push({
      url: `${SITE_URL}${path}`,
      changeFrequency: 'weekly',
      priority: 0.6,
      alternates: alt(path),
    });
  }

  // Signal category index pages
  const signalTypes = ['persons', 'orgs', 'places', 'commodities', 'policies', 'systems', 'named_events'];
  for (const st of signalTypes) {
    const path = `/signals/${st}`;
    entries.push({
      url: `${SITE_URL}${path}`,
      changeFrequency: 'daily',
      priority: 0.5,
      alternates: alt(path),
    });
  }

  // Source (publisher) profiles — only ones with meaningful coverage
  const feedRows = await query<{ name: string }>(
    `SELECT t.publisher_name AS name
       FROM titles_v3 t
      WHERE t.publisher_name IS NOT NULL
        AND t.processing_status IN ('assigned','out_of_scope')
      GROUP BY t.publisher_name
      HAVING COUNT(*) >= 20
      ORDER BY t.publisher_name`
  );
  for (const f of feedRows) {
    const path = `/sources/${encodeURIComponent(f.name)}`;
    entries.push({
      url: `${SITE_URL}${path}`,
      changeFrequency: 'weekly',
      priority: 0.4,
      alternates: alt(path),
    });
  }

  // Events — fill remaining capacity with most recent events that have a
  // dedicated page. Ordered newest-first so Google sees fresh content.
  const remaining = Math.max(0, SITEMAP_MAX_URLS - entries.length);
  if (remaining > 0) {
    const eventRows = await query<{ id: string; last_active: string | null; date: string; source_count: number }>(
      `SELECT e.id::text AS id,
              COALESCE(e.last_active, e.date)::text AS last_active,
              e.date::text AS date,
              e.source_batch_count AS source_count
         FROM events_v3 e
        WHERE e.is_promoted = true
          AND e.merged_into IS NULL
          AND e.is_catchall = false
          AND e.source_batch_count >= $1
        ORDER BY e.date DESC, e.source_batch_count DESC, e.id
        LIMIT $2`,
      [EVENT_MIN_SOURCES, remaining]
    );
    for (const r of eventRows) {
      entries.push({
        url: `${SITE_URL}/events/${r.id}`,
        lastModified: new Date(r.last_active || r.date),
        changeFrequency: 'monthly',
        priority: Math.min(0.7, 0.3 + Math.log10(Math.max(1, r.source_count)) * 0.1),
        alternates: alt(`/events/${r.id}`),
      });
    }
  }

  return entries;
}
