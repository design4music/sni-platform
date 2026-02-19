'use client';

import { useState } from 'react';
import { FramedNarrative, FrameStats } from '@/lib/types';

function MiniBar({ label, count, maxCount }: { label: string; count: number; maxCount: number }) {
  const pct = maxCount > 0 ? Math.round((count / maxCount) * 100) : 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 text-dashboard-text-muted truncate" title={label}>{label}</span>
      <div className="flex-1 h-1.5 bg-dashboard-border rounded-full overflow-hidden">
        <div className="h-full bg-blue-500/60 rounded-full" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-6 text-right text-dashboard-text-muted">{count}</span>
    </div>
  );
}

interface NarrativeOverlayProps {
  narrative: FramedNarrative;
  onClose: () => void;
}

function NarrativeOverlay({ narrative, onClose }: NarrativeOverlayProps) {
  // Frame-level stats from signal_stats JSONB
  const fs = narrative.signal_stats as unknown as FrameStats | null;
  const hasFrameStats = fs && fs.frame_title_count !== undefined;

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
              {hasFrameStats && fs.frame_pct > 0 && (
                <span className="ml-1">({fs.frame_pct}% of coverage)</span>
              )}
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

        <div className="p-4 space-y-5">
          {/* Moral Frame */}
          {narrative.moral_frame && (
            <div className="bg-dashboard-border/30 rounded-lg p-3">
              <p className="text-sm text-dashboard-text leading-relaxed">
                {narrative.moral_frame}
              </p>
            </div>
          )}

          {/* Description */}
          {narrative.description && (
            <p className="text-sm text-dashboard-text-muted leading-relaxed">
              {narrative.description}
            </p>
          )}

          {/* Frame-specific stats */}
          {hasFrameStats && (
            <>
              {/* Language Fingerprint */}
              {fs.frame_languages && Object.keys(fs.frame_languages).length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-2">
                    Language Profile
                  </h3>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(fs.frame_languages)
                      .sort((a, b) => b[1] - a[1])
                      .map(([lang, count]) => {
                        const pct = Math.round((count / fs.frame_title_count) * 100);
                        return (
                          <span
                            key={lang}
                            className="text-xs px-2 py-0.5 rounded bg-dashboard-border text-dashboard-text-muted"
                            title={`${count} headlines (${pct}%)`}
                          >
                            {lang.toUpperCase()} {pct}%
                          </span>
                        );
                      })}
                  </div>
                </div>
              )}

              {/* Publishers pushing this frame */}
              {fs.frame_publishers && fs.frame_publishers.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-2">
                    Who Pushes This Narrative
                  </h3>
                  <div className="space-y-1">
                    {fs.frame_publishers.slice(0, 8).map(p => (
                      <MiniBar
                        key={p.name}
                        label={p.name}
                        count={p.count}
                        maxCount={fs.frame_publishers[0].count}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Date span */}
              {fs.frame_date_first && fs.frame_date_last && (
                <div className="flex items-center gap-2 text-xs text-dashboard-text-muted">
                  <span className="font-semibold uppercase tracking-wide">Active</span>
                  <span>
                    {fs.frame_date_first === fs.frame_date_last
                      ? fs.frame_date_first
                      : `${fs.frame_date_first} - ${fs.frame_date_last}`}
                  </span>
                </div>
              )}
            </>
          )}

          {/* Legacy: top_sources if no frame stats */}
          {!hasFrameStats && narrative.top_sources && narrative.top_sources.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-2">
                Media Sources
              </h3>
              <div className="flex flex-wrap gap-1">
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

          {/* Sample Headlines */}
          {narrative.sample_titles && narrative.sample_titles.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-2">
                Sample Headlines
              </h3>
              <ul className="space-y-2">
                {narrative.sample_titles.slice(0, 7).map((sample, i) => (
                  <li key={i} className="text-sm flex items-start gap-2">
                    <span className="text-blue-400 mt-0.5 flex-shrink-0">-</span>
                    <div>
                      <span className="text-dashboard-text">{sample.title}</span>
                      <span className="text-dashboard-text-muted ml-2 text-xs">- {sample.publisher}</span>
                    </div>
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
  layout?: 'sidebar' | 'grid';
}

export default function NarrativeCards({ narratives, layout = 'sidebar' }: NarrativeCardsProps) {
  const [selectedNarrative, setSelectedNarrative] = useState<FramedNarrative | null>(null);

  if (narratives.length === 0) return null;

  const totalTitles = narratives.reduce((sum, n) => sum + n.title_count, 0);

  return (
    <>
      <div>
        <h3 className="text-lg font-semibold mb-2 text-dashboard-text">Narrative Frames</h3>
        <p className="text-xs text-dashboard-text-muted mb-3">
          {narratives.length} competing frames across {totalTitles} headlines.
        </p>
        <div className={layout === 'grid'
          ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3"
          : "space-y-3"
        }>
          {narratives.map((n) => {
            const fs = n.signal_stats as unknown as FrameStats | null;
            const pct = fs?.frame_pct;
            // Top language for inline hint
            const topLangs = fs?.frame_languages
              ? Object.entries(fs.frame_languages)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 3)
                  .map(([lang, count]) => {
                    const langPct = fs.frame_title_count > 0
                      ? Math.round((count / fs.frame_title_count) * 100)
                      : 0;
                    return `${lang.toUpperCase()} ${langPct}%`;
                  })
              : null;

            return (
              <button
                key={n.id}
                onClick={() => setSelectedNarrative(n)}
                className="w-full text-left p-3 rounded-lg border border-dashboard-border bg-dashboard-surface hover:border-blue-500/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h4 className="font-semibold text-sm">{n.label}</h4>
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-dashboard-border text-dashboard-text-muted">
                      {n.title_count}{pct !== undefined && pct > 0 ? ` (${pct}%)` : ''}
                    </span>
                  </div>
                </div>
                {n.moral_frame && (
                  <p className="text-xs text-dashboard-text-muted leading-relaxed mb-1.5 line-clamp-2">
                    {n.moral_frame}
                  </p>
                )}
                {/* Language hint */}
                {topLangs && topLangs.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {topLangs.map(l => (
                      <span key={l} className="text-[10px] px-1 py-0.5 rounded bg-dashboard-border/60 text-dashboard-text-muted">
                        {l}
                      </span>
                    ))}
                  </div>
                )}
              </button>
            );
          })}
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
