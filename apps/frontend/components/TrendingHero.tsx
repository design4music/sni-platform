'use client';

import { useMemo, useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import type { GlobalMonthView } from '@/lib/queries';
import type { CentroidStripeEntry } from '@/lib/types';

// Mirrors CentroidHero visual language (palette, stacked bars, day popover)
// but scoped to /trending/v2 — no per-centroid track links, no per-track
// calendar deep-links. Clicking the day popover takes the user to the same-day
// global overview (currently just re-renders with ?day=…; day drill-down is
// future work for the prototype).

const TRACK_COLORS: Record<string, string> = {
  geo_security: 'bg-red-400',
  geo_politics: 'bg-sky-400',
  geo_economy: 'bg-amber-400',
  geo_society: 'bg-emerald-400',
};
const TRACK_FALLBACK_COLOR = 'bg-zinc-400';

function trackColor(track: string): string {
  return TRACK_COLORS[track] || TRACK_FALLBACK_COLOR;
}

function formatTrackLabel(track: string): string {
  return track.replace(/^geo_/, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function formatMonthLong(monthStr: string): string {
  const [y, m] = monthStr.slice(0, 7).split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

function formatMonthShort(monthStr: string): string {
  const [y, m] = monthStr.slice(0, 7).split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString('en-US', { month: 'short' });
}

function dayNumber(dateStr: string): number {
  return parseInt(dateStr.split('-')[2], 10);
}

interface TrendingHeroProps {
  view: GlobalMonthView;
  activeMonth: string; // YYYY-MM
  isCurrentMonth: boolean;
  totalLabel: string; // e.g. "Global Briefing — April 2026"
}

export default function TrendingHero({
  view,
  activeMonth,
  isCurrentMonth,
  totalLabel,
}: TrendingHeroProps) {
  const [activeDate, setActiveDate] = useState<string | null>(null);
  const chartRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!activeDate) return;
    function onDocClick(e: MouseEvent) {
      if (!chartRef.current) return;
      if (!chartRef.current.contains(e.target as Node)) setActiveDate(null);
    }
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, [activeDate]);

  const maxStripeCount = Math.max(1, ...view.activity_stripe.map(s => s.total_sources));
  const logRatio = (n: number) =>
    n <= 0 ? 0 : Math.log10(n + 1) / Math.log10(maxStripeCount + 1);

  const trackRanking = useMemo(() => {
    const byTrack = new Map<string, number>();
    let total = 0;
    for (const day of view.activity_stripe) {
      if (!day.tracks.length || !day.total_sources) continue;
      for (const t of day.tracks) {
        const contribution = t.weight * day.total_sources;
        byTrack.set(t.track, (byTrack.get(t.track) || 0) + contribution);
        total += contribution;
      }
    }
    if (total === 0) return [];
    return Array.from(byTrack.entries())
      .map(([track, w]) => ({ track, share: w / total }))
      .sort((a, b) => b.share - a.share);
  }, [view.activity_stripe]);

  const baseUrl = '/trending/v2';

  return (
    <section>
      <div className="flex items-start justify-between gap-4 mb-5">
        <div className="min-w-0">
          <h2 className="text-2xl lg:text-3xl font-semibold text-dashboard-text">
            {totalLabel}
            {isCurrentMonth && (
              <span className="ml-3 align-middle inline-flex items-center px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-amber-500/15 text-amber-300 border border-amber-500/40 rounded">
                MTD · partial
              </span>
            )}
          </h2>
          <div className="mt-1 text-[12px] text-dashboard-text-muted tabular-nums">
            {view.total_sources.toLocaleString('en-US')} sources · {view.total_events.toLocaleString('en-US')} events · {view.active_centroid_count} centroids
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {view.prev_month ? (
            <Link
              href={`${baseUrl}?month=${view.prev_month}`}
              className="px-3 py-1.5 text-sm text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition"
              aria-label="Previous month"
            >
              ‹ {formatMonthShort(view.prev_month)}
            </Link>
          ) : null}
          {view.next_month ? (
            <Link
              href={`${baseUrl}?month=${view.next_month}`}
              className="px-3 py-1.5 text-sm text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition"
              aria-label="Next month"
            >
              {formatMonthShort(view.next_month)} ›
            </Link>
          ) : null}
        </div>
      </div>

      <div ref={chartRef}>
        <div className="relative">
          <div
            className="flex items-end gap-[3px] h-44"
            role="group"
            aria-label="Daily cross-track activity chart"
          >
            {view.activity_stripe.map(entry => (
              <StackedBar
                key={entry.date}
                entry={entry}
                ratio={logRatio(entry.total_sources)}
                isActive={entry.date === activeDate}
                onClick={() => setActiveDate(d => d === entry.date ? null : entry.date)}
              />
            ))}
          </div>
          {activeDate && (() => {
            const entry = view.activity_stripe.find(e => e.date === activeDate);
            if (!entry || !entry.tracks.length) return null;
            return <DayPopover entry={entry} onClose={() => setActiveDate(null)} />;
          })()}
        </div>

        <div className="flex mt-2 gap-[3px] text-[10px] text-dashboard-text-muted font-mono">
          {view.activity_stripe.map(entry => {
            const d = dayNumber(entry.date);
            const show = d === 1 || d % 5 === 0;
            return (
              <div key={entry.date} className="flex-1 text-center">
                {show ? d : ''}
              </div>
            );
          })}
        </div>

        {trackRanking.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] text-dashboard-text-muted">
            {trackRanking.map(({ track, share }) => (
              <span
                key={track}
                className="flex items-center gap-1.5"
              >
                <span className={`${trackColor(track)} inline-block w-2.5 h-2.5 rounded-sm`} />
                <span className="text-dashboard-text">{formatTrackLabel(track)}</span>
                <span className="tabular-nums">{Math.round(share * 100)}%</span>
              </span>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function StackedBar({
  entry,
  ratio,
  isActive,
  onClick,
}: {
  entry: CentroidStripeEntry;
  ratio: number;
  isActive: boolean;
  onClick: () => void;
}) {
  const hasTracks = entry.tracks.length > 0;

  if (!hasTracks) {
    return (
      <div
        className="flex-1 min-w-0 h-full flex items-end"
        title={`${entry.date}: no coverage`}
      >
        <div className="w-full h-[3px] bg-dashboard-border/40 rounded-sm" />
      </div>
    );
  }

  const heightPct = Math.max(4, Math.round(ratio * 100));
  const ariaLabel = `${entry.date}, ${entry.total_sources} sources`;

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={ariaLabel}
      className="flex-1 min-w-0 h-full flex flex-col justify-end items-stretch group p-0 cursor-pointer"
    >
      <div
        className={`relative w-full flex flex-col-reverse rounded-t-full overflow-hidden transition-all
          after:absolute after:inset-0 after:pointer-events-none
          after:bg-gradient-to-b after:from-white/15 after:via-transparent after:to-black/20
          ${isActive ? 'ring-2 ring-blue-400 ring-offset-1 ring-offset-dashboard-surface' : ''}`}
        style={{ height: `${heightPct}%` }}
      >
        {entry.tracks.map((seg, idx) => (
          <div
            key={`${entry.date}-${idx}`}
            className={`${trackColor(seg.track)} group-hover:brightness-125 transition`}
            style={{ height: `${seg.weight * 100}%` }}
          />
        ))}
      </div>
    </button>
  );
}

function DayPopover({
  entry,
  onClose,
}: {
  entry: CentroidStripeEntry;
  onClose: () => void;
}) {
  const [y, m, d] = entry.date.split('-').map(Number);
  const dateLabel = new Date(y, m - 1, d).toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  });

  return (
    <div
      className="absolute left-1/2 -translate-x-1/2 top-full mt-2 z-50 w-[min(420px,calc(100vw-2rem))]
                 bg-dashboard-surface border border-dashboard-border rounded-lg shadow-2xl
                 ring-1 ring-blue-400/20 p-4"
      role="dialog"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <div className="text-sm font-semibold text-dashboard-text">{dateLabel}</div>
          <div className="text-[11px] text-dashboard-text-muted tabular-nums">
            {entry.total_sources} sources globally
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-dashboard-text-muted hover:text-dashboard-text text-lg leading-none p-1 -mt-1"
          aria-label="Close"
        >
          ×
        </button>
      </div>
      <ul className="space-y-1.5">
        {entry.tracks.map(t => (
          <li key={t.track} className="flex items-center gap-2">
            <span className={`${trackColor(t.track)} inline-block w-2.5 h-2.5 rounded-sm shrink-0`} />
            <span className="flex-1 text-sm text-dashboard-text">
              {formatTrackLabel(t.track)}
            </span>
            <span className="text-xs text-dashboard-text-muted tabular-nums">
              {Math.round(t.weight * 100)}%
            </span>
            <span className="text-xs text-dashboard-text-muted tabular-nums">
              {Math.round(t.weight * entry.total_sources)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
