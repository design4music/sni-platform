import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import {
  CalendarHero,
  CalendarDayPanel,
  CalendarScopeCard,
} from '@/components/CalendarView';
import type { CalendarMonthView } from '@/lib/types';
import { getTrackIcon } from '@/components/TrackCard';
import {
  getCalendarMonthView,
  getCentroidById,
  getCentroidSummary,
  getCTMMonths,
  getTracksByCentroid,
} from '@/lib/queries';
import type { CentroidSummary } from '@/lib/queries';

// Map a CTM track key to the centroid_summaries column for that track.
// Returns null for tracks not covered by D-065 (humanitarian/information/energy).
function trackToSummaryKey(track: string): keyof Pick<CentroidSummary, 'economy' | 'politics' | 'security' | 'society'> | null {
  switch (track) {
    case 'geo_economy': return 'economy';
    case 'geo_politics': return 'politics';
    case 'geo_security': return 'security';
    case 'geo_society': return 'society';
    default: return null;
  }
}
import { getTrackLabel, getCentroidLabel, Track } from '@/lib/types';
import { setRequestLocale, getTranslations, getLocale } from 'next-intl/server';
import { buildPageMetadata, formatMonthLabel as formatMonthLabelSeo, humanizeEnum, formatCount, joinList, truncateDescription, breadcrumbList, type Locale as SeoLocale } from '@/lib/seo';
import JsonLd from '@/components/JsonLd';

// Canonical URL (no month param) is cacheable; month variants re-render
// dynamically because they read searchParams. Matches D-037 policy.
export const revalidate = 1800;

// Picks the most active day when one isn't explicitly requested.
function pickDefaultDay(view: CalendarMonthView, explicit: string | null): string | null {
  if (explicit && view.days.some(d => d.date === explicit)) return explicit;
  if (view.days.length === 0) return null;
  return view.days.reduce((best, d) => (d.total_sources > best.total_sources ? d : best)).date;
}

interface TrackPageProps {
  params: Promise<{ locale: string; centroid_key: string; track_key: string }>;
  searchParams: Promise<{ month?: string; day?: string }>;
}

export async function generateMetadata({ params, searchParams }: TrackPageProps): Promise<Metadata> {
  const { centroid_key, track_key } = await params;
  const { month: requestedMonth } = await searchParams;
  const locale = (await getLocale()) as SeoLocale;
  const tTracks = await getTranslations('tracks');
  const tCentroids = await getTranslations('centroids');
  const t = await getTranslations('track');

  const centroid = await getCentroidById(centroid_key, locale);
  if (!centroid) return { title: t('notFound') };
  const trackLabel = getTrackLabel(track_key as Track, tTracks);
  const centroidLabel = getCentroidLabel(centroid.id, centroid.label, tCentroids);
  const trackLower = trackLabel.toLowerCase();

  const months = await getCTMMonths(centroid_key, track_key);
  const activeMonth = requestedMonth && months.includes(requestedMonth)
    ? requestedMonth
    : months[0] || null;

  if (!activeMonth) {
    return buildPageMetadata({
      title: locale === 'de'
        ? `${centroidLabel} ${trackLower} Nachrichten`
        : `${centroidLabel} ${trackLower} news`,
      description: locale === 'de'
        ? `${centroidLabel} ${trackLower}-Nachrichten — Tages-Timeline und Quellenanalyse.`
        : `${centroidLabel} ${trackLower} news — daily timeline and source analysis.`,
      path: `/c/${centroid_key}/t/${track_key}`,
      locale,
    });
  }

  const monthLabel = formatMonthLabelSeo(activeMonth, locale);
  // EN: "USA security: April 2026 news"
  // DE: "USA Sicherheit: April 2026 Nachrichten"
  const title = locale === 'de'
    ? `${centroidLabel} ${trackLower}: ${monthLabel} Nachrichten`
    : `${centroidLabel} ${trackLower}: ${monthLabel} news`;

  // Description preference order:
  //   1. Editorial per-track state from centroid_summaries (D-065) — only
  //      exists for the four canonical tracks (economy/politics/security/society).
  //   2. Mechanical fallback from getCalendarMonthView (counts + themes).
  let description: string | undefined;
  const summaryKey = trackToSummaryKey(track_key);
  if (summaryKey) {
    const summary = await getCentroidSummary(centroid.id, activeMonth, locale);
    const trackPayload = summary?.[summaryKey];
    const state = trackPayload?.state?.trim();
    if (state) description = truncateDescription(state);
  }

  if (!description) {
    const view = await getCalendarMonthView(centroid_key, track_key, activeMonth, locale);
    if (view) {
      const activeDays = view.days.length;
      const clusterCount = view.days.reduce((s, d) => s + d.cluster_count, 0);
      const themes = (view.theme_chips || []).slice(0, 3).map(c => humanizeEnum(c.sector));
      if (locale === 'de') {
        const parts = [
          `Tagesgenaue ${trackLower}-Nachrichten für ${centroidLabel}, ${monthLabel}: ${formatCount(clusterCount, 'de')} Events an ${activeDays} Tagen, ${formatCount(view.scope.total_sources, 'de')} Quellen.`,
        ];
        if (themes.length) parts.push(`Schwerpunkte: ${joinList(themes, 'de')}.`);
        description = truncateDescription(parts.join(' '));
      } else {
        const parts = [
          `Day-by-day ${trackLower} news for ${centroidLabel}, ${monthLabel}. ${formatCount(clusterCount)} events across ${activeDays} days, ${formatCount(view.scope.total_sources)} sources.`,
        ];
        if (themes.length) parts.push(`Themes: ${joinList(themes)}.`);
        description = truncateDescription(parts.join(' '));
      }
    } else {
      description = locale === 'de'
        ? `${centroidLabel} ${trackLower}-Nachrichten für ${monthLabel}.`
        : `${centroidLabel} ${trackLower} news for ${monthLabel}.`;
    }
  }

  return buildPageMetadata({
    title,
    description,
    path: `/c/${centroid_key}/t/${track_key}`,
    locale,
  });
}

