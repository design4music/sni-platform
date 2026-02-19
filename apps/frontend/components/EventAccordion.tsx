'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Title } from '@/lib/types';

interface EventAccordionProps {
  event: {
    date: string;
    last_active?: string;
    title?: string;
    summary: string;
    tags?: string[];
    source_title_ids?: string[];
    source_count?: number;
    event_id?: string;
    has_narratives?: boolean;
  };
  allTitles: Title[];
  index: number;
  compact?: boolean;
}

function TagPill({ tag }: { tag: string }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 border border-blue-500/30 text-blue-400">
      {tag}
    </span>
  );
}

function formatDate(dateStr: string): string {
  // Convert "2026-01-22" to "Jan 22"
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function DateRange({ date, last_active }: { date: string; last_active?: string }) {
  const formattedFirst = formatDate(date);
  if (last_active && last_active !== date) {
    const formattedLast = formatDate(last_active);
    return (
      <span className="text-dashboard-text-muted">
        {formattedFirst} — {formattedLast}
      </span>
    );
  }
  return <span className="text-dashboard-text-muted">{formattedFirst}</span>;
}

export default function EventAccordion({ event, allTitles, index, compact = false }: EventAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Get related titles for this event
  const relatedTitles = event.source_title_ids
    ? allTitles.filter(t => event.source_title_ids!.includes(t.id))
    : [];

  const hasRelatedTitles = relatedTitles.length > 0;
  const sourceCount = event.source_count || relatedTitles.length;

  if (compact) {
    return (
      <div className="py-2">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            {/* Date range */}
            <p className="text-xs mb-1">
              <DateRange date={event.date} last_active={event.last_active} />
            </p>
            {/* Title if available, otherwise summary */}
            {event.title ? (
              <>
                <p className="text-sm font-medium text-dashboard-text mb-1">
                  {event.title}
                </p>
                <p className="text-sm text-dashboard-text-muted">
                  {event.summary}
                </p>
              </>
            ) : (
              <p className="text-sm text-dashboard-text">
                {event.summary}
              </p>
            )}
            {/* Tags */}
            {event.tags && event.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {event.tags.slice(0, 5).map((tag, i) => (
                  <TagPill key={i} tag={tag} />
                ))}
              </div>
            )}
          </div>
          {sourceCount > 0 && (
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="flex-shrink-0 text-xs text-dashboard-text-muted hover:text-dashboard-text transition"
              aria-expanded={isOpen}
            >
              {isOpen ? '−' : '+'} {sourceCount}
            </button>
          )}
        </div>
        {isOpen && hasRelatedTitles && (
          <div className="mt-2 pl-4 space-y-1 max-h-96 overflow-y-auto">
            {relatedTitles.map(title => (
              <div key={title.id} className="text-xs text-dashboard-text-muted">
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
                  <span>{title.title_display}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="border-l-4 border-blue-500 pl-4 py-2">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          {/* Date range */}
          <p className="text-sm mb-1">
            <DateRange date={event.date} last_active={event.last_active} />
          </p>
          {/* Title if available */}
          {event.title ? (
            <>
              <p className="text-lg font-semibold text-dashboard-text mb-1">
                {event.title}
              </p>
              <p className="text-dashboard-text">{event.summary}</p>
            </>
          ) : (
            <p className="text-dashboard-text">{event.summary}</p>
          )}
          {/* Tags */}
          {event.tags && event.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {event.tags.map((tag, i) => (
                <TagPill key={i} tag={tag} />
              ))}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {event.has_narratives && event.event_id && (
            <Link
              href={`/events/${event.event_id}`}
              className="text-xs text-blue-400 hover:text-blue-300 px-2 py-1 rounded border border-blue-500/20"
            >
              View analysis
            </Link>
          )}
          {sourceCount > 0 && (
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-sm text-blue-400 hover:text-blue-300 transition"
              aria-expanded={isOpen}
            >
              {isOpen ? '−' : '+'} {sourceCount} {sourceCount === 1 ? 'source' : 'sources'}
            </button>
          )}
        </div>
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
