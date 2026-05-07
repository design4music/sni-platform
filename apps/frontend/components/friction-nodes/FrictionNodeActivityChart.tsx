'use client';

import { useEffect, useState, useMemo } from 'react';
import { useLocale } from 'next-intl';
import {
  ComposedChart,
  Area,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type {
  NarrativeOnFn,
  NarrativeWeeklyPoint,
  FnEventVolumePoint,
} from '@/lib/friction-nodes-shared';
import { colorForNarrative } from '@/lib/friction-nodes-shared';

interface Props {
  narratives: NarrativeOnFn[];
  weekly: NarrativeWeeklyPoint[];
  eventVolume: FnEventVolumePoint[];
  heightClass?: string;
  labels: {
    sectionTitle?: string;
    sectionDescription?: string;
    titles: string;
    events: string;
    noData: string;
  };
}

/**
 * Combined activity chart: weekly events as background bars (FACTUAL layer)
 * + per-narrative attributed-headline counts as stacked colored areas
 * (INTERPRETIVE layer). Shared x-axis. Two y-axes (bars on the right
 * because event totals are typically larger than per-narrative title totals).
 */
export default function FrictionNodeActivityChart({
  narratives,
  weekly,
  eventVolume,
  heightClass = 'h-72',
  labels,
}: Props) {
  const locale = useLocale();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  // Merge per-week data: union of weeks across both sources, with
  // narrative counts and event_volume keyed onto each point.
  const data = useMemo(() => {
    const eventMap = new Map(eventVolume.map((p) => [p.week, p.count]));
    const narrativeMap = new Map(weekly.map((p) => [p.week, p.counts]));
    const allWeeks = new Set<string>([...eventMap.keys(), ...narrativeMap.keys()]);
    const sorted = Array.from(allWeeks).sort();
    return sorted.map((week) => {
      const counts = narrativeMap.get(week) ?? {};
      const point: Record<string, string | number> = {
        x: week,
        __events: eventMap.get(week) ?? 0,
      };
      for (const n of narratives) point[n.narrative_id] = counts[n.narrative_id] ?? 0;
      return point;
    });
  }, [eventVolume, weekly, narratives]);

  const labelByNarrative = useMemo(
    () => new Map(narratives.map((n) => [n.narrative_id, n.stance_label])),
    [narratives],
  );

  if (!data.length || !narratives.length) {
    return (
      <div className="mb-4">
        {labels.sectionTitle && (
          <h2 className="text-2xl font-bold mb-2">{labels.sectionTitle}</h2>
        )}
        <p className="text-sm text-dashboard-text-muted">{labels.noData}</p>
      </div>
    );
  }

  const formatWeek = (raw: string) =>
    new Date(raw).toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
      month: 'short',
      day: 'numeric',
    });

  const formatWeekFull = (raw: string) =>
    new Date(raw).toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });

  return (
    <div>
      {labels.sectionTitle && (
        <>
          <h2 className="text-2xl font-bold mb-2">{labels.sectionTitle}</h2>
          {labels.sectionDescription && (
            <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl leading-snug">
              {labels.sectionDescription}
            </p>
          )}
        </>
      )}

      <div className={`w-full ${heightClass}`}>
        {mounted && (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 8, right: 36, bottom: 0, left: -20 }}>
              <XAxis
                dataKey="x"
                tickFormatter={formatWeek}
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
                minTickGap={28}
              />
              {/* LEFT axis — narrative attribution counts (smaller scale) */}
              <YAxis
                yAxisId="left"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                allowDecimals={false}
              />
              {/* RIGHT axis — event volume (larger scale) */}
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fill: '#64748b', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                allowDecimals={false}
                width={28}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                labelFormatter={(raw) => formatWeekFull(String(raw))}
                formatter={(value, name) => {
                  if (name === '__events') {
                    return [value as number, labels.events];
                  }
                  return [
                    value as number,
                    labelByNarrative.get(String(name)) ?? String(name),
                  ];
                }}
              />
              {/* Background bars — events per week */}
              <Bar
                yAxisId="right"
                dataKey="__events"
                fill="#475569"
                fillOpacity={0.35}
                radius={[2, 2, 0, 0]}
              />
              {/* Foreground stacked areas — narrative attribution */}
              {narratives.map((n) => (
                <Area
                  key={n.narrative_id}
                  yAxisId="left"
                  type="monotone"
                  dataKey={n.narrative_id}
                  stackId="1"
                  stroke={colorForNarrative(n.display_order)}
                  fill={colorForNarrative(n.display_order)}
                  fillOpacity={0.75}
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Legend — narratives + the event-volume swatch */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 text-xs">
        {narratives.map((n) => (
          <span key={n.narrative_id} className="inline-flex items-center gap-1.5">
            <span
              className="w-3 h-3 rounded flex-shrink-0"
              style={{ backgroundColor: colorForNarrative(n.display_order), opacity: 0.85 }}
            />
            <span className="text-dashboard-text">{n.stance_label}</span>
            <span className="text-dashboard-text-muted tabular-nums">({n.match_count})</span>
          </span>
        ))}
        <span className="inline-flex items-center gap-1.5 ml-auto">
          <span
            aria-hidden
            className="w-3 h-3 rounded flex-shrink-0"
            style={{ backgroundColor: '#475569', opacity: 0.55 }}
          />
          <span className="text-dashboard-text-muted">{labels.events}</span>
        </span>
      </div>
    </div>
  );
}
