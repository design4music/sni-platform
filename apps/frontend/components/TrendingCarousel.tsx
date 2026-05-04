import Link from 'next/link';
import TrendingCarouselClient from './TrendingCarouselClient';
import {
  getFastestGrowingEvents,
  getGlobalAvailableMonths,
} from '@/lib/queries';
import type { TrendingEvent } from '@/lib/types';
import { getTranslations, getLocale } from 'next-intl/server';

export default async function TrendingCarousel() {
  const locale = await getLocale();
  const months = await getGlobalAvailableMonths();
  const currentMonth = months[0];
  if (!currentMonth) return null;

  const raw = await getFastestGrowingEvents(currentMonth, 12, locale);
  if (raw.length === 0) return null;

  // Adapt the lighter MV shape to TrendingEvent so the existing carousel
  // + card components keep working unchanged. trending_score is repurposed
  // as recent_7d_sources for the growth ribbon.
  const events: TrendingEvent[] = raw.map(r => ({
    id: r.id,
    title: r.title,
    date: r.date,
    last_active: r.last_active,
    source_batch_count: r.total_sources,
    tags: [],
    summary: r.summary,
    centroid_id: r.centroid_id,
    centroid_label: r.centroid_label,
    iso_codes: r.iso_codes,
    track: r.track,
    trending_score: r.recent_7d_sources,
    top_signals: r.top_signals,
  }));

  const t = await getTranslations('home');
  const tCommon = await getTranslations('common');

  return (
    <section>
      <div className="flex items-baseline justify-between gap-4 mb-3">
        <h2 className="text-3xl font-bold">{t('trendingNow')}</h2>
        <Link
          href="/trending"
          className="text-sm text-blue-400 hover:text-blue-300 transition shrink-0"
        >
          {tCommon('viewAll')}
        </Link>
      </div>
      <p className="text-sm text-dashboard-text-muted mb-6 max-w-3xl leading-relaxed">
        {t('trendingNowIntro')}
      </p>
      <TrendingCarouselClient events={events} />
    </section>
  );
}
