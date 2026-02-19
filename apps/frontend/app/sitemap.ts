import { MetadataRoute } from 'next';
import { getAllCentroids, getTracksByCentroid } from '@/lib/queries';
import { REGIONS, RegionKey } from '@/lib/types';

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

  // Centroid (country) pages + their track pages
  const centroids = await getAllCentroids();
  for (const c of centroids) {
    entries.push({
      url: `${SITE_URL}/c/${c.id}`,
      changeFrequency: 'daily',
      priority: 0.8,
    });

    const tracks = await getTracksByCentroid(c.id);
    for (const track of tracks) {
      entries.push({
        url: `${SITE_URL}/c/${c.id}/t/${track}`,
        changeFrequency: 'daily',
        priority: 0.7,
      });
    }
  }

  return entries;
}
