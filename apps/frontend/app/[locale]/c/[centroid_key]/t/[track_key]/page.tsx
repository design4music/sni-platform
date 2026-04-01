import { Suspense } from 'react';
import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import EventList from '@/components/EventList';
import StoryGroupList from '@/components/StoryGroupList';
import type { StoryGroup } from '@/components/StoryGroupList';
import MobileTocButton from '@/components/MobileTocButton';
import MonthNav from '@/components/MonthNav';
import {
  getCentroidById,
  getCentroidsByIds,
  getCTM,
  getMonthTimeline,
  getTitlesByCTM,
  getTracksByCentroid,
} from '@/lib/queries';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getTrackLabel, getCentroidLabel, getCountryName, getIsoFromBucketKey, Track, Event, Title } from '@/lib/types';
import { getTrackIcon } from '@/components/TrackCard';
import { setRequestLocale, getTranslations, getLocale } from 'next-intl/server';
import { ensureDE } from '@/lib/lazy-translate';
import TranslationNotice from '@/components/TranslationNotice';

export const dynamic = 'force-dynamic';

export async function generateMetadata({ params }: TrackPageProps): Promise<Metadata> {
  const { centroid_key, track_key } = await params;
  const t = await getTranslations('track');
  const tCentroidsMeta = await getTranslations('centroids');
  const tTracksMeta = await getTranslations('tracks');
  const centroid = await getCentroidById(centroid_key);
  if (!centroid) return { title: t('notFound') };
  const trackLabel = getTrackLabel(track_key as Track, tTracksMeta);
  const centroidLabel = getCentroidLabel(centroid.id, centroid.label, tCentroidsMeta);
  return {
    title: `${centroidLabel}: ${trackLabel}`,
    description: t('metaDescription', { track: trackLabel, label: centroidLabel }),
    alternates: { canonical: `/c/${centroid_key}/t/${track_key}` },
  };
}

const TOPICS_PAGE_SIZE = 10;

interface TrackPageProps {
  params: Promise<{ locale: string; centroid_key: string; track_key: string }>;
  searchParams: Promise<{ month?: string }>;
}

function formatMonthLabel(monthStr: string, loc?: string): string {
  const [year, month] = monthStr.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1, 1);
  return date.toLocaleDateString(loc === 'de' ? 'de-DE' : 'en-US', { month: 'long', year: 'numeric' });
}

// Helper functions for event processing
function countTitles(events: Event[]) {
  return events.reduce((sum, e) => sum + (e.source_title_ids?.length || 0), 0);
}


const STORY_GROUP_MIN_EVENTS = 50; // only group when there are many events

/** Build story groups from event families (Layer 2) or topic_core anchors (fallback).
 *  Prefers family_id grouping when available. Falls back to signal anchors.
 */
function buildStoryGroups(events: Event[]): { groups: StoryGroup[]; ungrouped: Event[] } {
  // Check if events have family data
  const hasFamilies = events.some(e => e.family_id);

  if (hasFamilies) {
    // Group by family_id — Layer 2 narrative topics
    const familyMap = new Map<string, { title: string; domain: string; summary: string; events: Event[] }>();
    const ungrouped: Event[] = [];

    for (const ev of events) {
      if (ev.family_id && ev.family_title) {
        if (!familyMap.has(ev.family_id)) {
          familyMap.set(ev.family_id, {
            title: ev.family_title,
            domain: ev.family_domain || '',
            summary: ev.family_summary || '',
            events: [],
          });
        }
        familyMap.get(ev.family_id)!.events.push(ev);
      } else {
        ungrouped.push(ev);
      }
    }

    const groups: StoryGroup[] = [];
    for (const [fid, fam] of familyMap) {
      if (fam.events.length < 1) continue;
      const totalSources = fam.events.reduce((sum, e) => sum + (e.source_title_ids?.length || 0), 0);
      fam.events.sort((a, b) => (b.source_title_ids?.length || 0) - (a.source_title_ids?.length || 0));
      groups.push({
        label: fam.domain || fam.title,
        anchor: fid,
        anchorType: 'family',
        events: fam.events,
        totalSources,
        topSignals: fam.domain ? [fam.title] : undefined,
      });
    }
    groups.sort((a, b) => b.totalSources - a.totalSources);
    ungrouped.sort((a, b) => (b.source_title_ids?.length || 0) - (a.source_title_ids?.length || 0));
    return { groups, ungrouped };
  }

  // Fallback: group by topic_core anchors (signal-based)
  const groupMap = new Map<string, Event[]>();
  const ungrouped: Event[] = [];

  for (const ev of events) {
    const anchor = ev.topic_core;
    if (!anchor || anchor.startsWith('TXT:')) {
      ungrouped.push(ev);
      continue;
    }
    const cleanAnchor = anchor.replace(/ \(general\)$/, '');
    if (!groupMap.has(cleanAnchor)) groupMap.set(cleanAnchor, []);
    groupMap.get(cleanAnchor)!.push(ev);
  }

  const groups: StoryGroup[] = [];
  for (const [anchor, evts] of groupMap) {
    if (evts.length < 2) {
      ungrouped.push(...evts);
      continue;
    }
    const anchorType = anchor.match(/^(PER|PLC|ORG|TGT|EVT):/)?.[1] || '';
    const raw = anchor.replace(/^(PER|PLC|ORG|TGT|EVT):/, '');
    const label = raw.length <= 3 ? raw : raw.charAt(0) + raw.slice(1).toLowerCase();
    const totalSources = evts.reduce((sum, e) => sum + (e.source_title_ids?.length || 0), 0);
    evts.sort((a, b) => (b.source_title_ids?.length || 0) - (a.source_title_ids?.length || 0));
    groups.push({ label, anchor, anchorType, events: evts, totalSources });
  }
  groups.sort((a, b) => b.totalSources - a.totalSources);
  ungrouped.sort((a, b) => (b.source_title_ids?.length || 0) - (a.source_title_ids?.length || 0));
  return { groups, ungrouped };
}

