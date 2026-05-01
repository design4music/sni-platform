'use client';

import { useEffect, useState } from 'react';
import { useLocale } from 'next-intl';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

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

interface Props {
  data: StackedTrackPoint[];
  /** Format the x-axis tick label from the raw `x` value. Default: identity. */
  xTickFormatter?: (raw: string) => string;
  /** Format the tooltip label (header) from the raw `x` value. Default: identity. */
  xTooltipFormatter?: (raw: string) => string;
  /** Tailwind height class. Default: h-48 (192px). */
  heightClass?: string;
}

export default function StackedTrackAreaChart({
  data,
  xTickFormatter,
  xTooltipFormatter,
  heightClass = 'h-48',
}: Props) {
  const locale = useLocale();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <div className={`w-full ${heightClass}`}>
      {mounted && (
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
            <XAxis
              dataKey="x"
              tickFormatter={xTickFormatter}
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
              labelFormatter={(raw) => xTooltipFormatter ? xTooltipFormatter(String(raw)) : String(raw)}
              formatter={(value, name) => [value as number, trackLabel(String(name) as Track, locale)]}
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
  );
}
