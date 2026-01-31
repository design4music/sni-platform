'use client';

import { useState } from 'react';
import EventList from './EventList';
import EventAccordion from './EventAccordion';
import { Event, Title } from '@/lib/types';

function getCountryFlag(iso2?: string): string {
  if (!iso2 || iso2.length !== 2) return '';
  const codePoints = iso2
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
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

  const flag = isoCodes.length === 1 ? getCountryFlag(isoCodes[0]) : '';

  return (
    <div id={`section-intl-${bucketKey}`} className="mb-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-3 rounded-lg bg-dashboard-border/50 hover:bg-dashboard-border transition-colors"
        aria-expanded={isOpen}
      >
        <span className="text-left">
          <span className="text-lg font-semibold text-dashboard-text">
            {flag && (
              <span className="mr-2 text-xl align-middle">{flag}</span>
            )}
            {countryName}
          </span>
          {isoCodes.length > 1 && (
            <span className="block text-xs text-dashboard-text-muted mt-0.5">
              {isoCodes.map(iso => getCountryFlag(iso) || iso).join(' ')}
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
        </div>
      )}
    </div>
  );
}
