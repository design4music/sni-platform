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
  const tCentroids = await getTranslations('centroids');

  const [centroid, deviation, events] = await Promise.all([
    getCentroidById(user.focusCentroid, locale),
    getCentroidDeviations(user.focusCentroid),
    getFocusCountryEvents(user.focusCentroid, 5, locale),
  ]);

  if (!centroid) return null;

  const label = getCentroidLabel(centroid.id, centroid.label, tCentroids);

  return (
    <section>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold">{t('focusCountry', { country: label })}</h2>
        <Link
          href={`/c/${centroid.id}`}
          className="text-sm text-blue-400 hover:text-blue-300 transition"
        >
          {t('viewAll')}
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Deviation card in first column */}
        <div className="md:col-span-1">
          {deviation && deviation.deviations ? (
            <DeviationCard week={deviation.week} deviations={deviation.deviations} />
          ) : (
            <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4 h-full flex items-center justify-center">
              <p className="text-sm text-dashboard-text-muted">{t('noDeviations')}</p>
            </div>
          )}
        </div>

        {/* Top events in remaining columns */}
        <div className="md:col-span-2 space-y-2">
          {events.length > 0 ? events.map(event => (
            <Link
              key={event.id}
              href={`/event/${event.id}`}
              className="block p-3 bg-dashboard-surface border border-dashboard-border rounded-lg hover:border-blue-500/50 transition"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="text-sm font-medium text-white truncate">{event.title}</h3>
                  {event.summary && (
                    <p className="text-xs text-dashboard-text-muted mt-1 line-clamp-2">{event.summary}</p>
                  )}
                </div>
                <span className="text-xs text-dashboard-text-muted whitespace-nowrap">
                  {event.source_batch_count} sources
                </span>
              </div>
            </Link>
          )) : (
            <p className="text-sm text-dashboard-text-muted">{t('noRecentEvents')}</p>
          )}
        </div>
      </div>
    </section>
  );
}
