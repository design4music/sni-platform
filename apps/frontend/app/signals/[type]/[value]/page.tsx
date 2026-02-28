import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import MentionTimeline from '@/components/signals/MentionTimeline';
import HorizontalBars from '@/components/signals/HorizontalBars';
import { getSignalProfile } from '@/lib/queries';
import { SignalType, SIGNAL_LABELS, getCountryName, getTrackLabel } from '@/lib/types';

export const dynamic = 'force-dynamic';

const VALID_TYPES = new Set<SignalType>([
  'persons', 'orgs', 'places', 'commodities', 'policies', 'systems', 'named_events',
]);

const TYPE_BADGE: Record<SignalType, { label: string; bg: string; border: string; text: string }> = {
  persons:      { label: 'Person',      bg: 'bg-blue-500/10',   border: 'border-blue-500/20',   text: 'text-blue-400' },
  orgs:         { label: 'Organization', bg: 'bg-green-500/10',  border: 'border-green-500/20',  text: 'text-green-400' },
  places:       { label: 'Place',       bg: 'bg-orange-500/10', border: 'border-orange-500/20', text: 'text-orange-400' },
  commodities:  { label: 'Commodity',   bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', text: 'text-yellow-400' },
  policies:     { label: 'Policy',      bg: 'bg-purple-500/10', border: 'border-purple-500/20', text: 'text-purple-400' },
  systems:      { label: 'System',      bg: 'bg-cyan-500/10',   border: 'border-cyan-500/20',   text: 'text-cyan-400' },
  named_events: { label: 'Event',       bg: 'bg-pink-500/10',   border: 'border-pink-500/20',   text: 'text-pink-400' },
};

interface Props {
  params: Promise<{ type: string; value: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { type, value } = await params;
  const decoded = decodeURIComponent(value);
  const badge = TYPE_BADGE[type as SignalType];
  if (!badge) return { title: 'Signal Not Found' };
  return {
    title: `${decoded} - ${badge.label} Signal`,
    description: `Signal profile for ${decoded}: mention timeline, geographic distribution, co-occurring signals, and top events.`,
  };
}

export default async function SignalDetailPage({ params }: Props) {
  const { type, value } = await params;
  const signalType = type as SignalType;
  if (!VALID_TYPES.has(signalType)) return notFound();

  const decoded = decodeURIComponent(value);
  const profile = await getSignalProfile(signalType, decoded);
  if (!profile || profile.total_events === 0) return notFound();

  const badge = TYPE_BADGE[signalType];

  const geoData = profile.geo.map(g => ({
    label: getCountryName(g.country),
    value: g.count,
  }));

  const trackData = profile.tracks.map(t => ({
    label: getTrackLabel(t.track),
    value: t.count,
  }));

  const categoryLabel = SIGNAL_LABELS[signalType];
  const breadcrumb = (
    <div className="flex items-center gap-1 text-sm">
      <Link href="/signals" className="text-blue-400 hover:text-blue-300">
        Signals
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
                {badge.label}
              </span>
            </div>
          </div>
          <span className="text-dashboard-text-muted text-sm whitespace-nowrap">
            {profile.total_events.toLocaleString()} events
            <span className="text-dashboard-text-muted/60"> (last 30 days)</span>
          </span>
        </div>
      </div>

      {/* Mention Timeline */}
      {profile.weekly.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-3">Mention Timeline</h2>
          <MentionTimeline weekly={profile.weekly} />
        </div>
      )}

      {/* Relationship Highlights — mega signals (200+ events) get 20, others get 10 */}
      {profile.relationship_clusters.length > 0 && (() => {
        const isMega = profile.total_events >= 200;
        const maxClusters = isMega ? 20 : 10;
        const visible = profile.relationship_clusters.slice(0, maxClusters);
        return (
          <div className="mb-8 p-4 rounded-lg border border-dashboard-border bg-dashboard-surface">
            <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-4">
              Relationship Highlights
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {visible.map(rc => {
                const rcBadge = TYPE_BADGE[rc.signal_type];
                return (
                  <div key={`${rc.signal_type}-${rc.value}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${rcBadge.bg} border ${rcBadge.border} ${rcBadge.text}`}>
                        {rcBadge.label}
                      </span>
                      <Link
                        href={`/signals/${rc.signal_type}/${encodeURIComponent(rc.value)}`}
                        className="text-sm font-medium text-dashboard-text hover:text-blue-400 transition truncate"
                      >
                        {rc.value}
                      </Link>
                      <span className="text-xs text-dashboard-text-muted ml-auto shrink-0">
                        {rc.event_count} ev
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
                                {new Date(ev.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
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
      })()}

      {/* Geo + Tracks side by side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-4 rounded-lg border border-dashboard-border bg-dashboard-surface">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
            Geographic Distribution
          </h3>
          <HorizontalBars data={geoData} color="#3b82f6" />
        </div>
        <div className="p-4 rounded-lg border border-dashboard-border bg-dashboard-surface">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
            Theme Breakdown
          </h3>
          <HorizontalBars data={trackData} color="#8b5cf6" />
        </div>
      </div>
    </DashboardLayout>
  );
}
