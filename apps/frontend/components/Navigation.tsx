'use client';

import Link from 'next/link';
import { useState } from 'react';

const REGIONS = [
  { key: 'africa', label: 'Africa' },
  { key: 'americas', label: 'Americas' },
  { key: 'asia', label: 'Asia' },
  { key: 'europe', label: 'Europe' },
  { key: 'mideast', label: 'Middle East' },
  { key: 'oceania', label: 'Oceania' },
];

export default function Navigation() {
  const [showRegions, setShowRegions] = useState(false);
  const [showComingSoon, setShowComingSoon] = useState(false);

  return (
    <nav className="flex items-center gap-6">
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
        <button className="text-dashboard-text-muted hover:text-dashboard-text transition">
          Regional
        </button>

        {showRegions && (
          <div className="absolute top-full right-0 mt-1 w-48 bg-dashboard-surface border border-dashboard-border rounded-lg shadow-lg py-2 z-50">
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
        )}
      </div>

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
  );
}