/** Split events into top-N topics and "other" (small topics + catchalls). */
function splitTopN(events: Event[], topN: number) {
  const sorted = [...events]
    .filter(e => !e.is_catchall)
    .sort((a, b) => (b.source_title_ids?.length || 0) - (a.source_title_ids?.length || 0));
  const catchalls = events.filter(e => e.is_catchall);
  const top = sorted.slice(0, topN);
  const rest = [...sorted.slice(topN), ...catchalls];
  return { top, rest };
}

const CORE_TITLES_LIMIT = 10;

const TITLE_STOP_WORDS = new Set([
  'the','a','an','in','on','at','to','for','of','and','or','with','as','by',
  'is','are','its','it','was','were','from','has','have','will','says','said',
  'after','over','amid','not','but','that','this','more','than','also','new',
]);

function titleWords(text: string): Set<string> {
  const words = new Set<string>();
  for (const w of text.toLowerCase().replace(/[.,;:!?"'()[\]]/g, '').split(/\s+/)) {
    if (w.length > 2 && !TITLE_STOP_WORDS.has(w)) words.add(w);
  }
  return words;
}

/** Select the most representative titles from a cluster.
 *
 *  Each headline is scored by how many content words it shares with ALL
 *  other headlines in the cluster (centrality score). The most "central"
 *  headlines best represent the cluster's core story.
 *
 *  Works before LLM title generation -- uses only source headlines.
 *  Multilingual titles score well because names/places are shared across
 *  languages (e.g., "Bushehr", "Macron", "Iran" appear in any language).
 */
function selectCoreTitles(allTitles: Title[]): Title[] {
  if (allTitles.length <= CORE_TITLES_LIMIT) return allTitles;

  // Build word sets for each title
  const wordSets = allTitles.map(t => titleWords(t.title_display));

  // Build corpus word frequency (how many titles contain each word)
  const corpusFreq = new Map<string, number>();
  for (const ws of wordSets) {
    for (const w of ws) {
      corpusFreq.set(w, (corpusFreq.get(w) || 0) + 1);
    }
  }

  // Score each title: sum of corpus frequency for its words.
  // Words that appear in many titles score higher (they're the core topic).
  // Normalize by title word count to avoid favoring long headlines.
  const scored = allTitles.map((title, i) => {
    const ws = wordSets[i];
    if (ws.size === 0) return { title, score: 0 };
    let score = 0;
    for (const w of ws) {
      score += corpusFreq.get(w) || 0;
    }
    return { title, score: score / ws.size };
  });

  scored.sort((a, b) => b.score - a.score);

  return scored.slice(0, CORE_TITLES_LIMIT).map(s => s.title);
}

/** Resolve titles per event using a pre-built lookup map.
 *  Selects top 10 most central titles (highest word overlap with cluster).
 */
function resolveEventTitles(events: Event[], titleMap: Map<string, Title>) {
  for (const event of events) {
    const allTitles = (event.source_title_ids || [])
      .map(id => titleMap.get(id))
      .filter((t): t is Title => t !== undefined);
    event.resolvedTitles = selectCoreTitles(allTitles);
  }
}

/* ------------------------------------------------------------------ */
/* Deferred async server components (wrapped in Suspense)             */
/* ------------------------------------------------------------------ */


/* ------------------------------------------------------------------ */
/* Main page component                                                */
/* ------------------------------------------------------------------ */

export default async function TrackPage({ params, searchParams }: TrackPageProps) {
  const { locale, centroid_key, track_key } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('track');
  const tNav = await getTranslations('nav');
  const tCommon = await getTranslations('common');
  const tCentroids = await getTranslations('centroids');
  const tTracks = await getTranslations('tracks');
  const localeStr = await getLocale();
  const { month } = await searchParams;

  const centroid = await getCentroidById(centroid_key, localeStr);
  if (!centroid) {
    notFound();
  }

  const track = track_key as Track;

  let ctm = await getCTM(centroid.id, track, month, locale);
  if (!ctm) {
    notFound();
  }

  // Lazy-translate CTM summary for DE users
  if (locale === 'de' && ctm.summary_text) {
    const de = await ensureDE('ctm', 'id', ctm.id, [
      { src: 'summary_text', dest: 'summary_text_de', text: ctm.summary_text },
    ]);
    if (de.summary_text) ctm = { ...ctm, summary_text: de.summary_text };
  }

  // Fetch immediate data in parallel (defer overlapping centroids + narratives via Suspense)
  const [titles, timeline, otherTracks] = await Promise.all([
    getTitlesByCTM(ctm.id),
    getMonthTimeline(centroid.id, track),
    getTracksByCentroid(centroid.id, month),
  ]);

  const months = timeline.map(t => t.month);
  const currentMonth = month || months[0];
  const eventCount = ctm.events_digest?.length || 0;
  const actualSourceCount = titles.length;

  // Build title lookup map and resolve per-event titles
  const titleMap = new Map(titles.map(t => [t.id, t]));

  // Process events for both content and TOC
  const allEvents = ctm.events_digest || [];
  resolveEventTitles(allEvents, titleMap);

  const homeIsoCodes = new Set(centroid.iso_codes || []);

  // Unified list: non-catchall sorted by source count, catchalls to OtherCoverage
  const { top: mainEvents, rest: otherEvents } = splitTopN(allEvents, allEvents.length);

  // Resolve bilateral badge data for country badges
  const bilateralBucketKeys = [...new Set(
    mainEvents
      .filter(e => e.event_type === 'bilateral' && e.bucket_key && !homeIsoCodes.has(e.bucket_key))
      .map(e => e.bucket_key!)
  )];
  const bucketCentroids = bilateralBucketKeys.length > 0 ? await getCentroidsByIds(bilateralBucketKeys) : [];
  const bucketCentroidMap = new Map(bucketCentroids.map(c => [c.id, c]));

  for (const event of mainEvents) {
    if (event.event_type === 'bilateral' && event.bucket_key && !homeIsoCodes.has(event.bucket_key)) {
      const bc = bucketCentroidMap.get(event.bucket_key);
      event.bucketLabel = getCentroidLabel(event.bucket_key, bc?.label || getCountryName(event.bucket_key), tCentroids);
      event.bucketIsoCodes = bc?.iso_codes || [getIsoFromBucketKey(event.bucket_key)];
      event.bucketLink = bc ? `/c/${event.bucket_key}/t/${track}?month=${currentMonth}` : undefined;
    } else if (event.event_type === 'domestic' || !event.bucket_key) {
      // Domestic events get the home centroid badge, disabled
      event.bucketLabel = getCentroidLabel(centroid.id, centroid.label, tCentroids);
      event.bucketIsoCodes = centroid.iso_codes || [];
      event.bucketDomestic = true;
    }
  }

  // TOC sections for mobile button
  const tocSections = [
    ...(ctm.summary_text ? [{ id: 'section-summary', label: t('summary') }] : []),
    ...(mainEvents.length > 0 ? [{ id: 'section-topics', label: t('topicsTitle') }] : []),
  ];



  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm">
      {/* Month selector (desktop only - mobile uses hamburger menu) */}
      {months.length > 0 && (
        <div className="hidden lg:block">
          <MonthNav
            months={months}
            currentMonth={currentMonth}
            baseUrl={`/c/${centroid.id}/t/${track}`}
          />
        </div>
      )}

      {/* Other Strategic Topics (Desktop only) */}
      {otherTracks.length > 0 && (
        <div className="hidden lg:block bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          <h3 className="text-xl font-bold mb-1 text-dashboard-text">
            {getCentroidLabel(centroid.id, centroid.label, tCentroids)}
          </h3>
          <p className="text-sm text-dashboard-text-muted mb-4">
            {tNav('otherStrategicTopics')}
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
                    {getTrackLabel(t as Track, tTracks)}
                  </span>
                  <span className="text-xs text-blue-400/60">{tNav('current')}</span>
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
                    {getTrackLabel(t as Track, tTracks)}
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>
      )}

    </div>
  );

  return (
    <DashboardLayout
      sidebar={sidebar}
      centroidLabel={getCentroidLabel(centroid.id, centroid.label, tCentroids)}
      centroidId={centroid.id}
      otherTracks={otherTracks}
      currentTrack={track}
      currentMonth={currentMonth}
      availableMonths={months}
    >
      {locale === 'de' && <TranslationNotice message={tCommon('translatedNotice')} />}
      {/* Track header */}
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <div className="mb-4">
          <Link
            href={`/c/${centroid.id}?month=${currentMonth}`}
            className="text-blue-400 hover:text-blue-300 text-sm"
          >
            ← {getCentroidLabel(centroid.id, centroid.label, tCentroids)}
          </Link>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold mb-2">
          {getCentroidLabel(centroid.id, centroid.label, tCentroids)}: {getTrackLabel(track, tTracks)}
        </h1>
        <p className="text-dashboard-text-muted">
          {t('headerStats', { month: formatMonthLabel(currentMonth, localeStr), events: eventCount, sources: actualSourceCount })}
        </p>
      </div>

      {/* CTM Summary */}
      {ctm.summary_text && (
        <div id="section-summary" className="mb-8">
          <h2 className="text-2xl font-bold mb-4">{t('summary')}</h2>
          <div className="text-lg leading-relaxed space-y-4">
            {ctm.summary_text.split('\n\n').flatMap((paragraph, idx) => {
              const trimmed = paragraph.trim();
              if (trimmed.startsWith('### ')) {
                const newlinePos = trimmed.indexOf('\n');
                const heading = newlinePos === -1 ? trimmed.slice(4) : trimmed.slice(4, newlinePos);
                const body = newlinePos === -1 ? null : trimmed.slice(newlinePos + 1).trim();
                const elements = [
                  <h3 key={`h-${idx}`} className="text-base font-semibold uppercase tracking-wide text-dashboard-text-muted mt-6 first:mt-0">
                    {heading}
                  </h3>
                ];
                if (body) {
                  elements.push(<p key={`p-${idx}`}>{body}</p>);
                }
                return elements;
              }
              return [<p key={idx}>{trimmed}</p>];
            })}
          </div>
        </div>
      )}

      {/* Events content */}
      {allEvents.length === 0 ? (
        // No events - show fallback content
        titles.length > 0 ? (
          <div className="mb-10">
            <h2 className="text-2xl font-bold mb-2">{t('sources')}</h2>
            <p className="text-sm text-dashboard-text-muted mb-4">
              {t('pendingClustering', { count: titles.length })}
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
                  {t('andMore', { count: titles.length - 50 })}
                </p>
              )}
            </div>
          </div>
        ) : (
          <div className="mb-10 py-12 text-center">
            <div className="text-dashboard-text-muted">
              <p className="text-lg mb-2">{t('noCoverage')}</p>
              <p className="text-sm">
                {t('checkBackLater')} {getCentroidLabel(centroid.id, centroid.label, tCentroids)}
              </p>
            </div>
          </div>
        )
      ) : (
        <>
          {/* Unified topics section */}
          <div id="section-topics" className="mb-10">
            {mainEvents.length > 0 ? (
              <>
                <h2 className="text-2xl font-bold mb-2">{t('topicsTitle')}</h2>
                <p className="text-sm text-dashboard-text-muted mb-4">
                  {t('sectionStats', { topics: mainEvents.length, sources: countTitles(allEvents) })}
                </p>

                {mainEvents.length >= STORY_GROUP_MIN_EVENTS && (mainEvents.some(e => e.family_id) || mainEvents.some(e => e.topic_core)) ? (() => {
                  const { groups, ungrouped: ungroupedEvents } = buildStoryGroups(mainEvents);
                  return (
                    <StoryGroupList
                      groups={groups}
                      ungrouped={ungroupedEvents}
                    />
                  );
                })() : (
                  <EventList
                    events={mainEvents}
                    initialLimit={TOPICS_PAGE_SIZE}
                    pageSize={TOPICS_PAGE_SIZE}
                    keyPrefix="topics"
                  />
                )}
              </>
            ) : otherEvents.length > 0 ? (
              <p className="text-sm text-dashboard-text-muted mb-4">
                {t('noMajorTopics')}
              </p>
            ) : null}

            {otherEvents.length > 0 && (
              <p className="text-sm text-dashboard-text-muted mt-4 py-2 border-t border-dashboard-border/50">
                + {otherEvents.reduce((s, e) => s + (e.source_title_ids?.length || 0), 0)} additional sources tracked
              </p>
            )}
          </div>
        </>
      )}

      {/* Mobile TOC Button */}
      <MobileTocButton sections={tocSections} />
    </DashboardLayout>
  );
}
