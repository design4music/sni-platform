'use client';

import { useState } from 'react';
import Link from 'next/link';

interface SourceFeed {
  id: string;
  name: string;
  language_code: string;
  source_domain?: string;
  url: string;
  total_titles: number;
  assigned_titles: number;
  logoUrl: string;
  domain: string;
}

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

interface SourceCountryAccordionProps {
  countryCode: string;
  countryName: string;
  feeds: SourceFeed[];
}

export default function SourceCountryAccordion({ countryCode, countryName, feeds }: SourceCountryAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);

  const languages = new Set(feeds.map(f => f.language_code));

  return (
    <div className="mb-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-3 rounded-lg bg-dashboard-border/50 hover:bg-dashboard-border transition-colors"
        aria-expanded={isOpen}
      >
        <span className="flex items-center gap-2 text-left">
          {countryCode !== 'GLOBAL' && <FlagImg iso2={countryCode} />}
          <span className="text-lg font-semibold text-dashboard-text">
            {countryName}
          </span>
        </span>
        <span className="flex items-center gap-3 flex-shrink-0">
          <span className="text-sm text-dashboard-text-muted">
            {feeds.length} {feeds.length === 1 ? 'source' : 'sources'} | {languages.size} {languages.size === 1 ? 'language' : 'languages'}
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
          <div className="divide-y divide-dashboard-border/50">
            {feeds.map(feed => (
              <div
                key={feed.id}
                className="flex items-center gap-4 py-3 px-2 -mx-2 rounded hover:bg-dashboard-surface transition-colors group"
              >
                <img
                  src={feed.logoUrl}
                  alt=""
                  className="w-5 h-5 flex-shrink-0 object-contain"
                />
                <Link
                  href={`/sources/${encodeURIComponent(feed.name)}`}
                  className="font-medium text-dashboard-text group-hover:text-blue-400 transition-colors flex-1 min-w-0 truncate"
                >
                  {feed.name}
                </Link>
                <span className="text-xs text-dashboard-text-muted flex-shrink-0 uppercase">
                  {feed.language_code}
                </span>
                {feed.total_titles > 0 && (
                  <span
                    className="text-xs text-dashboard-text-muted flex-shrink-0 tabular-nums w-24 text-right"
                    title={`${feed.assigned_titles.toLocaleString()} matched to countries / ${feed.total_titles.toLocaleString()} ingested`}
                  >
                    {feed.assigned_titles.toLocaleString()} / {feed.total_titles.toLocaleString()}
                  </span>
                )}
                <a
                  href={`https://${feed.domain}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-shrink-0"
                >
                  <svg
                    className="w-3.5 h-3.5 text-dashboard-text-muted/50 hover:text-white transition-colors"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
