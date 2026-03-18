'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import type { NarrativeMapEntry } from '@/lib/types';

interface NarrativePanelProps {
  countryLabel: string;
  narratives: NarrativeMapEntry[];
  mode: 'outgoing' | 'incoming';
  onClose: () => void;
}

const INITIAL_SHOW = 5;

export default function NarrativePanel({ countryLabel, narratives, mode, onClose }: NarrativePanelProps) {
  const t = useTranslations('narrativeMap');
  const [expanded, setExpanded] = useState(false);

  // Separate geo (operational) and ideological narratives
  const operational = narratives.filter(n => n.tier !== 'ideological');
  const ideological = narratives.filter(n => n.tier === 'ideological');

  const header = mode === 'outgoing'
    ? t('outgoingHeader', { country: countryLabel })
    : t('incomingHeader', { country: countryLabel });

  const renderNarrative = (n: NarrativeMapEntry) => (
    <div key={n.id} className="py-3 border-b border-dashboard-border last:border-b-0">
      <div className="flex items-start justify-between gap-2">
        <Link
          href={`/narratives/${n.id}`}
          className="font-medium text-sm text-dashboard-text hover:text-blue-400 transition line-clamp-2"
        >
          {n.name}
        </Link>
        <span className="shrink-0 text-xs bg-dashboard-surface-raised px-2 py-0.5 rounded text-dashboard-text-muted">
          {n.event_count} {t('events')}
        </span>
      </div>
      {n.claim && (
        <p className="text-xs text-dashboard-text-muted mt-1 line-clamp-2">{n.claim}</p>
      )}
      <span className="text-xs text-dashboard-text-muted opacity-60 mt-1 inline-block">
        {n.meta_name}
      </span>
    </div>
  );

  const renderSection = (items: NarrativeMapEntry[], sectionTitle?: string) => {
    if (items.length === 0) return null;
    const visible = expanded ? items : items.slice(0, INITIAL_SHOW);
    const remaining = items.length - INITIAL_SHOW;

    return (
      <div>
        {sectionTitle && (
          <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2 mt-4">
            {sectionTitle}
          </h4>
        )}
        {visible.map(renderNarrative)}
        {!expanded && remaining > 0 && (
          <button
            onClick={() => setExpanded(true)}
            className="text-xs text-blue-400 hover:text-blue-300 mt-2"
          >
            {t('showMore', { count: remaining })}
          </button>
        )}
        {expanded && items.length > INITIAL_SHOW && (
          <button
            onClick={() => setExpanded(false)}
            className="text-xs text-blue-400 hover:text-blue-300 mt-2"
          >
            {t('showLess')}
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-dashboard-border">
        <h3 className="text-base font-bold text-dashboard-text">{header}</h3>
        <button
          onClick={onClose}
          className="text-dashboard-text-muted hover:text-dashboard-text text-lg leading-none"
          aria-label="Close"
        >
          x
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-2">
        {narratives.length === 0 ? (
          <p className="text-sm text-dashboard-text-muted py-8 text-center">{t('noNarratives')}</p>
        ) : (
          <>
            {renderSection(operational)}
            {renderSection(ideological, t('ideological'))}
          </>
        )}
      </div>
    </div>
  );
}
