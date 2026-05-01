'use client';

import { useMemo } from 'react';
import Link from 'next/link';
import { useLocale } from 'next-intl';
import type { CentroidMonthView } from '@/lib/types';
import StackedTrackAreaChart, { type StackedTrackPoint } from './StackedTrackAreaChart';

// Centroid month view: per-day stacked-area of source counts across the 4
// strategic tracks. Same data source as the prior CentroidHero (calendar)
// but rendered as an area chart — lighter, no day popover. Drilling down
// to a track lives on TrackCards.

const TRACKS = ['geo_security', 'geo_politics', 'geo_economy', 'geo_society'] as const;

function formatMonthLong(monthStr: string, locale: string): string {
  const [y, m] = monthStr.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', {
    month: 'long', year: 'numeric',
  });
}

function formatMonthShort(monthStr: string, locale: string): string {
  const [y, m] = monthStr.split('-').map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', { month: 'short' });
}

interface Props {
  view: CentroidMonthView;
  centroidKey: string;
  activeMonth: string; // YYYY-MM
}

export default function CentroidActivityChart({ view, centroidKey, activeMonth }: Props) {
  const locale = useLocale();

  // Stripe entries carry per-track *weights* (shares, sum~=1) rather than
  // raw counts; multiply by total_sources to recover the count.
  const data: StackedTrackPoint[] = useMemo(() => {
    return view.activity_stripe.map(entry => {
      const weightByTrack = new Map(entry.tracks.map(t => [t.track, t.weight]));
      const point: StackedTrackPoint = {
        x: entry.date,
        geo_security: 0,
        geo_politics: 0,
        geo_economy: 0,
        geo_society: 0,
      };
      for (const track of TRACKS) {
        const w = weightByTrack.get(track) || 0;
        point[track] = Math.round(w * entry.total_sources);
      }
      return point;
    });
  }, [view.activity_stripe]);

  const baseUrl = `/c/${centroidKey}`;
  const prevMonth = view.prev_month;
  const nextMonth = view.next_month;

  return (
    <section>
      {/* Month header + prev/next nav. */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <h2 className="text-2xl lg:text-3xl font-semibold text-dashboard-text min-w-0">
          {formatMonthLong(activeMonth, locale)}
        </h2>
        <div className="flex items-center gap-1 shrink-0">
          {prevMonth ? (
            <Link
              href={`${baseUrl}?month=${prevMonth}`}
              className="px-2 py-1 text-xs text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition whitespace-nowrap"
              aria-label={`Previous month: ${formatMonthShort(prevMonth, locale)}`}
            >
              ‹ {formatMonthShort(prevMonth, locale)}
            </Link>
          ) : (
            <span className="px-2 py-1 text-xs text-dashboard-text-muted opacity-30 cursor-default whitespace-nowrap">‹</span>
          )}
          {nextMonth ? (
            <Link
              href={`${baseUrl}?month=${nextMonth}`}
              className="px-2 py-1 text-xs text-dashboard-text-muted hover:text-dashboard-text border border-dashboard-border rounded hover:bg-dashboard-border/30 transition whitespace-nowrap"
              aria-label={`Next month: ${formatMonthShort(nextMonth, locale)}`}
            >
              {formatMonthShort(nextMonth, locale)} ›
            </Link>
          ) : (
            <span className="px-2 py-1 text-xs text-dashboard-text-muted opacity-30 cursor-default whitespace-nowrap">›</span>
          )}
        </div>
      </div>

      <StackedTrackAreaChart
        data={data}
        xTickFormatter={(raw) => parseInt(raw.split('-')[2], 10).toString()}
      />
    </section>
  );
}
