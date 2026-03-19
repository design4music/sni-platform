import Link from 'next/link';
import Sparkline from '@/components/signals/Sparkline';
import { SignalWeekly, getCentroidLabel } from '@/lib/types';

interface Props {
  id: string;
  name: string;
  actorCentroid: string | null;
  actorLabel: string | null;
  eventCount: number;
  sparkline?: SignalWeekly[];
  matchedEventsLabel?: string;
  tCentroids?: (key: string) => string;
}

export default function NarrativeCard({ id, name, actorCentroid, actorLabel, eventCount, sparkline, matchedEventsLabel, tCentroids }: Props) {
  const displayLabel = actorCentroid && actorLabel
    ? getCentroidLabel(actorCentroid, actorLabel, tCentroids)
    : actorLabel;

  return (
    <div className="flex flex-col md:flex-row md:items-center gap-1 md:gap-3 px-4 py-3 rounded-lg bg-dashboard-surface border border-dashboard-border hover:border-blue-500/40 transition">
      {/* Title -- full text on mobile, truncated on desktop */}
      <Link href={`/narratives/${id}`} className="md:flex-1 md:min-w-0">
        <p className="text-sm font-medium text-dashboard-text md:truncate hover:text-blue-400 transition">
          {name}
        </p>
      </Link>
      {/* Meta row: actor, sparkline, event count -- stacked below title on mobile */}
      <div className="flex items-center gap-3">
        {displayLabel && actorCentroid && (
          <Link
            href={`/c/${actorCentroid}`}
            className="text-xs text-dashboard-text-muted hover:text-blue-400 transition shrink-0"
          >
            {displayLabel}
          </Link>
        )}
        {sparkline && sparkline.length >= 2 && (
          <div className="shrink-0">
            <Sparkline data={sparkline} width={80} height={24} />
          </div>
        )}
        <span className="text-xs text-dashboard-text-muted tabular-nums shrink-0" title={matchedEventsLabel || 'Matched events'}>
          {eventCount}
        </span>
      </div>
    </div>
  );
}
