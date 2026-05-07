'use client';

import { useEffect, useState, useMemo } from 'react';
import { useLocale } from 'next-intl';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import type { NarrativeOnFn, NarrativeWeeklyPoint } from '@/lib/friction-nodes-shared';
import { colorForNarrative } from '@/lib/friction-nodes-shared';

interface Props {
  narratives: NarrativeOnFn[];
  weekly: NarrativeWeeklyPoint[];
  heightClass?: string;
  labels: {
    sectionTitle?: string;
    sectionDescription?: string;
    titles: string;
    noData: string;
  };
}

/**
 * Stacked weekly area chart of per-narrative attributed-headline counts.
 * Pure interpretive layer — events live in a sibling component below
 * (FrictionNodeEventsByWeek) where they have their own bars + per-week
 * list and don't compete visually with the narrative colours.
 */
export default function FrictionNodeActivityChart({
  narratives,
  weekly,
  heightClass = 'h-64',
  labels,
}: Props) {
  const locale = useLocale();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const data = useMemo(() => {
    return weekly.map((p) => {
      const point: Record<string, string | number> = { x: p.week };
      for (const n of narratives) point[n.narrative_id] = p.counts[n.narrative_id] ?? 0;
      return point;
    });
  }, [weekly, narratives]);

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
            <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
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
                labelFormatter={(raw) => formatWeekFull(String(raw))}
                formatter={(value, name) => [
                  value as number,
                  labelByNarrative.get(String(name)) ?? String(name),
                ]}
              />
              {narratives.map((n) => (
                <Area
                  key={n.narrative_id}
                  type="monotone"
                  dataKey={n.narrative_id}
                  stackId="1"
                  stroke={colorForNarrative(n.display_order)}
                  fill={colorForNarrative(n.display_order)}
                  fillOpacity={0.75}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Legend — narratives only (events live in a sibling component below) */}
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
      </div>
    </div>
  );
}
