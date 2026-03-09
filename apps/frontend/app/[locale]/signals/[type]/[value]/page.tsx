import { Suspense } from 'react';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import MentionTimeline from '@/components/signals/MentionTimeline';
import HorizontalBars from '@/components/signals/HorizontalBars';
import { getSignalStats, getRelationshipClusters } from '@/lib/queries';
import { SignalType, getTrackLabel } from '@/lib/types';

const SIGNAL_CATEGORY_KEY: Record<SignalType, string> = {
  persons: 'topPersons',
  orgs: 'topOrgs',
  places: 'topPlaces',
  commodities: 'topCommodities',
  policies: 'topPolicies',
  systems: 'topSystems',
  named_events: 'topEvents',
};
import { getTranslations, getLocale } from 'next-intl/server';

export const revalidate = 300;

const VALID_TYPES = new Set<SignalType>([
  'persons', 'orgs', 'places', 'commodities', 'policies', 'systems', 'named_events',
]);

const TYPE_BADGE: Record<SignalType, { bg: string; border: string; text: string }> = {
  persons:      { bg: 'bg-blue-500/10',   border: 'border-blue-500/20',   text: 'text-blue-400' },
  orgs:         { bg: 'bg-green-500/10',  border: 'border-green-500/20',  text: 'text-green-400' },
  places:       { bg: 'bg-orange-500/10', border: 'border-orange-500/20', text: 'text-orange-400' },
  commodities:  { bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', text: 'text-yellow-400' },
  policies:     { bg: 'bg-purple-500/10', border: 'border-purple-500/20', text: 'text-purple-400' },
  systems:      { bg: 'bg-cyan-500/10',   border: 'border-cyan-500/20',   text: 'text-cyan-400' },
  named_events: { bg: 'bg-pink-500/10',   border: 'border-pink-500/20',   text: 'text-pink-400' },
};

const TYPE_LABEL_KEY: Record<SignalType, string> = {
  persons: 'person',
  orgs: 'organization',
  places: 'place',
  commodities: 'commodity',
  policies: 'policy',
  systems: 'system',
  named_events: 'eventType',
};

interface Props {
  params: Promise<{ type: string; value: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { type, value } = await params;
  const decoded = decodeURIComponent(value);
  const t = await getTranslations('signals');
  const typeKey = TYPE_LABEL_KEY[type as SignalType];
  if (!typeKey) return { title: 'Signal Not Found' };
  return {
    title: `${decoded} - ${t(typeKey)} Signal`,
    description: `Signal profile for ${decoded}: mention timeline, geographic distribution, co-occurring signals, and top events.`,
  };
}

export default async function SignalDetailPage({ params }: Props) {
  const { type, value } = await params;
  const signalType = type as SignalType;
  if (!VALID_TYPES.has(signalType)) return notFound();

  const decoded = decodeURIComponent(value);
  const tTracks = await getTranslations('tracks');
  const t = await getTranslations('signals');
  const tNav = await getTranslations('nav');
  const locale = await getLocale();
  const stats = await getSignalStats(signalType, decoded);
  if (!stats || stats.total === 0) return notFound();

  const badge = TYPE_BADGE[signalType];
  const countryNames = new Intl.DisplayNames([locale], { type: 'region' });

  const geoData = stats.geo.map(g => {
    let label: string;
    try { label = countryNames.of(g.country) || g.country; } catch { label = g.country; }
    return { label, value: g.count };
  });

  const trackData = stats.tracks.map(tk => ({
    label: getTrackLabel(tk.track, tTracks),
    value: tk.count,
  }));

  const categoryLabel = t(SIGNAL_CATEGORY_KEY[signalType]);
  const breadcrumb = (
    <div className="flex items-center gap-1 text-sm">
      <Link href="/signals" className="text-blue-400 hover:text-blue-300">
        {tNav('signals')}
      </Link>
      <span className="text-dashboard-text-muted">/</span>
      <Link href={`/signals/${type}`} className="text-blue-400 hover:text-blue-300">
        {categoryLabel}
      </Link>
    </div>
  );

  return (
    <DashboardLayout breadcrumb={breadcrumb}>
      {/* Header */}
      <div className="mb-8 pb-6 border-b border-dashboard-border">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold mb-2">{decoded}</h1>
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${badge.bg} border ${badge.border} ${badge.text}`}>
                {t(TYPE_LABEL_KEY[signalType])}
              </span>
            </div>
          </div>
          <span className="text-dashboard-text-muted text-sm whitespace-nowrap">
            {t('eventsCount', { total: stats.total.toLocaleString() })}
            <span className="text-dashboard-text-muted/60"> {t('last30days')}</span>
          </span>
        </div>
      </div>

      {/* Mention Timeline */}
      {stats.weekly.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-3">{t('mentionTimeline')}</h2>
          <MentionTimeline weekly={stats.weekly} />
        </div>
      )}

      {/* Relationship Highlights — streamed in via Suspense */}
      <Suspense fallback={<RelationshipSkeleton />}>
        <RelationshipSection type={signalType} value={decoded} totalEvents={stats.total} />
      </Suspense>

      {/* Geo + Tracks side by side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-4 rounded-lg border border-dashboard-border bg-dashboard-surface">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
            {t('geographicDistribution')}
          </h3>
          <HorizontalBars data={geoData} color="#3b82f6" />
        </div>
        <div className="p-4 rounded-lg border border-dashboard-border bg-dashboard-surface">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
            {t('themeBreakdown')}
          </h3>
          <HorizontalBars data={trackData} color="#8b5cf6" />
        </div>
      </div>
    </DashboardLayout>
  );
}

async function RelationshipSection({ type, value, totalEvents }: { type: SignalType; value: string; totalEvents: number }) {
  const t = await getTranslations('signals');
  const locale = await getLocale();
  const clusters = await getRelationshipClusters(type, value, undefined, locale);
  if (clusters.length === 0) return null;

  const isMega = totalEvents >= 200;
  const maxClusters = isMega ? 20 : 10;
  const visible = clusters.slice(0, maxClusters);
  const dateFmtLocale = locale === 'de' ? 'de-DE' : 'en-US';

  return (
    <div className="mb-8 p-4 rounded-lg border border-dashboard-border bg-dashboard-surface">
      <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-4">
        {t('relationshipHighlights')}
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {visible.map(rc => {
          const rcBadge = TYPE_BADGE[rc.signal_type];
          return (
            <div key={`${rc.signal_type}-${rc.value}`}>
              <div className="flex items-center gap-2 mb-1">
                <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${rcBadge.bg} border ${rcBadge.border} ${rcBadge.text}`}>
                  {t(TYPE_LABEL_KEY[rc.signal_type])}
                </span>
                <Link
                  href={`/signals/${rc.signal_type}/${encodeURIComponent(rc.value)}`}
                  className="text-sm font-medium text-dashboard-text hover:text-blue-400 transition truncate"
                >
                  {rc.value}
                </Link>
                <span className="text-xs text-dashboard-text-muted ml-auto shrink-0">
                  {rc.event_count} {t('evShort')}
                </span>
              </div>
              {rc.top_events.length > 0 && (
                <>
                  <Link
                    href={`/events/${rc.top_events[0].id}`}
                    className="text-sm text-dashboard-text hover:text-blue-400 transition line-clamp-1 mb-1 block"
                  >
                    {rc.label}
                  </Link>
                  <ul className="space-y-0.5">
                    {rc.top_events.slice(1).map(ev => (
                      <li key={ev.id} className="flex items-center gap-1.5">
                        <span className="text-dashboard-text-muted text-xs">&#183;</span>
                        <Link
                          href={`/events/${ev.id}`}
                          className="text-xs text-dashboard-text-muted hover:text-blue-400 transition truncate"
                        >
                          {ev.title}
                        </Link>
                        <span className="text-[10px] text-dashboard-text-muted/60 ml-auto shrink-0">
                          {new Date(ev.date).toLocaleDateString(dateFmtLocale, { month: 'short', day: 'numeric' })}
                        </span>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RelationshipSkeleton() {
  return (
    <div className="mb-8 p-4 rounded-lg border border-dashboard-border bg-dashboard-surface animate-pulse">
      <div className="h-4 w-48 bg-dashboard-border rounded mb-4" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="h-4 w-16 bg-dashboard-border/50 rounded" />
              <div className="h-4 w-28 bg-dashboard-border rounded" />
            </div>
            <div className="h-4 w-full bg-dashboard-border/50 rounded" />
            <div className="h-3 w-4/5 bg-dashboard-border/30 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
