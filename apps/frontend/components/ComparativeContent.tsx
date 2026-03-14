'use client';

import { useState, useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';
import { useTranslations } from 'next-intl';
import type { EntityAnalysis } from '@/lib/queries';
import type { RaiSection } from '@/lib/types';

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

function parseSections(raw: string): RaiSection[] {
  const sections: RaiSection[] = [];
  const lines = raw.split('\n');
  let current: RaiSection | null = null;
  let paragraphLines: string[] = [];

  const flushParagraph = () => {
    if (paragraphLines.length > 0 && current) {
      current.paragraphs.push(paragraphLines.join('\n'));
      paragraphLines = [];
    }
  };

  for (const line of lines) {
    const heading = line.match(/^##\s+(.+)$/);
    if (heading) {
      flushParagraph();
      if (current) sections.push(current);
      current = { heading: heading[1], paragraphs: [] };
      continue;
    }
    if (line.trim() === '') {
      flushParagraph();
    } else {
      paragraphLines.push(line);
    }
  }
  flushParagraph();
  if (current) sections.push(current);
  return sections;
}

interface Props {
  entityType: string;
  entityId: string;
  cachedAnalysis: EntityAnalysis | null;
  locale?: string;
}

export default function ComparativeContent({ entityType, entityId, cachedAnalysis, locale }: Props) {
  const { data: session } = useSession();
  const t = useTranslations('comparative');
  const tAnalysis = useTranslations('analysis');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [translating, setTranslating] = useState(false);
  const [translatedSections, setTranslatedSections] = useState<RaiSection[] | null>(null);
  const [sections, setSections] = useState<RaiSection[]>(() => {
    if (!cachedAnalysis?.sections) return [];
    const raw = cachedAnalysis.sections;
    if (typeof raw === 'string') {
      // Could be JSON array of RaiSection[] or raw markdown
      try {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) return parsed;
      } catch {
        // Raw markdown -- parse into sections
        return parseSections(raw);
      }
    }
    return [];
  });
  const [synthesis, setSynthesis] = useState<string | null>(
    cachedAnalysis?.synthesis || cachedAnalysis?.scores?.synthesis || null
  );
  const [blindSpots, setBlindSpots] = useState<string[] | null>(
    cachedAnalysis?.blind_spots || cachedAnalysis?.scores?.collective_blind_spots || null
  );

  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    if (sections.length > 0) return;
    if (!session?.user) return;

    setLoading(true);
    setError(null);

    fetch('/api/rai-analyse-comparative', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity_type: entityType, entity_id: entityId }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const data = await res.json().catch(() => ({ error: 'Request failed' }));
          throw new Error(data.error || `Error ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        let newSections: RaiSection[] = [];
        if (data.sections) {
          if (typeof data.sections === 'string') {
            try {
              const parsed = JSON.parse(data.sections);
              newSections = Array.isArray(parsed) ? parsed : parseSections(data.sections);
            } catch {
              newSections = parseSections(data.sections);
            }
          } else if (Array.isArray(data.sections)) {
            newSections = data.sections;
          }
        }
        setSections(newSections);
        setSynthesis(data.synthesis || data.scores?.synthesis || null);
        setBlindSpots(data.blind_spots || data.scores?.collective_blind_spots || null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Unknown error'))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session, entityType, entityId, retryCount]);

  // No analysis yet -- show generate button
  if (sections.length === 0) {
    if (!session?.user) {
      return (
        <div className="text-center py-12">
          <p className="text-dashboard-text-muted mb-4">{t('signInToGenerate')}</p>
          <a
            href="/auth/signin"
            className="inline-block text-sm px-4 py-2 rounded bg-dashboard-border text-dashboard-text-muted hover:text-dashboard-text transition-colors"
          >
            {t('signIn')}
          </a>
        </div>
      );
    }

    if (loading) {
      return (
        <div className="text-center py-12">
          <span className="inline-block w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin mb-4" />
          <p className="text-dashboard-text-muted">{t('generating')}</p>
          <p className="text-sm text-dashboard-text-muted/60 mt-2">{t('generatingTime')}</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="text-center py-12">
          <p className="text-sm text-red-400 mb-2">{error}</p>
          <button
            onClick={() => setRetryCount((c) => c + 1)}
            className="text-sm px-4 py-2 rounded bg-dashboard-border text-dashboard-text-muted hover:text-dashboard-text transition-colors"
          >
            {t('retry')}
          </button>
        </div>
      );
    }

    return null;
  }

  async function translateReport() {
    if (!cachedAnalysis?.id) return;
    setTranslating(true);
    try {
      const resp = await fetch('/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_type: 'entity_analysis',
          entity_id: cachedAnalysis.id,
          field: 'sections',
          locale: 'de',
        }),
      });
      if (!resp.ok) return;
      const data = await resp.json();
      if (data.translated) {
        const raw = typeof data.translated === 'string' ? data.translated : '';
        setTranslatedSections(parseSections(raw));
      }

      // Also translate synthesis
      const synthResp = await fetch('/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_type: 'entity_analysis',
          entity_id: cachedAnalysis.id,
          field: 'synthesis',
          locale: 'de',
        }),
      });
      if (synthResp.ok) {
        const synthData = await synthResp.json();
        if (synthData.translated) setSynthesis(synthData.translated);
      }
    } catch {
      // Silent fail -- user can retry
    } finally {
      setTranslating(false);
    }
  }

  const displaySections = (locale === 'de' && translatedSections) ? translatedSections : sections;
  const showTranslateBtn = locale === 'de' && sections.length > 0 && !translatedSections;

  // Render the report
  return (
    <div>
      {/* Translate button for DE users */}
      {showTranslateBtn && (
        <div className="mb-6">
          <button
            onClick={translateReport}
            disabled={translating}
            className="text-sm px-4 py-2 rounded bg-dashboard-border text-dashboard-text-muted hover:text-dashboard-text disabled:opacity-50 transition-colors"
          >
            {translating ? (
              <>
                <span className="inline-block w-3.5 h-3.5 border-2 border-current/30 border-t-current rounded-full animate-spin mr-2 align-middle" />
                {tAnalysis('translatingAnalysis')}
              </>
            ) : (
              tAnalysis('translateAnalysis')
            )}
          </button>
        </div>
      )}

      {displaySections.map((section, idx) => (
        <div key={idx} className="mb-6">
          <h2 className="text-xl font-semibold text-dashboard-text mt-8 mb-2">
            {section.heading}
          </h2>
          {section.paragraphs.map((p, pi) => (
            <div key={pi} className="mb-3">
              {renderMarkdown(p)}
            </div>
          ))}
        </div>
      ))}

      {/* Synthesis & blind spots */}
      {(synthesis || (blindSpots && blindSpots.length > 0)) && (
        <div className="border-t border-dashboard-border pt-8 mt-8">
          {synthesis && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-dashboard-text mb-2">{t('synthesis')}</h3>
              <p className="text-base text-dashboard-text-muted leading-relaxed">{synthesis}</p>
            </div>
          )}
          {blindSpots && blindSpots.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-dashboard-text mb-2">{t('collectiveBlindSpots')}</h3>
              <ul className="space-y-1.5">
                {blindSpots.map((s, i) => (
                  <li key={i} className="text-base text-dashboard-text-muted leading-relaxed flex items-start gap-2">
                    <span className="text-orange-400 mt-0.5 flex-shrink-0">?</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
