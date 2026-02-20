import Link from 'next/link';
import { RelatedEvent, getTrackLabel } from '@/lib/types';

interface RelatedStoriesProps {
  events: RelatedEvent[];
}

function FlagImg({ iso2 }: { iso2: string }) {
  if (!iso2 || iso2.length !== 2) return null;
  return (
    <img
      src={`/flags/${iso2.toLowerCase()}.png`}
      alt={iso2}
      width={20}
      height={15}
      className="opacity-70 inline-block align-middle"
      style={{ objectFit: 'contain', filter: 'saturate(0.6) brightness(0.9)' }}
    />
  );
}

export default function RelatedStories({ events }: RelatedStoriesProps) {
  if (events.length === 0) return null;

  // Show top event per centroid (most shared titles), skip duplicates
  const seen = new Set<string>();
  const unique: RelatedEvent[] = [];
  for (const ev of events) {
    if (!seen.has(ev.centroid_id)) {
      seen.add(ev.centroid_id);
      unique.push(ev);
    }
  }

  return (
    <div className="mb-8">
      <h2 className="text-2xl font-bold mb-2">Related Coverage</h2>
      <p className="text-sm text-dashboard-text-muted mb-4">
        Same story covered from other perspectives
      </p>
      <div className="space-y-2">
        {unique.map((ev) => {
          const isoCode = ev.iso_codes?.[0];

          return (
            <Link
              key={ev.id}
              href={`/events/${ev.id}`}
              className="flex items-center gap-3 px-4 py-3 rounded-lg bg-dashboard-border/30 hover:bg-dashboard-border/50 transition-colors"
            >
              <div className="flex-shrink-0 w-6 text-center">
                {isoCode ? <FlagImg iso2={isoCode} /> : (
                  <span className="text-dashboard-text-muted text-sm">*</span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm text-dashboard-text">
                    {ev.centroid_label}
                  </span>
                  <span className="text-xs text-dashboard-text-muted">
                    {getTrackLabel(ev.track)}
                  </span>
                </div>
                <span className="text-xs text-dashboard-text-muted line-clamp-1">
                  {ev.title || 'View event'}
                </span>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0 text-xs text-dashboard-text-muted">
                <span>{ev.source_batch_count} sources</span>
                <span className="px-1.5 py-0.5 rounded bg-dashboard-border"
                  title={`${ev.shared_titles} headlines appear in both this topic and the related one`}>
                  {ev.shared_titles} shared
                </span>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
