import DashboardLayout from '@/components/DashboardLayout';
import CentroidCard from '@/components/CentroidCard';
import MapSection from '@/components/MapSection';
import { getCentroidsByClass, getAllActiveFeeds } from '@/lib/queries';
import { REGIONS } from '@/lib/types';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

export default async function HomePage() {
  const systemicCentroids = await getCentroidsByClass('systemic');
  const geoCentroids = await getCentroidsByClass('geo');
  const feeds = await getAllActiveFeeds();

  // Non-State Actors are geo centroids with IDs starting with "NON-STATE-"
  const nonStateActors = geoCentroids.filter(c => c.id.startsWith('NON-STATE-'));
  const geoCentroidsWithMap = geoCentroids.filter(
    c => c.iso_codes && c.iso_codes.length > 0 && !c.id.startsWith('NON-STATE-')
  );

  // Get sample feeds for preview (12 feeds from different outlets)
  const sampleFeeds = feeds.slice(0, 12);

  return (
    <DashboardLayout>
      <div className="space-y-12">
        {/* Introduction */}
        <section className="max-w-3xl">
          <h1 className="text-5xl font-bold mb-6">Understand the world. Briefly.</h1>
          <p className="text-xl text-dashboard-text-muted mb-4">
            WorldBrief turns global reporting into continuously updated briefings by geography and theme.
            Explore what's happening across the world—clearly, quickly, and in context.
          </p>
          <div className="flex gap-4">
            <Link href="/disclaimer" className="text-blue-400 hover:text-blue-300 underline">
              How it works
            </Link>
          </div>
        </section>

        {/* Map */}
        <MapSection centroids={geoCentroidsWithMap} />

        {/* System Centroids */}
        <section>
          <h2 className="text-3xl font-bold mb-6">Global Thematic Lenses</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {systemicCentroids.map(centroid => (
              <CentroidCard key={centroid.id} centroid={centroid} />
            ))}
          </div>
        </section>

        {/* Regions */}
        <section>
          <h2 className="text-3xl font-bold mb-6">Regional Intelligence</h2>
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
        </section>

        {/* Non-State Actors */}
        {nonStateActors.length > 0 && (
          <section>
            <h2 className="text-3xl font-bold mb-6">Non-State Actors</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {nonStateActors.map(centroid => (
                <CentroidCard key={centroid.id} centroid={centroid} />
              ))}
            </div>
          </section>
        )}

        {/* Sources Preview */}
        <section>
          <div className="flex items-end justify-between mb-6">
            <div>
              <h2 className="text-3xl font-bold">Our Sources</h2>
              <p className="text-dashboard-text-muted mt-2">
                {feeds.length}+ international news sources across all regions
              </p>
            </div>
            <Link
              href="/sources"
              className="text-blue-400 hover:text-blue-300 underline text-sm"
            >
              View all sources
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {sampleFeeds.map(feed => (
              <div
                key={feed.id}
                className="bg-dashboard-surface border border-dashboard-border rounded p-3 text-center"
              >
                <p className="text-sm text-dashboard-text-muted truncate">
                  {feed.name}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* How it works - merged with metrics and disclaimer */}
        <section id="how-it-works" className="border-t border-dashboard-border pt-12">
          {/* Metrics strip */}
          <div className="grid grid-cols-3 gap-8 mb-8 text-center">
            <div>
              <p className="text-4xl md:text-5xl font-bold text-dashboard-text">{feeds.length}+</p>
              <p className="text-sm text-dashboard-text-muted mt-1">RSS feeds</p>
            </div>
            <div>
              <p className="text-4xl md:text-5xl font-bold text-dashboard-text">20+</p>
              <p className="text-sm text-dashboard-text-muted mt-1">languages</p>
            </div>
            <div>
              <p className="text-4xl md:text-5xl font-bold text-dashboard-text">5,000+</p>
              <p className="text-sm text-dashboard-text-muted mt-1">articles / day</p>
            </div>
          </div>

          {/* Short description */}
          <p className="text-center text-dashboard-text-muted max-w-2xl mx-auto mb-6">
            WorldBrief aggregates global reporting, filters for strategic relevance, and synthesizes it into structured briefings by geography and theme.
          </p>

          {/* AI disclaimer line */}
          <p className="text-center text-sm text-dashboard-text-muted/70">
            All summaries are AI-generated.{' '}
            <Link href="/disclaimer" className="text-blue-400/70 hover:text-blue-300 underline">
              Learn more about our method
            </Link>
          </p>
        </section>
      </div>
    </DashboardLayout>
  );
}
