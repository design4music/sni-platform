import type { Metadata } from 'next';
import { getTranslations, getLocale } from 'next-intl/server';
import DashboardLayout from '@/components/DashboardLayout';
import TrackCard from '@/components/TrackCard';
import {
  getCentroidById,
  getAvailableMonthsForCentroid,
  getTrackSummaryByCentroidAndMonth,
  getTracksByCentroid,
  getCentroidDeviationsForMonth,
  centroidHasPromotedForMonth,
  getCentroidMonthView,
  getActiveNarrativesForCentroid,
  getCentroidSummary,
  getCentroidMediaLens,
} from '@/lib/queries';
import CentroidActivityChart from '@/components/CentroidActivityChart';
import WeeklyDeviationCard from '@/components/WeeklyDeviationCard';
import MediaLensSection from '@/components/MediaLensSection';
import { Suspense } from 'react';
import { notFound, redirect } from 'next/navigation';
import Link from 'next/link';
import ActiveNarrativesSection from '@/components/ActiveNarrativesSection';
import SiblingOutlets from '@/components/SiblingOutlets';
import { REGIONS, Track, getTrackLabel, getCentroidLabel } from '@/lib/types';
import { buildPageMetadata, formatMonthLabel as formatMonthLabelSeo, humanizeEnum, formatCount, joinList, truncateDescription, breadcrumbList, type Locale as SeoLocale } from '@/lib/seo';
import JsonLd from '@/components/JsonLd';

