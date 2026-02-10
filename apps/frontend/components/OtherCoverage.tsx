'use client';

import { useState } from 'react';
import { Event, Title } from '@/lib/types';

interface OtherCoverageProps {
  label: string;
  events: Event[];       // Mix of small topics + catchall events
  allTitles: Title[];
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function DateRange({ date, lastActive }: { date: string; lastActive?: string }) {
  const first = formatDate(date);
  if (lastActive && lastActive !== date) {
    return <span>{first} — {formatDate(lastActive)}</span>;
  }
  return <span>{first}</span>;
}

function TitleLink({ title }: { title: Title }) {
  return (
    <div className="py-0.5 text-sm">
      {title.url_gnews ? (
        <a
          href={title.url_gnews}
          target="_blank"
          rel="noopener noreferrer"
          className="text-dashboard-text-muted hover:text-blue-400 transition"
        >
          {title.title_display}
        </a>
      ) : (
        <span className="text-dashboard-text-muted">{title.title_display}</span>
      )}
      {title.publisher_name && (
        <span className="text-dashboard-text-muted/60 text-xs ml-2">
          - {title.publisher_name}
        </span>
      )}
    </div>
  );
}

/** A small topic: date + title + indented linked titles. */
function SmallTopic({ event, allTitles }: { event: Event; allTitles: Title[] }) {
  const titles = allTitles.filter(t => (event.source_title_ids || []).includes(t.id));
  const topicTitle = event.title || event.summary || 'Untitled topic';

  return (
    <div className="mb-3">
      <div className="flex items-baseline gap-2 text-sm">
        <span className="text-xs text-dashboard-text-muted flex-shrink-0">
          <DateRange date={event.date} lastActive={event.last_active} />
        </span>
        <span className="font-medium text-dashboard-text">{topicTitle}</span>
        <span className="text-xs text-dashboard-text-muted flex-shrink-0">
          ({titles.length})
        </span>
      </div>
      <div className="pl-6 mt-0.5">
        {titles.map(t => (
          <TitleLink key={t.id} title={t} />
        ))}
      </div>
    </div>
  );
}

function countTitles(events: Event[]) {
  return events.reduce((sum, e) => sum + (e.source_title_ids?.length || 0), 0);
}

export default function OtherCoverage({ label, events, allTitles }: OtherCoverageProps) {
  const [isOpen, setIsOpen] = useState(false);

  const totalSources = countTitles(events);
  if (totalSources === 0) return null;

  // Separate small topics (non-catchall with 2+ sources) from singletons
  const smallTopics = events
    .filter(e => !e.is_catchall && (e.source_title_ids?.length || 0) >= 2)
    .sort((a, b) => (b.source_title_ids?.length || 0) - (a.source_title_ids?.length || 0));

  // Singletons: catchall titles + single-source non-catchall events
  const singletonEvents = events.filter(
    e => e.is_catchall || (e.source_title_ids?.length || 0) < 2
  );
  const singletonIds = singletonEvents.flatMap(e => e.source_title_ids || []);
  const singletonTitles = allTitles.filter(t => singletonIds.includes(t.id));

  return (
    <div className="mt-4 pt-3 border-t border-dashboard-border/50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-sm text-dashboard-text-muted hover:text-dashboard-text transition"
        aria-expanded={isOpen}
      >
        <span className={`transition-transform duration-200 ${isOpen ? 'rotate-90' : ''}`}>
          &#9656;
        </span>
        {label} ({totalSources} sources)
      </button>

      {isOpen && (
        <div className="mt-3 pl-2">
          {/* Small topics with grouped titles */}
          {smallTopics.length > 0 && (
            <div className="mb-4">
              {smallTopics.map((event, i) => (
                <SmallTopic key={event.event_id || i} event={event} allTitles={allTitles} />
              ))}
            </div>
          )}

          {/* Singletons */}
          {singletonTitles.length > 0 && (
            <div>
              {smallTopics.length > 0 && (
                <p className="text-xs text-dashboard-text-muted/60 uppercase tracking-wide mb-2">
                  Unclustered ({singletonTitles.length})
                </p>
              )}
              <div className="space-y-0.5">
                {singletonTitles.slice(0, 30).map(t => (
                  <TitleLink key={t.id} title={t} />
                ))}
                {singletonTitles.length > 30 && (
                  <p className="text-xs text-dashboard-text-muted pt-1">
                    ... and {singletonTitles.length - 30} more
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
