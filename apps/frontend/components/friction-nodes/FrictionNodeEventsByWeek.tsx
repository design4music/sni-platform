'use client';

import { useMemo, useState, useEffect } from 'react';
import { useLocale } from 'next-intl';
import Link from 'next/link';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { FnWeekBucket } from '@/lib/friction-nodes-shared';

interface Props {
  weeks: FnWeekBucket[];
  labels: {
    sectionTitle: string;
    sectionDescription: string;
    chartHelpText: string;
    weekOf: string;
    eventsThisWeek: string;
    moreThisWeek: string;
    sources: string;
    importance: string;
    none: string;
    selectAWeek: string;
    showAll: string;
  };
}

function formatWeekShort(weekStr: string, locale: string): string {
  const d = new Date(weekStr + 'T00:00:00');
  return d.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
    month: 'short',
    day: 'numeric',
  });
}

function formatWeekLong(weekStr: string, locale: string): string {
  const d = new Date(weekStr + 'T00:00:00');
  return d.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatEventDate(dateStr: string, locale: string): string {
  const d = new Date(dateStr + 'T12:00:00Z');
  return d.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function importanceBadge(score: number | null): { label: string; cls: string } | null {
  if (score == null) return null;
  if (score >= 0.5) return { label: 'high', cls: 'bg-amber-500/20 text-amber-300 border-amber-500/40' };
  return null;
}

/**
 * Combined event-volume bar chart + per-week events list. Bars in the
 * chart are clickable; clicking selects that week and the list updates.
 * Also offers an "All weeks" button that shows top events across the
 * full window (useful for the default view).
 */
export default function FrictionNodeEventsByWeek({ weeks, labels }: Props) {
  const locale = useLocale();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  // Default selection: the most recent week with >= 1 event.
  const initialWeek = useMemo(() => {
    for (let i = weeks.length - 1; i >= 0; i--) {
      if (weeks[i].total > 0) return weeks[i].week;
    }
    return null;
  }, [weeks]);

  // null means "All weeks" (cross-week aggregate).
  const [selectedWeek, setSelectedWeek] = useState<string | null>(initialWeek);

  if (!weeks.length) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-bold mb-2">{labels.sectionTitle}</h2>
        <p className="text-sm text-dashboard-text-muted italic">{labels.none}</p>
      </section>
    );
  }

  const data = weeks.map((w) => ({ x: w.week, count: w.total }));
  const totalEvents = weeks.reduce((acc, w) => acc + w.total, 0);

  // Build the displayed events list.
  // - selectedWeek = a week → that week's top events
  // - selectedWeek = null → top events across all weeks (sorted by source count)
  const allEvents = weeks.flatMap((w) => w.events);
  const allEventsSorted = [...allEvents].sort(
    (a, b) => (b.source_count ?? 0) - (a.source_count ?? 0),
  );
  const displayedEvents =
    selectedWeek == null
      ? allEventsSorted.slice(0, 12)
      : weeks.find((w) => w.week === selectedWeek)?.events ?? [];

  const selectedTotal =
    selectedWeek == null
      ? totalEvents
      : weeks.find((w) => w.week === selectedWeek)?.total ?? 0;

  const formatWeek = (raw: string) => formatWeekShort(raw, locale);
  const formatWeekTooltip = (raw: string) => formatWeekLong(raw, locale);

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold mb-2">{labels.sectionTitle}</h2>
      <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl leading-snug">
        {labels.sectionDescription}
      </p>

      {/* Bar chart — clickable */}
      <div className="w-full h-44 mb-2">
        {mounted && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{ top: 8, right: 8, bottom: 0, left: -20 }}
            >
              <XAxis
                dataKey="x"
                tickFormatter={formatWeek}
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
                minTickGap={28}
              />
              <YAxis
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                cursor={{ fill: '#3b82f6', fillOpacity: 0.1 }}
                labelFormatter={(raw) => formatWeekTooltip(String(raw))}
                formatter={(value) => [value as number, labels.eventsThisWeek]}
              />
              <Bar
                dataKey="count"
                radius={[2, 2, 0, 0]}
                onClick={(entry) => {
                  // Recharts passes the rectangle item; the original
                  // data point sits on .payload (or directly on entry
                  // depending on version).
                  const e = entry as unknown as { payload?: { x?: string }; x?: string };
                  const x = e?.payload?.x ?? (typeof e?.x === 'string' ? e.x : undefined);
                  if (x) setSelectedWeek(x);
                }}
                style={{ cursor: 'pointer' }}
              >
                {data.map((d) => (
                  <Cell
                    key={d.x}
                    fill={d.x === selectedWeek ? '#3b82f6' : '#475569'}
                    fillOpacity={d.x === selectedWeek ? 0.9 : 0.55}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <p className="text-[11px] text-dashboard-text-muted mb-4">{labels.chartHelpText}</p>

      {/* "All weeks" / current selection toggle */}
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <button
          type="button"
          onClick={() => setSelectedWeek(null)}
          className={`px-2.5 py-1 rounded-md text-xs transition border ${
            selectedWeek == null
              ? 'bg-blue-500 text-white border-blue-500 cursor-default font-medium'
              : 'bg-dashboard-surface border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text hover:border-blue-500/40'
          }`}
        >
          {labels.showAll}{' '}
          <span className="opacity-70 tabular-nums">({totalEvents})</span>
        </button>
        {selectedWeek && (
          <span className="text-sm text-dashboard-text-muted">
            <span className="text-dashboard-text font-medium">
              {labels.weekOf} {formatWeekLong(selectedWeek, locale)}
            </span>
            <span className="opacity-70 tabular-nums ml-2">({selectedTotal})</span>
          </span>
        )}
        {selectedWeek == null && (
          <span className="text-xs text-dashboard-text-muted italic">
            {labels.selectAWeek}
          </span>
        )}
      </div>

      {/* Events list */}
      {displayedEvents.length === 0 ? (
        <div className="text-sm text-dashboard-text-muted italic">{labels.none}</div>
      ) : (
        <div className="space-y-2">
          {displayedEvents.map((ev) => {
            const importance = importanceBadge(ev.importance);
            return (
              <Link
                key={ev.id}
                href={`/events/${ev.id}`}
                className="flex flex-col md:flex-row md:items-center gap-1 md:gap-3 px-4 py-3 rounded-lg bg-dashboard-surface border border-dashboard-border hover:border-blue-500/40 transition"
              >
                <span className="text-sm text-dashboard-text md:flex-1 md:min-w-0 leading-snug">
                  {ev.title}
                </span>
                <div className="flex items-center gap-2 shrink-0">
                  {importance && (
                    <span
                      className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border ${importance.cls}`}
                      title={`${labels.importance}: ${ev.importance?.toFixed(2)}`}
                    >
                      {importance.label}
                    </span>
                  )}
                  <span className="text-[11px] text-dashboard-text-muted tabular-nums">
                    {ev.source_count} {labels.sources}
                  </span>
                  <span className="text-[11px] text-dashboard-text-muted font-mono tabular-nums">
                    {formatEventDate(ev.date, locale)}
                  </span>
                </div>
              </Link>
            );
          })}
          {selectedWeek && selectedTotal > displayedEvents.length && (
            <p className="text-xs text-dashboard-text-muted italic pt-1">
              {labels.moreThisWeek.replace('{n}', String(selectedTotal - displayedEvents.length))}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
