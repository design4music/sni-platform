'use client';

import { useState } from 'react';
import EventAccordion from './EventAccordion';
import { Title, Event } from '@/lib/types';

interface EventListProps {
  events: Event[];
  allTitles: Title[];
  initialLimit?: number;
  compact?: boolean;
  keyPrefix: string;
}

export default function EventList({
  events,
  allTitles,
  initialLimit = 10,
  compact = false,
  keyPrefix,
}: EventListProps) {
  const [showAll, setShowAll] = useState(false);

  const displayedEvents = showAll ? events : events.slice(0, initialLimit);
  const hasMore = events.length > initialLimit;
  const remainingCount = events.length - initialLimit;

  return (
    <div className="space-y-3">
      {displayedEvents.map((event, idx) => (
        <EventAccordion
          key={`${keyPrefix}-${idx}`}
          event={event}
          allTitles={allTitles}
          index={idx}
          compact={compact}
        />
      ))}

      {hasMore && !showAll && (
        <button
          onClick={() => setShowAll(true)}
          className="mt-4 px-4 py-2 text-sm font-medium text-blue-400 hover:text-blue-300
                     bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30
                     rounded-lg transition-all duration-200"
        >
          Load {remainingCount} more {remainingCount === 1 ? 'topic' : 'topics'}
        </button>
      )}

      {showAll && hasMore && (
        <button
          onClick={() => setShowAll(false)}
          className="mt-4 px-4 py-2 text-sm font-medium text-dashboard-text-muted
                     hover:text-dashboard-text bg-dashboard-border/50 hover:bg-dashboard-border
                     rounded-lg transition-all duration-200"
        >
          Show less
        </button>
      )}
    </div>
  );
}
