import DashboardLayout from '@/components/DashboardLayout';
import EventList from '@/components/EventList';
import EventAccordion from '@/components/EventAccordion';
import TableOfContents, { TocSection } from '@/components/TableOfContents';
import MobileTocButton from '@/components/MobileTocButton';
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
import { getTrackLabel, getCountryName, Track, Event } from '@/lib/types';
import { getTrackIcon } from '@/components/TrackCard';

export const dynamic = 'force-dynamic';

interface TrackPageProps {
  params: Promise<{ centroid_key: string; track_key: string }>;
  searchParams: Promise<{ month?: string }>;
}

function formatMonthLabel(monthStr: string): string {
  const [year, month] = monthStr.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1, 1);
  return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

// Helper functions for event processing
function countTitles(events: Event[]) {
  return events.reduce((sum, e) => sum + (e.source_title_ids?.length || 0), 0);
}

function sortBySourceCount(events: Event[]) {
  return [...events].sort((a, b) => (b.source_title_ids?.length || 0) - (a.source_title_ids?.length || 0));
}

function isOtherCoverage(e: Event) {
  return e.summary.startsWith('[Storyline]') || e.summary.startsWith('Other ') || e.is_catchall === true;
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

  // Process events for both content and TOC
  const allEvents = ctm.events_digest || [];
  const homeIsoCodes = new Set(centroid.iso_codes || []);

  const isBilateralToSelf = (e: Event) =>
    e.event_type === 'bilateral' && e.bucket_key && homeIsoCodes.has(e.bucket_key);

  const domesticEvents = allEvents.filter(
    e => !e.event_type || e.event_type === 'domestic' || isBilateralToSelf(e)
  );
  const domesticMainEvents = domesticEvents.filter(e => !isOtherCoverage(e));
  const domesticOther = domesticEvents.filter(e => isOtherCoverage(e));

  const internationalEvents = allEvents.filter(
    e => (e.event_type === 'bilateral' && !isBilateralToSelf(e)) || e.event_type === 'other_international'
  );

  // Group bilateral events by bucket_key
  const bilateralGroups: Record<string, Event[]> = {};
  const otherInternational: Event[] = [];

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

  const isSystemicBucket = (key: string) => key.startsWith('SYS-');

  const sortedBilateralEntries = Object.entries(bilateralGroups).sort(
    ([keyA, a], [keyB, b]) => {
      const aIsSys = isSystemicBucket(keyA);
      const bIsSys = isSystemicBucket(keyB);
      if (aIsSys !== bIsSys) return aIsSys ? 1 : -1;
      return countTitles(b) - countTitles(a);
    }
  );

  // Compute unclustered titles
  const eventTitleIds = new Set(allEvents.flatMap(e => e.source_title_ids || []));
  const unclusteredTitles = titles.filter(t => !eventTitleIds.has(t.id));

  // Build TOC sections
  const tocSections: TocSection[] = [];

  if (ctm.summary_text) {
    tocSections.push({ id: 'section-summary', label: 'Summary' });
  }

  if (domesticEvents.length > 0) {
    tocSections.push({
      id: 'section-domestic',
      label: 'Domestic',
      count: domesticMainEvents.length
    });
  }

  if (internationalEvents.length > 0) {
    const intlChildren: TocSection[] = [];

    sortedBilateralEntries.forEach(([bucketKey, events]) => {
      const mainEvents = events.filter(e => !isOtherCoverage(e));
      intlChildren.push({
        id: `section-intl-${bucketKey}`,
        label: getCountryName(bucketKey),
        count: mainEvents.length
      });
    });

    if (otherInternational.length > 0) {
      const mainEvents = otherInternational.filter(e => !isOtherCoverage(e));
      intlChildren.push({
        id: 'section-intl-other',
        label: 'Other International',
        count: mainEvents.length
      });
    }

    tocSections.push({
      id: 'section-international',
      label: 'International',
      count: internationalEvents.filter(e => !isOtherCoverage(e)).length,
      children: intlChildren
    });
  }

  if (unclusteredTitles.length > 0) {
    tocSections.push({
      id: 'section-other-sources',
      label: 'Other Sources',
      count: unclusteredTitles.length
    });
  }

  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm">
      {/* Month selector (desktop only - mobile uses hamburger menu) */}
      {months.length > 0 && (
        <div className="hidden lg:block">
          <h3 className="text-lg font-semibold mb-3 text-dashboard-text">View by Month</h3>
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

      {/* Other Strategic Topics (Desktop only) */}
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
                  className="flex items-center gap-3 px-4 py-3 rounded-lg bg-blue-600/20 border border-blue-500/40 cursor-default"
                >
                  <span className="text-blue-400">{getTrackIcon(t)}</span>
                  <span className="text-base font-medium text-blue-400">
                    {getTrackLabel(t as Track)}
                  </span>
                  <span className="text-xs text-blue-400/60">(current)</span>
                </div>
              ) : (
                <Link
                  key={t}
                  href={`/c/${centroid.id}/t/${t}?month=${currentMonth}`}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg bg-dashboard-border/30 hover:bg-dashboard-border
                             border border-transparent hover:border-dashboard-border
                             transition-all duration-150"
                >
                  <span className="text-dashboard-text-muted">{getTrackIcon(t)}</span>
                  <span className="text-base font-medium text-dashboard-text hover:text-white transition">
                    {getTrackLabel(t as Track)}
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>
      )}

      {/* Table of Contents (Desktop only) */}
      {tocSections.length > 0 && (
        <div className="hidden lg:block">
          <TableOfContents sections={tocSections} />
        </div>
      )}

      {/* Same track, other centroids */}
      {overlappingCentroids.length > 0 && (
        <div className="hidden lg:block bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          <h3 className="text-base font-semibold mb-3 text-dashboard-text">
            &ldquo;{getTrackLabel(track)}&rdquo; Elsewhere
          </h3>
          <div className="space-y-1">
            {overlappingCentroids.slice(0, 5).map(c => (
              <Link
                key={c.id}
                href={`/c/${c.id}/t/${track}?month=${currentMonth}`}
                className="block px-3 py-2 rounded text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border/50 transition"
              >
                {c.label}
                <span className="text-xs ml-2 opacity-60">({c.overlap_count})</span>
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
      currentMonth={currentMonth}
      availableMonths={months}
    >
      {/* Track header */}
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <div className="mb-4">
          <Link
            href={`/c/${centroid.id}?month=${currentMonth}`}
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
        <div id="section-summary" className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Summary</h2>
          <div className="text-lg leading-relaxed space-y-4">
            {ctm.summary_text.split('\n\n').map((paragraph, idx) => (
              <p key={idx}>{paragraph}</p>
            ))}
          </div>
        </div>
      )}

      {/* Events content */}
      {allEvents.length === 0 ? (
        // No events - show fallback content
        titles.length > 0 ? (
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
        ) : (
          <div className="mb-10 py-12 text-center">
            <div className="text-dashboard-text-muted">
              <p className="text-lg mb-2">No coverage available for this topic</p>
              <p className="text-sm">
                Check back later or explore other topics for {centroid.label}
              </p>
            </div>
          </div>
        )
      ) : (
        <>
          {/* Domestic section */}
          {domesticEvents.length > 0 && (
            <div id="section-domestic" className="mb-10">
              <h2 className="text-2xl font-bold mb-2">Domestic</h2>
              <p className="text-sm text-dashboard-text-muted mb-4">
                {domesticMainEvents.length} events | {countTitles(domesticEvents)} sources
              </p>

              <EventList
                events={sortBySourceCount(domesticMainEvents)}
                allTitles={titles}
                initialLimit={10}
                keyPrefix="domestic"
              />

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
            <div id="section-international" className="mb-10">
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
                  <div key={bucketKey} id={`section-intl-${bucketKey}`} className="mb-6">
                    <h3 className="text-lg font-semibold mb-3">
                      {countryName}
                      <span className="text-sm font-normal text-dashboard-text-muted ml-2">
                        {mainEvents.length} events | {countTitles(events)} sources
                      </span>
                    </h3>
                    <div className="pl-4 border-l-2 border-dashboard-border">
                      <EventList
                        events={sortBySourceCount(mainEvents)}
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
                  <div id="section-intl-other" className="mb-6">
                    <h3 className="text-lg font-semibold mb-3">
                      Other International
                      <span className="text-sm font-normal text-dashboard-text-muted ml-2">
                        {mainEvents.length} events | {countTitles(otherInternational)} sources
                      </span>
                    </h3>
                    <div className="pl-4 border-l-2 border-dashboard-border">
                      <EventList
                        events={sortBySourceCount(mainEvents)}
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

          {/* Other Sources (unclustered) */}
          {unclusteredTitles.length > 0 && (
            <div id="section-other-sources" className="mt-10 pt-6 border-t border-dashboard-border">
              <h2 className="text-xl font-bold mb-2 text-dashboard-text-muted">
                Other Sources
              </h2>
              <p className="text-sm text-dashboard-text-muted mb-4">
                {unclusteredTitles.length} additional articles not grouped into events
              </p>
              <div className="space-y-2">
                {unclusteredTitles.slice(0, 20).map((title) => (
                  <div key={title.id} className="py-2 border-b border-dashboard-border/30">
                    {title.url_gnews ? (
                      <a
                        href={title.url_gnews}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-dashboard-text-muted hover:text-blue-400 transition text-sm"
                      >
                        {title.title_display}
                      </a>
                    ) : (
                      <span className="text-dashboard-text-muted text-sm">{title.title_display}</span>
                    )}
                    {title.publisher_name && (
                      <span className="text-dashboard-text-muted/60 text-xs ml-2">
                        - {title.publisher_name}
                      </span>
                    )}
                  </div>
                ))}
                {unclusteredTitles.length > 20 && (
                  <p className="text-dashboard-text-muted text-sm pt-2">
                    ... and {unclusteredTitles.length - 20} more
                  </p>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Mobile TOC Button */}
      <MobileTocButton sections={tocSections} />
    </DashboardLayout>
  );
}