export default async function TrackPage({ params, searchParams }: TrackPageProps) {
  const { locale, centroid_key, track_key } = await params;
  const { month } = await searchParams;
  setRequestLocale(locale);

  // Note: legacy ?day=YYYY-MM-DD is redirected at the edge in
  // middleware.ts (308 to /c/{c}/t/{t}/{date}), so we don't handle it
  // here. If it ever reaches this point (middleware bypass, future
  // refactor), falling through to the month view is a safe default.

  const centroid = await getCentroidById(centroid_key, locale);
  if (!centroid) notFound();

  const months = await getCTMMonths(centroid_key, track_key);
  if (months.length === 0) {
    return (
      <DashboardLayout>
        <div className="p-6 text-dashboard-text-muted">No coverage for this track yet.</div>
      </DashboardLayout>
    );
  }
  const activeMonth = month && months.includes(month) ? month : months[0];

  const view = await getCalendarMonthView(centroid_key, track_key, activeMonth, locale);
  if (!view) notFound();

  const tTracks = await getTranslations('tracks');
  const tCentroids = await getTranslations('centroids');
  const tNav = await getTranslations('nav');
  const trackLabel = getTrackLabel(track_key as Track, tTracks);
  const centroidLabel = getCentroidLabel(centroid.id, centroid.label, tCentroids);

  const idx = months.indexOf(activeMonth);
  const prevMonth = idx < months.length - 1 ? months[idx + 1] : null;
  const nextMonth = idx > 0 ? months[idx - 1] : null;

  const otherTracksList = await getTracksByCentroid(centroid_key);
  const otherTracks = otherTracksList.filter(t => t !== track_key);

  const defaultDay = pickDefaultDay(view, null);

  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm">
      <CalendarScopeCard scope={view.scope} trackLabel={trackLabel} />

      {otherTracks.length > 0 && (
        <div className="hidden lg:block bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          <h3 className="text-xl font-bold mb-1 text-dashboard-text">{centroidLabel}</h3>
          <p className="text-sm text-dashboard-text-muted mb-4">
            {tNav('otherStrategicTopics')}
          </p>
          <nav className="space-y-1">
            {otherTracksList.map(t => {
              const isCurrent = t === track_key;
              return isCurrent ? (
                <div
                  key={t}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg bg-blue-600/20 border border-blue-500/40 cursor-default"
                >
                  <span className="text-blue-400">{getTrackIcon(t)}</span>
                  <span className="text-base font-medium text-blue-400">
                    {getTrackLabel(t as Track, tTracks)}
                  </span>
                  <span className="text-xs text-blue-400/60">{tNav('current')}</span>
                </div>
              ) : (
                <Link
                  key={t}
                  href={`/c/${centroid.id}/t/${t}?month=${activeMonth}`}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg bg-dashboard-border/30 hover:bg-dashboard-border border border-transparent hover:border-dashboard-border transition-all duration-150"
                >
                  <span className="text-dashboard-text-muted">{getTrackIcon(t)}</span>
                  <span className="text-base font-medium text-dashboard-text hover:text-white transition">
                    {getTrackLabel(t as Track, tTracks)}
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>
      )}
    </div>
  );

  return (
    <DashboardLayout
      sidebar={sidebar}
      topFullWidthContent={
        <CalendarHero
          view={view}
          centroidLabel={centroidLabel}
          trackLabel={trackLabel}
          centroidKey={centroid_key}
          trackKey={track_key}
          activeMonth={activeMonth}
          prevMonth={prevMonth}
          nextMonth={nextMonth}
          defaultDay={defaultDay}
        />
      }
      centroidLabel={centroidLabel}
      centroidId={centroid.id}
      otherTracks={otherTracks}
      currentTrack={track_key}
      currentMonth={activeMonth}
      availableMonths={months}
    >
      <JsonLd
        data={breadcrumbList([
          { name: centroidLabel, path: `/c/${centroid.id}` },
          { name: trackLabel, path: `/c/${centroid.id}/t/${track_key}` },
        ])}
      />
      <CalendarDayPanel view={view} defaultDay={defaultDay} />
    </DashboardLayout>
  );
}
