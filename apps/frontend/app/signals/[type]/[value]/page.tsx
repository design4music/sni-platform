import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import MentionTimeline from '@/components/signals/MentionTimeline';
import HorizontalBars from '@/components/signals/HorizontalBars';
import { getSignalProfile } from '@/lib/queries';
import { SignalType, getCountryName, getTrackLabel } from '@/lib/types';

export const revalidate = 300;

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

  const breadcrumb = (
    <Link href="/signals" className="text-blue-400 hover:text-blue-300 text-sm">
      &larr; Signals
    </Link>
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
          </span>
        </div>
        {profile.context && (
          <p className="mt-3 text-sm text-dashboard-text-muted leading-relaxed">
            {profile.context}
          </p>
        )}
      </div>

      {/* Mention Timeline */}
      {profile.weekly.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-3">Mention Timeline</h2>
          <MentionTimeline weekly={profile.weekly} />
        </div>
      )}

      {/* 2x2 Grid: Relationships + Geo | Tracks + Top Events */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Relationships */}
        <div className="p-4 rounded-lg border border-dashboard-border bg-dashboard-surface">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
            Relationships
          </h3>
          {profile.co_occurring.length > 0 ? (
            <ul className="space-y-1.5">
              {profile.co_occurring.map(co => {
                const coBadge = TYPE_BADGE[co.signal_type];
                return (
                  <li key={`${co.signal_type}-${co.value}`}>
                    <Link
                      href={`/signals/${co.signal_type}/${encodeURIComponent(co.value)}`}
                      className="flex items-center gap-2 py-1 px-2 -mx-2 rounded hover:bg-dashboard-border/50 transition group"
                    >
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${coBadge.bg} border ${coBadge.border} ${coBadge.text}`}>
                        {coBadge.label}
                      </span>
                      <span className="text-sm text-dashboard-text group-hover:text-blue-400 transition truncate">
                        {co.value}
                      </span>
                      <span className="text-xs text-dashboard-text-muted ml-auto shrink-0">
                        {co.event_count}
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-sm text-dashboard-text-muted">No co-occurring signals found.</p>
          )}
        </div>

        {/* Geographic Distribution */}
        <div className="p-4 rounded-lg border border-dashboard-border bg-dashboard-surface">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
            Geographic Distribution
          </h3>
          <HorizontalBars data={geoData} color="#3b82f6" />
        </div>

        {/* Theme Breakdown */}
        <div className="p-4 rounded-lg border border-dashboard-border bg-dashboard-surface">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
            Theme Breakdown
          </h3>
          <HorizontalBars data={trackData} color="#8b5cf6" />
        </div>

        {/* Top Events */}
        <div className="p-4 rounded-lg border border-dashboard-border bg-dashboard-surface">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
            Top Events
          </h3>
          {profile.top_events.length > 0 ? (
            <ul className="space-y-2">
              {profile.top_events.slice(0, 10).map((ev, i) => (
                <li key={ev.id}>
                  <Link
                    href={`/events/${ev.id}`}
                    className="flex items-start gap-2 py-1.5 px-2 -mx-2 rounded hover:bg-dashboard-border/50 transition group"
                  >
                    <span className="text-xs text-dashboard-text-muted mt-0.5 w-5 shrink-0">
                      {i + 1}.
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-dashboard-text group-hover:text-blue-400 transition line-clamp-2">
                        {ev.title}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5 text-xs text-dashboard-text-muted">
                        <span>{new Date(ev.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                        <span>{ev.source_batch_count} src</span>
                        <span>{ev.centroid_label}</span>
                        <span className="text-dashboard-text-muted/60">{getTrackLabel(ev.track)}</span>
                      </div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-dashboard-text-muted">No events found.</p>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
