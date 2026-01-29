import Link from 'next/link';
import { TRACK_LABELS, Track } from '@/lib/types';

interface TrackCardProps {
  centroidId: string;
  track: Track;
  latestMonth?: string;
  titleCount?: number;
  disabled?: boolean;
  hasHistoricalData?: boolean;
}

function getTrackIcon(track: string) {
  const trackLower = track.toLowerCase();

  // Military & Security
  if (trackLower.includes('military') || trackLower.includes('security') || trackLower.includes('defense')) {
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    );
  }

  // Diplomacy & Politics
  if (trackLower.includes('diplomacy') || trackLower.includes('diplomatic') || trackLower.includes('politic')) {
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    );
  }

  // Economy & Finance & Trade
  if (trackLower.includes('econom') || trackLower.includes('finance') || trackLower.includes('trade')) {
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    );
  }

  // Energy
  if (trackLower.includes('energy')) {
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    );
  }

  // Climate & Environment
  if (trackLower.includes('climate') || trackLower.includes('environment')) {
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    );
  }

  // Health & Humanitarian
  if (trackLower.includes('health') || trackLower.includes('humanitarian')) {
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
      </svg>
    );
  }

  // Technology
  if (trackLower.includes('tech') || trackLower.includes('cyber')) {
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    );
  }

  // Media
  if (trackLower.includes('media')) {
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
      </svg>
    );
  }

  // Default icon
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
  );
}

export default function TrackCard({
  centroidId,
  track,
  latestMonth,
  titleCount,
  disabled,
  hasHistoricalData
}: TrackCardProps) {
  const href = latestMonth
    ? `/c/${centroidId}/t/${track}?month=${latestMonth}`
    : `/c/${centroidId}/t/${track}`;

  const articleCount = titleCount || 0;
  const hasArticles = articleCount > 0;
  const trackLabel = TRACK_LABELS[track].replace(/^Geo\s+/i, '');

  // If disabled, render a non-interactive div instead of Link
  if (disabled) {
    return (
      <div
        className="block p-6 border border-dashboard-border bg-dashboard-surface rounded-lg opacity-50 cursor-not-allowed"
      >
        <div className="flex items-center gap-3 mb-3">
          <div className="text-dashboard-text-muted">
            {getTrackIcon(track)}
          </div>
          <h3 className="text-lg font-semibold flex-1 text-dashboard-text-muted">{trackLabel}</h3>
          <span
            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium bg-gray-500/10 border-gray-500/30 text-gray-400"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
            <span className="tabular-nums">0</span>
          </span>
        </div>
        <div className="text-sm text-dashboard-text-muted">
          {hasHistoricalData ? (
            <span>No coverage this month</span>
          ) : (
            <span>No data available</span>
          )}
        </div>
      </div>
    );
  }

  return (
    <Link
      href={href}
      className="block p-6 border border-dashboard-border bg-dashboard-surface rounded-lg hover:border-blue-500 transition"
    >
      <div className="flex items-center gap-3 mb-3">
        <div className="text-blue-400">
          {getTrackIcon(track)}
        </div>
        <h3 className="text-lg font-semibold flex-1">{trackLabel}</h3>
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium ${
            hasArticles
              ? 'bg-green-500/10 border-green-500/30 text-green-400'
              : 'bg-red-500/10 border-red-500/30 text-red-400'
          }`}
          title={hasArticles ? `${articleCount.toLocaleString()} total articles` : 'No articles yet'}
        >
          {hasArticles ? (
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          )}
          <span className="tabular-nums">{articleCount.toLocaleString()}</span>
        </span>
      </div>
      <div className="text-sm text-dashboard-text-muted">
        {latestMonth && <span>Latest: {latestMonth}</span>}
      </div>
    </Link>
  );
}
