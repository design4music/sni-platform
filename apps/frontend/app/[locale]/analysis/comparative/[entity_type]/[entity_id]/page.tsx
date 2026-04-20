import { Suspense } from 'react';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import ComparativeContent from '@/components/ComparativeContent';
import { getEntityAnalysis, getStanceNarratives, getNarrativesForEvent } from '@/lib/queries';
import { query } from '@/lib/db';
import { setRequestLocale, getTranslations } from 'next-intl/server';
import { ensureDE } from '@/lib/lazy-translate';

export const dynamic = 'force-dynamic';

interface Props {
  params: Promise<{ locale: string; entity_type: string; entity_id: string }>;
}

interface EntityContext {
  centroid_id: string;
  centroid_name: string;
  track: string;
  event_title: string;
}

async function getEntityContext(entityType: string, entityId: string, locale?: string): Promise<EntityContext | null> {
  if (entityType === 'event') {
    const rows = await query<{
      centroid_id: string;
      centroid_name: string;
      track: string;
      event_title: string;
    }>(
      `SELECT c.centroid_id, cv.label as centroid_name, c.track,
              COALESCE(e.title, e.topic_core) as event_title
       FROM events_v3 e
       JOIN ctm c ON c.id = e.ctm_id
       JOIN centroids_v3 cv ON cv.id = c.centroid_id
       WHERE e.id = $1`,
      [entityId]
    );
    return rows.length > 0 ? rows[0] : null;
  }
  const rows = await query<{
    centroid_id: string;
    centroid_name: string;
    track: string;
    event_title: string;
  }>(
    `SELECT c.centroid_id, cv.label as centroid_name, c.track, '' as event_title
     FROM ctm c
     JOIN centroids_v3 cv ON cv.id = c.centroid_id
     WHERE c.id = $1`,
    [entityId]
  );
  return rows.length > 0 ? rows[0] : null;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale, entity_type, entity_id } = await params;
  const ctx = await getEntityContext(entity_type, entity_id, locale);
  const title = ctx?.event_title
    ? `Analysis: ${ctx.event_title.slice(0, 60)}`
    : 'Comparative Analysis';
  // Comparative analyses duplicate content from the underlying event/centroid
  // page; keep the canonical source in the index and exclude this surface.
  return {
    title,
    description: 'Comparative media framing analysis across editorial clusters',
    robots: { index: false, follow: true },
  };
}

