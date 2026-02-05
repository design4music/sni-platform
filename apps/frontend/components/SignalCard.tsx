import { TopSignal } from '@/lib/types';

interface SignalCardProps {
  signal: TopSignal;
  rank: number;
}

export default function SignalCard({ signal, rank }: SignalCardProps) {
  return (
    <div className="p-4 border border-dashboard-border bg-dashboard-surface rounded-lg">
      <div className="flex items-center justify-between mb-1">
        <h4 className={`font-semibold ${rank === 0 ? 'text-base' : 'text-sm'}`}>
          {signal.value}
        </h4>
        <span className="text-xs text-dashboard-text-muted/60 tabular-nums">
          {signal.count}
        </span>
      </div>
      {signal.context && (
        <p className="text-xs text-dashboard-text-muted leading-relaxed mt-1">
          {signal.context}
        </p>
      )}
    </div>
  );
}
