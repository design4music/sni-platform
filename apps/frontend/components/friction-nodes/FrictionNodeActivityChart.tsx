'use client';

import { useEffect, useState } from 'react';
import { useLocale } from 'next-intl';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import type { NarrativeOnFn, NarrativeWeeklyPoint } from '@/lib/friction-nodes-shared';
import { colorForNarrative } from '@/lib/friction-nodes-shared';

interface Props {
  narratives: NarrativeOnFn[];
  weekly: NarrativeWeeklyPoint[];
  /** Tailwind height class (default h-64). */
  heightClass?: string;
  labels: {
    sectionTitle: string;
    sectionDescription: string;
    titles: string;
    noData: string;
  };
}

/**
 * Stacked area chart of weekly narrative activity for a friction node.
 *
 * Same visual rhythm as the StackedTrackAreaChart on centroid pages, but
 * each stacked layer is one narrative (coloured by display_order slot),
 * and bucketing is weekly across all available history rather than daily
 * within one month.
 *
 * Data shape comes from getFrictionNodeWeeklyActivity — pivots on the
 * server, so this component does no pivoting.
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

  if (!weekly.length || !narratives.length) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-bold mb-2">{labels.sectionTitle}</h2>
        <p className="text-sm text-dashboard-text-muted mb-4">{labels.noData}</p>
      </section>
    );
  }

  // Flatten counts.{narrative_id} → top-level keys for Recharts.
  const data = weekly.map((p) => ({ x: p.week, ...p.counts }));

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

  // Map narrative_id -> short label for tooltip + legend (use stance_label).
  const labelByNarrative = new Map(narratives.map((n) => [n.narrative_id, n.stance_label]));

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold mb-2">{labels.sectionTitle}</h2>
      <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl leading-snug">
        {labels.sectionDescription}
      </p>

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
                  fillOpacity={0.7}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Custom legend — narrative stance labels with their colour swatches. */}
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
    </section>
  );
}
