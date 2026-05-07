'use client';

import { useEffect, useState } from 'react';
import { useLocale } from 'next-intl';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import type { FnEventVolumePoint } from '@/lib/friction-nodes-shared';

interface Props {
  data: FnEventVolumePoint[];
  labels: {
    title: string;
    description: string;
    events: string;
    none: string;
  };
}

/**
 * Compact weekly bar strip showing event volume on the FN. Sits right
 * above the narrative-stack chart so the reader sees:
 *   FACTS (bars) — when stuff happened
 *   FRAMES (stacked area) — how it was framed
 * Same x-axis convention (weekly buckets) so the two read together.
 */
export default function FrictionNodeEventVolumeStrip({ data, labels }: Props) {
  const locale = useLocale();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!data.length) {
    return (
      <div className="text-xs text-dashboard-text-muted italic mb-3">{labels.none}</div>
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
    <div className="mb-3">
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-[11px] uppercase tracking-wider text-dashboard-text-muted">
          {labels.title}
        </span>
        <span className="text-[10px] text-dashboard-text-muted">{labels.description}</span>
      </div>
      <div className="w-full h-16">
        {mounted && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 2, right: 8, bottom: 0, left: -28 }}>
              <XAxis
                dataKey="week"
                tickFormatter={formatWeek}
                tick={{ fill: '#94a3b8', fontSize: 9 }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
                minTickGap={28}
              />
              <YAxis
                tick={{ fill: '#94a3b8', fontSize: 9 }}
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
                formatter={(value) => [value as number, labels.events]}
              />
              <Bar dataKey="count" fill="#94a3b8" fillOpacity={0.65} radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
