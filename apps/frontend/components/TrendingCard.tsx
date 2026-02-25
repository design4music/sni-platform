import Link from 'next/link';
import { TrendingEvent, getTrackLabel, formatTimeAgo } from '@/lib/types';
import { getTrackIcon } from './TrackCard';

interface TrendingCardProps {
  event: TrendingEvent;
  compact?: boolean;
}

function FlagImg({ iso2, size = 20 }: { iso2: string; size?: number }) {
  if (!iso2 || iso2.length !== 2) return null;
  return (
    <span
      className="inline-flex items-center justify-center rounded border border-blue-500/30 bg-blue-500/10 overflow-hidden align-middle"
      style={{ width: size + 6, height: Math.round(size * 0.75) + 4 }}
    >
      <img
        src={`/flags/${iso2.toLowerCase()}.png`}
        alt={iso2}
        width={size}
        height={Math.round(size * 0.75)}
        className="opacity-70"
        style={{ objectFit: 'contain', filter: 'saturate(0.6) brightness(0.9)' }}
      />
    </span>
  );
}

function FreshnessDot({ lastActive }: { lastActive: string }) {
  const isRecent = (Date.now() - new Date(lastActive).getTime()) < 172800000;
  if (!isRecent) return null;
  return (
    <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" title="Active in last 48h" />
  );
}

function SignalPills({ signals }: { signals?: string[] }) {
  if (!signals || signals.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1">
      {signals.map(s => (
        <span key={s} className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-500/10 border border-blue-500/20 text-blue-400">
          {s}
        </span>
      ))}
    </div>
  );
}

export default function TrendingCard({ event, compact }: TrendingCardProps) {
  const timeAgo = formatTimeAgo(new Date(event.last_active));
  const trackLabel = getTrackLabel(event.track);

  if (compact) {
    return (
      <Link
        href={`/events/${event.id}`}
        className="block p-3 border border-dashboard-border bg-dashboard-surface rounded-lg hover:border-blue-500 transition group"
      >
        <div className="flex items-start gap-3">
          <div className="text-blue-400 shrink-0 mt-0.5">
            {getTrackIcon(event.track)}
          </div>
          <div className="min-w-0 flex-1 space-y-1.5">
            <h3 className="text-sm font-medium text-dashboard-text group-hover:text-blue-400 transition">
              {event.title}
            </h3>
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-dashboard-text-muted">
              <span className="flex items-center gap-1">
                {event.iso_codes?.slice(0, 2).map(iso => (
                  <FlagImg key={iso} iso2={iso} size={14} />
                ))}
                {event.centroid_label}
              </span>
              <span>{event.source_batch_count} sources</span>
              {timeAgo && <span>{timeAgo}</span>}
              <FreshnessDot lastActive={event.last_active} />
            </div>
            <SignalPills signals={event.top_signals} />
          </div>
        </div>
      </Link>
    );
  }

  // Hero card (default)
  return (
    <Link
      href={`/events/${event.id}`}
      className="block p-5 border border-dashboard-border bg-dashboard-surface rounded-lg hover:border-blue-500 transition"
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="flex items-center gap-1">
          {event.iso_codes?.slice(0, 3).map(iso => (
            <FlagImg key={iso} iso2={iso} />
          ))}
        </span>
        <span className="text-xs text-dashboard-text-muted truncate">{event.centroid_label}</span>
        <span className="flex items-center gap-1.5 ml-auto text-blue-400">
          {getTrackIcon(event.track)}
          <span className="text-xs text-dashboard-text-muted">{trackLabel}</span>
        </span>
      </div>

      <h3 className="text-lg font-semibold mb-2">
        {event.title}
      </h3>

      {event.summary && (
        <p className="text-sm text-dashboard-text-muted leading-relaxed mb-3 line-clamp-4">
          {event.summary}
        </p>
      )}

      <div className="flex items-center gap-3 text-xs text-dashboard-text-muted mb-2">
        <span>{event.source_batch_count} sources</span>
        {timeAgo && <span>{timeAgo}</span>}
        <FreshnessDot lastActive={event.last_active} />
      </div>

      <SignalPills signals={event.top_signals} />
    </Link>
  );
}
