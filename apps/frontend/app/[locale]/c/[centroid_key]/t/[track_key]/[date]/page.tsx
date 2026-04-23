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
  type Locale as SeoLocale,
} from '@/lib/seo';
import JsonLd from '@/components/JsonLd';

// Day-canonical page: indexable iff a daily_briefs row exists for
// (centroid, track, date). Threshold >5 promoted clusters is already
// enforced at brief-generation time.
export const revalidate = 1800;

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
  if (!view || !day || !day.daily_brief) {
    // No brief → not indexable. Serving 404 at the page level handles the
    // status code; here we just ensure metadata doesn't leak a real title.
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

  const description = truncateDescription(day.daily_brief);

  return buildPageMetadata({
    title,
    description,
    path: `/c/${centroid_key}/t/${track_key}/${date}`,
    locale,
    ogType: 'article',
    publishedTime: `${date}T00:00:00Z`,
  });
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
  if (!day || !day.daily_brief) notFound();

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
  const articleJsonLd = newsArticleJsonLd({
    headline: `${centroidLabel} ${trackLabel.toLowerCase()}: ${dayLabel}`,
    description: truncateDescription(day.daily_brief),
    datePublished: `${date}T00:00:00Z`,
    path,
    locale: locale as SeoLocale,
    articleSection: trackLabel,
  });

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
          articleJsonLd,
          breadcrumbList([
            { name: centroidLabel, path: `/c/${centroid.id}` },
            { name: trackLabel, path: `/c/${centroid.id}/t/${track_key}` },
            { name: dayLabel, path },
          ]),
        ]}
      />
      <CalendarDayPanel view={view} defaultDay={date} />
    </DashboardLayout>
  );
}
