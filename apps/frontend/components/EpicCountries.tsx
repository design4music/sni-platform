'use client';

import { useState } from 'react';
import Link from 'next/link';
import { EpicEvent } from '@/lib/types';

function FlagImg({ iso2, size = 20 }: { iso2: string; size?: number }) {
  if (!iso2 || iso2.length !== 2) return null;
  return (
    <span
      className="inline-flex items-center justify-center rounded border border-blue-500/30 bg-blue-500/10 overflow-hidden align-middle"
      style={{ width: size + 6, height: Math.round(size * 0.75) + 4 }}
    >
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

// SVG icon for SYS/NON-STATE centroids without flags
function CentroidIcon({ centroidId, size = 20 }: { centroidId: string; size?: number }) {
  const id = centroidId.toUpperCase();
  const svgSize = Math.round(size * 0.8);

  let path: string;
  if (id.includes('TRADE') || id.includes('FINANCE')) {
    path = 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
  } else if (id.includes('DIPLOMACY')) {
    path = 'M3 7l6 6h6l6-6M9 13l3 4M15 13l-3 4';
  } else if (id.includes('MILITARY')) {
    path = 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z';
  } else if (id.includes('ENERGY')) {
    path = 'M13 10V3L4 14h7v7l9-11h-7z';
  } else if (id.includes('TECH')) {
    path = 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z';
  } else if (id.includes('CLIMATE')) {
    path = 'M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z';
  } else if (id.includes('HEALTH')) {
    path = 'M12 9v6m-3-3h6M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
  } else if (id.includes('HUMANITARIAN')) {
    path = 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z';
  } else if (id.includes('MEDIA')) {
    path = 'M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z';
  } else {
    path = 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z';
  }

  return (
    <span
      className="inline-flex items-center justify-center rounded border border-blue-500/30 bg-blue-500/10 align-middle"
      style={{ width: size + 6, height: Math.round(size * 0.75) + 4 }}
    >
      <svg
        className="text-blue-400 opacity-70"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        width={svgSize}
        height={svgSize}
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={path} />
      </svg>
    </span>
  );
}

function CentroidBadge({ centroidId, isoCodes, size = 20 }: {
  centroidId: string;
  isoCodes: string[] | null;
  size?: number;
}) {
  // EU has a flag on flagcdn
  if (isoCodes?.length === 1 && isoCodes[0].length === 2) {
    return <FlagImg iso2={isoCodes[0]} size={size} />;
  }
  if (isoCodes && isoCodes.length > 1) {
    return (
      <span className="flex items-center gap-0.5">
        {isoCodes.slice(0, 3).map(iso => (
          <FlagImg key={iso} iso2={iso} size={Math.round(size * 0.8)} />
        ))}
      </span>
    );
  }
  // SYS or NON-STATE without a usable flag
  if (centroidId.startsWith('SYS-') || centroidId.startsWith('NON-STATE-')) {
    return <CentroidIcon centroidId={centroidId} size={size} />;
  }
  return null;
}

export interface CountryGroup {
  centroidId: string;
  label: string;
  displayLabel: string;
  events: EpicEvent[];
  isoCodes: string[] | null;
  summary: string | null;
}

function EpicCountryItem({ group, defaultOpen }: { group: CountryGroup; defaultOpen: boolean }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-3 rounded-lg bg-dashboard-border/50 hover:bg-dashboard-border transition-colors"
        aria-expanded={isOpen}
      >
        <span className="text-left flex items-center gap-2">
          <CentroidBadge centroidId={group.centroidId} isoCodes={group.isoCodes} />
          <span className="text-lg font-semibold text-dashboard-text">
            {group.displayLabel}
          </span>
        </span>
        <span className="flex items-center gap-3 flex-shrink-0">
          <span className="text-sm text-dashboard-text-muted">
            {group.events.length} {group.events.length === 1 ? 'topic' : 'topics'}
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
          {group.summary && (
            <p className="text-sm text-dashboard-text-muted leading-relaxed py-2 mb-1">
              {group.summary}
            </p>
          )}
          <div className="space-y-0">
            {group.events.map(ev => (
              <div key={ev.event_id} className="py-2">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-dashboard-text-muted mb-1">{ev.date}</p>
                    {ev.title ? (
                      <Link
                        href={`/c/${ev.centroid_id}/t/${ev.track}`}
                        className="text-sm font-medium text-dashboard-text hover:text-blue-400 transition"
                      >
                        {ev.title}
                      </Link>
                    ) : (
                      <p className="text-sm text-dashboard-text">
                        {ev.summary.slice(0, 120)}
                      </p>
                    )}
                  </div>
                  <span className="flex-shrink-0 text-xs text-dashboard-text-muted pt-4">
                    {ev.source_batch_count} sources
                  </span>
                </div>
              </div>
            ))}
          </div>
          {/* Link to country centroid page */}
          <div className="pt-3 pb-1">
            <Link
              href={`/c/${group.centroidId}`}
              className="text-sm text-blue-400 hover:text-blue-300 transition"
            >
              View {group.displayLabel} page &rarr;
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

export default function EpicCountries({ groups }: { groups: CountryGroup[] }) {
  return (
    <div className="space-y-2">
      {groups.map((group, i) => (
        <EpicCountryItem key={group.centroidId} group={group} defaultOpen={i === 0} />
      ))}
    </div>
  );
}
