'use client';

import { useMemo, useState } from 'react';
import EventAccordion from './EventAccordion';
import type { Event } from '@/lib/types';

export interface StoryGroup {
  label: string;
  anchor: string;
  anchorType: string;
  events: Event[];
  totalSources: number;
  topSignals?: string[];
}

interface Props {
  groups: StoryGroup[];
  ungrouped: Event[];
  initialGroupsShown?: number;
  initialEventsPerGroup?: number;
}

function eventMatchesFilter(event: Event, filter: string): boolean {
  const filterUpper = filter.toUpperCase();
  if (event.topic_core?.toUpperCase().includes(filterUpper)) return true;
  if (event.bucket_key && filter.startsWith('COUNTRY:') && event.bucket_key === filter.slice(8)) return true;
  if (event.tags?.some(t => t.toUpperCase() === filterUpper)) return true;
  return false;
}

export default function StoryGroupList({
  groups,
  ungrouped,
  initialGroupsShown = 15,
  initialEventsPerGroup = 5,
}: Props) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [groupsShown, setGroupsShown] = useState(initialGroupsShown);
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [minSources, setMinSources] = useState(0);
  const [sortBy, setSortBy] = useState<'sources' | 'date'>('sources');
  const [activeWeek, setActiveWeek] = useState<string | null>(null);

  const toggleGroup = (anchor: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(anchor)) next.delete(anchor);
      else next.add(anchor);
      return next;
    });
  };

  const getWeek = (dateStr?: string): string => {
    if (!dateStr) return 'unknown';
    const day = parseInt(dateStr.slice(8, 10));
    if (day <= 7) return 'W1';
    if (day <= 14) return 'W2';
    if (day <= 21) return 'W3';
    return 'W4';
  };

  const getWeekLabel = (week: string): string => {
    const sample = [...groups.flatMap(g => g.events), ...ungrouped].find(e => e.date);
    if (!sample?.date) return week;
    const m = parseInt(sample.date.split('-')[1]);
    const mn = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m - 1] || '';
    if (week === 'W1') return `${mn} 1-7`;
    if (week === 'W2') return `${mn} 8-14`;
    if (week === 'W3') return `${mn} 15-21`;
    if (week === 'W4') return `${mn} 22+`;
    return week;
  };

  const weekOptions = useMemo(() => {
    const allEvts = [...groups.flatMap(g => g.events), ...ungrouped];
    const counts = new Map<string, number>();
    for (const ev of allEvts) {
      const w = getWeek(ev.date);
      counts.set(w, (counts.get(w) || 0) + 1);
    }
    return ['W4', 'W3', 'W2', 'W1']
      .filter(w => counts.has(w))
      .map(w => ({ week: w, label: getWeekLabel(w), count: counts.get(w) || 0 }));
  }, [groups, ungrouped]);

  const countryFilters = useMemo(() => {
    const counts = new Map<string, { label: string; events: number }>();
    for (const ev of [...groups.flatMap(g => g.events), ...ungrouped]) {
      if (ev.event_type === 'bilateral' && ev.bucket_key && ev.bucketLabel) {
        const key = 'COUNTRY:' + ev.bucket_key;
        const existing = counts.get(key);
        if (existing) existing.events += 1;
        else counts.set(key, { label: ev.bucketLabel, events: 1 });
      }
    }
    return [...counts.entries()].sort((a, b) => b[1].events - a[1].events);
  }, [groups, ungrouped]);

  const handleFilter = (filter: string | null) => {
    if (filter === activeFilter) setActiveFilter(null);
    else { setActiveFilter(filter); setGroupsShown(100); }
  };

  const handleTagFilter = (tag: string) => {
    const parts = tag.split(':');
    if (parts.length === 2) {
      const anchorKey = parts[0].toUpperCase() + ':' + parts[1].toUpperCase();
      const match = groups.find(g => g.anchor.toUpperCase() === anchorKey || g.anchor.toUpperCase().startsWith(anchorKey));
      if (match) { handleFilter(match.anchor); return; }
    }
    handleFilter(tag);
  };

  const filteredGroups = useMemo(() => {
    if (!activeFilter) return groups;
    const exact = groups.filter(g => g.anchor === activeFilter);
    if (exact.length > 0) return exact;
    return groups.map(g => ({ ...g, events: g.events.filter(e => eventMatchesFilter(e, activeFilter)) })).filter(g => g.events.length > 0);
  }, [groups, activeFilter]);

  const visibleGroups = filteredGroups.slice(0, activeFilter ? filteredGroups.length : groupsShown);
  const hasMoreGroups = !activeFilter && filteredGroups.length > groupsShown;

  const filteredUngrouped = useMemo(() => {
    let result = [...ungrouped];
    if (activeWeek) result = result.filter(e => getWeek(e.date) === activeWeek);
    if (minSources > 0) result = result.filter(e => (e.source_title_ids?.length || 0) >= minSources);
    if (activeFilter) result = result.filter(e => eventMatchesFilter(e, activeFilter));
    if (sortBy === 'date') result.sort((a, b) => (a.date || '').localeCompare(b.date || ''));
    return result;
  }, [ungrouped, activeFilter, activeWeek, minSources, sortBy]);

  const totalTopics = groups.reduce((s, g) => s + g.events.length, 0) + ungrouped.length;
  const showFilters = totalTopics >= 50;

  return (
    <div className="space-y-4">
      {showFilters && (
        <div className="space-y-3 mb-2">
          {weekOptions.length > 1 && (
            <div className="flex flex-wrap gap-1.5 items-center">
              <span className="text-xs text-dashboard-text-muted">Week:</span>
              <button onClick={() => setActiveWeek(null)}
                className={`px-2.5 py-1 rounded-full text-xs font-medium border transition ${activeWeek === null ? 'bg-purple-600/20 border-purple-500/40 text-purple-400' : 'border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text'}`}>All</button>
              {weekOptions.map(w => (
                <button key={w.week} onClick={() => setActiveWeek(activeWeek === w.week ? null : w.week)}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium border transition ${activeWeek === w.week ? 'bg-purple-600/20 border-purple-500/40 text-purple-400' : 'border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text'}`}>
                  {w.label}
                </button>
              ))}
            </div>
          )}
          <div className="flex flex-wrap gap-1.5 items-center">
            <span className="text-xs text-dashboard-text-muted">Tags:</span>
            <button onClick={() => handleFilter(null)}
              className={`px-2.5 py-1 rounded-full text-xs font-medium border transition ${activeFilter === null ? 'bg-blue-600/20 border-blue-500/40 text-blue-400' : 'border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text'}`}>All</button>
            {groups.map(g => (
              <button key={g.anchor} onClick={() => handleFilter(g.anchor)}
                className={`px-2.5 py-1 rounded-full text-xs font-medium border transition ${activeFilter === g.anchor ? 'bg-blue-600/20 border-blue-500/40 text-blue-400' : 'border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text'}`}>
                {g.label} ({g.events.length})
              </button>
            ))}
          </div>
          {countryFilters.length > 0 && (
            <div className="flex flex-wrap gap-1.5 items-center">
              <span className="text-xs text-dashboard-text-muted">Countries:</span>
              {countryFilters.map(([key, info]) => (
                <button key={key} onClick={() => handleFilter(key)}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium border transition ${activeFilter === key ? 'bg-emerald-600/20 border-emerald-500/40 text-emerald-400' : 'border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text'}`}>
                  {info.label} ({info.events})
                </button>
              ))}
            </div>
          )}
          <div className="flex items-center gap-6 text-xs text-dashboard-text-muted">
            <div className="flex items-center gap-2">
              <span>Min sources:</span>
              {[0, 5, 10, 20].map(t => (
                <button key={t} onClick={() => setMinSources(t)}
                  className={`px-2 py-0.5 rounded border transition ${minSources === t ? 'bg-blue-600/20 border-blue-500/40 text-blue-400' : 'border-dashboard-border hover:text-dashboard-text'}`}>
                  {t === 0 ? 'All' : `${t}+`}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <span>Sort:</span>
              {(['sources', 'date'] as const).map(s => (
                <button key={s} onClick={() => setSortBy(s)}
                  className={`px-2 py-0.5 rounded border transition ${sortBy === s ? 'bg-blue-600/20 border-blue-500/40 text-blue-400' : 'border-dashboard-border hover:text-dashboard-text'}`}>
                  {s === 'sources' ? 'Sources' : 'Date'}
                </button>
              ))}
            </div>
            {activeFilter && (
              <button onClick={() => handleFilter(null)} className="text-blue-400 hover:text-blue-300">Clear filter</button>
            )}
          </div>
        </div>
      )}

      {visibleGroups.map(group => {
        const isExpanded = expandedGroups.has(group.anchor);
        let allEvents = [...group.events];
        if (activeWeek) allEvents = allEvents.filter(e => getWeek(e.date) === activeWeek);
        if (minSources > 0) allEvents = allEvents.filter(e => (e.source_title_ids?.length || 0) >= minSources);
        if (sortBy === 'date') allEvents.sort((a, b) => (a.date || '').localeCompare(b.date || ''));
        if (allEvents.length === 0) return null;
        const visibleEvents = isExpanded ? allEvents : allEvents.slice(0, initialEventsPerGroup);
        const hasMoreEvents = allEvents.length > initialEventsPerGroup;

        return (
          <div key={group.anchor} className="border border-dashboard-border rounded-lg overflow-hidden">
            <button onClick={() => toggleGroup(group.anchor)}
              className="w-full flex items-center justify-between px-4 py-3 bg-dashboard-surface hover:bg-dashboard-surface-hover transition-colors text-left">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-semibold text-dashboard-text">{group.label}</span>
                {group.topSignals && group.topSignals.length > 0 && (
                  <span className="text-xs text-dashboard-text-muted">+ {group.topSignals.join(', ')}</span>
                )}
                <span className="text-xs text-dashboard-text-muted px-2 py-0.5 rounded-full bg-dashboard-border/50">
                  {allEvents.length} {allEvents.length === 1 ? 'topic' : 'topics'} | {group.totalSources} sources
                </span>
              </div>
              <svg className={`w-4 h-4 text-dashboard-text-muted transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <div className="px-4 pb-3 space-y-1">
              {visibleEvents.map((event, i) => {
                const isBig = (event.source_title_ids?.length || 0) >= 10;
                return <EventAccordion key={`${group.anchor}-${i}`} event={event} index={i} twoLiner={!isBig} onTagFilter={handleTagFilter} />;
              })}
              {!isExpanded && hasMoreEvents && (
                <button onClick={() => toggleGroup(group.anchor)} className="text-sm text-blue-400 hover:text-blue-300 py-1">
                  + {allEvents.length - initialEventsPerGroup} more topics
                </button>
              )}
            </div>
          </div>
        );
      })}

      {hasMoreGroups && (
        <button onClick={() => setGroupsShown(prev => prev + 10)}
          className="w-full py-3 text-sm text-blue-400 hover:text-blue-300 border border-dashboard-border rounded-lg">
          Show more story groups ({filteredGroups.length - groupsShown} remaining)
        </button>
      )}

      {filteredUngrouped.length > 0 && (
        <div className="mt-4 border border-dashboard-border rounded-lg overflow-hidden">
          <button onClick={() => toggleGroup('__ungrouped__')}
            className="w-full flex items-center justify-between px-4 py-3 bg-dashboard-surface hover:bg-dashboard-surface-hover transition-colors text-left">
            <span className="text-sm text-dashboard-text-muted">
              {activeFilter ? 'Matching' : 'Other'} Topics ({filteredUngrouped.length})
            </span>
            <svg className={`w-4 h-4 text-dashboard-text-muted transition-transform ${expandedGroups.has('__ungrouped__') ? 'rotate-180' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedGroups.has('__ungrouped__') && (
            <div className="px-4 pb-3 space-y-1">
              {filteredUngrouped.slice(0, 30).map((event, i) => (
                <EventAccordion key={`ungrouped-${i}`} event={event} index={i} twoLiner onTagFilter={handleTagFilter} />
              ))}
              {filteredUngrouped.length > 30 && (
                <p className="text-xs text-dashboard-text-muted py-1">+ {filteredUngrouped.length - 30} more</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
