'use client';

import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { FramedNarrative, FrameStats } from '@/lib/types';

interface NarrativeCardsProps {
  narratives: FramedNarrative[];
  layout?: 'sidebar' | 'grid';
}

export default function NarrativeCards({ narratives, layout = 'sidebar' }: NarrativeCardsProps) {
  const { data: session } = useSession();

  if (narratives.length === 0) return null;

  const totalTitles = narratives.reduce((sum, n) => sum + n.title_count, 0);

  return (
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
            <div
              key={n.id}
              className="w-full text-left p-3 rounded-lg border border-dashboard-border bg-dashboard-surface"
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
                <div className="flex flex-wrap gap-1 mb-2">
                  {topLangs.map(l => (
                    <span key={l} className="text-[10px] px-1 py-0.5 rounded bg-dashboard-border/60 text-dashboard-text-muted">
                      {l}
                    </span>
                  ))}
                </div>
              )}
              {/* Analyse link */}
              {session?.user ? (
                <Link
                  href={`/analysis/${n.id}`}
                  className="mt-2 inline-block text-xs px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
                >
                  Analyse
                </Link>
              ) : (
                <a
                  href="/auth/signin"
                  className="mt-2 inline-block text-xs px-3 py-1 rounded bg-dashboard-border text-dashboard-text-muted hover:text-dashboard-text transition-colors"
                >
                  Sign in to analyse
                </a>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
