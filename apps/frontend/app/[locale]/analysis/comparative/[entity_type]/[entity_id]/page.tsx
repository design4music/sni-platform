import { Suspense } from 'react';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import ComparativeContent from '@/components/ComparativeContent';
import { getEntityAnalysis, getStanceNarratives, getEventSiblings } from '@/lib/queries';
import type { SiblingEvent } from '@/lib/queries';
import { query } from '@/lib/db';
import { setRequestLocale } from 'next-intl/server';

export const dynamic = 'force-dynamic';

interface Props {
  params: Promise<{ locale: string; entity_type: string; entity_id: string }>;
}

interface EntityContext {
  centroid_id: string;
  centroid_name: string;
  track: string;
  event_title: string;
  siblings?: SiblingEvent[];
}

async function getEntityContext(entityType: string, entityId: string, locale?: string): Promise<EntityContext | null> {
  if (entityType === 'sibling_group') {
    // Fetch all sibling events for this group
    const siblingRows = await query<{
      event_id: string;
      event_title: string;
      source_count: number;
      centroid_id: string;
      centroid_name: string;
      track: string;
    }>(
      `SELECT e.id as event_id,
              COALESCE(${locale === 'de' ? 'e.title_de, ' : ''}e.title, e.topic_core) as event_title,
              e.source_batch_count as source_count,
              ctm.centroid_id, cv.label as centroid_name, ctm.track
       FROM events_v3 e
       JOIN ctm ON ctm.id = e.ctm_id
       JOIN centroids_v3 cv ON cv.id = ctm.centroid_id
       WHERE e.sibling_group = $1
       ORDER BY e.source_batch_count DESC`,
      [entityId]
    );
    if (siblingRows.length === 0) return null;
    const primary = siblingRows[0];
    return {
      centroid_id: primary.centroid_id,
      centroid_name: siblingRows.map((r) => r.centroid_name).join(' / '),
      track: primary.track,
      event_title: primary.event_title,
      siblings: siblingRows.map((r) => ({
        event_id: r.event_id,
        title: r.event_title,
        source_count: r.source_count,
        centroid_name: r.centroid_name,
        sibling_group: entityId,
      })),
    };
  }

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
  const title = entity_type === 'sibling_group'
    ? `Cross-Centroid Analysis: ${ctx?.event_title?.slice(0, 50) || 'Unified'}`
    : ctx?.event_title
      ? `Analysis: ${ctx.event_title.slice(0, 60)}`
      : 'Comparative Analysis';
  return { title, description: 'Comparative media framing analysis across editorial clusters' };
}

