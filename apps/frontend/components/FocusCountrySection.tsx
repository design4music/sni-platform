import Link from 'next/link';
import { auth } from '@/auth';
import { getCentroidById, getCentroidDeviations, getFocusCountryEvents } from '@/lib/queries';
import { query } from '@/lib/db';
import DeviationCard from './DeviationCard';
import FocusCarouselClient from './FocusCarouselClient';
import { getLocale, getTranslations } from 'next-intl/server';
import { getCentroidLabel } from '@/lib/types';

export default async function FocusCountrySection() {
  const session = await auth();
  const userId = session?.user?.id;
  if (!userId) return null;

  // Read focus_centroid directly from DB to avoid stale JWT cache
  const rows = await query<{ focus_centroid: string | null }>(
    'SELECT focus_centroid FROM users WHERE id = $1',
    [userId]
  );
  const focusCentroid = rows[0]?.focus_centroid;
  if (!focusCentroid) return null;

  const locale = await getLocale();
  const t = await getTranslations('home');
  const tCommon = await getTranslations('common');
  const tCentroids = await getTranslations('centroids');

  const [centroid, deviation] = await Promise.all([
    getCentroidById(focusCentroid, locale),
    getCentroidDeviations(focusCentroid),
  ]);
  const hasDeviation = !!(deviation && deviation.deviations);
  const eventCount = hasDeviation ? 8 : 9;
  const events = await getFocusCountryEvents(focusCentroid, eventCount, locale);

  if (!centroid) return null;

  const label = getCentroidLabel(centroid.id, centroid.label, tCentroids);

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">{t('focusCountry', { country: label })}</h2>
        <Link
          href={`/c/${centroid.id}`}
          className="text-sm text-blue-400 hover:text-blue-300 transition"
        >
          {t('viewAll')}
        </Link>
      </div>

      {events.length === 0 && !deviation ? (
        <p className="text-sm text-dashboard-text-muted">{t('noRecentEvents')}</p>
      ) : (
        <FocusCarouselClient>
          {deviation && deviation.deviations && (
            <DeviationCard week={deviation.week} deviations={deviation.deviations} />
          )}
          {events.map(event => (
            <Link
              key={event.id}
              href={`/events/${event.id}`}
              className="p-3 bg-dashboard-surface border border-dashboard-border rounded-lg hover:border-blue-500/50 transition flex flex-col"
            >
              <h3 className="text-sm font-medium text-white line-clamp-2 mb-1">{event.title}</h3>
              {event.summary && (
                <p className="text-xs text-dashboard-text-muted line-clamp-2 flex-1">{event.summary}</p>
              )}
              <div className="flex items-center justify-between mt-2 text-xs text-dashboard-text-muted">
                <span>{event.date}</span>
                <span>{event.source_batch_count} {tCommon('sources')}</span>
              </div>
            </Link>
          ))}
        </FocusCarouselClient>
      )}
    </section>
  );
}
