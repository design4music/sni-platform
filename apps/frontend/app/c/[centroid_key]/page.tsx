import DashboardLayout from '@/components/DashboardLayout';
import TrackCard from '@/components/TrackCard';
import {
  getCentroidById,
  getTrackSummaryByCentroid,
  getAllCentroids,
} from '@/lib/queries';
import { notFound } from 'next/navigation';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

interface CentroidPageProps {
  params: Promise<{ centroid_key: string }>;
}

export default async function CentroidPage({ params }: CentroidPageProps) {
  const { centroid_key } = await params;
  const centroid = await getCentroidById(centroid_key);

  if (!centroid) {
    notFound();
  }

  const trackData = await getTrackSummaryByCentroid(centroid.id);
  const tracks = trackData.map(t => t.track).sort();
  const allCentroids = await getAllCentroids();
  const otherCentroids = allCentroids.filter(c => c.id !== centroid.id).slice(0, 10);

  const sidebar = (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-3">About</h3>
        <div className="space-y-2 text-sm">
          <p>
            <span className="text-dashboard-text-muted">Type:</span>{' '}
            <span className="capitalize">{centroid.class}</span>
          </p>
          {centroid.primary_theater && (
            <p>
              <span className="text-dashboard-text-muted">Region:</span>{' '}
              <Link
                href={`/region/${centroid.primary_theater}`}
                className="text-blue-400 hover:text-blue-300"
              >
                {centroid.primary_theater}
              </Link>
            </p>
          )}
        </div>
      </div>

      {otherCentroids.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Other Centroids</h3>
          <div className="space-y-2">
            {otherCentroids.map(c => (
              <Link
                key={c.id}
                href={`/c/${c.id}`}
                className="block text-sm text-dashboard-text-muted hover:text-dashboard-text transition"
              >
                {c.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <DashboardLayout title={centroid.label} sidebar={sidebar}>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-4">Strategic Tracks</h2>
          <p className="text-dashboard-text-muted mb-6">
            Narratives organized by strategic domain
          </p>
        </div>

        {tracks.length === 0 ? (
          <div className="text-center py-12 bg-dashboard-surface border border-dashboard-border rounded-lg">
            <p className="text-dashboard-text-muted">No tracks available for this centroid</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {trackData.map(data => (
              <TrackCard
                key={data.track}
                centroidId={centroid.id}
                track={data.track}
                latestMonth={data.latestMonth}
                titleCount={data.totalTitles}
              />
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
