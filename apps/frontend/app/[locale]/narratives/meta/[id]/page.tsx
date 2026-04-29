import { Suspense } from 'react';
import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import DashboardLayout from '@/components/DashboardLayout';
import NarrativeCard from '@/components/narratives/NarrativeCard';
import MentionTimeline from '@/components/signals/MentionTimeline';
import { getMetaNarrativeById, getAllMetaNarratives, getStrategicNarratives, getNarrativeSparklines, getMetaNarrativeActivity } from '@/lib/queries';
import { buildAlternates } from '@/lib/seo';
import { setRequestLocale, getTranslations } from 'next-intl/server';
import { getCentroidLabel } from '@/lib/types';

export const revalidate = 21600;

interface Props {
  params: Promise<{ locale: string; id: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id, locale } = await params;
  const meta = await getMetaNarrativeById(id, locale);
  if (!meta) return { title: 'Not Found' };
  return {
    title: meta.name,
    description: meta.description,
    alternates: buildAlternates(`/narratives/meta/${id}`),
  };
}

async function MetaTimeline({ metaId }: { metaId: string }) {
  const weekly = await getMetaNarrativeActivity(metaId);
  if (!weekly || weekly.length === 0) return null;
  return (
    <div className="mb-8">
      <MentionTimeline weekly={weekly} />
    </div>
  );
}

export default async function MetaNarrativePage({ params }: Props) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('narratives');
  const tCentroids = await getTranslations('centroids');

  const [meta, allMeta, allNarratives, sparklines] = await Promise.all([
    getMetaNarrativeById(id, locale),
    getAllMetaNarratives(locale),
    getStrategicNarratives(locale),
    getNarrativeSparklines(),
  ]);

  if (!meta) return notFound();

  const childNarratives = allNarratives.filter(n => n.meta_narrative_id === id);
  const totalEvents = childNarratives.reduce((sum, n) => sum + (n.event_count || 0), 0);

  const breadcrumb = (
    <div className="text-sm text-dashboard-text-muted">
      <Link href="/narratives" className="text-blue-400 hover:text-blue-300">
        {t('title')}
      </Link>
      <span className="mx-2">/</span>
      <span>{meta.name}</span>
    </div>
  );

  const sidebar = (
    <div className="lg:sticky lg:top-24 space-y-6">
      <div className="bg-dashboard-surface border border-dashboard-border rounded-lg p-4">
        <h3 className="text-sm font-semibold text-dashboard-text-muted uppercase tracking-wider mb-3">
          {t('allMeta')}
        </h3>
        <nav className="space-y-1">
          {allMeta.map(m => (
            <Link
              key={m.id}
              href={`/narratives/meta/${m.id}`}
              className={`block px-3 py-2 rounded text-sm transition ${
                m.id === id
                  ? 'bg-blue-500/20 text-blue-400 font-medium'
                  : 'text-dashboard-text-muted hover:text-dashboard-text hover:bg-dashboard-border'
              }`}
            >
              {m.name}
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );

  return (
    <DashboardLayout sidebar={sidebar} breadcrumb={breadcrumb}>
      <div className="mb-8 pb-8 border-b border-dashboard-border">
        <h1 className="text-3xl md:text-4xl font-bold mb-2">{meta.name}</h1>
        <p className="text-lg text-dashboard-text-muted mb-4">{meta.description}</p>
        <div className="flex items-center gap-4 text-sm text-dashboard-text-muted">
          <span>{t('narrativesInMeta', { count: childNarratives.length })}</span>
          <span>{totalEvents} {t('events').toLowerCase()}</span>
        </div>
      </div>

      {/* Aggregate timeline */}
      <Suspense fallback={<div className="w-full h-56 animate-pulse bg-dashboard-border/20 rounded-lg mb-8" />}>
        <MetaTimeline metaId={id} />
      </Suspense>

      {/* Child narratives */}
      <div className="space-y-1">
        {childNarratives.map(n => (
          <NarrativeCard
            key={n.id}
            id={n.id}
            name={n.name}
            actorCentroid={n.actor_centroid}
            actorLabel={n.actor_label || null}
            eventCount={n.event_count || 0}
            sparkline={sparklines[n.id]}
            matchedEventsLabel={t('matchedEvents')}
            tCentroids={tCentroids}
          />
        ))}
      </div>
    </DashboardLayout>
  );
}