// 12h cache. Page content (period summary, theme chips, top events,
// activity chart) updates with the daemon's clustering cycle but doesn't
// need to be fresher than every half-day. Static reference content
// (Background Brief + Strategic Narratives) lives at /c/[id]/about.
export const revalidate = 43200;

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
  //   1. Editorial overview from centroid_summaries.overall (D-065).
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

  // EN: "Germany news: April 2026 briefing" — country first for keyword
  // match, month as freshness signal.
  const title = activeMonth
    ? (locale === 'de'
        ? `${centroidLabel} Nachrichten: ${formatMonthLabelSeo(activeMonth, 'de')} Briefing`
        : `${centroidLabel} news: ${formatMonthLabelSeo(activeMonth, 'en')} briefing`)
    : (locale === 'de' ? `${centroidLabel} — Nachrichten-Briefing` : `${centroidLabel} news briefing`);

  // SEO: per-month canonical so each ?month=YYYY-MM is indexable as a
  // distinct page. Without month, canonical is the bare /c/{id} (latest).
  const explicitMonth = requestedMonth && availableMonths.includes(requestedMonth);
  const canonicalPath = explicitMonth
    ? `/c/${centroid_key}?month=${requestedMonth}`
    : `/c/${centroid_key}`;

  return buildPageMetadata({
    title,
    description,
    path: canonicalPath,
    locale,
  });
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

  const availableMonths = await getAvailableMonthsForCentroid(centroid.id);
  const currentMonth = selectedMonth && availableMonths.includes(selectedMonth)
    ? selectedMonth
    : availableMonths[0] || null;

  // Edge case: centroid has no months with promoted events at all. Send
  // visitors to the static /about page (which doesn't depend on monthly
  // data). Static reference is the meaningful surface for these centroids.
  if (!currentMonth) {
    redirect(`/c/${centroid.id}/about`);
  }

  // If a specific ?month= was requested but isn't in availableMonths
  // (filtered to months with promoted events), bounce to canonical.
  if (selectedMonth && selectedMonth !== currentMonth) {
    redirect(`/c/${centroid.id}`);
  }

  const configuredTracks = await getTracksByCentroid(centroid.id, currentMonth);

  // Parallel fetch of month-varying data.
  const [monthTrackData, weeklyDeviations, hasPromoted, activeNarratives, periodSummary, mediaLens] = await Promise.all([
    getTrackSummaryByCentroidAndMonth(centroid.id, currentMonth),
    getCentroidDeviationsForMonth(centroid.id, currentMonth),
    centroidHasPromotedForMonth(centroid.id, currentMonth),
    getActiveNarrativesForCentroid(centroid.id, currentMonth, locale),
    getCentroidSummary(centroid.id, currentMonth, locale),
    getCentroidMediaLens(centroid.id, currentMonth),
  ]);

  const centroidMonthView = hasPromoted
    ? await getCentroidMonthView(centroid.id, currentMonth, locale)
    : null;

  // Belt-and-suspenders: getAvailableMonthsForCentroid already filters to
  // months with promoted events, so this should never fire. If it does,
  // fall back to the static /about page rather than render a half-empty
  // monthly view.
  if (!centroidMonthView) {
    redirect(`/c/${centroid.id}/about`);
  }

  const trackDataMap = new Map(monthTrackData.map(td => [td.track, td.titleCount]));
  const trackLastActiveMap = new Map(monthTrackData.map(td => [td.track, td.lastActive]));

  const theaterLabel = centroid.primary_theater
    ? (REGIONS as Record<string, string>)[centroid.primary_theater] || centroid.primary_theater
    : null;
  const centroidLabel = getCentroidLabel(centroid.id, centroid.label, tCentroids);

  // Map summary track payloads by track key for lookup below.
  const summaryByTrack: Record<string, string | null> = {
    geo_economy: periodSummary?.economy?.state || null,
    geo_politics: periodSummary?.politics?.state || null,
    geo_security: periodSummary?.security?.state || null,
    geo_society: periodSummary?.society?.state || null,
  };

  // Top zone: header link to /about + briefing + activity chart + 2x2 track cards.
  const enhancedTop = (
    <div className="space-y-8">
      {/* "About {Country}" pointer to the static reference page */}
      <div className="flex items-center justify-end -mb-4">
        <Link
          href={`/c/${centroid.id}/about`}
          className="text-sm text-blue-400 hover:text-blue-300 transition"
        >
          {locale === 'de' ? `Über ${centroidLabel}` : `About ${centroidLabel}`} →
        </Link>
      </div>

      {/* Tier-0 country briefing — one paragraph setting the period's dominant tension */}
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

      {/* Topic-mix area chart — replaces the heavier per-day calendar hero. */}
      <CentroidActivityChart
        view={centroidMonthView}
        centroidKey={centroid.id}
        activeMonth={currentMonth}
      />

      {configuredTracks.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {configuredTracks.map(track => {
            const titleCount = trackDataMap.get(track) || 0;
            const hasDataThisMonth = titleCount > 0;
            const heroTrack = centroidMonthView.tracks.find(td => td.track === track);
            const trackState = summaryByTrack[track] || null;
            return (
              <TrackCard
                key={track}
                centroidId={centroid.id}
                track={track}
                latestMonth={currentMonth}
                titleCount={titleCount}
                disabled={!hasDataThisMonth}
                hasHistoricalData={true}
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
  );

  const crumbs: Array<{ name: string; path: string }> = [];
  if (theaterLabel) {
    crumbs.push({ name: theaterLabel, path: `/region/${centroid.primary_theater}` });
  }
  crumbs.push({ name: centroidLabel, path: `/c/${centroid.id}` });

  return (
    <DashboardLayout
      title={centroidLabel}
      breadcrumb={theaterLabel ? (
        <Link
          href={`/region/${centroid.primary_theater}`}
          className="text-blue-400 hover:text-blue-300 text-sm"
        >
          &larr; {theaterLabel}
        </Link>
      ) : undefined}
      topFullWidthContent={enhancedTop}
    >
      <JsonLd data={breadcrumbList(crumbs)} />
      <div className="space-y-8">
        {/* Active Narratives (main, varies per month) +
            Sidebar (Unusual Activity + Media Lens + Sources from Country).
            Strategic Narratives + Background Brief moved to /c/[id]/about. */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="min-w-0 lg:col-span-2 space-y-8">
            <ActiveNarrativesSection centroidId={centroid.id} narratives={activeNarratives} />
          </div>
          <aside className="min-w-0 space-y-6">
            <WeeklyDeviationCard
              centroidId={centroid.id}
              initialMonth={currentMonth}
              initialWeeks={weeklyDeviations}
            />
            {mediaLens.length > 0 && (
              <MediaLensSection
                rows={mediaLens}
                centroidLabel={centroidLabel}
                month={currentMonth}
                locale={locale}
              />
            )}
            {centroid.iso_codes && centroid.iso_codes.length === 1 && (
              <Suspense fallback={null}>
                <SiblingOutlets countryCode={centroid.iso_codes[0]} />
              </Suspense>
            )}
          </aside>
        </div>
      </div>
    </DashboardLayout>
  );
}
