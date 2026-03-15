'use client';

import { useTranslations } from 'next-intl';
import type { DeviationFlag } from '@/lib/queries';

interface DeviationCardProps {
  week: string;
  deviations: DeviationFlag[];
}

function getSeverity(z: number | undefined): 'high' | 'moderate' {
  if (z && Math.abs(z) > 3) return 'high';
  return 'moderate';
}

function getBorderColor(deviations: DeviationFlag[]): string {
  const hasHigh = deviations.some(d => d.z != null && Math.abs(d.z) > 3);
  return hasHigh ? 'border-red-500/60' : 'border-amber-500/60';
}

function formatMultiplier(current: number, baseline: number): string {
  if (baseline === 0) return '';
  const ratio = current / baseline;
  if (ratio >= 2) return Math.round(ratio) + 'x';
  if (ratio >= 1.3) return ratio.toFixed(1) + 'x';
  if (ratio <= 0.5) return Math.round((1 / ratio)) + 'x fewer';
  return '';
}

function DeviationItem({ d, t }: { d: DeviationFlag; t: (key: string, values?: Record<string, string>) => string }) {
  const severity = getSeverity(d.z);
  const dotColor = severity === 'high' ? 'bg-red-400' : 'bg-amber-400';

  if (d.type === 'new_actor') {
    const actor = (d.actor || '').replace(/_/g, ' ');
    return (
      <div className="flex items-start gap-2">
        <span className={`mt-1.5 w-1.5 h-1.5 rounded-full ${dotColor} shrink-0`} />
        <span className="text-sm text-dashboard-text">
          {t('deviationNewActor', { actor })}
        </span>
      </div>
    );
  }

  if (d.type === 'event_count_spike' && d.current != null && d.baseline_mean != null) {
    const mult = formatMultiplier(d.current, d.baseline_mean);
    return (
      <div className="flex items-start gap-2">
        <span className={`mt-1.5 w-1.5 h-1.5 rounded-full ${dotColor} shrink-0`} />
        <span className="text-sm text-dashboard-text">
          {t('deviationEventSpike', { count: String(d.current), mult, avg: String(Math.round(d.baseline_mean)) })}
        </span>
      </div>
    );
  }

  if (d.type === 'event_count_drop' && d.current != null && d.baseline_mean != null) {
    const mult = formatMultiplier(d.baseline_mean, d.current);
    return (
      <div className="flex items-start gap-2">
        <span className={`mt-1.5 w-1.5 h-1.5 rounded-full ${dotColor} shrink-0`} />
        <span className="text-sm text-dashboard-text">
          {t('deviationEventDrop', { count: String(d.current), mult, avg: String(Math.round(d.baseline_mean)) })}
        </span>
      </div>
    );
  }

  if (d.type === 'importance_surge') return null;

  if (d.type === 'polarity_shift' && d.current != null && d.baseline_mean != null) {
    const nowCoop = Math.round(d.current * 100);
    const wasCoop = Math.round(d.baseline_mean * 100);
    return (
      <div className="flex items-start gap-2">
        <span className={`mt-1.5 w-1.5 h-1.5 rounded-full ${dotColor} shrink-0`} />
        <span className="text-sm text-dashboard-text">
          {t('deviationPolarity', { now: String(nowCoop), was: String(wasCoop) })}
        </span>
      </div>
    );
  }

  return null;
}

function formatWeek(week: string): string {
  const d = new Date(week + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export default function DeviationCard({ week, deviations }: DeviationCardProps) {
  const t = useTranslations('centroid');

  if (!deviations || deviations.length === 0) return null;

  return (
    <div className={`bg-dashboard-surface border ${getBorderColor(deviations)} rounded-lg p-4`}>
      <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-1">
        {t('unusualActivity')}
      </h3>
      <p className="text-xs text-dashboard-text-muted mb-3">
        {t('comparedToBaseline', { week: formatWeek(week) })}
      </p>
      <div className="space-y-2">
        {deviations.map((d, i) => (
          <DeviationItem key={i} d={d} t={t} />
        ))}
      </div>
    </div>
  );
}
