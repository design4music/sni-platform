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

      {/* Events split into Key Events (domestic) and Activity Overview (bilateral/multilateral) */}
      {(() => {
        const allEvents = ctm.events_digest || [];

        // Helper to count titles in events
        const countTitles = (events: typeof allEvents) =>
          events.reduce((sum, e) => sum + (e.source_title_ids?.length || 0), 0);

        // Helper to check if event is a storyline
        const isStoryline = (e: typeof allEvents[0]) =>
          e.summary.startsWith('[Storyline]');

        // Helper to check if event is a systemic group
        const isAliasGroup = (e: typeof allEvents[0]) =>
          e.is_alias_group === true || (e.summary.startsWith('[') && !isStoryline(e) && e.summary.includes('] '));

        // Parse systemic event summary: "[Theme] LABEL - N sources" -> theme
        const getAliasLabel = (summary: string) => {
          const match = summary.match(/^\[([^\]]+)\]/);
          return match ? match[1] : 'Other';
        };

        // Key Events: domestic events that are NOT storyline and NOT systemic
        const keyEvents = allEvents.filter(
          e => (!e.event_type || e.event_type === 'domestic') && !isStoryline(e) && !isAliasGroup(e)
        );

        // Domestic systemic groups (mechanical events)
        const domesticAlias = allEvents.filter(
          e => e.event_type === 'domestic' && isAliasGroup(e)
        );

        // Domestic storyline (ungrouped domestic titles)
        const domesticStoryline = allEvents.find(
          e => e.event_type === 'domestic' && isStoryline(e)
        );

        // Activity Overview: bilateral and other_international bucket events
        const activityEvents = allEvents.filter(
          e => e.event_type === 'bilateral' || e.event_type === 'other_international'
        );

        // Group activity events by bucket_key for bilateral
        const bilateralGroups: Record<string, typeof activityEvents> = {};
        const otherInternationalEvents: typeof activityEvents = [];

        activityEvents.forEach(event => {
          if (event.event_type === 'bilateral' && event.bucket_key) {
            if (!bilateralGroups[event.bucket_key]) {
              bilateralGroups[event.bucket_key] = [];
            }
            bilateralGroups[event.bucket_key].push(event);
          } else if (event.event_type === 'other_international') {
            otherInternationalEvents.push(event);
          }
        });

        // Sort bilateral groups by title count (descending)
        const sortedBilateralEntries = Object.entries(bilateralGroups).sort(
          ([, a], [, b]) => countTitles(b) - countTitles(a)
        );

        return (
          <>
            {/* Key Events section */}
            {(keyEvents.length > 0 || domesticAlias.length > 0) && (
              <div className="mb-8">
                <h2 className="text-2xl font-bold mb-2">Key Events</h2>
                <p className="text-sm text-dashboard-text-muted mb-4">
                  {keyEvents.length + domesticAlias.length} items | {countTitles([...keyEvents, ...domesticAlias])} sources
                </p>

                {/* Domestic systemic groups at the top */}
                {domesticAlias.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-3 text-dashboard-text-muted">By Theme</h3>
                    <div className="space-y-2">
                      {domesticAlias.map((event, idx) => (
                        <EventAccordion
                          key={`domestic-sys-${idx}`}
                          event={{
                            ...event,
                            summary: `${getAliasLabel(event.summary)} (${event.source_title_ids?.length || 0} sources)`
                          }}
                          allTitles={titles}
                          index={idx}
                          compact
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* LLM-extracted events */}
                {keyEvents.length > 0 && (
                  <div className="space-y-4">
                    {domesticAlias.length > 0 && (
                      <h3 className="text-lg font-semibold mb-3 text-dashboard-text-muted">Specific Events</h3>
                    )}
                    {keyEvents.map((event, idx) => (
                      <EventAccordion
                        key={`key-${idx}`}
                        event={event}
                        allTitles={titles}
                        index={idx}
                      />
                    ))}
                  </div>
                )}

                {/* Domestic storyline */}
                {domesticStoryline && domesticStoryline.source_title_ids && (
                  <div className="mt-6 pt-4 border-t border-dashboard-border">
                    <EventAccordion
                      key="domestic-storyline"
                      event={{
                        ...domesticStoryline,
                        summary: `Other domestic coverage (${domesticStoryline.source_title_ids.length} sources)`
                      }}
                      allTitles={titles}
                      index={999}
                    />
                  </div>
                )}
              </div>
            )}

            {/* Activity Overview section */}
            {activityEvents.length > 0 && (
              <div className="mb-8">
                <h2 className="text-2xl font-bold mb-2">Activity Overview</h2>
                <p className="text-sm text-dashboard-text-muted mb-6">
                  {activityEvents.length} items | {countTitles(activityEvents)} sources |{' '}
                  Coverage of {centroid.label}&apos;s interactions with other countries
                </p>

                {/* Bilateral groups */}
                {sortedBilateralEntries.map(([counterparty, events]) => {
                  const aliasEvents = events.filter(e => isAliasGroup(e));
                  const llmEvents = events.filter(e => !isStoryline(e) && !isAliasGroup(e));
                  const storyline = events.find(e => isStoryline(e));
                  const groupTitleCount = countTitles(events);
                  // Extract country name from bucket_key like "ASIA-CHINA" -> "China"
                  const countryName = counterparty.split('-').pop() || counterparty;

                  return (
                    <div key={counterparty} className="mb-6">
                      <h3 className="text-lg font-semibold mb-3">
                        {countryName}
                        <span className="text-sm font-normal text-dashboard-text-muted ml-2">
                          {aliasEvents.length + llmEvents.length} items | {groupTitleCount} sources
                        </span>
                      </h3>
                      <div className="space-y-2 pl-4 border-l-2 border-dashboard-border">
                        {/* Systemic groups first */}
                        {aliasEvents.map((event, idx) => (
                          <EventAccordion
                            key={`bilateral-${counterparty}-sys-${idx}`}
                            event={{
                              ...event,
                              summary: `${getAliasLabel(event.summary)} (${event.source_title_ids?.length || 0} sources)`
                            }}
                            allTitles={titles}
                            index={idx}
                            compact
                          />
                        ))}
                        {/* LLM-extracted events */}
                        {llmEvents.map((event, idx) => (
                          <EventAccordion
                            key={`bilateral-${counterparty}-${idx}`}
                            event={event}
                            allTitles={titles}
                            index={idx}
                            compact
                          />
                        ))}
                        {storyline && storyline.source_title_ids && storyline.source_title_ids.length > 0 && (
                          <EventAccordion
                            key={`bilateral-${counterparty}-storyline`}
                            event={{
                              ...storyline,
                              summary: `Other ${countryName} coverage (${storyline.source_title_ids.length} sources)`
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

                {/* Other International News */}
                {otherInternationalEvents.length > 0 && (() => {
                  const aliasEvents = otherInternationalEvents.filter(e => isAliasGroup(e));
                  const llmEvents = otherInternationalEvents.filter(e => !isStoryline(e) && !isAliasGroup(e));
                  const storyline = otherInternationalEvents.find(e => isStoryline(e));
                  const groupTitleCount = countTitles(otherInternationalEvents);

                  return (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold mb-3">
                        Other International News
                        <span className="text-sm font-normal text-dashboard-text-muted ml-2">
                          {aliasEvents.length + llmEvents.length} items | {groupTitleCount} sources
                        </span>
                      </h3>
                      <div className="space-y-2 pl-4 border-l-2 border-dashboard-border">
                        {/* Systemic groups first */}
                        {aliasEvents.map((event, idx) => (
                          <EventAccordion
                            key={`other-intl-sys-${idx}`}
                            event={{
                              ...event,
                              summary: `${getAliasLabel(event.summary)} (${event.source_title_ids?.length || 0} sources)`
                            }}
                            allTitles={titles}
                            index={idx}
                            compact
                          />
                        ))}
                        {/* LLM-extracted events */}
                        {llmEvents.map((event, idx) => (
                          <EventAccordion
                            key={`other-intl-${idx}`}
                            event={event}
                            allTitles={titles}
                            index={idx}
                            compact
                          />
                        ))}
                        {storyline && storyline.source_title_ids && storyline.source_title_ids.length > 0 && (
                          <EventAccordion
                            key="other-intl-storyline"
                            event={{
                              ...storyline,
                              summary: `Other international coverage (${storyline.source_title_ids.length} sources)`
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
