'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { FramedNarrative, FrameStats, RaiSection } from '@/lib/types';

/** Render a paragraph-level markdown block as React elements. */
function renderMarkdown(text: string): React.ReactNode {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];
  let listKey = 0;

  const flushList = () => {
    if (listItems.length === 0) return;
    elements.push(
      <ul key={`ul-${listKey++}`} className="list-disc pl-5 mb-2 space-y-0.5 text-sm text-dashboard-text-muted leading-relaxed">
        {listItems.map((item, i) => (
          <li key={i} dangerouslySetInnerHTML={{ __html: inlineFormat(item) }} />
        ))}
      </ul>
    );
    listItems = [];
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Sub-heading (### within a section)
    const subHeading = line.match(/^###\s+(.+)$/);
    if (subHeading) {
      flushList();
      elements.push(
        <h5 key={`h-${i}`} className="text-xs font-semibold text-dashboard-text mt-3 mb-1">
          {subHeading[1]}
        </h5>
      );
      continue;
    }

    // Blockquote
    if (line.startsWith('> ')) {
      flushList();
      elements.push(
        <blockquote
          key={`bq-${i}`}
          className="border-l-2 border-emerald-500/40 pl-3 my-2 text-sm italic text-dashboard-text-muted/80 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: inlineFormat(line.slice(2)) }}
        />
      );
      continue;
    }

    // Bullet list item
    const bullet = line.match(/^[\-\*]\s+(.+)$/);
    if (bullet) {
      listItems.push(bullet[1]);
      continue;
    }

    // Regular line
    flushList();
    const trimmed = line.trim();
    if (trimmed) {
      elements.push(
        <span
          key={`l-${i}`}
          className="block text-sm text-dashboard-text-muted leading-relaxed"
          dangerouslySetInnerHTML={{ __html: inlineFormat(trimmed) }}
        />
      );
    }
  }
  flushList();

  return <>{elements}</>;
}

/** Apply inline markdown formatting (bold, italic). */
function inlineFormat(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>');
}

interface NarrativeOverlayProps {
  narrative: FramedNarrative;
  onClose: () => void;
}

function NarrativeOverlay({ narrative, onClose }: NarrativeOverlayProps) {
  const [sections, setSections] = useState<RaiSection[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // If already cached in the narrative object, use it
    if (narrative.rai_full_analysis) {
      const existing = typeof narrative.rai_full_analysis === 'string'
        ? JSON.parse(narrative.rai_full_analysis)
        : narrative.rai_full_analysis;
      if (Array.isArray(existing)) {
        setSections(existing);
        return;
      }
    }

    // Otherwise trigger the API call
    setLoading(true);
    setError(null);
    fetch('/api/rai-analyse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ narrative_id: narrative.id }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.error || `Error ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        if (data.sections && Array.isArray(data.sections)) {
          setSections(data.sections);
          // Update the narrative object so re-opening is instant
          narrative.rai_full_analysis = data.sections;
        } else {
          setError('No analysis returned');
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [narrative]);

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
              {narrative.title_count} sources
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

          {/* RAI Analysis */}
          <div>
            <h3 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-3">
              RAI Analysis
            </h3>
            {loading && (
              <div className="flex items-center gap-3 text-sm text-dashboard-text-muted py-4">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Generating analysis... (this may take up to a minute)
              </div>
            )}
            {error && (
              <p className="text-sm text-red-400 py-2">{error}</p>
            )}
            {sections && sections.map((s) => (
              <div key={s.heading} className="mb-4">
                <h4 className="text-sm font-semibold text-dashboard-text mb-1.5">{s.heading}</h4>
                {s.paragraphs.map((p, i) => (
                  <div key={i} className="mb-2">
                    {renderMarkdown(p)}
                  </div>
                ))}
              </div>
            ))}
          </div>

          {/* Media Sources (outlet pills) */}
          {narrative.top_sources && narrative.top_sources.length > 0 && (
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
  const { data: session } = useSession();

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
                {/* Analyse button */}
                {session?.user ? (
                  <button
                    onClick={() => setSelectedNarrative(n)}
                    className="mt-2 text-xs px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
                  >
                    Analyse
                  </button>
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
