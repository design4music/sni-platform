'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Title } from '@/lib/types';
import { useTranslations, useLocale } from 'next-intl';
import ExternalLink from './ExternalLink';

interface EventAccordionProps {
  event: {
    date: string;
    last_active?: string;
    title?: string;
    summary: string;
    tags?: string[];
    source_title_ids?: string[];
    source_count?: number;
    importance_score?: number;
    event_id?: string;
    has_narratives?: boolean;
    resolvedTitles?: Title[];
  };
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

function formatDate(dateStr: string, locale: string): string {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', { month: 'short', day: 'numeric' });
}

function DateRange({ date, last_active, locale }: { date: string; last_active?: string; locale: string }) {
  const formattedFirst = formatDate(date, locale);
  if (last_active && last_active !== date) {
    const formattedLast = formatDate(last_active, locale);
    return (
      <span className="text-dashboard-text-muted">
        {formattedFirst} — {formattedLast}
      </span>
    );
  }
  return <span className="text-dashboard-text-muted">{formattedFirst}</span>;
}

export default function EventAccordion({ event, index, compact = false }: EventAccordionProps) {
  const tTrending = useTranslations('trending');
  const tCommon = useTranslations('common');
  const tEvent = useTranslations('event');
  const locale = useLocale();
  const [isOpen, setIsOpen] = useState(false);

  const relatedTitles = event.resolvedTitles || [];
  const hasRelatedTitles = relatedTitles.length > 0;
  const sourceCount = event.source_count || relatedTitles.length;
  const isImportant = (event.importance_score || 0) >= 0.5;

  if (compact) {
    return (
      <div className={`py-2 ${isImportant ? 'border-l-2 border-yellow-500/60 pl-2' : ''}`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            {/* Date range */}
            <p className="text-xs mb-1 flex items-center">
              <DateRange date={event.date} last_active={event.last_active} locale={locale} />
              {event.last_active && (Date.now() - new Date(event.last_active + 'T00:00:00').getTime()) < 172800000 && (
                <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse ml-2" title={tTrending('active48h')} />
              )}
            </p>
            {/* Title if available, otherwise summary */}
            {event.title ? (
              <>
                {event.event_id ? (
                  <Link href={`/events/${event.event_id}`} className="text-sm font-medium text-dashboard-text hover:text-blue-400 transition-colors mb-1 block">
                    {event.title}
                  </Link>
                ) : (
                  <p className="text-sm font-medium text-dashboard-text mb-1">
                    {event.title}
                  </p>
                )}
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
              {isOpen ? '\u2212' : '+'} {sourceCount}
            </button>
          )}
        </div>
        {isOpen && hasRelatedTitles && (
          <div className="mt-2 pl-4 space-y-1">
            {relatedTitles.slice(0, 10).map(title => (
              <div key={title.id} className="text-xs text-dashboard-text-muted">
                {title.url_gnews ? (
                  <ExternalLink href={title.url_gnews} className="text-blue-400 hover:text-blue-300">
                    {title.title_display}
                  </ExternalLink>
                ) : (
                  <span>{title.title_display}</span>
                )}
              </div>
            ))}
            {relatedTitles.length > 10 && event.event_id && (
              <Link
                href={`/events/${event.event_id}`}
                className="inline-block mt-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                {tEvent('viewAllSources', { count: sourceCount })}
              </Link>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`border-l-4 pl-4 py-2 ${isImportant ? 'border-yellow-500/60 shadow-[0_0_12px_rgba(234,179,8,0.12)]' : 'border-blue-500'}`}>
      <div>
        {/* Title if available */}
        {event.title ? (
          <>
            {event.event_id ? (
              <Link href={`/events/${event.event_id}`} className="text-lg font-semibold text-dashboard-text hover:text-blue-400 transition-colors mb-1 block">
                {event.title}
              </Link>
            ) : (
              <p className="text-lg font-semibold text-dashboard-text mb-1">
                {event.title}
              </p>
            )}
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
        {/* Date + sources row */}
        <div className="flex items-center gap-3 mt-2 text-sm">
          <span className="flex items-center">
            <DateRange date={event.date} last_active={event.last_active} locale={locale} />
            {event.last_active && (Date.now() - new Date(event.last_active + 'T00:00:00').getTime()) < 172800000 && (
              <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse ml-2" title={tTrending('active48h')} />
            )}
          </span>
          {sourceCount > 0 && (
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-sm text-blue-400 hover:text-blue-300 transition"
              aria-expanded={isOpen}
            >
              {isOpen ? '\u2212' : '+'} {sourceCount} {sourceCount === 1 ? tCommon('source') : tCommon('sources')}
            </button>
          )}
        </div>
      </div>

      {isOpen && hasRelatedTitles && (
        <div className="mt-3 pl-4 border-l border-dashboard-border space-y-2">
          {relatedTitles.slice(0, 10).map(title => (
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
          {relatedTitles.length > 10 && event.event_id && (
            <Link
              href={`/events/${event.event_id}`}
              className="inline-block text-sm text-blue-400 hover:text-blue-300 transition-colors"
            >
              {tEvent('viewAllSources', { count: sourceCount })}
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
