'use client';

import { useEffect, useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import type { CentroidDeviation } from '@/lib/queries';
import { DeviationItem } from './DeviationCard';

interface WeeklyDeviationCardProps {
  centroidId: string;
  initialMonth: string; // 'YYYY-MM'
  // Every ISO week (Monday-anchored) intersecting initialMonth, quiet
  // weeks included. Ordered oldest -> newest by the query.
  initialWeeks: CentroidDeviation[];
}

function weekSeverity(week: CentroidDeviation): 'quiet' | 'moderate' | 'high' {
  if (!week.deviations || week.deviations.length === 0) return 'quiet';
  let maxZ = 0;
  for (const d of week.deviations) {
    const z = d.z != null ? Math.abs(d.z) : 2.5;
    if (z > maxZ) maxZ = z;
  }
  if (maxZ > 3) return 'high';
  return 'moderate';
}

function markerClasses(severity: 'quiet' | 'moderate' | 'high', active: boolean): string {
  const base = 'flex-1 h-7 rounded border text-[10px] font-medium tabular-nums flex items-center justify-center transition cursor-pointer select-none min-w-0';
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

function formatMonthLong(month: string, loc: string): string {
  const [y, m] = month.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(loc === 'de' ? 'de-DE' : 'en-US', {
    month: 'long',
    year: 'numeric',
  });
}

function formatMonthShort(month: string, loc: string): string {
  const [y, m] = month.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(loc === 'de' ? 'de-DE' : 'en-US', {
    month: 'short',
  });
}

function shiftMonth(month: string, delta: number): string {
  const [y, m] = month.split('-').map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

function pickInitialIdx(weeks: CentroidDeviation[]): number {
  for (let i = weeks.length - 1; i >= 0; i--) {
    if (weeks[i].deviations && weeks[i].deviations!.length > 0) return i;
  }
  return Math.max(0, weeks.length - 1);
}

export default function WeeklyDeviationCard({
  centroidId,
  initialMonth,
  initialWeeks,
}: WeeklyDeviationCardProps) {
  const t = useTranslations('centroid');
  const locale = useLocale();

  const [month, setMonth] = useState<string>(initialMonth);
  const [weeks, setWeeks] = useState<CentroidDeviation[]>(initialWeeks);
  const [activeIdx, setActiveIdx] = useState<number>(pickInitialIdx(initialWeeks));
  const [loading, setLoading] = useState<boolean>(false);

  const prevMonth = shiftMonth(month, -1);
  const nextMonth = shiftMonth(month, 1);

  useEffect(() => {
    // Skip fetching the initial month — it came as props.
    if (month === initialMonth) {
      setWeeks(initialWeeks);
      setActiveIdx(pickInitialIdx(initialWeeks));
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetch(`/api/centroid/${encodeURIComponent(centroidId)}/deviations?month=${month}`)
      .then(r => r.json())
      .then((body: { weeks?: CentroidDeviation[] }) => {
        if (cancelled) return;
        const next = body.weeks || [];
        setWeeks(next);
        setActiveIdx(pickInitialIdx(next));
      })
      .catch(() => {
        if (cancelled) return;
        setWeeks([]);
        setActiveIdx(0);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [month, centroidId, initialMonth, initialWeeks]);

  const active = weeks[activeIdx];
  const anyFlags = weeks.some(w => w.deviations && w.deviations.length > 0);
  const borderColor = weeks.some(w => weekSeverity(w) === 'high')
    ? 'border-red-500/40'
    : weeks.some(w => weekSeverity(w) === 'moderate')
    ? 'border-amber-500/40'
    : 'border-dashboard-border';

  return (
    <div className={`bg-dashboard-surface border ${borderColor} rounded-lg p-4`}>
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider">
            {t('unusualActivity')}
          </h3>
          <p className="text-[11px] text-dashboard-text-muted mt-0.5">
            {formatMonthLong(month, locale)}
          </p>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            type="button"
            onClick={() => setMonth(prevMonth)}
            disabled={loading}
            className="px-2 py-1 text-[11px] text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition disabled:opacity-50"
            aria-label="Previous month"
          >
            ‹ {formatMonthShort(prevMonth, locale)}
          </button>
          <button
            type="button"
            onClick={() => setMonth(nextMonth)}
            disabled={loading}
            className="px-2 py-1 text-[11px] text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition disabled:opacity-50"
            aria-label="Next month"
          >
            {formatMonthShort(nextMonth, locale)} ›
          </button>
        </div>
      </div>

      {weeks.length === 0 ? (
        <p className="text-sm text-dashboard-text-muted italic">
          {loading
            ? (locale === 'de' ? 'Lade…' : 'Loading…')
            : (locale === 'de' ? 'Keine Basisdaten für diesen Monat.' : 'No baseline data for this month.')}
        </p>
      ) : (
        <>
          <div className={`flex gap-1.5 mb-3 ${loading ? 'opacity-60' : ''}`}>
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
            {active && t('comparedToBaseline', { week: formatWeekShort(active.week, locale) })}
          </p>
          {!active || !active.deviations || active.deviations.length === 0 ? (
            <p className="text-sm text-dashboard-text-muted italic">
              {locale === 'de' ? 'Keine Abweichungen diese Woche.' : 'No deviations this week.'}
              {!anyFlags && (
                <span className="block mt-1 text-[11px]">
                  {locale === 'de'
                    ? 'Alle Wochen dieses Monats sind ruhig.'
                    : 'All weeks this month are quiet.'}
                </span>
              )}
            </p>
          ) : (
            <div className="space-y-2">
              {active.deviations.map((d, i) => (
                <DeviationItem key={i} d={d} t={t} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
