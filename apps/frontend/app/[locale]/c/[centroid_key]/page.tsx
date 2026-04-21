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
  getTracksByCentroid,
  getTopSignalsForCentroid,
  getCentroidDeviationsForMonth,
  getCentroidMediaLens,
  centroidHasPromotedForMonth,
  getCentroidMonthView,
  getActiveNarrativesForCentroid,
  getCentroidSummary,
} from '@/lib/queries';
import CentroidHero from '@/components/CentroidHero';
import WeeklyDeviationCard from '@/components/WeeklyDeviationCard';
import MediaLensSection from '@/components/MediaLensSection';
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import CentroidNarrativeSection from '@/components/narratives/CentroidNarrativeSection';
import ActiveNarrativesSidebar from '@/components/ActiveNarrativesSidebar';
import { REGIONS, TRACK_LABELS, Track, getTrackLabel, getCentroidLabel, SignalType, SIGNAL_LABELS } from '@/lib/types';
import { buildPageMetadata, formatMonthLabel as formatMonthLabelSeo, humanizeEnum, formatCount, joinList, truncateDescription, breadcrumbList, type Locale as SeoLocale } from '@/lib/seo';
import JsonLd from '@/components/JsonLd';

// Canonical URL (no month param) is cacheable; month variants re-render
// dynamically because they read searchParams. Matches D-037 policy.
export const revalidate = 1800;

interface CentroidPageProps {
  params: Promise<{ centroid_key: string }>;
  searchParams: Promise<{ month?: string }>;
}

