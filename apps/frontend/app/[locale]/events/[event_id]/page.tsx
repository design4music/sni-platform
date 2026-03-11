import { Suspense } from 'react';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import NarrativeCards from '@/components/NarrativeOverlay';
import RaiSidebar from '@/components/RaiSidebar';
import StanceClusterCard from '@/components/StanceClusterCard';
import ExpandableTitles from '@/components/ExpandableTitles';
import SignalDashboard from '@/components/SignalDashboard';
import RelatedStories from '@/components/RelatedStories';
import ExtractButton from '@/components/ExtractButton';
import { getEventById, getEventTitles, getEventSagaSiblings, getFramedNarratives, getStanceNarratives, getEntityAnalysis, getRelatedEvents } from '@/lib/queries';
import { getTrackLabel, getCentroidLabel } from '@/lib/types';
import { setRequestLocale, getTranslations, getLocale } from 'next-intl/server';
import { ensureDE } from '@/lib/lazy-translate';
import TranslationNotice from '@/components/TranslationNotice';

export const revalidate = 3600;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, event_id } = await params;
  const t = await getTranslations('event');
  const event = await getEventById(event_id, locale);
  if (!event) return { title: t('notFound') };
  const title = event.title || t('eventDetail');
  return {
    title,
    description: event.summary ? `${event.summary.slice(0, 155)}...` : t('metaDescription', { title }),
    alternates: { canonical: `/events/${event_id}` },
  };
}

interface Props {
  params: Promise<{ locale: string; event_id: string }>;
}

