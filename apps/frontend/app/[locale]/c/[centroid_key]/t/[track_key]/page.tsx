import { Suspense } from 'react';
import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import EventList from '@/components/EventList';
import OtherCoverage from '@/components/OtherCoverage';
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

/** Select titles most relevant to the topic's generated title.
 *  Scores each source headline by word overlap with the event title,
 *  picks the top CORE_TITLES_LIMIT. This ensures coherence: titles about
 *  the same story score highest, regardless of language or publisher.
 */
function selectCoreTitles(allTitles: Title[], eventTitle?: string): Title[] {
  if (allTitles.length <= CORE_TITLES_LIMIT) return allTitles;

  if (!eventTitle) {
    // No generated title yet -- fall back to recency
    return [...allTitles]
      .sort((a, b) => new Date(b.pubdate_utc).getTime() - new Date(a.pubdate_utc).getTime())
      .slice(0, CORE_TITLES_LIMIT);
  }

  const eventWords = titleWords(eventTitle);

  // Score each title by word overlap with event title
  const scored = allTitles.map(title => {
    const words = titleWords(title.title_display);
    let overlap = 0;
    for (const w of words) {
      if (eventWords.has(w)) overlap++;
    }
    return { title, score: overlap };
  });

  // Sort by score desc, then date desc for ties
  scored.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return new Date(b.title.pubdate_utc).getTime() - new Date(a.title.pubdate_utc).getTime();
  });

  return scored.slice(0, CORE_TITLES_LIMIT).map(s => s.title);
}

/** Resolve titles per event using a pre-built lookup map.
 *  Selects top 10 most relevant titles (scored by similarity to event title).
 */
function resolveEventTitles(events: Event[], titleMap: Map<string, Title>) {
  for (const event of events) {
    const allTitles = (event.source_title_ids || [])
      .map(id => titleMap.get(id))
      .filter((t): t is Title => t !== undefined);
    event.resolvedTitles = selectCoreTitles(allTitles, event.title);
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
    getTracksByCentroid(centroid.id),
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
          {mainEvents.length > 0 && (
            <div id="section-topics" className="mb-10">
              <h2 className="text-2xl font-bold mb-2">{t('topicsTitle')}</h2>
              <p className="text-sm text-dashboard-text-muted mb-4">
                {t('sectionStats', { topics: mainEvents.length, sources: countTitles(allEvents) })}
              </p>

              <EventList
                events={mainEvents}
                initialLimit={TOPICS_PAGE_SIZE}
                pageSize={TOPICS_PAGE_SIZE}
                keyPrefix="topics"
              />

              {otherEvents.length > 0 && (
                <OtherCoverage
                  label={t('otherStrategicTopics')}
                  events={otherEvents}
                />
              )}
            </div>
          )}
        </>
      )}

      {/* Mobile TOC Button */}
      <MobileTocButton sections={tocSections} />
    </DashboardLayout>
  );
}
