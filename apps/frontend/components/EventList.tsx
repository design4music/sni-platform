'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import EventAccordion from './EventAccordion';
import { Event } from '@/lib/types';

interface EventListProps {
  events: Event[];
  initialLimit?: number;
  pageSize?: number;
  compact?: boolean;
  keyPrefix: string;
}

export default function EventList({
  events,
  initialLimit = 10,
  pageSize = 10,
  compact = false,
  keyPrefix,
}: EventListProps) {
  const t = useTranslations('track');
  const [visibleCount, setVisibleCount] = useState(initialLimit);

  const displayedEvents = events.slice(0, visibleCount);
  const remaining = events.length - visibleCount;
  const hasMore = remaining > 0;
  const nextBatch = Math.min(pageSize, remaining);

  return (
    <div className="space-y-3">
      {displayedEvents.map((event, idx) => (
        <EventAccordion
          key={`${keyPrefix}-${idx}`}
          event={event}
          index={idx}
          compact={compact}
        />
      ))}

      {hasMore && (
        <button
          onClick={() => setVisibleCount((v) => v + pageSize)}
          className="mt-4 px-4 py-2 text-sm font-medium text-blue-400 hover:text-blue-300
                     bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30
                     rounded-lg transition-all duration-200"
        >
          {t('loadMore', { count: nextBatch })}
        </button>
      )}
    </div>
  );
}
