'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
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

    const bullet = line.match(/^[\-\*]\s+(.+)$/);
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
}

export default function AnalysisContent({ narrative, sampleTitles }: AnalysisContentProps) {
  const { data: session } = useSession();
  const [sections, setSections] = useState<RaiSection[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
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
        } else {
          setError('No analysis returned');
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [narrative, session]);

  if (!session?.user && !narrative.rai_full_analysis) {
    return (
      <div className="py-8 text-center">
        <a
          href="/auth/signin"
          className="text-sm px-4 py-2 rounded bg-dashboard-border text-dashboard-text-muted hover:text-dashboard-text transition-colors"
        >
          Sign in to generate analysis
        </a>
      </div>
    );
  }

  return (
    <div>
      {/* Loading state */}
      {loading && (
        <div className="flex items-center gap-3 text-dashboard-text-muted py-8">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Generating analysis... (this may take up to a minute)
        </div>
      )}

      {/* Error */}
      {error && <p className="text-red-400 py-4">{error}</p>}

      {/* Analysis sections */}
      {sections && sections.map((s) => (
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

      {/* Sample Headlines appendix */}
      {sampleTitles.length > 0 && (
        <div className="mt-10 pt-8 border-t border-dashboard-border">
          <h2 className="text-xl font-semibold text-dashboard-text mb-4">Sample Headlines</h2>
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
