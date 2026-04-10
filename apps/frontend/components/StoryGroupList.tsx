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

export interface CountrySection {
  countryKey: string;
  countryLabel: string;
  countryIsoCodes: string[];
  families: StoryGroup[];
  standalones: Event[];
  totalSources: number;
  totalTopics: number;
}

interface Props {
  groups: StoryGroup[];
  ungrouped: Event[];
  countrySections?: CountrySection[];
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

const MIN_DISPLAY_SOURCES = 5;

export default function StoryGroupList({
  groups,
  ungrouped,
  countrySections,
  initialGroupsShown = 15,
  initialEventsPerGroup = 5,
}: Props) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [groupsShown, setGroupsShown] = useState(initialGroupsShown);
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [minSources, setMinSources] = useState(0);
  const [sortBy, setSortBy] = useState<'sources' | 'date'>('sources');
  const [activeWeek, setActiveWeek] = useState<string | null>(null);
  const [showFilterOverlay, setShowFilterOverlay] = useState(false);

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

  // Country sections mode (new mechanical families)
  if (countrySections && countrySections.length > 0) {
    // Filter out country sections with no visible topics (all below MIN_DISPLAY_SOURCES)
    const substantialSections = countrySections.filter(s => {
      const famVisible = s.families.some(f => f.events.some(e => (e.source_title_ids?.length || 0) >= MIN_DISPLAY_SOURCES));
      const soloVisible = s.standalones.some(e => (e.source_title_ids?.length || 0) >= MIN_DISPLAY_SOURCES);
      return famVisible || soloVisible;
    });
    const sectionsShown = activeFilter ? substantialSections.length : groupsShown;
    const visibleSections = substantialSections.slice(0, sectionsShown);
    const hasMoreSections = !activeFilter && substantialSections.length > sectionsShown;

    // Collect all hidden small topics for summary
    const hiddenCount = countrySections.reduce((sum, s) => {
      const famHidden = s.families.reduce((fs, f) =>
        fs + f.events.filter(e => (e.source_title_ids?.length || 0) < MIN_DISPLAY_SOURCES).length, 0);
      const soloHidden = s.standalones.filter(e => (e.source_title_ids?.length || 0) < MIN_DISPLAY_SOURCES).length;
      return sum + famHidden + soloHidden;
    }, 0);

    return (
      <div className="space-y-3">
        {visibleSections.map(section => {
          const isExpanded = expandedGroups.has(section.countryKey);
          const isoCode = section.countryIsoCodes[0]?.toLowerCase();
          return (
            <div key={section.countryKey} className="border border-dashboard-border rounded-lg overflow-hidden">
              <button onClick={() => toggleGroup(section.countryKey)}
                className="w-full flex items-center justify-between px-4 py-3 bg-dashboard-surface hover:bg-dashboard-surface-hover transition-colors text-left">
                <div className="flex items-center gap-2.5">
                  {isoCode && (
                    <img src={`https://flagcdn.com/20x15/${isoCode}.png`}
                      alt="" className="flex-shrink-0" width={20} height={15} />
                  )}
                  <span className="text-base font-semibold text-dashboard-text">{section.countryLabel}</span>
                  <span className="text-xs text-dashboard-text-muted px-2 py-0.5 rounded-full bg-dashboard-border/50">
                    {section.totalTopics} topics | {section.totalSources} sources
                  </span>
                </div>
                <svg className={`w-4 h-4 text-dashboard-text-muted transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                  fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {isExpanded && (
                <div className="px-4 pb-3 space-y-3">
                  {/* Families within this country */}
                  {section.families.map(fam => {
                    const famEvents = fam.events.filter(e => (e.source_title_ids?.length || 0) >= MIN_DISPLAY_SOURCES);
                    if (famEvents.length === 0) return null;
                    const famSrc = famEvents.reduce((s, e) => s + (e.source_title_ids?.length || 0), 0);
                    const isFamExpanded = expandedGroups.has(fam.anchor);
                    const visibleFamEvents = isFamExpanded ? famEvents : famEvents.slice(0, initialEventsPerGroup);
                    const hasMoreFam = famEvents.length > initialEventsPerGroup;
                    return (
                      <div key={fam.anchor} className="border-l-2 border-blue-500/30 pl-3">
                        <div className="flex items-center gap-2 mb-1">
                          <a href={`/families/${fam.anchor}`}
                            className="text-sm font-medium text-dashboard-text hover:text-blue-400 transition-colors">
                            {fam.label}
                          </a>
                          <span className="text-xs text-dashboard-text-muted">{famEvents.length} topics | {famSrc} src</span>
                          {famEvents.length > initialEventsPerGroup && (
                            <button onClick={() => toggleGroup(fam.anchor)}
                              className="text-xs text-blue-400 hover:text-blue-300">
                              {expandedGroups.has(fam.anchor) ? 'less' : 'more'}
                            </button>
                          )}
                        </div>
                        {fam.topSignals && fam.topSignals[0] && (
                          <p className="text-xs text-dashboard-text-muted mb-1 leading-relaxed">{fam.topSignals[0]}</p>
                        )}
                        {visibleFamEvents.map((event, i) => {
                          const srcCount = event.source_title_ids?.length || 0;
                          const dateStr = event.date ? new Date(event.date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
                          const href = event.event_id ? `/events/${event.event_id}` : '#';
                          return (
                            <a key={`${fam.anchor}-${i}`} href={href}
                              className="flex items-start gap-2 py-1 px-1 rounded hover:bg-dashboard-surface-hover transition-colors group">
                              <span className="text-sm text-dashboard-text group-hover:text-blue-400 flex-1 line-clamp-1">{event.title}</span>
                              <span className="text-xs text-dashboard-text-muted whitespace-nowrap flex-shrink-0">
                                {dateStr && <span className="mr-2">{dateStr}</span>}
                                {srcCount} src
                              </span>
                            </a>
                          );
                        })}
                        {!isFamExpanded && hasMoreFam && (
                          <button onClick={() => toggleGroup(fam.anchor)} className="text-xs text-blue-400 hover:text-blue-300 py-0.5 ml-1">
                            + {famEvents.length - initialEventsPerGroup} more
                          </button>
                        )}
                      </div>
                    );
                  })}

                  {/* Standalone topics within this country */}
                  {section.standalones.filter(e => (e.source_title_ids?.length || 0) >= MIN_DISPLAY_SOURCES).map((event, i) => {
                    const srcCount = event.source_title_ids?.length || 0;
                    const dateStr = event.date ? new Date(event.date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
                    const href = event.event_id ? `/events/${event.event_id}` : '#';
                    return (
                      <a key={`solo-${section.countryKey}-${i}`} href={href}
                        className="flex items-start gap-2 py-1.5 px-1 rounded hover:bg-dashboard-surface-hover transition-colors group">
                        <span className="text-sm text-dashboard-text group-hover:text-blue-400 flex-1 line-clamp-1">{event.title}</span>
                        <span className="text-xs text-dashboard-text-muted whitespace-nowrap flex-shrink-0">
                          {dateStr && <span className="mr-2">{dateStr}</span>}
                          {srcCount} src
                        </span>
                      </a>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}

        {hasMoreSections && (
          <button onClick={() => setGroupsShown(prev => prev + 10)}
            className="w-full py-3 text-sm text-blue-400 hover:text-blue-300 border border-dashboard-border rounded-lg">
            Show more countries ({substantialSections.length - sectionsShown} remaining)
          </button>
        )}

        {hiddenCount > 0 && (
          <p className="text-xs text-dashboard-text-muted py-2">
            + {hiddenCount} smaller topics (under {MIN_DISPLAY_SOURCES} sources) not shown
          </p>
        )}
      </div>
    );
  }

  // Legacy flat-groups mode (fallback)
  return (
    <div className="space-y-4">
      {showFilters && (
        <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-dashboard-text">Filter topics</h3>
            {activeFilter && (
              <button onClick={() => handleFilter(null)} className="text-xs text-blue-400 hover:text-blue-300">
                Clear filter
              </button>
            )}
          </div>

          {/* Inline filters: week, min sources, sort */}
          <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-dashboard-text-muted">
            {weekOptions.length > 1 && (
              <div className="flex flex-wrap items-center gap-1.5">
                <span>Week:</span>
                <button onClick={() => setActiveWeek(null)}
                  className={`px-2 py-0.5 rounded border transition ${activeWeek === null ? 'bg-purple-600/20 border-purple-500/40 text-purple-400' : 'border-dashboard-border hover:text-dashboard-text'}`}>All</button>
                {weekOptions.map(w => (
                  <button key={w.week} onClick={() => setActiveWeek(activeWeek === w.week ? null : w.week)}
                    className={`px-2 py-0.5 rounded border transition ${activeWeek === w.week ? 'bg-purple-600/20 border-purple-500/40 text-purple-400' : 'border-dashboard-border hover:text-dashboard-text'}`}>
                    {w.label}
                  </button>
                ))}
              </div>
            )}
            <div className="flex flex-wrap items-center gap-1.5">
              <span>Min:</span>
              {[0, 5, 10, 20].map(t => (
                <button key={t} onClick={() => setMinSources(t)}
                  className={`px-2 py-0.5 rounded border transition ${minSources === t ? 'bg-blue-600/20 border-blue-500/40 text-blue-400' : 'border-dashboard-border hover:text-dashboard-text'}`}>
                  {t === 0 ? 'All' : `${t}+`}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-1.5">
              <span>Sort:</span>
              {(['sources', 'date'] as const).map(s => (
                <button key={s} onClick={() => setSortBy(s)}
                  className={`px-2 py-0.5 rounded border transition ${sortBy === s ? 'bg-blue-600/20 border-blue-500/40 text-blue-400' : 'border-dashboard-border hover:text-dashboard-text'}`}>
                  {s === 'sources' ? 'Sources' : 'Date'}
                </button>
              ))}
            </div>
          </div>

          {/* Tags & Countries button */}
          <div className="mt-3 flex items-center gap-2">
            <button onClick={() => setShowFilterOverlay(!showFilterOverlay)}
              className={`px-3 py-1.5 rounded text-xs font-medium border transition ${
                activeFilter ? 'bg-blue-600/20 border-blue-500/40 text-blue-400' : 'border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text'
              }`}>
              {activeFilter ? `Filtered: ${groups.find(g => g.anchor === activeFilter)?.label || countryFilters.find(([k]) => k === activeFilter)?.[1]?.label || 'active'}` : 'Filter by tags & countries'}
            </button>
            {activeFilter && (
              <span className="text-xs text-dashboard-text-muted">
                ({filteredGroups.reduce((s, g) => s + g.events.length, 0) + filteredUngrouped.length} matching)
              </span>
            )}
          </div>
        </div>
      )}

      {/* Tags & Countries overlay */}
      {showFilterOverlay && showFilters && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-start justify-center pt-20 px-4" onClick={() => setShowFilterOverlay(false)}>
          <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-6 max-w-lg w-full max-h-[70vh] overflow-y-auto shadow-xl"
               onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-dashboard-text">Filter by tags & countries</h3>
              <button onClick={() => setShowFilterOverlay(false)} className="text-dashboard-text-muted hover:text-dashboard-text text-xl leading-none">&times;</button>
            </div>

            {/* Tags section */}
            <div className="mb-6">
              <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">Tags ({groups.length})</h4>
              <div className="flex flex-wrap gap-1.5">
                <button onClick={() => { handleFilter(null); setShowFilterOverlay(false); }}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium border transition ${activeFilter === null ? 'bg-blue-600/20 border-blue-500/40 text-blue-400' : 'border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text'}`}>
                  All
                </button>
                {groups.map(g => (
                  <button key={g.anchor} onClick={() => { handleFilter(g.anchor); setShowFilterOverlay(false); }}
                    className={`px-2.5 py-1 rounded-full text-xs font-medium border transition ${activeFilter === g.anchor ? 'bg-blue-600/20 border-blue-500/40 text-blue-400' : 'border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text'}`}>
                    {g.label} ({g.events.length})
                  </button>
                ))}
              </div>
            </div>

            {/* Countries section */}
            {countryFilters.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">Countries ({countryFilters.length})</h4>
                <div className="flex flex-wrap gap-1.5">
                  {countryFilters.map(([key, info]) => (
                    <button key={key} onClick={() => { handleFilter(key); setShowFilterOverlay(false); }}
                      className={`px-2.5 py-1 rounded-full text-xs font-medium border transition ${activeFilter === key ? 'bg-emerald-600/20 border-emerald-500/40 text-emerald-400' : 'border-dashboard-border text-dashboard-text-muted hover:text-dashboard-text'}`}>
                      {info.label} ({info.events})
                    </button>
                  ))}
                </div>
              </div>
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
                {group.topSignals && group.topSignals.length > 0 && group.anchorType !== 'family' && (
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
              {/* Family summary paragraph */}
              {group.topSignals && group.topSignals[0] && group.anchorType === 'family' && (
                <p className="text-sm text-dashboard-text-muted py-2 border-b border-dashboard-border/30 mb-2 leading-relaxed">
                  {group.topSignals[0]}
                </p>
              )}
              {/* Compact topic list for families, full accordion for signal groups */}
              {group.anchorType === 'family' ? (
                <>
                  {visibleEvents.map((event, i) => {
                    const srcCount = event.source_title_ids?.length || 0;
                    const dateStr = event.date ? new Date(event.date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
                    const isoCodes = event.bucket_key ? [event.bucket_key] : [];
                    const href = event.event_id ? `/events/${event.event_id}` : '#';
                    return (
                      <a key={`fam-topic-${i}`} href={href}
                        className="flex items-start gap-2 py-1.5 px-1 pl-2 rounded hover:bg-dashboard-surface-hover transition-colors group">
                        {isoCodes[0] ? (
                          <img src={`https://flagcdn.com/16x12/${isoCodes[0].toLowerCase()}.png`}
                            alt="" className="mt-1 flex-shrink-0" width={16} height={12} />
                        ) : (
                          <span className="inline-block flex-shrink-0" style={{ width: 16 }} />
                        )}
                        <span className="text-sm text-dashboard-text group-hover:text-blue-400 flex-1 line-clamp-1">{event.title}</span>
                        <span className="text-xs text-dashboard-text-muted whitespace-nowrap flex-shrink-0">
                          {dateStr && <span className="mr-2">{dateStr}</span>}
                          {srcCount} src
                        </span>
                      </a>
                    );
                  })}
                  {!isExpanded && hasMoreEvents && (
                    <button onClick={() => toggleGroup(group.anchor)} className="text-sm text-blue-400 hover:text-blue-300 py-1">
                      + {allEvents.length - initialEventsPerGroup} more topics
                    </button>
                  )}
                </>
              ) : (
                <>
                  {visibleEvents.map((event, i) => {
                    const isBig = (event.source_title_ids?.length || 0) >= 10;
                    return <EventAccordion key={`${group.anchor}-${i}`} event={event} index={i} twoLiner={!isBig} onTagFilter={handleTagFilter} />;
                  })}
                  {!isExpanded && hasMoreEvents && (
                    <button onClick={() => toggleGroup(group.anchor)} className="text-sm text-blue-400 hover:text-blue-300 py-1">
                      + {allEvents.length - initialEventsPerGroup} more topics
                    </button>
                  )}
                </>
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

      {/* Standalone topics (display-worthy but not in a family) */}
      {filteredUngrouped.filter(e => (e.source_title_ids?.length || 0) >= 6).length > 0 && (
        <div className="space-y-1 mt-2">
          {filteredUngrouped.filter(e => (e.source_title_ids?.length || 0) >= 6).map((event, i) => (
            <EventAccordion key={`standalone-${i}`} event={event} index={i} twoLiner onTagFilter={handleTagFilter} />
          ))}
        </div>
      )}

      {/* Micro-clusters: collapsed summary */}
      {filteredUngrouped.filter(e => (e.source_title_ids?.length || 0) < 6).length > 0 && (
        <div className="mt-4 border border-dashboard-border rounded-lg overflow-hidden">
          <button onClick={() => toggleGroup('__micro__')}
            className="w-full flex items-center justify-between px-4 py-3 bg-dashboard-surface hover:bg-dashboard-surface-hover transition-colors text-left">
            <span className="text-sm text-dashboard-text-muted">
              + {filteredUngrouped.filter(e => (e.source_title_ids?.length || 0) < 6).reduce((s, e) => s + (e.source_title_ids?.length || 0), 0)} additional sources in {filteredUngrouped.filter(e => (e.source_title_ids?.length || 0) < 6).length} smaller topics
            </span>
            <svg className={`w-4 h-4 text-dashboard-text-muted transition-transform ${expandedGroups.has('__micro__') ? 'rotate-180' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {expandedGroups.has('__micro__') && (
            <div className="px-4 pb-3 space-y-1">
              {filteredUngrouped.filter(e => (e.source_title_ids?.length || 0) < 6).slice(0, 30).map((event, i) => (
                <EventAccordion key={`micro-${i}`} event={event} index={i} twoLiner onTagFilter={handleTagFilter} />
              ))}
              {filteredUngrouped.filter(e => (e.source_title_ids?.length || 0) < 6).length > 30 && (
                <p className="text-xs text-dashboard-text-muted py-1">+ {filteredUngrouped.filter(e => (e.source_title_ids?.length || 0) < 6).length - 30} more</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
