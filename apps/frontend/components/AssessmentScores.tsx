'use client';

import { useState, useEffect } from 'react';

interface Shifts {
  overall_score?: number;
  bias_score?: number;
  coherence_score?: number;
  credibility_score?: number;
  evidence_quality?: number;
  relevance_score?: number;
  safety_score?: number;
  [key: string]: number | undefined;
}

interface Props {
  initialAdequacy: number | null;
  initialShifts: Shifts | null;
}

export default function AssessmentScores({ initialAdequacy, initialShifts }: Props) {
  const [adequacy, setAdequacy] = useState<number | null>(initialAdequacy);
  const [shifts, setShifts] = useState<Shifts | null>(initialShifts);

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail.adequacy != null) setAdequacy(detail.adequacy);
      if (detail.shifts) setShifts(detail.shifts);
    };
    window.addEventListener('rai-scores-updated', handler);
    return () => window.removeEventListener('rai-scores-updated', handler);
  }, []);

  if (adequacy == null && !shifts) return null;

  return (
    <div className="bg-dashboard-border/30 rounded-lg p-4 space-y-3">
      <h3 className="text-sm font-semibold text-dashboard-text">Assessment Scores</h3>

      {adequacy != null && (
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-dashboard-text-muted">Adequacy</span>
            <span className="text-xs font-medium">{Math.round(adequacy * 100)}%</span>
          </div>
          <div className="h-1.5 bg-dashboard-border rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                adequacy >= 0.7 ? 'bg-green-500' : adequacy >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${Math.round(adequacy * 100)}%` }}
            />
          </div>
        </div>
      )}

      {shifts && Object.entries(shifts)
        .filter(([k]) => !['overall_score', 'adequacy'].includes(k))
        .map(([key, val]) => {
          if (typeof val !== 'number') return null;
          const label = key.replace(/_score$/, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
          const pct = Math.round(val * 100);
          return (
            <div key={key}>
              <div className="flex justify-between text-xs mb-0.5">
                <span className="text-dashboard-text-muted">{label}</span>
                <span>{pct}%</span>
              </div>
              <div className="h-1.5 bg-dashboard-border rounded-full overflow-hidden">
                <div className="h-full bg-blue-500/60 rounded-full" style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
    </div>
  );
}
