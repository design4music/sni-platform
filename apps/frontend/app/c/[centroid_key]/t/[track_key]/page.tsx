import ReadingLayout from '@/components/ReadingLayout';
import {
  getCentroidById,
  getCTM,
  getCTMMonths,
  getTitlesByCTM,
  getTracksByCentroid,
  getCentroidsWithTrack,
} from '@/lib/queries';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { TRACK_LABELS, Track } from '@/lib/types';

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
  const centroidsWithTrack = await getCentroidsWithTrack(track);

  const currentMonth = month || months[0];

  const sidebar = (
    <div className="space-y-6 text-sm">
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

      {/* Other tracks for same centroid */}
      {otherTracks.length > 1 && (
        <div>
          <h3 className="text-lg font-semibold mb-3 text-dashboard-text">Other Tracks</h3>
          <div className="space-y-1">
            {otherTracks
              .filter(t => t !== track)
              .map(t => (
                <Link
                  key={t}
                  href={`/c/${centroid.id}/t/${t}`}
                  className="block text-dashboard-text-muted hover:text-dashboard-text transition"
                >
                  {TRACK_LABELS[t as Track]}
                </Link>
              ))}
          </div>
        </div>
      )}

      {/* Same track on other centroids */}
      {centroidsWithTrack.length > 1 && (
        <div>
          <h3 className="text-lg font-semibold mb-3 text-dashboard-text">
            {TRACK_LABELS[track]} Elsewhere
          </h3>
          <div className="space-y-1">
            {centroidsWithTrack
              .filter(c => c.id !== centroid.id)
              .slice(0, 10)
              .map(c => (
                <Link
                  key={c.id}
                  href={`/c/${c.id}/t/${track}`}
                  className="block text-dashboard-text-muted hover:text-dashboard-text transition"
                >
                  {c.label}
                </Link>
              ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <ReadingLayout sidebar={sidebar}>
      {/* Track header */}
      <div className="mb-8 pb-8 border-b border-reading-border">
        <div className="mb-4">
          <Link
            href={`/c/${centroid.id}`}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            ← {centroid.label}
          </Link>
        </div>
        <h1 className="text-4xl font-bold mb-2">{TRACK_LABELS[track]}</h1>
        <p className="text-xl text-reading-text-muted">
          {currentMonth} • {ctm.title_count} articles
        </p>
      </div>

      {/* CTM Summary */}
      {ctm.summary_text && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Summary</h2>
          <div className="text-lg leading-relaxed text-reading-text">
            {ctm.summary_text}
          </div>
        </div>
      )}

      {/* Events Digest */}
      {ctm.events_digest && ctm.events_digest.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Key Events</h2>
          <div className="space-y-4">
            {ctm.events_digest.map((event, idx) => (
              <div key={idx} className="border-l-4 border-blue-500 pl-4">
                <p className="text-sm text-reading-text-muted mb-1">{event.date}</p>
                <p className="text-reading-text">{event.summary}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Source Articles */}
      {titles.length > 0 && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Source Articles</h2>
          <div className="space-y-3">
            {titles.map(title => (
              <div key={title.id} className="pb-3 border-b border-reading-border">
                {title.url_gnews ? (
                  <a
                    href={title.url_gnews}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 font-medium"
                  >
                    {title.title_display}
                  </a>
                ) : (
                  <p className="font-medium">{title.title_display}</p>
                )}
                <div className="text-sm text-reading-text-muted mt-1">
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
      )}

      {/* AI disclaimer */}
      <div className="mt-12 pt-8 border-t border-reading-border">
        <p className="text-sm text-reading-text-muted italic">
          This narrative was generated by AI based on {ctm.title_count} source articles.
          All content should be independently verified for critical applications.
        </p>
      </div>
    </ReadingLayout>
  );
}
