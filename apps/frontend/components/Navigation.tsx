'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { getTrackLabel, Track } from '@/lib/types';
import { getTrackIcon } from './TrackCard';

const REGIONS = [
  { key: 'africa', label: 'Africa' },
  { key: 'americas', label: 'Americas' },
  { key: 'asia', label: 'Asia' },
  { key: 'europe', label: 'Europe' },
  { key: 'mideast', label: 'Middle East' },
  { key: 'oceania', label: 'Oceania' },
];

interface NavigationProps {
  // For mobile: pass other tracks for current centroid
  centroidLabel?: string;
  centroidId?: string;
  otherTracks?: string[];
  currentTrack?: string;
  currentMonth?: string;
  // For mobile month selector on CTM pages
  availableMonths?: string[];
  trackForMonths?: string; // track slug for building month links
}

export default function Navigation({
  centroidLabel,
  centroidId,
  otherTracks,
  currentTrack,
  currentMonth,
  availableMonths,
  trackForMonths
}: NavigationProps) {
  const [showRegions, setShowRegions] = useState(false);
  const [showComingSoon, setShowComingSoon] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mobileRegionsOpen, setMobileRegionsOpen] = useState(false);
  const [mobileMonthsOpen, setMobileMonthsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <>
      {/* Desktop Navigation */}
      <nav className="hidden md:flex items-center gap-6">
        <Link
          href="/global"
          className="text-dashboard-text-muted hover:text-dashboard-text transition"
        >
          Global
        </Link>

        <div
          className="relative"
          onMouseEnter={() => setShowRegions(true)}
          onMouseLeave={() => setShowRegions(false)}
        >
          <button className="text-dashboard-text-muted hover:text-dashboard-text transition py-2">
            Regional
          </button>

          {showRegions && (
            <div className="absolute top-full right-0 pt-1 z-50">
              <div className="w-48 bg-dashboard-surface border border-dashboard-border rounded-lg shadow-lg py-2">
                {REGIONS.map(region => (
                  <Link
                    key={region.key}
                    href={`/region/${region.key}`}
                    className="block px-4 py-2 text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border transition"
                  >
                    {region.label}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>

        <Link
          href="/sources"
          className="text-dashboard-text-muted hover:text-dashboard-text transition"
        >
          Sources
        </Link>

        <div
          className="relative"
          onMouseEnter={() => setShowComingSoon(true)}
          onMouseLeave={() => setShowComingSoon(false)}
        >
          <div className="w-8 h-8 rounded-full bg-dashboard-border flex items-center justify-center cursor-not-allowed">
            <svg
              className="w-5 h-5 text-dashboard-text-muted"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>

          {showComingSoon && (
            <div className="absolute top-full right-0 mt-2 px-3 py-2 bg-dashboard-surface border border-dashboard-border rounded shadow-lg whitespace-nowrap text-sm text-dashboard-text-muted z-50">
              Coming soon
            </div>
          )}
        </div>
      </nav>

      {/* Mobile Navigation Buttons */}
      <div className="flex md:hidden items-center gap-2">
        <button
          onClick={() => setMobileMenuOpen(true)}
          className="p-2 rounded-lg bg-dashboard-border/50 hover:bg-dashboard-border transition"
          aria-label="Open menu"
        >
          <svg className="w-6 h-6 text-dashboard-text" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div className="w-8 h-8 rounded-full bg-dashboard-border flex items-center justify-center cursor-not-allowed">
          <svg
            className="w-5 h-5 text-dashboard-text-muted"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
        </div>
      </div>

      {/* Mobile Full-Screen Menu - Portal to escape header stacking context */}
      {mounted && mobileMenuOpen && createPortal(
        <div className="fixed inset-0 z-[100] flex flex-col" style={{ backgroundColor: '#0a0e1a' }}>
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-dashboard-border">
            <span className="text-xl font-bold text-dashboard-text">Menu</span>
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="p-2 rounded-lg bg-dashboard-border/50 hover:bg-dashboard-border transition"
              aria-label="Close menu"
            >
              <svg className="w-6 h-6 text-dashboard-text" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Menu Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Main Navigation - Compact icon buttons */}
            <div className="grid grid-cols-3 gap-3">
              <Link
                href="/global"
                onClick={() => setMobileMenuOpen(false)}
                className="flex flex-col items-center justify-center p-4 rounded-lg bg-dashboard-surface border border-dashboard-border hover:bg-dashboard-border transition"
              >
                <svg className="w-6 h-6 text-blue-400 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-xs text-dashboard-text-muted">Global</span>
              </Link>

              <button
                onClick={() => setMobileRegionsOpen(!mobileRegionsOpen)}
                className={`flex flex-col items-center justify-center p-4 rounded-lg bg-dashboard-surface border transition ${
                  mobileRegionsOpen ? 'border-blue-500 bg-blue-600/10' : 'border-dashboard-border hover:bg-dashboard-border'
                }`}
              >
                <svg className="w-6 h-6 text-blue-400 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span className="text-xs text-dashboard-text-muted">Regional</span>
              </button>

              <Link
                href="/sources"
                onClick={() => setMobileMenuOpen(false)}
                className="flex flex-col items-center justify-center p-4 rounded-lg bg-dashboard-surface border border-dashboard-border hover:bg-dashboard-border transition"
              >
                <svg className="w-6 h-6 text-blue-400 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                </svg>
                <span className="text-xs text-dashboard-text-muted">Sources</span>
              </Link>
            </div>

            {/* Regional dropdown expansion */}
            {mobileRegionsOpen && (
              <div className="rounded-lg bg-dashboard-surface border border-dashboard-border overflow-hidden">
                {REGIONS.map(region => (
                  <Link
                    key={region.key}
                    href={`/region/${region.key}`}
                    onClick={() => setMobileMenuOpen(false)}
                    className="block px-4 py-3 text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border transition border-b border-dashboard-border/50 last:border-b-0"
                  >
                    {region.label}
                  </Link>
                ))}
              </div>
            )}

            {/* Other Strategic Topics (if provided) */}
            {centroidLabel && otherTracks && otherTracks.length > 0 && (
              <div className="mt-6 pt-6 border-t border-dashboard-border">
                <h3 className="text-xl font-bold mb-2 text-dashboard-text">
                  {centroidLabel}
                </h3>
                <p className="text-sm text-dashboard-text-muted mb-4">
                  Other Strategic Topics
                </p>
                <div className="space-y-1">
                  {otherTracks.map(t => {
                    const isCurrent = t === currentTrack;
                    return isCurrent ? (
                      <div
                        key={t}
                        className="flex items-center gap-3 px-4 py-3 rounded-lg bg-blue-600/20 border border-blue-500/40"
                      >
                        <span className="text-blue-400">{getTrackIcon(t)}</span>
                        <span className="text-base font-medium text-blue-400">
                          {getTrackLabel(t as Track)}
                        </span>
                        <span className="text-xs text-blue-400/60">(current)</span>
                      </div>
                    ) : (
                      <Link
                        key={t}
                        href={`/c/${centroidId}/t/${t}${currentMonth ? `?month=${currentMonth}` : ''}`}
                        onClick={() => setMobileMenuOpen(false)}
                        className="flex items-center gap-3 px-4 py-3 rounded-lg bg-dashboard-border/30 hover:bg-dashboard-border transition"
                      >
                        <span className="text-dashboard-text-muted">{getTrackIcon(t)}</span>
                        <span className="text-base font-medium text-dashboard-text">
                          {getTrackLabel(t as Track)}
                        </span>
                      </Link>
                    );
                  })}
                </div>
              </div>
            )}

            {/* View by Month (if on CTM page with months) */}
            {centroidId && trackForMonths && availableMonths && availableMonths.length > 0 && (
              <div className="mt-6 pt-6 border-t border-dashboard-border">
                <div className="rounded-lg bg-dashboard-surface border border-dashboard-border overflow-hidden">
                  <button
                    onClick={() => setMobileMonthsOpen(!mobileMonthsOpen)}
                    className="w-full flex items-center justify-between px-4 py-4 text-lg font-medium text-dashboard-text hover:bg-dashboard-border transition"
                  >
                    <span>View by Month</span>
                    <svg
                      className={`w-5 h-5 transition-transform ${mobileMonthsOpen ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {mobileMonthsOpen && (
                    <div className="border-t border-dashboard-border">
                      {availableMonths.map(m => {
                        const isCurrent = m === currentMonth;
                        return (
                          <Link
                            key={m}
                            href={`/c/${centroidId}/t/${trackForMonths}?month=${m}`}
                            onClick={() => setMobileMenuOpen(false)}
                            className={`block px-6 py-3 transition ${
                              isCurrent
                                ? 'bg-blue-600/20 text-blue-400 font-medium'
                                : 'text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border'
                            }`}
                          >
                            {m}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
