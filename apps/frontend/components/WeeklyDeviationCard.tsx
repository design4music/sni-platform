'use client';

import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import type { CentroidDeviation } from '@/lib/queries';
import { DeviationItem } from './DeviationCard';

interface WeeklyDeviationCardProps {
  // Every ISO week (Monday-anchored) that intersects the displayed month,
  // quiet weeks included. Ordered oldest -> newest by the query.
  weeks: CentroidDeviation[];
}

// Severity derived from the strongest |z| in the week's flags; new_actor
// flags have no z and are treated as moderate.
function weekSeverity(week: CentroidDeviation): 'quiet' | 'moderate' | 'high' {
  if (!week.deviations || week.deviations.length === 0) return 'quiet';
  let maxZ = 0;
  for (const d of week.deviations) {
    const z = d.z != null ? Math.abs(d.z) : 2.5; // new_actor: moderate-equivalent
    if (z > maxZ) maxZ = z;
  }
  if (maxZ > 3) return 'high';
  return 'moderate';
}

function markerClasses(severity: 'quiet' | 'moderate' | 'high', active: boolean): string {
  const base = 'flex-1 h-7 rounded border text-[10px] font-medium tabular-nums flex items-center justify-center transition cursor-pointer select-none';
  const activeRing = active ? 'ring-2 ring-blue-400/60 ring-offset-1 ring-offset-dashboard-surface' : '';
  switch (severity) {
    case 'high':
      return `${base} ${activeRing} bg-red-500/20 border-red-500/60 text-red-300 hover:bg-red-500/30`;
    case 'moderate':
      return `${base} ${activeRing} bg-amber-500/15 border-amber-500/50 text-amber-300 hover:bg-amber-500/25`;
    case 'quiet':
      return `${base} ${activeRing} bg-dashboard-border/20 border-dashboard-border/60 text-dashboard-text-muted hover:bg-dashboard-border/30`;
  }
}

function formatWeekShort(week: string, loc: string): string {
  const d = new Date(week + 'T00:00:00');
  return d.toLocaleDateString(loc === 'de' ? 'de-DE' : 'en-US', { month: 'short', day: 'numeric' });
}

export default function WeeklyDeviationCard({ weeks }: WeeklyDeviationCardProps) {
  const t = useTranslations('centroid');
  const locale = useLocale();

  // Pick initial expanded week: latest flagged week if any, else latest overall.
  const initialIdx = (() => {
    for (let i = weeks.length - 1; i >= 0; i--) {
      if (weeks[i].deviations && weeks[i].deviations!.length > 0) return i;
    }
    return weeks.length - 1;
  })();
  const [activeIdx, setActiveIdx] = useState<number>(initialIdx);

  if (!weeks || weeks.length === 0) return null;

  const active = weeks[activeIdx];
  const activeSeverity = weekSeverity(active);
  const borderColor =
    weeks.some(w => weekSeverity(w) === 'high')
      ? 'border-red-500/40'
      : weeks.some(w => weekSeverity(w) === 'moderate')
      ? 'border-amber-500/40'
      : 'border-dashboard-border';

  return (
    <div className={`bg-dashboard-surface border ${borderColor} rounded-lg p-4`}>
      <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
        {t('unusualActivity')}
      </h3>
      <div className="flex gap-1.5 mb-3">
        {weeks.map((w, i) => {
          const sev = weekSeverity(w);
          return (
            <button
              key={w.week}
              type="button"
              onClick={() => setActiveIdx(i)}
              className={markerClasses(sev, i === activeIdx)}
              aria-label={`Week of ${w.week}`}
              title={formatWeekShort(w.week, locale)}
            >
              {formatWeekShort(w.week, locale)}
            </button>
          );
        })}
      </div>
      <p className="text-xs text-dashboard-text-muted mb-3">
        {t('comparedToBaseline', { week: formatWeekShort(active.week, locale) })}
      </p>
      {activeSeverity === 'quiet' || !active.deviations || active.deviations.length === 0 ? (
        <p className="text-sm text-dashboard-text-muted italic">
          {locale === 'de' ? 'Keine Abweichungen diese Woche.' : 'No deviations this week.'}
        </p>
      ) : (
        <div className="space-y-2">
          {active.deviations.map((d, i) => (
            <DeviationItem key={i} d={d} t={t} />
          ))}
        </div>
      )}
    </div>
  );
}
