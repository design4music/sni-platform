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

// Server-side default-day picker (not imported from client component)
function pickDefaultDay(view: CalendarMonthView, explicit: string | null): string | null {
  if (explicit && view.days.some(d => d.date === explicit)) return explicit;
  if (view.days.length === 0) return null;
  return view.days.reduce((best, d) => (d.total_sources > best.total_sources ? d : best)).date;
}
import { getTrackIcon } from '@/components/TrackCard';
import {
  getCalendarMonthView,
  getCentroidById,
  getCTMMonths,
  getTracksByCentroid,
} from '@/lib/queries';
import { getTrackLabel, getCentroidLabel, Track } from '@/lib/types';
import { setRequestLocale, getTranslations } from 'next-intl/server';

export const dynamic = 'force-dynamic';

interface CalendarPageProps {
  params: Promise<{ locale: string; centroid_key: string; track_key: string }>;
  searchParams: Promise<{ month?: string; day?: string }>;
}

export async function generateMetadata({ params }: CalendarPageProps): Promise<Metadata> {
  const { centroid_key, track_key } = await params;
  const tTracks = await getTranslations('tracks');
  const tCentroids = await getTranslations('centroids');
  const centroid = await getCentroidById(centroid_key);
  if (!centroid) return { title: 'Not found' };
  const trackLabel = getTrackLabel(track_key as Track, tTracks);
  const centroidLabel = getCentroidLabel(centroid.id, centroid.label, tCentroids);
  return {
    title: `${centroidLabel}: ${trackLabel} — Calendar`,
    alternates: { canonical: `/c/${centroid_key}/t/${track_key}/calendar` },
  };
}

export default async function CalendarPage({ params, searchParams }: CalendarPageProps) {
  const { locale, centroid_key, track_key } = await params;
  const { month, day } = await searchParams;
  setRequestLocale(locale);

  const centroid = await getCentroidById(centroid_key, locale);
  if (!centroid) notFound();

  const months = await getCTMMonths(centroid_key, track_key);
  if (months.length === 0) {
    return (
      <DashboardLayout>
        <div className="p-6 text-dashboard-text-muted">No data for this CTM.</div>
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

  // Track switcher (reused from CTM track page pattern)
  const otherTracksList = await getTracksByCentroid(centroid_key);
  const otherTracks = otherTracksList.filter(t => t !== track_key);

  const defaultDay = pickDefaultDay(view, day || null);

  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm">
      {/* Analysis scope info box (month nav lives in the hero, not here) */}
      <CalendarScopeCard scope={view.scope} trackLabel={trackLabel} />

      {/* Other tracks for this centroid */}
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
                  href={`/c/${centroid.id}/t/${t}/calendar?month=${activeMonth}`}
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
      <CalendarDayPanel view={view} defaultDay={defaultDay} />
    </DashboardLayout>
  );
}
