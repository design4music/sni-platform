'use client';

import { useMemo, useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import type { CentroidMonthView, CentroidStripeEntry } from '@/lib/types';

// ---------------------------------------------------------------------------
// Track palette — one base color per track, solid 400 fills.
// Matches per-track calendar page family hues (red/sky/amber/emerald).
// ---------------------------------------------------------------------------

const TRACK_COLORS: Record<string, string> = {
  geo_security: 'bg-red-400',
  geo_politics: 'bg-sky-400',
  geo_economy:  'bg-amber-400',
  geo_society:  'bg-emerald-400',
};
const TRACK_FALLBACK_COLOR = 'bg-zinc-400';

function trackColor(track: string): string {
  return TRACK_COLORS[track] || TRACK_FALLBACK_COLOR;
}

function formatTrackLabel(track: string): string {
  return track.replace(/^geo_/, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function formatMonthLong(monthStr: string): string {
  const [y, m] = monthStr.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

function formatMonthShort(monthStr: string): string {
  const [y, m] = monthStr.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString('en-US', { month: 'short' });
}

function dayNumber(dateStr: string): number {
  return parseInt(dateStr.split('-')[2], 10);
}

// ---------------------------------------------------------------------------
// CentroidHero — country-level, cross-track stacked activity chart.
// ---------------------------------------------------------------------------

interface HeroProps {
  view: CentroidMonthView;
  centroidLabel: string;
  centroidKey: string;
  activeMonth: string; // YYYY-MM
}

export default function CentroidHero({
  view,
  centroidLabel,
  centroidKey,
  activeMonth,
}: HeroProps) {
  const [activeDate, setActiveDate] = useState<string | null>(null);
  const chartRef = useRef<HTMLDivElement | null>(null);

  // Close popover on outside click
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

  // Month-aggregate track share for the legend
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

  const prevMonth = view.prev_month;
  const nextMonth = view.next_month;
  const baseUrl = `/c/${centroidKey}`;

  return (
    <section>
      {/* Header row: title + month nav */}
      <div className="flex items-start justify-between gap-4 mb-5">
        <div className="min-w-0">
          <h2 className="text-2xl lg:text-3xl font-semibold text-dashboard-text">
            {centroidLabel}
            <span className="text-dashboard-text-muted font-normal">
              {' · '}
              {formatMonthLong(activeMonth)}
            </span>
          </h2>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {prevMonth ? (
            <Link
              href={`${baseUrl}?month=${prevMonth}`}
              className="px-3 py-1.5 text-sm text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition"
              aria-label="Previous month"
            >
              ‹ {formatMonthShort(prevMonth)}
            </Link>
          ) : null}
          {nextMonth ? (
            <Link
              href={`${baseUrl}?month=${nextMonth}`}
              className="px-3 py-1.5 text-sm text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition"
              aria-label="Next month"
            >
              {formatMonthShort(nextMonth)} ›
            </Link>
          ) : null}
        </div>
      </div>

      {/* Stacked activity chart */}
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
            return (
              <DayPopover
                entry={entry}
                centroidKey={centroidKey}
                activeMonth={activeMonth}
                onClose={() => setActiveDate(null)}
              />
            );
          })()}
        </div>

        {/* Day number axis */}
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

        {/* Legend: 4 tracks + share % */}
        {trackRanking.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] text-dashboard-text-muted">
            {trackRanking.map(({ track, share }) => (
              <Link
                key={track}
                href={`/c/${centroidKey}/t/${track}?month=${activeMonth}`}
                className="flex items-center gap-1.5 hover:text-dashboard-text transition"
              >
                <span className={`${trackColor(track)} inline-block w-2.5 h-2.5 rounded-sm`} />
                <span className="text-dashboard-text">{formatTrackLabel(track)}</span>
                <span className="tabular-nums">{Math.round(share * 100)}%</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// StackedBar — one day's vertical segmented column, colored by track.
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// DayPopover — floating card shown on day-bar click. Mobile-friendly tooltip
// replacement: date, total sources, per-track breakdown with deep-link
// calendar shortcuts. Closes on outside click (handled by parent).
// ---------------------------------------------------------------------------

function DayPopover({
  entry,
  centroidKey,
  activeMonth,
  onClose,
}: {
  entry: CentroidStripeEntry;
  centroidKey: string;
  activeMonth: string;
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
            {entry.total_sources} sources
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
          <li key={t.track}>
            <Link
              href={`/c/${centroidKey}/t/${t.track}?month=${activeMonth}&day=${entry.date}`}
              className="flex items-center gap-2 group"
            >
              <span className={`${trackColor(t.track)} inline-block w-2.5 h-2.5 rounded-sm shrink-0`} />
              <span className="flex-1 text-sm text-dashboard-text group-hover:text-blue-400 transition">
                {formatTrackLabel(t.track)}
              </span>
              <span className="text-xs text-dashboard-text-muted tabular-nums">
                {Math.round(t.weight * 100)}%
              </span>
              <span className="text-xs text-dashboard-text-muted tabular-nums">
                {Math.round(t.weight * entry.total_sources)}
              </span>
            </Link>
          </li>
        ))}
      </ul>
      <div className="mt-3 pt-2 border-t border-dashboard-border text-[10px] text-dashboard-text-muted">
        Click a track to open its calendar for this day
      </div>
    </div>
  );
}
