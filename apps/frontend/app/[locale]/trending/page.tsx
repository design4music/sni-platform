import { Suspense } from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import TrendingCard from '@/components/TrendingCard';
import { getTrendingEvents, getTrendingSignals, getTopNarrativePerEvent } from '@/lib/queries';
import { dedupTrendingEvents } from '@/lib/dedup-trending';
import { getTranslations, setRequestLocale } from 'next-intl/server';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Trending Stories - WorldBrief',
  description: 'The biggest stories right now, ranked by time-decayed source count across 180+ global news outlets.',
};

async function TrendingSignalsSidebar({ signals }: { signals: Record<string, { signal_type: string; value: string; event_count: number }[]> }) {
  const t = await getTranslations('trending');
  const SIGNAL_TYPE_KEYS: Record<string, string> = {
    persons: 'topPersons',
    orgs: 'topOrgs',
    places: 'topPlaces',
    commodities: 'topCommodities',
    policies: 'topPolicies',
  };
  const types = Object.keys(SIGNAL_TYPE_KEYS);

  return (
    <div className="sticky top-24 space-y-6">
      <h2 className="text-lg font-bold">
        <Link href="/signals" className="hover:text-blue-400 transition">
          {t('signals')}
        </Link>
      </h2>
      {types.map(type => {
        const items = signals[type];
        if (!items || items.length === 0) return null;
        return (
          <div key={type}>
            <h3 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">
              <Link href={`/signals/${type}`} className="hover:text-blue-400 transition">
                {t(SIGNAL_TYPE_KEYS[type] as any)}
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
                      {item.event_count} {item.event_count === 1 ? t('story') : t('stories')}
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

async function DeferredSignalsSidebar() {
  const t = await getTranslations('trending');
  const signals = await getTrendingSignals();
  return <TrendingSignalsSidebar signals={signals} />;
}

export default async function TrendingPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  const t = await getTranslations('trending');
  const raw = await getTrendingEvents(30, locale);
  const events = dedupTrendingEvents(raw).slice(0, 12);

  // Fetch top narrative per event (one badge per card, from event's own centroid)
  const narrativeMap = await getTopNarrativePerEvent(events.map(e => e.id));

  const heroEvents = events.slice(0, 3);
  const restEvents = events.slice(3);

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold mb-2">{t('title')}</h1>
            <p className="text-dashboard-text-muted">
              {t('subtitle')}
            </p>
          </div>
          <Link
            href="/trending/v2"
            className="shrink-0 text-xs px-3 py-1.5 rounded border border-blue-500/40 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 transition"
          >
            Preview v2 →
          </Link>
        </div>

        {/* Top 3 hero cards - full width */}
        {heroEvents.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {heroEvents.map(event => (
              <TrendingCard key={event.id} event={event} narrative={narrativeMap[event.id]} />
            ))}
          </div>
        )}

        {/* Two-column: compact list + sidebar */}
        {events.length > 3 && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-2">
              {restEvents.map(event => (
                <TrendingCard key={event.id} event={event} compact narrative={narrativeMap[event.id]} />
              ))}
            </div>
            <aside>
              <Suspense fallback={
                <div className="sticky top-24 space-y-6">
                  <h2 className="text-lg font-bold">{t('signals')}</h2>
                  <div className="space-y-3">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="h-24 rounded bg-dashboard-surface animate-pulse" />
                    ))}
                  </div>
                </div>
              }>
                <DeferredSignalsSidebar />
              </Suspense>
            </aside>
          </div>
        )}

        {events.length === 0 && (
          <p className="text-dashboard-text-muted text-center py-12">
            {t('empty')}
          </p>
        )}
      </div>
    </DashboardLayout>
  );
}
