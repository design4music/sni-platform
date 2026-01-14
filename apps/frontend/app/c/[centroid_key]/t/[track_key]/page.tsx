import DashboardLayout from '@/components/DashboardLayout';
import EventAccordion from '@/components/EventAccordion';
import {
  getCentroidById,
  getCTM,
  getCTMMonths,
  getTitlesByCTM,
  getTracksByCentroid,
  getOverlappingCentroidsForTrack,
} from '@/lib/queries';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getTrackLabel, Track } from '@/lib/types';

export const dynamic = 'force-dynamic';

interface TrackPageProps {
  params: Promise<{ centroid_key: string; track_key: string }>;
  searchParams: Promise<{ month?: string }>;
}

export default async function TrackPage({ params, searchParams }: TrackPageProps) {
  const { centroid_key, track_key } = await params;
  const { month } = await searchParams;

  const centroid = await getCentroidById(centroid_key);
  if (!centroid) {
    notFound();
  }

  const track = track_key as Track;

  const ctm = await getCTM(centroid.id, track, month);
  if (!ctm) {
    notFound();
  }

  const titles = await getTitlesByCTM(ctm.id);
  const months = await getCTMMonths(centroid.id, track);
  const otherTracks = await getTracksByCentroid(centroid.id);
  const overlappingCentroids = await getOverlappingCentroidsForTrack(centroid.id, track);

  const currentMonth = month || months[0];
  const eventCount = ctm.events_digest?.length || 0;

  const sidebar = (
    <div className="space-y-6 text-sm">
      {/* Context Block */}
      <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
        <h3 className="text-xs uppercase tracking-wide text-dashboard-text-muted mb-3">Context</h3>
        <div className="space-y-2">
          <p className="text-dashboard-text font-medium">
            {centroid.label} · {getTrackLabel(track)}
          </p>
          <p className="text-dashboard-text-muted">
            {currentMonth}
          </p>
          <div className="flex gap-4 text-xs text-dashboard-text-muted pt-2">
            <span>{eventCount} events</span>
            <span>{ctm.title_count} sources</span>
          </div>
        </div>
      </div>

      {/* Month selector */}
      {months.length > 1 && (
        <div>
          <h3 className="text-lg font-semibold mb-3 text-dashboard-text">Archive</h3>
          <div className="space-y-1">
            {months.map(m => {
              const isCurrent = m === currentMonth;
              return (
                <Link
                  key={m}
                  href={`/c/${centroid.id}/t/${track}?month=${m}`}
                  className={`block px-3 py-2 rounded ${
                    isCurrent
                      ? 'bg-blue-600 text-white'
                      : 'text-dashboard-text-muted hover:bg-dashboard-border'
                  }`}
                >
                  {m}
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Other topics for same centroid */}
      {otherTracks.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3 text-dashboard-text">Other Topics</h3>
          <div className="space-y-1">
            {otherTracks.map(t => {
              const isCurrent = t === track;
              return isCurrent ? (
                <span
                  key={t}
                  className="block text-dashboard-text cursor-default opacity-50"
                >
                  {getTrackLabel(t as Track)}
                </span>
              ) : (
                <Link
                  key={t}
                  href={`/c/${centroid.id}/t/${t}`}
                  className="block text-dashboard-text-muted hover:text-dashboard-text transition"
                >
                  {getTrackLabel(t as Track)}
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Same track, other centroids */}
      {overlappingCentroids.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3 text-dashboard-text">
            Topic "{getTrackLabel(track)}" Elsewhere
          </h3>
          <div className="space-y-1">
            {overlappingCentroids.map(c => (
              <Link
                key={c.id}
                href={`/c/${c.id}/t/${track}`}
                className="block text-dashboard-text-muted hover:text-dashboard-text transition"
              >
                {c.label}
                <span className="text-xs ml-2">({c.overlap_count} shared)</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <DashboardLayout sidebar={sidebar}>
      {/* Track header */}
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <div className="mb-4">
          <Link
            href={`/c/${centroid.id}`}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            ← {centroid.label}
          </Link>
        </div>
        <h1 className="text-4xl font-bold">
          {centroid.label}: {getTrackLabel(track)}
        </h1>
      </div>

      {/* CTM Summary */}
      {ctm.summary_text && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Summary</h2>
          <div className="text-lg leading-relaxed space-y-4">
            {ctm.summary_text.split('\n\n').map((paragraph, idx) => (
              <p key={idx}>{paragraph}</p>
            ))}
          </div>
        </div>
      )}

      {/* Events Digest with Related Articles */}
      {ctm.events_digest && ctm.events_digest.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Key Events</h2>
          <div className="space-y-4">
            {ctm.events_digest.map((event, idx) => (
              <EventAccordion
                key={idx}
                event={event}
                allTitles={titles}
                index={idx}
              />
            ))}
          </div>
        </div>
      )}

      {/* Unassigned Source Articles (titles not linked to any event) */}
      {(() => {
        const assignedTitleIds = new Set(
          ctm.events_digest?.flatMap(e => e.source_title_ids || []) || []
        );
        const unassignedTitles = titles.filter(t => !assignedTitleIds.has(t.id));

        return unassignedTitles.length > 0 ? (
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">Other Sources</h2>
            <div className="space-y-3">
              {unassignedTitles.map(title => (
                <div key={title.id} className="pb-3 border-b border-dashboard-border">
                  {title.url_gnews ? (
                    <a
                      href={title.url_gnews}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 font-medium"
                    >
                      {title.title_display}
                    </a>
                  ) : (
                    <p className="font-medium text-dashboard-text">{title.title_display}</p>
                  )}
                  <div className="text-sm text-dashboard-text-muted mt-1">
                    {title.publisher_name && <span>{title.publisher_name}</span>}
                    {title.pubdate_utc && (
                      <span className="ml-2">
                        {new Date(title.pubdate_utc).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null;
      })()}

      {/* AI disclaimer */}
      <div className="mt-12 pt-8 border-t border-dashboard-border">
        <p className="text-sm text-dashboard-text-muted italic">
          This narrative was generated by AI based on {ctm.title_count} source articles.
          All content should be independently verified for critical applications.
        </p>
      </div>
    </DashboardLayout>
  );
}