function formatDate(dateStr: string, locale: string = 'en-US'): string {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function PerspectiveBadge({ centroidId, label, track, trackLabel, month }: {
  centroidId: string; label: string; track: string; trackLabel: string; month: string;
}) {
  // Extract ISO code from centroid_id like "MIDEAST-IRAN" -> "IR" or "AMERICAS-USA" -> "US"
  const parts = centroidId.split('-');
  const isoCode = parts.length > 1 ? parts[parts.length - 1] : null;
  // Map common codes
  const isoMap: Record<string, string> = {
    USA: 'US', IRAN: 'IR', ISRAEL: 'IL', TURKEY: 'TR', CHINA: 'CN',
    RUSSIA: 'RU', INDIA: 'IN', BRAZIL: 'BR', GERMANY: 'DE', FRANCE: 'FR',
    JAPAN: 'JP', UK: 'GB', KOREA: 'KR', AUSTRALIA: 'AU', CANADA: 'CA',
  };
  const iso2 = isoCode ? (isoMap[isoCode] || (isoCode.length === 2 ? isoCode : null)) : null;

  return (
    <Link
      href={`/c/${centroidId}/t/${track}?month=${month}`}
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 hover:border-blue-500/40 transition-colors"
    >
      {iso2 && (
        <img
          src={`/flags/${iso2.toLowerCase()}.png`}
          alt={iso2}
          width={20}
          height={15}
          className="opacity-80"
          style={{ objectFit: 'contain', filter: 'saturate(0.7)' }}
        />
      )}
      <span className="text-sm font-medium text-blue-400">{label}</span>
      <span className="text-xs text-blue-400/60">{trackLabel}</span>
    </Link>
  );
}

/* ------------------------------------------------------------------ */
/* Deferred async server components                                   */
/* ------------------------------------------------------------------ */

async function EventSidebar({ eventId, coherenceCheck, locale }: {
  eventId: string;
  coherenceCheck?: { reason: string; topics?: string[] } | null;
  locale?: string;
}) {
  const t = await getTranslations('event');
  const narratives = await getFramedNarratives('event', eventId, locale);

  // Check for stance-clustered narratives (new comparative system)
  const stanceClusters = await getStanceNarratives('event', eventId, locale);
  const entityAnalysis = stanceClusters.length > 0
    ? await getEntityAnalysis('event', eventId, locale)
    : null;

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

  const rawStats = narratives.length > 0 ? narratives[0].signal_stats : null;
  const signalStats = rawStats?.title_count ? rawStats : null;
  const raiSignals = narratives.length > 0 ? narratives[0].rai_signals : null;

  // Legacy narratives (non-stance-clustered)
  const legacyNarratives = narratives.filter(
    (n) => !n.extraction_method || n.extraction_method !== 'stance_clustered'
  );

  return (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm">
      {/* Stance-clustered coverage landscape (new system) */}
      {stanceClusters.length > 0 && (
        <StanceClusterCard
          clusters={stanceClusters}
          entityType="event"
          entityId={eventId}
          synthesis={entityAnalysis?.synthesis || entityAnalysis?.scores?.synthesis}
          blindSpots={entityAnalysis?.blind_spots || entityAnalysis?.scores?.collective_blind_spots}
          frameDivergence={entityAnalysis?.scores?.frame_divergence}
          hasFullReport={!!entityAnalysis?.sections}
        />
      )}

      {/* Legacy narrative cards (shown if no stance clusters, or alongside for transition) */}
      {stanceClusters.length === 0 && (
        <>
          {legacyNarratives.length > 0 ? (
            <NarrativeCards narratives={legacyNarratives} />
          ) : coherenceCheck ? (
            <div className="bg-dashboard-border/30 rounded-lg p-5 space-y-2">
              <h3 className="text-sm font-semibold text-amber-300">{t('mixedCluster')}</h3>
              <p className="text-xs text-dashboard-text-muted leading-relaxed">
                {coherenceCheck.reason}
              </p>
              {coherenceCheck.topics?.length && coherenceCheck.topics.length > 0 && (
                <ul className="text-xs text-dashboard-text-muted space-y-0.5 list-disc list-inside">
                  {coherenceCheck.topics.map((topic: string, i: number) => (
                    <li key={i}>{topic}</li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <div className="bg-dashboard-border/30 rounded-lg p-5 space-y-3">
              <h3 className="text-sm font-semibold text-dashboard-text">{t('narrativeAnalysis')}</h3>
              <p className="text-xs text-dashboard-text-muted leading-relaxed">
                {t('extractDescription')}
              </p>
              <p className="text-xs text-dashboard-text-muted leading-relaxed">
                {t('extractTiming')}
              </p>
              <ExtractButton entityType="event" entityId={eventId} />
            </div>
          )}
        </>
      )}

      {/* Coverage Assessment */}
      {raiSignals && (
        <RaiSidebar signals={raiSignals} stats={signalStats} />
      )}
    </div>
  );
}

async function EventSignalSection({ eventId, locale }: { eventId: string; locale?: string }) {
  const narratives = await getFramedNarratives('event', eventId, locale);
  const rawStats = narratives.length > 0 ? narratives[0].signal_stats : null;
  const signalStats = rawStats?.title_count ? rawStats : null;

  if (!signalStats) return null;
  return (
    <div className="mb-8">
      <SignalDashboard stats={signalStats} />
    </div>
  );
}

async function SourceHeadlinesSection({ eventId }: { eventId: string }) {
  const t = await getTranslations('event');
  const titles = await getEventTitles(eventId);
  if (titles.length === 0) return null;
  return (
    <div className="mb-8">
      <h2 className="text-2xl font-bold mb-4">{t('sourceHeadlines')}</h2>
      <ExpandableTitles titles={titles} />
    </div>
  );
}

async function RelatedStoriesSection({ eventId, centroidId }: {
  eventId: string; centroidId: string;
}) {
  const relatedEvents = await getRelatedEvents(eventId, centroidId);
  return <RelatedStories events={relatedEvents} />;
}

/* ------------------------------------------------------------------ */
/* Main page component                                                */
/* ------------------------------------------------------------------ */

export default async function EventDetailPage({ params }: Props) {
  const { locale, event_id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('event');
  const tCommon = await getTranslations('common');
  const tCentroids = await getTranslations('centroids');
  const tTracks = await getTranslations('tracks');
  const intlLocale = await getLocale();

  let event = await getEventById(event_id, locale);
  if (!event) return notFound();

  // Lazy-translate title + summary for DE users
  if (locale === 'de') {
    const de = await ensureDE('events_v3', 'id', event.id, [
      { src: 'title', dest: 'title_de', text: event.title || '', style: 'headline' },
      { src: 'summary', dest: 'summary_de', text: event.summary || '' },
    ]);
    if (de.title) event = { ...event, title: de.title };
    if (de.summary) event = { ...event, summary: de.summary };
  }

  // Only fetch saga siblings immediately (fast, needed for story timeline)
  const sagaSiblings = event.saga
    ? await getEventSagaSiblings(event.saga, event_id, locale)
    : [];

  const trackLabel = getTrackLabel(event.track, tTracks);

  const breadcrumb = (
    <div className="text-sm text-dashboard-text-muted">
      <Link href={`/c/${event.centroid_id}`} className="text-blue-400 hover:text-blue-300">
        {getCentroidLabel(event.centroid_id, event.centroid_label, tCentroids)}
      </Link>
      <span className="mx-2">/</span>
      <Link
        href={`/c/${event.centroid_id}/t/${event.track}?month=${event.month}`}
        className="text-blue-400 hover:text-blue-300"
      >
        {trackLabel}
      </Link>
      <span className="mx-2">/</span>
      <span>{event.title || t('eventDetail')}</span>
    </div>
  );

  const sidebarFallback = (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm animate-pulse">
      <div className="bg-dashboard-border/30 rounded-lg p-5 space-y-3">
        <div className="h-4 w-32 bg-dashboard-border rounded" />
        <div className="h-3 w-full bg-dashboard-border/50 rounded" />
        <div className="h-3 w-4/5 bg-dashboard-border/50 rounded" />
      </div>
    </div>
  );

  const sidebar = (
    <Suspense fallback={sidebarFallback}>
      <EventSidebar eventId={event_id} coherenceCheck={event.coherence_check} locale={locale} />
    </Suspense>
  );

  return (
    <DashboardLayout sidebar={sidebar} breadcrumb={breadcrumb}>
      {locale === 'de' && <TranslationNotice message={tCommon('translatedNotice')} />}
      {/* Perspective badge */}
      <div className="mb-4">
        <PerspectiveBadge
          centroidId={event.centroid_id}
          label={getCentroidLabel(event.centroid_id, event.centroid_label, tCentroids)}
          track={event.track}
          trackLabel={trackLabel}
          month={event.month}
        />
      </div>

      {/* Header */}
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <h1 className="text-3xl md:text-4xl font-bold mb-2">
          {event.title || t('eventDetail')}
        </h1>
        <div className="flex flex-wrap items-center gap-3 text-dashboard-text-muted">
          <span>{formatDate(event.date, intlLocale)}</span>
          {event.last_active && event.last_active !== event.date && (
            <span>- {formatDate(event.last_active, intlLocale)}</span>
          )}
          <span className="text-xs px-2 py-0.5 rounded bg-dashboard-border">
            {tCommon('sourcesCount', { count: event.source_batch_count })}
          </span>
        </div>
        {event.tags && event.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {event.tags.map((tag, i) => (
              <span
                key={i}
                className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Story Timeline */}
      {sagaSiblings.length > 0 && (
        <div className="mb-8 pb-8 border-b border-dashboard-border">
          <h2 className="text-lg font-semibold mb-3 text-dashboard-text-muted">{t('storyTimeline')}</h2>
          <div className="border-l-2 border-blue-500/30 pl-4 space-y-3">
            {[...sagaSiblings, { id: event_id, title: event.title || t('currentEvent'), date: event.date, source_batch_count: event.source_batch_count, month: event.month }]
              .sort((a, b) => a.date.localeCompare(b.date))
              .map((sib) => {
                const isCurrent = sib.id === event_id;
                return (
                  <div key={sib.id} className={`relative ${isCurrent ? 'text-dashboard-text' : 'text-dashboard-text-muted'}`}>
                    <div className="absolute -left-[1.3rem] top-1.5 w-2 h-2 rounded-full bg-blue-500" />
                    <div className="flex items-baseline gap-3 flex-wrap">
                      <span className="text-xs font-mono shrink-0">{formatDate(sib.date, intlLocale)}</span>
                      {isCurrent ? (
                        <span className="font-semibold">{sib.title}</span>
                      ) : (
                        <Link href={`/events/${sib.id}`} className="hover:text-blue-400 transition-colors">
                          {sib.title}
                        </Link>
                      )}
                      <span className="text-xs px-1.5 py-0.5 rounded bg-dashboard-border shrink-0">
                        {tCommon('sourcesCount', { count: sib.source_batch_count })}
                      </span>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Summary */}
      {event.summary && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">{t('summary')}</h2>
          <div className="text-lg leading-relaxed space-y-4">
            {event.summary.split('\n\n').map((para, i) => (
              <p key={i}>{para.trim()}</p>
            ))}
          </div>
        </div>
      )}

      {/* Topic Stats (deferred - depends on narratives) */}
      <Suspense fallback={null}>
        <EventSignalSection eventId={event_id} locale={locale} />
      </Suspense>

      {/* Related Coverage (deferred) */}
      <Suspense fallback={null}>
        <RelatedStoriesSection eventId={event_id} centroidId={event.centroid_id} />
      </Suspense>

      {/* Source Headlines (deferred) */}
      <Suspense fallback={
        <div className="mb-8 animate-pulse">
          <div className="h-7 w-48 bg-dashboard-border rounded mb-4" />
          <div className="space-y-2">
            <div className="h-4 w-full bg-dashboard-border/50 rounded" />
            <div className="h-4 w-5/6 bg-dashboard-border/50 rounded" />
            <div className="h-4 w-4/6 bg-dashboard-border/50 rounded" />
          </div>
        </div>
      }>
        <SourceHeadlinesSection eventId={event_id} />
      </Suspense>
    </DashboardLayout>
  );
}
