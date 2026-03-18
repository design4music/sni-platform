import Link from 'next/link';
import Sparkline from '@/components/signals/Sparkline';
import { SignalWeekly } from '@/lib/types';

interface Props {
  id: string;
  name: string;
  actorCentroid: string | null;
  actorLabel: string | null;
  eventCount: number;
  sparkline?: SignalWeekly[];
}

export default function NarrativeCard({ id, name, actorCentroid, actorLabel, eventCount, sparkline }: Props) {
  return (
    <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-dashboard-surface border border-dashboard-border hover:border-blue-500/40 transition">
      <Link href={`/narratives/${id}`} className="flex-1 min-w-0">
        <p className="text-sm font-medium text-dashboard-text truncate hover:text-blue-400 transition">
          {name}
        </p>
      </Link>
      {actorLabel && actorCentroid && (
        <Link
          href={`/c/${actorCentroid}`}
          className="text-xs text-dashboard-text-muted hover:text-blue-400 transition shrink-0"
        >
          {actorLabel}
        </Link>
      )}
      {sparkline && sparkline.length >= 2 && (
        <div className="shrink-0">
          <Sparkline data={sparkline} width={80} height={24} />
        </div>
      )}
      <span className="text-xs text-dashboard-text-muted tabular-nums shrink-0" title="Matched events">
        {eventCount}
      </span>
    </div>
  );
}
