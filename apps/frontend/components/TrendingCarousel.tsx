import Link from 'next/link';
import TrendingCarouselClient from './TrendingCarouselClient';
import { getTrendingEvents } from '@/lib/queries';
import { dedupTrendingEvents } from '@/lib/dedup-trending';
import { getTranslations, getLocale } from 'next-intl/server';

export default async function TrendingCarousel() {
  const locale = await getLocale();
  const raw = await getTrendingEvents(30, locale);
  const events = dedupTrendingEvents(raw).slice(0, 12);
  if (events.length === 0) return null;
  const t = await getTranslations('home');
  const tCommon = await getTranslations('common');

  return (
    <section>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold">{t('trendingNow')}</h2>
        <Link
          href="/trending"
          className="text-sm text-blue-400 hover:text-blue-300 transition"
        >
          {tCommon('viewAll')}
        </Link>
      </div>
      <TrendingCarouselClient events={events} />
    </section>
  );
}
