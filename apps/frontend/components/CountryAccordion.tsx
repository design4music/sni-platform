'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import EventList from './EventList';
import OtherCoverage from './OtherCoverage';
import { Event } from '@/lib/types';

function FlagImg({ iso2, size = 20 }: { iso2: string; size?: number }) {
  if (!iso2 || iso2.length !== 2) return null;
  return (
    <span className="inline-flex items-center justify-center rounded border border-blue-500/30 bg-blue-500/10 overflow-hidden align-middle"
      style={{ width: size + 6, height: Math.round(size * 0.75) + 4 }}>
      <img
        src={`/flags/${iso2.toLowerCase()}.png`}
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
  totalSourceCount: number;
  defaultOpen?: boolean;
  centroidLink?: string;
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
  totalSourceCount,
  defaultOpen = false,
  centroidLink,
}: CountryAccordionProps) {
  const tTrack = useTranslations('track');
  const tCommon = useTranslations('common');
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
            {centroidLink && (
              <Link
                href={centroidLink}
                scroll
                onClick={(e) => e.stopPropagation()}
                className="inline-flex items-center ml-2 text-xs text-blue-400/60 hover:text-blue-400 transition align-middle"
                title={`${countryName} profile`}
              >
                &#8599;
              </Link>
            )}
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
            {tCommon('topicsCount', { count: mainEvents.length })} | {tCommon('sourcesCount', { count: totalSourceCount })}
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
                initialLimit={10}
                compact
                keyPrefix={`bilateral-${bucketKey}`}
              />
              {otherEvents.length > 0 && (
                <OtherCoverage
                  label={tTrack('otherCoverage', { country: countryName })}
                  events={otherEvents}
                />
              )}
            </>
          ) : otherEvents.length > 0 ? (
            <OtherCoverage
              label={tTrack('otherCoverage', { country: countryName })}
              events={otherEvents}
              flat
            />
          ) : null}
        </div>
      )}
    </div>
  );
}
