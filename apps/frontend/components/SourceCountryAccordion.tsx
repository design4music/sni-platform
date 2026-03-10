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
  geo_hhi: number | null;
  signal_richness: number | null;
  top_track: string | null;
}

interface SourceLabels {
  statArticles: string;
  statGeoFocus: string;
  statSignalRichness: string;
  focusBroad: string;
  focusModerate: string;
  focusNarrow: string;
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

const TRACK_MAPPING: Record<string, string> = {
  geo_politics: 'politics', geo_security: 'security', geo_economy: 'economy',
  geo_information: 'information', geo_humanitarian: 'humanitarian', geo_energy: 'energy',
};

const TRACK_COLORS: Record<string, string> = {
  politics: 'bg-purple-400', security: 'bg-red-400', economy: 'bg-green-400',
  information: 'bg-blue-400', humanitarian: 'bg-yellow-400', energy: 'bg-orange-400',
};

function TrackDot({ track }: { track: string }) {
  const main = TRACK_MAPPING[track] || track;
  const color = TRACK_COLORS[main] || 'bg-gray-400';
  return (
    <span className="flex items-center gap-1" title={main}>
      <span className={`w-2 h-2 rounded-full ${color}`} />
      <span className="text-[10px] text-dashboard-text-muted">{main}</span>
    </span>
  );
}

function GeoFocusBadge({ hhi, labels }: { hhi: number; labels: SourceLabels }) {
  const level = hhi >= 0.5 ? 'narrow' : hhi >= 0.2 ? 'moderate' : 'broad';
  const colors = {
    broad: 'text-green-400 bg-green-400/10 border-green-400/20',
    moderate: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
    narrow: 'text-red-400 bg-red-400/10 border-red-400/20',
  };
  const text = level === 'broad' ? labels.focusBroad : level === 'moderate' ? labels.focusModerate : labels.focusNarrow;
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded border ${colors[level]}`} title={`HHI: ${hhi.toFixed(2)}`}>
      {text}
    </span>
  );
}

interface SourceCountryAccordionProps {
  countryCode: string;
  countryName: string;
  feeds: SourceFeed[];
  labels: SourceLabels;
}

export default function SourceCountryAccordion({ countryCode, countryName, feeds, labels }: SourceCountryAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [sortBy, setSortBy] = useState<'name' | 'articles' | 'focus' | 'richness'>('name');

  const languages = new Set(feeds.map(f => f.language_code));

  const sorted = [...feeds].sort((a, b) => {
    switch (sortBy) {
      case 'articles': return b.assigned_titles - a.assigned_titles;
      case 'focus': return (a.geo_hhi ?? 1) - (b.geo_hhi ?? 1); // broad first
      case 'richness': return (b.signal_richness ?? 0) - (a.signal_richness ?? 0);
      default: return a.name.localeCompare(b.name);
    }
  });

  const SortBtn = ({ field, children }: { field: typeof sortBy; children: React.ReactNode }) => (
    <button
      onClick={(e) => { e.stopPropagation(); setSortBy(field); }}
      className={`text-[10px] px-1 rounded transition-colors ${sortBy === field ? 'text-blue-400 font-semibold' : 'text-dashboard-text-muted hover:text-dashboard-text'}`}
    >
      {children}
    </button>
  );

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
          {/* Sort controls */}
          <div className="flex items-center gap-1 px-2 py-1.5 mb-1">
            <span className="text-[10px] text-dashboard-text-muted mr-1">Sort:</span>
            <SortBtn field="name">A-Z</SortBtn>
            <SortBtn field="articles">{labels.statArticles}</SortBtn>
            <SortBtn field="focus">{labels.statGeoFocus}</SortBtn>
            <SortBtn field="richness">{labels.statSignalRichness}</SortBtn>
          </div>
          <div className="divide-y divide-dashboard-border/50">
            {sorted.map(feed => (
              <div
                key={feed.id}
                className="flex items-center gap-3 py-2.5 px-2 -mx-2 rounded hover:bg-dashboard-surface transition-colors group"
              >
                <img
                  src={feed.logoUrl}
                  alt=""
                  className="w-5 h-5 flex-shrink-0 object-contain"
                />
                <Link
                  href={`/sources/${encodeURIComponent(feed.name).replace(/\./g, '%2E')}`}
                  className="font-medium text-dashboard-text group-hover:text-blue-400 transition-colors min-w-0 truncate"
                  style={{ flex: '1 1 140px' }}
                >
                  {feed.name}
                </Link>

                {/* Analytics badges */}
                <div className="hidden md:flex items-center gap-2 flex-shrink-0">
                  {feed.top_track && <TrackDot track={feed.top_track} />}
                  {feed.geo_hhi !== null && <GeoFocusBadge hhi={feed.geo_hhi} labels={labels} />}
                  {feed.signal_richness !== null && (
                    <span className="text-[10px] text-dashboard-text-muted tabular-nums" title={labels.statSignalRichness}>
                      {feed.signal_richness.toFixed(1)} sig
                    </span>
                  )}
                </div>

                <span className="text-xs text-dashboard-text-muted flex-shrink-0 uppercase w-6 text-center">
                  {feed.language_code}
                </span>
                {feed.total_titles > 0 && (
                  <span
                    className="text-xs text-dashboard-text-muted flex-shrink-0 tabular-nums w-20 text-right hidden sm:inline"
                    title={`${feed.assigned_titles.toLocaleString()} matched / ${feed.total_titles.toLocaleString()} ingested`}
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
