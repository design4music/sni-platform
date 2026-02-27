import type { Metadata } from 'next';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import TrendingCard from '@/components/TrendingCard';
import { getTrendingEvents, getTrendingSignals } from '@/lib/queries';

export const revalidate = 300;

export const metadata: Metadata = {
  title: 'Trending Stories - WorldBrief',
  description: 'The biggest stories right now, ranked by time-decayed source count across 180+ global news outlets.',
};

const SIGNAL_TYPE_LABELS: Record<string, string> = {
  persons: 'Top Persons',
  orgs: 'Top Organizations',
  places: 'Top Places',
  commodities: 'Top Commodities',
  policies: 'Top Policies',
};

function TrendingSignalsSidebar({ signals }: { signals: Record<string, { signal_type: string; value: string; event_count: number }[]> }) {
  const types = Object.keys(SIGNAL_TYPE_LABELS);

  return (
    <div className="sticky top-24 space-y-6">
      <h2 className="text-lg font-bold">
        <Link href="/signals" className="hover:text-blue-400 transition">
          Trending Signals
        </Link>
      </h2>
      {types.map(type => {
        const items = signals[type];
        if (!items || items.length === 0) return null;
        return (
          <div key={type}>
            <h3 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">
              <Link href={`/signals/${type}`} className="hover:text-blue-400 transition">
                {SIGNAL_TYPE_LABELS[type]}
              </Link>
            </h3>
            <ul className="space-y-1.5">
              {items.map(item => (
                <li key={item.value}>
                  <Link
                    href={`/signals/${item.signal_type}/${encodeURIComponent(item.value)}`}
                    className="flex items-center justify-between text-sm py-0.5 rounded hover:text-blue-400 transition"
                  >
                    <span className="truncate text-dashboard-text">{item.value}</span>
                    <span className="text-xs text-dashboard-text-muted shrink-0 ml-2">
                      {item.event_count} {item.event_count === 1 ? 'story' : 'stories'}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
}

export default async function TrendingPage() {
  const [events, signals] = await Promise.all([
    getTrendingEvents(30),
    getTrendingSignals(),
  ]);

  const heroEvents = events.slice(0, 3);
  const restEvents = events.slice(3);

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold mb-2">Trending Stories</h1>
          <p className="text-dashboard-text-muted">
            The biggest stories right now, ranked by source count with time decay.
          </p>
        </div>

        {/* Top 3 hero cards - full width */}
        {heroEvents.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {heroEvents.map(event => (
              <TrendingCard key={event.id} event={event} />
            ))}
          </div>
        )}

        {/* Two-column: compact list + sidebar */}
        {events.length > 3 && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-2">
              {restEvents.map(event => (
                <TrendingCard key={event.id} event={event} compact />
              ))}
            </div>
            <aside>
              <TrendingSignalsSidebar signals={signals} />
            </aside>
          </div>
        )}

        {events.length === 0 && (
          <p className="text-dashboard-text-muted text-center py-12">
            No trending stories found. Check back soon.
          </p>
        )}
      </div>
    </DashboardLayout>
  );
}
