'use client';

import { useState } from 'react';
import { Title } from '@/lib/types';

interface EventAccordionProps {
  event: {
    date: string;
    summary: string;
    source_title_ids?: string[];
  };
  allTitles: Title[];
  index: number;
}

export default function EventAccordion({ event, allTitles, index }: EventAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Get related titles for this event
  const relatedTitles = event.source_title_ids
    ? allTitles.filter(t => event.source_title_ids!.includes(t.id))
    : [];

  const hasRelatedTitles = relatedTitles.length > 0;

  return (
    <div className="border-l-4 border-blue-500 pl-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <p className="text-sm text-dashboard-text-muted mb-1">{event.date}</p>
          <p className="text-dashboard-text">{event.summary}</p>
        </div>
        {hasRelatedTitles && (
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex-shrink-0 text-sm text-blue-400 hover:text-blue-300 transition"
            aria-expanded={isOpen}
          >
            {isOpen ? '−' : '+'} {relatedTitles.length} {relatedTitles.length === 1 ? 'source' : 'sources'}
          </button>
        )}
      </div>

      {isOpen && hasRelatedTitles && (
        <div className="mt-3 pl-4 border-l border-dashboard-border space-y-2">
          {relatedTitles.map(title => (
            <div key={title.id} className="text-sm">
              {title.url_gnews ? (
                <a
                  href={title.url_gnews}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300"
                >
                  {title.title_display}
                </a>
              ) : (
                <p className="text-dashboard-text-muted">{title.title_display}</p>
              )}
              <div className="text-xs text-dashboard-text-muted mt-1">
                {title.publisher_name && <span>{title.publisher_name}</span>}
                {title.pubdate_utc && (
                  <span className="ml-2">
                    {new Date(title.pubdate_utc).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
