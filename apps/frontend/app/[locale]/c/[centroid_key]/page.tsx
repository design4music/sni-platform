import type { Metadata } from 'next';
import { getTranslations, getLocale } from 'next-intl/server';
import DashboardLayout from '@/components/DashboardLayout';
import TrackCard from '@/components/TrackCard';
import { getTrackIcon } from '@/components/TrackCard';
import GeoBriefSection from '@/components/GeoBriefSection';
import MonthNav from '@/components/MonthNav';
import CentroidMiniMapWrapper from '@/components/CentroidMiniMapWrapper';
import {
  getCentroidById,
  getAvailableMonthsForCentroid,
  getTrackSummaryByCentroidAndMonth,
  getConfiguredTracksForCentroid,
  getCentroidMonthlySummary,
  getTopSignalsForCentroid,
  getStanceForCentroid,
} from '@/lib/queries';
import { getOutletLogoUrl } from '@/lib/logos';
import StanceSidebar from './StanceSidebar';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { REGIONS, TRACK_LABELS, Track, getTrackLabel, getCentroidLabel, SignalType, SIGNAL_LABELS } from '@/lib/types';
import type { CentroidStanceScore } from '@/lib/queries';

export const dynamic = 'force-dynamic';

interface CentroidPageProps {
  params: Promise<{ centroid_key: string }>;
  searchParams: Promise<{ month?: string }>;
}

export async function generateMetadata({ params }: CentroidPageProps): Promise<Metadata> {
  const { centroid_key } = await params;
  const t = await getTranslations('centroid');
  const tCentroidsMeta = await getTranslations('centroids');
  const centroid = await getCentroidById(centroid_key);
  if (!centroid) return { title: t('notFound') };
  const centroidLabel = getCentroidLabel(centroid.id, centroid.label, tCentroidsMeta);
  return {
    title: centroidLabel,
    description: t('metaDescription', { label: centroidLabel }),
    alternates: { canonical: `/c/${centroid_key}` },
  };
}

function formatMonthLabel(monthStr: string, loc?: string): string {
  const [year, month] = monthStr.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1, 1);
  return date.toLocaleDateString(loc === 'de' ? 'de-DE' : 'en-US', { month: 'long', year: 'numeric' });
}

export default async function CentroidPage({ params, searchParams }: CentroidPageProps) {
  const { centroid_key } = await params;
  const { month: selectedMonth } = await searchParams;
  const t = await getTranslations('centroid');
  const tCentroids = await getTranslations('centroids');
  const tTracks = await getTranslations('tracks');
  const locale = await getLocale();
  const centroid = await getCentroidById(centroid_key, locale);

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

  // Fetch track data, centroid summary, and top signals for the current month
  const [monthTrackData, centroidSummary, topSignals, stanceScores] = await Promise.all([
    currentMonth ? getTrackSummaryByCentroidAndMonth(centroid.id, currentMonth) : Promise.resolve([]),
    currentMonth ? getCentroidMonthlySummary(centroid.id, currentMonth) : Promise.resolve(null),
    getTopSignalsForCentroid(centroid.id, currentMonth || undefined),
    getStanceForCentroid(centroid.id),
  ]);

  // Build maps of track -> titleCount and track -> lastActive for the current month
  const trackDataMap = new Map(monthTrackData.map(t => [t.track, t.titleCount]));
  const trackLastActiveMap = new Map(monthTrackData.map(t => [t.track, t.lastActive]));

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
            {getCentroidLabel(centroid.id, centroid.label, tCentroids)}
          </h3>
          <p className="text-sm text-dashboard-text-muted mb-4">
            {t('strategicTracks')}
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
                    {getTrackLabel(t as Track, tTracks)}
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
                    {getTrackLabel(t as Track, tTracks)}
                  </span>
                  <span className="text-xs tabular-nums">0</span>
                </div>
              );
            })}
          </nav>
        </div>
      )}
      {topSignals.length > 0 && (
        <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
            {t('topSignals')}
          </h3>
          <div className="flex flex-wrap gap-1.5">
            {topSignals.map(s => {
              const typeLabel = s.signal_type.replace(/s$/, '').replace(/_/g, ' ');
              return (
                <Link
                  key={`${s.signal_type}-${s.value}`}
                  href={`/signals/${s.signal_type}/${encodeURIComponent(s.value)}`}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 hover:bg-blue-500/20 hover:border-blue-500/40 transition text-[11px]"
                >
                  <span className="text-blue-400/70">{typeLabel}:</span>
                  <span className="text-dashboard-text truncate max-w-[100px]">{s.value}</span>
                  <span className="text-dashboard-text-muted tabular-nums">{s.event_count}</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}
      {stanceScores.length > 0 && (
        <StanceSidebar
          scores={stanceScores.map(s => ({
            feed_name: s.feed_name,
            source_domain: s.source_domain,
            score: s.score,
            logoUrl: s.source_domain ? getOutletLogoUrl(s.source_domain, 16) : null,
          }))}
          month={stanceScores[0]?.month || ''}
          title={t('publisherSentiment')}
        />
      )}
    </div>
  );

  const theaterLabel = centroid.primary_theater
    ? (REGIONS as Record<string, string>)[centroid.primary_theater] || centroid.primary_theater
    : null;

  return (
    <DashboardLayout
      title={getCentroidLabel(centroid.id, centroid.label, tCentroids)}
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
            centroidLabel={getCentroidLabel(centroid.id, centroid.label, tCentroids)}
            miniMap={centroid.iso_codes && centroid.iso_codes.length > 0
              ? <CentroidMiniMapWrapper isoCodes={centroid.iso_codes} />
              : undefined}
          />
        ) : undefined
      }
    >
      <div className="space-y-8">
        {/* Show mini-map standalone if no Background Brief exists */}
        {!centroid.profile_json && centroid.iso_codes && centroid.iso_codes.length > 0 && (
          <div className="mb-2">
            <CentroidMiniMapWrapper isoCodes={centroid.iso_codes} />
          </div>
        )}
        <div>
          <h2 className="text-2xl font-bold mb-4">
            {t('strategicTracks')}{currentMonth && ` \u2014 ${formatMonthLabel(currentMonth, locale)}`}
          </h2>
          {!centroidSummary && (
            <p className="text-dashboard-text-muted mb-6">
              {t('trackDescription', { label: getCentroidLabel(centroid.id, centroid.label, tCentroids) })}
            </p>
          )}
        </div>

        {centroidSummary && (
          <div className="mb-8">
            <h2 className="text-xl font-bold mb-3">{t('monthlyOverview')}</h2>
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
              {t('summaryStats', { events: centroidSummary.total_events, tracks: centroidSummary.track_count })}
            </p>
          </div>
        )}

        {!isFrozen && (
          configuredTracks.length === 0 ? (
            <div className="text-center py-12 bg-dashboard-surface border border-dashboard-border rounded-lg">
              <p className="text-dashboard-text-muted">{t('noTracks')}</p>
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
                    lastActive={trackLastActiveMap.get(track) || undefined}
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
