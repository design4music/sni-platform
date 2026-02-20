import { MetadataRoute } from 'next';
import { query } from '@/lib/db';
import { REGIONS } from '@/lib/types';

const SITE_URL = 'https://worldbrief.info';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const entries: MetadataRoute.Sitemap = [];

  // Static pages
  entries.push(
    { url: SITE_URL, changeFrequency: 'daily', priority: 1.0 },
    { url: `${SITE_URL}/epics`, changeFrequency: 'daily', priority: 0.9 },
    { url: `${SITE_URL}/about`, changeFrequency: 'monthly', priority: 0.4 },
    { url: `${SITE_URL}/disclaimer`, changeFrequency: 'monthly', priority: 0.3 },
    { url: `${SITE_URL}/sources`, changeFrequency: 'weekly', priority: 0.5 },
    { url: `${SITE_URL}/global`, changeFrequency: 'weekly', priority: 0.6 },
  );

  // Region pages
  for (const key of Object.keys(REGIONS)) {
    entries.push({
      url: `${SITE_URL}/region/${key.toLowerCase()}`,
      changeFrequency: 'daily',
      priority: 0.8,
    });
  }

  // Centroid pages + track pages in a single query
  const rows = await query<{ centroid_id: string; track: string | null }>(
    `SELECT c.id as centroid_id, ctm.track
     FROM centroids_v3 c
     LEFT JOIN (SELECT DISTINCT centroid_id, track FROM ctm) ctm ON ctm.centroid_id = c.id
     WHERE c.is_active = true
     ORDER BY c.id, ctm.track`
  );

  const centroidTracks = new Map<string, string[]>();
  for (const row of rows) {
    if (!centroidTracks.has(row.centroid_id)) {
      centroidTracks.set(row.centroid_id, []);
    }
    if (row.track) {
      centroidTracks.get(row.centroid_id)!.push(row.track);
    }
  }

  for (const [centroidId, tracks] of centroidTracks) {
    entries.push({
      url: `${SITE_URL}/c/${centroidId}`,
      changeFrequency: 'daily',
      priority: 0.8,
    });
    for (const track of tracks) {
      entries.push({
        url: `${SITE_URL}/c/${centroidId}/t/${track}`,
        changeFrequency: 'daily',
        priority: 0.7,
      });
    }
  }

  return entries;
}
