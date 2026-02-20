'use client';

import Link from 'next/link';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { createPortal } from 'react-dom';
import { useSession, signOut } from 'next-auth/react';
import { getTrackLabel, Track } from '@/lib/types';
import { getTrackIcon } from './TrackCard';

function formatMonth(month: string): string {
  const [year, m] = month.split('-');
  const date = new Date(parseInt(year), parseInt(m, 10) - 1);
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

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
  const { data: session } = useSession();
  const [showRegions, setShowRegions] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mobileRegionsOpen, setMobileRegionsOpen] = useState(false);
  const [mobileMonthsOpen, setMobileMonthsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchFocused, setSearchFocused] = useState(false);
  const router = useRouter();
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <>
      {/* Desktop Navigation */}
      <nav className="hidden md:flex items-center gap-6">
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

        <Link
          href="/epics"
          className="text-dashboard-text-muted hover:text-dashboard-text transition"
        >
          Epics
        </Link>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (searchQuery.trim()) {
              router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
              setSearchQuery('');
              searchRef.current?.blur();
            }
          }}
          className="relative"
        >
          <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-dashboard-text-muted pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={searchRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            placeholder="Search..."
            className={`pl-8 pr-3 py-1.5 bg-dashboard-surface border border-dashboard-border rounded-lg text-sm text-dashboard-text placeholder-dashboard-text-muted focus:outline-none focus:border-blue-500 transition-all ${
              searchFocused ? 'w-64' : 'w-48'
            }`}
          />
        </form>

        {session?.user ? (
          <div
            className="relative"
            onMouseEnter={() => setShowUserMenu(true)}
            onMouseLeave={() => setShowUserMenu(false)}
          >
            <button className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium">
              {(session.user.name || session.user.email || '?')[0].toUpperCase()}
            </button>

            {showUserMenu && (
              <div className="absolute top-full right-0 pt-1 z-50">
                <div className="w-56 bg-dashboard-surface border border-dashboard-border rounded-lg shadow-lg py-2">
                  <div className="px-4 py-2 border-b border-dashboard-border">
                    {session.user.name && (
                      <p className="text-sm font-medium text-dashboard-text">{session.user.name}</p>
                    )}
                    <p className="text-xs text-dashboard-text-muted truncate">{session.user.email}</p>
                  </div>
                  <button
                    onClick={() => signOut()}
                    className="w-full text-left px-4 py-2 text-sm text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border transition"
                  >
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <Link
            href="/auth/signin"
            className="text-sm px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition"
          >
            Sign In
          </Link>
        )}
      </nav>

      {/* Mobile Navigation Buttons */}
      <div className="flex md:hidden items-center gap-2">
        <Link
          href="/search"
          className="p-2 rounded-lg bg-dashboard-border/50 hover:bg-dashboard-border transition"
          aria-label="Search"
        >
          <svg className="w-6 h-6 text-dashboard-text" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </Link>
        <button
          onClick={() => setMobileMenuOpen(true)}
          className="p-2 rounded-lg bg-dashboard-border/50 hover:bg-dashboard-border transition"
          aria-label="Open menu"
        >
          <svg className="w-6 h-6 text-dashboard-text" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {session?.user ? (
          <button
            onClick={() => signOut()}
            className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium"
            aria-label="Sign out"
          >
            {(session.user.name || session.user.email || '?')[0].toUpperCase()}
          </button>
        ) : (
          <Link
            href="/auth/signin"
            className="p-2 rounded-lg bg-dashboard-border/50 hover:bg-dashboard-border transition"
            aria-label="Sign in"
          >
            <svg className="w-6 h-6 text-dashboard-text" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </Link>
        )}
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

              <Link
                href="/epics"
                onClick={() => setMobileMenuOpen(false)}
                className="flex flex-col items-center justify-center p-4 rounded-lg bg-dashboard-surface border border-dashboard-border hover:bg-dashboard-border transition"
              >
                <svg className="w-6 h-6 text-blue-400 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span className="text-xs text-dashboard-text-muted">Epics</span>
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
                            {formatMonth(m)}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Account */}
            <div className="rounded-lg bg-dashboard-surface border border-dashboard-border overflow-hidden">
              {session?.user ? (
                <>
                  <div className="px-4 py-3 border-b border-dashboard-border/50">
                    {session.user.name && (
                      <p className="text-sm font-medium text-dashboard-text">{session.user.name}</p>
                    )}
                    <p className="text-xs text-dashboard-text-muted truncate">{session.user.email}</p>
                  </div>
                  <button
                    onClick={() => { signOut(); setMobileMenuOpen(false); }}
                    className="w-full text-left px-4 py-3 text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border transition"
                  >
                    Sign Out
                  </button>
                </>
              ) : (
                <Link
                  href="/auth/signin"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-4 py-3 text-blue-400 hover:text-blue-300 hover:bg-dashboard-border transition"
                >
                  Sign In
                </Link>
              )}
            </div>

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
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
