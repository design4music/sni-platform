'use client';

import { useState } from 'react';
import { FramedNarrative } from '@/lib/types';

interface ScoreBarProps {
  label: string;
  value: number | undefined;
  color?: string;
}

function ScoreBar({ label, value, color = 'blue' }: ScoreBarProps) {
  if (value === undefined || value === null) return null;
  const percent = Math.round(value * 100);
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
    purple: 'bg-purple-500',
  };
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-20 text-dashboard-text-muted">{label}</span>
      <div className="flex-1 h-2 bg-dashboard-border rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClasses[color as keyof typeof colorClasses] || 'bg-blue-500'}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="w-8 text-right text-dashboard-text">{percent}%</span>
    </div>
  );
}

interface NarrativeOverlayProps {
  narrative: FramedNarrative;
  onClose: () => void;
}

function NarrativeOverlay({ narrative, onClose }: NarrativeOverlayProps) {
  const shifts = narrative.rai_shifts;
  const hasRai = narrative.rai_analyzed_at !== null;

  return (
    <div
      className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-dashboard-surface border border-dashboard-border rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-dashboard-surface border-b border-dashboard-border p-4 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">{narrative.label}</h2>
            <p className="text-sm text-dashboard-text-muted">
              {narrative.title_count} headlines
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-dashboard-text-muted hover:text-dashboard-text p-1"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-4 space-y-6">
          {/* Moral Frame */}
          {narrative.moral_frame && (
            <div>
              <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wide mb-2">
                Narrative Frame
              </h3>
              <p className="text-sm text-dashboard-text leading-relaxed">
                {narrative.moral_frame}
              </p>
            </div>
          )}

          {/* Sources */}
          {(narrative.top_sources?.length || narrative.proportional_sources?.length) && (
            <div>
              <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wide mb-2">
                Media Sources
              </h3>
              <div className="space-y-2">
                {narrative.top_sources && narrative.top_sources.length > 0 && (
                  <div>
                    <span className="text-xs text-dashboard-text-muted mr-2">Favors this frame:</span>
                    <div className="inline-flex flex-wrap gap-1 mt-1">
                      {narrative.top_sources.map((src, i) => (
                        <span
                          key={i}
                          className="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20"
                        >
                          {src}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {narrative.proportional_sources && narrative.proportional_sources.length > 0 && (
                  <div>
                    <span className="text-xs text-dashboard-text-muted mr-2">Broad coverage:</span>
                    <div className="inline-flex flex-wrap gap-1 mt-1">
                      {narrative.proportional_sources.map((src, i) => (
                        <span
                          key={i}
                          className="text-xs px-2 py-0.5 rounded bg-gray-500/10 text-gray-400 border border-gray-500/20"
                        >
                          {src}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* RAI Analysis Section */}
          {hasRai ? (
            <>
              <div className="border-t border-dashboard-border pt-4">
                <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wide mb-3">
                  RAI Analysis
                </h3>

                {/* Score Bars */}
                {shifts && (
                  <div className="space-y-2 mb-4">
                    <ScoreBar label="Overall" value={shifts.overall_score} color="blue" />
                    <ScoreBar label="Credibility" value={shifts.credibility_score} color="green" />
                    <ScoreBar label="Evidence" value={shifts.evidence_quality} color="green" />
                    <ScoreBar label="Coherence" value={shifts.coherence_score} color="purple" />
                    <ScoreBar label="Bias" value={shifts.bias_score} color="yellow" />
                  </div>
                )}
              </div>

              {/* Synthesis */}
              {narrative.rai_synthesis && (
                <div>
                  <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-2">
                    Synthesis
                  </h4>
                  <p className="text-sm text-dashboard-text leading-relaxed">
                    {narrative.rai_synthesis}
                  </p>
                </div>
              )}

              {/* Conflicts */}
              {narrative.rai_conflicts && narrative.rai_conflicts.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-2">
                    Detected Conflicts
                  </h4>
                  <ul className="space-y-1">
                    {narrative.rai_conflicts.map((conflict, i) => (
                      <li key={i} className="text-sm text-dashboard-text-muted flex items-start gap-2">
                        <span className="text-yellow-500 mt-0.5">!</span>
                        <span>{conflict}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Blind Spots */}
              {narrative.rai_blind_spots && narrative.rai_blind_spots.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-2">
                    Blind Spots
                  </h4>
                  <ul className="space-y-1">
                    {narrative.rai_blind_spots.map((spot, i) => (
                      <li key={i} className="text-sm text-dashboard-text-muted flex items-start gap-2">
                        <span className="text-orange-500 mt-0.5">?</span>
                        <span>{spot}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Full RAI Analysis (Expandable) */}
              {narrative.rai_full_analysis && (
                <details className="border-t border-dashboard-border pt-4">
                  <summary className="cursor-pointer text-sm font-semibold text-blue-400 hover:text-blue-300">
                    View Full Analysis Report
                  </summary>
                  <div
                    className="mt-3 text-sm text-dashboard-text-muted leading-relaxed
                               [&_h1]:text-lg [&_h1]:font-semibold [&_h1]:text-dashboard-text [&_h1]:mt-4 [&_h1]:mb-2
                               [&_h2]:text-base [&_h2]:font-semibold [&_h2]:text-dashboard-text [&_h2]:mt-3 [&_h2]:mb-2
                               [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:text-dashboard-text [&_h3]:mt-2 [&_h3]:mb-1
                               [&_p]:my-2 [&_strong]:text-dashboard-text
                               [&_ul]:my-2 [&_ul]:ml-4 [&_ul]:list-disc
                               [&_ol]:my-2 [&_ol]:ml-4 [&_ol]:list-decimal
                               [&_li]:my-1"
                    dangerouslySetInnerHTML={{ __html: narrative.rai_full_analysis }}
                  />
                </details>
              )}
            </>
          ) : (
            <div className="border-t border-dashboard-border pt-4">
              <p className="text-sm text-dashboard-text-muted italic">
                RAI analysis not yet available for this narrative.
              </p>
            </div>
          )}

          {/* Sample Headlines */}
          {narrative.sample_titles && narrative.sample_titles.length > 0 && (
            <div className="border-t border-dashboard-border pt-4">
              <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wide mb-2">
                Sample Headlines
              </h3>
              <ul className="space-y-2">
                {narrative.sample_titles.slice(0, 5).map((sample, i) => (
                  <li key={i} className="text-sm">
                    <span className="text-dashboard-text">{sample.title}</span>
                    <span className="text-dashboard-text-muted ml-2">- {sample.publisher}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface NarrativeCardsProps {
  narratives: FramedNarrative[];
}

export default function NarrativeCards({ narratives }: NarrativeCardsProps) {
  const [selectedNarrative, setSelectedNarrative] = useState<FramedNarrative | null>(null);

  if (narratives.length === 0) return null;

  return (
    <>
      <div>
        <h3 className="text-lg font-semibold mb-2 text-dashboard-text">How It Was Framed</h3>
        <p className="text-xs text-dashboard-text-muted mb-3">
          Contested narratives from {narratives.reduce((sum, n) => sum + n.title_count, 0)} headlines.
          Click for analysis.
        </p>
        <div className="space-y-3">
          {narratives.map((n) => (
            <button
              key={n.id}
              onClick={() => setSelectedNarrative(n)}
              className="w-full text-left p-3 rounded-lg border border-dashboard-border bg-dashboard-surface hover:border-blue-500/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <h4 className="font-semibold text-sm">{n.label}</h4>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  {n.rai_analyzed_at && (
                    <span
                      className="w-2 h-2 rounded-full bg-green-500"
                      title="RAI analyzed"
                    />
                  )}
                  <span className="text-xs px-1.5 py-0.5 rounded bg-dashboard-border text-dashboard-text-muted">
                    {n.title_count}
                  </span>
                </div>
              </div>
              {n.moral_frame && (
                <p className="text-xs text-dashboard-text-muted leading-relaxed mb-2 line-clamp-2">
                  {n.moral_frame}
                </p>
              )}
              {/* Over-indexed sources */}
              {n.top_sources && n.top_sources.length > 0 && (
                <div className="mb-1">
                  <span className="text-xs text-dashboard-text-muted mr-1">Favored by:</span>
                  <span className="text-xs text-blue-400">
                    {n.top_sources.slice(0, 2).join(', ')}
                    {n.top_sources.length > 2 && ` +${n.top_sources.length - 2}`}
                  </span>
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Overlay */}
      {selectedNarrative && (
        <NarrativeOverlay
          narrative={selectedNarrative}
          onClose={() => setSelectedNarrative(null)}
        />
      )}
    </>
  );
}
