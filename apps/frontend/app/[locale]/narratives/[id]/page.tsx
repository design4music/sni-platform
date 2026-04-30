import { Suspense } from 'react';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import MentionTimeline from '@/components/signals/MentionTimeline';
import CompetingNarrativesPanel from '@/components/narratives/CompetingNarrativesPanel';
import { getStrategicNarrativeById, getNarrativeWeeklyActivity, getNarrativeEvents } from '@/lib/queries';
import { buildPageMetadata, articleJsonLd, breadcrumbList, type Locale as SeoLocale } from '@/lib/seo';
import JsonLd from '@/components/JsonLd';
import { getCentroidLabel } from '@/lib/types';
import { setRequestLocale, getTranslations, getLocale } from 'next-intl/server';

export const dynamic = 'force-dynamic';

interface Props {
  params: Promise<{ locale: string; id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id, locale } = await params;
  const narrative = await getStrategicNarrativeById(id, locale);
  if (!narrative) return { title: 'Not Found' };
  return buildPageMetadata({
    title: narrative.name,
    description: narrative.claim || narrative.name,
    path: `/narratives/${id}`,
    locale: locale as SeoLocale,
    ogType: 'article',
  });
}

function formatDate(dateStr: string, locale: string = 'en-US'): string {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

async function NarrativeTimeline({ narrativeId }: { narrativeId: string }) {
  const t = await getTranslations('narratives');
  const weekly = await getNarrativeWeeklyActivity(narrativeId);
  if (!weekly || weekly.length === 0) return null;
  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold mb-3 text-dashboard-text-muted">{t('timeline')}</h2>
      <MentionTimeline weekly={weekly} />
    </div>
  );
}

async function NarrativeEventsList({ narrativeId, locale }: { narrativeId: string; locale: string }) {
  const t = await getTranslations('narratives');
  const intlLocale = await getLocale();
  const events = await getNarrativeEvents(narrativeId, 50, locale);
  if (events.length === 0) return null;
  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold mb-3 text-dashboard-text-muted">{t('matchedEvents')}</h2>
      <div className="space-y-2">
        {events.map(ev => (
          <Link
            key={ev.id}
            href={`/events/${ev.id}`}
            className="flex flex-col md:flex-row md:items-center gap-1 md:gap-3 px-4 py-3 rounded-lg bg-dashboard-surface border border-dashboard-border hover:border-blue-500/40 transition"
          >
            <span className="text-sm text-dashboard-text md:truncate md:flex-1">
              {ev.title}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-dashboard-text-muted font-mono shrink-0">
                {formatDate(ev.date, intlLocale)}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${
                ev.confidence >= 0.8
                  ? 'bg-blue-500/20 text-blue-400'
                  : 'bg-slate-500/20 text-slate-400'
              }`}>
                {Math.round(ev.confidence * 100)}%
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default async function NarrativeDetailPage({ params }: Props) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('narratives');
  const tCentroids = await getTranslations('centroids');

  const narrative = await getStrategicNarrativeById(id, locale);
  if (!narrative) return notFound();

  const breadcrumb = (
    <div className="text-sm text-dashboard-text-muted flex flex-wrap items-baseline gap-y-0.5 overflow-hidden">
      <Link href="/narratives" className="text-blue-400 hover:text-blue-300 shrink-0">
        {t('title')}
      </Link>
      <span className="mx-1 md:mx-2 shrink-0">/</span>
      {narrative.meta_name && (
        <>
          <Link href={`/narratives/meta/${narrative.meta_narrative_id}`} className="text-blue-400 hover:text-blue-300">
            {narrative.meta_name}
          </Link>
          <span className="mx-1 md:mx-2 shrink-0">/</span>
        </>
      )}
      <span>{narrative.name}</span>
    </div>
  );

  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-6">
      {/* Meta-narrative card */}
      {narrative.meta_name && (
        <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">
            {t('meta')}
          </h3>
          <Link
            href={`/narratives/meta/${narrative.meta_narrative_id}`}
            className="text-base font-medium text-blue-400 hover:text-blue-300 transition"
          >
            {narrative.meta_name}
          </Link>
        </div>
      )}

      {/* Actor centroid card */}
      {narrative.actor_centroid && narrative.actor_label && (
        <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">
            {t('actor')}
          </h3>
          <Link
            href={`/c/${narrative.actor_centroid}`}
            className="text-base font-medium text-blue-400 hover:text-blue-300 transition"
          >
            {getCentroidLabel(narrative.actor_centroid!, narrative.actor_label!, tCentroids)}
          </Link>
        </div>
      )}

      {/* Event count */}
      {narrative.event_count != null && narrative.event_count > 0 && (
        <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
          <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">
            {t('events')}
          </h3>
          <p className="text-2xl font-bold text-dashboard-text" title={t('matchedEvents')}>{narrative.event_count}</p>
        </div>
      )}

      {/* Competing narratives (deferred) */}
      <Suspense fallback={null}>
        <CompetingNarrativesPanel
          narrativeId={id}
          actorCentroid={narrative.actor_centroid}
          locale={locale}
        />
      </Suspense>
    </div>
  );

  const narrativeJsonLd = [
    articleJsonLd({
      headline: narrative.name,
      description: narrative.claim || narrative.name,
      path: `/narratives/${narrative.id}`,
      locale: locale as SeoLocale,
    }),
    breadcrumbList([
      { name: 'Narratives', path: '/narratives' },
      { name: narrative.name, path: `/narratives/${narrative.id}` },
    ]),
  ];

  return (
    <DashboardLayout sidebar={sidebar} breadcrumb={breadcrumb}>
      <JsonLd data={narrativeJsonLd} />
      {/* Header */}
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <h1 className="text-3xl md:text-4xl font-bold mb-4">{narrative.name}</h1>

        {narrative.claim && (
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-1">{t('claim')}</h2>
            <p className="text-lg text-dashboard-text">{narrative.claim}</p>
          </div>
        )}

        {narrative.normative_conclusion && (
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-1">{t('normativeConclusion')}</h2>
            <p className="text-dashboard-text-muted">{narrative.normative_conclusion}</p>
          </div>
        )}

        {/* Keywords */}
        {narrative.keywords && narrative.keywords.length > 0 && (
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">{t('keywords')}</h2>
            <div className="flex flex-wrap gap-1.5">
              {narrative.keywords.map((kw, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400">
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Action classes */}
        {narrative.action_classes && narrative.action_classes.length > 0 && (
          <div className="mb-4">
            <h2 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">{t('actionClasses')}</h2>
            <div className="flex flex-wrap gap-1.5">
              {narrative.action_classes.map((ac, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400">
                  {ac}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Domains */}
        {narrative.domains && narrative.domains.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-2">{t('domains')}</h2>
            <div className="flex flex-wrap gap-1.5">
              {narrative.domains.map((d, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                  {d}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Activity Timeline (deferred) */}
      <Suspense fallback={<div className="w-full h-56 animate-pulse bg-dashboard-border/20 rounded-lg mb-8" />}>
        <NarrativeTimeline narrativeId={id} />
      </Suspense>

      {/* Matched Events (deferred) */}
      <Suspense fallback={
        <div className="animate-pulse space-y-2 mb-8">
          <div className="h-6 w-40 bg-dashboard-border rounded" />
          {[1, 2, 3].map(i => (
            <div key={i} className="h-12 bg-dashboard-border/30 rounded-lg" />
          ))}
        </div>
      }>
        <NarrativeEventsList narrativeId={id} locale={locale} />
      </Suspense>
    </DashboardLayout>
  );
}
