'use client';

import { useState } from 'react';
import EventAccordion from './EventAccordion';
import type { Event } from '@/lib/types';

export interface StoryGroup {
  label: string;
  anchor: string;
  anchorType: string; // PER, PLC, ORG, TGT, EVT
  events: Event[];
  totalSources: number;
  topSignals?: string[]; // other frequent signals in this group
}

interface Props {
  groups: StoryGroup[];
  ungrouped: Event[];
  initialGroupsShown?: number;
  initialEventsPerGroup?: number;
}

export default function StoryGroupList({
  groups,
  ungrouped,
  initialGroupsShown = 15,
  initialEventsPerGroup = 5,
}: Props) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [groupsShown, setGroupsShown] = useState(initialGroupsShown);

  const toggleGroup = (anchor: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(anchor)) next.delete(anchor);
      else next.add(anchor);
      return next;
    });
  };

  const visibleGroups = groups.slice(0, groupsShown);
  const hasMoreGroups = groups.length > groupsShown;

  return (
    <div className="space-y-4">
      {visibleGroups.map(group => {
        const isExpanded = expandedGroups.has(group.anchor);
        const visibleEvents = isExpanded
          ? group.events
          : group.events.slice(0, initialEventsPerGroup);
        const hasMoreEvents = group.events.length > initialEventsPerGroup;

        return (
          <div key={group.anchor} className="border border-dashboard-border rounded-lg overflow-hidden">
            {/* Group header */}
            <button
              onClick={() => toggleGroup(group.anchor)}
              className="w-full flex items-center justify-between px-4 py-3 bg-dashboard-surface hover:bg-dashboard-surface-hover transition-colors text-left"
            >
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-semibold text-dashboard-text">
                  {group.label}
                </span>
                {group.topSignals && group.topSignals.length > 0 && (
                  <span className="text-xs text-dashboard-text-muted">
                    + {group.topSignals.join(', ')}
                  </span>
                )}
                <span className="text-xs text-dashboard-text-muted px-2 py-0.5 rounded-full bg-dashboard-border/50">
                  {group.events.length} {group.events.length === 1 ? 'topic' : 'topics'} | {group.totalSources} sources
                </span>
              </div>
              <svg
                className={`w-4 h-4 text-dashboard-text-muted transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Events within group */}
            <div className="px-4 pb-3 space-y-2">
              {visibleEvents.map((event, i) => (
                <EventAccordion key={`${group.anchor}-${i}`} event={event} index={i} />
              ))}
              {!isExpanded && hasMoreEvents && (
                <button
                  onClick={() => toggleGroup(group.anchor)}
                  className="text-sm text-blue-400 hover:text-blue-300 py-1"
                >
                  + {group.events.length - initialEventsPerGroup} more topics
                </button>
              )}
            </div>
          </div>
        );
      })}

      {hasMoreGroups && (
        <button
          onClick={() => setGroupsShown(prev => prev + 10)}
          className="w-full py-3 text-sm text-blue-400 hover:text-blue-300 border border-dashboard-border rounded-lg"
        >
          Show more story groups ({groups.length - groupsShown} remaining)
        </button>
      )}

      {/* Ungrouped events */}
      {ungrouped.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-dashboard-text mb-3">
            Other Topics ({ungrouped.length})
          </h3>
          <div className="space-y-2">
            {ungrouped.slice(0, 10).map((event, i) => (
              <EventAccordion key={`ungrouped-${i}`} event={event} index={i} />
            ))}
            {ungrouped.length > 10 && (
              <p className="text-sm text-dashboard-text-muted py-2">
                + {ungrouped.length - 10} more topics
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