export async function generateMetadata({ params, searchParams }: CentroidPageProps): Promise<Metadata> {
  const { centroid_key } = await params;
  const { month: requestedMonth } = await searchParams;
  const locale = (await getLocale()) as SeoLocale;
  const t = await getTranslations('centroid');
  const tCentroidsMeta = await getTranslations('centroids');
  const tTracks = await getTranslations('tracks');

  const centroid = await getCentroidById(centroid_key, locale);
  if (!centroid) return { title: t('notFound') };
  const centroidLabel = getCentroidLabel(centroid.id, centroid.label, tCentroidsMeta);

  // Pick active month: requested (if valid) or latest available.
  const availableMonths = await getAvailableMonthsForCentroid(centroid.id);
  const activeMonth = requestedMonth && availableMonths.includes(requestedMonth)
    ? requestedMonth
    : availableMonths[0] || null;

  // Description preference order:
  //   1. Editorial overview from centroid_summaries.overall (D-065) — these
  //      are LLM-curated period briefings, far richer than a stats dump.
  //   2. Mechanical fallback from getCentroidMonthView (counts + themes).
  //   3. Static i18n template (no active month).
  let description: string | undefined;
  if (activeMonth) {
    const summary = await getCentroidSummary(centroid.id, activeMonth, locale);
    const overall = summary?.overall?.trim();
    if (overall) description = truncateDescription(overall);
  }

  if (!description && activeMonth) {
    const view = await getCentroidMonthView(centroid.id, activeMonth, locale);
    const monthLabel = formatMonthLabelSeo(activeMonth, locale);

    if (view && view.tracks.length > 0) {
      const totalSources = view.activity_stripe.reduce((s, d) => s + d.total_sources, 0);
      const trackNames = view.tracks
        .filter(t => t.title_count > 0)
        .slice(0, 3)
        .map(t => getTrackLabel(t.track as Track, tTracks).toLowerCase());
      const themeCounts = new Map<string, number>();
      for (const tr of view.tracks) {
        for (const chip of tr.theme_chips || []) {
          const key = chip.sector;
          themeCounts.set(key, (themeCounts.get(key) || 0) + chip.weight);
        }
      }
      const topThemes = [...themeCounts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([sector]) => humanizeEnum(sector));

      if (locale === 'de') {
        const parts: string[] = [
          `${centroidLabel} im ${monthLabel}: ${formatCount(totalSources, 'de')} Quellen zu ${joinList(trackNames, 'de')}.`,
        ];
        if (topThemes.length) parts.push(`Schwerpunkte: ${joinList(topThemes, 'de')}.`);
        parts.push('Mehrsprachiges Nachrichten-Briefing.');
        description = truncateDescription(parts.join(' '));
      } else {
        const parts: string[] = [
          `${centroidLabel} in ${monthLabel}: ${formatCount(totalSources)} sources covering ${joinList(trackNames)}.`,
        ];
        if (topThemes.length) parts.push(`Top themes: ${joinList(topThemes)}.`);
        parts.push('Multilingual news briefing.');
        description = truncateDescription(parts.join(' '));
      }
    }
  }

  if (!description) {
    description = t('metaDescription', { label: centroidLabel });
  }

  // EN: "Germany news: April 2026 briefing" — country first for keyword match,
  // month as freshness signal.
  const title = activeMonth
    ? (locale === 'de'
        ? `${centroidLabel} Nachrichten: ${formatMonthLabelSeo(activeMonth, 'de')} Briefing`
        : `${centroidLabel} news: ${formatMonthLabelSeo(activeMonth, 'en')} briefing`)
    : (locale === 'de' ? `${centroidLabel} — Nachrichten-Briefing` : `${centroidLabel} news briefing`);

  return buildPageMetadata({
    title,
    description,
    path: `/c/${centroid_key}`,
    locale,
  });
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

  // Fetch available months
  const availableMonths = await getAvailableMonthsForCentroid(centroid.id);

  // Determine current month (use selected or default to latest)
  const currentMonth = selectedMonth && availableMonths.includes(selectedMonth)
    ? selectedMonth
    : availableMonths[0] || null;

  // Get tracks that exist for the current month (month-aware: Jan=6, March=4)
  const configuredTracks = await getTracksByCentroid(centroid.id, currentMonth || undefined);

  // Fetch track data, top signals, and new-view gate in parallel
  const [monthTrackData, topSignals, weeklyDeviations, mediaLens, hasPromoted, activeNarratives, periodSummary] = await Promise.all([
    currentMonth ? getTrackSummaryByCentroidAndMonth(centroid.id, currentMonth) : Promise.resolve([]),
    getTopSignalsForCentroid(centroid.id, currentMonth || undefined),
    currentMonth ? getCentroidDeviationsForMonth(centroid.id, currentMonth) : Promise.resolve([]),
    currentMonth
      ? getCentroidMediaLens(centroid.id, currentMonth)
      : Promise.resolve({ local_self: null, local_abroad: [], foreign: [] }),
    currentMonth ? centroidHasPromotedForMonth(centroid.id, currentMonth) : Promise.resolve(false),
    currentMonth ? getActiveNarrativesForCentroid(centroid.id, currentMonth, locale) : Promise.resolve([]),
    getCentroidSummary(centroid.id, currentMonth, locale),
  ]);

  // New hero view data: only loaded when the month has promoted events.
  const centroidMonthView = hasPromoted && currentMonth
    ? await getCentroidMonthView(centroid.id, currentMonth, locale)
    : null;

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

  // Legacy sidebar: only when the enhanced CentroidHero view is not
  // available for this centroid+month. Media-Lens/Deviation/Narrative
  // widgets have moved into in-page section pairs below the hero.
  const legacyLayout = !centroidMonthView;

  const legacySidebar = legacyLayout ? (
    <div className="lg:sticky lg:top-24 space-y-6">
      {availableMonths.length > 0 && currentMonth && (
        <MonthNav
          months={availableMonths}
          currentMonth={currentMonth}
          baseUrl={`/c/${centroid.id}`}
        />
      )}
      {configuredTracks.length > 0 && (
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
    </div>
  ) : undefined;

  const theaterLabel = centroid.primary_theater
    ? (REGIONS as Record<string, string>)[centroid.primary_theater] || centroid.primary_theater
    : null;

  // Map summary track payloads by track key for lookup below.
  const summaryByTrack: Record<string, string | null> = {
    geo_economy: periodSummary?.economy?.state || null,
    geo_politics: periodSummary?.politics?.state || null,
    geo_security: periodSummary?.security?.state || null,
    geo_society: periodSummary?.society?.state || null,
  };

  // Enhanced top zone: briefing + hero calendar + 2x2 track cards, all spanning full width.
  // Only rendered when we have promoted events for this month.
  const enhancedTop = centroidMonthView ? (
    <div className="space-y-8">
      {/* Tier 0 "Country briefing" — one paragraph setting the period's dominant tension */}
      {periodSummary && periodSummary.overall && (
        <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-5">
          <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted mb-2">
            {locale === 'de' ? 'Überblick' : 'Overview'}
            {periodSummary.tier === 3 && (
              <span className="ml-2 text-amber-400/70">
                {locale === 'de' ? '(wenig Berichterstattung)' : '(limited coverage)'}
              </span>
            )}
          </div>
          <p className="text-[15px] leading-relaxed text-dashboard-text">
            {periodSummary.overall}
          </p>
        </div>
      )}

      <CentroidHero
        view={centroidMonthView}
        centroidLabel={getCentroidLabel(centroid.id, centroid.label, tCentroids)}
        centroidKey={centroid.id}
        activeMonth={currentMonth || ''}
      />
      {configuredTracks.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {configuredTracks.map(track => {
            const titleCount = trackDataMap.get(track) || 0;
            const hasDataThisMonth = titleCount > 0;
            const hasHistoricalData = tracksWithHistoricalData.has(track);
            const heroTrack = centroidMonthView.tracks.find(t => t.track === track);
            const trackState = summaryByTrack[track] || null;
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
                topEvents={heroTrack?.top_events}
                themeChips={heroTrack?.theme_chips}
                summaryText={trackState}
                calendarHref={`/c/${centroid.id}/t/${track}?month=${currentMonth}`}
              />
            );
          })}
        </div>
      )}
    </div>
  ) : undefined;

  const crumbs: Array<{ name: string; path: string }> = [];
  if (theaterLabel) {
    crumbs.push({ name: theaterLabel, path: `/region/${centroid.primary_theater}` });
  }
  crumbs.push({
    name: getCentroidLabel(centroid.id, centroid.label, tCentroids),
    path: `/c/${centroid.id}`,
  });

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
      sidebar={legacySidebar}
      topFullWidthContent={enhancedTop}
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
      <JsonLd data={breadcrumbList(crumbs)} />
      <div className="space-y-8">
        {/* Show mini-map standalone if no Background Brief exists */}
        {!centroid.profile_json && centroid.iso_codes && centroid.iso_codes.length > 0 && (
          <div className="mb-2">
            <CentroidMiniMapWrapper isoCodes={centroid.iso_codes} />
          </div>
        )}
        {/* Legacy header only when enhanced hero is NOT active */}
        {!centroidMonthView && (
          <div>
            <h2 className="text-2xl font-bold mb-4">
              {t('strategicTracks')}{currentMonth && ` \u2014 ${formatMonthLabel(currentMonth, locale)}`}
            </h2>
            <p className="text-dashboard-text-muted mb-6">
              {t('trackDescription', { label: getCentroidLabel(centroid.id, centroid.label, tCentroids) })}
            </p>
          </div>
        )}

        {!centroidMonthView && (
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
        {/* Section pair 1: Media Lens (main) + Unusual Activity (sidebar).
            min-w-0 on both grid cells so long content (e.g., "Media-stance"
            headings, outlet pill rows) can shrink below intrinsic width
            instead of stretching the page horizontally on narrow viewports. */}
        {currentMonth && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="min-w-0 lg:col-span-2">
              <MediaLensSection
                centroidId={centroid.id}
                centroidLabel={getCentroidLabel(centroid.id, centroid.label, tCentroids)}
                initialMonth={currentMonth}
                initialLens={mediaLens}
              />
            </div>
            <aside className="min-w-0">
              <WeeklyDeviationCard
                centroidId={centroid.id}
                initialMonth={currentMonth}
                initialWeeks={weeklyDeviations}
              />
            </aside>
          </div>
        )}

        {/* Section pair 2: Strategic Narratives (main) + Active Narratives (sidebar) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="min-w-0 lg:col-span-2">
            <Suspense fallback={null}>
              <CentroidNarrativeSection centroidId={centroid.id} locale={locale} />
            </Suspense>
          </div>
          <aside className="min-w-0">
            <ActiveNarrativesSidebar centroidId={centroid.id} narratives={activeNarratives} />
          </aside>
        </div>
      </div>
    </DashboardLayout>
  );
}
