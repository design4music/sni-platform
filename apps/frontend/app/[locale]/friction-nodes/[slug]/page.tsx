import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { setRequestLocale, getLocale } from 'next-intl/server';
import { getFrictionNodeView } from '@/lib/friction-nodes';
import PerspectivesView from '@/components/friction-nodes/PerspectivesView';

export const dynamic = 'force-dynamic';

interface Props {
  params: Promise<{ locale: string; slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug, locale } = await params;
  const view = await getFrictionNodeView(slug, locale);
  if (!view) return { title: 'Not Found' };
  return {
    title: `${view.fn.name} — Friction Node | WorldBrief`,
    description: view.fn.description ?? view.fn.name,
    robots: { index: false, follow: false }, // shadow route, don't index
  };
}

export default async function FrictionNodePage({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const intlLocale = await getLocale();

  const view = await getFrictionNodeView(slug, locale);
  if (!view) return notFound();

  const isDe = intlLocale === 'de';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Shadow-route notice */}
      <div className="mb-6 px-3 py-2 rounded border border-amber-500/30 bg-amber-500/5 text-xs text-amber-400">
        {isDe
          ? 'Schatten-Route — experimentelle Friction-Node-Architektur. Noch nicht in der Hauptnavigation.'
          : 'Shadow route — experimental friction-node architecture. Not yet in main navigation.'}
      </div>

      {/* Breadcrumb */}
      <div className="text-sm text-dashboard-text-muted mb-3">
        <Link href="/" className="text-blue-400 hover:text-blue-300">
          WorldBrief
        </Link>
        <span className="mx-2">/</span>
        <span>{isDe ? 'Friction Nodes' : 'Friction Nodes'}</span>
        <span className="mx-2">/</span>
        <span>{view.fn.name}</span>
      </div>

      {/* Header */}
      <header className="mb-8">
        <div className="flex flex-wrap items-baseline gap-3 mb-3">
          <h1 className="text-3xl font-bold text-dashboard-text">
            {view.fn.name}
          </h1>
          <span className="text-xs text-dashboard-text-muted font-mono">
            {view.fn.id}
          </span>
        </div>
        {view.fn.description && (
          <p className="text-base text-dashboard-text-muted leading-relaxed max-w-4xl">
            {view.fn.description}
          </p>
        )}
        <div className="mt-4 flex flex-wrap gap-4 text-xs text-dashboard-text-muted">
          <div>
            <span className="uppercase tracking-wider mr-1">{isDe ? 'Schauplaetze' : 'Manifests in'}:</span>
            <span className="font-mono">{view.fn.centroid_ids.join(', ')}</span>
          </div>
          <div>
            <span className="uppercase tracking-wider mr-1">{isDe ? 'Narrative' : 'Narratives'}:</span>
            <span>{view.narratives.length}</span>
          </div>
          <div>
            <span className="uppercase tracking-wider mr-1">{isDe ? 'Verknuepfte Ereignisse' : 'Linked events'}:</span>
            <span>{view.event_count}</span>
          </div>
        </div>
        {view.fn.topic_keywords && view.fn.topic_keywords.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {view.fn.topic_keywords.map((kw) => (
              <span
                key={kw}
                className="text-[11px] text-dashboard-text-muted bg-dashboard-surface border border-dashboard-border px-2 py-0.5 rounded"
              >
                {kw}
              </span>
            ))}
          </div>
        )}
      </header>

      {/* Perspectives */}
      <section className="mb-10">
        <h2 className="text-lg font-semibold text-dashboard-text-muted uppercase tracking-wider mb-4">
          {isDe ? 'Perspektiven' : 'Perspectives'}
        </h2>
        <p className="text-sm text-dashboard-text-muted mb-4 max-w-3xl">
          {isDe
            ? 'Dieselben Fakten, unter unterschiedlichen Rahmen gelesen. Jede Spalte ist die Position einer Koalition; das geladene Vokabular zeigt, wie diese Koalition das umstrittene Phaenomen formuliert.'
            : 'The same facts, read under different frames. Each column is one coalition’s position; the loaded vocabulary shows how that coalition articulates the contested phenomenon.'}
        </p>
        <PerspectivesView narratives={view.narratives} locale={intlLocale} />
      </section>

      {/* Footer note */}
      <footer className="mt-12 pt-6 border-t border-dashboard-border text-xs text-dashboard-text-muted">
        {isDe
          ? 'Die Verknuepfung zwischen Schlagzeilen und Narrativen erfolgt derzeit ueber einen mechanischen Schluesselwortabgleich (Demonstration). Die Pipeline-Integration ist noch nicht aktiv.'
          : 'Title-to-narrative attribution is currently via mechanical keyword match (demo). Pipeline integration not yet active.'}
      </footer>
    </div>
  );
}
