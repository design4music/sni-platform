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
  const actualSourceCount = titles.length;

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
            <span>{actualSourceCount} sources</span>
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

      {/* Events split into Domestic and International sections */}
      {(() => {
        const allEvents = ctm.events_digest || [];

        // Helper to count titles in events
        const countTitles = (events: typeof allEvents) =>
          events.reduce((sum, e) => sum + (e.source_title_ids?.length || 0), 0);

        // Helper to check if event is "Other Coverage" bucket
        const isOtherCoverage = (e: typeof allEvents[0]) =>
          e.summary.startsWith('[Storyline]') || e.summary.startsWith('Other ') || e.is_alias_group === true;

        // Domestic events (no event_type or domestic)
        const domesticEvents = allEvents.filter(
          e => !e.event_type || e.event_type === 'domestic'
        );
        const domesticMainEvents = domesticEvents.filter(e => !isOtherCoverage(e));
        const domesticOther = domesticEvents.filter(e => isOtherCoverage(e));

        // International: bilateral and other_international
        const internationalEvents = allEvents.filter(
          e => e.event_type === 'bilateral' || e.event_type === 'other_international'
        );

        // Group bilateral events by bucket_key
        const bilateralGroups: Record<string, typeof internationalEvents> = {};
        const otherInternational: typeof internationalEvents = [];

        internationalEvents.forEach(event => {
          if (event.event_type === 'bilateral' && event.bucket_key) {
            if (!bilateralGroups[event.bucket_key]) {
              bilateralGroups[event.bucket_key] = [];
            }
            bilateralGroups[event.bucket_key].push(event);
          } else {
            otherInternational.push(event);
          }
        });

        // Sort bilateral groups by title count (descending)
        const sortedBilateralEntries = Object.entries(bilateralGroups).sort(
          ([, a], [, b]) => countTitles(b) - countTitles(a)
        );

        return (
          <>
            {/* Domestic section */}
            {domesticEvents.length > 0 && (
              <div className="mb-10">
                <h2 className="text-2xl font-bold mb-2">Domestic</h2>
                <p className="text-sm text-dashboard-text-muted mb-4">
                  {domesticMainEvents.length} events | {countTitles(domesticEvents)} sources
                </p>

                {/* Main events */}
                <div className="space-y-3">
                  {domesticMainEvents.map((event, idx) => (
                    <EventAccordion
                      key={`domestic-${idx}`}
                      event={event}
                      allTitles={titles}
                      index={idx}
                    />
                  ))}
                </div>

                {/* Other Domestic Events */}
                {domesticOther.length > 0 && (
                  <div className="mt-6 pt-4 border-t border-dashboard-border">
                    <EventAccordion
                      key="domestic-other"
                      event={{
                        date: domesticOther[0]?.date || '',
                        summary: `Other Domestic Events (${countTitles(domesticOther)} sources)`,
                        source_title_ids: domesticOther.flatMap(e => e.source_title_ids || [])
                      }}
                      allTitles={titles}
                      index={999}
                    />
                  </div>
                )}
              </div>
            )}

            {/* International section */}
            {internationalEvents.length > 0 && (
              <div className="mb-10">
                <h2 className="text-2xl font-bold mb-2">International</h2>
                <p className="text-sm text-dashboard-text-muted mb-6">
                  {internationalEvents.filter(e => !isOtherCoverage(e)).length} events | {countTitles(internationalEvents)} sources
                </p>

                {/* Bilateral groups by country */}
                {sortedBilateralEntries.map(([bucketKey, events]) => {
                  const mainEvents = events.filter(e => !isOtherCoverage(e));
                  const otherEvents = events.filter(e => isOtherCoverage(e));
                  // Extract country name from bucket_key like "ASIA-CHINA" -> "China"
                  const countryName = bucketKey.split('-').pop() || bucketKey;

                  return (
                    <div key={bucketKey} className="mb-6">
                      <h3 className="text-lg font-semibold mb-3">
                        {countryName}
                        <span className="text-sm font-normal text-dashboard-text-muted ml-2">
                          {mainEvents.length} events | {countTitles(events)} sources
                        </span>
                      </h3>
                      <div className="space-y-2 pl-4 border-l-2 border-dashboard-border">
                        {mainEvents.map((event, idx) => (
                          <EventAccordion
                            key={`bilateral-${bucketKey}-${idx}`}
                            event={event}
                            allTitles={titles}
                            index={idx}
                            compact
                          />
                        ))}
                        {otherEvents.length > 0 && (
                          <EventAccordion
                            key={`bilateral-${bucketKey}-other`}
                            event={{
                              date: otherEvents[0]?.date || '',
                              summary: `Other ${countryName} Coverage (${countTitles(otherEvents)} sources)`,
                              source_title_ids: otherEvents.flatMap(e => e.source_title_ids || [])
                            }}
                            allTitles={titles}
                            index={998}
                            compact
                          />
                        )}
                      </div>
                    </div>
                  );
                })}

                {/* Other International */}
                {otherInternational.length > 0 && (() => {
                  const mainEvents = otherInternational.filter(e => !isOtherCoverage(e));
                  const otherEvents = otherInternational.filter(e => isOtherCoverage(e));

                  return (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold mb-3">
                        Other International
                        <span className="text-sm font-normal text-dashboard-text-muted ml-2">
                          {mainEvents.length} events | {countTitles(otherInternational)} sources
                        </span>
                      </h3>
                      <div className="space-y-2 pl-4 border-l-2 border-dashboard-border">
                        {mainEvents.map((event, idx) => (
                          <EventAccordion
                            key={`other-intl-${idx}`}
                            event={event}
                            allTitles={titles}
                            index={idx}
                            compact
                          />
                        ))}
                        {otherEvents.length > 0 && (
                          <EventAccordion
                            key="other-intl-other"
                            event={{
                              date: otherEvents[0]?.date || '',
                              summary: `Other Coverage (${countTitles(otherEvents)} sources)`,
                              source_title_ids: otherEvents.flatMap(e => e.source_title_ids || [])
                            }}
                            allTitles={titles}
                            index={997}
                            compact
                          />
                        )}
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}
          </>
        );
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