async function StrategicNarrativesSidebar({ entityType, entityId }: { entityType: string; entityId: string }) {
  if (entityType !== 'event') return null;
  const links = await getNarrativesForEvent(entityId);
  if (links.length === 0) return null;

  return (
    <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4 space-y-3">
      <h3 className="text-sm font-semibold text-dashboard-text">Strategic Narratives</h3>
      <p className="text-xs text-dashboard-text-muted leading-relaxed">
        Geopolitical narratives connected to this event
      </p>
      <div className="space-y-1.5">
        {links.map(link => (
          <Link
            key={link.narrative_id}
            href={`/narratives/${link.narrative_id}`}
            className="flex items-center gap-2 text-xs hover:text-purple-400 transition"
          >
            <span className="text-purple-400/70 shrink-0">&bull;</span>
            <span className="text-dashboard-text truncate">{link.narrative_name}</span>
            {link.actor_label && (
              <span className="text-dashboard-text-muted shrink-0">{link.actor_label}</span>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}

async function AnalysisSidebar({
  entityType,
  entityId,
  locale,
}: {
  entityType: string;
  entityId: string;
  locale: string;
}) {
  const t = await getTranslations('comparative');

  const clusters = await getStanceNarratives(entityType, entityId, locale);

  // Lazy-translate cluster labels for DE
  if (locale === 'de') {
    for (const c of clusters) {
      const de = await ensureDE('narratives', 'id', c.id, [
        { src: 'label', dest: 'label_de', text: c.label || '', style: 'headline' },
      ]);
      if (de.label) c.label = de.label;
    }
  }

  const analysis = await getEntityAnalysis(entityType, entityId, locale);

  const scores = analysis?.scores;
  const totalTitles = clusters.reduce((sum, c) => sum + c.title_count, 0);

  return (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm">
      {/* Cluster overview */}
      <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-semibold text-dashboard-text">{t('clustersAnalysed')}</h3>
        <p className="text-xs text-dashboard-text-muted">
          {t('clustersHeadlines', { clusters: clusters.length, headlines: totalTitles })}
        </p>
        {clusters.map((c, i) => {
          const dotColor = c.cluster_label === 'critical'
            ? 'bg-red-500'
            : c.cluster_label === 'supportive'
              ? 'bg-green-500'
              : 'bg-slate-400';
          return (
            <div key={`${c.cluster_label}-${i}`} className="flex items-start gap-2">
              <span className={`w-2 h-2 rounded-full mt-1 flex-shrink-0 ${dotColor}`} />
              <div>
                <span className="text-xs font-semibold text-dashboard-text uppercase">
                  {c.cluster_label}
                </span>
                <p className="text-xs text-dashboard-text-muted">{c.label}</p>
                <p className="text-xs text-dashboard-text-muted/60">
                  {t('publishersTitles', { publishers: c.cluster_publishers.length, titles: c.title_count })}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Structural metrics */}
      {scores && (
        <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-dashboard-text">{t('structuralMetrics')}</h3>
          {scores.frame_divergence != null && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-dashboard-text-muted">{t('frameDivergence')}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${
                scores.frame_divergence >= 0.7
                  ? 'bg-red-500/20 text-red-400 border-red-500/30'
                  : scores.frame_divergence >= 0.4
                    ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
                    : 'bg-green-500/20 text-green-400 border-green-500/30'
              }`}>
                {Math.round(scores.frame_divergence * 100)}%
              </span>
            </div>
          )}
          {scores.collective_blind_spots && scores.collective_blind_spots.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide mb-1.5">
                {t('blindSpots')}
              </h4>
              <ul className="space-y-1">
                {scores.collective_blind_spots.map((s: string, i: number) => (
                  <li key={i} className="text-xs text-dashboard-text-muted leading-relaxed flex items-start gap-1.5">
                    <span className="text-orange-400 mt-0.5 flex-shrink-0">?</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Strategic narratives */}
      <Suspense fallback={null}>
        <StrategicNarrativesSidebar entityType={entityType} entityId={entityId} />
      </Suspense>

      {/* How to read */}
      <div className="bg-dashboard-border/30 rounded-lg p-4 space-y-2">
        <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide">
          {t('howToRead')}
        </h4>
        <p className="text-xs text-dashboard-text-muted leading-relaxed">
          {t('howToReadP1')}
        </p>
        <p className="text-xs text-dashboard-text-muted leading-relaxed">
          {t('howToReadP2')}
        </p>
      </div>
    </div>
  );
}

export default async function ComparativeAnalysisPage({ params }: Props) {
  const { locale, entity_type, entity_id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('comparative');

  const ctx = await getEntityContext(entity_type, entity_id, locale);
  if (!ctx) return notFound();

  const analysis = await getEntityAnalysis(entity_type, entity_id, locale);

  // Lazy-translate synthesis and blind_spots for DE (short fields)
  if (locale === 'de' && analysis?.id) {
    const de = await ensureDE('entity_analyses', 'id', analysis.id, [
      { src: 'synthesis', dest: 'synthesis_de', text: analysis.synthesis || '' },
    ]);
    if (de.synthesis) analysis.synthesis = de.synthesis;
    // blind_spots is text[] -- translate as joined string, ensureDE won't help
    // These are served via COALESCE in the query when _de columns are populated
  }

  const breadcrumb = (
    <div className="text-sm text-dashboard-text-muted">
      <Link href={`/c/${ctx.centroid_id}`} className="text-blue-400 hover:text-blue-300">
        {ctx.centroid_name}
      </Link>
      <span className="mx-2">/</span>
      <Link
        href={`/c/${ctx.centroid_id}/t/${ctx.track}`}
        className="text-blue-400 hover:text-blue-300"
      >
        {ctx.track.replace(/_/g, ' ')}
      </Link>
      {entity_type === 'event' && ctx.event_title && (
        <>
          <span className="mx-2">/</span>
          <Link
            href={`/events/${entity_id}`}
            className="text-blue-400 hover:text-blue-300"
          >
            {ctx.event_title.length > 50
              ? ctx.event_title.slice(0, 50) + '...'
              : ctx.event_title}
          </Link>
        </>
      )}
      <span className="mx-2">/</span>
      <span>{t('breadcrumbAnalysis')}</span>
    </div>
  );

  const sidebar = (
    <Suspense fallback={
      <div className="lg:sticky lg:top-24 space-y-6 text-sm animate-pulse">
        <div className="bg-dashboard-border/30 rounded-lg p-5 space-y-3">
          <div className="h-4 w-32 bg-dashboard-border rounded" />
          <div className="h-3 w-full bg-dashboard-border/50 rounded" />
        </div>
      </div>
    }>
      <AnalysisSidebar entityType={entity_type} entityId={entity_id} locale={locale} />
    </Suspense>
  );

  return (
    <DashboardLayout sidebar={sidebar} breadcrumb={breadcrumb}>
      {/* LLM disclaimer */}
      <div className="mb-6 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
        <p className="text-xs text-amber-300 leading-relaxed">
          {t('llmDisclaimer')}
        </p>
      </div>

      {/* Title */}
      <h1 className="text-3xl md:text-4xl font-bold mb-2">
        {t('title')}
      </h1>
      {ctx.event_title && (
        <p className="text-lg text-dashboard-text-muted mb-4">
          {ctx.event_title}
        </p>
      )}

      {/* Analysis content */}
      <ComparativeContent
        entityType={entity_type}
        entityId={entity_id}
        cachedAnalysis={analysis}
        locale={locale}
      />
    </DashboardLayout>
  );
}
