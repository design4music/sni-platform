import { Suspense } from 'react';
import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import EventList from '@/components/EventList';
import OtherCoverage from '@/components/OtherCoverage';
import CountryAccordion from '@/components/CountryAccordion';
import TableOfContents, { TocSection } from '@/components/TableOfContents';
import MobileTocButton from '@/components/MobileTocButton';
import MonthNav from '@/components/MonthNav';
import {
  getCentroidById,
  getCentroidsByIds,
  getCTM,
  getMonthTimeline,
  getTitlesByCTM,
  getTracksByCentroid,
  getFramedNarratives,
} from '@/lib/queries';
import NarrativeCards from '@/components/NarrativeOverlay';
import ExtractButton from '@/components/ExtractButton';
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

// Display limits: top N topics shown, rest collapse into "Other Coverage"
const DOMESTIC_TOP_N = 20;
const INTL_TOP_N = 5;
const INITIAL_DISPLAY = 5;  // Show first 5, then "load more"

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

/** Resolve titles per event using a pre-built lookup map */
function resolveEventTitles(events: Event[], titleMap: Map<string, Title>) {
  for (const event of events) {
    event.resolvedTitles = (event.source_title_ids || [])
      .map(id => titleMap.get(id))
      .filter((t): t is Title => t !== undefined);
  }
}

/* ------------------------------------------------------------------ */
/* Deferred async server components (wrapped in Suspense)             */
/* ------------------------------------------------------------------ */


