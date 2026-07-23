import Link from 'next/link';
import Sparkline from '@/components/signals/Sparkline';
import { PositionSummary, SignalWeekly } from '@/lib/types';

interface Props {
  position: PositionSummary;
  sparkline?: SignalWeekly[];
  labels: { events: string; owner: string; nodes: string };
}

// stance_sign: -1 critical (rose), +1 supporting (emerald), 0 neutral (slate)
function stanceColor(sign: number): string {
  if (sign > 0) return 'bg-emerald-500';
  if (sign < 0) return 'bg-rose-500';
  return 'bg-slate-500';
}

export default function PositionCard({ position: p, sparkline, labels }: Props) {
  const owners = p.owner_centroids.slice(0, 3).map(o => o.label).join(', ');
  const extraOwners = p.owner_centroids.length > 3 ? ` +${p.owner_centroids.length - 3}` : '';

  return (
    <Link
      href={`/narratives/${p.id}`}
      className="group flex gap-3 px-4 py-3 rounded-lg bg-dashboard-surface border border-dashboard-border hover:border-blue-500/40 transition"
    >
      <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${stanceColor(p.stance_sign)}`} />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-dashboard-text group-hover:text-blue-400 transition">
          {p.name}
        </p>
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-dashboard-text-muted">
          {owners && (
            <span className="truncate">
              <span className="opacity-60">{labels.owner}:</span> {owners}{extraOwners}
            </span>
          )}
          {p.coalitions.slice(0, 3).map(c => (
            <span key={c.coalition} className="rounded bg-dashboard-border/60 px-1.5 py-0.5 font-mono text-[10px]">
              {c.coalition}
            </span>
          ))}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        {sparkline && sparkline.length >= 2 && (
          <div className="hidden shrink-0 sm:block">
            <Sparkline data={sparkline} width={72} height={22} />
          </div>
        )}
        <div className="flex flex-col items-end tabular-nums leading-tight">
          <span className="text-sm font-semibold text-dashboard-text" title={labels.events}>
            {p.event_count}
          </span>
          <span className="text-[10px] text-dashboard-text-muted" title={labels.nodes}>
            {p.fn_count} {labels.nodes}
          </span>
        </div>
      </div>
    </Link>
  );
}
