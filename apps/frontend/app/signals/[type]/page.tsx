import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import Sparkline from '@/components/signals/Sparkline';
import { getSignalCategoryDetail } from '@/lib/queries';
import { SignalType, SIGNAL_LABELS } from '@/lib/types';

export const revalidate = 300;

const VALID_TYPES = new Set<SignalType>([
  'persons', 'orgs', 'places', 'commodities', 'policies', 'systems', 'named_events',
]);

const TYPE_COLORS: Record<SignalType, string> = {
  persons: '#60a5fa',
  orgs: '#4ade80',
  places: '#fb923c',
  commodities: '#facc15',
  policies: '#a78bfa',
  systems: '#22d3ee',
  named_events: '#f472b6',
};

interface Props {
  params: Promise<{ type: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { type } = await params;
  const label = SIGNAL_LABELS[type as SignalType];
  if (!label) return { title: 'Signal Category Not Found' };
  return {
    title: `${label} - Signal Observatory`,
    description: `Ranked ${label.toLowerCase()} by event mentions over the last 30 days.`,
  };
}

/** Compute week-over-week trend from sparkline data */
function getTrend(weekly: { week: string; count: number }[]): 'up' | 'down' | 'flat' {
  if (weekly.length < 2) return 'flat';
  const last = weekly[weekly.length - 1].count;
  const prev = weekly[weekly.length - 2].count;
  if (last > prev * 1.2) return 'up';
  if (last < prev * 0.8) return 'down';
  return 'flat';
}

export default async function SignalCategoryPage({ params }: Props) {
  const { type } = await params;
  const signalType = type as SignalType;
  if (!VALID_TYPES.has(signalType)) return notFound();

  const entries = await getSignalCategoryDetail(signalType, 25);
  const label = SIGNAL_LABELS[signalType];
  const color = TYPE_COLORS[signalType];
  const maxCount = Math.max(...entries.map(e => e.event_count), 1);

  const breadcrumb = (
    <Link href="/signals" className="text-blue-400 hover:text-blue-300 text-sm">
      &larr; Signal Observatory
    </Link>
  );

  return (
    <DashboardLayout breadcrumb={breadcrumb}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold mb-2">{label}</h1>
          <p className="text-dashboard-text-muted text-sm">
            Ranked by event mentions over the last 30 days. Click any row to explore.
          </p>
        </div>

        {entries.length > 0 ? (
          <div className="border border-dashboard-border rounded-lg overflow-hidden">
            {/* Header row */}
            <div className="flex items-center gap-4 px-4 py-2 text-xs text-dashboard-text-muted uppercase tracking-wider border-b border-dashboard-border bg-dashboard-border/20">
              <span className="w-6 text-right shrink-0">#</span>
              <span className="flex-1">Signal</span>
              <span className="hidden sm:block w-[100px] shrink-0 text-center">Trend</span>
              <span className="w-20 text-right shrink-0">Events</span>
            </div>

            {entries.map((entry, i) => {
              const pct = (entry.event_count / maxCount) * 100;
              const trend = getTrend(entry.weekly);

              return (
                <Link
                  key={entry.value}
                  href={`/signals/${type}/${encodeURIComponent(entry.value)}`}
                  className="relative flex items-center gap-4 px-4 py-3 hover:bg-dashboard-border/40 transition border-b border-dashboard-border last:border-b-0 group"
                >
                  {/* Background magnitude bar */}
                  <div
                    className="absolute inset-y-0 left-0 opacity-[0.06]"
                    style={{ width: `${pct}%`, backgroundColor: color }}
                  />

                  {/* Rank */}
                  <span className="relative text-sm text-dashboard-text-muted w-6 text-right shrink-0">
                    {i + 1}
                  </span>

                  {/* Name + trend arrow */}
                  <div className="relative min-w-0 flex-1 flex items-center gap-2">
                    <span className="text-sm font-medium text-dashboard-text group-hover:text-blue-400 transition truncate">
                      {entry.value}
                    </span>
                    {trend === 'up' && (
                      <span className="text-green-400 text-xs shrink-0" title="Trending up">^</span>
                    )}
                    {trend === 'down' && (
                      <span className="text-red-400 text-xs shrink-0" title="Trending down">v</span>
                    )}
                  </div>

                  {/* Sparkline */}
                  <div className="relative hidden sm:block shrink-0">
                    <Sparkline data={entry.weekly} color={color} />
                  </div>

                  {/* Count */}
                  <span className="relative text-sm text-dashboard-text-muted shrink-0 w-20 text-right tabular-nums">
                    {entry.event_count.toLocaleString()}
                  </span>
                </Link>
              );
            })}
          </div>
        ) : (
          <p className="text-dashboard-text-muted text-center py-12">
            No signals found for this category.
          </p>
        )}
      </div>
    </DashboardLayout>
  );
}
