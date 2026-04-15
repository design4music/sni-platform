'use client';

import { useMemo, useEffect, useRef, useCallback, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import ExternalLink from './ExternalLink';
import { PublisherFavicon } from './ExpandableTitles';
import type {
  CalendarMonthView,
  CalendarDayView,
  CalendarClusterCard,
  CalendarClusterSource,
  CalendarStripeEntry,
  CalendarAnalysisScope,
} from '@/lib/types';

const INITIAL_EVENTS_SHOWN = 3; // top-N events shown per day before "Show all"

// Tailwind palette for stack segments: top cluster strongest, decaying, "other" muted
const SEGMENT_COLORS = [
  'bg-blue-500',
  'bg-blue-500/75',
  'bg-blue-500/55',
  'bg-blue-500/40',
  'bg-blue-500/25',
];
const OTHER_COLOR = 'bg-slate-500/40';

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

function pickDefaultDay(view: CalendarMonthView, explicit: string | null): string | null {
  if (explicit && view.days.some(d => d.date === explicit)) return explicit;
  if (view.days.length === 0) return null;
  return view.days.reduce((best, d) => (d.total_sources > best.total_sources ? d : best)).date;
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

  const jumpToDay = (date: string) => {
    if (!dayByDate.has(date)) return;
    setCurrentDay(date);
    // Let the router update settle, then scroll
    setTimeout(() => {
      const el = document.getElementById(`day-${date}`);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 80);
  };

  const baseUrl = `/c/${centroidKey}/t/${trackKey}/calendar`;

  return (
    <section className="border border-dashboard-border bg-dashboard-surface rounded-xl overflow-hidden">
      {/* Header row: breadcrumb + month nav */}
      <div className="flex items-start justify-between gap-4 px-6 pt-6 pb-5">
        <div className="min-w-0">
          <div className="text-[11px] uppercase tracking-wider text-dashboard-text-muted">
            {centroidLabel}
          </div>
          <h1 className="text-2xl lg:text-3xl font-semibold text-dashboard-text mt-1">
            {trackLabel}
            <span className="text-dashboard-text-muted font-normal">
              {' · '}
              {formatMonthLong(activeMonth)}
            </span>
          </h1>
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
      <div className="px-6 pb-6">
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
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// CalendarDayStream — vertical day list in the main content column
// ---------------------------------------------------------------------------

interface DayStreamProps {
  view: CalendarMonthView;
  defaultDay: string | null;
}

export function CalendarDayStream({ view, defaultDay }: DayStreamProps) {
  const [currentDay, setCurrentDay] = useDayParam(defaultDay);
  const dayRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const [showAllByDay, setShowAllByDay] = useState<Record<string, boolean>>({});

  // Align a day card to the top of the viewport with a fixed header offset.
  // scroll-mt-28 on the card handles the gap; scrollIntoView does the work.
  const scrollToDay = useCallback((date: string) => {
    const el = dayRefs.current[date];
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, []);

  // Smooth-scroll to initial day on mount
  useEffect(() => {
    if (!currentDay) return;
    scrollToDay(currentDay);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Also scroll when the URL-driven currentDay changes (e.g. chart click)
  const lastScrolledRef = useRef<string | null>(null);
  useEffect(() => {
    if (!currentDay || currentDay === lastScrolledRef.current) return;
    lastScrolledRef.current = currentDay;
    // Defer to let the expand render
    setTimeout(() => scrollToDay(currentDay), 30);
  }, [currentDay, scrollToDay]);

  if (view.days.length === 0) {
    return (
      <div className="text-center py-16 text-dashboard-text-muted border border-dashed border-dashboard-border rounded-lg">
        No promoted topics for this month yet.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {view.days.map(day => {
        const isExpanded = day.date === currentDay;
        const showAll = !!showAllByDay[day.date];
        const shownClusters = showAll
          ? day.clusters
          : day.clusters.slice(0, INITIAL_EVENTS_SHOWN);
        const hiddenCount = day.clusters.length - shownClusters.length;
        return (
          <div
            key={day.date}
            id={`day-${day.date}`}
            ref={el => {
              dayRefs.current[day.date] = el;
            }}
            className={`scroll-mt-28 rounded-lg border transition-colors ${
              isExpanded
                ? 'border-blue-500/50 bg-dashboard-surface'
                : 'border-dashboard-border bg-dashboard-surface/60 hover:bg-dashboard-surface'
            }`}
          >
            <button
              type="button"
              onClick={() => {
                if (isExpanded) {
                  setCurrentDay('');
                } else {
                  setCurrentDay(day.date);
                  // Ensure the expanded card snaps to top
                  setTimeout(() => scrollToDay(day.date), 30);
                }
              }}
              className="w-full flex items-center gap-3 px-5 py-4 text-left"
            >
              <span className="text-dashboard-text-muted text-sm w-4">
                {isExpanded ? '▾' : '▸'}
              </span>
              <span className="font-semibold text-dashboard-text">
                {formatDayHeading(day.date)}
              </span>
            </button>

            {isExpanded && (
              <div className="px-5 pb-5 pt-1 space-y-4">
                {day.daily_brief && (
                  <article className="p-4 rounded-md border border-dashboard-border bg-dashboard-bg/70">
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
                    onClick={() =>
                      setShowAllByDay(s => ({ ...s, [day.date]: true }))
                    }
                    className="w-full py-2 text-sm text-dashboard-text-muted hover:text-dashboard-text border border-dashed border-dashboard-border rounded-lg hover:bg-dashboard-border/20 transition"
                  >
                    Show all {day.clusters.length} topics
                  </button>
                )}
              </div>
            )}
          </div>
        );
      })}
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
  onClick,
}: {
  entry: CalendarStripeEntry;
  ratio: number;
  hasDay: boolean;
  isExpanded: boolean;
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
  const topTitle = entry.segments[0]?.title || '';
  const tooltip = `${entry.date} · ${total} sources${topTitle ? `\nTop: ${topTitle}` : ''}`;

  return (
    <button
      type="button"
      onClick={onClick}
      title={tooltip}
      className="flex-1 min-w-0 h-full flex flex-col justify-end items-stretch group p-0 cursor-pointer"
      aria-label={tooltip}
    >
      <div
        className={`w-full flex flex-col-reverse rounded-sm overflow-hidden transition-all ${
          isExpanded ? 'ring-2 ring-blue-400 ring-offset-1 ring-offset-dashboard-surface' : ''
        }`}
        style={{ height: `${heightPct}%` }}
      >
        {entry.segments.map((seg, idx) => {
          const segRatio = seg.source_count / Math.max(1, total);
          const isOther = seg.cluster_id === null;
          const colorClass = isOther
            ? OTHER_COLOR
            : SEGMENT_COLORS[Math.min(idx, SEGMENT_COLORS.length - 1)];
          return (
            <div
              key={`${entry.date}-${idx}`}
              className={`${colorClass} group-hover:brightness-110 transition`}
              style={{ height: `${Math.max(2, segRatio * 100)}%` }}
            />
          );
        })}
      </div>
    </button>
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

function SourceRow({ source }: { source: CalendarClusterSource }) {
  const publisher = source.publisher_name || 'Unknown';
  const body = (
    <span className="flex items-start gap-2 text-[13px] leading-snug">
      <span className="shrink-0 mt-[1px]">
        <PublisherFavicon publisher={publisher} />
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
    <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-5">
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

// ---------------------------------------------------------------------------
// Back-compat default export: used to be the whole thing. Now it just renders
// hero + day stream together (for callers that render inside max-w-3xl main).
// ---------------------------------------------------------------------------

interface LegacyProps extends HeroProps {
  initialDay?: string;
}

export default function CalendarView(props: LegacyProps) {
  const defaultDay = pickDefaultDay(props.view, props.initialDay || null);
  return (
    <>
      <CalendarHero {...props} defaultDay={defaultDay} />
      <div className="mt-8">
        <CalendarDayStream view={props.view} defaultDay={defaultDay} />
      </div>
    </>
  );
}

// Exported utility for the page to compute default day server-side
export { pickDefaultDay };
