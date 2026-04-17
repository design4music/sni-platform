import Link from 'next/link';
import { Track, getTrackLabel } from '@/lib/types';
import { getTranslations } from 'next-intl/server';

interface TopEvent {
  id: string;
  title: string;
  date: string;
  source_count: number;
  has_event_page: boolean;
}

interface ThemeChip {
  sector: string;
  subject: string;
  weight: number;
}

interface TrackCardProps {
  centroidId: string;
  track: Track;
  latestMonth?: string;
  titleCount?: number;
  disabled?: boolean;
  hasHistoricalData?: boolean;
  lastActive?: string;
  // New (optional): top events + calendar deep-link for the enhanced hero layout
  topEvents?: TopEvent[];
  themeChips?: ThemeChip[];
  summaryText?: string | null;
  calendarHref?: string;
}

function formatThemeLabel(s: string): string {
  return s.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
}

export function getTrackIcon(track: string) {
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

  // Health & Humanitarian & Society
  if (trackLower.includes('health') || trackLower.includes('humanitarian') || trackLower.includes('society')) {
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

export default async function TrackCard({
  centroidId,
  track,
  latestMonth,
  titleCount,
  disabled,
  hasHistoricalData,
  lastActive,
  topEvents,
  themeChips,
  summaryText,
  calendarHref,
}: TrackCardProps) {
  const tTracks = await getTranslations('tracks');
  const tTrack = await getTranslations('track');
  const href =
    calendarHref ||
    (latestMonth
      ? `/c/${centroidId}/t/${track}?month=${latestMonth}`
      : `/c/${centroidId}/t/${track}`);

  const articleCount = titleCount || 0;
  const hasArticles = articleCount > 0;
  const trackLabel = getTrackLabel(track, tTracks).replace(/^Geo\s+/i, '');
  const enriched = (topEvents && topEvents.length > 0) || !!summaryText || (themeChips && themeChips.length > 0);

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
            <span>{tTrack('noCoverageThisMonth')}</span>
          ) : (
            <span>{tTrack('noDataAvailable')}</span>
          )}
        </div>
      </div>
    );
  }

  // Enriched card: header + summary + top events list (non-clickable wrapper so
  // inner event links work independently)
  if (enriched) {
    return (
      <div className="p-6 border border-dashboard-border bg-dashboard-surface rounded-lg">
        <Link
          href={href}
          className="flex items-center gap-3 mb-3 group"
        >
          <div className="text-blue-400">{getTrackIcon(track)}</div>
          <h3 className="text-lg font-semibold flex-1 group-hover:text-blue-400 transition">
            {trackLabel}
          </h3>
          <span
            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium bg-green-500/10 border-green-500/30 text-green-400"
            title={tTrack('totalArticles', { count: articleCount.toLocaleString() })}
          >
            <span className="tabular-nums">{articleCount.toLocaleString()}</span>
            {lastActive && (Date.now() - new Date(lastActive + 'T00:00:00').getTime()) < 172800000 && (
              <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" title={tTrack('activeLast48h')} />
            )}
          </span>
        </Link>

        {themeChips && themeChips.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-1.5">
            {themeChips.map((chip, i) => (
              <span
                key={`${chip.sector}-${chip.subject}-${i}`}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px]
                           bg-dashboard-border/40 border border-dashboard-border text-dashboard-text-muted"
              >
                <span className="text-dashboard-text">
                  {formatThemeLabel(chip.sector)}
                  <span className="text-dashboard-text-muted"> · {formatThemeLabel(chip.subject)}</span>
                </span>
                <span className="tabular-nums">{Math.round(chip.weight * 100)}%</span>
              </span>
            ))}
          </div>
        )}

        {summaryText && (
          <p className="text-sm text-dashboard-text-muted leading-relaxed mb-4 line-clamp-4">
            {summaryText}
          </p>
        )}

        {topEvents && topEvents.length > 0 && (
          <ul className="space-y-1.5 mb-3">
            {topEvents.map(ev => (
              <li key={ev.id}>
                {ev.has_event_page ? (
                  <Link
                    href={`/events/${ev.id}`}
                    className="flex items-start gap-2 text-sm text-dashboard-text hover:text-blue-400 transition"
                  >
                    <span className="text-dashboard-text-muted tabular-nums text-[11px] pt-0.5 shrink-0 w-6 text-right">
                      {ev.source_count}
                    </span>
                    <span className="flex-1 min-w-0 truncate">{ev.title || '(untitled)'}</span>
                  </Link>
                ) : (
                  <div className="flex items-start gap-2 text-sm text-dashboard-text-muted">
                    <span className="tabular-nums text-[11px] pt-0.5 shrink-0 w-6 text-right">
                      {ev.source_count}
                    </span>
                    <span className="flex-1 min-w-0 truncate">{ev.title || '(untitled)'}</span>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}

        <Link
          href={href}
          className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition"
        >
          View full calendar →
        </Link>
      </div>
    );
  }

  // Legacy compact card
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
          title={hasArticles ? tTrack('totalArticles', { count: articleCount.toLocaleString() }) : tTrack('noArticlesYet')}
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
          {lastActive && (Date.now() - new Date(lastActive + 'T00:00:00').getTime()) < 172800000 && (
            <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" title={tTrack('activeLast48h')} />
          )}
        </span>
      </div>
      <div className="text-sm text-dashboard-text-muted">
        {latestMonth && <span>{tTrack('latest')}: {latestMonth}</span>}
      </div>
    </Link>
  );
}
