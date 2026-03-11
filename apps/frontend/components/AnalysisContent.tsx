'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useTranslations } from 'next-intl';
import type { RaiSection, NarrativeDetail } from '@/lib/types';

/** Apply inline markdown formatting (bold, italic). */
function inlineFormat(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>');
}

/** Render a paragraph-level markdown block as React elements. */
function renderMarkdown(text: string): React.ReactNode {
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];
  let listKey = 0;

  const flushList = () => {
    if (listItems.length === 0) return;
    elements.push(
      <ul key={`ul-${listKey++}`} className="list-disc pl-5 mb-2 space-y-0.5 text-base text-dashboard-text-muted leading-relaxed">
        {listItems.map((item, i) => (
          <li key={i} dangerouslySetInnerHTML={{ __html: inlineFormat(item) }} />
        ))}
      </ul>
    );
    listItems = [];
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    const subHeading = line.match(/^###\s+(.+)$/);
    if (subHeading) {
      flushList();
      elements.push(
        <h5 key={`h-${i}`} className="text-sm font-semibold text-dashboard-text mt-4 mb-1">
          {subHeading[1]}
        </h5>
      );
      continue;
    }

    if (line.startsWith('> ')) {
      flushList();
      elements.push(
        <blockquote
          key={`bq-${i}`}
          className="border-l-4 border-blue-500 pl-4 my-3 text-base italic text-dashboard-text-muted/80 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: inlineFormat(line.slice(2)) }}
        />
      );
      continue;
    }

    const bullet = line.match(/^\s*[\-\*]\s+(.+)$/);
    if (bullet) {
      listItems.push(bullet[1]);
      continue;
    }

    flushList();
    const trimmed = line.trim();
    if (trimmed) {
      elements.push(
        <span
          key={`l-${i}`}
          className="block text-base text-dashboard-text-muted leading-relaxed"
          dangerouslySetInnerHTML={{ __html: inlineFormat(trimmed) }}
        />
      );
    }
  }
  flushList();

  return <>{elements}</>;
}

interface AnalysisContentProps {
  narrative: NarrativeDetail;
  sampleTitles: Array<{ title: string; publisher: string }>;
  locale?: string;
}

