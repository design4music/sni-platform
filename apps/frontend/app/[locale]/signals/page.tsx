import { Suspense } from 'react';
import type { Metadata } from 'next';
import DashboardLayout from '@/components/DashboardLayout';
import SignalGraph from '@/components/signals/SignalGraph';
import SignalAccordion from '@/components/signals/SignalAccordion';
import { getSignalGraph, getSignalHeatmap } from '@/lib/queries';
import { SignalType } from '@/lib/types';
import { getTranslations } from 'next-intl/server';

export const revalidate = 300;

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('signals');
  return {
    title: `${t('title')} - WorldBrief`,
    description: t('observatorySubtitle'),
  };
}

const CATEGORIES: { type: SignalType; icon: string; badge: string }[] = [
  { type: 'persons',      icon: 'P', badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  { type: 'orgs',         icon: 'O', badge: 'bg-green-500/10 text-green-400 border-green-500/20' },
  { type: 'places',       icon: 'G', badge: 'bg-orange-500/10 text-orange-400 border-orange-500/20' },
  { type: 'commodities',  icon: 'C', badge: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' },
  { type: 'policies',     icon: 'L', badge: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
  { type: 'systems',      icon: 'S', badge: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
  { type: 'named_events', icon: 'E', badge: 'bg-pink-500/10 text-pink-400 border-pink-500/20' },
];

async function DeferredGraph() {
  const t = await getTranslations('signals');
  const graph = await getSignalGraph(5);
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{t('cooccurrenceNetwork')}</h2>
        <p className="text-xs text-dashboard-text-muted hidden sm:block">
          {t('hoverHint')}
        </p>
      </div>
      <SignalGraph nodes={graph.nodes} edges={graph.edges} />
      <p className="text-xs text-dashboard-text-muted">
        {t('graphDescription')}{' '}
        {t('graphColorLegend')}{' '}
        <span className="text-blue-400">{t('person')}</span>,{' '}
        <span className="text-green-400">{t('organization')}</span>,{' '}
        <span className="text-orange-400">{t('place')}</span>,{' '}
        <span className="text-yellow-400">{t('commodity')}</span>,{' '}
        <span className="text-purple-400">{t('policy')}</span>,{' '}
        <span className="text-cyan-400">{t('system')}</span>,{' '}
        <span className="text-pink-400">{t('eventType')}</span>.
      </p>
    </div>
  );
}

async function DeferredAccordion() {
  const t = await getTranslations('signals');
  const heatmapSignals = await getSignalHeatmap(5);
  if (heatmapSignals.length === 0) return null;
  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-lg font-semibold mb-1">{t('signalActivity')}</h2>
        <p className="text-xs text-dashboard-text-muted">
          {t('signalActivityDesc')}
        </p>
      </div>
      <SignalAccordion signals={heatmapSignals} categories={CATEGORIES} />
    </div>
  );
}

function GraphSkeleton() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Co-occurrence Network</h2>
      </div>
      <div className="w-full rounded-lg border border-dashboard-border bg-[#0f172a] animate-pulse" style={{ height: 400 }} />
    </div>
  );
}

function AccordionSkeleton() {
  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-lg font-semibold mb-1">Signal Activity</h2>
        <p className="text-xs text-dashboard-text-muted">Loading categories...</p>
      </div>
      <div className="space-y-2">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-12 rounded-lg border border-dashboard-border bg-dashboard-surface animate-pulse" />
        ))}
      </div>
    </div>
  );
}

export default async function SignalObservatoryPage() {
  const t = await getTranslations('signals');
  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold mb-2">{t('title')}</h1>
          <p className="text-dashboard-text-muted">
            {t('observatorySubtitle')}
          </p>
        </div>

        <Suspense fallback={<GraphSkeleton />}>
          <DeferredGraph />
        </Suspense>

        <Suspense fallback={<AccordionSkeleton />}>
          <DeferredAccordion />
        </Suspense>
      </div>
    </DashboardLayout>
  );
}
