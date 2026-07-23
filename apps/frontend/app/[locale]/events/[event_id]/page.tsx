import { Suspense } from 'react';
import type { Metadata } from 'next';
import { notFound, permanentRedirect } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import ExpandableTitles from '@/components/ExpandableTitles';
import RelatedStories from '@/components/RelatedStories';
import EventNarrativeBadges from '@/components/narratives/EventNarrativeBadges';
import { getEventById, getEventTitles, getEventSagaSiblings, getRelatedEvents, resolveCanonicalEventId } from '@/lib/queries';
import { getTrackLabel, getCentroidLabel } from '@/lib/types';
import { setRequestLocale, getTranslations, getLocale } from 'next-intl/server';
import { ensureDE } from '@/lib/lazy-translate';
import TranslationNotice from '@/components/TranslationNotice';
import { buildPageMetadata, truncateDescription, formatCount, newsArticleJsonLd, breadcrumbList, type Locale as SeoLocale } from '@/lib/seo';
import JsonLd from '@/components/JsonLd';

export const dynamic = 'force-dynamic';

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { event_id } = await params;
  const locale = (await getLocale()) as SeoLocale;
  const t = await getTranslations('event');
  const event = await getEventById(event_id, locale);
  if (!event) return { title: t('notFound') };
  const title = event.title || t('eventDetail');

  // Compose description: summary + dateline (date, source count). Dateline adds
  // a stable signal even when summary is short or shared across related events.
  const dateline = (() => {
    if (!event.date) return '';
    const d = new Date(event.date + 'T00:00:00');
    const dateStr = d.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    const n = event.source_batch_count || 0;
    if (locale === 'de') {
      return ` (${dateStr}, ${formatCount(n, 'de')} Quelle${n === 1 ? '' : 'n'})`;
    }
    return ` (${dateStr}, ${formatCount(n)} source${n === 1 ? '' : 's'})`;
  })();

  const summary = (event.summary || '').trim();
  const description = summary
    ? truncateDescription(summary + dateline)
    : truncateDescription(t('metaDescription', { title }) + dateline);

  const base = buildPageMetadata({
    title,
    description,
    path: `/events/${event_id}`,
    locale,
    ogType: 'article',
    publishedTime: event.date ? `${event.date}T00:00:00Z` : undefined,
  });
  // Events without a generated prose summary are thin-content pages.
  // Exclude from Google's index but keep follow so link equity passes through.
  return summary ? base : { ...base, robots: { index: false, follow: true } };
}

interface Props {
  params: Promise<{ locale: string; event_id: string }>;
}

function formatDate(dateStr: string, locale: string = 'en-US'): string {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

/* ------------------------------------------------------------------ */
/* Deferred async server components                                   */
/* ------------------------------------------------------------------ */

// EventSidebar + EventSignalSection (RAI / SignalDashboard / Coverage
// Assessment) removed 2026-05-03. Both blocks read narratives.signal_stats /
// rai_signals which were populated by an on-demand extraction that ran
// only on 2026-02-19 (see Asana ticket — comparative-analysis rewire will
// rebuild per-event analysis on top of outlet_entity_stance).

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

  const canonicalId = await resolveCanonicalEventId(event_id);
  if (canonicalId && canonicalId !== event_id) {
    permanentRedirect(`/${locale}/events/${canonicalId}`);
  }

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

  // Sidebar is now just narrative chips. Inline.
  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm">
      <Suspense fallback={null}>
        <EventNarrativeBadges eventId={event_id} centroidId={event.centroid_id} variant="sidebar" />
      </Suspense>
    </div>
  );

  const centroidName = getCentroidLabel(event.centroid_id, event.centroid_label, tCentroids);
  const jsonLdBlocks: Record<string, unknown>[] = [
    newsArticleJsonLd({
      headline: event.title || t('eventDetail'),
      description: (event.summary || '').slice(0, 300),
      datePublished: event.date ? `${event.date}T00:00:00Z` : new Date().toISOString(),
      dateModified: event.last_active ? `${event.last_active}T00:00:00Z` : undefined,
      path: `/events/${event_id}`,
      locale: locale as SeoLocale,
      articleSection: trackLabel,
      keywords: Array.isArray(event.tags) ? event.tags.slice(0, 10) : undefined,
    }),
    breadcrumbList([
      { name: centroidName, path: `/c/${event.centroid_id}` },
      { name: trackLabel, path: `/c/${event.centroid_id}/t/${event.track}?month=${event.month}` },
      { name: event.title || t('eventDetail'), path: `/events/${event_id}` },
    ]),
  ];

  return (
    <DashboardLayout sidebar={sidebar} breadcrumb={breadcrumb}>
      <JsonLd data={jsonLdBlocks} />
      {locale === 'de' && <TranslationNotice message={tCommon('translatedNotice')} />}

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
          <p className="text-xs text-dashboard-text-muted mt-4 pt-4 border-t border-dashboard-border">
            by WorldBrief &amp;{' '}
            <Link href="/about" className="text-blue-400 hover:underline">Maksim Micheliov</Link>
            {' | AI-generated summary'}
          </p>
        </div>
      )}

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
