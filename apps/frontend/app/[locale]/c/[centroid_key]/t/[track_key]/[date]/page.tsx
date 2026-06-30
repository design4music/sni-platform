import { notFound } from 'next/navigation';
import type { Metadata } from 'next';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import {
  CalendarHero,
  CalendarDayPanel,
  CalendarScopeCard,
} from '@/components/CalendarView';
import { getTrackIcon } from '@/components/TrackCard';
import {
  getCalendarMonthView,
  getCentroidById,
  getCTMMonths,
  getTracksByCentroid,
} from '@/lib/queries';
import { getTrackLabel, getCentroidLabel, Track } from '@/lib/types';
import { setRequestLocale, getTranslations, getLocale } from 'next-intl/server';
import {
  buildPageMetadata,
  formatDayLabel,
  isValidDateSlug,
  truncateDescription,
  breadcrumbList,
  newsArticleJsonLd,
  humanizeEnum,
  formatCount,
  joinList,
  type Locale as SeoLocale,
} from '@/lib/seo';
import JsonLd from '@/components/JsonLd';

// Day-canonical page. Two modes:
//   - Brief present: indexable, NewsArticle JSON-LD, og:type=article
//   - Brief absent but day has promoted events: renders for user nav
//     (hero calendar stripe links here) but noindex + no article
//     schema. Keeps internal navigation working without flooding
//     Google with thin pages.
//   - Day has zero promoted events (or invalid date): 404.
// Day-canonical URLs have a huge param space (75 centroids × 4 tracks ×
// ~150 days × 2 locales). On Render's 512MB instance, ISR caching this
// route was a major OOM contributor under bot crawl. force-dynamic +
// the query-level lib/cache.ts memoization keeps real-user perf fine.
export const dynamic = 'force-dynamic';

interface DayPageProps {
  params: Promise<{ locale: string; centroid_key: string; track_key: string; date: string }>;
}

export async function generateMetadata({ params }: DayPageProps): Promise<Metadata> {
  const { centroid_key, track_key, date } = await params;
  const locale = (await getLocale()) as SeoLocale;

  if (!isValidDateSlug(date)) return { title: 'Not found', robots: { index: false } };
  const month = date.slice(0, 7);

  const centroid = await getCentroidById(centroid_key, locale);
  if (!centroid) return { title: 'Not found', robots: { index: false } };

  const view = await getCalendarMonthView(centroid_key, track_key, month, locale);
  const day = view?.days.find(d => d.date === date);
  if (!view || !day) {
    // No promoted events for this day → truly empty, not indexable.
    return { title: 'Not found', robots: { index: false } };
  }

  const tTracks = await getTranslations('tracks');
  const tCentroids = await getTranslations('centroids');
  const trackLabel = getTrackLabel(track_key as Track, tTracks);
  const centroidLabel = getCentroidLabel(centroid.id, centroid.label, tCentroids);
  const trackLower = trackLabel.toLowerCase();
  const dayLabel = formatDayLabel(date, locale);

  const title = locale === 'de'
    ? `${centroidLabel} ${trackLower}: ${dayLabel} Nachrichten`
    : `${centroidLabel} ${trackLower}: ${dayLabel} news`;

  // Brief present → indexable article with the brief as description.
  // Brief absent → mechanical description (events + top themes) and noindex.
  if (day.daily_brief) {
    return buildPageMetadata({
      title,
      description: truncateDescription(day.daily_brief),
      path: `/c/${centroid_key}/t/${track_key}/${date}`,
      locale,
      ogType: 'article',
      publishedTime: `${date}T00:00:00Z`,
    });
  }

  const stripe = view.activity_stripe.find(s => s.date === date);
  const themes = (stripe?.themes || []).slice(0, 3).map(t => humanizeEnum(t.sector));
  const description = truncateDescription(
    locale === 'de'
      ? [
          `${formatCount(day.cluster_count, 'de')} Events, ${formatCount(day.total_sources, 'de')} Quellen zu ${centroidLabel} ${trackLower} am ${dayLabel}.`,
          themes.length ? `Schwerpunkte: ${joinList(themes, 'de')}.` : '',
        ].filter(Boolean).join(' ')
      : [
          `${formatCount(day.cluster_count)} events, ${formatCount(day.total_sources)} sources on ${centroidLabel} ${trackLower} for ${dayLabel}.`,
          themes.length ? `Themes: ${joinList(themes)}.` : '',
        ].filter(Boolean).join(' ')
  );

  return {
    ...buildPageMetadata({
      title,
      description,
      path: `/c/${centroid_key}/t/${track_key}/${date}`,
      locale,
    }),
    robots: { index: false, follow: true },
  };
}

export default async function DayPage({ params }: DayPageProps) {
  const { locale, centroid_key, track_key, date } = await params;
  setRequestLocale(locale);

  if (!isValidDateSlug(date)) notFound();
  const activeMonth = date.slice(0, 7);

  const centroid = await getCentroidById(centroid_key, locale);
  if (!centroid) notFound();

  const months = await getCTMMonths(centroid_key, track_key);
  if (!months.includes(activeMonth)) notFound();

  const view = await getCalendarMonthView(centroid_key, track_key, activeMonth, locale);
  if (!view) notFound();

  const day = view.days.find(d => d.date === date);
  if (!day) notFound();

  const tTracks = await getTranslations('tracks');
  const tCentroids = await getTranslations('centroids');
  const tNav = await getTranslations('nav');
  const trackLabel = getTrackLabel(track_key as Track, tTracks);
  const centroidLabel = getCentroidLabel(centroid.id, centroid.label, tCentroids);
  const dayLabel = formatDayLabel(date, locale as SeoLocale);

  const idx = months.indexOf(activeMonth);
  const prevMonth = idx < months.length - 1 ? months[idx + 1] : null;
  const nextMonth = idx > 0 ? months[idx - 1] : null;

  const otherTracksList = await getTracksByCentroid(centroid_key);
  const otherTracks = otherTracksList.filter(t => t !== track_key);

  const path = `/c/${centroid.id}/t/${track_key}/${date}`;
  // NewsArticle schema only for days with a brief — those are the
  // substantive article-like pages. No-brief days render as navigable
  // event listings without an article claim.
  const articleJsonLd = day.daily_brief
    ? newsArticleJsonLd({
        headline: `${centroidLabel} ${trackLabel.toLowerCase()}: ${dayLabel}`,
        description: truncateDescription(day.daily_brief),
        datePublished: `${date}T00:00:00Z`,
        path,
        locale: locale as SeoLocale,
        articleSection: trackLabel,
      })
    : null;

  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm">
      <CalendarScopeCard scope={view.scope} trackLabel={trackLabel} />

      {otherTracksList.length > 0 && (
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
          defaultDay={date}
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
        data={[
          ...(articleJsonLd ? [articleJsonLd] : []),
          breadcrumbList([
            { name: centroidLabel, path: `/c/${centroid.id}` },
            { name: trackLabel, path: `/c/${centroid.id}/t/${track_key}` },
            { name: dayLabel, path },
          ]),
        ]}
      />
      <CalendarDayPanel
        view={view}
        defaultDay={date}
        centroidKey={centroid_key}
        trackKey={track_key}
      />
    </DashboardLayout>
  );
}
