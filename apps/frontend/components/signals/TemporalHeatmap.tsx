'use client';

import Link from 'next/link';
import { useLocale } from 'next-intl';
import { SignalCategoryEntry, SignalType } from '@/lib/types';

const TYPE_COLORS: Record<SignalType, { base: string; bg: string }> = {
  persons:      { base: '96, 165, 250', bg: 'text-blue-400' },
  orgs:         { base: '74, 222, 128', bg: 'text-green-400' },
  places:       { base: '251, 146, 60', bg: 'text-orange-400' },
  commodities:  { base: '250, 204, 21', bg: 'text-yellow-400' },
  policies:     { base: '167, 139, 250', bg: 'text-purple-400' },
  systems:      { base: '34, 211, 238', bg: 'text-cyan-400' },
  named_events: { base: '244, 114, 182', bg: 'text-pink-400' },
};

interface Props {
  signals: SignalCategoryEntry[];
}

export default function TemporalHeatmap({ signals }: Props) {
  const locale = useLocale();
  const dateFmtLocale = locale === 'de' ? 'de-DE' : 'en-US';
  if (!signals || signals.length === 0) return null;

  // Collect all unique weeks, sorted
  const weekSet = new Set<string>();
  for (const s of signals) {
    for (const w of s.weekly) weekSet.add(w.week);
  }
  const weeks = Array.from(weekSet).sort();
  if (weeks.length === 0) return null;

  // Find global max for intensity scaling
  let globalMax = 1;
  for (const s of signals) {
    for (const w of s.weekly) {
      if (w.count > globalMax) globalMax = w.count;
    }
  }

  // Format week for header
  function fmtWeek(w: string) {
    const d = new Date(w);
    return d.toLocaleDateString(dateFmtLocale, { month: 'short', day: 'numeric' });
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr>
            <th className="text-left py-1 pr-3 text-dashboard-text-muted font-normal w-32">Signal</th>
            {weeks.map(w => (
              <th key={w} className="text-center py-1 px-1 text-dashboard-text-muted font-normal whitespace-nowrap">
                {fmtWeek(w)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {signals.map(s => {
            const countMap = new Map<string, number>();
            for (const w of s.weekly) countMap.set(w.week, w.count);
            const rgb = TYPE_COLORS[s.signal_type]?.base || '148, 163, 184';

            return (
              <tr key={`${s.signal_type}:${s.value}`} className="group">
                <td className="py-1 pr-3 truncate max-w-[8rem]">
                  <Link
                    href={`/signals/${s.signal_type}/${encodeURIComponent(s.value)}`}
                    className="text-dashboard-text hover:text-blue-400 transition"
                  >
                    {s.value}
                  </Link>
                </td>
                {weeks.map(w => {
                  const count = countMap.get(w) || 0;
                  const intensity = count / globalMax;
                  return (
                    <td key={w} className="py-1 px-1">
                      <div
                        className="w-full h-5 rounded-sm flex items-center justify-center"
                        style={{
                          backgroundColor: count > 0 ? `rgba(${rgb}, ${0.1 + intensity * 0.7})` : 'rgba(51, 65, 85, 0.3)',
                        }}
                        title={`${s.value}: ${count} events (${fmtWeek(w)})`}
                      >
                        {count > 0 && (
                          <span className="text-[10px] text-white/70">{count}</span>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
