import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import TrackCard from '@/components/TrackCard';
import { getTrackIcon } from '@/components/TrackCard';
import GeoBriefSection from '@/components/GeoBriefSection';
import MonthNav from '@/components/MonthNav';
import {
  getCentroidById,
  getAvailableMonthsForCentroid,
  getTrackSummaryByCentroidAndMonth,
  getConfiguredTracksForCentroid,
  getCentroidMonthlySummary,
} from '@/lib/queries';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { REGIONS, TRACK_LABELS, Track, getTrackLabel } from '@/lib/types';

export const dynamic = 'force-dynamic';

interface CentroidPageProps {
  params: Promise<{ centroid_key: string }>;
  searchParams: Promise<{ month?: string }>;
}

export async function generateMetadata({ params }: CentroidPageProps): Promise<Metadata> {
  const { centroid_key } = await params;
  const centroid = await getCentroidById(centroid_key);
  if (!centroid) return { title: 'Country Not Found' };
  return {
    title: centroid.label,
    description: `${centroid.label} news briefing: strategic tracks, topic summaries, and multilingual source analysis from international media.`,
    alternates: { canonical: `/c/${centroid_key}` },
  };
}

function formatMonthLabel(monthStr: string): string {
  const [year, month] = monthStr.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1, 1);
  return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
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

  // Fetch track data and centroid summary for the current month
  const [monthTrackData, centroidSummary] = await Promise.all([
    currentMonth ? getTrackSummaryByCentroidAndMonth(centroid.id, currentMonth) : Promise.resolve([]),
    currentMonth ? getCentroidMonthlySummary(centroid.id, currentMonth) : Promise.resolve(null),
  ]);

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

  const isFrozen = !!centroidSummary;

  const sidebar = (
    <div className={isFrozen ? "lg:sticky lg:top-24 space-y-6" : "space-y-6"}>
      {availableMonths.length > 0 && currentMonth && (
        <MonthNav
          months={availableMonths}
          currentMonth={currentMonth}
          baseUrl={`/c/${centroid.id}`}
        />
      )}
      {isFrozen && configuredTracks.length > 0 && (
        <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          <h3 className="text-xl font-bold mb-1 text-dashboard-text">
            {centroid.label}
          </h3>
          <p className="text-sm text-dashboard-text-muted mb-4">
            Strategic Tracks
          </p>
          <nav className="space-y-1">
            {configuredTracks.map(t => {
              const titleCount = trackDataMap.get(t) || 0;
              const hasData = titleCount > 0;
              return hasData ? (
                <Link
                  key={t}
                  href={`/c/${centroid.id}/t/${t}?month=${currentMonth}`}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg bg-dashboard-border/30 hover:bg-dashboard-border
                             border border-transparent hover:border-dashboard-border
                             transition-all duration-150"
                >
                  <span className="text-dashboard-text-muted">{getTrackIcon(t)}</span>
                  <span className="text-base font-medium text-dashboard-text hover:text-white transition flex-1">
                    {getTrackLabel(t as Track)}
                  </span>
                  <span className="text-xs text-dashboard-text-muted tabular-nums">{titleCount}</span>
                </Link>
              ) : (
                <div
                  key={t}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg opacity-40"
                >
                  <span>{getTrackIcon(t)}</span>
                  <span className="text-base font-medium flex-1">
                    {getTrackLabel(t as Track)}
                  </span>
                  <span className="text-xs tabular-nums">0</span>
                </div>
              );
            })}
          </nav>
        </div>
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
          {!centroidSummary && (
            <p className="text-dashboard-text-muted mb-6">
              This is a monthly strategic snapshot of developments related to {centroid.label},
              organized by domain. Each card represents a distinct analytical track, summarizing
              how events and narratives evolved during the month within that sphere. Together,
              they form a cross-sectional view of the country&apos;s strategic activity for the
              selected period.
            </p>
          )}
        </div>

        {centroidSummary && (
          <div className="mb-8">
            <h2 className="text-xl font-bold mb-3">Monthly Overview</h2>
            <div className="text-lg leading-relaxed space-y-4">
              {centroidSummary.summary_text.split('\n\n').flatMap((paragraph, idx) => {
                const trimmed = paragraph.trim();
                if (!trimmed) return [];
                if (trimmed.startsWith('### ')) {
                  const newlinePos = trimmed.indexOf('\n');
                  const heading = newlinePos === -1 ? trimmed.slice(4) : trimmed.slice(4, newlinePos);
                  const body = newlinePos === -1 ? null : trimmed.slice(newlinePos + 1).trim();
                  const elements = [
                    <h3 key={`h-${idx}`} className="text-base font-semibold uppercase tracking-wide text-dashboard-text-muted mt-6 first:mt-0">
                      {heading}
                    </h3>
                  ];
                  if (body) {
                    elements.push(<p key={`p-${idx}`}>{body}</p>);
                  }
                  return elements;
                }
                return [<p key={idx}>{trimmed}</p>];
              })}
            </div>
            <p className="text-sm text-dashboard-text-muted mt-3">
              Based on {centroidSummary.total_events} topics across {centroidSummary.track_count} tracks
            </p>
          </div>
        )}

        {!isFrozen && (
          configuredTracks.length === 0 ? (
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
          )
        )}
      </div>
    </DashboardLayout>
  );
}
