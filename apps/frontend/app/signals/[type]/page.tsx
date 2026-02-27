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
    description: `Ranked ${label.toLowerCase()} by event mentions, with sparkline trends and context.`,
  };
}

export default async function SignalCategoryPage({ params }: Props) {
  const { type } = await params;
  const signalType = type as SignalType;
  if (!VALID_TYPES.has(signalType)) return notFound();

  const entries = await getSignalCategoryDetail(signalType, 25);
  const label = SIGNAL_LABELS[signalType];
  const color = TYPE_COLORS[signalType];

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
            Ranked by event mentions over the last 30 days.
          </p>
        </div>

        {entries.length > 0 ? (
          <div className="border border-dashboard-border rounded-lg overflow-hidden">
            {entries.map((entry, i) => (
              <Link
                key={entry.value}
                href={`/signals/${type}/${encodeURIComponent(entry.value)}`}
                className="flex items-center gap-4 px-4 py-3 hover:bg-dashboard-border/40 transition border-b border-dashboard-border last:border-b-0 group"
              >
                {/* Rank */}
                <span className="text-sm text-dashboard-text-muted w-6 text-right shrink-0">
                  {i + 1}
                </span>

                {/* Name + context */}
                <div className="min-w-0 flex-1">
                  <span className="text-sm font-medium text-dashboard-text group-hover:text-blue-400 transition">
                    {entry.value}
                  </span>
                  {entry.context && (
                    <p className="text-xs text-dashboard-text-muted line-clamp-1 mt-0.5">
                      {entry.context}
                    </p>
                  )}
                </div>

                {/* Sparkline */}
                <div className="hidden sm:block shrink-0">
                  <Sparkline data={entry.weekly} color={color} />
                </div>

                {/* Count */}
                <span className="text-sm text-dashboard-text-muted shrink-0 w-16 text-right">
                  {entry.event_count} evt
                </span>
              </Link>
            ))}
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
