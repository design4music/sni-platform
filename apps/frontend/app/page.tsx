import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import MapSection from '@/components/MapSection';
import SourceCarousel from '@/components/SourceCarousel';
import AnimatedStats from '@/components/AnimatedStats';
import EpicCard from '@/components/EpicCard';
import { getCentroidsByClass, getAllActiveFeeds, getLatestEpics } from '@/lib/queries';
import { REGIONS } from '@/lib/types';
import Link from 'next/link';

export const revalidate = 300;

export const metadata: Metadata = {
  title: 'WorldBrief - Understand the world. Briefly.',
  description: 'AI-powered global news intelligence. Multilingual coverage from 180+ sources, organized by country, theme, and narrative frame. Updated daily.',
  alternates: { canonical: '/' },
};

export default async function HomePage() {
  const geoCentroids = await getCentroidsByClass('geo');
  const feeds = await getAllActiveFeeds();
  const latestEpics = await getLatestEpics(3);

  const geoCentroidsWithMap = geoCentroids.filter(
    c => c.iso_codes && c.iso_codes.length > 0 && !c.id.startsWith('NON-STATE-')
  );

  // Group centroids by region for region cards
  const centroidsByRegion: Record<string, string[]> = {};
  for (const c of geoCentroids) {
    if (c.primary_theater && !c.id.startsWith('NON-STATE-')) {
      if (!centroidsByRegion[c.primary_theater]) centroidsByRegion[c.primary_theater] = [];
      centroidsByRegion[c.primary_theater].push(c.label);
    }
  }

  return (
    <DashboardLayout>
      <div className="space-y-12">
        {/* Introduction */}
        <section className="max-w-3xl">
          <h1 className="text-5xl font-bold mb-6">Understand the world. Briefly.</h1>
          <p className="text-xl text-dashboard-text-muted mb-4">
            WorldBrief turns global news reporting into continuously updated briefings,
            organized by country and topic. See what&apos;s happening around the
            world — clearly, quickly, and with sources.
          </p>
          <div className="flex gap-4">
            <Link href="/disclaimer" className="text-blue-400 hover:text-blue-300 underline">
              How it works
            </Link>
          </div>
        </section>

        {/* Map */}
        <MapSection centroids={geoCentroidsWithMap} />

        {/* Regions */}
        <section>
          <h2 className="text-3xl font-bold mb-6">World regions at a glance</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(REGIONS).map(([key, label]) => {
              const names = centroidsByRegion[key] || [];
              return (
                <Link
                  key={key}
                  href={`/region/${key.toLowerCase()}`}
                  className="p-6 border border-dashboard-border bg-dashboard-surface rounded-lg hover:border-blue-500 transition group"
                >
                  <h3 className="text-xl font-semibold mb-2">{label}</h3>
                  <p className="text-sm text-dashboard-text-muted leading-relaxed">
                    {names.join(', ')}
                  </p>
                </Link>
              );
            })}
          </div>
          <p className="text-sm text-dashboard-text-muted mt-4">
            Coverage varies by country and region depending on available media sources.
          </p>
        </section>

        {/* Cross-Country Epics */}
        {latestEpics.length > 0 && (
          <section>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-bold">Cross-Country Stories</h2>
              <Link
                href="/epics"
                className="text-sm text-blue-400 hover:text-blue-300 transition"
              >
                View all
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {latestEpics.map(epic => (
                <EpicCard key={epic.id} epic={epic} />
              ))}
            </div>
          </section>
        )}

        {/* Sources Carousel */}
        <SourceCarousel feedCount={feeds.length} />

        {/* Animated Stats */}
        <AnimatedStats
          feedCount={feeds.length}
          languageCount={20}
          dailyArticles={5000}
          centroidCount={85}
        />
      </div>
    </DashboardLayout>
  );
}