export default function AnalysisContent({ narrative, sampleTitles, locale }: AnalysisContentProps) {
  const { data: session } = useSession();
  const t = useTranslations('analysis');
  const [sections, setSections] = useState<RaiSection[] | null>(null);
  const [synthesis, setSynthesis] = useState<string | null>(narrative.rai_synthesis || null);
  const [conflicts, setConflicts] = useState<string[] | null>(narrative.rai_conflicts || null);
  const [blindSpots, setBlindSpots] = useState<string[] | null>(narrative.rai_blind_spots || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [translating, setTranslating] = useState(false);
  const [translatedAnalysis, setTranslatedAnalysis] = useState<RaiSection[] | null>(null);

  useEffect(() => {
    // Check for cached DE translation first
    if (locale === 'de' && narrative.rai_full_analysis_de) {
      const deSections = typeof narrative.rai_full_analysis_de === 'string'
        ? JSON.parse(narrative.rai_full_analysis_de)
        : narrative.rai_full_analysis_de;
      if (Array.isArray(deSections)) {
        setTranslatedAnalysis(deSections);
      }
    }

    // If already cached, use it
    if (narrative.rai_full_analysis) {
      const existing = typeof narrative.rai_full_analysis === 'string'
        ? JSON.parse(narrative.rai_full_analysis)
        : narrative.rai_full_analysis;
      if (Array.isArray(existing)) {
        setSections(existing);
        return;
      }
    }

    if (!session?.user) return;

    // Trigger API call
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
          // Update scores from fresh API response
          if (data.scores) {
            if (data.scores.synthesis) setSynthesis(data.scores.synthesis);
            if (data.scores.conflicts) setConflicts(data.scores.conflicts);
            if (data.scores.blind_spots) setBlindSpots(data.scores.blind_spots);
            // Broadcast to sidebar AssessmentScores component
            // On fresh analysis, shift scores are flat on data.scores (bias_detected, coherence, etc.)
            // On cached reads, they're nested under data.scores.shifts
            window.dispatchEvent(new CustomEvent('rai-scores-updated', {
              detail: { adequacy: data.scores.adequacy, shifts: data.scores.shifts || data.scores },
            }));
          }
        } else {
          setError('No analysis returned');
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [narrative, session, locale]);

  async function translateField(field: string) {
    const resp = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        entity_type: 'narrative',
        entity_id: narrative.id,
        field,
        locale: 'de',
      }),
    });
    if (!resp.ok) return null;
    const data = await resp.json();
    return data.translated ?? null;
  }

  async function handleTranslate() {
    setTranslating(true);
    try {
      const results = await Promise.all([
        translateField('rai_full_analysis'),
        translateField('rai_synthesis'),
        translateField('rai_conflicts'),
        translateField('rai_blind_spots'),
      ]);

      // Main analysis sections
      if (results[0]) {
        const parsed = typeof results[0] === 'string' ? JSON.parse(results[0]) : results[0];
        if (Array.isArray(parsed)) setTranslatedAnalysis(parsed);
      }
      // Synthesis
      if (results[1]) setSynthesis(typeof results[1] === 'string' ? results[1] : null);
      // Conflicts
      if (results[2]) {
        const arr = typeof results[2] === 'string' ? JSON.parse(results[2]) : results[2];
        if (Array.isArray(arr)) setConflicts(arr);
      }
      // Blind spots
      if (results[3]) {
        const arr = typeof results[3] === 'string' ? JSON.parse(results[3]) : results[3];
        if (Array.isArray(arr)) setBlindSpots(arr);
      }
    } catch {
      // Silently fail — user can retry
    } finally {
      setTranslating(false);
    }
  }

  if (!session?.user && !narrative.rai_full_analysis) {
    return (
      <div className="py-8 text-center">
        <a
          href="/auth/signin"
          className="text-sm px-4 py-2 rounded bg-dashboard-border text-dashboard-text-muted hover:text-dashboard-text transition-colors"
        >
          {t('signInToGenerate')}
        </a>
      </div>
    );
  }

  const hasSynthesisSection = synthesis || (conflicts && conflicts.length > 0) || (blindSpots && blindSpots.length > 0);
  const displaySections = (locale === 'de' && translatedAnalysis) ? translatedAnalysis : sections;
  const showTranslateBtn = locale === 'de' && sections && !translatedAnalysis;

  return (
    <div>
      {/* Loading state */}
      {loading && (
        <div className="flex items-center gap-3 text-dashboard-text-muted py-8">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {t('generating')}
        </div>
      )}

      {/* Error */}
      {error && <p className="text-red-400 py-4">{error}</p>}

      {/* Translate button for DE users */}
      {showTranslateBtn && (
        <div className="mb-6">
          <button
            onClick={handleTranslate}
            disabled={translating}
            className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-wait text-white transition-colors"
          >
            {translating ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                {t('translatingAnalysis')}
              </>
            ) : (
              t('translateAnalysis')
            )}
          </button>
        </div>
      )}

      {/* Analysis sections */}
      {displaySections && displaySections.map((s) => (
        <div key={s.heading} className="mb-6">
          <h2 className="text-xl font-semibold text-dashboard-text mb-2 mt-8">
            {s.heading}
          </h2>
          {s.paragraphs.map((p, i) => (
            <div key={i} className="mb-2">
              {renderMarkdown(p)}
            </div>
          ))}
        </div>
      ))}

      {/* Synthesis, Conflicts, Blind Spots */}
      {hasSynthesisSection && (
        <div className="mt-10 pt-8 border-t border-dashboard-border space-y-6">
          {synthesis && (
            <div>
              <h2 className="text-xl font-semibold text-dashboard-text mb-2">{t('synthesis')}</h2>
              <p className="text-base text-dashboard-text-muted leading-relaxed">{synthesis}</p>
            </div>
          )}

          {conflicts && conflicts.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-dashboard-text mb-2">{t('conflicts')}</h2>
              <ul className="space-y-1.5">
                {conflicts.map((c, i) => (
                  <li key={i} className="text-base text-dashboard-text-muted leading-relaxed flex items-start gap-2">
                    <span className="text-orange-400 mt-1 flex-shrink-0">-</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {blindSpots && blindSpots.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-dashboard-text mb-2">{t('blindSpots')}</h2>
              <ul className="space-y-1.5">
                {blindSpots.map((b, i) => (
                  <li key={i} className="text-base text-dashboard-text-muted leading-relaxed flex items-start gap-2">
                    <span className="text-orange-400 mt-1 flex-shrink-0">?</span>
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Sample Headlines appendix */}
      {sampleTitles.length > 0 && (
        <div className="mt-10 pt-8 border-t border-dashboard-border">
          <h2 className="text-xl font-semibold text-dashboard-text mb-4">{t('sampleHeadlines')}</h2>
          <ul className="space-y-2">
            {sampleTitles.slice(0, 15).map((sample, i) => (
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
  );
}
