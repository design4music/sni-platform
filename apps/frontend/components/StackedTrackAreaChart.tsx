'use client';

import { useEffect, useState } from 'react';
import { useLocale } from 'next-intl';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

// Reusable stacked-area chart for the 4 strategic tracks.
// Used by both CentroidActivityChart (per-day within one month) and
// OutletTrackTimeline (per-month across many months). Caller provides
// flat data points keyed by 'x' (label) + per-track raw count fields.

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

export type StackedTrackPoint = {
  x: string;
  geo_security: number;
  geo_politics: number;
  geo_economy: number;
  geo_society: number;
};

/** xMode controls how the `x` value is rendered on axis ticks + tooltip
 *  headers. String preset (not a function prop) so server components can
 *  pass it through to this client component without serialisation issues. */
export type XMode = 'day' | 'month';

interface Props {
  data: StackedTrackPoint[];
  /** Default 'day' (formats YYYY-MM-DD as the day number). 'month'
   *  formats YYYY-MM as "Mon YYYY". */
  xMode?: XMode;
  /** Tailwind height class. Default: h-48 (192px). */
  heightClass?: string;
  /** Show the built-in Recharts legend. Default true. Set false when
   *  the parent provides its own legend (e.g. OutletTrackTimeline's
   *  "Lifetime" % swatches). */
  showLegend?: boolean;
}

function dayTick(raw: string): string {
  return parseInt(raw.split('-')[2], 10).toString();
}
function dayTooltip(raw: string): string {
  return raw;
}
function monthTick(raw: string, locale: string): string {
  const [y, m] = raw.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
    month: 'short', year: '2-digit',
  });
}
function monthTooltip(raw: string, locale: string): string {
  const [y, m] = raw.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
    month: 'short', year: 'numeric',
  });
}

export default function StackedTrackAreaChart({
  data,
  xMode = 'day',
  heightClass = 'h-48',
  showLegend = true,
}: Props) {
  const locale = useLocale();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const tickFmt = xMode === 'month'
    ? (raw: string) => monthTick(raw, locale)
    : dayTick;
  const tooltipFmt = xMode === 'month'
    ? (raw: string) => monthTooltip(raw, locale)
    : dayTooltip;

  return (
    <div>
      <div className={`w-full ${heightClass}`}>
        {mounted && (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
              <XAxis
                dataKey="x"
                tickFormatter={tickFmt}
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
                labelFormatter={(raw) => tooltipFmt(String(raw))}
                formatter={(value, name) => [value as number, trackLabel(String(name) as Track, locale)]}
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

      {/* Custom legend — matches the outlet-page "Lifetime %" legend style
          (rounded swatches, white labels). Drops the default Recharts plain
          square swatches. */}
      {showLegend && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 text-xs">
          {TRACKS.map(track => (
            <span key={track} className="inline-flex items-center gap-1.5">
              <span
                className="w-3 h-3 rounded flex-shrink-0"
                style={{ backgroundColor: TRACK_COLORS[track], opacity: 0.85 }}
              />
              <span className="text-dashboard-text">{trackLabel(track, locale)}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