async function AnalysisSidebar({
  entityType,
  entityId,
  locale,
  siblings,
}: {
  entityType: string;
  entityId: string;
  locale: string;
  siblings?: SiblingEvent[];
}) {
  let clusters;
  if (entityType === 'sibling_group' && siblings) {
    // Fetch clusters for all sibling events
    const allClusters = await Promise.all(
      siblings.map((s) => getStanceNarratives('event', s.event_id, locale))
    );
    // Tag each cluster with its centroid
    clusters = allClusters.flatMap((cs, i) =>
      cs.map((c) => ({ ...c, centroid_name: siblings[i].centroid_name }))
    );
  } else {
    clusters = await getStanceNarratives(entityType, entityId, locale);
  }
  const analysis = await getEntityAnalysis(entityType, entityId, locale);

  const scores = analysis?.scores;
  const totalTitles = clusters.reduce((sum, c) => sum + c.title_count, 0);

  return (
    <div className="lg:sticky lg:top-24 space-y-6 text-sm">
      {/* Cluster overview */}
      <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-semibold text-dashboard-text">Clusters Analysed</h3>
        <p className="text-xs text-dashboard-text-muted">
          {clusters.length} clusters, {totalTitles} headlines
        </p>
        {clusters.map((c, i) => {
          const dotColor = c.cluster_label === 'critical'
            ? 'bg-red-500'
            : c.cluster_label === 'supportive'
              ? 'bg-green-500'
              : 'bg-slate-400';
          const centroidLabel = 'centroid_name' in c ? (c as { centroid_name: string }).centroid_name : null;
          return (
            <div key={`${centroidLabel || ''}-${c.cluster_label}-${i}`} className="flex items-start gap-2">
              <span className={`w-2 h-2 rounded-full mt-1 flex-shrink-0 ${dotColor}`} />
              <div>
                <span className="text-xs font-semibold text-dashboard-text uppercase">
                  {centroidLabel ? `${centroidLabel} / ` : ''}{c.cluster_label}
                </span>
                <p className="text-xs text-dashboard-text-muted">{c.label}</p>
                <p className="text-xs text-dashboard-text-muted/60">
                  {c.cluster_publishers.length} publishers, {c.title_count} titles
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Structural metrics */}
      {scores && (
        <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-dashboard-text">Structural Metrics</h3>
          {scores.frame_divergence != null && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-dashboard-text-muted">Frame Divergence</span>
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
                Blind Spots
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

      {/* How to read */}
      <div className="bg-dashboard-border/30 rounded-lg p-4 space-y-2">
        <h4 className="text-xs font-semibold text-dashboard-text-muted uppercase tracking-wide">
          How to Read This
        </h4>
        <p className="text-xs text-dashboard-text-muted leading-relaxed">
          This analysis examines media coverage, not reality itself. Coverage is
          the only raw material available. If all coverage is distorted, we can
          only note the distortion.
        </p>
        <p className="text-xs text-dashboard-text-muted leading-relaxed">
          We evaluate structural coherence: motives, incentives, historical
          patterns, and power dynamics. We ask what makes sense given how the
          world works -- not what any single source claims is true.
        </p>
      </div>
    </div>
  );
}

export default async function ComparativeAnalysisPage({ params }: Props) {
  const { locale, entity_type, entity_id } = await params;
  setRequestLocale(locale);

  const ctx = await getEntityContext(entity_type, entity_id, locale);
  if (!ctx) return notFound();

  const analysis = await getEntityAnalysis(entity_type, entity_id, locale);

  const breadcrumb = (
    <div className="text-sm text-dashboard-text-muted">
      {entity_type === 'sibling_group' && ctx.siblings ? (
        <>
          {ctx.siblings.map((s, i) => (
            <span key={s.event_id}>
              {i > 0 && <span className="mx-1 text-dashboard-text-muted/40">|</span>}
              <Link href={`/events/${s.event_id}`} className="text-blue-400 hover:text-blue-300">
                {s.centroid_name}
              </Link>
            </span>
          ))}
          <span className="mx-2">/</span>
          <span>Cross-Centroid Analysis</span>
        </>
      ) : (
        <>
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
          <span>Comparative Analysis</span>
        </>
      )}
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
      <AnalysisSidebar entityType={entity_type} entityId={entity_id} locale={locale} siblings={ctx.siblings} />
    </Suspense>
  );

  return (
    <DashboardLayout sidebar={sidebar} breadcrumb={breadcrumb}>
      {/* LLM disclaimer */}
      <div className="mb-6 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
        <p className="text-xs text-amber-300 leading-relaxed">
          This analysis is generated by an AI system operating under the RAI Framework.
          It examines media coverage patterns, not underlying reality. Use it as a
          starting point for your own investigation, not as a final assessment.
        </p>
      </div>

      {/* Title */}
      <h1 className="text-3xl md:text-4xl font-bold mb-2">
        {entity_type === 'sibling_group' ? 'Cross-Centroid Media Analysis' : 'Comparative Media Analysis'}
      </h1>
      {ctx.event_title && (
        <p className="text-lg text-dashboard-text-muted mb-4">
          {ctx.event_title}
        </p>
      )}
      {entity_type === 'sibling_group' && ctx.siblings && (
        <div className="flex flex-wrap gap-2 mb-8">
          {ctx.siblings.map((s) => (
            <Link
              key={s.event_id}
              href={`/events/${s.event_id}`}
              className="text-xs px-3 py-1 rounded-full bg-dashboard-border text-dashboard-text-muted hover:text-dashboard-text transition-colors"
            >
              {s.centroid_name} ({s.source_count} src)
            </Link>
          ))}
        </div>
      )}

      {/* Analysis content */}
      <ComparativeContent
        entityType={entity_type}
        entityId={entity_id}
        cachedAnalysis={analysis}
      />
    </DashboardLayout>
  );
}
