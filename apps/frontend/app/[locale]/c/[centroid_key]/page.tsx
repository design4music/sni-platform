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
  getCentroidMonthlySummary,
  getTopSignalsForCentroid,
  getStanceForCentroid,
  getCentroidDeviations,
  centroidHasPromotedForMonth,
  getCentroidMonthView,
  getActiveNarrativesForCentroid,
} from '@/lib/queries';
import CentroidHero from '@/components/CentroidHero';
import { getOutletLogoUrl } from '@/lib/logos';
import DeviationCard from '@/components/DeviationCard';
import StanceSidebar from './StanceSidebar';
import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import CentroidNarrativeSection from '@/components/narratives/CentroidNarrativeSection';
import { REGIONS, TRACK_LABELS, Track, getTrackLabel, getCentroidLabel, SignalType, SIGNAL_LABELS } from '@/lib/types';
import type { CentroidStanceScore } from '@/lib/queries';
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

  // Try to build a rich description from month view (shares cache with page render).
  let description: string;
  if (activeMonth) {
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

      // EN: "Germany in April 2026: 1,234 sources covering politics, economy,
      // security. Top themes: diplomacy, military, trade. Multilingual news
      // briefing." — lead with country+month (primary search intent), end
      // with value prop.
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
    } else {
      description = t('metaDescription', { label: centroidLabel });
    }
  } else {
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

  // Fetch track data, centroid summary, top signals, and new-view gate in parallel
  const [monthTrackData, centroidSummary, topSignals, stanceScores, deviationData, hasPromoted, activeNarratives] = await Promise.all([
    currentMonth ? getTrackSummaryByCentroidAndMonth(centroid.id, currentMonth) : Promise.resolve([]),
    currentMonth ? getCentroidMonthlySummary(centroid.id, currentMonth) : Promise.resolve(null),
    getTopSignalsForCentroid(centroid.id, currentMonth || undefined),
    getStanceForCentroid(centroid.id),
    getCentroidDeviations(centroid.id),
    currentMonth ? centroidHasPromotedForMonth(centroid.id, currentMonth) : Promise.resolve(false),
    currentMonth ? getActiveNarrativesForCentroid(centroid.id, currentMonth, locale) : Promise.resolve([]),
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

  const isFrozen = !!centroidSummary;

  const sidebar = (
    <div className={isFrozen ? "lg:sticky lg:top-24 space-y-6" : "space-y-6"}>
      {availableMonths.length > 0 && currentMonth && !centroidMonthView && (
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
      {activeNarratives.length > 0 && (
        <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
            Active Narratives
          </h3>
          <ul className="space-y-2">
            {activeNarratives.map(n => {
              const foreign = n.actor_centroid && n.actor_centroid !== centroid.id;
              const actorLabel = foreign
                ? getCentroidLabel(n.actor_centroid!, n.actor_centroid!, tCentroids)
                : null;
              return (
                <li key={n.id}>
                  <Link
                    href={`/narratives/${n.id}`}
                    className="flex items-start gap-2 text-sm text-dashboard-text hover:text-blue-400 transition group"
                  >
                    <span className="text-dashboard-text-muted tabular-nums text-[11px] pt-0.5 shrink-0 w-6 text-right">
                      {n.event_count}
                    </span>
                    <span className="flex-1 min-w-0 leading-snug">
                      {n.name}
                      {actorLabel && (
                        <span className="ml-1.5 inline-flex items-center px-1.5 py-0 rounded-sm text-[10px]
                                         bg-amber-500/10 border border-amber-500/30 text-amber-400 align-middle">
                          from {actorLabel}
                        </span>
                      )}
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      )}
      {deviationData && deviationData.deviations && deviationData.deviations.length > 0 && (
        <DeviationCard
          week={deviationData.week}
          deviations={deviationData.deviations}
        />
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

  // Enhanced top zone: hero calendar + 2x2 track cards, both spanning full width.
  // Only rendered when we have promoted events for this month.
  const enhancedTop = centroidMonthView ? (
    <div className="space-y-8">
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
                summaryText={heroTrack?.summary_text}
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
      sidebar={sidebar}
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
            {!centroidSummary && (
              <p className="text-dashboard-text-muted mb-6">
                {t('trackDescription', { label: getCentroidLabel(centroid.id, centroid.label, tCentroids) })}
              </p>
            )}
          </div>
        )}

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

        {!centroidMonthView && !isFrozen && (
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
        {/* Narrative section (deferred) */}
        <Suspense fallback={null}>
          <CentroidNarrativeSection centroidId={centroid.id} locale={locale} />
        </Suspense>
      </div>
    </DashboardLayout>
  );
}
