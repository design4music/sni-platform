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
            <Link href="#how-it-works" className="text-blue-400 hover:text-blue-300 underline">
              How it works
            </Link>
          </div>
        </section>

        {/* AI Disclaimer */}
        <section className="bg-dashboard-surface border border-dashboard-border rounded-lg p-6 max-w-3xl">
          <h2 className="text-xl font-semibold mb-2">AI-Generated Content</h2>
          <p className="text-dashboard-text-muted">
            Summaries are AI-generated from aggregated reporting. Source links are provided for verification.{' '}
            <Link href="#how-it-works" className="text-blue-400 hover:text-blue-300 underline">
              Learn how WorldBrief works
            </Link>
            .
          </p>
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

        {/* How it works */}
        <section id="how-it-works" className="max-w-3xl">
          <h2 className="text-3xl font-bold mb-6">How WorldBrief Works</h2>
          <div className="space-y-4 text-dashboard-text-muted">
            <p>
              <strong className="text-dashboard-text">1. Ingestion:</strong> WorldBrief continuously monitors global news sources via RSS feeds,
              capturing thousands of articles daily across multiple languages.
            </p>
            <p>
              <strong className="text-dashboard-text">2. Strategic Filtering:</strong> Articles are filtered for strategic relevance
              using taxonomy matching and AI-powered gating, focusing on geopolitical, security, and economic developments.
            </p>
            <p>
              <strong className="text-dashboard-text">3. Centroid Assignment:</strong> Strategic articles are assigned to centroids
              (countries, regions, or thematic lenses) and classified into tracks (military, diplomacy, economic, etc.).
            </p>
            <p>
              <strong className="text-dashboard-text">4. Narrative Generation:</strong> AI synthesizes monthly summaries and event
              timelines for each centroid-track combination, creating structured intelligence narratives.
            </p>
            <p>
              <strong className="text-dashboard-text">5. Presentation:</strong> You navigate these narratives through an intuitive
              interface organized by actor, theme, and time.
            </p>
          </div>
        </section>
      </div>
    </DashboardLayout>
  );
}
