import Link from 'next/link';
import { auth } from '@/auth';
import { getCentroidById, getCentroidDeviations, getFocusCountryEvents } from '@/lib/queries';
import DeviationCard from './DeviationCard';
import { getLocale, getTranslations } from 'next-intl/server';
import { getCentroidLabel } from '@/lib/types';

export default async function FocusCountrySection() {
  const session = await auth();
  const user = session?.user as any;
  if (!user?.focusCentroid) return null;

  const locale = await getLocale();
  const t = await getTranslations('home');
  const tCommon = await getTranslations('common');
  const tCentroids = await getTranslations('centroids');

  const [centroid, deviation, events] = await Promise.all([
    getCentroidById(user.focusCentroid, locale),
    getCentroidDeviations(user.focusCentroid),
    getFocusCountryEvents(user.focusCentroid, 6, locale),
  ]);

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

      <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 md:mx-0 md:px-0 scrollbar-hide">
        {/* Deviation card */}
        {deviation && deviation.deviations && (
          <div className="flex-shrink-0 w-64">
            <DeviationCard week={deviation.week} deviations={deviation.deviations} />
          </div>
        )}

        {/* Event cards */}
        {events.map(event => (
          <Link
            key={event.id}
            href={`/events/${event.id}`}
            className="flex-shrink-0 w-64 p-3 bg-dashboard-surface border border-dashboard-border rounded-lg hover:border-blue-500/50 transition flex flex-col"
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

        {events.length === 0 && !deviation && (
          <p className="text-sm text-dashboard-text-muted">{t('noRecentEvents')}</p>
        )}
      </div>
    </section>
  );
}
