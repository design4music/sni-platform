import Link from 'next/link';
import { RelatedEvent, getTrackLabel } from '@/lib/types';

interface RelatedStoriesProps {
  events: RelatedEvent[];
  thisSourceCount: number;
}

function FlagImg({ iso2 }: { iso2: string }) {
  if (!iso2 || iso2.length !== 2) return null;
  return (
    <img
      src={`https://flagcdn.com/w40/${iso2.toLowerCase()}.png`}
      alt={iso2}
      width={20}
      height={15}
      className="opacity-70 inline-block align-middle"
      style={{ objectFit: 'contain', filter: 'saturate(0.6) brightness(0.9)' }}
    />
  );
}

export default function RelatedStories({ events, thisSourceCount }: RelatedStoriesProps) {
  if (events.length === 0) return null;

  // Group by centroid to avoid showing 3 entries for "United States"
  const byCentroid = new Map<string, RelatedEvent[]>();
  for (const ev of events) {
    if (!byCentroid.has(ev.centroid_id)) byCentroid.set(ev.centroid_id, []);
    byCentroid.get(ev.centroid_id)!.push(ev);
  }

  return (
    <div className="mb-8">
      <h2 className="text-2xl font-bold mb-2">Related Coverage</h2>
      <p className="text-sm text-dashboard-text-muted mb-4">
        Same story covered from other perspectives
      </p>
      <div className="space-y-2">
        {Array.from(byCentroid.entries()).map(([centroidId, evts]) => {
          // Show the event with most shared titles as the primary
          const primary = evts[0];
          const totalShared = evts.reduce((s, e) => s + e.shared_titles, 0);
          const totalSources = evts.reduce((s, e) => s + e.source_batch_count, 0);
          const overlapPct = Math.round((totalShared / thisSourceCount) * 100);
          const isoCode = primary.iso_codes?.[0];

          return (
            <div key={centroidId} className="flex items-center gap-3 px-4 py-3 rounded-lg bg-dashboard-border/30 hover:bg-dashboard-border/50 transition-colors">
              <div className="flex-shrink-0 w-6 text-center">
                {isoCode ? <FlagImg iso2={isoCode} /> : (
                  <span className="text-dashboard-text-muted text-sm">*</span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm text-dashboard-text">
                    {primary.centroid_label}
                  </span>
                  <span className="text-xs text-dashboard-text-muted">
                    {getTrackLabel(primary.track)}
                  </span>
                </div>
                <Link
                  href={`/events/${primary.id}`}
                  className="text-xs text-blue-400 hover:text-blue-300 line-clamp-1"
                >
                  {primary.title || 'View event'}
                </Link>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0 text-xs text-dashboard-text-muted">
                <span>{totalSources} sources</span>
                <span className="px-1.5 py-0.5 rounded bg-dashboard-border" title="Shared headline overlap">
                  {overlapPct}% overlap
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
