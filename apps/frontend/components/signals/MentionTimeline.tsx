'use client';

import { useState, useEffect } from 'react';
import { useLocale, useTranslations } from 'next-intl';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface Props {
  weekly: { week: string; count: number }[];
}

export default function MentionTimeline({ weekly }: Props) {
  const locale = useLocale();
  const tCommon = useTranslations('common');
  const dateFmtLocale = locale === 'de' ? 'de-DE' : 'en-US';
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  function formatWeek(w: string) {
    const d = new Date(w);
    return d.toLocaleDateString(dateFmtLocale, { month: 'short', day: 'numeric' });
  }

  if (!weekly || weekly.length === 0) return null;
  if (!mounted) return <div className="w-full h-56" />;

  return (
    <div className="w-full h-56">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={weekly} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
          <defs>
            <linearGradient id="mentionFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="week"
            tickFormatter={formatWeek}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
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
            labelFormatter={(label) => formatWeek(String(label))}
            formatter={(value) => [value, tCommon('events')]}
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="url(#mentionFill)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
