'use client';

import Link from 'next/link';
import { TrendingEvent, EventNarrativeLink, getTrackLabel, getCentroidLabel, formatTimeAgo } from '@/lib/types';
import { getTrackIcon } from './TrackCard';
import { useTranslations } from 'next-intl';

function Perspectives({ perspectives, tCentroids, alsoLabel }: { perspectives?: TrendingEvent[]; tCentroids: any; alsoLabel: string }) {
  if (!perspectives || perspectives.length === 0) return null;
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-xs text-dashboard-text-muted">
      <span>{alsoLabel}:</span>
      {perspectives.map(p => (
        <Link
          key={p.id}
          href={`/events/${p.id}`}
          className="inline-flex items-center gap-1 hover:text-blue-400 transition"
        >
          {p.iso_codes?.slice(0, 1).map(iso => (
            <FlagImg key={iso} iso2={iso} size={12} />
          ))}
          <span>{getCentroidLabel(p.centroid_id, p.centroid_label, tCentroids)}</span>
          <span className="text-dashboard-text-muted/60">({p.source_batch_count})</span>
        </Link>
      ))}
    </div>
  );
}

interface TrendingCardProps {
  event: TrendingEvent;
  compact?: boolean;
  narrative?: EventNarrativeLink;
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

function FreshnessDot({ lastActive, title }: { lastActive: string; title: string }) {
  const isRecent = (Date.now() - new Date(lastActive).getTime()) < 172800000;
  if (!isRecent) return null;
  return (
    <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" title={title} />
  );
}

function parseSignal(raw: string): { type: string; value: string } {
  const idx = raw.indexOf(':');
  if (idx > 0) return { type: raw.slice(0, idx), value: raw.slice(idx + 1) };
  return { type: 'persons', value: raw };
}

function NarrativeBadge({ narrative }: { narrative?: EventNarrativeLink }) {
  if (!narrative) return null;
  return (
    <Link
      href={`/narratives/${narrative.narrative_id}`}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-purple-500/10 border border-purple-500/20 text-purple-400 hover:bg-purple-500/20 transition truncate max-w-full"
    >
      <span className="truncate">{narrative.narrative_name}</span>
    </Link>
  );
}

function SignalPills({ signals }: { signals?: string[] }) {
  if (!signals || signals.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1">
      {signals.map(s => {
        const { type, value } = parseSignal(s);
        return (
          <Link
            key={s}
            href={`/signals/${type}/${encodeURIComponent(value)}`}
            className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-500/10 border border-blue-500/20 text-blue-400 hover:bg-blue-500/20 transition"
          >
            {value}
          </Link>
        );
      })}
    </div>
  );
}

export default function TrendingCard({ event, compact, narrative }: TrendingCardProps) {
  const tTracks = useTranslations('tracks');
  const tCentroids = useTranslations('centroids');
  const tCommon = useTranslations('common');
  const tTrending = useTranslations('trending');
  const timeAgo = formatTimeAgo(new Date(event.last_active), tCommon);
  const trackLabel = getTrackLabel(event.track, tTracks);
  const eventHref = `/events/${event.id}`;
  const isEmerging = (Date.now() - new Date(event.last_active).getTime()) < 43200000; // 12h

  if (compact) {
    return (
      <div className={`p-3 border bg-dashboard-surface rounded-lg hover:border-blue-500 transition group ${isEmerging ? 'border-yellow-500/40 shadow-[0_0_12px_rgba(234,179,8,0.15)]' : 'border-dashboard-border'}`}>
        <div className="flex items-start gap-3">
          <div className="text-blue-400 shrink-0 mt-0.5">
            {getTrackIcon(event.track)}
          </div>
          <div className="min-w-0 flex-1 space-y-1.5">
            <h3 className="text-sm font-medium text-dashboard-text group-hover:text-blue-400 transition">
              <Link href={eventHref}>{event.title}</Link>
            </h3>
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-dashboard-text-muted">
              <span className="flex items-center gap-1">
                {event.iso_codes?.slice(0, 2).map(iso => (
                  <FlagImg key={iso} iso2={iso} size={14} />
                ))}
                {getCentroidLabel(event.centroid_id, event.centroid_label, tCentroids)}
              </span>
              <span>{tCommon('sourcesCount', { count: event.source_batch_count })}</span>
              {timeAgo && <span>{timeAgo}</span>}
              <FreshnessDot lastActive={event.last_active} title={tTrending('active48h')} />
            </div>
            <div className="flex flex-wrap items-center gap-1">
              <NarrativeBadge narrative={narrative} />
              <SignalPills signals={event.top_signals} />
            </div>
            <Perspectives perspectives={event.perspectives} tCentroids={tCentroids} alsoLabel={tTrending('also')} />
          </div>
        </div>
      </div>
    );
  }

  // Hero card (default)
  return (
    <div className={`p-5 border bg-dashboard-surface rounded-lg hover:border-blue-500 transition ${isEmerging ? 'border-yellow-500/40 shadow-[0_0_16px_rgba(234,179,8,0.2)]' : 'border-dashboard-border'}`}>
      <div className="flex items-center gap-2 mb-3">
        <span className="flex items-center gap-1">
          {event.iso_codes?.slice(0, 3).map(iso => (
            <FlagImg key={iso} iso2={iso} />
          ))}
        </span>
        <span className="text-xs text-dashboard-text-muted truncate">{getCentroidLabel(event.centroid_id, event.centroid_label, tCentroids)}</span>
        <span className="flex items-center gap-1.5 ml-auto text-blue-400">
          {getTrackIcon(event.track)}
          <span className="text-xs text-dashboard-text-muted">{trackLabel}</span>
        </span>
      </div>

      <Link href={eventHref}>
        <h3 className="text-lg font-semibold mb-2 hover:text-blue-400 transition">
          {event.title}
        </h3>
      </Link>

      {event.summary && (
        <p className="text-sm text-dashboard-text-muted leading-relaxed mb-3 line-clamp-4">
          {event.summary}
        </p>
      )}

      <div className="flex items-center gap-3 text-xs text-dashboard-text-muted mb-2">
        <span>{tCommon('sourcesCount', { count: event.source_batch_count })}</span>
        {timeAgo && <span>{timeAgo}</span>}
        <FreshnessDot lastActive={event.last_active} title={tTrending('active48h')} />
      </div>

      <div className="flex flex-wrap items-center gap-1">
        <NarrativeBadge narrative={narrative} />
        <SignalPills signals={event.top_signals} />
      </div>
      <Perspectives perspectives={event.perspectives} tCentroids={tCentroids} alsoLabel={tTrending('also')} />
    </div>
  );
}
