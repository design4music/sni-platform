import DashboardLayout from '@/components/DashboardLayout';
import TrackCard from '@/components/TrackCard';
import GeoBriefSection from '@/components/GeoBriefSection';
import MonthPicker from '@/components/MonthPicker';
import {
  getCentroidById,
  getAvailableMonthsForCentroid,
  getTrackSummaryByCentroidAndMonth,
  getConfiguredTracksForCentroid,
} from '@/lib/queries';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { REGIONS } from '@/lib/types';

export const dynamic = 'force-dynamic';

function formatMonthLabel(monthStr: string): string {
  const [year, month] = monthStr.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1, 1);
  return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

interface CentroidPageProps {
  params: Promise<{ centroid_key: string }>;
  searchParams: Promise<{ month?: string }>;
}

export default async function CentroidPage({ params, searchParams }: CentroidPageProps) {
  const { centroid_key } = await params;
  const { month: selectedMonth } = await searchParams;
  const centroid = await getCentroidById(centroid_key);

  if (!centroid) {
    notFound();
  }

  // Fetch available months and configured tracks
  const availableMonths = await getAvailableMonthsForCentroid(centroid.id);
  const configuredTracks = await getConfiguredTracksForCentroid(centroid.id);

  // Determine current month (use selected or default to latest)
  const currentMonth = selectedMonth && availableMonths.includes(selectedMonth)
    ? selectedMonth
    : availableMonths[0] || null;

  // Fetch track data for the current month
  const monthTrackData = currentMonth
    ? await getTrackSummaryByCentroidAndMonth(centroid.id, currentMonth)
    : [];

  // Build a map of track -> titleCount for the current month
  const trackDataMap = new Map(monthTrackData.map(t => [t.track, t.titleCount]));

  // For each configured track, check if it has any historical data
  const tracksWithHistoricalData = new Set(
    availableMonths.length > 0
      ? configuredTracks.filter(track =>
          monthTrackData.some(t => t.track === track) ||
          // A track has historical data if it exists in any month's data
          true // We'd need another query for this, but for now assume all configured tracks have potential
        )
      : []
  );

  const sidebar = (
    <div className="space-y-6">
      {availableMonths.length > 0 && currentMonth && (
        <MonthPicker
          months={availableMonths}
          currentMonth={currentMonth}
          baseUrl={`/c/${centroid.id}`}
        />
      )}
    </div>
  );

  const theaterLabel = centroid.primary_theater
    ? (REGIONS as Record<string, string>)[centroid.primary_theater] || centroid.primary_theater
    : null;

  return (
    <DashboardLayout
      title={centroid.label}
      breadcrumb={theaterLabel ? (
        <Link
          href={`/region/${centroid.primary_theater}`}
          className="text-blue-400 hover:text-blue-300 text-sm"
        >
          &larr; {theaterLabel}
        </Link>
      ) : undefined}
      sidebar={sidebar}
      fullWidthContent={
        centroid.profile_json ? (
          <GeoBriefSection
            profile={centroid.profile_json}
            updatedAt={centroid.updated_at}
            centroidLabel={centroid.label}
          />
        ) : undefined
      }
    >
      <div className="space-y-8">
        <div>
          <h2 className="text-2xl font-bold mb-4">
            Strategic Tracks{currentMonth && ` \u2014 ${formatMonthLabel(currentMonth)}`}
          </h2>
          <p className="text-dashboard-text-muted mb-6">
            This is a monthly strategic snapshot of developments related to {centroid.label},
            organized by domain. Each card represents a distinct analytical track, summarizing
            how events and narratives evolved during the month within that sphere. Together,
            they form a cross-sectional view of the country&apos;s strategic activity for the
            selected period.
          </p>
        </div>

        {configuredTracks.length === 0 ? (
          <div className="text-center py-12 bg-dashboard-surface border border-dashboard-border rounded-lg">
            <p className="text-dashboard-text-muted">No tracks configured for this centroid</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {configuredTracks.map(track => {
              const titleCount = trackDataMap.get(track) || 0;
              const hasDataThisMonth = titleCount > 0;
              const hasHistoricalData = tracksWithHistoricalData.has(track);

              return (
                <TrackCard
                  key={track}
                  centroidId={centroid.id}
                  track={track}
                  latestMonth={currentMonth || undefined}
                  titleCount={titleCount}
                  disabled={!hasDataThisMonth}
                  hasHistoricalData={hasHistoricalData}
                />
              );
            })}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
