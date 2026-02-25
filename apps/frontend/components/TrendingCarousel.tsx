import Link from 'next/link';
import TrendingCarouselClient from './TrendingCarouselClient';
import { getTrendingEvents } from '@/lib/queries';

export default async function TrendingCarousel() {
  const events = await getTrendingEvents(12);
  if (events.length === 0) return null;

  return (
    <section>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold">Trending Now</h2>
        <Link
          href="/trending"
          className="text-sm text-blue-400 hover:text-blue-300 transition"
        >
          View all
        </Link>
      </div>
      <TrendingCarouselClient events={events} />
    </section>
  );
}
