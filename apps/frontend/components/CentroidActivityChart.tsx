'use client';

import { useMemo, useEffect, useState } from 'react';
import Link from 'next/link';
import { useLocale } from 'next-intl';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { CentroidMonthView } from '@/lib/types';

// Topic-mix area chart — lighter replacement for CentroidHero (calendar).
// Same data source (view.activity_stripe), same 4-track palette, same
// prev/next month nav. No day popover — drilling down to a specific
// track lives on the TrackCards already.

const TRACKS = ['geo_security', 'geo_politics', 'geo_economy', 'geo_society'] as const;
type Track = typeof TRACKS[number];

const TRACK_COLORS: Record<Track, string> = {
  geo_security: '#f87171', // red-400
  geo_politics: '#38bdf8', // sky-400
  geo_economy:  '#fbbf24', // amber-400
  geo_society:  '#34d399', // emerald-400
};

function trackLabel(track: Track, locale: string): string {
  const en: Record<Track, string> = {
    geo_security: 'Security',
    geo_politics: 'Politics',
    geo_economy: 'Economy',
    geo_society: 'Society',
  };
  const de: Record<Track, string> = {
    geo_security: 'Sicherheit',
    geo_politics: 'Politik',
    geo_economy: 'Wirtschaft',
    geo_society: 'Gesellschaft',
  };
  return (locale === 'de' ? de : en)[track];
}

function formatMonthLong(monthStr: string, locale: string): string {
  const [y, m] = monthStr.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
    month: 'long', year: 'numeric',
  });
}

function formatMonthShort(monthStr: string, locale: string): string {
  const [y, m] = monthStr.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', { month: 'short' });
}

function formatDayShort(dateStr: string): string {
  return parseInt(dateStr.split('-')[2], 10).toString();
}

interface Props {
  view: CentroidMonthView;
  centroidKey: string;
  activeMonth: string; // YYYY-MM
}

export default function CentroidActivityChart({ view, centroidKey, activeMonth }: Props) {
  const locale = useLocale();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  // Recharts wants flat objects { date, geo_security: N, ... } per day.
  // Stripe entries carry per-track *weights* (shares, sum~=1) rather than
  // raw counts; multiply by total_sources to recover the count.
  const data = useMemo(() => {
    return view.activity_stripe.map(entry => {
      const point: Record<string, string | number> = { date: entry.date };
      const weightByTrack = new Map(entry.tracks.map(t => [t.track, t.weight]));
      for (const track of TRACKS) {
        const w = weightByTrack.get(track) || 0;
        point[track] = Math.round(w * entry.total_sources);
      }
      return point;
    });
  }, [view.activity_stripe]);

  const baseUrl = `/c/${centroidKey}`;
  const prevMonth = view.prev_month;
  const nextMonth = view.next_month;

  return (
    <section>
      {/* Month header + prev/next nav. Matches CentroidHero's pattern. */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <h2 className="text-2xl lg:text-3xl font-semibold text-dashboard-text min-w-0">
          {formatMonthLong(activeMonth, locale)}
        </h2>
        <div className="flex items-center gap-1 shrink-0">
          {prevMonth ? (
            <Link
              href={`${baseUrl}?month=${prevMonth}`}
              className="px-2 py-1 text-xs text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition whitespace-nowrap"
              aria-label={`Previous month: ${formatMonthShort(prevMonth, locale)}`}
            >
              ‹ {formatMonthShort(prevMonth, locale)}
            </Link>
          ) : (
            <span className="px-2 py-1 text-xs text-dashboard-text-muted opacity-30 cursor-default whitespace-nowrap">‹</span>
          )}
          {nextMonth ? (
            <Link
              href={`${baseUrl}?month=${nextMonth}`}
              className="px-2 py-1 text-xs text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition whitespace-nowrap"
              aria-label={`Next month: ${formatMonthShort(nextMonth, locale)}`}
            >
              {formatMonthShort(nextMonth, locale)} ›
            </Link>
          ) : (
            <span className="px-2 py-1 text-xs text-dashboard-text-muted opacity-30 cursor-default whitespace-nowrap">›</span>
          )}
        </div>
      </div>

      {/* Chart. Recharts is client-only — render an empty box pre-mount to
          keep layout stable. */}
      <div className="w-full h-48">
        {mounted && (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
              <XAxis
                dataKey="date"
                tickFormatter={formatDayShort}
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
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
                labelFormatter={(label) => String(label)}
              />
              <Legend
                wrapperStyle={{ fontSize: 11, paddingTop: 4 }}
                iconType="square"
                formatter={(value: string) => trackLabel(value as Track, locale)}
              />
              {TRACKS.map(track => (
                <Area
                  key={track}
                  type="monotone"
                  dataKey={track}
                  stackId="1"
                  stroke={TRACK_COLORS[track]}
                  fill={TRACK_COLORS[track]}
                  fillOpacity={0.7}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  );
}
