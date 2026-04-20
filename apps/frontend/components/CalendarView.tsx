'use client';

import { useMemo, useEffect, useCallback, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import ExternalLink from './ExternalLink';
import type {
  CalendarMonthView,
  CalendarDayView,
  CalendarClusterCard,
  CalendarClusterSource,
  CalendarStripeEntry,
  CalendarAnalysisScope,
} from '@/lib/types';

const INITIAL_EVENTS_SHOWN = 3; // top-N events shown per day before "Show all"

// One base color per track; tints assigned to sectors by their month-level
// aggregate share (top sector = brightest tint, #2 = next, etc.). This gives
// each sector a stable color across all days so the eye can follow it.
const TRACK_TINTS: Record<string, string[]> = {
  geo_security: ['bg-red-400',     'bg-red-500',     'bg-red-600',     'bg-red-700',     'bg-red-800'],
  geo_politics: ['bg-sky-400',     'bg-sky-500',     'bg-sky-600',     'bg-sky-700',     'bg-sky-800'],
  geo_economy:  ['bg-amber-400',   'bg-amber-500',   'bg-amber-600',   'bg-amber-700',   'bg-amber-800'],
  geo_society:  ['bg-emerald-400', 'bg-emerald-500', 'bg-emerald-600', 'bg-emerald-700', 'bg-emerald-800'],
};
const DEFAULT_TINTS = ['bg-zinc-400', 'bg-zinc-500', 'bg-zinc-600', 'bg-zinc-700', 'bg-zinc-800'];

function trackTints(trackKey: string): string[] {
  return TRACK_TINTS[trackKey] || DEFAULT_TINTS;
}

// Ghost fallback for covered days where title_labels gave no usable themes
// (rare — non-strategic only). Use the track's darkest tint so the column
// still reads as "this track", just muted.
function ghostTint(trackKey: string): string {
  const tints = trackTints(trackKey);
  return tints[tints.length - 1];
}

interface SectorRanking {
  sector: string;
  share: number;
  tint: string;
}

// Aggregate sector share over the whole month and assign each sector a tint
// by its rank. Sectors beyond the tint list fall back to the darkest tint.
function buildSectorRanking(
  stripe: CalendarStripeEntry[],
  trackKey: string
): SectorRanking[] {
  const bySector = new Map<string, number>();
  let total = 0;
  for (const day of stripe) {
    if (!day.themes.length || !day.total_sources) continue;
    for (const t of day.themes) {
      const contribution = t.weight * day.total_sources;
      bySector.set(t.sector, (bySector.get(t.sector) || 0) + contribution);
      total += contribution;
    }
  }
  if (total === 0) return [];
  const tints = trackTints(trackKey);
  return Array.from(bySector.entries())
    .map(([sector, w]) => ({ sector, share: w / total }))
    .sort((a, b) => b.share - a.share)
    .map((entry, idx) => ({
      ...entry,
      tint: tints[Math.min(idx, tints.length - 1)],
    }));
}

function formatSector(sector: string): string {
  return sector.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

function formatMonthLong(monthStr: string): string {
  const [y, m] = monthStr.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

function formatMonthShort(monthStr: string): string {
  const [y, m] = monthStr.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString('en-US', { month: 'short' });
}

function formatDayHeading(dateStr: string): string {
  // Compact calendar abbreviation: "Mon 6". Month omitted — it's always "this month".
  const [y, m, d] = dateStr.split('-').map(Number);
  const dt = new Date(y, m - 1, d);
  const wd = dt.toLocaleDateString('en-US', { weekday: 'short' });
  return `${wd} ${d}`;
}

function dayNumber(dateStr: string): number {
  return parseInt(dateStr.split('-')[2], 10);
}

// Client-shared state via URL: ?day=YYYY-MM-DD
function useDayParam(defaultDay: string | null): [string | null, (d: string) => void] {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const current = searchParams.get('day') || defaultDay;

  const setDay = useCallback(
    (date: string) => {
      const next = new URLSearchParams(Array.from(searchParams.entries()));
      next.set('day', date);
      router.replace(`${pathname}?${next.toString()}`, { scroll: false });
    },
    [router, pathname, searchParams]
  );

  return [current, setDay];
}

// ---------------------------------------------------------------------------
// CalendarHero — full-width top panel with header + stacked chart
// ---------------------------------------------------------------------------

interface HeroProps {
  view: CalendarMonthView;
  centroidLabel: string;
  trackLabel: string;
  centroidKey: string;
  trackKey: string;
  activeMonth: string;
  prevMonth: string | null;
  nextMonth: string | null;
  defaultDay: string | null;
}

export function CalendarHero({
  view,
  centroidLabel,
  trackLabel,
  centroidKey,
  trackKey,
  activeMonth,
  prevMonth,
  nextMonth,
  defaultDay,
}: HeroProps) {
  const [currentDay, setCurrentDay] = useDayParam(defaultDay);

  const dayByDate = useMemo(() => {
    const m = new Map<string, CalendarDayView>();
    for (const d of view.days) m.set(d.date, d);
    return m;
  }, [view.days]);

  const maxStripeCount = Math.max(1, ...view.activity_stripe.map(s => s.total_sources));
  const logRatio = (n: number) =>
    n <= 0 ? 0 : Math.log10(n + 1) / Math.log10(maxStripeCount + 1);

  const sectorRanking = useMemo(
    () => buildSectorRanking(view.activity_stripe, trackKey),
    [view.activity_stripe, trackKey]
  );
  const sectorTints = useMemo(() => {
    const m = new Map<string, string>();
    for (const r of sectorRanking) m.set(r.sector, r.tint);
    return m;
  }, [sectorRanking]);

  const jumpToDay = (date: string) => {
    if (!dayByDate.has(date)) return;
    setCurrentDay(date);
    // No scroll — the day panel is in a fixed position below the chart.
  };

  const baseUrl = `/c/${centroidKey}/t/${trackKey}`;

  return (
    <section>
      {/* Header row: breadcrumb + month nav */}
      <div className="flex items-start justify-between gap-4 mb-5">
        <div className="min-w-0">
          <Link
            href={`/c/${centroidKey}`}
            className="text-[11px] uppercase tracking-wider text-dashboard-text-muted hover:text-dashboard-text transition"
          >
            {centroidLabel}
          </Link>
          <h1 className="text-2xl lg:text-3xl font-semibold text-dashboard-text mt-1">
            {trackLabel}
            <span className="text-dashboard-text-muted font-normal">
              {' · '}
              {formatMonthLong(activeMonth)}
            </span>
          </h1>
          {view.theme_chips && view.theme_chips.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {view.theme_chips.map((chip, i) => (
                <span
                  key={`${chip.sector}-${chip.subject}-${i}`}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px]
                             bg-dashboard-border/40 border border-dashboard-border text-dashboard-text-muted"
                >
                  <span className="text-dashboard-text">
                    {formatSector(chip.sector)}
                    <span className="text-dashboard-text-muted"> · {formatSector(chip.subject)}</span>
                  </span>
                  <span className="tabular-nums">{Math.round(chip.weight * 100)}%</span>
                </span>
              ))}
            </div>
          )}
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
      <div>
        <div
          className="flex items-end gap-[3px] h-44"
          role="group"
          aria-label="Daily activity chart"
        >
          {view.activity_stripe.map(entry => (
            <StackedBar
              key={entry.date}
              entry={entry}
              ratio={logRatio(entry.total_sources)}
              hasDay={dayByDate.has(entry.date)}
              isExpanded={entry.date === currentDay}
              sectorTints={sectorTints}
              trackKey={trackKey}
              onClick={() => jumpToDay(entry.date)}
            />
          ))}
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
        <SectorLegend ranking={sectorRanking} />
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// CalendarDayPanel — single fixed-position content surface that swaps contents
// when the URL `?day=` changes. The chart above is the only day picker.
// Fade animation on day change; no vertical day list.
// ---------------------------------------------------------------------------

interface DayPanelProps {
  view: CalendarMonthView;
  defaultDay: string | null;
}

export function CalendarDayPanel({ view, defaultDay }: DayPanelProps) {
  const [currentDay, setCurrentDay] = useDayParam(defaultDay);
  const [showAll, setShowAll] = useState(false);

  // Reset "show all" toggle when the day changes
  useEffect(() => {
    setShowAll(false);
  }, [currentDay]);

  if (view.days.length === 0) {
    return (
      <div className="text-center py-16 text-dashboard-text-muted border border-dashed border-dashboard-border rounded-lg">
        No promoted topics for this month yet.
      </div>
    );
  }

  const dayIndex = view.days.findIndex(d => d.date === currentDay);
  const day = dayIndex >= 0 ? view.days[dayIndex] : null;
  const prevDay = dayIndex > 0 ? view.days[dayIndex - 1] : null;
  const nextDay = dayIndex >= 0 && dayIndex < view.days.length - 1 ? view.days[dayIndex + 1] : null;

  if (!day) {
    return (
      <div className="text-center py-16 text-dashboard-text-muted border border-dashed border-dashboard-border rounded-lg">
        Select a day on the chart above.
      </div>
    );
  }

  const shownClusters = showAll
    ? day.clusters
    : day.clusters.slice(0, INITIAL_EVENTS_SHOWN);
  const hiddenCount = day.clusters.length - shownClusters.length;

  // Swipe handlers: left = next day, right = prev day
  let touchStartX: number | null = null;
  let touchStartY: number | null = null;
  const onTouchStart = (e: React.TouchEvent) => {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
  };
  const onTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX === null || touchStartY === null) return;
    const dx = e.changedTouches[0].clientX - touchStartX;
    const dy = e.changedTouches[0].clientY - touchStartY;
    touchStartX = null;
    touchStartY = null;
    // Horizontal swipe must exceed 50px and dominate vertical movement
    if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy)) return;
    if (dx < 0 && nextDay) setCurrentDay(nextDay.date);
    else if (dx > 0 && prevDay) setCurrentDay(prevDay.date);
  };

  return (
    // `key` forces remount on day change so the fade-in animation replays.
    <div
      key={day.date}
      className="animate-day-fade touch-pan-y"
      onTouchStart={onTouchStart}
      onTouchEnd={onTouchEnd}
    >
      {/* Day nav: prev/next arrows flanking the current day heading.
          Also a visual affordance that the panel can be swiped on mobile. */}
      <div className="flex items-center justify-between gap-2 mb-5">
        <button
          type="button"
          onClick={() => prevDay && setCurrentDay(prevDay.date)}
          disabled={!prevDay}
          className="flex items-center gap-1 px-2 py-1 text-sm text-dashboard-text-muted hover:text-dashboard-text disabled:opacity-30 disabled:cursor-default transition whitespace-nowrap"
          aria-label={prevDay ? `Previous day: ${formatDayHeading(prevDay.date)}` : 'No earlier day'}
        >
          ‹<span className="hidden sm:inline">{prevDay ? ` ${formatDayHeading(prevDay.date)}` : ''}</span>
        </button>
        <h2 className="text-2xl font-semibold text-dashboard-text text-center min-w-0 truncate">
          {formatDayHeading(day.date)}
        </h2>
        <button
          type="button"
          onClick={() => nextDay && setCurrentDay(nextDay.date)}
          disabled={!nextDay}
          className="flex items-center gap-1 px-2 py-1 text-sm text-dashboard-text-muted hover:text-dashboard-text disabled:opacity-30 disabled:cursor-default transition whitespace-nowrap"
          aria-label={nextDay ? `Next day: ${formatDayHeading(nextDay.date)}` : 'No later day'}
        >
          <span className="hidden sm:inline">{nextDay ? `${formatDayHeading(nextDay.date)} ` : ''}</span>›
        </button>
      </div>
      <div className="sm:hidden text-center text-[10px] text-dashboard-text-muted -mt-3 mb-4">
        Swipe left or right for more days
      </div>

      {day.daily_brief && (
        <article className="mb-5 p-4 rounded-md border border-dashboard-border bg-dashboard-bg/70">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-blue-400 mb-2">
            Daily brief
          </div>
          <div className="text-[15px] leading-relaxed text-dashboard-text whitespace-pre-wrap">
            {day.daily_brief}
          </div>
        </article>
      )}

      <div className="space-y-2">
        {shownClusters.map(cluster => (
          <ClusterCardRow key={cluster.id} cluster={cluster} />
        ))}
      </div>

      {hiddenCount > 0 && (
        <button
          type="button"
          onClick={() => setShowAll(true)}
          className="mt-3 w-full py-2 text-sm text-dashboard-text-muted hover:text-dashboard-text border border-dashed border-dashboard-border rounded-lg hover:bg-dashboard-border/20 transition"
        >
          Show all {day.clusters.length} topics
        </button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// StackedBar — one day's vertical segmented column in the activity chart
// ---------------------------------------------------------------------------

function StackedBar({
  entry,
  ratio,
  hasDay,
  isExpanded,
  sectorTints,
  trackKey,
  onClick,
}: {
  entry: CalendarStripeEntry;
  ratio: number;
  hasDay: boolean;
  isExpanded: boolean;
  sectorTints: Map<string, string>;
  trackKey: string;
  onClick: () => void;
}) {
  if (!hasDay) {
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
  const total = entry.total_sources;
  const hasThemes = entry.themes.length > 0;

  const themesLine = hasThemes
    ? entry.themes
        .map(t => `${formatSector(t.sector)} (${formatSector(t.subject)}) ${Math.round(t.weight * 100)}%`)
        .join(' · ')
    : 'No theme breakdown';
  const tooltip = `${entry.date} · ${total} sources\n${themesLine}`;

  return (
    <button
      type="button"
      onClick={onClick}
      title={tooltip}
      className="flex-1 min-w-0 h-full flex flex-col justify-end items-stretch group p-0 cursor-pointer"
      aria-label={tooltip}
    >
      <div
        className={`relative w-full flex flex-col-reverse rounded-t-full overflow-hidden transition-all
          after:absolute after:inset-0 after:pointer-events-none
          after:bg-gradient-to-b after:from-white/15 after:via-transparent after:to-black/20
          ${isExpanded ? 'ring-2 ring-blue-400 ring-offset-1 ring-offset-dashboard-surface' : ''}`}
        style={{ height: `${heightPct}%` }}
      >
        {hasThemes ? (
          entry.themes.map((seg, idx) => (
            <div
              key={`${entry.date}-${idx}`}
              className={`${sectorTints.get(seg.sector) || DEFAULT_TINTS[DEFAULT_TINTS.length - 1]} group-hover:brightness-125 transition`}
              style={{ height: `${seg.weight * 100}%` }}
            />
          ))
        ) : (
          <div className={`${ghostTint(trackKey)} h-full w-full group-hover:brightness-125 transition`} />
        )}
      </div>
    </button>
  );
}

// ---------------------------------------------------------------------------
// SectorLegend — compact legend under the activity chart
//
// Aggregates theme weight × source count across the whole month, surfaces the
// top sectors so users can decode the bar colors. Each line: swatch + sector
// name + month-level share percentage.
// ---------------------------------------------------------------------------

function SectorLegend({ ranking }: { ranking: SectorRanking[] }) {
  if (ranking.length === 0) return null;
  return (
    <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] text-dashboard-text-muted">
      {ranking.map(({ sector, share, tint }) => (
        <div key={sector} className="flex items-center gap-1.5">
          <span className={`${tint} inline-block w-2.5 h-2.5 rounded-sm`} />
          <span className="text-dashboard-text">{formatSector(sector)}</span>
          <span className="tabular-nums">{Math.round(share * 100)}%</span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// ClusterCardRow — one event line inside an expanded day
//
// Two shapes:
// - Big cluster (has_event_page, >= 5 sources): title + small source count,
//   whole row clickable to /events/[id], mouseover tooltip "Read more on event page".
// - Small cluster (< 5 sources): title + inline list of source headlines, each
//   linking to the original publication (via ExternalLink leaving-site popup).
// ---------------------------------------------------------------------------

function ClusterCardRow({ cluster }: { cluster: CalendarClusterCard }) {
  const title = cluster.title || '(untitled topic)';

  if (cluster.has_event_page) {
    return (
      <Link
        href={`/events/${cluster.id}`}
        title="Read more on the topic page"
        className="block"
      >
        <div className="flex items-start gap-3 p-3 rounded-md border border-dashboard-border bg-dashboard-bg/50 hover:border-blue-500/50 hover:bg-dashboard-bg transition-colors">
          <div className="min-w-0 flex-1">
            <div className="text-[15px] leading-snug text-dashboard-text">{title}</div>
            <div className="mt-1 text-[11px] text-dashboard-text-muted tabular-nums">
              {cluster.source_count} sources
            </div>
          </div>
          <div className="shrink-0 text-dashboard-text-muted text-lg leading-none pt-0.5">
            ›
          </div>
        </div>
      </Link>
    );
  }

  // Small cluster: expose raw source headlines inline
  const sources = cluster.sources || [];
  return (
    <div className="p-3 rounded-md border border-dashboard-border bg-dashboard-bg/50">
      <div className="text-[15px] leading-snug text-dashboard-text mb-2">{title}</div>
      {sources.length > 0 && (
        <ul className="space-y-1.5 ml-1">
          {sources.map(src => (
            <SourceRow key={src.id} source={src} />
          ))}
        </ul>
      )}
    </div>
  );
}

function PublisherIcon({
  domain,
  publisher,
}: {
  domain: string | null;
  publisher: string;
}) {
  const [failed, setFailed] = useState(false);
  if (domain && !failed) {
    return (
      <img
        src={`https://www.google.com/s2/favicons?domain=${domain}&sz=64`}
        alt=""
        width={16}
        height={16}
        className="w-4 h-4 rounded-sm flex-shrink-0"
        onError={() => setFailed(true)}
      />
    );
  }
  // Fallback: initial-letter square
  return (
    <span className="w-4 h-4 rounded-sm bg-dashboard-border flex items-center justify-center text-[9px] text-dashboard-text-muted flex-shrink-0">
      {publisher.charAt(0).toUpperCase()}
    </span>
  );
}

function SourceRow({ source }: { source: CalendarClusterSource }) {
  const publisher = source.publisher_name || 'Unknown';
  const body = (
    <span className="flex items-start gap-2 text-[13px] leading-snug">
      <span className="shrink-0 mt-[3px]">
        <PublisherIcon domain={source.publisher_domain} publisher={publisher} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="text-dashboard-text-muted text-[11px] block">{publisher}</span>
        <span className="text-dashboard-text">{source.title_display}</span>
      </span>
    </span>
  );
  if (source.url) {
    return (
      <li>
        <ExternalLink href={source.url} className="block hover:text-blue-400 transition">
          {body}
        </ExternalLink>
      </li>
    );
  }
  return <li className="opacity-80">{body}</li>;
}

// ---------------------------------------------------------------------------
// CalendarScopeCard — sidebar info box
// ---------------------------------------------------------------------------

export function CalendarScopeCard({
  scope,
  trackLabel,
}: {
  scope: CalendarAnalysisScope;
  trackLabel: string;
}) {
  return (
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wider text-dashboard-text-muted mb-3">
        About this analysis
      </h3>
      <p className="text-sm leading-relaxed text-dashboard-text">
        We analyzed{' '}
        <strong className="text-blue-400 tabular-nums">
          {scope.total_sources.toLocaleString()}
        </strong>{' '}
        sources from{' '}
        <strong className="text-blue-400 tabular-nums">{scope.outlet_count}</strong>{' '}
        media outlets to automatically extract major day-by-day developments on the{' '}
        <span className="text-dashboard-text font-medium">{trackLabel}</span> track.
      </p>
      <div className="mt-4 pt-4 border-t border-dashboard-border text-[11px] text-dashboard-text-muted space-y-1.5">
        <div className="flex items-center justify-between">
          <span>Active days</span>
          <span className="tabular-nums text-dashboard-text">{scope.active_days}</span>
        </div>
        <div className="flex items-center justify-between">
          <span>Topics per day</span>
          <span className="text-dashboard-text">up to 20</span>
        </div>
      </div>
      <div className="mt-4 pt-4 border-t border-dashboard-border">
        <div className="text-[10px] uppercase tracking-wider text-dashboard-text-muted mb-2">
          Reading the chart
        </div>
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-dashboard-text-muted">
          <span className="w-3 h-3 rounded-sm bg-blue-500 inline-block" />
          <span>Top topic</span>
          <span className="w-3 h-3 rounded-sm bg-blue-500/40 ml-2 inline-block" />
          <span>Also covered</span>
          <span className="w-3 h-3 rounded-sm bg-slate-500/40 ml-2 inline-block" />
          <span>Tail</span>
        </div>
      </div>
    </div>
  );
}

// Default export is the hero (named export retained for symmetry). The page
// renders CalendarHero in topFullWidthContent and CalendarDayPanel as children.
export default CalendarHero;