async function NarrativeSection({
  entityType, entityId, narrativeFramesLabel, noNarrativesLabel, locale,
}: {
  entityType: 'event' | 'ctm'; entityId: string; narrativeFramesLabel: string; noNarrativesLabel: string; locale?: string;
}) {
  const narratives = await getFramedNarratives(entityType, entityId, locale);

  // Lazy-translate narrative card fields for DE users
  if (locale === 'de') {
    for (const n of narratives) {
      const de = await ensureDE('narratives', 'id', n.id, [
        { src: 'label', dest: 'label_de', text: n.label || '', style: 'headline' },
        { src: 'description', dest: 'description_de', text: n.description || '' },
        { src: 'moral_frame', dest: 'moral_frame_de', text: n.moral_frame || '' },
      ]);
      if (de.label) n.label = de.label;
      if (de.description) n.description = de.description;
      if (de.moral_frame) n.moral_frame = de.moral_frame;
    }
  }
  if (narratives.length > 0) {
    return (
      <div id="section-narratives" className="mb-8">
        <h2 className="text-2xl font-bold mb-4">{narrativeFramesLabel}</h2>
        <NarrativeCards narratives={narratives} layout="grid" />
      </div>
    );
  }
  return (
    <div id="section-narratives" className="mb-8 p-6 rounded-lg border border-dashboard-border bg-dashboard-surface text-center">
      <p className="text-sm text-dashboard-text-muted mb-3">
        {noNarrativesLabel}
      </p>
      <ExtractButton entityType={entityType} entityId={entityId} />
    </div>
  );
}

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

  const isBilateralToSelf = (e: Event) =>
    e.event_type === 'bilateral' && e.bucket_key && homeIsoCodes.has(e.bucket_key);

  const domesticEvents = allEvents.filter(
    e => !e.event_type || e.event_type === 'domestic' || isBilateralToSelf(e)
  );
  const { top: domesticMainEvents, rest: domesticOther } = splitTopN(domesticEvents, DOMESTIC_TOP_N);

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

  // Fetch centroid records for bucket keys (needed for multi-country groups like NORDIC)
  const bucketKeys = Object.keys(bilateralGroups);
  const bucketCentroids = await getCentroidsByIds(bucketKeys);
  const bucketCentroidMap = new Map(bucketCentroids.map(c => [c.id, c]));

  // Build TOC sections (always include narratives since section always renders)
  const tocSections: TocSection[] = [];

  if (ctm.summary_text) {
    tocSections.push({ id: 'section-summary', label: t('summary') });
  }

  if (ctm.summary_text) {
    tocSections.push({ id: 'section-narratives', label: t('narrativeFrames') });
  }

  if (domesticEvents.length > 0) {
    tocSections.push({ id: 'section-domestic', label: t('domestic') });
  }

  if (internationalEvents.length > 0) {
    tocSections.push({ id: 'section-international', label: t('international') });
  }



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

      {/* Table of Contents (Desktop only) */}
      {tocSections.length > 0 && (
        <div className="hidden lg:block">
          <TableOfContents sections={tocSections} />
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

      {/* Narrative Frames (deferred via Suspense, only if CTM has a summary) */}
      {ctm.summary_text && (
        <Suspense fallback={
          <div id="section-narratives" className="mb-8 animate-pulse">
            <div className="h-7 w-48 bg-dashboard-border rounded mb-4" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="h-32 bg-dashboard-surface border border-dashboard-border rounded-lg" />
              <div className="h-32 bg-dashboard-surface border border-dashboard-border rounded-lg" />
            </div>
          </div>
        }>
          <NarrativeSection entityType="ctm" entityId={ctm.id} narrativeFramesLabel={t('narrativeFrames')} noNarrativesLabel={t('noNarratives')} locale={locale} />
        </Suspense>
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
          {/* Domestic section */}
          {domesticEvents.length > 0 && (
            <div id="section-domestic" className="mb-10">
              <h2 className="text-2xl font-bold mb-2">{t('domestic')}</h2>
              <p className="text-sm text-dashboard-text-muted mb-4">
                {t('sectionStats', { topics: domesticMainEvents.length, sources: countTitles(domesticEvents) })}
              </p>

              {domesticMainEvents.length > 0 ? (
                <>
                  <EventList
                    events={domesticMainEvents}
                    initialLimit={INITIAL_DISPLAY}
                    keyPrefix="domestic"
                  />
                  {domesticOther.length > 0 && (
                    <OtherCoverage
                      label={t('otherDomestic')}
                      events={domesticOther}
                    />
                  )}
                </>
              ) : domesticOther.length > 0 ? (
                <OtherCoverage
                  label={t('otherDomestic')}
                  events={domesticOther}
                  flat
                />
              ) : null}
            </div>
          )}

          {/* International section */}
          {internationalEvents.length > 0 && (
            <div id="section-international" className="mb-10">
              <h2 className="text-2xl font-bold mb-2">{t('international')}</h2>
              <p className="text-sm text-dashboard-text-muted mb-6">
                {t('sectionStats', { topics: internationalEvents.filter(e => !e.is_catchall).length, sources: countTitles(internationalEvents) })}
              </p>

              {/* Bilateral groups by country */}
              {sortedBilateralEntries.map(([bucketKey, events], index) => {
                const { top: mainEvents, rest: otherEvents } = splitTopN(events, INTL_TOP_N);
                const bucketCentroid = bucketCentroidMap.get(bucketKey);
                const countryLabel = getCentroidLabel(bucketKey, bucketCentroid?.label || getCountryName(bucketKey), tCentroids);
                const isoCodes = bucketCentroid?.iso_codes || [getIsoFromBucketKey(bucketKey)];

                return (
                  <CountryAccordion
                    key={bucketKey}
                    bucketKey={bucketKey}
                    countryName={countryLabel}
                    isoCodes={isoCodes}
                    mainEvents={mainEvents}
                    otherEvents={otherEvents}
                    totalSourceCount={countTitles(events)}
                    defaultOpen={index === 0}
                    centroidLink={bucketCentroid ? `/c/${bucketKey}/t/${track}?month=${currentMonth}` : undefined}
                  />
                );
              })}

              {/* Other International */}
              {otherInternational.length > 0 && (() => {
                const { top: mainEvents, rest: otherEvents } = splitTopN(otherInternational, INTL_TOP_N);

                return (
                  <CountryAccordion
                    bucketKey="other"
                    countryName={t('otherInternational')}
                    isoCodes={[]}
                    mainEvents={mainEvents}
                    otherEvents={otherEvents}
                    totalSourceCount={countTitles(otherInternational)}
                    defaultOpen={sortedBilateralEntries.length === 0}
                  />
                );
              })()}
            </div>
          )}

        </>
      )}

      {/* Mobile TOC Button */}
      <MobileTocButton sections={tocSections} />
    </DashboardLayout>
  );
}
