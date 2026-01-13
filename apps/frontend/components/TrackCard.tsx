import Link from 'next/link';
import { TRACK_LABELS, Track } from '@/lib/types';

interface TrackCardProps {
  centroidId: string;
  track: Track;
  latestMonth?: string;
  titleCount?: number;
}

export default function TrackCard({ centroidId, track, latestMonth, titleCount }: TrackCardProps) {
  const href = latestMonth
    ? `/c/${centroidId}/t/${track}?month=${latestMonth}`
    : `/c/${centroidId}/t/${track}`;

  return (
    <Link
      href={href}
      className="block p-6 border border-dashboard-border bg-dashboard-surface rounded-lg hover:border-blue-500 transition"
    >
      <h3 className="text-lg font-semibold mb-2">{TRACK_LABELS[track]}</h3>
      <div className="flex gap-4 text-sm text-dashboard-text-muted">
        {latestMonth && <span>Latest: {latestMonth}</span>}
        {titleCount !== undefined && <span>{titleCount} articles</span>}
      </div>
    </Link>
  );
}
