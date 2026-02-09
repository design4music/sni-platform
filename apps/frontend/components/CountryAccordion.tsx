'use client';

import { useState } from 'react';
import EventList from './EventList';
import EventAccordion from './EventAccordion';
import { Event, Title } from '@/lib/types';

function FlagImg({ iso2, size = 20 }: { iso2: string; size?: number }) {
  if (!iso2 || iso2.length !== 2) return null;
  return (
    <span className="inline-flex items-center justify-center rounded border border-blue-500/30 bg-blue-500/10 overflow-hidden align-middle"
      style={{ width: size + 6, height: Math.round(size * 0.75) + 4 }}>
      <img
        src={`https://flagcdn.com/w40/${iso2.toLowerCase()}.png`}
        alt={iso2}
        width={size}
        height={Math.round(size * 0.75)}
        className="opacity-70"
        style={{ objectFit: 'contain', filter: 'saturate(0.6) brightness(0.9)' }}
      />
    </span>
  );
}

interface CountryAccordionProps {
  bucketKey: string;
  countryName: string;
  isoCodes: string[];
  mainEvents: Event[];
  otherEvents: Event[];
  allTitles: Title[];
  totalSourceCount: number;
  defaultOpen?: boolean;
}

function countTitles(events: Event[]) {
  return events.reduce((sum, e) => sum + (e.source_title_ids?.length || 0), 0);
}

function sortBySourceCount(events: Event[]) {
  return [...events].sort((a, b) => (b.source_title_ids?.length || 0) - (a.source_title_ids?.length || 0));
}

function CatchallTitleList({ events, allTitles }: { events: Event[]; allTitles: Title[] }) {
  const [showAll, setShowAll] = useState(false);
  const titleIds = events.flatMap(e => e.source_title_ids || []);
  const titles = allTitles.filter(t => titleIds.includes(t.id));
  const displayed = showAll ? titles : titles.slice(0, 20);
  const remaining = titles.length - 20;

  return (
    <div className="space-y-1">
      {displayed.map(title => (
        <div key={title.id} className="py-1 text-sm">
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
      ))}
      {remaining > 0 && !showAll && (
        <button
          onClick={() => setShowAll(true)}
          className="mt-2 px-3 py-1.5 text-xs font-medium text-blue-400 hover:text-blue-300
                     bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30
                     rounded-lg transition-all duration-200"
        >
          Show {remaining} more
        </button>
      )}
    </div>
  );
}

export default function CountryAccordion({
  bucketKey,
  countryName,
  isoCodes,
  mainEvents,
  otherEvents,
  allTitles,
  totalSourceCount,
  defaultOpen = false,
}: CountryAccordionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div id={`section-intl-${bucketKey}`} className="mb-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-3 rounded-lg bg-dashboard-border/50 hover:bg-dashboard-border transition-colors"
        aria-expanded={isOpen}
      >
        <span className="text-left">
          <span className="text-lg font-semibold text-dashboard-text">
            {isoCodes.length === 1 && isoCodes[0].length === 2 && (
              <span className="mr-2"><FlagImg iso2={isoCodes[0]} /></span>
            )}
            {countryName}
          </span>
          {isoCodes.length > 1 && (
            <span className="flex items-center gap-1 mt-0.5">
              {isoCodes.map(iso => (
                <FlagImg key={iso} iso2={iso} size={16} />
              ))}
            </span>
          )}
        </span>
        <span className="flex items-center gap-3 flex-shrink-0">
          <span className="text-sm text-dashboard-text-muted">
            {mainEvents.length} topics | {totalSourceCount} sources
          </span>
          <span
            className={`text-dashboard-text-muted transition-transform duration-200 ${isOpen ? 'rotate-90' : ''}`}
          >
            &#9656;
          </span>
        </span>
      </button>

      {isOpen && (
        <div className="mt-2 pl-4 border-l-2 border-dashboard-border">
          {mainEvents.length > 0 ? (
            <>
              <EventList
                events={sortBySourceCount(mainEvents)}
                allTitles={allTitles}
                initialLimit={10}
                compact
                keyPrefix={`bilateral-${bucketKey}`}
              />
              {otherEvents.length > 0 && (
                <div className="mt-2">
                  <EventAccordion
                    key={`bilateral-${bucketKey}-other`}
                    event={{
                      date: otherEvents[0]?.date || '',
                      summary: `Other ${countryName} Coverage (${countTitles(otherEvents)} sources)`,
                      source_title_ids: otherEvents.flatMap(e => e.source_title_ids || [])
                    }}
                    allTitles={allTitles}
                    index={998}
                    compact
                  />
                </div>
              )}
            </>
          ) : otherEvents.length > 0 ? (
            <CatchallTitleList
              events={otherEvents}
              allTitles={allTitles}
            />
          ) : null}
        </div>
      )}
    </div>
  );
}
