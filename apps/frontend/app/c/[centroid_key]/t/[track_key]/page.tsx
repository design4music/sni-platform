import DashboardLayout from '@/components/DashboardLayout';
import EventList from '@/components/EventList';
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
import { getTrackLabel, getCountryName, Track } from '@/lib/types';

export const dynamic = 'force-dynamic';

interface TrackPageProps {
  params: Promise<{ centroid_key: string; track_key: string }>;
  searchParams: Promise<{ month?: string }>;
}

function formatMonthLabel(monthStr: string): string {
  // Convert "2026-01" to "January 2026"
  const [year, month] = monthStr.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1, 1);
  return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
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

      {/* Other Strategic Topics - Redesigned (Desktop only) */}
      {otherTracks.length > 0 && (
        <div className="hidden lg:block bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          <h3 className="text-xl font-bold mb-1 text-dashboard-text">
            {centroid.label}
          </h3>
          <p className="text-sm text-dashboard-text-muted mb-4">
            Other Strategic Topics
          </p>
          <nav className="space-y-1">
            {otherTracks.map(t => {
              const isCurrent = t === track;
              return isCurrent ? (
                <div
                  key={t}
                  className="block px-4 py-3 rounded-lg bg-blue-600/20 border border-blue-500/40 cursor-default"
                >
                  <span className="text-base font-medium text-blue-400">
                    {getTrackLabel(t as Track)}
                  </span>
                  <span className="ml-2 text-xs text-blue-400/60">(current)</span>
                </div>
              ) : (
                <Link
                  key={t}
                  href={`/c/${centroid.id}/t/${t}`}
                  className="block px-4 py-3 rounded-lg bg-dashboard-border/30 hover:bg-dashboard-border
                             border border-transparent hover:border-dashboard-border
                             transition-all duration-150"
                >
                  <span className="text-base font-medium text-dashboard-text hover:text-white transition">
                    {getTrackLabel(t as Track)}
                  </span>
                </Link>
              );
            })}
          </nav>
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
    <DashboardLayout
      sidebar={sidebar}
      centroidLabel={centroid.label}
      centroidId={centroid.id}
      otherTracks={otherTracks}
      currentTrack={track}
    >
      {/* Track header */}
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <div className="mb-4">
          <Link
            href={`/c/${centroid.id}`}
            className="text-blue-400 hover:text-blue-300 text-sm"
          >
            ← {centroid.label}
          </Link>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-2">
          {centroid.label}: {getTrackLabel(track)}
        </h1>
        <p className="text-dashboard-text-muted">
          {formatMonthLabel(currentMonth)} | {eventCount} events | {actualSourceCount} sources
        </p>
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
        const homeIsoCodes = new Set(centroid.iso_codes || []);

        // No events - show fallback content
        if (allEvents.length === 0) {
          // Has titles but no events - show raw titles
          if (titles.length > 0) {
            return (
              <div className="mb-10">
                <h2 className="text-2xl font-bold mb-2">Sources</h2>
                <p className="text-sm text-dashboard-text-muted mb-4">
                  {titles.length} articles collected - event clustering pending
                </p>
                <div className="space-y-2">
                  {titles.slice(0, 50).map((title) => (
                    <div key={title.id} className="py-2 border-b border-dashboard-border/50">
                      {title.url_gnews ? (
                        <a
                          href={title.url_gnews}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-dashboard-text hover:text-blue-400 transition"
                        >
                          {title.title_display}
                        </a>
                      ) : (
                        <span className="text-dashboard-text">{title.title_display}</span>
                      )}
                      {title.publisher_name && (
                        <span className="text-dashboard-text-muted text-sm ml-2">
                          - {title.publisher_name}
                        </span>
                      )}
                    </div>
                  ))}
                  {titles.length > 50 && (
                    <p className="text-dashboard-text-muted text-sm pt-2">
                      ... and {titles.length - 50} more
                    </p>
                  )}
                </div>
              </div>
            );
          }

          // No events AND no titles - show unavailable message
          return (
            <div className="mb-10 py-12 text-center">
              <div className="text-dashboard-text-muted">
                <p className="text-lg mb-2">No coverage available for this topic</p>
                <p className="text-sm">
                  Check back later or explore other topics for {centroid.label}
                </p>
              </div>
            </div>
          );
        }

        // Helper to count titles in events
        const countTitles = (events: typeof allEvents) =>
          events.reduce((sum, e) => sum + (e.source_count || e.source_title_ids?.length || 0), 0);

        // Helper to check if event is "Other Coverage" bucket
        const isOtherCoverage = (e: typeof allEvents[0]) =>
          e.summary.startsWith('[Storyline]') || e.summary.startsWith('Other ') || e.is_alias_group === true;

        // Helper to check if bilateral event is actually domestic (bucket_key matches home ISO)
        const isBilateralToSelf = (e: typeof allEvents[0]) =>
          e.event_type === 'bilateral' && e.bucket_key && homeIsoCodes.has(e.bucket_key);

        // Domestic events: no event_type, domestic, OR bilateral to self
        const domesticEvents = allEvents.filter(
          e => !e.event_type || e.event_type === 'domestic' || isBilateralToSelf(e)
        );
        const domesticMainEvents = domesticEvents.filter(e => !isOtherCoverage(e));
        const domesticOther = domesticEvents.filter(e => isOtherCoverage(e));

        // International: bilateral (not to self) and other_international
        const internationalEvents = allEvents.filter(
          e => (e.event_type === 'bilateral' && !isBilateralToSelf(e)) || e.event_type === 'other_international'
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

                {/* Main events with pagination */}
                <EventList
                  events={domesticMainEvents}
                  allTitles={titles}
                  initialLimit={10}
                  keyPrefix="domestic"
                />

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
                  const countryName = getCountryName(bucketKey);

                  return (
                    <div key={bucketKey} className="mb-6">
                      <h3 className="text-lg font-semibold mb-3">
                        {countryName}
                        <span className="text-sm font-normal text-dashboard-text-muted ml-2">
                          {mainEvents.length} events | {countTitles(events)} sources
                        </span>
                      </h3>
                      <div className="pl-4 border-l-2 border-dashboard-border">
                        <EventList
                          events={mainEvents}
                          allTitles={titles}
                          initialLimit={10}
                          compact
                          keyPrefix={`bilateral-${bucketKey}`}
                        />
                        {otherEvents.length > 0 && (
                          <div className="mt-2">
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
                          </div>
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
                      <div className="pl-4 border-l-2 border-dashboard-border">
                        <EventList
                          events={mainEvents}
                          allTitles={titles}
                          initialLimit={10}
                          compact
                          keyPrefix="other-intl"
                        />
                        {otherEvents.length > 0 && (
                          <div className="mt-2">
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
                          </div>
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


    </DashboardLayout>
  );
}
