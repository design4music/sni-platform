import DashboardLayout from '@/components/DashboardLayout';
import MapSection from '@/components/MapSection';
import SourceCarousel from '@/components/SourceCarousel';
import AnimatedStats from '@/components/AnimatedStats';
import { getCentroidsByClass, getAllActiveFeeds } from '@/lib/queries';
import { REGIONS } from '@/lib/types';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

export default async function HomePage() {
  const geoCentroids = await getCentroidsByClass('geo');
  const feeds = await getAllActiveFeeds();

  const geoCentroidsWithMap = geoCentroids.filter(
    c => c.iso_codes && c.iso_codes.length > 0 && !c.id.startsWith('NON-STATE-')
  );

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
            {Object.entries(REGIONS).map(([key, label]) => (
              <Link
                key={key}
                href={`/region/${key.toLowerCase()}`}
                className="p-8 border border-dashboard-border bg-dashboard-surface rounded-lg hover:border-blue-500 transition text-center"
              >
                <h3 className="text-xl font-semibold">{label}</h3>
              </Link>
            ))}
          </div>
          <p className="text-sm text-dashboard-text-muted mt-4">
            Coverage varies by country and region depending on available media sources.
          </p>
        </section>

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
